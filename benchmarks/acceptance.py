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

import math
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
    min_frac = crit.get("min_near_white", 3.0)
    max_frac = crit.get("max_near_white", None)
    ok = frac >= min_frac and (max_frac is None or frac <= max_frac)
    return {"passed": ok, "near_white_pct": round(frac, 2),
            "min_near_white": min_frac, "max_near_white": max_frac}


def _check_file_size(path: Path, crit: dict[str, Any]) -> dict[str, Any]:
    size = path.stat().st_size if path.exists() else 0
    ok = size >= crit.get("min_bytes", 1000)
    return {"passed": ok, "bytes": size, "min_bytes": crit.get("min_bytes", 1000)}


def evaluate_acceptance(path: str | Path, criteria: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate a list of acceptance criteria against a saved PNG.

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

    try:
        width, height, pixels = _decode(p)
    except Exception as exc:  # noqa: BLE001 - report any decode failure
        result["decoded"] = False
        result["error"] = str(exc)
        for crit in criteria:
            result["checks"].append({"kind": crit.get("kind"), "passed": False, "error": str(exc)})
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


# ---------------------------------------------------------------------------
# WP9 — Reference-anchored corpus expansion (pixel-only, no vision model)
# ---------------------------------------------------------------------------

# Guardrail set shared by review_ok and the harvest filter.
_DISQUALIFYING = [
    "mostly near-black",
    "very low contrast",
    "likely object too small",
    "mostly near-white",
    "likely object clipped at frame edge",
]


def _hue_families(pixels: list[tuple[int, int, int]], bg: tuple[int, int, int],
                  max_families: int = 3, max_rounds: int = 12,
                  min_inertia_drop: float = 1.0) -> list[dict[str, Any]]:
    """1-D k-means (by hue) over non-background pixels.

    Returns dominant hue families sorted by descending pixel count. Each entry
    is ``{"hue": float, "fraction": float}`` where ``fraction`` is of all
    non-background pixels.
    """
    nonbg = [p for p in pixels
             if abs(p[0] - bg[0]) + abs(p[1] - bg[1]) + abs(p[2] - bg[2]) > 30]
    if not nonbg:
        return []
    hues = sorted(_rgb_to_hue(p) for p in nonbg)
    n = len(hues)
    lo, hi = hues[0], hues[-1]
    if hi - lo >= 180.0:  # wrap-around cluster present; spread seeds around circle
        centers = [(hues[0] + 360.0 * (k + 0.5) / max_families) % 360.0
                   for k in range(max_families)]
    else:
        centers = [lo + (hi - lo) * (k + 0.5) / max_families for k in range(max_families)]
    centers = [c % 360.0 for c in centers]
    prev_inertia = None
    for _ in range(max_rounds):
        clusters: list[list[float]] = [[] for _ in centers]
        for h in hues:
            best = min(range(len(centers)), key=lambda i: _hue_distance(h, centers[i]))
            clusters[best].append(h)
        new_centers = []
        for i, cl in enumerate(clusters):
            if cl:
                # Circular mean for hue.
                s = sum(math.sin(math.radians(x)) for x in cl)
                c = sum(math.cos(math.radians(x)) for x in cl)
                new_centers.append(math.degrees(math.atan2(s, c)) % 360.0)
            else:
                new_centers.append(centers[i])
        inertia = sum(
            _hue_distance(h, centers[min(range(len(centers)),
                                         key=lambda i: _hue_distance(h, centers[i]))]) ** 2
            for h in hues
        )
        centers = [x % 360.0 for x in new_centers]
        if prev_inertia is not None and abs(prev_inertia - inertia) < min_inertia_drop:
            break
        prev_inertia = inertia
    counts: dict[float, int] = {round(c, 2): 0 for c in centers}
    for h in hues:
        best = min(counts, key=lambda k: _hue_distance(h, k))
        counts[best] += 1
    out = [{"hue": float(k), "fraction": round(v / n, 4)} for k, v in counts.items() if v > 0]
    out.sort(key=lambda d: d["fraction"], reverse=True)
    return out


def _hue_to_rgb(hue: float) -> list[float]:
    """Return an sRGB 0-1 triple for a pure hue (full saturation/value).

    Used only to express a derived hue family as a ``color_family`` target the
    existing ``evaluate_acceptance`` consumes (it converts the target back to
    hue internally, so value/saturation are irrelevant).
    """
    h = ((hue % 360.0) + 360.0) % 360.0
    c = 1.0
    x = c * (1 - abs((h / 60.0) % 2 - 1))
    if h < 60:
        r, g, b = c, x, 0.0
    elif h < 120:
        r, g, b = x, c, 0.0
    elif h < 180:
        r, g, b = 0.0, c, x
    elif h < 240:
        r, g, b = 0.0, x, c
    elif h < 300:
        r, g, b = x, 0.0, c
    else:
        r, g, b = c, 0.0, x
    return [round(r, 4), round(g, 4), round(b, 4)]


def reference_to_acceptance(reference_png: str | Path,
                           *, min_family_fraction: float = 0.05,
                           hue_tol: float = 35.0) -> dict[str, Any]:
    """Derive a pixel-only acceptance spec from a reference image.

    The spec is a list of criterion dicts consumable directly by
    ``evaluate_acceptance()`` — no vision model, no hand-authoring. It captures:

    * ``non_empty`` + ``review_ok`` — reject blank/clipped/busy references.
    * one ``color_family`` per dominant (non-background) hue family — the
      candidate render must reproduce the reference's dominant hues.
    * a ``bright_fraction`` band (min + max) to guard against blown-out or
      near-black references leaking through.
    * ``shape_profile`` tolerances derived from the reference's foreground
      structure, so a converged candidate must be comparably "structured".

    Returns ``{"acceptance": [...], "derived": {...}, "error": ...}``.
    """
    p = Path(reference_png)
    if not p.exists() or p.stat().st_size == 0:
        return {"acceptance": [], "derived": {}, "error": "reference missing or empty"}
    try:
        width, height, pixels = _decode(p)
    except Exception as exc:  # noqa: BLE001
        return {"acceptance": [], "derived": {}, "error": f"decode failed: {exc}"}

    review = review_preview(p)
    families = _hue_families(pixels, pixels[0])
    fg = review.get("foreground_bbox_area_percent", 0.0)
    edge = review.get("edge_density", 0.0)
    near_white = review.get("near_white_percent", 0.0)
    near_black = review.get("near_black_percent", 0.0)
    shape_rows = _shape_profile_rows(pixels, width, height)

    acceptance: list[dict[str, Any]] = [
        {"kind": "non_empty", "min_mean_dev": 2.0, "min_nonbg": 2.0},
        {"kind": "review_ok", "fail_on": list(_DISQUALIFYING)},
    ]
    for fam in families:
        if fam["fraction"] < min_family_fraction:
            continue
        acceptance.append({
            "kind": "color_family",
            "target": _hue_to_rgb(fam["hue"]),
            "hue_tol": hue_tol,
            "min_fraction": max(0.5 * fam["fraction"], 0.01),
            "_ref_fraction": fam["fraction"],
        })
    acceptance.append({"kind": "bright_fraction", "min_near_white": 0.0, "max_near_white": 95.0})
    acceptance.append({
        "kind": "shape_profile",
        # Require at least half the reference's structural rows, so a converged
        # candidate is comparably detailed (not a blank or a blob).
        "min_rows": max(3, int(shape_rows * 0.5)),
    })

    derived = {
        "hue_families": families,
        "foreground_bbox_area_percent": fg,
        "edge_density": edge,
        "near_black_percent": near_black,
        "near_white_percent": near_white,
        "shape_rows": shape_rows,
        "bright_fraction_band": [0.0, 95.0],
    }
    return {"acceptance": acceptance, "derived": derived}


def filter_reference(reference_png: str | Path, *,
                     max_near_black: float = 98.0,
                     min_contrast: float = 6.0,
                     max_near_white: float = 95.0,
                     max_edge_density: float = 80.0,
                     min_foreground_bbox_percent: float = 8.0,
                     max_foreground_bbox_percent: float = 85.0) -> dict[str, Any]:
    """Pixel-only harvest filter: reject unsuitable reference images.

    A reference is rejected (and must not enter the corpus) when it is:
      * near-black / low-contrast (blank-ish),
      * blown out (near-white clipping),
      * watermarked / busy (edge density too high — text/UI over the subject),
      * tiny / clipped (too little foreground),
      * a full-frame flat fill (foreground bbox occupies almost everything).

    All thresholds operate on ``review_preview`` stats — no vision model.

    Returns ``{"ok": bool, "reasons": [...], "stats": {...}}``.
    """
    p = Path(reference_png)
    if not p.exists() or p.stat().st_size == 0:
        return {"ok": False, "reasons": ["reference missing or empty"], "stats": {}}
    review = review_preview(p)
    stats = {
        "mean_brightness": review.get("mean_brightness"),
        "contrast": review.get("contrast"),
        "near_black_percent": review.get("near_black_percent"),
        "near_white_percent": review.get("near_white_percent"),
        "edge_density": review.get("edge_density"),
        "foreground_bbox_area_percent": review.get("foreground_bbox_area_percent"),
    }
    reasons: list[str] = []
    if review.get("near_black_percent", 0.0) > max_near_black:
        reasons.append("near-black / blank (likely object missing)")
    if review.get("contrast", 100.0) < min_contrast:
        reasons.append("very low contrast")
    if review.get("near_white_percent", 0.0) > max_near_white:
        reasons.append("blown out / clipped highlights")
    if review.get("edge_density", 100.0) > max_edge_density:
        reasons.append("too busy / watermarked (excessive edge density)")
    if review.get("foreground_bbox_area_percent", 0.0) < min_foreground_bbox_percent:
        reasons.append("subject too small / clipped")
    if review.get("foreground_bbox_area_percent", 100.0) > max_foreground_bbox_percent:
        reasons.append("flat full-frame fill (no distinct subject)")
    return {"ok": not reasons, "reasons": reasons, "stats": stats}


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
