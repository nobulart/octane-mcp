from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .models import ALLOWED_OPS, COMMAND_SCHEMA_REVISION, SCHEMA_VERSION, ValidationResult, command_schema, validate_command_model


def validate_command(command: Mapping[str, Any]) -> ValidationResult:
    """Validate a queued Octane MCP command envelope and typed payload contract."""

    return validate_command_model(command)


def validate_command_file(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "path": str(path), "errors": [f"invalid JSON: {exc}"], "warnings": [], "error_details": []}
    if not isinstance(data, Mapping):
        return {"ok": False, "path": str(path), "errors": ["command file must contain a JSON object"], "warnings": [], "error_details": []}
    result = validate_command(data)
    return {
        "ok": result.ok,
        "path": str(path),
        "id": data.get("id"),
        "op": data.get("op"),
        "errors": result.errors,
        "warnings": result.warnings,
        "error_details": result.error_details,
    }


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


__all__ = [
    "ALLOWED_OPS",
    "COMMAND_SCHEMA_REVISION",
    "SCHEMA_VERSION",
    "ValidationResult",
    "command_schema",
    "validate_command",
    "validate_command_file",
    "validate_queue",
]
