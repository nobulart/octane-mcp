"""OctaneX MCP benchmark harness.

Drives a benchmark task from deterministic spec to a verified native Octane
render. The harness:

  1. builds the scene spec (combined OBJ + materials + per-group assignments +
     camera + lighting + save settings) from benchmarks.spec;
  2. mirrors the OBJ into the Octane sandbox container workspace assets/ dir
     (pitfall #14: Octane cannot read host repo paths);
  3. queues the full command sequence into the container queue/ dir via the
     bridge's own write_command path;
  4. drains the queue with the one-shot Lua bridge (preferred for rendering,
     pitfall #18); the bridge writes the PNG to the absolute path we give
     save_preview;
  5. verifies the PNG with pixel-based acceptance checks (no vision model).

The harness is safe to run offline in a dry mode that stops after queueing, so
the same code path is unit-tested without a live Octane session.

Environment notes
-----------------
  * The container workspace is ``~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP``
    (resolved by octanex_mcp.config.resovle_config().workspace).
  * One-shot bridge drains ALL queued commands and does not release early, so
    it is the correct drain mode for a full end-to-end capture.
  * save_preview must be the FINAL op; do NOT also emit start_render before it
    (pitfall #9/#10).
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from octanex_mcp.bridge import Workspace, write_command
from octanex_mcp.config import resolve_config

import benchmarks.acceptance as acceptance
from benchmarks.spec import BenchmarkTask, get_task

DEFAULT_CONTAINER = Path(
    os.path.expanduser("~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP")
)


@dataclass
class TaskRun:
    slug: str
    tier: int
    title: str
    obj_path: Path | None = None
    queued: int = 0
    preview_path: Path | None = None
    acceptance: dict[str, Any] | None = None
    drain: dict[str, Any] | None = None
    error: str | None = None
    duration_seconds: float = 0.0
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "tier": self.tier,
            "title": self.title,
            "obj_path": str(self.obj_path) if self.obj_path else None,
            "queued": self.queued,
            "preview_path": str(self.preview_path) if self.preview_path else None,
            "passed": bool(self.acceptance and self.acceptance.get("passed")),
            "acceptance": self.acceptance,
            "drain": self.drain,
            "error": self.error,
            "duration_seconds": round(self.duration_seconds, 2),
            "notes": self.notes,
        }


def _queue_from_spec(spec: dict[str, Any], ws: Workspace, obj_abs_path: Path) -> list[dict[str, Any]]:
    """Materialize a task spec into a queued command sequence. Returns the
    queued command payloads in order (import -> materials -> assignments ->
    camera -> lighting -> save_preview)."""
    commands: list[tuple[str, dict[str, Any]]] = []
    commands.append(("import_geometry", {"path": str(obj_abs_path), "format": "obj", "name": spec["mesh_name"]}))
    for mat in spec["materials"]:
        payload = {k: mat[k] for k in mat if k in {
            "name", "kind", "color", "roughness", "metallic", "transmission",
            "ior", "opacity", "clearcoat", "anisotropy", "emission",
        } and mat.get(k) is not None}
        commands.append(("create_material", payload))
    for assign in spec["assignments"]:
        # group_index is passed at the top level so the Lua handler reads it
        commands.append(("assign_material", {
            "object_name": spec["mesh_name"],
            "material_name": assign["material_name"],
            "group_index": assign["group_index"],
        }))
    commands.append(("set_camera", spec["camera"]))
    commands.append(("set_lighting", {"preset": spec["lighting"]}))
    save = spec["save"]
    preview_path = (ws.renders_dir / f"bench_{spec['mesh_name']}.png").resolve()
    commands.append(("save_preview", {
        "path": str(preview_path),
        "width": save.get("width", 1280),
        "height": save.get("height", 1280),
        "quality": save.get("quality"),
        "min_samples": 24,
        "timeout_seconds": 120,
    }))

    queued = []
    for op, payload in commands:
        res = write_command(op, payload, ws)
        queued.append(res)
    return queued


def run_task(
    task: BenchmarkTask,
    *,
    container: Path | None = None,
    dry_run: bool = False,
    drain: bool = True,
    drain_timeout: float = 60.0,
    quality_override: str | None = None,
) -> TaskRun:
    """Run a single benchmark task end-to-end (or up to the dry_run boundary).

    dry_run=True: build + mirror + queue only; do not drain or verify.
    drain=False: queue only; return before draining (for batched draining).
    """
    run = TaskRun(slug=task.slug, tier=task.tier, title=task.title)
    start = time.time()
    cfg = resolve_config()
    if container is None:
        container = cfg.workspace
    ws = Workspace(root=container)
    ws.ensure()

    try:
        spec = task.build_scene()
        if quality_override:
            spec["save"]["quality"] = quality_override

        # mirror OBJ into container assets/
        obj_name = f"bench_{spec['mesh_name']}.obj"
        obj_abs_path = (ws.assets_dir / obj_name).resolve()
        obj_abs_path.write_text(spec["obj"], encoding="utf-8")
        run.obj_path = obj_abs_path

        # verify OBJ face indices are in range (off-by-one guard, pitfall #13/#19)
        _validate_obj_indices(obj_abs_path)
        run.notes.append("obj indices in range")

        queued = _queue_from_spec(spec, ws, obj_abs_path)
        run.queued = len(queued)
        run.preview_path = (ws.renders_dir / f"bench_{spec['mesh_name']}.png").resolve()

        if dry_run:
            run.notes.append("dry_run: stopped after queueing")
            return run
        if not drain:
            run.notes.append("drain deferred")
            return run

        drain_result = drain_oneshot(ws, timeout_seconds=drain_timeout)
        run.drain = drain_result
        if not drain_result.get("ok"):
            run.error = f"drain failed: {drain_result.get('error')}"
            run.duration_seconds = time.time() - start
            return run

        # poll for preview file
        preview = run.preview_path
        waited = 0.0
        while not (preview and preview.exists()) and waited < 15.0:
            time.sleep(1.0)
            waited += 1.0
        if preview and preview.exists():
            run.acceptance = acceptance.evaluate_acceptance(preview, spec["acceptance"])
        else:
            run.error = "preview not written by bridge"
            run.acceptance = acceptance.evaluate_acceptance(preview or Path("/nonexistent.png"), spec["acceptance"])

    except Exception as exc:  # noqa: BLE001
        run.error = f"{type(exc).__name__}: {exc}"
    run.duration_seconds = time.time() - start
    return run


def _validate_obj_indices(obj_path: Path) -> None:
    """Assert max face index <= vertex count (catches the orphanting/off-by-one
    bug that produces blank renders)."""
    lines = obj_path.read_text().splitlines()
    vcount = sum(1 for l in lines if l.startswith("v "))
    max_idx = 0
    for l in lines:
        if l.startswith("f "):
            for tok in l.split()[1:]:
                v = int(tok.split("/")[0])
                max_idx = max(max_idx, v)
    if max_idx > vcount:
        raise ValueError(f"OBJ face index out of range: max={max_idx} vcount={vcount}")
    if vcount == 0:
        raise ValueError("OBJ has no vertices")


def drain_oneshot(ws: Workspace, *, timeout_seconds: float = 60.0) -> dict[str, Any]:
    """Drain the container queue by running the one-shot bridge via AppleScript.

    The v2 one-shot bridge drains the ENTIRE queue in a single run (it loops
    over all queued JSON files). The AppleScript only *clicks* the Scripts menu
    item and returns immediately, so we give osascript a generous timeout (it
    must not be killed mid-click), then poll the queue until it empties or the
    render window elapses.

    Returns {"ok", "clicks", "timeout_seconds", "queue_remaining", [error]}.
    """
    from octanex_mcp.bridge_control import run_bridge_script

    result: dict[str, Any] = {"ok": False, "clicks": 0, "timeout_seconds": timeout_seconds, "queue_remaining": -1}
    waited = 0.0
    # First click to start the drain (whole queue in one pass).
    res = run_bridge_script("oneshot", timeout_seconds=max(30, int(timeout_seconds)))
    result["clicks"] += 1
    result["last_bridge_result"] = res
    if not res.get("ok"):
        result["error"] = res.get("error") or res.get("stderr") or "bridge script click failed"
        # Re-attempt up to 2 more times in case of a transient menu miss.
        if result["clicks"] < 3:
            time.sleep(2.0)
            return drain_oneshot(ws, timeout_seconds=timeout_seconds)
        return result

    # Poll until queue drains (files move to processed/failed) or timeout.
    while waited < timeout_seconds:
        q = list(ws.queue_dir.glob("*.json"))
        result["queue_remaining"] = len(q)
        if not q:
            result["ok"] = True
            break
        time.sleep(2.0)
        waited += 2.0
    if not result["ok"]:
        result.setdefault("error", "queue did not fully drain within timeout")
    return result


def run_tier(
    tier: int,
    *,
    container: Path | None = None,
    dry_run: bool = False,
    drain: bool = True,
    **kwargs: Any,
) -> list[TaskRun]:
    """Run every task in a tier. Returns TaskRun list in spec order."""
    from benchmarks.spec import tasks_by_tier

    runs: list[TaskRun] = []
    for task in tasks_by_tier(tier):
        runs.append(run_task(task, container=container, dry_run=dry_run, drain=drain, **kwargs))
    return runs


def run_all(
    *,
    container: Path | None = None,
    tiers: list[int] | None = None,
    dry_run: bool = False,
    drain: bool = True,
    **kwargs: Any,
) -> dict[str, Any]:
    from benchmarks.spec import ALL_TASKS

    tiers = tiers or sorted({t.tier for t in ALL_TASKS})
    runs: list[TaskRun] = []
    for tier in tiers:
        runs.extend(run_tier(tier, container=container, dry_run=dry_run, drain=drain, **kwargs))
    passed = sum(1 for r in runs if r.acceptance and r.acceptance.get("passed"))
    return {
        "total": len(runs),
        "passed": passed,
        "failed": len(runs) - passed,
        "tiers": tiers,
        "runs": [r.as_dict() for r in runs],
    }
