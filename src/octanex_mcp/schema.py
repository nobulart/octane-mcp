from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:
    from .bridge import Workspace

from .models import ALLOWED_OPS, COMMAND_SCHEMA_REVISION, MAX_RENDER_DIMENSION, SCHEMA_VERSION, ValidationResult, command_schema, validate_command_model

VALIDATION_SCHEMA: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "command_schema_revision": COMMAND_SCHEMA_REVISION,
    "path_rules": "Paths may be absolute or workspace-relative, but generated paths must not contain '..'.",
}

# ============================================================================
# Expanded material/light schema constants
# ============================================================================

ALLOWED_CREATION_KINDS: set[str] = {
    "glossy", "diffuse", "specular", "metallic",
    "glass", "ceramic", "atmosphere",
    "prismatic", "translucent", "fabric",
}

ALLOWED_CREATION_MATERIAL_TYPES: set[str] = frozenset(ALLOWED_CREATION_KINDS)

ALLOWED_LIGHT_TYPES: set[str] = {
    "area_light", "sun_light",
    "point_light", "spot_light", "directional_light",
    "environment", "emissive",
}

ALLOWED_MATERIAL_SHADERS: set[str] = frozenset(ALLOWED_CREATION_MATERIAL_TYPES)

ALLOWED_LIGHT_MODE_TYPES: set[str] = frozenset({
    "default", "key", "fill", "rim", "accent",
    "environment", "emissive", "area_light",
    "spot_light", "point_light", "sun_light", "directional_light",
})

ALLOWED_MATERIAL_TYPES: set[str] = frozenset({
    "diffuse", "glossy", "specular", "metallic",
    "glass", "ceramic", "atmosphere",
    "prismatic", "translucent", "fabric",
})

ALLOWED_LIGHT_TYPE: set[str] = frozenset(ALLOWED_LIGHT_MODE_TYPES)


def create_material_schema() -> dict[str, Any]:
    """Return the material schema with supported kinds and types."""
    return {
        "material_kinds": sorted(ALLOWED_CREATION_KINDS),
        "material_types": sorted(ALLOWED_CREATION_MATERIAL_TYPES),
        "material_fields": {
            "glass": {"types": ["ior", "opacity", "subsurface_scattering"], "ior": "float", "default_ior": 1.52},
            "ceramic": {"types": ["glaze", "roughness", "base_color"], "default_glaze": 0.6},
            "atmosphere": {"types": ["density", "absorption", "scattering"], "default_density": 0.5},
            "prismatic": {"types": ["dispersion", "opacity", "refraction_index"], "default_dispersion": 0.08},
            "translucent": {"types": ["thickness", "subsurface", "normal"], "default_thickness": 0.1},
            "fabric": {"types": ["weave", "normal", "opacity"], "default_weave": "plain"},
        },
    }


def create_light_schema() -> dict[str, Any]:
    """Return the light schema with supported light types and field ranges."""
    return {
        "light_types": sorted(ALLOWED_LIGHT_TYPES),
        "light_modes": sorted(ALLOWED_LIGHT_MODE_TYPES),
        "light_fields": {
            "area_intensity": {"type": "number", "min": 0, "max": 100},
            "area_width": {"type": "number", "min": 0, "max": 100},
            "area_height": {"type": "number", "min": 0, "max": 100},
            "sun_intensity": {"type": "number", "min": 0, "max": 200},
            "sun_angle": {"type": "number", "min": 0, "max": 180},
            "point_intensity": {"type": "number", "min": 0, "max": 200},
            "point_distance": {"type": "number", "min": 0, "max": 100},
            "spot_intensity": {"type": "number", "min": 0, "max": 200},
            "spot_cutoff": {"type": "number", "min": 0, "max": 180},
            "directional_intensity": {"type": "number", "min": 0, "max": 200},
            "environment_intensity": {"type": "number", "min": 0, "max": 100},
            "emissive_intensity": {"type": "number", "min": 0, "max": 500},
        },
    }


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


def validate_queue(workspace: Workspace) -> dict[str, Any]:
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
    "VALIDATION_SCHEMA",
    "MAX_RENDER_DIMENSION",
    "ValidationResult",
    "command_schema",
    "create_material_schema",
    "create_light_schema",
    "validate_command",
    "validate_command_file",
    "validate_queue",
    "ALLOWED_CREATION_KINDS",
    "ALLOWED_CREATION_MATERIAL_TYPES",
    "ALLOWED_LIGHT_TYPES",
    "ALLOWED_MATERIAL_SHADERS",
    "ALLOWED_LIGHT_MODE_TYPES",
    "ALLOWED_MATERIAL_TYPES",
    "ALLOWED_LIGHT_TYPE",
]
