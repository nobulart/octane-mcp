"""Shared backend protocol for the Agentic Canvas.

A backend turns an internal *scene plan* (right now a plain dict; later a typed
model) into a backend-specific representation and optionally renders it. The
browser never sees Octane commands — it only hydrates ``canvas.scene.v1`` emitted
by ``WebGLBackend.build``.

The protocol is deliberately small (build / render_preview / save_png) so a fake
in-memory backend and the future Octane backend both satisfy it without bending
the interface. ``render_preview`` / ``save_png`` are optional for backends that
don't produce pixels (the WebGL tier renders in the browser, not the server).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping, Optional

from octanex_mcp.canvas_scene import SCHEMA_VERSION, validate_scene


class Backend(ABC):
    """Minimal backend contract shared by all canvas renderers."""

    #: Stable backend identifier surfaced in the gateway capabilities.
    name: str = "abstract"

    @abstractmethod
    def build(self, scene: Mapping[str, Any]) -> Mapping[str, Any]:
        """Convert a scene plan into this backend's representation.

        For ``WebGLBackend`` this returns a validated ``canvas.scene.v1`` dict.
        For the future Octane backend it returns a queue/Lua command set.
        """
        raise NotImplementedError

    def render_preview(self, scene: Mapping[str, Any]) -> Mapping[str, Any]:
        """Optional: produce an intermediate preview. Returns backend metadata."""
        return {"ok": True, "backend": self.name, "supported": False}

    def save_png(self, scene: Mapping[str, Any], path: Optional[str] = None) -> Mapping[str, Any]:
        """Optional: persist a render to PNG. Returns backend metadata."""
        return {"ok": True, "backend": self.name, "supported": False}


def build_scene(backend: Backend, scene: Mapping[str, Any]) -> Mapping[str, Any]:
    """Build via a backend and validate the WebGL output contract.

    Raises ``ValueError`` if the backend emits a scene that fails
    ``canvas.scene.v1`` validation — fail-closed so the browser is never handed
    a partially-valid scene.
    """
    result = backend.build(scene)
    if backend.name == "webgl":
        ok, errors = validate_scene(result)
        if not ok:
            raise ValueError(f"WebGLBackend produced invalid scene: {errors}")
    return result
