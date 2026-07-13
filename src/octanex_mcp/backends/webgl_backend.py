"""WebGL backend: emits ``canvas.scene.v1`` for the browser three.js renderer.

This backend is *pure conversion*. It takes a scene plan (the output of
``canvas_scene.plan_scene`` or anything already shaped like ``canvas.scene.v1``)
and normalises it into a browser-hydratable scene. It performs no rendering on
the server — the browser hydrates the returned JSON with three.js. The browser is
therefore fully functional with no Octane running, which is the central UX unlock
of the build plan.
"""

from __future__ import annotations

from typing import Any, Mapping

from octanex_mcp.canvas_scene import SCHEMA_VERSION, validate_scene
from octanex_mcp.backends.base import Backend

# Fields we forward verbatim from a plan into the emitted scene. Anything not in
# this set is dropped so the browser contract stays tight.
_FORWARD_ROOT = ("title", "intent", "units", "camera", "environment", "provenance")
_FORWARD_OBJECT = ("id", "label", "type", "position", "scale", "rotation", "points", "radius", "material", "text", "data")
_FORWARD_MATERIAL = ("id", "color", "opacity", "roughness", "metalness", "emissive", "emissiveIntensity", "wireframe")
_FORWARD_ANNOTATION = ("id", "text", "target", "position")


class WebGLBackend(Backend):
    """Converts a scene plan to ``canvas.scene.v1`` for three.js hydration."""

    name = "webgl"

    def build(self, scene: Mapping[str, Any]) -> Mapping[str, Any]:
        # Already a valid canvas scene? Normalise and pass through.
        src = dict(scene)
        scene_id = src.get("scene_id") or _derive_scene_id(src)

        out: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "scene_id": scene_id,
        }
        for key in _FORWARD_ROOT:
            if key in src and src[key] is not None:
                out[key] = src[key]

        out["objects"] = [_clean_object(o) for o in (src.get("objects") or [])]
        out["materials"] = [_clean_material(m) for m in (src.get("materials") or [])]
        out["annotations"] = [_clean_annotation(a) for a in (src.get("annotations") or [])]

        # Sensible defaults so the browser always has a complete scene.
        out.setdefault("camera", {"position": [4, 3, 4], "target": [0, 0, 0], "fov": 45})
        out.setdefault("environment", {"background": "#070a0e", "lighting": "soft_studio"})
        out.setdefault("provenance", {"source": "agent"})

        # Don't trust callers; validate so the browser contract is guaranteed.
        ok, errors = validate_scene(out)
        if not ok:
            raise ValueError(f"WebGLBackend produced invalid scene: {errors}")
        return out

    def render_preview(self, scene: Mapping[str, Any]) -> Mapping[str, Any]:
        # The browser renders; the server only confirms it can build.
        built = self.build(scene)
        return {"ok": True, "backend": self.name, "supported": True, "scene_id": built.get("scene_id")}

    def save_png(self, scene: Mapping[str, Any], path: Any = None) -> Mapping[str, Any]:
        # Snapshotting is a browser-side concern (canvas.toDataURL / WKWebView).
        return {"ok": True, "backend": self.name, "supported": False}


def _derive_scene_id(scene: Mapping[str, Any]) -> str:
    title = (scene.get("title") or "scene").lower()
    slug = "".join(ch if ch.isalnum() else "_" for ch in title).strip("_") or "scene"
    return slug[:48]


def _clean_object(o: Mapping[str, Any]) -> dict[str, Any]:
    return {k: o[k] for k in _FORWARD_OBJECT if k in o}


def _clean_material(m: Mapping[str, Any]) -> dict[str, Any]:
    return {k: m[k] for k in _FORWARD_MATERIAL if k in m}


def _clean_annotation(a: Mapping[str, Any]) -> dict[str, Any]:
    return {k: a[k] for k in _FORWARD_ANNOTATION if k in a}
