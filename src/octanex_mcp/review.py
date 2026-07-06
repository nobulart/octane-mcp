from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path
from typing import Any

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _read_png_pixels(path: Path) -> tuple[int, int, list[tuple[int, int, int]]]:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("not a PNG file")

    pos = len(PNG_SIGNATURE)
    width = height = bit_depth = color_type = None
    compressed = bytearray()
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        kind = data[pos + 4 : pos + 8]
        payload = data[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(">IIBBBBB", payload)
            if compression != 0 or filter_method != 0 or interlace != 0:
                raise ValueError("unsupported PNG compression/filter/interlace settings")
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            break

    if width is None or height is None or bit_depth is None or color_type is None:
        raise ValueError("PNG missing IHDR")
    if bit_depth != 8:
        raise ValueError("only 8-bit PNG previews are supported")

    channels_by_type = {0: 1, 2: 3, 4: 2, 6: 4}
    channels = channels_by_type.get(color_type)
    if channels is None:
        raise ValueError("palette PNG previews are not supported")

    raw = zlib.decompress(bytes(compressed))
    stride = width * channels
    expected = (stride + 1) * height
    if len(raw) < expected:
        raise ValueError("PNG pixel data is truncated")

    rows: list[bytes] = []
    prev = bytearray(stride)
    offset = 0
    for _ in range(height):
        filter_type = raw[offset]
        scanline = bytearray(raw[offset + 1 : offset + 1 + stride])
        offset += stride + 1
        recon = bytearray(stride)
        for i, value in enumerate(scanline):
            left = recon[i - channels] if i >= channels else 0
            up = prev[i]
            up_left = prev[i - channels] if i >= channels else 0
            if filter_type == 0:
                recon[i] = value
            elif filter_type == 1:
                recon[i] = (value + left) & 0xFF
            elif filter_type == 2:
                recon[i] = (value + up) & 0xFF
            elif filter_type == 3:
                recon[i] = (value + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                recon[i] = (value + _paeth(left, up, up_left)) & 0xFF
            else:
                raise ValueError(f"unsupported PNG filter type {filter_type}")
        rows.append(bytes(recon))
        prev = recon

    pixels: list[tuple[int, int, int]] = []
    for row in rows:
        for x in range(width):
            base = x * channels
            if color_type == 0:
                gray = row[base]
                pixels.append((gray, gray, gray))
            elif color_type == 2:
                pixels.append((row[base], row[base + 1], row[base + 2]))
            elif color_type == 4:
                gray = row[base]
                pixels.append((gray, gray, gray))
            elif color_type == 6:
                pixels.append((row[base], row[base + 1], row[base + 2]))
    return width, height, pixels


def _round3(value: float) -> float:
    rounded = round(float(value), 3)
    return 0.0 if rounded == -0.0 else rounded


def _edge_density(width: int, height: int, luminance: list[float]) -> float:
    if width < 2 or height < 2:
        return 0.0
    edges = 0
    comparisons = 0
    threshold = 18.0
    for y in range(height):
        for x in range(width):
            here = luminance[y * width + x]
            if x + 1 < width:
                edges += abs(here - luminance[y * width + x + 1]) >= threshold
                comparisons += 1
            if y + 1 < height:
                edges += abs(here - luminance[(y + 1) * width + x]) >= threshold
                comparisons += 1
    return (edges / comparisons) * 100.0 if comparisons else 0.0


def _foreground_metrics(width: int, height: int, luminance: list[float], contrast: float) -> dict[str, float]:
    if not luminance or width <= 0 or height <= 0:
        return {"foreground_pixel_percent": 0.0, "foreground_bbox_area_percent": 0.0}
    sorted_luma = sorted(luminance)
    background = sorted_luma[len(sorted_luma) // 2]
    threshold = max(12.0, contrast * 0.35)
    xs: list[int] = []
    ys: list[int] = []
    foreground_count = 0
    for idx, value in enumerate(luminance):
        if abs(value - background) >= threshold:
            foreground_count += 1
            ys.append(idx // width)
            xs.append(idx % width)
    foreground_pixel_percent = foreground_count / len(luminance) * 100.0
    if not xs or not ys:
        bbox_area_percent = 0.0
    else:
        bbox_width = max(xs) - min(xs) + 1
        bbox_height = max(ys) - min(ys) + 1
        bbox_area_percent = bbox_width * bbox_height / (width * height) * 100.0
    return {
        "foreground_pixel_percent": _round3(foreground_pixel_percent),
        "foreground_bbox_area_percent": _round3(bbox_area_percent),
    }


def _diagnosis(
    *,
    issues: list[str],
    mean: float,
    contrast: float,
    near_black: float,
    near_white: float,
    edge_density: float,
) -> dict[str, Any]:
    likely_causes: list[str] = []
    recommended_actions: list[dict[str, Any]] = []
    if "mostly near-black" in issues:
        likely_causes.extend(["lighting too dim", "camera may be inside or behind geometry", "material may be too dark"])
        recommended_actions.append({"action": "increase_lighting", "patch": {"lighting": {"preset": "brighter_studio"}}})
        recommended_actions.append({"action": "increase_exposure", "patch": {"render": {"exposure_compensation": 1.0}}})
    if "mostly near-white" in issues:
        likely_causes.extend(["exposure too high", "environment too bright", "material/emission clipping highlights"])
        recommended_actions.append({"action": "reduce_exposure", "patch": {"render": {"exposure_compensation": -1.0}}})
    if "very low contrast" in issues:
        likely_causes.extend(["flat lighting", "object blends into background", "camera framing has too little visible geometry"])
        recommended_actions.append({"action": "increase_contrast", "patch": {"lighting": {"preset": "soft_studio", "key_fill_ratio": 2.0}}})
    if "likely object too small" in issues:
        likely_causes.extend(["camera is too far away", "asset scale is too small", "scene has excessive empty frame"])
        recommended_actions.append({"action": "tighten_camera", "patch_hint": "move camera closer or reduce fov around asset bounds"})
    severity = "ok"
    if issues:
        severity = "error" if near_black > 98.0 or near_white > 98.0 or contrast < 2.0 else "warning"
    return {
        "ok": not issues,
        "severity": severity,
        "issues": issues,
        "metrics": {
            "mean_brightness": _round3(mean),
            "contrast": _round3(contrast),
            "near_black_percent": _round3(near_black),
            "near_white_percent": _round3(near_white),
            "edge_density": _round3(edge_density),
        },
        "likely_causes": list(dict.fromkeys(likely_causes)),
        "recommended_actions": recommended_actions,
    }


def suggest_camera_fix(preview_review: dict[str, Any], asset_bounds: dict[str, Any]) -> dict[str, Any]:
    center = [float(value) for value in asset_bounds.get("center", [0.0, 0.0, 0.0])]
    radius = max(float(asset_bounds.get("radius", 1.0)), 0.1)
    issues = set(preview_review.get("issues", []))
    fov = 36.0 if "likely object too small" in issues else 45.0
    margin = 2.2 if "likely object clipped at frame edge" in issues else 1.45
    distance = radius * margin
    camera = {
        "position": [_round3(center[0] + distance), _round3(center[1] - distance * 1.2), _round3(center[2] + distance * 0.8)],
        "target": center,
        "fov": fov,
    }
    return {"action": "adjust_camera", "reason": "improve object framing", "patch": {"camera": camera}}


def suggest_lighting_fix(preview_review: dict[str, Any]) -> dict[str, Any]:
    issues = set(preview_review.get("issues", []))
    if "mostly near-white" in issues:
        return {"action": "reduce_exposure", "reason": "preview is clipped", "patch": {"lighting": {"preset": "soft_studio"}, "render": {"exposure_compensation": -1.0}}}
    return {"action": "increase_lighting", "reason": "preview is dark or low contrast", "patch": {"lighting": {"preset": "brighter_studio"}, "render": {"exposure_compensation": 1.0}}}


def review_preview(path: str | Path | None = None) -> dict[str, Any]:
    preview_path = Path(path) if path is not None else Path("preview.png")
    result: dict[str, Any] = {
        "path": str(preview_path),
        "exists": preview_path.exists(),
        "ok": False,
        "issues": [],
    }
    if not preview_path.exists():
        result["issues"].append("file does not exist")
        return result

    result["file_size"] = preview_path.stat().st_size
    if result["file_size"] <= 0:
        result["issues"].append("file is empty")
        return result

    try:
        width, height, pixels = _read_png_pixels(preview_path)
    except Exception as exc:
        result["issues"].append(f"could not decode PNG: {exc}")
        return result

    luminance = [0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b in pixels]
    count = len(luminance) or 1
    mean = sum(luminance) / count
    variance = sum((value - mean) ** 2 for value in luminance) / count
    contrast = math.sqrt(variance)
    near_black = sum(value <= 8 for value in luminance) / count * 100.0
    near_white = sum(value >= 247 for value in luminance) / count * 100.0
    edge_density = _edge_density(width, height, luminance)
    foreground = _foreground_metrics(width, height, luminance, contrast)
    likely_blank = contrast < 2.0 or near_black > 98.0
    likely_clipped = near_white > 98.0
    likely_tiny = (
        not likely_blank
        and not likely_clipped
        and edge_density < 2.0
        and contrast >= 2.0
        and foreground["foreground_bbox_area_percent"] < 12.0
    )

    result.update(
        {
            "dimensions": [width, height],
            "mean_brightness": _round3(mean),
            "contrast": _round3(contrast),
            "near_black_percent": _round3(near_black),
            "near_white_percent": _round3(near_white),
            "edge_density": _round3(edge_density),
            **foreground,
            "likely_blank": likely_blank,
            "likely_clipped": likely_clipped,
            "likely_object_too_small": likely_tiny,
        }
    )
    if likely_blank:
        result["issues"].append("mostly near-black" if near_black > 98.0 else "very low contrast")
    if likely_clipped:
        result["issues"].append("mostly near-white")
    if likely_tiny:
        result["issues"].append("likely object too small")
    diagnosis = _diagnosis(issues=result["issues"], mean=mean, contrast=contrast, near_black=near_black, near_white=near_white, edge_density=edge_density)
    result.update(diagnosis)
    result["diagnosis"] = diagnosis
    result["ok"] = not result["issues"]
    return result
