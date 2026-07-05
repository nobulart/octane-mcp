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
    likely_blank = contrast < 2.0 or near_black > 98.0
    likely_clipped = near_white > 98.0

    result.update(
        {
            "dimensions": [width, height],
            "mean_brightness": _round3(mean),
            "contrast": _round3(contrast),
            "near_black_percent": _round3(near_black),
            "near_white_percent": _round3(near_white),
            "edge_density": _round3(edge_density),
            "likely_blank": likely_blank,
            "likely_clipped": likely_clipped,
        }
    )
    if likely_blank:
        result["issues"].append("mostly near-black" if near_black > 98.0 else "very low contrast")
    if likely_clipped:
        result["issues"].append("mostly near-white")
    result["ok"] = not result["issues"]
    return result
