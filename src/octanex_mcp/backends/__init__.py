"""Renderer backend abstraction for the Agentic Canvas.

Octane is no longer the architecture — it is one of several backends that consume
the renderer-neutral ``canvas.scene.v1`` model. This package defines the shared
``Backend`` protocol and the concrete implementations:

- ``FakeBackend``   — in-memory, for tests / smoke runs (no renderer).
- ``WebGLBackend``  — pure conversion of a scene plan to ``canvas.scene.v1`` JSON
  that the browser hydrates via three.js (realtime tier).
- ``LuisaBackend``  — offline quality tier: compiles ``canvas.scene.v1`` to a
  ``.luisa`` scene and renders a real PNG via ``luisa-render-cli -b metal``.

The Octane backend remains the existing queue/Lua/PNG path and is wired in a
later phase (see ``docs/canvas-web-ui-build-plan.md`` §5, §7).
"""

from __future__ import annotations

from .base import Backend, build_scene
from .fake_backend import FakeBackend
from .webgl_backend import WebGLBackend
from .luisa_backend import LuisaBackend

__all__ = ["Backend", "build_scene", "FakeBackend", "WebGLBackend", "LuisaBackend"]
