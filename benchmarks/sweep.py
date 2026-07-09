"""Sequential live sweep of the recipe library, honest promotion.

Direction-A deliverable. One recipe at a time, container queue cleared between
runs to avoid stale state, native render allowed to converge (up to
--png-wait seconds), and native_octane_verified flipped ONLY when the rendered
PNG passes pixel acceptance (benchmarks.acceptance.evaluate_acceptance).

Design notes
------------
* We do NOT use run_recipe(drain=True): its internal drain_oneshot returns
  "drain failed" if the queue has not fully emptied within drain_timeout, but a
  slow native render keeps processing after Python returns, so the PNG may still
  appear later. Instead we queue with drain=False, click the one-shot bridge
  ONCE (the Lua drain loop processes the entire queue and runs the final
  save_preview render in a single pass), then poll for the PNG.
* The one-shot drain is NOT re-clicked on a timer. A second click while
  save_preview's render is active is ignored, and re-clicking after the queue
  empties would restart/kill that render. We only re-click on a genuine failed
  click (TCC-denied / app-busy), capped.
* Per-recipe results are flushed to --results incrementally so a crash mid-sweep
  loses at most the in-flight recipe.

Usage
-----
    uv run python benchmarks/sweep.py \
        --png-wait 600 --results benchmarks/sweep_results.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import time
from pathlib import Path

from octanex_mcp.bridge import Workspace, resolve_config
from octanex_mcp.bridge_control import reset_octane_scene, run_bridge_script
from octanex_mcp.recipes import _find_recipe_dir, _read_scene_json, _recipe_dirs

import benchmarks.acceptance as acceptance
from benchmarks.verify_recipes import derive_criteria, run_recipe, _promote

CONTAINER = os.path.expanduser(
    "~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP"
)


def _clear_container() -> None:
    for sub in ("queue", "processed", "failed"):
        for f in glob.glob(os.path.join(CONTAINER, sub, "*.json")):
            try:
                os.remove(f)
            except OSError:
                pass
    log = os.path.join(CONTAINER, "bridge.log")
    try:
        open(log, "w").close()
    except OSError:
        pass


def _clear_stale_preview(preview_path: str) -> None:
    """Delete any pre-existing preview PNG so we can only trust a FRESHLY
    rendered file (mtime > run start). This is the guard that prevents the
    sweep from 'passing' a stale blank frame left by a previous run."""
    try:
        if os.path.exists(preview_path):
            os.remove(preview_path)
    except OSError:
        pass


def _queue_count() -> int:
    return len(glob.glob(os.path.join(CONTAINER, "queue", "*.json")))


def _click_oneshot(timeout_seconds: int = 40) -> dict | None:
    """Run the one-shot bridge once. Returns the run_bridge_script result dict
    (so callers can branch on ok/tcc_blocked/busy) or None on unexpected error."""
    try:
        return run_bridge_script("oneshot", timeout_seconds=timeout_seconds)
    except Exception as exc:  # noqa: BLE001
        print(f"  [warn] oneshot click failed: {exc!r}")
        return None


def _reset_octane_scene() -> dict:
    """Reset Octane X to a fresh scene via File > New (warm-engine rule).

    A sequential sweep must NOT carry stale scene-graph nodes between recipes;
    request_render_restart wedges on mixed state otherwise. This uses the
    shared, hardened AppleScript helper (TCC-classified errors, no dup script).
    Returns {ok, error}.
    """
    return reset_octane_scene()


def sweep_one(slug: str, *, png_wait: int, quality: str | None) -> dict:
    """Queue one recipe, drain, wait for PNG, evaluate + promote if passed."""
    recipe_dir = _find_recipe_dir(slug)
    data = _read_scene_json(recipe_dir / "scene.json")
    result: dict = {
        "slug": slug,
        "title": str(data.get("title") or slug),
        "domain": str(data.get("domain") or data.get("category") or "uncategorized"),
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "queued": False,
        "preview_exists": False,
        "acceptance": None,
        "promoted": False,
        "error": None,
        "notes": [],
    }
    try:
        # Reset the Octane scene to a fresh graph so request_render_restart
        # does not wedge on stale nodes left by the previous recipe.
        reset = _reset_octane_scene()
        if not reset["ok"]:
            result["error"] = f"scene reset failed: {reset['error']}"
            result["notes"].append("scene reset FAILED — aborting to avoid wedge")
            return result
        _clear_container()
        # Queue only (rewrites container paths, strips start_render).
        run = run_recipe(
            slug, dry_run=False, drain=False, copy_back=False, quality=quality or "preview"
        )
        result["queued"] = run.queued > 0
        result["preview_path"] = str(run.preview_path)
        if run.error:
            result["error"] = f"queue error: {run.error}"
            return result

        # GUARD: remove any pre-existing preview PNG so we can only trust a
        # FRESH render (file created/updated AFTER this point in time).
        _clear_stale_preview(str(run.preview_path))
        run_start = time.time()

        png = run.preview_path
        waited = 0.0
        last_click = time.time()
        fresh = False
        max_clicks = 6
        clicks = 0
        # Drain model (verified end-to-end): a SINGLE oneshot click runs the
        # Lua drain loop, which processes EVERY queued command (assembly +
        # save_preview) in one pass, then starts the single real render and
        # saves the frame. We then POLL for the queue to empty and a FRESH PNG.
        # We do NOT re-click on a timer — a second click while Octane is busy
        # in the save_preview render is ignored, and re-clicking after the
        # queue empties would restart/kill that in-progress render. We only
        # re-click on a genuine launch/click failure (TCC-denied or app-busy),
        # capped at max_clicks to avoid a click storm.
        result_click = _click_oneshot()
        clicks += 1
        while waited < png_wait:
            time.sleep(5)
            waited += 5.0
            qc = _queue_count()
            if png and Path(png).exists() and os.path.getmtime(png) >= run_start - 1.0:
                fresh = True
            # Done: queue empty AND a fresh frame exists.
            if qc == 0 and fresh:
                break
            # Only re-nudge if the last click actually failed (not busy) and we
            # still have click budget. A busy/failed click here is a real
            # control problem, not a render-in-progress — so a re-click is safe.
            failed = isinstance(result_click, dict) and not result_click.get("ok")
            if failed and qc > 0 and (time.time() - last_click) >= 6.0 and clicks < max_clicks:
                result_click = _click_oneshot()
                clicks += 1
                last_click = time.time()
            # If queue is empty but no fresh PNG yet, just wait (render finishing).
        result["clicks"] = clicks

        if not fresh or not (png and Path(png).exists()):
            result["error"] = (
                f"no FRESH preview written within {png_wait}s "
                f"(queue_left={_queue_count()}; stale file or never rendered)"
            )
            return result

        result["preview_exists"] = True
        result["render_seconds"] = round(time.time() - run_start, 1)
        criteria = derive_criteria(slug, data)
        acc = acceptance.evaluate_acceptance(Path(png), criteria)
        # Capture REAL numeric metrics for audit (never trust a pass without these).
        # evaluate_acceptance returns {passed, exists, decoded, checks:[...]}; the
        # numeric signal lives in acc["checks"] (each has mean_dev / nonbg_pct / etc).
        metrics = {
            "passed": acc.get("passed"),
            "exists": acc.get("exists"),
            "decoded": acc.get("decoded"),
            "checks": acc.get("checks", []),
            "error": acc.get("error"),
        }
        try:
            from benchmarks.png_stats import stats as _png_stats

            ps = _png_stats(str(png))
            metrics["png_stats"] = {
                "mean_rgb": [round(x, 1) for x in ps.get("mean", [])],
                "nonbg_pct": round(ps.get("nonbg", 0.0), 2),
                "edge_energy": round(ps.get("edge_mean", 0.0), 3),
            }
        except Exception as exc:  # noqa: BLE001
            metrics["png_stats_error"] = f"{type(exc).__name__}: {exc}"
        result["acceptance"] = metrics
        # NOTE: do NOT reject on a fast render_seconds — Octane can produce a
        # recognisable simple-scene preview in under 1s (see agent-quickstart).
        # The fresh-mtime gate above already blocks stale-file fraud.
        if acc.get("passed"):
            _promote(recipe_dir, data, Path(png))
            result["promoted"] = True
            result["notes"].append("promoted: PNG + native_octane_verified=true")
        else:
            result["notes"].append("NOT promoted: pixel acceptance failed")
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"{type(exc).__name__}: {exc}"
    result["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return result


def _main() -> None:
    ap = argparse.ArgumentParser(description="Sequential honest recipe sweep")
    ap.add_argument("--png-wait", type=int, default=600)
    ap.add_argument("--quality", default=None, help="optional save_preview quality tier")
    ap.add_argument("--results", default="benchmarks/sweep_results.json")
    ap.add_argument("--slugs", nargs="*", help="optional slug subset (priority first)")
    args = ap.parse_args()

    # Default: priority subset first, then the rest.
    priority = [
        "network-graph", "pca-3d", "correlation-heatmap",
        "scatter-plot", "data-bars", "histogram",
    ]
    all_dirs = _recipe_dirs()
    all_slugs = []
    for d in all_dirs:
        sd = _read_scene_json(d / "scene.json")
        all_slugs.append(str(sd.get("slug") or d.name))
    if args.slugs:
        slugs = args.slugs
    else:
        slugs = [s for s in priority if s in all_slugs] + [
            s for s in all_slugs if s not in priority
        ]

    results: list[dict] = []
    for slug in slugs:
        print(f"[sweep] {slug} ...", flush=True)
        r = sweep_one(slug, png_wait=args.png_wait, quality=args.quality)
        results.append(r)
        # Incremental flush.
        Path(args.results).write_text(json.dumps(results, indent=2), encoding="utf-8")
        status = "PROMOTED" if r["promoted"] else ("FAIL" if r["error"] else "rendered-not-promoted")
        print(f"[sweep] {slug} -> {status} ({r.get('finished_at')})", flush=True)

    passed = sum(1 for r in results if r["acceptance"] and r["acceptance"].get("passed"))
    promoted = sum(1 for r in results if r["promoted"])
    print(f"\n[sweep] done: {len(results)} recipes, {passed} pixel-passed, {promoted} promoted", flush=True)


if __name__ == "__main__":
    _main()
