"""In-memory backend used for tests and smoke runs (no Octane, no WebGL)."""

from __future__ import annotations

from typing import Any, Mapping

from .base import Backend


class FakeBackend(Backend):
    """Returns the scene unchanged and echoes render calls.

    Useful as the protocol test double and for ``/canvas/build`` dry runs where
    no real renderer is attached.
    """

    name = "fake"

    def build(self, scene: Mapping[str, Any]) -> Mapping[str, Any]:
        return dict(scene)

    def render_preview(self, scene: Mapping[str, Any]) -> Mapping[str, Any]:
        return {"ok": True, "backend": self.name, "supported": True, "scene_id": scene.get("scene_id")}

    def save_png(self, scene: Mapping[str, Any], path: Any = None) -> Mapping[str, Any]:
        return {"ok": True, "backend": self.name, "supported": True, "path": path}
