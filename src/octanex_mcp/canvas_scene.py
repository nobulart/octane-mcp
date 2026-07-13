"""Renderer-neutral canvas scene model (``canvas.scene.v1``).

This is the *single* scene format the browser-side three.js renderer hydrates.
It is intentionally smaller and safer than the full Octane command DSL: the
browser never interprets arbitrary Octane commands, it only consumes this
flattened scene JSON. The Python side stays the source of truth — the browser
renders what we hand it, and the agent loop edits scene dicts server-side.

See ``docs/canvas-web-ui-build-plan.md`` §6 for the contract and §5 for the
role in the backend abstraction.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Tuple

SCHEMA_VERSION = "canvas.scene.v1"

# Object types the browser renderer understands in this first cut.
KNOWN_OBJECT_TYPES = {
    "box",
    "sphere",
    "ellipsoid",
    "cylinder",
    "mesh",
    "polyline",
    "points",
    "arrow",
    "text_label",
}

# Material fields we expose to the WebGL tier (the common subset from the plan's
# risk table — keep this small so Octane and WebGL materials don't diverge).
KNOWN_MATERIAL_FIELDS = {
    "color",
    "opacity",
    "roughness",
    "metalness",
    "emissive",
    "emissiveIntensity",
    "wireframe",
}


# --------------------------------------------------------------------------- #
# Construction helpers
# --------------------------------------------------------------------------- #
def default_scene(
    *,
    scene_id: str = "neutral_demo",
    title: str = "Neutral demo scene",
    intent: str = "",
) -> Dict[str, Any]:
    """Return a minimal, valid ``canvas.scene.v1`` scene with one reference cube."""
    return {
        "schema_version": SCHEMA_VERSION,
        "scene_id": scene_id,
        "title": title,
        "intent": intent,
        "units": "arbitrary",
        "camera": {"position": [4, 3, 4], "target": [0, 0, 0], "fov": 45},
        "environment": {"background": "#070a0e", "lighting": "soft_studio"},
        "objects": [
            {
                "id": "cube",
                "label": "#1",
                "type": "box",
                "position": [0, 0, 0],
                "scale": [1, 1, 1],
                "material": "neutral_matte",
            }
        ],
        "materials": [
            {
                "id": "neutral_matte",
                "color": "#9aa6b2",
                "roughness": 0.8,
                "metalness": 0.0,
                "opacity": 1.0,
            }
        ],
        "annotations": [],
        "provenance": {"source": "agent"},
    }


def _material_referenced(scene: Mapping[str, Any], mat_id: str) -> bool:
    return any(o.get("material") == mat_id for o in scene.get("objects", []))


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
def validate_scene(scene: Mapping[str, Any]) -> Tuple[bool, List[str]]:
    """Return ``(ok, errors)`` for a candidate ``canvas.scene.v1`` scene.

    Fail-closed: anything missing a schema_version, an unrecognised object type,
    or an object referencing a missing material is rejected. The browser should
    never be handed a scene that would partially render and silently look wrong.
    """
    errors: List[str] = []
    if not isinstance(scene, Mapping):
        return False, ["scene must be a JSON object"]
    if scene.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}")

    camera = scene.get("camera")
    if not isinstance(camera, Mapping):
        errors.append("camera must be an object")
    else:
        for key in ("position", "target", "fov"):
            if key not in camera:
                errors.append(f"camera.{key} is required")

    objects = scene.get("objects")
    if not isinstance(objects, list):
        errors.append("objects must be a list")
        objects = []
    for i, obj in enumerate(objects):
        if not isinstance(obj, Mapping):
            errors.append(f"objects[{i}] must be an object")
            continue
        oid = obj.get("id", f"#{i}")
        if "id" not in obj:
            errors.append(f"objects[{i}] missing id")
        if obj.get("type") not in KNOWN_OBJECT_TYPES:
            errors.append(f"objects[{i}] ({oid}) has unknown type {obj.get('type')!r}")

    materials = scene.get("materials")
    if materials is not None and not isinstance(materials, list):
        errors.append("materials must be a list")
        materials = []
    mat_ids = {m.get("id") for m in (materials or []) if isinstance(m, Mapping)}
    for i, obj in enumerate(objects):
        if not isinstance(obj, Mapping):
            continue
        oid = obj.get("id", f"#{i}")
        ref = obj.get("material")
        if ref is not None and ref not in mat_ids:
            errors.append(f"objects[{i}] ({oid}) references missing material {ref!r}")

    return (len(errors) == 0, errors)


# --------------------------------------------------------------------------- #
# Deterministic stub planner (Phase 4 first cut — no LLM yet)
# --------------------------------------------------------------------------- #
def plan_scene(text: str) -> Dict[str, Any]:
    """Map a free-text intent to a scene plan deterministically.

    This is the ``before LLM`` planner from the build plan: a small pattern table
    that always yields a valid ``canvas.scene.v1`` scene so the WebGL viewport can
    show *something* useful immediately, without Octane. The interpreted intent is
    preserved in the scene's ``intent`` field for honest display.
    """
    t = (text or "").lower()

    if any(k in t for k in ("cube", "box", "cuboid")):
        return _scene_with(shape="box", intent=text, scene_id="cube")
    if any(k in t for k in ("sphere", "planet", "ball", "globe")):
        return _scene_with(shape="sphere", intent=text, scene_id="sphere")
    if any(k in t for k in ("orbit", "decay", "satellite")):
        return _orbital_scene(intent=text)
    if any(k in t for k in ("bar", "chart", "histogram")):
        return _bar_scene(intent=text)
    if any(k in t for k in ("terrain", "landscape", "heightmap", "dem")):
        return _terrain_scene(intent=text)

    # Neutral demo + the literal intent, so the user sees what we heard.
    return default_scene(scene_id="neutral_demo", title="Neutral demo scene", intent=text)


def _scene_with(*, shape: str, intent: str, scene_id: str) -> Dict[str, Any]:
    if shape == "sphere":
        obj = {
            "id": "sphere",
            "label": "#1",
            "type": "sphere",
            "position": [0, 0, 0],
            "scale": [1, 1, 1],
            "material": "sphere_mat",
        }
        mat = {"id": "sphere_mat", "color": "#2f8fff", "roughness": 0.5, "metalness": 0.0, "opacity": 1.0}
    else:
        obj = {
            "id": "cube",
            "label": "#1",
            "type": "box",
            "position": [0, 0, 0],
            "scale": [1, 1, 1],
            "material": "cube_mat",
        }
        mat = {"id": "cube_mat", "color": "#9aa6b2", "roughness": 0.8, "metalness": 0.0, "opacity": 1.0}
    return {
        "schema_version": SCHEMA_VERSION,
        "scene_id": scene_id,
        "title": f"{shape.title()} scene",
        "intent": intent,
        "units": "arbitrary",
        "camera": {"position": [4, 3, 4], "target": [0, 0, 0], "fov": 45},
        "environment": {"background": "#070a0e", "lighting": "soft_studio"},
        "objects": [obj],
        "materials": [mat],
        "annotations": [],
        "provenance": {"source": "agent"},
    }


def _orbital_scene(*, intent: str) -> Dict[str, Any]:
    # A clear tilted circular orbit (48 segments) so it reads as a ring around the
    # planet, not a tiny arc. Radius 1.8 with a visible tube thickness.
    import math

    orbit_r = 1.8
    tilt = math.radians(22)
    pts = []
    for i in range(49):
        a = (i / 48) * 2 * math.pi
        x = orbit_r * math.cos(a)
        z = orbit_r * math.sin(a)
        # tilt the ring about the X axis
        y = z * math.sin(tilt)
        z = z * math.cos(tilt)
        pts.append([round(x, 3), round(y, 3), round(z, 3)])
    return {
        "schema_version": SCHEMA_VERSION,
        "scene_id": "orbital_decay",
        "title": "Orbital decay timeline",
        "intent": intent,
        "units": "arbitrary",
        "camera": {"position": [4, 3, 4], "target": [0, 0, 0], "fov": 45},
        "environment": {"background": "#070a0e", "lighting": "soft_studio"},
        "objects": [
            {
                "id": "earth",
                "label": "#1",
                "type": "sphere",
                "position": [0, 0, 0],
                "scale": [1, 1, 1],
                "material": "blue_planet",
            },
            {
                "id": "orbit_path",
                "label": "#2",
                "type": "polyline",
                "points": pts,
                "radius": 0.04,
                "material": "cyan_emissive",
            },
        ],
        "materials": [
            {"id": "blue_planet", "color": "#2f8fff", "roughness": 0.6, "metalness": 0.0, "opacity": 1.0},
            {"id": "cyan_emissive", "color": "#35e0d8", "emissive": "#35e0d8", "emissiveIntensity": 1.5},
        ],
        "annotations": [{"id": "label_decay", "text": "decaying orbit", "target": "orbit_path"}],
        "provenance": {"source": "agent"},
    }


def _bar_scene(*, intent: str) -> Dict[str, Any]:
    heights = [0.6, 1.0, 0.4, 1.3, 0.8]
    objects = []
    materials = []
    spacing = 1.4
    for i, h in enumerate(heights):
        mid = (len(heights) - 1) / 2
        x = (i - mid) * spacing
        mat_id = f"bar_mat_{i}"
        objects.append(
            {
                "id": f"bar_{i}",
                "label": f"#{i + 1}",
                "type": "box",
                "position": [x, h / 2, 0],
                "scale": [0.8, h, 0.8],
                "material": mat_id,
            }
        )
        materials.append(
            {"id": mat_id, "color": "#5ad17a", "roughness": 0.5, "metalness": 0.1, "opacity": 1.0}
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "scene_id": "bar_chart",
        "title": "Bar chart",
        "intent": intent,
        "units": "arbitrary",
        "camera": {"position": [0, 4, 9], "target": [0, 0.8, 0], "fov": 45},
        "environment": {"background": "#070a0e", "lighting": "soft_studio"},
        "objects": objects,
        "materials": materials,
        "annotations": [],
        "provenance": {"source": "agent"},
    }


def _terrain_scene(*, intent: str) -> Dict[str, Any]:
    # Placeholder grid until the geo track lands (Phase 8). Honest: it is a grid,
    # not real DEM data.
    n = 10
    step = 0.5
    objects = []
    for ix in range(n):
        for iz in range(n):
            x = (ix - (n - 1) / 2) * step
            z = (iz - (n - 1) / 2) * step
            objects.append(
                {
                    "id": f"cell_{ix}_{iz}",
                    "label": "",
                    "type": "box",
                    "position": [x, 0.1, z],
                    "scale": [0.4, 0.2, 0.4],
                    "material": "terrain_mat",
                }
            )
    return {
        "schema_version": SCHEMA_VERSION,
        "scene_id": "terrain_grid",
        "title": "Terrain placeholder grid",
        "intent": intent,
        "units": "arbitrary",
        "camera": {"position": [6, 6, 6], "target": [0, 0, 0], "fov": 45},
        "environment": {"background": "#070a0e", "lighting": "soft_studio"},
        "objects": objects,
        "materials": [
            {"id": "terrain_mat", "color": "#6b5b3e", "roughness": 0.9, "metalness": 0.0, "opacity": 1.0}
        ],
        "annotations": [{"id": "label_placeholder", "text": "placeholder terrain grid", "target": "cell_0_0"}],
        "provenance": {"source": "agent"},
    }


# --------------------------------------------------------------------------- #
# Scene patching (Phase 5 first cut — live object edits, server-side truth)
# --------------------------------------------------------------------------- #
# A *patch* mutates the current canvas.scene.v1 in place. Object-level patches
# target one object's fields (position/scale/material ref); material patches
# target a material's color/opacity/etc. The result is always re-validated so
# the browser is never handed a broken scene.
_PATCHABLE_OBJECT_FIELDS = {"position", "scale", "rotation", "label"}
_PATCHABLE_MATERIAL_FIELDS = {
    "color",
    "opacity",
    "roughness",
    "metalness",
    "emissive",
    "emissiveIntensity",
    "wireframe",
}


def patch_object(scene: Mapping[str, Any], object_id: str, changes: Mapping[str, Any]) -> Dict[str, Any]:
    """Apply ``changes`` to one object in ``scene`` (mutates a copy). Returns the new scene.

    ``changes`` may include object fields (position/scale/rotation/label) and a
    ``material`` sub-dict whose keys are patched onto the object's referenced
    material. Re-validates; raises ``ValueError`` if the result is no longer a
    valid ``canvas.scene.v1``.
    """
    scene = dict(scene)
    objects = [dict(o) for o in scene.get("objects", [])]
    target = next((o for o in objects if o.get("id") == object_id), None)
    if target is None:
        raise KeyError(f"no object with id {object_id!r}")

    raw_mat = changes.get("material")
    if raw_mat is None:
        mat_changes = {}
    elif isinstance(raw_mat, Mapping):
        mat_changes = raw_mat
    else:
        # A bare material id (repointing to a different material) is not a
        # supported first-cut patch — reject loudly instead of silently dropping it.
        raise ValueError("material patch must be an object of material fields, not a bare id")
    rest = {k: v for k, v in changes.items() if k != "material"}

    for k, v in rest.items():
        if k not in _PATCHABLE_OBJECT_FIELDS:
            raise ValueError(f"cannot patch object field {k!r}")
        target[k] = v

    if mat_changes:
        mat_id = target.get("material")
        if not mat_id:
            raise ValueError("object has no material to patch")
        materials = [dict(m) for m in scene.get("materials", [])]
        mat = next((m for m in materials if m.get("id") == mat_id), None)
        if mat is None:
            raise KeyError(f"no material with id {mat_id!r}")
        for k, v in mat_changes.items():
            if k not in _PATCHABLE_MATERIAL_FIELDS:
                raise ValueError(f"cannot patch material field {k!r}")
            mat[k] = v
        scene["materials"] = materials

    scene["objects"] = objects
    ok, errors = validate_scene(scene)
    if not ok:
        raise ValueError(f"patch produced invalid scene: {errors}")
    return scene


def patch_scene(scene: Mapping[str, Any], changes: Mapping[str, Any]) -> Dict[str, Any]:
    """Shallow-patch top-level scene fields (title/intent/camera/environment).

    Object/material edits go through :func:`patch_object`. Re-validates.
    """
    scene = dict(scene)
    allowed = {"title", "intent", "units", "camera", "environment", "provenance"}
    for k, v in changes.items():
        if k not in allowed:
            raise ValueError(f"cannot patch top-level field {k!r}")
        scene[k] = v
    ok, errors = validate_scene(scene)
    if not ok:
        raise ValueError(f"patch produced invalid scene: {errors}")
    return scene
