from __future__ import annotations

import json
import os
import struct
import subprocess
import tempfile
import threading
import time
import uuid
import zlib as _zlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional, Mapping, Sequence

if TYPE_CHECKING:
    from .scene import load_scene_manifest as _load_scene_manifest, save_scene_manifest as _save_scene_manifest

from .config import DEFAULT_APP_PATH, DEFAULT_WORKSPACE, OctaneConfig, resolve_config
from .schema import ALLOWED_OPS, SCHEMA_VERSION, validate_command, validate_queue
from .review import (
    compare_previews as _default_compare,
    review_preview as _default_review,
    save_preview as _default_save_preview,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RECIPE_BOOK_PATH = REPO_ROOT / "docs" / "recipe-book.md"
DEFAULT_PREVIEW_PATH = Path("preview.png")


@dataclass(frozen=True)
class Workspace:
    root: Path = field(default_factory=lambda: resolve_config().workspace)

    @classmethod
    def from_config(cls, config: OctaneConfig) -> "Workspace":
        return cls(root=config.workspace)

    @property
    def queue_dir(self) -> Path:
        return self.root / "queue"

    @property
    def processed_dir(self) -> Path:
        return self.root / "processed"

    @property
    def processing_dir(self) -> Path:
        return self.root / "processing"

    @property
    def failed_dir(self) -> Path:
        return self.root / "failed"

    @property
    def results_dir(self) -> Path:
        return self.root / "results"

    @property
    def artifacts_dir(self) -> Path:
        return self.root / "artifacts"

    @property
    def assets_dir(self) -> Path:
        return self.root / "assets"

    @property
    def renders_dir(self) -> Path:
        return self.root / "renders"

    @property
    def scenes_dir(self) -> Path:
        return self.root / "scenes"

    @property
    def reviews_dir(self) -> Path:
        return self.artifacts_dir / "reviews"

    @property
    def status_path(self) -> Path:
        return self.root / "status.json"

    def ensure(self) -> None:
        for path in [
            self.root,
            self.queue_dir,
            self.processing_dir,
            self.processed_dir,
            self.failed_dir,
            self.results_dir,
            self.artifacts_dir,
            self.assets_dir,
            self.renders_dir,
            self.scenes_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def ensure_dir(self) -> None:
        self.renders_dir.mkdir(parents=True, exist_ok=True)


def octane_app_status(app_path: Optional[Path] = None, config: Optional[OctaneConfig] = None) -> Dict[str, Any]:
    config = resolve_config() if config is None else config
    app_path = config.app_path if app_path is None else app_path
    exe = app_path / "Contents" / "MacOS" / "Octane X"
    plist = app_path / "Contents" / "Info.plist"
    return {
        "app_path": str(app_path),
        "app_exists": app_path.exists(),
        "executable": str(exe),
        "executable_exists": exe.exists(),
        "info_plist_exists": plist.exists(),
        "workspace": str(config.workspace),
        "repo_root": str(config.repo_root),
    }


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def read_status(workspace: Workspace = Workspace()) -> Dict[str, Any]:
    workspace.ensure()
    if not workspace.status_path.exists():
        return {
            "bridge_seen": False,
            "status_path": str(workspace.status_path),
            "message": "No status file yet. Start hermes_bridge.lua inside Octane X.",
        }
    try:
        return json.loads(workspace.status_path.read_text())
    except Exception as exc:
        return {"bridge_seen": True, "status_error": str(exc), "status_path": str(workspace.status_path)}


def write_command(op: str, payload: Optional[Dict[str, Any]] = None, workspace: Workspace = Workspace()) -> Dict[str, Any]:
    if op not in ALLOWED_OPS:
        raise ValueError(f"Unsupported op {op!r}; allowed: {sorted(ALLOWED_OPS)}")
    workspace.ensure()
    command_id = f"{time.time_ns()}-{uuid.uuid4().hex[:8]}"
    command = {
        "schema_version": SCHEMA_VERSION,
        "id": command_id,
        "op": op,
        "payload": payload or {},
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "octanex-mcp",
    }
    validation = validate_command(command)
    if not validation.ok:
        raise ValueError("Invalid command payload: " + "; ".join(validation.errors))
    text = json.dumps(command, indent=2, default=_json_default)
    tmp_path = workspace.queue_dir / f".{command_id}.json.tmp"
    final_path = workspace.queue_dir / f"{command_id}.json"
    tmp_path.write_text(text)
    os.replace(tmp_path, final_path)

    # Publish to inbox for hermes_bridge.lua. The bridge drains `queue/`
    # first; if `queue/` is missed (e.g. a transient container-FS stall
    # while the drain's `ls` runs) it falls back to INBOX. A SINGLE
    # overwritten inbox.json would then carry ONLY the last command, so we
    # write one distinct per-command inbox file instead. The bridge
    # (v2) already scans INBOX via a directory listing of inbox_*.json.
    inbox_path = workspace.root / f"inbox_{command_id}.json"
    inbox_path.write_text(text)

    return {
        "queued": True,
        "command_id": command_id,
        "op": op,
        "path": str(final_path),
        "inbox_path": str(inbox_path),
        "schema_version": SCHEMA_VERSION,
        "validation": {"ok": validation.ok, "errors": validation.errors, "warnings": validation.warnings, "error_details": validation.error_details},
        # NOTE: deliberately do NOT block on read_status() here. A stalled
        # container FS made that read hang indefinitely (blocking the whole
        # queue), and status is only diagnostic. Callers that need it should
        # read it themselves.
        "status": None,
    }


def list_commands(workspace: Workspace = Workspace()) -> Dict[str, Any]:
    workspace.ensure()
    def names(p: Path) -> list[str]:
        return sorted(p.name for p in p.glob("*.json"))
    return {
        "queue": names(workspace.queue_dir),
        "processing": names(workspace.processing_dir),
        "processed": names(workspace.processed_dir)[-20:],
        "failed": names(workspace.failed_dir)[-20:],
        "results": names(workspace.results_dir)[-20:],
        "validation": validate_queue(workspace),
        "status": read_status(workspace),
    }


def flush_queue(workspace: Workspace = Workspace(), *, backup: bool = True) -> Dict[str, Any]:
    """Safely clear the command queue before a live render.

    The container queue is a shared, persistent directory. Across sessions it
    accumulates stale commands (observed: 2000+ leftover JSON files). Draining
    those blindly would re-render old scenes, so any live run should flush
    first. We MOVE files into a dated backup dir (never delete) so the operation
    is recoverable, and return the count moved.

    Returns {"flushed": int, "backup_dir": str|None, "queue_remaining": int}.
    """
    workspace.ensure()
    pending = sorted(workspace.queue_dir.glob("*.json"))
    moved = 0
    backup_dir: Optional[Path] = None
    if pending and backup:
        stamp = time.strftime("%Y-%m-%dT%H-%M-%SZ", time.gmtime())
        backup_dir = workspace.root / "queue_backups" / stamp
        backup_dir.mkdir(parents=True, exist_ok=True)
    for p in pending:
        moved += 1
        if backup_dir is not None:
            os.replace(p, backup_dir / p.name)
        else:
            p.unlink()
    return {
        "flushed": moved,
        "backup_dir": str(backup_dir) if backup_dir else None,
        "queue_remaining": len(list(workspace.queue_dir.glob("*.json"))),
        "backup": backup,
    }


def _recipe_heading(title: str) -> str:
    safe = " ".join(title.strip().split())
    return safe[:96] or "Untitled recipe"


def record_recipe_entry(
    *,
    title: str,
    outcome: str,
    context: str,
    steps: Iterable[str],
    signals: Iterable[str] = (),
    follow_ups: Iterable[str] = (),
    recipe_path: Path = RECIPE_BOOK_PATH,
) -> Dict[str, Any]:
    normalized_outcome = outcome.strip().lower()
    if normalized_outcome not in {"success", "failure", "partial", "pitfall"}:
        raise ValueError("outcome must be one of: success, failure, partial, pitfall")
    recipe_path.parent.mkdir(parents=True, exist_ok=True)
    if not recipe_path.exists():
        recipe_path.write_text("# OctaneX MCP Recipe Book\n\nReusable field notes from real MCP usage.\n\n", encoding="utf-8")

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    clean_steps = [f"- {item.strip()}" for item in steps if item and item.strip()]
    clean_signals = [f"- {item.strip()}" for item in signals if item and item.strip()]
    clean_follow_ups = [f"- {item.strip()}" for item in follow_ups if item and item.strip()]
    section = [
        f"## {_recipe_heading(title)}",
        "",
        f"- **Outcome:** {normalized_outcome}",
        f"- **Recorded:** {stamp}",
        f"- **Context:** {context.strip() or 'Not specified.'}",
        "",
        "### Steps",
        *(clean_steps or ["- Not specified."]),
        "",
        "### Signals / evidence",
        *(clean_signals or ["- Not specified."]),
        "",
        "### Follow-ups",
        *(clean_follow_ups or ["- None."]),
        "",
    ]
    with recipe_path.open("a", encoding="utf-8") as handle:
        handle.write("\n" + "\n".join(section))
    return {"recorded": True, "path": str(recipe_path), "title": _recipe_heading(title), "outcome": normalized_outcome}


def read_recipe_book(limit_chars: int = 12000, recipe_path: Path = RECIPE_BOOK_PATH) -> Dict[str, Any]:
    if not recipe_path.exists():
        return {"path": str(recipe_path), "exists": False, "content": ""}
    text = recipe_path.read_text(encoding="utf-8")
    if len(text) > limit_chars:
        text = text[: limit_chars // 2] + "\n\n... [truncated] ...\n\n" + text[-limit_chars // 2 :]
    return {"path": str(recipe_path), "exists": True, "content": text}


def create_simple_obj(name: str = "mcp_cube", size: float = 1.0, workspace: Workspace = Workspace()) -> Dict[str, Any]:
    workspace.ensure()
    safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name) or "mcp_cube"
    s = float(size) / 2.0
    obj = f"""# Generated by octanex-mcp
o {safe_name}
usemtl default
v {-s} {-s} {-s}
v {s} {-s} {-s}
v {s} {s} {-s}
v {-s} {s} {-s}
v {-s} {-s} {s}
v {s} {-s} {s}
v {s} {s} {s}
v {-s} {s} {s}
f 1 2 3 4
f 5 8 7 6
f 1 5 6 2
f 2 6 7 3
f 3 7 8 4
f 5 1 4 8
"""
    path = workspace.assets_dir / f"{safe_name}.obj"
    path.write_text(obj)
    return {
        "path": str(path),
        "name": safe_name,
        "size": size,
        "bounds": {
            "min": [round(-s, 6), round(-s, 6), round(-s, 6)],
            "max": [round(s, 6), round(s, 6), round(s, 6)],
            "center": [0.0, 0.0, 0.0],
            "radius": round((3.0 * s * s) ** 0.5, 6),
        },
    }


def concept_to_commands(prompt: str) -> list[Dict[str, Any]]:
    """Very small deterministic concept compiler for MVP smoke tests."""
    lower = prompt.lower()
    material = {
        "name": "concept_primary_material",
        "kind": "glossy",
        "color": [0.8, 0.8, 0.8],
        "roughness": 0.25,
    }
    if "cyber" in lower or "neon" in lower:
        material.update({"color": [0.05, 0.75, 1.0], "roughness": 0.12})
    if "gold" in lower:
        material.update({"color": [1.0, 0.67, 0.18], "metallic": 1.0, "roughness": 0.18})
    return [
        {"op": "open_or_create_project", "payload": {"name": "Hermes Concept"}},
        {"op": "create_material", "payload": material},
        {"op": "set_camera", "payload": {"position": [2.8, 1.8, 4.2], "target": [0, 0.4, 0], "fov": 45}},
        {"op": "set_lighting", "payload": {"preset": "studio_neon" if "neon" in lower else "soft_studio"}},
        {"op": "start_render", "payload": {"samples": 128, "width": 1280, "height": 1280}},
        {"op": "build_concept", "payload": {"prompt": prompt, "note": "MVP placeholder: bridge should import generated assets and map this prompt to scene nodes."}},
    ]


# ============================================================================
# Preview comparison utilities
# ============================================================================

def compare_previews(
    path_a: str | Path,
    path_b: str | Path,
) -> Dict[str, Any]:
    """Compare two preview PNG files on brightness, contrast, clipping, edge density."""
    review_a = _default_review(path_a)
    review_b = _default_review(path_b)
    return {
        "path_a": str(path_a),
        "path_b": str(path_b),
        "a": review_a,
        "b": review_b,
        "comparison": {
            "mean_brightness_diff": round(abs(review_a.get("mean_brightness", 0) - review_b.get("mean_brightness", 0)), 3),
            "contrast_diff": round(abs(review_a.get("contrast", 0) - review_b.get("contrast", 0)), 3),
            "near_black_diff": round(abs(review_a.get("near_black_percent", 0) - review_b.get("near_black_percent", 0)), 3),
            "near_white_diff": round(abs(review_a.get("near_white_percent", 0) - review_b.get("near_white_percent", 0)), 3),
            "edge_density_diff": round(abs(review_a.get("edge_density", 0) - review_b.get("edge_density", 0)), 3),
            "both_ok": review_a.get("ok") and review_b.get("ok"),
            "a_clipped": bool(review_a.get("likely_clipped")),
            "b_clipped": bool(review_b.get("likely_clipped")),
            "a_blank": bool(review_a.get("likely_blank")),
            "b_blank": bool(review_b.get("likely_blank")),
        },
    }


# ============================================================================
# Convenience re-exports for test files
# ============================================================================

def load_scene_manifest(scene_id: str, workspace: Workspace = Workspace()) -> Dict[str, Any]:
    """Load a scene manifest from the filesystem. Re-exported from .scene for convenience."""
    from .scene import load_scene_manifest as _ls
    return _ls(scene_id, workspace)


def save_scene_manifest(plan: Mapping[str, Any], workspace: Workspace = Workspace()) -> Dict[str, Any]:
    """Save a scene manifest to disk. Re-exported from .scene for convenience."""
    from .scene import save_scene_manifest as _ss
    return _ss(plan, workspace)


# ============================================================================
# Octane patch scene — granular updates to a loaded scene manifest
# ============================================================================

def octane_patch_scene(
    scene_id: str,
    workspace: Optional[Workspace] = None,
    patch_camera: Optional[Dict[str, Any]] = None,
    patch_lighting: Optional[Dict[str, Any]] = None,
    patch_render: Optional[Dict[str, Any]] = None,
    add_materials: Optional[list[Dict[str, Any]]] = None,
    update_materials: Optional[list[Dict[str, Any]]] = None,
    add_objects: Optional[list[Dict[str, Any]]] = None,
    update_objects: Optional[list[Dict[str, Any]]] = None,
    remove_objects: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """Apply granular patches to a scene manifest."""
    if workspace is None:
        workspace = Workspace()
    workspace.ensure()

    loaded = load_scene_manifest(scene_id, workspace)
    scene = loaded["scene"]

    if patch_camera is not None:
        existing_camera = scene.get("camera") or {}
        scene["camera"] = {**existing_camera, **patch_camera}

    if patch_lighting is not None:
        existing_lighting = scene.get("lighting") or {}
        scene["lighting"] = {**existing_lighting, **patch_lighting}

    if patch_render is not None:
        existing_render = scene.get("render") or {}
        scene["render"] = {**existing_render, **patch_render}

    if add_materials:
        added: list[str] = []
        names_in_scene = {str(m.get("name") or m.get("id") or "") for m in scene.get("materials", [])}
        for material in add_materials:
            mat_name = str(material.get("name") or material.get("id") or "material")
            if mat_name not in names_in_scene:
                scene.setdefault("materials", []).append(material)
                names_in_scene.add(mat_name)
                added.append(mat_name)
        if added:
            saved = save_scene_manifest(scene, workspace)
            return {**saved, "patched": True, "added_materials": added}

    if update_materials:
        for new_mat in update_materials:
            name_key = (new_mat.get("name") or new_mat.get("id") or "")
            updated = False
            for existing in scene.get("materials", []):
                if (existing.get("name") or existing.get("id") or "") == name_key:
                    existing.update(new_mat)
                    updated = True
                    break
            if not updated:
                scene.setdefault("materials", []).append(new_mat)
        saved = save_scene_manifest(scene, workspace)
        return {**saved, "patched": True, "updated_materials": [str(m.get("name") or m.get("id") or "") for m in update_materials]}

    if add_objects:
        added_objs: list[str] = []
        ids_in_scene = {str(o.get("id") or o.get("name") or "") for o in scene.get("objects", [])}
        for obj in add_objects:
            obj_id = str(obj.get("id") or obj.get("name") or "object")
            if obj_id not in ids_in_scene:
                scene.setdefault("objects", []).append(obj)
                ids_in_scene.add(obj_id)
                added_objs.append(obj_id)
        if added_objs:
            saved = save_scene_manifest(scene, workspace)
            return {**saved, "patched": True, "added_objects": added_objs}

    if update_objects:
        updated_objs: list[str] = []
        for new_obj in update_objects:
            name_key = (new_obj.get("id") or new_obj.get("name") or "")
            found = False
            for existing in scene.get("objects", []):
                if (existing.get("id") or existing.get("name") or "") == name_key:
                    existing.update(new_obj)
                    found = True
                    updated_objs.append(name_key)
                    break
            if not found:
                scene.setdefault("objects", []).append(new_obj)
                updated_objs.append(name_key)
        saved = save_scene_manifest(scene, workspace)
        return {**saved, "patched": True, "updated_objects": updated_objs}

    if remove_objects:
        kept: list[Dict] = []
        removed_objs: list[str] = []
        for obj in scene.get("objects", []):
            obj_id = str(obj.get("id") or obj.get("name") or "object")
            if obj_id in remove_objects:
                removed_objs.append(obj_id)
            else:
                kept.append(obj)
        if removed_objs:
            scene["objects"] = kept
            saved = save_scene_manifest(scene, workspace)
            return {**saved, "patched": True, "removed_objects": removed_objs}

    saved = save_scene_manifest(scene, workspace)
    return {**saved, "patched": True, "message": "no patches applied"}


# ============================================================================
# Render-review orchestration loop
# ============================================================================

def octane_render_review_loop(
    scene_id: str = "current_scene",
    workspace: Optional[Workspace] = None,
    max_iterations: int = 10,
    iteration_delay: float = 1.5,
    preview_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Start Octane renders, capture previews, review, and loop until acceptance."""
    if workspace is None:
        workspace = Workspace()
    workspace.ensure()

    reviews_dir = workspace.reviews_dir
    reviews_dir.mkdir(parents=True, exist_ok=True)

    iterations: list[Dict[str, Any]] = []
    iteration = 0
    last_review: Dict[str, Any] = {}

    while iteration < max_iterations:
        iteration += 1

        render_cmd = write_command("start_render", {
            "scene_id": scene_id,
            "samples": 128,
        })

        scene = None
        try:
            loaded = load_scene_manifest(scene_id, workspace)
            scene = loaded["scene"]
        except FileNotFoundError:
            scene = {"camera": {"position": [0, 0, 0], "fov": 45}, "lighting": {"preset": "soft_studio"}}

        actual_preview = Path(preview_path) if preview_path else workspace.renders_dir / "preview.png"
        if not actual_preview.exists():
            actual_preview = workspace.renders_dir / "preview.png"

        review = _default_review(str(actual_preview))
        review["path"] = str(actual_preview)
        review["iteration"] = iteration
        review["scene_id"] = scene_id

        checkpoint = reviews_dir / f"checkpoint_{iteration:04d}.json"
        checkpoint.write_text(json.dumps(review, indent=2, default=str), encoding="utf-8")

        iterations.append(review)
        last_review = review

        if review.get("ok", False):
            break

        if iteration < max_iterations:
            if review.get("likely_object_too_small"):
                center = scene.get("camera", {}).get("position", [0.0, 0.0, 0.0])
                fov = scene.get("camera", {}).get("fov", 45)
                if fov > 30:
                    scene["camera"]["fov"] = max(36.0, fov - 6)
                    scene["camera"]["position"] = [c * 0.9 for c in center]

            if review.get("near_black_percent", 0) > 90:
                scene.setdefault("lighting", {})["preset"] = "brighter_studio"

            scene.setdefault("render", {}).setdefault("samples", 0)
            scene["render"]["samples"] += 64
            save_scene_manifest(scene, workspace)

        time.sleep(iteration_delay)

    return {
        "completed": True,
        "iterations": iteration,
        "max_iterations": max_iterations,
        "final_review": last_review,
        "checkpoint": str(reviews_dir / f"checkpoint_{iteration:04d}.json"),
        "all_checks": list(dict.fromkeys(k for i in iterations for k in i.keys())),
    }


# ============================================================================
# Scene graph harvest (real-time OctaneX scene graph query)
# ============================================================================

def scene_harvest(workspace: Optional[Workspace] = None) -> Dict[str, Any]:
    """Query the live OctaneX scene graph and serialize it to JSON.

    This reads the current scene graph from Octane X's node graph,
    harvesting all nodes with their names, types, properties, and connections.
    Returns the harvest result as a dictionary that can be inspected by the agent.
    """
    if workspace is None:
        workspace = Workspace()
    ws = workspace
    ws.ensure()

    # Write the scene_harvest command to the queue
    harvest_cmd = {
        "op": "scene_harvest",
        "payload": {"dry_run": False},
    }
    cmd_path = write_command("scene_harvest", {"dry_run": False}, ws)

    # Read the harvest result from results/scene_harvest.json
    results_dir = ws.results_dir
    harvest_path = results_dir / "scene_harvest.json"

    # Wait briefly for the bridge to produce the harvest result
    import time
    harvest_data: Dict[str, Any] = {"nodes": [], "count": 0, "timestamp": "", "source": str(cmd_path)}
    for _ in range(5):
        if harvest_path.exists():
            try:
                raw = harvest_path.read_text(encoding="utf-8")
                if raw.strip():
                    import json
                    try:
                        harvest_data = json.loads(raw)
                    except json.JSONDecodeError:
                        harvest_data = {"nodes": [], "count": 0, "raw": raw[:500], "source": str(cmd_path)}
                    break
            except Exception as exc:
                harvest_data["error"] = str(exc)
                break
        time.sleep(0.5)

    if not harvest_data.get("nodes"):
        harvest_data["nodes"] = []
        harvest_data["count"] = 0

    return harvest_data


def probe_types(workspace: Optional[Workspace] = None) -> Dict[str, Any]:
    """Probe which Octane node types this build actually supports.

    The persistent/oneshot Lua bridge runs ``handle_probe_types``: it
    tests each candidate ``NT_*`` constant for existence + create-ability
    and enumerates the daylight environment node's attribute pins. This
    is the live counterpart to the offline API corpus — it answers
    "can the bridge build a real dark_studio / light here?" for the
    exact running build. Returns the probe result dict (or an error
    shape if the bridge has not yet produced it).
    """
    if workspace is None:
        workspace = Workspace()
    ws = workspace
    ws.ensure()

    cmd_path = write_command("probe_types", {}, ws)

    results_dir = ws.results_dir
    probe_path = results_dir / "probe_types.json"

    import time
    import json

    probe_data: Dict[str, Any] = {"ok": False, "source": str(cmd_path)}
    for _ in range(5):
        if probe_path.exists():
            try:
                raw = probe_path.read_text(encoding="utf-8")
                if raw.strip():
                    try:
                        probe_data = json.loads(raw)
                    except json.JSONDecodeError:
                        probe_data = {"ok": False, "raw": raw[:500], "source": str(cmd_path)}
                    break
            except Exception as exc:
                probe_data["error"] = str(exc)
                break
        time.sleep(0.5)

    return probe_data
