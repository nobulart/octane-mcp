from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import PurePosixPath
from typing import Any, Mapping

# Light types accepted by create_light (mirrors schema.ALLOWED_LIGHT_TYPES;
# defined locally to avoid a circular import with schema.py).
ALLOWED_LIGHT_TYPES: frozenset[str] = frozenset({
    "area_light", "sun_light", "point_light", "spot_light", "directional_light",
    "environment", "emissive",
})

SCHEMA_VERSION = "1.0"
COMMAND_SCHEMA_REVISION = "typed-contracts-1"
MAX_RENDER_DIMENSION = 8192

# Render convergence quality tiers. Each tier resolves to an Octane film
# maxRenderTime (GPU stop, seconds; 0 = unlimited) AND a wall-clock
# timeout_seconds (Lua poll ceiling). Both act as caps; whichever is hit
# first stops the render. min_samples / samples are targets only.
QUALITY_TIERS: dict[str, dict[str, Any]] = {
    # `fast` is the creator default (500 s/px). Octane X ships a film
    # `maxSamples` of 5000, which makes every scene-render crawl to an
    # irrelevant convergence. The bridge overrides the film's maxSamples with
    # the command's `samples` field on every render, so a 500-s/px
    # target gets a clean, presentable frame in 1-3 s instead of 30+ s.
    "fast": {"max_render_time": 6, "timeout_seconds": 10, "min_samples": 64, "samples": 500},
    "preview": {"max_render_time": 10, "timeout_seconds": 10, "min_samples": 16, "samples": 256},
    "standard": {"max_render_time": 30, "timeout_seconds": 30, "min_samples": 24, "samples": 512},
    "high": {"max_render_time": 60, "timeout_seconds": 60, "min_samples": 48, "samples": 1024},
    "ultra": {"max_render_time": 120, "timeout_seconds": 120, "min_samples": 96, "samples": 2048},
    "final": {"max_render_time": 0, "timeout_seconds": 600, "min_samples": 1024, "samples": 1_000_000},
}
# Creator default: 500 s/px `fast` tier. Overrides Octane X's
# 5000 s/px film default on every render (see request_render_restart),
# so scenes build/render in 1-3 s instead of crawling to convergence.
DEFAULT_QUALITY = "fast"


ALLOWED_OPS = {
    "ping",
    "open_or_create_project",
    "import_geometry",
    "create_material",
    "assign_material",
    "set_camera",
    "set_lighting",
    "create_light",
    "start_render",
    "pause_render",
    "save_preview",
    "save_scene",
    "scene_harvest",
    "scene_summary",
    "build_concept",
    "set_object_transform",
    "probe_types",
}


@dataclass(frozen=True)
class ValidationErrorDetail:
    code: str
    message: str
    field: str | None = None

    def as_dict(self) -> dict[str, str]:
        item = {"code": self.code, "message": self.message}
        if self.field is not None:
            item["field"] = self.field
        return item


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: list[str]
    warnings: list[str]
    error_details: list[dict[str, str]] = field(default_factory=list)


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


class _Collector:
    def __init__(self) -> None:
        self.details: list[ValidationErrorDetail] = []
        self.warnings: list[str] = []

    @property
    def errors(self) -> list[str]:
        return [detail.message for detail in self.details]

    def error(self, code: str, message: str, field: str | None = None) -> None:
        self.details.append(ValidationErrorDetail(code=code, message=message, field=field))


class PayloadValidator:
    op: str

    def __init__(self, op: str) -> None:
        self.op = op

    def validate(self, payload: Mapping[str, Any], errors: _Collector) -> None:
        return None

    def require_string(self, payload: Mapping[str, Any], field: str, errors: _Collector) -> None:
        value = payload.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.error(f"payload.{field}.required", f"payload.{field} is required for {self.op}", f"payload.{field}")
        elif not isinstance(value, str):
            errors.error(f"payload.{field}.type", f"payload.{field} must be a string for {self.op}", f"payload.{field}")

    def optional_number(self, payload: Mapping[str, Any], field: str, errors: _Collector) -> Any:
        value = payload.get(field)
        if value is not None and not _is_number(value):
            errors.error(f"payload.{field}.type", f"payload.{field} must be a number for {self.op}", f"payload.{field}")
            return None
        return value

    def optional_number_range(self, payload: Mapping[str, Any], field: str, minimum: float, maximum: float, errors: _Collector) -> None:
        value = self.optional_number(payload, field, errors)
        if value is not None and not minimum <= float(value) <= maximum:
            errors.error(
                f"payload.{field}.out_of_range",
                f"payload.{field} must be between {minimum:g} and {maximum:g} for {self.op}",
                f"payload.{field}",
            )

    def required_vector3(self, payload: Mapping[str, Any], field: str, errors: _Collector) -> None:
        value = payload.get(field)
        if value is None:
            errors.error(f"payload.{field}.required", f"payload.{field} is required for {self.op}", f"payload.{field}")
            return
        if not isinstance(value, list) or len(value) != 3 or not all(_is_number(item) for item in value):
            errors.error(f"payload.{field}.type", f"payload.{field} must be a 3-number array for {self.op}", f"payload.{field}")

    def optional_vector3(self, payload: Mapping[str, Any], field: str, errors: _Collector) -> None:
        value = payload.get(field)
        if value is None:
            return
        if not isinstance(value, list) or len(value) != 3 or not all(_is_number(item) for item in value):
            errors.error(f"payload.{field}.type", f"payload.{field} must be a 3-number array for {self.op}", f"payload.{field}")

    def optional_color(self, payload: Mapping[str, Any], field: str, errors: _Collector) -> None:
        value = payload.get(field)
        if value is None:
            return
        if not isinstance(value, list) or len(value) not in {3, 4} or not all(_is_number(item) for item in value):
            errors.error(f"payload.{field}.type", f"payload.{field} must be a 3- or 4-number array for {self.op}", f"payload.{field}")
            return
        if any(float(item) < 0.0 or float(item) > 1.0 for item in value):
            errors.error(f"payload.{field}.out_of_range", f"payload.{field} values must be between 0 and 1 for {self.op}", f"payload.{field}")

    def optional_safe_path(self, payload: Mapping[str, Any], field: str, errors: _Collector) -> None:
        value = payload.get(field)
        if value is None:
            return
        if not isinstance(value, str):
            errors.error(f"payload.{field}.type", f"payload.{field} must be a string for {self.op}", f"payload.{field}")
            return
        if not value.strip():
            errors.error(f"payload.{field}.required", f"payload.{field} is required for {self.op}", f"payload.{field}")
            return
        path = PurePosixPath(value.replace("\\", "/"))
        if ".." in path.parts:
            errors.error(f"payload.{field}.unsafe", f"payload.{field} must not contain '..' traversal for {self.op}", f"payload.{field}")


class PingPayload(PayloadValidator):
    pass


class ImportGeometryPayload(PayloadValidator):
    def validate(self, payload: Mapping[str, Any], errors: _Collector) -> None:
        self.require_string(payload, "path", errors)
        self.optional_safe_path(payload, "path", errors)


class CreateMaterialPayload(PayloadValidator):
    def validate(self, payload: Mapping[str, Any], errors: _Collector) -> None:
        self.require_string(payload, "name", errors)
        self.optional_color(payload, "color", errors)
        self.optional_color(payload, "diffuse", errors)
        self.optional_color(payload, "albedo", errors)
        self.optional_number_range(payload, "roughness", 0, 1, errors)
        self.optional_number_range(payload, "metallic", 0, 1, errors)
        self.optional_number_range(payload, "specular", 0, 1, errors)
        self.optional_number_range(payload, "transmission", 0, 1, errors)
        self.optional_number_range(payload, "ior", 1.0, 2.5, errors)
        self.optional_number_range(payload, "opacity", 0, 1, errors)
        self.optional_number_range(payload, "clearcoat", 0, 1, errors)
        self.optional_number_range(payload, "anisotropy", 0, 1, errors)
        self.optional_number_range(payload, "emission", 0, 1000, errors)
        self.optional_safe_path(payload, "texture_path", errors)
        self.optional_safe_path(payload, "normal_path", errors)


class CreateLightPayload(PayloadValidator):
    def validate(self, payload: Mapping[str, Any], errors: _Collector) -> None:
        self.require_string(payload, "name", errors)
        light_type = payload.get("light_type")
        if light_type is not None and light_type not in ALLOWED_LIGHT_TYPES:
            errors.error(
                "payload.light_type.invalid",
                f"light_type must be one of {sorted(ALLOWED_LIGHT_TYPES)}",
                "light_type",
            )
        if light_type == "area_light":
            self.optional_number_range(payload, "intensity", 0, 100, errors)
            self.optional_vector3(payload, "size", errors)
        elif light_type == "sun_light":
            self.optional_number_range(payload, "intensity", 0, 200, errors)
            self.optional_number_range(payload, "angle", 0, 180, errors)
        elif light_type == "environment":
            self.optional_number_range(payload, "intensity", 0, 100, errors)
            self.optional_safe_path(payload, "hdr_path", errors)
        elif light_type == "emissive":
            self.optional_number_range(payload, "intensity", 0, 500, errors)
        self.optional_vector3(payload, "position", errors)
        self.optional_vector3(payload, "direction", errors)


class AssignMaterialPayload(PayloadValidator):
    def validate(self, payload: Mapping[str, Any], errors: _Collector) -> None:
        self.require_string(payload, "object_name", errors)
        self.require_string(payload, "material_name", errors)


class SetCameraPayload(PayloadValidator):
    def validate(self, payload: Mapping[str, Any], errors: _Collector) -> None:
        self.required_vector3(payload, "position", errors)
        self.required_vector3(payload, "target", errors)
        self.optional_number_range(payload, "fov", 5, 120, errors)


class SetObjectTransformPayload(PayloadValidator):
    def validate(self, payload: Mapping[str, Any], errors: _Collector) -> None:
        self.require_string(payload, "object_name", errors)
        # At least one transform channel must be present.
        has = any(k in payload for k in ("translation", "rotation_euler", "scale"))
        if not has:
            errors.error(
                "payload.transform.required",
                "set_object_transform needs translation, rotation_euler, or scale",
                "payload",
            )
        self.optional_vector3(payload, "translation", errors)
        self.optional_vector3(payload, "rotation_euler", errors)
        self.optional_vector3(payload, "scale", errors)


class SetLightingPayload(PayloadValidator):
    pass


class StartRenderPayload(PayloadValidator):
    def validate(self, payload: Mapping[str, Any], errors: _Collector) -> None:
        self.optional_number_range(payload, "samples", 1, 1_000_000, errors)
        self.optional_number_range(payload, "width", 1, MAX_RENDER_DIMENSION, errors)
        self.optional_number_range(payload, "height", 1, MAX_RENDER_DIMENSION, errors)


class SavePreviewPayload(PayloadValidator):
    def validate(self, payload: Mapping[str, Any], errors: _Collector) -> None:
        self.optional_safe_path(payload, "path", errors)
        self.optional_number_range(payload, "width", 1, MAX_RENDER_DIMENSION, errors)
        self.optional_number_range(payload, "height", 1, MAX_RENDER_DIMENSION, errors)
        self.optional_number_range(payload, "samples", 1, 1_000_000, errors)
        self.optional_number_range(payload, "min_samples", 0, 1_000_000, errors)
        self.optional_number_range(payload, "timeout_seconds", 0, 600, errors)
        self.optional_number_range(payload, "max_render_time", 0, 600, errors)
        quality = payload.get("quality")
        if quality is not None and quality not in QUALITY_TIERS:
            errors.error(
                "payload.quality.invalid",
                f"quality must be one of {sorted(QUALITY_TIERS)}",
                "quality",
            )


class SceneSummaryPayload(PayloadValidator):
    pass


class SceneHarvestPayload(PayloadValidator):
    def validate(self, payload: Mapping[str, Any], errors: _Collector) -> None:
        dry_run = payload.get("dry_run")
        if dry_run is not None and not isinstance(dry_run, bool):
            errors.error("payload.dry_run.type", "payload.dry_run must be a boolean for scene_harvest", "payload.dry_run")


class BuildConceptPayload(PayloadValidator):
    def validate(self, payload: Mapping[str, Any], errors: _Collector) -> None:
        self.require_string(payload, "prompt", errors)


class ProbeTypesPayload(PayloadValidator):
    pass


PAYLOAD_VALIDATORS: dict[str, type[PayloadValidator]] = {
    "ping": PingPayload,
    "open_or_create_project": PayloadValidator,
    "import_geometry": ImportGeometryPayload,
    "create_material": CreateMaterialPayload,
    "assign_material": AssignMaterialPayload,
    "set_camera": SetCameraPayload,
    "set_lighting": SetLightingPayload,
    "set_object_transform": SetObjectTransformPayload,
    "create_light": CreateLightPayload,
    "start_render": StartRenderPayload,
    "pause_render": PayloadValidator,
    "save_preview": SavePreviewPayload,
    "save_scene": PayloadValidator,
    "scene_harvest": SceneHarvestPayload,
    "scene_summary": SceneSummaryPayload,
    "build_concept": BuildConceptPayload,
    "probe_types": ProbeTypesPayload,
}


def validate_command_model(command: Mapping[str, Any]) -> ValidationResult:
    errors = _Collector()

    schema_version = command.get("schema_version")
    if schema_version != SCHEMA_VERSION:
        errors.error("schema_version.invalid", f"schema_version must be {SCHEMA_VERSION!r}", "schema_version")

    command_id = command.get("id")
    if not _is_non_empty_string(command_id):
        errors.error("id.required", "id is required", "id")

    op = command.get("op")
    if not _is_non_empty_string(op):
        errors.error("op.required", "op is required", "op")
    elif op not in ALLOWED_OPS:
        errors.error("op.unsupported", f"op {op!r} is not allowed", "op")

    payload = command.get("payload")
    if payload is None:
        errors.error("payload.required", "payload is required", "payload")
        payload = {}
    elif not isinstance(payload, Mapping):
        errors.error("payload.type", "payload must be an object", "payload")
        payload = {}

    created_at = command.get("created_at")
    if not _validate_iso_utc(created_at):
        errors.error("created_at.invalid", "created_at must be an ISO-8601 UTC timestamp ending in Z", "created_at")

    source = command.get("source")
    if source != "octanex-mcp":
        errors.warnings.append("source should be 'octanex-mcp'")

    if isinstance(op, str) and isinstance(payload, Mapping) and op in ALLOWED_OPS:
        PAYLOAD_VALIDATORS.get(op, PayloadValidator)(op).validate(payload, errors)

    detail_dicts = [detail.as_dict() for detail in errors.details]
    return ValidationResult(ok=not errors.details, errors=errors.errors, warnings=errors.warnings, error_details=detail_dicts)


def command_schema() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "command_schema_revision": COMMAND_SCHEMA_REVISION,
        "envelope": {
            "required": ["schema_version", "id", "op", "payload", "created_at", "source"],
            "source": "octanex-mcp",
            "created_at": "ISO-8601 UTC timestamp ending in Z",
        },
        "operations": {
            "ping": {"fields": {"message": {"type": "string", "required": False}}},
            "open_or_create_project": {"fields": {"name": {"type": "string", "required": False}}},
            "import_geometry": {"fields": {"path": {"type": "safe path", "required": True}, "format": {"type": "string", "required": False}, "name": {"type": "string", "required": False}}},
            "create_material": {"fields": {"name": {"type": "string", "required": True}, "kind": {"type": "string", "required": False}, "color": {"type": "number[3|4]", "min": 0, "max": 1}, "roughness": {"type": "number", "min": 0, "max": 1}, "metallic": {"type": "number", "min": 0, "max": 1}, "anisotropy": {"type": "number", "min": 0, "max": 1}}},
            "assign_material": {"fields": {"object_name": {"type": "string", "required": True}, "material_name": {"type": "string", "required": True}}},
            "set_camera": {"fields": {"position": {"type": "number[3]", "required": True}, "target": {"type": "number[3]", "required": True}, "fov": {"type": "number", "min": 5, "max": 120}}},
            "set_object_transform": {"fields": {"object_name": {"type": "string", "required": True}, "translation": {"type": "number[3]", "required": False}, "rotation_euler": {"type": "number[3]", "required": False}, "scale": {"type": "number[3]", "required": False}}},
            "set_lighting": {"fields": {"preset": {"type": "string", "required": False}}},
            "create_light": {"fields": {"name": {"type": "string", "required": True}, "light_type": {"type": "string", "required": True, "allowed": ["area_light", "sun_light", "point_light", "spot_light", "directional_light", "environment", "emissive"]}, "intensity": {"type": "number", "min": 0, "max": 500}, "angle": {"type": "number", "min": 0, "max": 180}, "size": {"type": "number[3]", "required": False}, "position": {"type": "number[3]", "required": False}, "direction": {"type": "number[3]", "required": False}, "hdr_path": {"type": "safe path", "required": False}}},
            "start_render": {"fields": {"samples": {"type": "number", "min": 1, "max": 1_000_000}, "width": {"type": "number", "min": 1, "max": MAX_RENDER_DIMENSION}, "height": {"type": "number", "min": 1, "max": MAX_RENDER_DIMENSION}}},
            "pause_render": {"fields": {}},
            "save_preview": {"fields": {"path": {"type": "safe path", "required": False}, "width": {"type": "number", "min": 1, "max": MAX_RENDER_DIMENSION}, "height": {"type": "number", "min": 1, "max": MAX_RENDER_DIMENSION}, "samples": {"type": "number", "min": 1, "max": 1_000_000}, "min_samples": {"type": "number", "min": 0, "max": 1_000_000}, "timeout_seconds": {"type": "number", "min": 0, "max": 600}}},
            "save_scene": {"fields": {"path": {"type": "safe path", "required": False}}},
            "scene_harvest": {"fields": {"dry_run": {"type": "boolean", "required": False}}},
            "scene_summary": {"fields": {}},
            "build_concept": {"fields": {"prompt": {"type": "string", "required": True}}},
            "probe_types": {"fields": {}},
        },
        "path_rules": "Paths may be absolute or workspace-relative, but generated asset paths must not contain '..' traversal.",
        "examples": {
            "import_geometry": {"schema_version": SCHEMA_VERSION, "id": "example-import", "op": "import_geometry", "payload": {"path": "assets/cube.obj", "format": "obj", "name": "cube"}, "created_at": "2026-01-01T00:00:00Z", "source": "octanex-mcp"},
            "set_camera": {"schema_version": SCHEMA_VERSION, "id": "example-camera", "op": "set_camera", "payload": {"position": [2.8, 1.8, 4.2], "target": [0, 0, 0], "fov": 45}, "created_at": "2026-01-01T00:00:00Z", "source": "octanex-mcp"},
            "start_render": {"schema_version": SCHEMA_VERSION, "id": "example-render", "op": "start_render", "payload": {"samples": 128, "width": 1280, "height": 1280}, "created_at": "2026-01-01T00:00:00Z", "source": "octanex-mcp"},
        },
    }
