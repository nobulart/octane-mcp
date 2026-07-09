"""Pixel-level acceptance checks for benchmark renders.

No vision model is used. Every check operates on raw decoded RGB pixels via the
stdlib PNG reader in ``octanex_mcp.review`` (which depends only on ``struct`` /
``zlib``). This is deliberate: hallucinating vision models have previously
reported empty renders as correct (see docs/recipe-book.md chess-pawn entry), so
the authoritative signal is always the pixel data itself.

Public entry point: ``evaluate_acceptance(path, criteria) -> (passed, report)``
where ``report`` is a list of per-criterion result dicts.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from octanex_mcp.review import review_preview


def _decode(path: Path) -> tuple[int, int, list[tuple[int, int, int]]]:
    from octanex_mcp.review import _read_png_pixels

    return _read_png_pixels(path)


def _mean_dev_and_nonbg(pixels: list[tuple[int, int, int]], bg: tuple[int, int, int]) -> tuple[float, float]:
    n = len(pixels) or 1
    dev_sum = 0.0
    nonbg = 0
    for (r, g, b) in pixels:
        dev = abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2])
        dev_sum += dev
        if dev > 30:
            nonbg += 1
    return dev_sum / n, 100.0 * nonbg / n


def _color_fraction(
    pixels: list[tuple[int, int, int]],
    target: list[float],
    tol: float,
) -> float:
    tr, tg, tb = [int(round(c * 255)) for c in target]
    thr = max(1, int(round(tol * 255)))
    n = len(pixels) or 1
    hit = 0
    for (r, g, b) in pixels:
        if abs(r - tr) <= thr and abs(g - tg) <= thr and abs(b - tb) <= thr:
            hit += 1
    return hit / n


def _shape_profile_rows(
    pixels: list[tuple[int, int, int]],
    width: int,
    height: int,
) -> int:
    """Count rows that contain foreground silhouette structure (a proxy for
    an upright/structured subject rather than a featureless blob)."""
    if width < 4 or height < 4:
        return 0
    # per-row median background, then mark deviating columns
    step_y = max(1, height // 80)
    step_x = max(1, width // 160)
    rows_with_structure = 0
    for y in range(0, height, step_y):
        vals = sorted(
            (pixels[y * width + x][0] + pixels[y * width + x][1] + pixels[y * width + x][2]) // 3
            for x in range(0, width, step_x)
        )
        row_bg = vals[len(vals) // 2]
        cols = sum(
            1
            for x in range(0, width, step_x)
            if abs((pixels[y * width + x][0] + pixels[y * width + x][1] + pixels[y * width + x][2]) // 3 - row_bg) > 18
        )
        if cols >= 2:
            rows_with_structure += 1
    return rows_with_structure


def _check_non_empty(pixels, bg, crit: dict[str, Any]) -> dict[str, Any]:
    mean_dev, nonbg = _mean_dev_and_nonbg(pixels, bg)
    ok = mean_dev >= crit.get("min_mean_dev", 1.0) and nonbg >= crit.get("min_nonbg", 1.0)
    return {"passed": ok, "mean_dev": round(mean_dev, 2), "nonbg_pct": round(nonbg, 2),
            "thresholds": {"min_mean_dev": crit.get("min_mean_dev", 1.0), "min_nonbg": crit.get("min_nonbg", 1.0)}}


def _check_review_ok(path: Path, crit: dict[str, Any]) -> dict[str, Any]:
    review = review_preview(path)
    fail_on = set(crit.get("fail_on", []))
    issues = review.get("issues", [])
    triggered = [i for i in issues if i in fail_on]
    return {"passed": not triggered, "issues": issues, "fail_on": sorted(fail_on),
            "triggered": triggered, "ok": review.get("ok", False)}


def _rgb_to_hue(rgb: tuple[int, int, int]) -> float:
    """Return hue in degrees [0,360) for an 0-255 RGB triple (HSV hue)."""
    r, g, b = [c / 255.0 for c in rgb]
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if d < 1e-6:
        return 0.0
    if mx == r:
        h = (g - b) / d + (6 if g < b else 0)
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return (h * 60.0) % 360.0


def _hue_distance(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def _check_color_family(pixels, crit: dict[str, Any]) -> dict[str, Any]:
    """Verify the dominant non-background hue belongs to a target hue family.

    More robust than exact-RGB ``color_present`` for lit PBR: Octane colour
    management + studio lighting legitimately shift value/saturation, but the
    *hue* of a correctly-assigned material stays in family. ``target`` is an
    sRGB 0-1 triple; ``hue_tol`` (deg, default 35) is the allowed hue distance
    for a pixel to count; ``min_fraction`` is the fraction of non-bg pixels that
    must fall in-family.
    """
    tr, tg, tb = [int(round(c * 255)) for c in crit["target"]]
    target_hue = _rgb_to_hue((tr, tg, tb))
    hue_tol = crit.get("hue_tol", 35.0)
    min_fraction = crit.get("min_fraction", 0.02)
    bg = pixels[0]
    in_family = 0
    nonbg = 0
    for (r, g, b) in pixels:
        if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) <= 30:
            continue
        nonbg += 1
        if _hue_distance(_rgb_to_hue((r, g, b)), target_hue) <= hue_tol:
            in_family += 1
    frac = in_family / nonbg if nonbg else 0.0
    ok = frac >= min_fraction
    return {"passed": ok, "hue_family_fraction": round(frac, 4),
            "target_hue": round(target_hue, 1), "hue_tol": hue_tol,
            "min_fraction": min_fraction, "nonbg": nonbg}


def _check_color_present(pixels, crit: dict[str, Any]) -> dict[str, Any]:
    frac = _color_fraction(pixels, crit["target"], crit.get("tol", 0.18))
    ok = frac >= crit.get("min_fraction", 0.01)
    return {"passed": ok, "fraction": round(frac, 4), "target": crit["target"],
            "tol": crit.get("tol", 0.18), "min_fraction": crit.get("min_fraction", 0.01)}


def _check_color_absent(pixels, crit: dict[str, Any]) -> dict[str, Any]:
    frac = _color_fraction(pixels, crit["target"], crit.get("tol", 0.18))
    ok = frac <= crit.get("max_fraction", 0.0)
    return {"passed": ok, "fraction": round(frac, 4), "max_fraction": crit.get("max_fraction", 0.0)}


def _check_shape_profile(pixels, width, height, crit: dict[str, Any]) -> dict[str, Any]:
    rows = _shape_profile_rows(pixels, width, height)
    ok = rows >= crit.get("min_rows", 6)
    return {"passed": ok, "rows_with_structure": rows, "min_rows": crit.get("min_rows", 6)}


def _check_bright_fraction(pixels, crit: dict[str, Any]) -> dict[str, Any]:
    near_white = sum(1 for (r, g, b) in pixels if r >= 247 and g >= 247 and b >= 247)
    frac = 100.0 * near_white / (len(pixels) or 1)
    ok = frac >= crit.get("min_near_white", 3.0)
    return {"passed": ok, "near_white_pct": round(frac, 2), "min_near_white": crit.get("min_near_white", 3.0)}


def _check_file_size(path: Path, crit: dict[str, Any]) -> dict[str, Any]:
    size = path.stat().st_size if path.exists() else 0
    ok = size >= crit.get("min_bytes", 1000)
    return {"passed": ok, "bytes": size, "min_bytes": crit.get("min_bytes", 1000)}


def evaluate_acceptance(
    path: str | Path,
    criteria: list[dict[str, Any]],
    *,
    wait_seconds: float = 20.0,
    poll: float = 0.25,
) -> dict[str, Any]:
    """Evaluate a list of acceptance criteria against a saved PNG.

    Octane's ``saveImage`` returns before the PNG is fully flushed to disk, so a
    caller that reads immediately can hit a truncated-IDAT decode error
    (``Error -5 ... incomplete or truncated stream``) even though the final file
    is valid. We therefore retry the decode until the file stabilizes or
    ``wait_seconds`` elapses; only a persistent decode failure is reported as an
    error.

    Returns:
        {"passed": bool, "path": str, "decoded": bool, "checks": [per-criterion dict]}
    """
    p = Path(path)
    result: dict[str, Any] = {"passed": False, "path": str(p), "exists": p.exists(), "checks": []}
    if not p.exists() or p.stat().st_size == 0:
        for crit in criteria:
            c = {"kind": crit.get("kind"), "passed": False, "error": "png missing or empty"}
            result["checks"].append(c)
        return result

    width = height = pixels = None
    last_exc: Exception | None = None
    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        try:
            width, height, pixels = _decode(p)
            last_exc = None
            break
        except Exception as exc:  # noqa: BLE001 - transient until flush completes
            last_exc = exc
            time.sleep(poll)
    if pixels is None:
        result["decoded"] = False
        result["error"] = str(last_exc)
        for crit in criteria:
            result["checks"].append({"kind": crit.get("kind"), "passed": False, "error": str(last_exc)})
        return result

    result["decoded"] = True
    bg = pixels[0]
    for crit in criteria:
        kind = crit.get("kind")
        if kind == "non_empty":
            c = _check_non_empty(pixels, bg, crit)
        elif kind == "review_ok":
            c = _check_review_ok(p, crit)
        elif kind == "color_present":
            c = _check_color_present(pixels, crit)
        elif kind == "color_family":
            c = _check_color_family(pixels, crit)
        elif kind == "color_absent":
            c = _check_color_absent(pixels, crit)
        elif kind == "shape_profile":
            c = _check_shape_profile(pixels, width, height, crit)
        elif kind == "bright_fraction":
            c = _check_bright_fraction(pixels, crit)
        elif kind == "file_size":
            c = _check_file_size(p, crit)
        else:
            c = {"kind": kind, "passed": False, "error": f"unknown criterion {kind!r}"}
        c["kind"] = kind
        result["checks"].append(c)

    result["passed"] = all(c.get("passed") for c in result["checks"])
    return result


def summarize(report: dict[str, Any]) -> str:
    """One-line-ish human summary of an acceptance report (for chat output)."""
    if not report.get("exists", False):
        return f"  ✗ PNG missing/empty: {report['path']}"
    if not report.get("decoded", False):
        return f"  ✗ decode error: {report.get('error')}"
    lines = []
    for c in report["checks"]:
        icon = "✓" if c.get("passed") else "✗"
        detail = {k: v for k, v in c.items() if k not in ("kind", "passed")}
        lines.append(f"  {icon} {c['kind']}: {detail}")
    verdict = "PASS" if report["passed"] else "FAIL"
    return f"  [{verdict}] " + "; ".join(f"{c['kind']}={'ok' if c.get('passed') else 'X'}" for c in report["checks"])
