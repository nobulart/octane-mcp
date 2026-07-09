"""Verify the checked-in recipe library against native Octane.

This is the direction-A deliverable from the 2026-07-09 brainstorm: the benchmark
suite proves 18/18 tasks render natively, but only 2/18 *recipes* carry
``native_octane_verified=true`` — the other 16 ship a *reference* preview, not a
verified native Octane output. This module closes that gap honestly:

  * **offline** (``--dry-run`` / ``verify_recipe_library(dry_run=True)``): checks
    the *reproducibility contract* of every recipe — valid scene.json, schema-valid
    commands, a mirrorable OBJ, assets present, and no T3–6-style render blockers
    (notably a ``start_render`` emitted immediately before ``save_preview``, which
    is pitfall #9/#10). No Octane required.
  * **live** (``OCTANEX_LIVE=1 --live``): mirrors each recipe OBJ into the Octane
    sandbox, rewrites ``import_geometry`` + ``save_preview`` paths to the container
    FS (pitfall #14), drops the collision-prone ``start_render``, queues, drains the
    one-shot bridge, and evaluates the rendered PNG with pixel-based acceptance
    (no vision model — see ``benchmarks/acceptance.py``).

Reuse, don't re-implement:
  * OBJ mirroring + path rewriting mirror ``benchmarks/harness._queue_from_spec``
    and ``octanex_mcp.recipes._rewrite_preview_outputs``.
  * Drain + pixel acceptance reuse ``benchmarks.harness.drain_oneshot`` and
    ``benchmarks.acceptance.evaluate_acceptance``.

Promotion (copying the container PNG back into the recipe dir + flipping
``native_octane_verified``) is **opt-in** via ``copy_back=True`` and is NEVER done
silently — a recipe is only marked verified when a real native PNG has been rendered
and passed pixel acceptance.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from octanex_mcp.bridge import Workspace, write_command
from octanex_mcp.config import resolve_config
from octanex_mcp.recipes import (
    RECIPES_ROOT,
    _find_recipe_dir,
    _read_scene_json,
    _resolved_commands,
)

import benchmarks.acceptance as acceptance
from benchmarks.harness import drain_oneshot


# Review issues that always disqualify a recipe render (mirrors benchmark acceptance).
_DISQUALIFYING_ISSUES = [
    "mostly near-black",
    "very low contrast",
    "likely object too small",
    "mostly near-white",
    "likely object clipped at frame edge",
]


@dataclass
class RecipeRun:
    slug: str
    title: str
    domain: str
    obj_mirrored: bool = False
    queued: int = 0
    preview_path: Path | None = None
    acceptance: dict[str, Any] | None = None
    contract_ok: bool = False
    contract_errors: list[str] = field(default_factory=list)
    contract_warnings: list[str] = field(default_factory=list)
    error: str | None = None
    duration_seconds: float = 0.0
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.title,
            "domain": self.domain,
            "obj_mirrored": self.obj_mirrored,
            "queued": self.queued,
            "preview_path": str(self.preview_path) if self.preview_path else None,
            "contract_ok": self.contract_ok,
            "contract_errors": self.contract_errors,
            "contract_warnings": self.contract_warnings,
            "passed": bool(self.acceptance and self.acceptance.get("passed")),
            "acceptance": self.acceptance,
            "error": self.error,
            "duration_seconds": round(self.duration_seconds, 2),
            "notes": self.notes,
        }


def derive_criteria(slug: str, data: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Default pixel acceptance for a recipe render.

    Rejects blank/collided frames via ``non_empty`` + ``review_ok``. Recipes may
    optionally declare their own ``acceptance`` list in scene.json to override.
    Kept deliberately simple — the authoritative signal is always raw pixels, never
    a vision model.
    """
    explicit = data.get("acceptance")
    if isinstance(explicit, list) and explicit:
        return list(explicit)
    return [
        {"kind": "non_empty", "min_mean_dev": 2.0, "min_nonbg": 2.0},
        {"kind": "review_ok", "fail_on": list(_DISQUALIFYING_ISSUES)},
    ]


def _check_contract(slug: str, recipe_dir: Path, data: Mapping[str, Any]) -> tuple[bool, list[str], list[str], Path | None]:
    """Offline reproducibility contract. Returns (ok, errors, warnings, obj_path)."""
    errors: list[str] = []
    warnings: list[str] = []
    obj_path: Path | None = None

    if not (recipe_dir / "scene.obj").exists():
        errors.append("missing scene.obj")
    else:
        obj_path = recipe_dir / "scene.obj"

    if not (recipe_dir / "scene.mtl").exists():
        errors.append("missing scene.mtl")

    commands = _resolved_commands(data)
    if not commands:
        errors.append("commands must not be empty")
    else:
        prev_op = None
        for cmd in commands:
            op = cmd.get("op")
            # pitfall #9/#10: start_render immediately before save_preview collides
            # with the render-restart loop and aborts saveImage. The live runner
            # strips it (matching the benchmark harness), so this is a *warning*,
            # not a hard failure — every unverified recipe currently does this.
            if prev_op == "start_render" and op == "save_preview":
                warnings.append("start_render emitted immediately before save_preview (pitfall #9/#10); live runner strips it")
            prev_op = op
        if prev_op != "save_preview":
            errors.append("no save_preview command")

    # schema-validate the queued command sequence the way queue_recipe would
    from octanex_mcp.schema import SCHEMA_VERSION, validate_command  # local import: avoids cycle noise at module load

    for idx, cmd in enumerate(commands):
        envelope = {
            "schema_version": SCHEMA_VERSION,
            "id": f"verify-{slug}-{idx}",
            "op": cmd.get("op"),
            "payload": cmd.get("payload") or {},
            "created_at": "2026-01-01T00:00:00Z",
            "source": "octanex-mcp",
        }
        result = validate_command(envelope)
        if not result.ok:
            errors.append(f"invalid command {idx} ({cmd.get('op')}): " + "; ".join(result.errors))

    # A target/reference preview must exist (proof the recipe intends real output)
    has_ref = any((recipe_dir / name).exists() for name in ("preview.png", "photoreal-preview.png", "octane-preview.png"))
    if not has_ref:
        errors.append("no preview.png / photoreal-preview.png / octane-preview.png reference")

    return (not errors), errors, warnings, obj_path


def run_recipe(
    slug: str,
    *,
    container: Path | None = None,
    dry_run: bool = False,
    drain: bool = True,
    drain_timeout: float = 120.0,
    quality: str | None = None,
    copy_back: bool = False,
) -> RecipeRun:
    """Run one recipe's scene.json end-to-end (or up to the dry_run boundary).

    Live path mirrors the OBJ into the container, rewrites import/save paths to the
    container FS, drops the collision-prone ``start_render``, queues, optionally
    drains, and evaluates the rendered PNG with pixel acceptance. ``copy_back``
    copies the container PNG into the recipe dir and flips ``native_octane_verified``
    — opt-in only, never silent.
    """
    start = time.time()
    recipe_dir = _find_recipe_dir(slug)
    data = _read_scene_json(recipe_dir / "scene.json")
    run = RecipeRun(slug=slug, title=str(data.get("title") or slug), domain=str(data.get("domain") or data.get("category") or "uncategorized"))

    cfg = resolve_config()
    ws = Workspace(root=container or cfg.workspace)
    ws.ensure()

    contract_ok, contract_errors, contract_warnings, obj_path = _check_contract(slug, recipe_dir, data)
    run.contract_ok = contract_ok
    run.contract_errors = contract_errors
    run.contract_warnings = contract_warnings
    if not contract_ok:
        run.error = "contract failed: " + "; ".join(contract_errors)
        run.duration_seconds = time.time() - start
        return run

    assert obj_path is not None
    # Mirror OBJ into container assets/ (pitfall #14: Octane cannot read repo paths)
    obj_dst = ws.assets_dir / f"recipe_{slug}.obj"
    obj_dst.write_text(obj_path.read_text(encoding="utf-8"))
    run.obj_mirrored = True

    commands = _resolved_commands(data)
    # Per-recipe unique preview filename so concurrent/sequential batches don't
    # clobber each other's PNG (recipe scene.json paths name "octane-preview.png",
    # which would collide across recipes otherwise).
    preview_filename = f"recipe_{slug}_octane-preview.png"
    for cmd in commands:
        op = cmd.get("op")
        p = cmd.setdefault("payload", {})
        if op == "import_geometry":
            p["path"] = str(obj_dst)
        elif op == "start_render":
            cmd["_drop"] = True  # strip collision-prone op
        elif op == "save_preview":
            original = str(p.get("path") or "")
            p["bundle_path"] = str(recipe_dir / "octane-preview.png")
            p["path"] = str((ws.renders_dir / preview_filename).resolve())
            if quality:
                p["quality"] = quality
    commands = [c for c in commands if not c.get("_drop")]

    for idx, cmd in enumerate(commands):
        write_command(str(cmd["op"]), dict(cmd.get("payload") or {}), ws)
    run.queued = len(commands)
    run.preview_path = (ws.renders_dir / preview_filename).resolve()
    run.notes.append("queued; start_render stripped; paths rewritten to container FS")

    if dry_run:
        run.notes.append("dry_run: stopped after queueing (no drain/verify)")
        run.duration_seconds = time.time() - start
        return run
    if not drain:
        run.notes.append("drain deferred")
        run.duration_seconds = time.time() - start
        return run

    drain_result = drain_oneshot(ws, timeout_seconds=max(30, int(drain_timeout)))
    if not drain_result.get("ok"):
        run.error = f"drain failed: {drain_result.get('error')}"
        run.duration_seconds = time.time() - start
        return run

    waited = 0.0
    while not (run.preview_path and run.preview_path.exists()) and waited < 15.0:
        time.sleep(1.0)
        waited += 1.0

    if run.preview_path and run.preview_path.exists():
        criteria = derive_criteria(slug, data)
        run.acceptance = acceptance.evaluate_acceptance(run.preview_path, criteria)
        if copy_back and run.acceptance.get("passed"):
            _promote(recipe_dir, data, run.preview_path)
            run.notes.append("promoted: PNG copied to recipe dir + native_octane_verified=true")
    else:
        run.error = "preview not written by bridge"
        run.acceptance = acceptance.evaluate_acceptance(run.preview_path or Path("/nonexistent.png"), derive_criteria(slug, data))

    run.duration_seconds = time.time() - start
    return run


def _promote(recipe_dir: Path, data: Mapping[str, Any], container_png: Path) -> None:
    """Copy the rendered PNG into the recipe dir and flip the verified flag."""
    dest = recipe_dir / "octane-preview.png"
    dest.write_bytes(container_png.read_bytes())
    updated = dict(data)
    updated["native_octane_verified"] = True
    updated["status"] = f"native_octane_verified (verify_recipes, {time.strftime('%Y-%m-%d')})"
    (recipe_dir / "scene.json").write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")


def verify_recipe_library(
    *,
    recipes_root: Path = RECIPES_ROOT,
    container: Path | None = None,
    dry_run: bool = True,
    live: bool = False,
    drain_timeout: float = 120.0,
    copy_back: bool = False,
    slug: str | None = None,
) -> dict[str, Any]:
    """Verify the recipe library.

    dry_run=True: offline contract check only (default).
    live=True (requires ``OCTANEX_LIVE=1``): mirror + queue + drain + pixel-accept.
    """
    if live and os.environ.get("OCTANEX_LIVE") != "1":
        raise RuntimeError("live verification requires OCTANEX_LIVE=1 (and a running Octane X)")

    from octanex_mcp.recipes import _recipe_dirs

    dirs = _recipe_dirs(recipes_root)
    if slug:
        dirs = [d for d in dirs if d.name == slug or (d / "scene.json").exists() and _read_scene_json(d / "scene.json").get("slug") == slug]
        if not dirs:
            raise ValueError(f"unknown recipe slug {slug!r}")

    runs: list[RecipeRun] = []
    for recipe_dir in dirs:
        data = _read_scene_json(recipe_dir / "scene.json")
        s = str(data.get("slug") or recipe_dir.name)
        if live:
            runs.append(run_recipe(s, container=container, dry_run=False, drain_timeout=drain_timeout, copy_back=copy_back))
        else:
            r = RecipeRun(slug=s, title=str(data.get("title") or s), domain=str(data.get("domain") or data.get("category") or "uncategorized"))
            ok, errs, warns, _ = _check_contract(s, recipe_dir, data)
            r.contract_ok = ok
            r.contract_errors = errs
            r.contract_warnings = warns
            if not ok:
                r.error = "contract failed: " + "; ".join(errs)
            runs.append(r)

    contract_ok = sum(1 for r in runs if r.contract_ok)
    passed = sum(1 for r in runs if r.acceptance and r.acceptance.get("passed"))
    return {
        "mode": "live" if live else "dry_run",
        "total": len(runs),
        "contract_ok": contract_ok,
        "contract_failed": len(runs) - contract_ok,
        "passed": passed if live else None,
        "recipes": [r.as_dict() for r in runs],
    }


def _main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Verify the OctaneX MCP recipe library")
    ap.add_argument("--live", action="store_true", help="render live in Octane (requires OCTANEX_LIVE=1)")
    ap.add_argument("--dry-run", action="store_true", help="offline contract check only (default)")
    ap.add_argument("--slug", help="verify a single recipe by slug")
    ap.add_argument("--copy-back", action="store_true", help="copy rendered PNG into recipe dir + flip verified flag (live only)")
    ap.add_argument("--drain-timeout", type=float, default=120.0)
    args = ap.parse_args()

    live = args.live
    report = verify_recipe_library(
        dry_run=not live,
        live=live,
        slug=args.slug,
        copy_back=args.copy_back,
        drain_timeout=args.drain_timeout,
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    _main()
