from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "1.0"

ALLOWED_OPS = {
    "ping",
    "open_or_create_project",
    "import_geometry",
    "create_material",
    "assign_material",
    "set_camera",
    "set_lighting",
    "start_render",
    "pause_render",
    "save_preview",
    "save_scene",
    "scene_summary",
    "build_concept",
}

_REQUIRED_PAYLOAD_FIELDS: dict[str, tuple[str, ...]] = {
    "import_geometry": ("path",),
    "create_material": ("name",),
    "assign_material": ("object_name", "material_name"),
    "set_camera": ("position", "target"),
    "build_concept": ("prompt",),
}

_NUMBER_FIELDS: dict[str, tuple[str, ...]] = {
    "create_material": ("roughness", "metallic"),
    "set_camera": ("fov",),
    "start_render": ("samples", "width", "height"),
    "save_preview": ("width", "height"),
}

_VECTOR_FIELDS: dict[str, tuple[str, ...]] = {
    "create_material": ("color",),
    "set_camera": ("position", "target"),
}


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: list[str]
    warnings: list[str]


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_iso_utc(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if not value.endswith("Z"):
        return False
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
        return True
    except ValueError:
        return False


def validate_command(command: Mapping[str, Any]) -> ValidationResult:
    """Validate a queued Octane MCP command envelope and its shallow payload."""

    errors: list[str] = []
    warnings: list[str] = []

    schema_version = command.get("schema_version")
    if schema_version != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}")

    command_id = command.get("id")
    if not _is_non_empty_string(command_id):
        errors.append("id is required")

    op = command.get("op")
    if not _is_non_empty_string(op):
        errors.append("op is required")
    elif op not in ALLOWED_OPS:
        errors.append(f"op {op!r} is not allowed")

    payload = command.get("payload")
    if payload is None:
        errors.append("payload is required")
        payload = {}
    elif not isinstance(payload, Mapping):
        errors.append("payload must be an object")
        payload = {}

    created_at = command.get("created_at")
    if not _validate_iso_utc(created_at):
        errors.append("created_at must be an ISO-8601 UTC timestamp ending in Z")

    source = command.get("source")
    if source != "octanex-mcp":
        warnings.append("source should be 'octanex-mcp'")

    if isinstance(op, str) and isinstance(payload, Mapping):
        for field in _REQUIRED_PAYLOAD_FIELDS.get(op, ()):
            value = payload.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(f"payload.{field} is required for {op}")

        for field in _NUMBER_FIELDS.get(op, ()):
            if field in payload and payload[field] is not None and not _is_number(payload[field]):
                errors.append(f"payload.{field} must be a number for {op}")

        for field in _VECTOR_FIELDS.get(op, ()):
            if field in payload and payload[field] is not None:
                value = payload[field]
                if not isinstance(value, list) or len(value) != 3 or not all(_is_number(item) for item in value):
                    errors.append(f"payload.{field} must be a 3-number array for {op}")

        if op == "import_geometry" and "path" in payload and not isinstance(payload["path"], str):
            errors.append("payload.path must be a string for import_geometry")
        if op == "save_preview" and payload.get("path") is not None and not isinstance(payload.get("path"), str):
            errors.append("payload.path must be a string for save_preview")

    return ValidationResult(ok=not errors, errors=errors, warnings=warnings)


def validate_command_file(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "path": str(path), "errors": [f"invalid JSON: {exc}"], "warnings": []}
    if not isinstance(data, Mapping):
        return {"ok": False, "path": str(path), "errors": ["command file must contain a JSON object"], "warnings": []}
    result = validate_command(data)
    return {"ok": result.ok, "path": str(path), "id": data.get("id"), "op": data.get("op"), "errors": result.errors, "warnings": result.warnings}


def validate_queue(workspace: Any) -> dict[str, Any]:
    workspace.ensure()
    items = [validate_command_file(path) for path in sorted(workspace.queue_dir.glob("*.json"))]
    invalid = sum(1 for item in items if not item["ok"])
    return {
        "ok": invalid == 0,
        "checked": len(items),
        "valid": len(items) - invalid,
        "invalid": invalid,
        "items": items,
    }
