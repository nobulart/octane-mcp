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
  (which drains the whole queue autonomously in Lua), then poll for the PNG.
* The one-shot drain is re-nudged if the queue is non-empty after a stall window.
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
from octanex_mcp.bridge_control import run_bridge_script
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


def _click_oneshot(timeout_seconds: int = 40) -> None:
    try:
        run_bridge_script("oneshot", timeout_seconds=timeout_seconds)
    except Exception as exc:  # noqa: BLE001
        print(f"  [warn] oneshot click failed: {exc!r}")


def _reset_octane_scene() -> dict:
    """Reset Octane X to a fresh scene via File > New (warm-engine rule).

    A sequential sweep must NOT carry stale scene-graph nodes between recipes;
    request_render_restart wedges on mixed state otherwise. This UI-scripts
    Octane's File menu (Hermes.app needs Accessibility/TCC, same as the bridge).
    Returns {ok, error}.
    """
    script = (
        'tell application "System Events"\n'
        '  if not (exists process "Octane X") then error "Octane X not running"\n'
        '  tell process "Octane X"\n'
        '    set frontmost to true\n'
        '    try\n'
        '      set _probe to count of menu bar items of menu bar 1\n'
        '    on error errMsg number errNum\n'
        '      if errNum is -1719 then error "assistive access denied (-1719)" number errNum\n'
        '      error errMsg number errNum\n'
        '    end try\n'
        '    click menu item "New" of menu 1 of menu bar item "File" of menu bar 1\n'
        '  end tell\n'
        'end tell\n'
    )
    import subprocess

    try:
        proc = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=20,
        )
        if proc.returncode == 0:
            return {"ok": True}
        err = (proc.stderr or proc.stdout or "").strip()
        if "-1719" in err:
            return {"ok": False, "error": "assistive access denied (-1719): grant Accessibility to Hermes.app"}
        return {"ok": False, "error": err or f"osascript rc={proc.returncode}"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


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
        max_clicks = 30
        clicks = 0
        # Drain loop: the one-shot bridge reliably drains only ~1 command per
        # launch, then exits. So we re-click aggressively (every ~6s) while the
        # queue is non-empty, until it empties. Once qc==0 we STOP clicking and
        # just wait for save_preview's in-progress render to write the PNG
        # (a click would restart/kill that render).
        _click_oneshot()
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
            # Keep draining while work remains (and we have click budget).
            if qc > 0 and (time.time() - last_click) >= 6.0 and clicks < max_clicks:
                _click_oneshot()
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
