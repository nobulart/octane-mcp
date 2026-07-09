"""Regenerate every recipe preview with an Octane reset between each.

The unverified-recipe sweep produced 18 files with distinct md5s but identical
decoded pixels (every PNG was the same blank gradient). Root cause: the oneshot
bridge was never reset between recipes, so Octane kept rendering the same stale
environment frame. Flipping 18 verified flags on that would be a false claim.

This driver makes the reset explicit and per-recipe:
  1. File > New  (warm-engine reset; clears the in-memory project + scripts)
  2. relaunch the oneshot bridge via the Scripts menu
  3. run_recipe(slug, copy_back=True)  (queue + drain + pixel-accept + promote)

Run with OCTANEX_LIVE=1 and a running Octane X. Each recipe's native PNG is
promoted (copied to recipe dir + native_octane_verified=true) ONLY if pixel
acceptance passes.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Make the repo importable when run via `uv run python benchmarks/regen_reset.py`
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from octanex_mcp.config import resolve_config  # noqa: E402
from octanex_mcp.bridge_control import reset_octane_scene, run_bridge_script  # noqa: E402
from octanex_mcp.recipes import RECIPES_ROOT, _recipe_dirs, _read_scene_json  # noqa: E402
from benchmarks.verify_recipes import run_recipe  # noqa: E402


def octane_running() -> bool:
    out = subprocess.run(
        ["pgrep", "-x", "Octane X"], capture_output=True, text=True
    ).stdout.strip()
    return bool(out)


def file_new_reset() -> None:
    """Warm-engine reset: File > New on the running Octane process.

    Uses the shared, hardened helper (TCC-classified errors, no duplicated
    inline AppleScript). The in-memory project + scripts are cleared; Octane
    then spins up a fresh (empty) project and auto-renders a frame.
    """
    reset = reset_octane_scene()
    if not reset.get("ok"):
        print(f"    [warn] File>New reset failed: {reset.get('error')}", file=sys.stderr)
    # Let the new (empty) project spin up and auto-render a frame.
    time.sleep(8)


def relaunch_bridge() -> None:
    cfg = resolve_config()
    result = run_bridge_script("oneshot", config=cfg)
    if not result.get("ok"):
        print(f"    [warn] oneshot relaunch failed: {result.get('error')}", file=sys.stderr)
    # Give the Lua bridge time to register before we queue commands.
    time.sleep(3)


def main() -> int:
    if os.environ.get("OCTANEX_LIVE") != "1":
        print("ERROR: set OCTANEX_LIVE=1 first", file=sys.stderr)
        return 2
    if not octane_running():
        print("ERROR: Octane X is not running", file=sys.stderr)
        return 2

    drain_timeout = float(os.environ.get("DRAIN_TIMEOUT", "90"))
    dirs = _recipe_dirs(RECIPES_ROOT)
    slugs = []
    for d in dirs:
        data = _read_scene_json(d / "scene.json")
        slugs.append(str(data.get("slug") or d.name))

    print(f"regenerating {len(slugs)} recipes with reset between each", file=sys.stderr)
    results = []
    for i, slug in enumerate(slugs):
        print(f"[{i+1}/{len(slugs)}] {slug}: File>New + relaunch bridge", file=sys.stderr)
        file_new_reset()
        relaunch_bridge()
        try:
            run = run_recipe(slug, dry_run=False, drain_timeout=drain_timeout, copy_back=True)
        except Exception as exc:  # noqa: BLE001 - record and continue
            results.append({"slug": slug, "error": f"{type(exc).__name__}: {exc}", "passed": False})
            continue
        d = run.as_dict()
        results.append(
            {
                "slug": slug,
                "queued": d["queued"],
                "passed": d["passed"],
                "error": d["error"],
                "acceptance": d["acceptance"],
                "notes": d["notes"],
            }
        )
        status = "OK" if d["passed"] else ("ERR " + str(d["error"] or "accept-fail"))
        print(f"    -> {status}", file=sys.stderr)

    passed = sum(1 for r in results if r.get("passed"))
    print(json.dumps({"total": len(results), "passed": passed, "recipes": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
