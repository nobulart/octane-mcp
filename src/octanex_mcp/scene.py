from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .bridge import Workspace, write_command
from .schema import SCHEMA_VERSION, validate_command
from .visuals import create_primitive_obj


def _safe_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.:-]+", "_", str(value).strip())
    return safe.strip("_") or "scene"


def namespaced(scene_id: str, object_id: str) -> str:
    return f"Hermes::{_safe_id(scene_id)}::{_safe_id(object_id)}"


def normalize_scene_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
    scene_id = _safe_id(str(plan.get("scene_id") or "scene"))
    normalized = dict(plan)
    normalized["schema_version"] = str(plan.get("schema_version") or SCHEMA_VERSION)
    normalized["scene_manifest_version"] = str(plan.get("scene_manifest_version") or "2.0")
    normalized["scene_id"] = scene_id
    normalized.setdefault("intent", "")
    normalized.setdefault("units", "arbitrary")
    normalized.setdefault("objects", [])
    normalized.setdefault("materials", [])
    normalized.setdefault("groups", [])
    normalized.setdefault("annotations", [])
    normalized.setdefault("camera", {})
    normalized.setdefault("lighting", {})
    normalized.setdefault("render", {})
    normalized.setdefault("quality_targets", {})
    normalized.setdefault("provenance", {})
    normalized["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not isinstance(normalized["objects"], list):
        raise ValueError("scene_plan.objects must be a list")
    if not isinstance(normalized["materials"], list):
        raise ValueError("scene_plan.materials must be a list")
    return normalized


_PRIMITIVE_TYPES = {"box", "sphere", "ellipsoid", "cylinder"}


def build_scene_commands(plan: Mapping[str, Any], workspace: Workspace = Workspace()) -> list[dict[str, Any]]:
    scene = normalize_scene_plan(plan)
    scene_id = scene["scene_id"]
    commands: list[dict[str, Any]] = []
    material_names: dict[str, str] = {}

    for material in scene["materials"]:
        if not isinstance(material, Mapping):
            raise ValueError("scene_plan.materials entries must be objects")
        raw_name = str(material.get("name") or material.get("id") or "material")
        namespaced_name = namespaced(scene_id, raw_name)
        material_names[raw_name] = namespaced_name
        payload = dict(material)
        payload["name"] = namespaced_name
        commands.append({"op": "create_material", "payload": payload})

    for obj in scene["objects"]:
        if not isinstance(obj, Mapping):
            raise ValueError("scene_plan.objects entries must be objects")
        obj_type = str(obj.get("type", "mesh"))
        object_id = str(obj.get("id") or obj.get("name") or "object")
        object_name = namespaced(scene_id, object_id)
        if obj_type in _PRIMITIVE_TYPES:
            asset = create_primitive_obj(dict(obj), scene_id=scene_id, workspace=workspace)
            obj["path"] = asset["path"]
            obj["format"] = asset["format"]
            obj["bounds"] = asset["bounds"]
        elif obj_type != "mesh":
            raise ValueError(f"unsupported scene object type {obj_type!r}")
        path = obj.get("path")
        if not path:
            raise ValueError(f"scene object {object_id!r} is missing path")
        payload = {"path": str(path), "format": str(obj.get("format") or "obj"), "name": object_name}
        if obj.get("transform") is not None:
            payload["transform"] = obj.get("transform")
        if obj.get("bounds") is not None:
            payload["bounds"] = obj.get("bounds")
        commands.append({"op": "import_geometry", "payload": payload})
        material_ref = obj.get("material")
        if material_ref:
            material_name = material_names.get(str(material_ref), namespaced(scene_id, str(material_ref)))
            commands.append({"op": "assign_material", "payload": {"object_name": object_name, "material_name": material_name}})

    camera = scene.get("camera") or {}
    if camera:
        commands.append({"op": "set_camera", "payload": dict(camera)})
    lighting = scene.get("lighting") or {}
    if lighting:
        commands.append({"op": "set_lighting", "payload": dict(lighting)})
    render = scene.get("render") or {}
    if render:
        commands.append({"op": "start_render", "payload": dict(render)})

    for idx, command in enumerate(commands):
        envelope = {
            "schema_version": SCHEMA_VERSION,
            "id": f"scene-{idx}",
            "op": command["op"],
            "payload": command["payload"],
            "created_at": "2026-01-01T00:00:00Z",
            "source": "octanex-mcp",
        }
        validation = validate_command(envelope)
        if not validation.ok:
            raise ValueError(f"invalid scene command {idx} ({command['op']}): " + "; ".join(validation.errors))
    return commands


def save_scene_manifest(plan: Mapping[str, Any], workspace: Workspace = Workspace()) -> dict[str, Any]:
    workspace.ensure()
    scene = normalize_scene_plan(plan)
    commands = build_scene_commands(scene, workspace)
    scene["commands"] = commands
    path = _scene_manifest_path(scene["scene_id"], workspace)
    path.write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
    return {"saved": True, "path": str(path), "scene_id": scene["scene_id"], "command_count": len(commands)}


def _scene_manifest_path(scene_id: str, workspace: Workspace) -> Path:
    return workspace.scenes_dir / f"{_safe_id(scene_id)}.json"


def load_scene_manifest(scene_id: str, workspace: Workspace = Workspace()) -> dict[str, Any]:
    workspace.ensure()
    path = _scene_manifest_path(scene_id, workspace)
    if not path.exists():
        raise FileNotFoundError(f"scene manifest not found: {path}")
    scene = normalize_scene_plan(json.loads(path.read_text(encoding="utf-8")))
    return {"loaded": True, "path": str(path), "scene_id": scene["scene_id"], "scene": scene}


def _save_loaded_scene(scene: Mapping[str, Any], workspace: Workspace) -> dict[str, Any]:
    payload = dict(scene)
    payload.pop("commands", None)
    return save_scene_manifest(payload, workspace)


def add_scene_object(scene_id: str, object_spec: Mapping[str, Any], workspace: Workspace = Workspace()) -> dict[str, Any]:
    loaded = load_scene_manifest(scene_id, workspace)
    scene = loaded["scene"]
    obj = dict(object_spec)
    object_id = str(obj.get("id") or obj.get("name") or "object")
    if any(str(existing.get("id") or existing.get("name") or "object") == object_id for existing in scene["objects"]):
        raise ValueError(f"scene object already exists: {object_id}")
    scene["objects"].append(obj)
    saved = _save_loaded_scene(scene, workspace)
    return {**saved, "object": obj, "object_count": len(scene["objects"])}


def update_scene_object(scene_id: str, object_id: str, changes: Mapping[str, Any], workspace: Workspace = Workspace()) -> dict[str, Any]:
    loaded = load_scene_manifest(scene_id, workspace)
    scene = loaded["scene"]
    for obj in scene["objects"]:
        current_id = str(obj.get("id") or obj.get("name") or "object")
        if current_id == object_id:
            obj.update(dict(changes))
            saved = _save_loaded_scene(scene, workspace)
            return {**saved, "object": obj, "object_count": len(scene["objects"])}
    raise ValueError(f"scene object not found: {object_id}")


def remove_scene_object(scene_id: str, object_id: str, workspace: Workspace = Workspace()) -> dict[str, Any]:
    loaded = load_scene_manifest(scene_id, workspace)
    scene = loaded["scene"]
    kept = []
    removed = None
    for obj in scene["objects"]:
        current_id = str(obj.get("id") or obj.get("name") or "object")
        if current_id == object_id:
            removed = obj
        else:
            kept.append(obj)
    if removed is None:
        raise ValueError(f"scene object not found: {object_id}")
    scene["objects"] = kept
    saved = _save_loaded_scene(scene, workspace)
    return {**saved, "removed": removed, "object_count": len(kept)}


def queue_scene_plan(plan: Mapping[str, Any], workspace: Workspace = Workspace()) -> dict[str, Any]:
    manifest = save_scene_manifest(plan, workspace)
    commands = build_scene_commands(plan, workspace)
    queued = [write_command(command["op"], command["payload"], workspace) for command in commands]
    return {"scene_id": manifest["scene_id"], "manifest": manifest, "queued_commands": queued}


def requeue_scene(scene_id: str, workspace: Workspace = Workspace()) -> dict[str, Any]:
    loaded = load_scene_manifest(scene_id, workspace)
    return queue_scene_plan(loaded["scene"], workspace)
