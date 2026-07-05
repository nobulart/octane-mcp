from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .bridge import Workspace, write_command
from .schema import SCHEMA_VERSION, validate_command


def _safe_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.:-]+", "_", str(value).strip())
    return safe.strip("_") or "scene"


def namespaced(scene_id: str, object_id: str) -> str:
    return f"Hermes::{_safe_id(scene_id)}::{_safe_id(object_id)}"


def normalize_scene_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
    scene_id = _safe_id(str(plan.get("scene_id") or "scene"))
    normalized = dict(plan)
    normalized["schema_version"] = str(plan.get("schema_version") or SCHEMA_VERSION)
    normalized["scene_id"] = scene_id
    normalized.setdefault("units", "arbitrary")
    normalized.setdefault("objects", [])
    normalized.setdefault("materials", [])
    normalized.setdefault("camera", {})
    normalized.setdefault("lighting", {})
    normalized.setdefault("render", {})
    normalized["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not isinstance(normalized["objects"], list):
        raise ValueError("scene_plan.objects must be a list")
    if not isinstance(normalized["materials"], list):
        raise ValueError("scene_plan.materials must be a list")
    return normalized


def build_scene_commands(plan: Mapping[str, Any]) -> list[dict[str, Any]]:
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
        if obj.get("type", "mesh") != "mesh":
            raise ValueError("only mesh scene objects are supported for now")
        object_id = str(obj.get("id") or obj.get("name") or "object")
        object_name = namespaced(scene_id, object_id)
        path = obj.get("path")
        if not path:
            raise ValueError(f"scene object {object_id!r} is missing path")
        commands.append({"op": "import_geometry", "payload": {"path": str(path), "format": str(obj.get("format") or "obj"), "name": object_name}})
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
    commands = build_scene_commands(scene)
    scene["commands"] = commands
    path = workspace.scenes_dir / f"{scene['scene_id']}.json"
    path.write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
    return {"saved": True, "path": str(path), "scene_id": scene["scene_id"], "command_count": len(commands)}


def queue_scene_plan(plan: Mapping[str, Any], workspace: Workspace = Workspace()) -> dict[str, Any]:
    manifest = save_scene_manifest(plan, workspace)
    commands = build_scene_commands(plan)
    queued = [write_command(command["op"], command["payload"], workspace) for command in commands]
    return {"scene_id": manifest["scene_id"], "manifest": manifest, "queued_commands": queued}
