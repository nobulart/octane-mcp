"""Local HTTP gateway for the OctaneX Agentic Canvas dashboard.

The MCP server (`server.py`) is stdio-only and owned by Hermes. This gateway
is a *separate* lightweight process that exposes the same capabilities over
``http://127.0.0.1:8731`` so a native WKWebView app can drive Octane X without
injecting UI into Octane itself.

Design:
- The dashboard is a thin client: JS in ``apps/octanex-canvas/web`` talks to this
  gateway, which calls the project's existing library functions (the same ones
  the MCP tools wrap) and reads ``Workspace().renders_dir/preview.png`` and
  ``status.json`` off the filesystem.
- Octane X is driven exactly as before: we queue JSON commands the Lua bridge
  consumes. Nothing about the MCP protocol or Hermes registration changes.
- ``OCTANEX_RENDER_HOST`` lets the laptop act as a thin client to a Mac Studio
  renderer (see ``run_remote_bridge_and_pull``). Localhost is the default.

This module is intentionally dependency-light: it does not import FastMCP.
"""

from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import threading
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional

from octanex_mcp.bridge import (
    Workspace,
    create_simple_obj,
    flush_queue,
    list_commands,
    octane_app_status,
    read_recipe_book,
    read_status,
    write_command,
)
from octanex_mcp.bridge_control import octane_process_status, reset_octane_scene, run_bridge_script
from octanex_mcp.config import resolve_config
from octanex_mcp.models import QUALITY_TIERS
from octanex_mcp.recipes import (
    load_recipe,
    queue_recipe,
    recipe_index,
)
from octanex_mcp.review import (
    review_preview,
    suggest_camera_fix,
    suggest_lighting_fix,
)
from octanex_mcp.schema import command_schema, validate_command, validate_queue
from octanex_mcp.server import _build_save_preview_envelope
from octanex_mcp.animation import orbit_manifest, build_animation_commands
from octanex_mcp.scene import swap_geometry, queue_scene_plan
from octanex_mcp.bridge_control import octane_process_status, reset_octane_scene, run_bridge_script
from octanex_mcp.scheduler import DispatchLoop
from octanex_mcp.canvas_scene import plan_scene, patch_object, patch_scene
from octanex_mcp.backends import WebGLBackend, build_scene
from octanex_mcp.recipes import load_recipe, recipe_to_canvas_scene, save_recipe, RECIPES_ROOT
from octanex_mcp import hermes_config

WEB_DIR_DEFAULT = Path(__file__).resolve().parents[2] / "apps" / "octanex-canvas" / "web"
WEB_DIR = Path(os.environ.get("OCTANEX_GATEWAY_WEB_DIR", str(WEB_DIR_DEFAULT)))

# Hermes API surface for agentic chat. The canvas routes model queries
# through the local Hermes proxy (OpenAI-compatible) rather than any
# single provider directly — the proxy attaches the user's real credentials
# and knows every upstream (Nous Portal, local Ollama, ...).
HERMES_PROXY_URL = os.environ.get(
    "HERMES_PROXY_URL", "http://127.0.0.1:8645/v1/chat/completions"
)

# Local OpenAI-compatible LLM endpoint (Ollama). The canvas routes
# locally-served models here; cloud/Nous models go through HERMES_PROXY_URL.
LOCAL_LLM_URL = os.environ.get(
    "LOCAL_LLM_URL", "http://localhost:11434/v1/chat/completions"
)

def _chat_upstream(model_id: str) -> str:
    """Pick the OpenAI-compatible upstream for a model id.

    Local/non-cloud providers (Ollama / inferencer) hit LOCAL_LLM_URL
    directly; cloud/Nous models go through the Hermes proxy, which attaches
    the user's real credentials. Routing is driven by the model's `cloud`
    flag (authoritative — it already distinguishes local Ollama models from
    Nous/cloud ones), not a brittle provider-name allowlist. The allowlist is
    kept only as a fallback for unknown ids that aren't namespaced cloud ids.
    """
    try:
        opts = hermes_config.list_models().get("options", [])
    except Exception:  # noqa: BLE001 - never block chat on a config hiccup
        opts = []
    for o in opts:
        if o.get("id") == model_id:
            # cloud:False == served locally (Ollama / inferencer) -> LOCAL_LLM_URL
            return LOCAL_LLM_URL if not o.get("cloud") else HERMES_PROXY_URL
    # Unknown id: assume local if it isn't a namespaced cloud id (e.g. "org/model").
    return LOCAL_LLM_URL if "/" not in model_id else HERMES_PROXY_URL


def _chat_completion(upstream: str, body: Dict[str, Any]) -> str:
    # Local LLMs (esp. large MLX models) can take a minute+ to first token;
    # give the upstream generous headroom so a slow model degrades to a
    # readable timeout rather than a false "unavailable" 502.
    req = urllib.request.Request(
        upstream,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer x"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.loads(r.read())
    return data.get("choices", [{}])[0].get("message", {}).get("content", "")


# --------------------------------------------------------------------------- #
# Agent "DNA" — a condensed SOUL the canvas bakes into every chat turn so the
# model is prewarmed with the octanex-mcp toolkit and the live scene it owns.
# Distilled from the project's AGENTS.md / skills: the canvas is a shared
# visualisation medium; recipes are editable geometry; conversation-first.
# --------------------------------------------------------------------------- #
CANVAS_SOUL = """You are the agent inside the OctaneX Agentic Canvas — a local, \
visualisation-first modelling surface. The user is building 3D scenes you can \
see and edit.

CORE FACTS (your DNA):
- The canvas renders canvas.scene.v1: objects with {id, type, label, material, \
geometry}. Mesh objects carry triangle-list geometry from recipes/imports.
- Recipes are pre-built scenes (⌘K). Selecting one loads real, pickable, editable \
meshes — a starting point, not a screenshot. The user can click an object to select it.
- You can change the live scene via the canvas patch tool: color, opacity, scale, \
position, rotation, and (for meshes) geometry. Reference objects by their id; the \
UI may pass you a `selection` (the clicked object id) and a `scene` summary.
CRITICAL: express EVERY scene edit as a `canvas.patch(...)` call in your reply
(for example: `canvas.patch(object_id="ancient-temple_4", color="red")`). Do NOT
only narrate the edit ("I made the roof red") — the narration alone will not
change the canvas. If you describe an edit, also emit the canvas.patch(...) call.
- Conversation-first: plain chat is design discussion; only an explicit \
visualise/build/render intent commits a build. Never rebuild the scene on a \
casual question.
- Be precise and terse. When the user references "the fan blades" / "that ring" / \
"@id", map it to the actual object id from the scene summary you are given, then \
state the id you acted on. If a referenced object isn't in the scene, say so.
- You can be sent a screenshot of the current viewport (image). Analyse it \
truthfully: report what geometry, colors, and framing you actually see; do not \
invent detail. If something looks wrong (black faces, clipping, off-center), say so.
- Keep edits minimal and reversible. Prefer one concrete change per turn."""


def _scene_system_prompt(scene: Optional[Mapping[str, Any]], selection: Optional[str]) -> str:
    """Build the scene-aware system prompt for a chat turn."""
    parts = [CANVAS_SOUL]
    if scene:
        objs = scene.get("objects", []) or []
        mats = {m.get("id"): m for m in (scene.get("materials", []) or [])}
        lines = []
        for o in objs:
            m = mats.get(o.get("material"))
            color = (m or {}).get("color", "?")
            lines.append(f"- {o.get('id')}: type={o.get('type')} label={o.get('label')!r} color={color}")
        summary = "\n".join(lines) if lines else "(empty scene)"
        parts.append(
            f"\nLIVE SCENE under your control (scene_id={scene.get('scene_id')!r}, {len(objs)} object(s)):\n{summary}"
        )
        if selection:
            sel = next((o for o in objs if o.get("id") == selection), None)
            if sel:
                parts.append(f"\nThe user currently has SELECTED object id={selection!r} (label={sel.get('label')!r}).")
            else:
                parts.append(f"\nThe user referenced selection id={selection!r} but it is not in the live scene.")
    return "\n".join(parts)


def _user_content(text: str, image: Optional[str]) -> Any:
    """Return an OpenAI-compatible user message content.

    ``image`` is a data URL (``data:image/png;base64,…``); when present we send a
    multimodal message so the model can analyse the screenshot.
    """
    if not image:
        return text
    return [
        {"type": "text", "text": text or "What do you see in this viewport screenshot?"},
        {"type": "image_url", "image_url": {"url": image}},
    ]


# In-memory current canvas scene (canvas.scene.v1). The browser hydrates this
# and the agent loop edits it server-side; we do not persist scene state to disk
# in this phase (that lands with /canvas/scene POST + history in Phase 3).
_canvas_scene: Dict[str, Any] = {}


def _hex_to_rgb(hex_str: str) -> list[float]:
    """Convert ``#rrggbb`` (canvas subset) to a 0..1 RGB array for Octane."""
    h = (hex_str or "").lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        return [0.6, 0.6, 0.6]
    return [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


def _octane_ready_plan(scene: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a copy of the canvas scene with hex colors converted to Octane RGB arrays.

    The live scene the browser owns keeps its WebGL-friendly hex subset;
    only the Octane handoff needs the array form.
    """
    plan = dict(scene)
    mats = []
    for m in scene.get("materials", []):
        if isinstance(m, Mapping):
            m = dict(m)
            if isinstance(m.get("color"), str):
                m["color"] = _hex_to_rgb(m["color"])
        mats.append(m)
    plan["materials"] = mats
    return plan
_canvas_backend = WebGLBackend()


# --------------------------------------------------------------------------- #
# Serialization
# --------------------------------------------------------------------------- #
def _to_jsonable(obj: Any) -> Any:
    """Convert dataclasses / Paths / dicts / lists into JSON-safe structures."""
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_to_jsonable(v) for v in obj]
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return _to_jsonable(dataclasses.asdict(obj))
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    return str(obj)


# --------------------------------------------------------------------------- #
# Tool dispatch (underlying library functions, not the nested MCP wrappers)
# --------------------------------------------------------------------------- #
DISPATCH: Dict[str, Callable[[Dict[str, Any]], Any]] = {
    "octane_status": lambda a: {"app": octane_app_status(), "commands": list_commands()},
    "octane_bridge_process_status": lambda a: octane_process_status(),
    "octane_queue_recipe": lambda a: queue_recipe(a["slug"], overrides=a.get("overrides") or {}),
    "octane_recipe_book": lambda a: read_recipe_book(limit_chars=a.get("limit_chars", 12000)),
    "octane_recipe_index": lambda a: recipe_index(),
    "octane_load_recipe": lambda a: load_recipe(a["slug"]),
    "octane_validate_command": lambda a: validate_command(a["command"]),
    "octane_validate_queue": lambda a: validate_queue(a["commands"]),
    "octane_flush_queue": lambda a: flush_queue(Workspace(), backup=a.get("backup", True)),
    "octane_review_preview": lambda a: review_preview(a.get("path")),
    "octane_suggest_camera_fix": lambda a: suggest_camera_fix(a["preview_review"], a.get("asset_bounds", {})),
    "octane_suggest_lighting_fix": lambda a: suggest_lighting_fix(a.get("preview_review", {})),
    "octane_import_geometry": lambda a: write_command(
        "import_geometry", {"path": a["path"], "format": a.get("format", "obj"), "name": a.get("name")}
    ),
    "octane_swap_geometry": lambda a: _swap_geometry_dispatch(a),
    "octane_start_render": lambda a: write_command(
        "start_render",
        {"samples": a.get("samples", 128), "width": a.get("width", 1280), "height": a.get("height", 1280)},
    ),
    "octane_set_camera": lambda a: write_command(
        "set_camera", {"position": a["position"], "target": a["target"], "fov": a.get("fov", 45.0)}
    ),
    "octane_set_lighting": lambda a: write_command("set_lighting", {"preset": a.get("preset", "soft_studio")}),
    "octane_save_preview": lambda a: write_command(
        "save_preview",
        _build_save_preview_envelope(
            path=a.get("path"),
            width=a.get("width", 1280),
            height=a.get("height", 1280),
            samples=a.get("samples", 64),
            min_samples=a.get("min_samples", 16),
            timeout_seconds=a.get("timeout_seconds", 10),
            quality=a.get("quality"),
            max_render_time=a.get("max_render_time"),
            progressive=a.get("progressive", False),
        ),
    ),
    "octane_run_bridge": lambda a: run_bridge_script(
        a.get("mode", "oneshot"), dry_run=a.get("dry_run", False),
        timeout_seconds=a.get("timeout_seconds", 30),
    ),
    "octane_run_oneshot_bridge": lambda a: run_bridge_script(
        "oneshot", dry_run=a.get("dry_run", False), timeout_seconds=a.get("timeout_seconds", 30),
    ),
    "octane_start_persistent_bridge": lambda a: run_bridge_script(
        "persistent", dry_run=a.get("dry_run", False), timeout_seconds=a.get("timeout_seconds", 30),
    ),
    "octane_reset_octane_scene": lambda a: reset_octane_scene(timeout_seconds=a.get("timeout_seconds", 20)),
    # WP6 promoted recipe tools (thin wrappers over queue_recipe)
    "octane_build_product_studio": lambda a: queue_recipe(
        "photoreal-product-studio", overrides=a.get("overrides") or {}
    ),
    "octane_build_planet_scene": lambda a: queue_recipe(
        {"earth": "photoreal-earth-space", "saturn": "saturn-moons-space"}.get(
            (a.get("planet") or "earth").lower(), "photoreal-earth-space"
        ),
        overrides=a.get("overrides") or {},
    ),
    "octane_visualize_network": lambda a: queue_recipe(
        "network-graph", overrides=a.get("overrides") or {}
    ),
    # WP8 — animation bake (queues per-frame set_camera + save_preview commands)
    "octane_build_animation": lambda a: _dispatch_build_animation(a),
}


def _dispatch_build_animation(args: Dict[str, Any]) -> Dict[str, Any]:
    """Gateway parity for the ``octane_build_animation`` MCP tool.

    Builds the orbit manifest + per-frame command envelopes and writes each to
    the workspace queue (same side-effect as the MCP tool). Returns a summary
    the Canvas UI can render.
    """
    from octanex_mcp.models import QUALITY_TIERS

    center = tuple(args.get("center", [0.0, 0.0, 0.0]))
    manifest = orbit_manifest(
        center=center,  # type: ignore[arg-type]
        radius=args.get("radius", 8.0),
        height=args.get("orbit_height", 2.0),
        fps=args.get("fps", 24),
        duration=args.get("duration", 6.0),
        start_deg=args.get("start_deg", 0.0),
        end_deg=args.get("end_deg", 360.0),
        fov=args.get("fov", 45.0),
        segments=args.get("segments", 24),
    )
    quality = args.get("quality")
    tier = QUALITY_TIERS.get(quality) if quality else None
    frame_cmds = build_animation_commands(
        manifest,
        width=args.get("width", 1280),
        height=args.get("height", 1280),
        samples=args.get("samples", 64 if not tier else tier["samples"]),
        min_samples=args.get("min_samples", 16 if not tier else tier["min_samples"]),
        timeout_seconds=args.get("timeout_seconds", 10 if not tier else tier["timeout_seconds"]),
        quality=quality,
        max_render_time=args.get("max_render_time"),
    )
    queued = [write_command(c["op"], c["payload"]) for c in frame_cmds]
    return {"ok": True, "frames": len(queued) // 2, "queued_commands": queued}


def _swap_geometry_dispatch(args: Dict[str, Any]) -> Dict[str, Any]:
    """Gateway parity for the ``octane_swap_geometry`` MCP tool.

    Hot-swaps an object's geometry asset in place (preserving its stable node
    name) and, when ``queue`` is True, writes the swap command into the workspace
    queue so the bridge hot-replaces the mesh on the next drain.
    """
    scene_id = args["scene_id"]
    object_id = args["object_id"]
    new_path = args["new_path"]
    fmt = args.get("format", "obj")
    result = swap_geometry(scene_id, object_id, new_path, format=fmt, queue=False, workspace=Workspace())
    if args.get("queue", False):
        swap_cmd = result.get("swap_command")
        if swap_cmd:
            result["queued"] = write_command(swap_cmd["op"], swap_cmd["payload"])
    return result


def call_tool(name: str, args: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Dispatch a tool by name. Returns ``{"ok": bool, "result" | "error"}``."""
    fn = DISPATCH.get(name)
    if fn is None:
        return {"ok": False, "error": f"unknown tool: {name}"}
    try:
        result = fn(args or {})
    except Exception as exc:  # surface as a tool error, never crash the server
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "result": _to_jsonable(result)}


# --------------------------------------------------------------------------- #
# Render-host (Studio) support
# --------------------------------------------------------------------------- #
def render_host() -> str:
    try:
        return resolve_config().render_host
    except Exception:
        return "localhost"


def _remote_workspace(host: str) -> str:
    """Mirror the laptop's default workspace path on the remote host."""
    return str(resolve_config().workspace)


def run_remote_bridge_and_pull(*, mode: str = "oneshot", timeout: int = 60) -> Dict[str, Any]:
    """Render on ``OCTANEX_RENDER_HOST`` and ``scp`` the preview back locally.

    Written for the Mac Studio thin-client path (A5). Untested against live
    hardware in CI; requires shared-key SSH to the host named by
    ``OCTANEX_RENDER_HOST`` and the same OctaneMCP workspace layout on both
    machines.
    """
    host = render_host()
    if host in ("localhost", "127.0.0.1", ""):
        return {"ok": False, "error": "render_host is local; use the local bridge instead"}
    try:
        subprocess.run(
            ["ssh", host, "octanex-mcp", "run-oneshot", "--timeout", str(timeout)],
            check=True,
            timeout=timeout + 30,
            capture_output=True,
            text=True,
        )
    except Exception as exc:
        return {"ok": False, "error": f"remote bridge failed: {exc}"}
    remote_ws = _remote_workspace(host)
    local_dir = Workspace().renders_dir
    local_dir.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["scp", f"{host}:{remote_ws}/preview.png", str(local_dir / "preview.png")],
            check=True,
            timeout=120,
            capture_output=True,
            text=True,
        )
    except Exception as exc:
        return {"ok": False, "error": f"preview pull failed: {exc}"}
    return {"ok": True, "host": host, "preview": str(local_dir / "preview.png")}


# --------------------------------------------------------------------------- #
# HTTP handler
# --------------------------------------------------------------------------- #
_CONTENT_TYPES = {
    "html": "text/html; charset=utf-8",
    "js": "application/javascript; charset=utf-8",
    "css": "text/css; charset=utf-8",
    "json": "application/json; charset=utf-8",
    "png": "image/png",
    "svg": "image/svg+xml",
    "ico": "image/x-icon",
}


class Handler(BaseHTTPRequestHandler):
    # HTTP/1.1 + explicit Content-Length so fetch-hooking browser extensions /
    # intercepting proxies can't clip the stream and produce a truncated
    # (SyntaxError) module load on localhost.
    protocol_version = "HTTP/1.1"

    def handle(self) -> None:
        # Swallow benign client-disconnect noise. Browsers abort sockets on
        # tab close / reload / keep-alive expiry, surfacing as
        # ConnectionResetError / BrokenPipeError while reading the request
        # line or writing the response. These are not server faults and must
        # not dump a traceback into the log for every disconnect.
        try:
            super().handle()
        except (ConnectionResetError, BrokenPipeError):
            pass

    def _send_json(self, obj: Any, code: int = 200) -> None:
        body = json.dumps(_to_jsonable(obj), indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", _CONTENT_TYPES["json"])
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, data: bytes, content_type: str, code: int = 200,
                    extra_headers: Optional[Dict[str, str]] = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw or b"{}")
        except json.JSONDecodeError:
            return {}

    # --- GET --------------------------------------------------------------- #
    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path == "/health":
            self._send_json({"ok": True})
            return
        if path == "/config":
            self._send_json({"render_host": render_host(), "workspace": str(Workspace().root)})
            return
        if path == "/config/models":
            # Hermes Agent harness model options for the agentic interaction. The
            # harness (not this gateway) performs intent -> scene, so the canvas
            # selector reflects and sets the harness's authoritative model.
            self._send_json(hermes_config.list_models())
            return
        if path == "/config/vox":
            # Voice-conversation (STT/TTS) mode flag + the terse contract the
            # harness adopts when VOX is enabled.
            self._send_json(hermes_config.get_vox())
            return
        if path == "/status":
            # status.json lives in the Octane container FS, which can block on
            # read while the bridge writes it (every ~0.5s during a render). A
            # blocking read would hang this request (HTTP 000) and starve the
            # FAB's progress poll. Read it in a guard thread with a short
            # timeout so /status always answers promptly.
            self._send_json(_read_status_safe())
            return
        if path == "/preview":
            progressive = qs.get("progressive", ["0"])[0] == "1"
            name = "preview_progressive.png" if progressive else "preview.png"
            p = Workspace().renders_dir / name
            if not p.exists():
                self._send_json({"ok": False, "error": "no preview yet"}, code=404)
                return
            self._send_bytes(p.read_bytes(), _CONTENT_TYPES["png"])
            return
        if path == "/canvas/scene":
            if not _canvas_scene:
                self._send_json({"ok": False, "error": "no scene built yet"}, code=404)
                return
            self._send_json({"ok": True, "scene": _canvas_scene})
            return
        if path == "/canvas/recipes":
            # Lightweight recipe catalog for the ⌘K palette — served directly
            # from the recipe index so the palette works without the MCP server.
            try:
                idx = recipe_index()
                recipes = [
                    {"slug": r.get("slug") or r.get("name"), "title": r.get("title"), "tier": r.get("tier")}
                    for r in (idx.get("recipes") if isinstance(idx, Mapping) else idx or [])
                ]
            except Exception as exc:  # noqa: BLE001 - never block the palette on a hiccup
                recipes = []
            self._send_json({"ok": True, "recipes": recipes})
            return
        if path.startswith("/canvas/recipe/"):
            # Instant-load a pre-existing recipe scene into the WebGL canvas.
            # The recipe is a pre-built scene whose geometry lives in scene.obj;
            # we instantiate it as a canvas.scene.v1 so the browser renders real,
            # pickable, editable meshes (a starting point for interactive
            # development) rather than a flat preview raster.
            slug = path[len("/canvas/recipe/"):].strip("/")
            if not slug:
                self._send_json({"ok": False, "error": "recipe slug required"}, code=400)
                return
            try:
                scene = recipe_to_canvas_scene(slug)
            except ValueError as exc:
                self._send_json({"ok": False, "error": str(exc)}, code=404)
                return
            recipe = load_recipe(slug)
            preview = recipe.get("preview_path")
            preview_url = f"/recipe-preview/{slug}" if preview else None
            self._send_json({
                "ok": True,
                "slug": slug,
                "title": recipe.get("title"),
                "scene": scene,
                "preview_url": preview_url,
            })
            return
        if path.startswith("/recipe-preview/"):
            # Serve a recipe's bundled preview raster (instant-load target).
            slug = path[len("/recipe-preview/"):].strip("/")
            candidates = [
                RECIPES_ROOT / slug / "preview.png",
                RECIPES_ROOT / slug / "octane-preview.png",
                RECIPES_ROOT / slug / "photoreal-preview.png",
            ]
            for cand in candidates:
                if cand.exists() and cand.is_file():
                    self._send_bytes(cand.read_bytes(), "image/png")
                    return
            self._send_json({"ok": False, "error": "preview not found"}, code=404)
            return
        self._serve_static(path)

    # --- POST -------------------------------------------------------------- #
    def do_POST(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        payload = self._read_json()

        if path == "/mcp/call":
            name = payload.get("tool")
            args = payload.get("args") or {}
            if not isinstance(name, str):
                self._send_json({"ok": False, "error": "tool name required"}, code=400)
                return
            if not isinstance(args, dict):
                self._send_json({"ok": False, "error": "args must be an object"}, code=400)
                return
            result = call_tool(name, args)
            self._send_json(result, code=200 if result.get("ok") else 400)
            return
        if path == "/intent":
            text = payload.get("text", "")
            voice = bool(payload.get("voice", False))
            entry = {"ts": datetime.now(timezone.utc).isoformat(), "text": text, "voice": voice}
            log = Workspace().root / "intents.jsonl"
            try:
                with log.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(entry) + "\n")
            except OSError:
                pass
            self._send_json({"ok": True, "queued": True, "text": text})
            return
        if path == "/canvas/build":
            # Accept either an explicit scene plan or a free-text intent. The
            # deterministic planner (no LLM yet) always yields a valid
            # canvas.scene.v1, so the WebGL viewport can render without Octane.
            plan = payload.get("scene")
            if plan is None:
                plan = plan_scene(payload.get("intent") or payload.get("text") or "")
            try:
                scene = build_scene(_canvas_backend, plan)
            except ValueError as exc:
                self._send_json({"ok": False, "error": str(exc)}, code=422)
                return
            _canvas_scene.clear()
            _canvas_scene.update(scene)
            self._send_json({"ok": True, "scene": _canvas_scene, "schema_version": scene.get("schema_version")})
            return
        if path == "/canvas/patch":
            # Live edit of the current scene (Phase 5 first cut): selection ->
            # inspector edit -> redraw. Patches object/material/top-level fields
            # server-side (`_canvas_scene` stays the source of truth), validates,
            # and returns the updated scene for the browser to re-hydrate.
            if not _canvas_scene:
                self._send_json({"ok": False, "error": "no scene built yet"}, code=404)
                return
            object_id = payload.get("object_id")
            changes = payload.get("changes")
            if not isinstance(changes, Mapping):
                self._send_json({"ok": False, "error": "changes must be an object"}, code=400)
                return
            try:
                if object_id:
                    patched = patch_object(_canvas_scene, object_id, changes)
                else:
                    patched = patch_scene(_canvas_scene, changes)
            except (ValueError, KeyError) as exc:
                self._send_json({"ok": False, "error": str(exc)}, code=422)
                return
            _canvas_scene.clear()
            _canvas_scene.update(patched)
            self._send_json({"ok": True, "scene": _canvas_scene})
            return
        if path == "/canvas/to-octane":
            # Phase 6 handoff: push the live WebGL scene into the Octane
            # render pipeline. Flush the shared queue first (per AGENTS.md),
            # queue the scene's OBJs + command sequence, then drain the whole
            # queue via one oneshot bridge run. The browser flips to Final/
            # Split to watch the result.
            if not _canvas_scene:
                self._send_json({"ok": False, "error": "no scene built yet"}, code=404)
                return

            # Camera inheritance: the browser FAB hands the live WebGL
            # viewport camera as a `camera` override. Stamp it onto the
            # scene so queue_scene_plan emits THIS camera (the last
            # set_camera in the queue) instead of the scene's stored
            # default — otherwise the default overrides the user's view.
            if isinstance(payload.get("camera"), Mapping):
                _canvas_scene["camera"] = dict(payload["camera"])
            # Canvas uses hex colors (WebGL-friendly subset); the Octane
            # bridge expects RGB arrays. Convert at the boundary so the
            # live scene the browser owns stays untouched.
            plan = _octane_ready_plan(_canvas_scene)

            # Run the drain + render in a background thread so this request
            # returns immediately. The bridge writes live progress
            # (samples_done/samples_target/render_stage) to status.json during
            # the render, which the browser polls via /status — so the FAB
            # ring fills in real time instead of only after the render ends.
            # A module-level lock serializes renders (one Octane at a time).
            # Run the drain + render in a background thread so this request
            # returns immediately. The bridge writes live progress
            # (samples_done/samples_target/render_stage) to status.json during
            # the render, which the browser polls via /status — so the FAB
            # ring fills in real time instead of only after the render ends.
            # A module-level lock serializes renders (one Octane at a time).
            # flush + queue happen ONCE, inside the lock, so a concurrent
            # render (or an external octane_flush_queue) can never move away
            # the commands we just queued before the bridge drains them.
            queued_result: dict[str, Any] = {}
            from concurrent.futures import Future
            result_slot: Future[dict[str, Any]] = Future()

            def _drain_and_render() -> None:
                with _render_lock:
                    try:
                        flush_queue(Workspace(), backup=True)
                        q = queue_scene_plan(plan, workspace=Workspace())
                        queued_result.update(q)
                        run_bridge_script("oneshot", dry_run=bool(payload.get("dry_run", False)))
                    except Exception as exc:  # noqa: BLE001 - log, don't crash the thread
                        print("to-octane render error: " + str(exc))
                    finally:
                        result_slot.set_result(queued_result)

            threading.Thread(target=_drain_and_render, name="octane-render", daemon=True).start()
            # Wait briefly for the worker to flush+queue so we can return an
            # accurate scene_id / command count. The bridge render itself runs
            # uninterrupted in the background.
            try:
                queued = result_slot.result(timeout=10)
            except Exception:
                queued = {}
            self._send_json(
                {"ok": True, "async": True, "scene_id": queued.get("scene_id"),
                 "queued_commands": len(queued.get("queued_commands") or []),
                 "message": "render started; poll /status for progress"},
                code=202,
            )
            return
        if path == "/canvas/cancel":
            # Cancel the in-flight Octane render. The browser FAB calls this
            # when the user clicks the active render button. pause_render tells
            # Octane to stop; the bridge then lands whatever frame exists.
            try:
                from octanex_mcp.bridge import write_command
                res = write_command("pause_render", {})
                self._send_json({"ok": True, "paused": res.get("queued", False)}, code=200)
            except Exception as exc:  # noqa: BLE001
                self._send_json({"ok": False, "error": str(exc)}, code=500)
            return
        if path == "/canvas/commit":
            # Persist the live canvas scene into the recipebook under a slug.
            # Upserts by slug (overwrites an existing recipe of that name).
            slug = (payload.get("slug") or "").strip()
            scene = payload.get("scene") or _canvas_scene
            if not slug:
                self._send_json({"ok": False, "error": "slug required"}, code=400)
                return
            if not isinstance(scene, Mapping):
                self._send_json({"ok": False, "error": "no scene to commit"}, code=422)
                return
            try:
                out = save_recipe(scene, slug, mode="commit", title=payload.get("title"))
            except Exception as exc:  # noqa: BLE001
                self._send_json({"ok": False, "error": str(exc)}, code=500)
                return
            self._send_json({"ok": True, **out}, code=200)
            return
        if path == "/canvas/fork":
            # Save the live canvas scene as a NEW recipe (never overwrites) and
            # return a fresh scene seed so the canvas can start a new session
            # from it without mutating the original.
            slug = (payload.get("slug") or "fork").strip()
            scene = payload.get("scene") or _canvas_scene
            if not isinstance(scene, Mapping):
                self._send_json({"ok": False, "error": "no scene to fork"}, code=422)
                return
            try:
                out = save_recipe(scene, slug, mode="fork", title=payload.get("title"))
            except Exception as exc:  # noqa: BLE001
                self._send_json({"ok": False, "error": str(exc)}, code=500)
                return
            # Seed a fresh session scene from the committed objects so the user
            # can diverge without touching the source recipe.
            seed = {
                "schema_version": scene.get("schema_version", "canvas.scene.v1"),
                "scene_id": out["slug"],
                "objects": scene.get("objects", []),
                "materials": scene.get("materials", []),
                "camera": scene.get("camera", {}),
                "environment": scene.get("environment", {}),
            }
            self._send_json({"ok": True, **out, "seed_scene": seed}, code=200)
            return
        if path == "/config/models":
            # Set the Hermes Agent harness model that powers the agentic
            # interaction (intent -> scene). Surgical edit to ~/.hermes/config.yaml;
            # the harness reads it on next interpretation. Validate against known ids.
            model_id = payload.get("model")
            if not isinstance(model_id, str) or not model_id:
                self._send_json({"ok": False, "error": "model must be a non-empty string"}, code=400)
                return
            try:
                result = hermes_config.set_current_model(model_id)
            except ValueError as exc:
                self._send_json({"ok": False, "error": str(exc)}, code=422)
                return
            self._send_json({"ok": True, **result})
            return
        if path == "/canvas/chat":
            # Agentic query -> the selected Hermes model. The model is routed
            # to the right OpenAI-compatible upstream: locally-served models
            # (Ollama / inferencer) hit LOCAL_LLM_URL; cloud/Nous models go
            # through the Hermes proxy, which attaches the user's real
            # credentials. The turn is scene-aware: the UI sends the live
            # scene summary + the selected object id (if any), and may attach
            # a viewport screenshot (data URL) for vision analysis.
            text = (payload.get("text") or "").strip()
            model = payload.get("model") or ""
            voice = bool(payload.get("voice", False))
            scene = payload.get("scene") or None
            selection = payload.get("selection") or None
            image = payload.get("image") or None
            if not text and not image:
                self._send_json({"ok": False, "error": "text or image required"}, code=400)
                return
            if not model:
                model = (hermes_config.list_models().get("current") or "")
            messages = []
            system = _scene_system_prompt(scene, selection)
            if voice:
                system = (system + "\n\n" + hermes_config.VOX_CONTRACT).strip()
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": _user_content(text, image)})
            body = {"model": model, "messages": messages, "stream": False}
            upstream = _chat_upstream(model)
            try:
                content = _chat_completion(upstream, body)
            except Exception as exc:  # noqa: BLE001 - upstream may be down
                label = "local LLM" if upstream == LOCAL_LLM_URL else "hermes proxy"
                self._send_json(
                    {"ok": False, "error": f"{label} unavailable: {exc}"},
                    code=502,
                )
                return
            self._send_json({"ok": True, "model": model, "reply": content})
            return
        if path == "/config/vox":
            # Enable/disable VOX voice-conversation mode. The canvas writes the
            # flag into the Hermes config; the harness adopts the terse contract
            # on the next interpretation when enabled.
            enabled = payload.get("enabled")
            if not isinstance(enabled, bool):
                self._send_json({"ok": False, "error": "enabled must be true/false"}, code=400)
                return
            try:
                result = hermes_config.set_vox(enabled)
            except ValueError as exc:
                self._send_json({"ok": False, "error": str(exc)}, code=422)
                return
            self._send_json({"ok": True, **result})
            return
        if path == "/remote/render":
            self._send_json(run_remote_bridge_and_pull(), code=200)
            return
        if path == "/dispatch/start":
            poll = float(payload.get("poll_seconds", 15.0))
            drain = int(payload.get("drain_timeout", 240))
            self._send_json(start_dispatch_daemon(poll_seconds=poll, drain_timeout=drain))
            return
        if path == "/dispatch/stop":
            self._send_json(stop_dispatch_daemon())
            return
        if path == "/dispatch/status":
            self._send_json(dispatch_status())
            return
        if path == "/dispatch/tick":
            # One unit of work without a long-lived daemon (cron-friendly).
            # A live render.lock from another actor makes this a safe no-op.
            from octanex_mcp.scheduler import DispatchLoop as _DL

            self._send_json(_DL().tick())
            return
        self._send_json({"ok": False, "error": "unknown route"}, code=404)

    # --- static ------------------------------------------------------------ #
    def _inline_index(self) -> bytes:
        # Serve a single self-contained HTML document: the renderer + app
        # bundles are concatenated inline as one <script type="module">, so the
        # browser parses the JS from the HTML body itself. There is then NO
        # separate app.js / renderer.js fetch for a fetch-hooking browser
        # extension to intercept and (truncate) — which was the cause of the
        # 'Unexpected end of input' SyntaxError on localhost module loads.
        # Falls back to the plain index.html when the bundle files are absent
        # (e.g. minimal test fixtures).
        renderer_path = WEB_DIR / "canvas" / "renderer.js"
        app_path = WEB_DIR / "app.js"
        if not (renderer_path.exists() and app_path.exists()):
            return (WEB_DIR / "index.html").read_bytes()
        renderer = renderer_path.read_text()
        app = app_path.read_text()
        # The app's `import {CanvasRenderer} from "./canvas/renderer.js"` is
        # redundant once concatenated (renderer is already in scope); drop it.
        app = app.replace('import { CanvasRenderer } from "./canvas/renderer.js";\n', "")
        html = (WEB_DIR / "index.html").read_text()
        # Remove the now-inlined external script + css links; embed JS inline.
        html = html.replace('<script type="module" src="app.js?v=4"></script>', "")
        html = html.replace('<link rel="stylesheet" href="app.css?v=4" />',
                             '<link rel="stylesheet" href="app.css" />')
        inline = (
            '<script type="module">\n'
            f"{renderer}\n{app}\n"
            "</script>\n"
        )
        return html.replace("</body>", inline + "</body>").encode("utf-8")

    def _serve_static(self, path: str) -> None:
        if path in ("", "/"):
            # Inline the JS bundle into the HTML so there is no separate
            # app.js fetch for a fetch-hooking extension to clip.
            self._send_bytes(self._inline_index(), _CONTENT_TYPES["html"],
                             extra_headers={"Cache-Control": "no-store",
                                            "Connection": "close"})
            return
        # Allow cache-busting version queries (?v=N) without 404-ing: strip the
        # query so /app.js?v=3 still resolves to the real app.js. A fresh URL
        # defeats any poisoned HTTP cache that no-store can't purge.
        path = path.split("?", 1)[0]
        target = (WEB_DIR / path.lstrip("/")).resolve()
        if not str(target).startswith(str(WEB_DIR.resolve())):
            self._send_json({"ok": False, "error": "forbidden"}, code=403)
            return
        if not target.exists() or not target.is_file():
            self._send_json({"ok": False, "error": "not found"}, code=404)
            return
        ctype = _CONTENT_TYPES.get(target.suffix.lstrip("."), "application/octet-stream")
        # No-cache: the canvas is a live dev bundle; never let the browser
        # serve a stale app.js/app.css and silently run old key handlers.
        # Connection: close forces a clean EOF so a fetch-hooking extension
        # can't hold the stream open and clip the module (truncated SyntaxError).
        self._send_bytes(target.read_bytes(), ctype,
                         extra_headers={"Cache-Control": "no-store",
                                        "Connection": "close"})

    def log_message(self, *args: Any) -> None:  # quiet
        return


def make_server(host: str = "127.0.0.1", port: int = 8731) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), Handler)


# --------------------------------------------------------------------------- #
# Shared-engine dispatch daemon (one per gateway process)
# --------------------------------------------------------------------------- #
# A single DispatchLoop serves the shared Octane queue. It is guarded by a lock
# so the gateway never starts two loops. The filesystem render.lock inside
# DispatchLoop still serializes this daemon against any OTHER actor (cron tick,
# hand-rolled drain) — so the engine is never double-driven even if both run.
_dispatch_loop: Optional[DispatchLoop] = None
_dispatch_lock = threading.Lock()
# Serializes Octane renders kicked off via /canvas/to-octane (one engine at a time).
_render_lock = threading.Lock()


def _read_status_safe(timeout_seconds: float = 1.5) -> dict:
    """Read Octane status.json without blocking the request thread.

    The file lives in the Octane container FS and can stall on read while the
    bridge rewrites it during a render. Guard the read in a worker thread and
    fall back to a minimal status object on timeout so /status always answers.
    """
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(read_status)
        try:
            return fut.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError:
            return {"render_stage": "unknown", "error": "status.json read timed out",
                    "hint": "Octane container FS read stalled; progress may lag"}
        except Exception as exc:  # noqa: BLE001
            return {"render_stage": "unknown", "error": f"status read failed: {exc}"}


def start_dispatch_daemon(
    *,
    poll_seconds: float = 15.0,
    drain_timeout: int = 240,
    max_retries: int = 5,
) -> Dict[str, Any]:
    """Idempotently start the background dispatch loop (no-op if already running)."""
    global _dispatch_loop
    with _dispatch_lock:
        if _dispatch_loop is not None and not _dispatch_loop._stop:
            return {"ok": True, "running": True, "already": True}
        loop = DispatchLoop(
            poll_seconds=poll_seconds,
            drain_timeout=drain_timeout,
            max_retries=max_retries,
        )
        _dispatch_loop = loop
    t = threading.Thread(target=loop.run, name="octanex-dispatch", daemon=True)
    t.start()
    return {"ok": True, "running": True, "already": False}


def stop_dispatch_daemon() -> Dict[str, Any]:
    global _dispatch_loop
    with _dispatch_lock:
        loop = _dispatch_loop
        _dispatch_loop = None
    if loop is not None:
        loop.stop()
        return {"ok": True, "stopped": True}
    return {"ok": True, "stopped": False}


def dispatch_status() -> Dict[str, Any]:
    with _dispatch_lock:
        loop = _dispatch_loop
    if loop is None:
        return {"ok": True, "running": False, "loop": None}
    return {"ok": True, "running": not loop._stop, "loop": loop.status()}


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="OctaneX Agentic Canvas HTTP gateway")
    ap.add_argument("--port", type=int, default=int(os.environ.get("OCTANEX_GATEWAY_PORT", "8731")))
    ap.add_argument("--host", default=os.environ.get("OCTANEX_GATEWAY_HOST", "127.0.0.1"))
    ap.add_argument(
        "--dispatch",
        action="store_true",
        help="auto-start the shared-engine dispatch loop (serves the job queue)",
    )
    ap.add_argument("--dispatch-poll", type=float, default=float(os.environ.get("OCTANEX_DISPATCH_POLL", "15.0")))
    ap.add_argument("--dispatch-drain-timeout", type=int, default=int(os.environ.get("OCTANEX_DISPATCH_DRAIN", "240")))
    args = ap.parse_args()
    if args.dispatch:
        start_dispatch_daemon(poll_seconds=args.dispatch_poll, drain_timeout=args.dispatch_drain_timeout)
        print(f"octanex dispatch loop enabled (poll={args.dispatch_poll}s)", flush=True)
    server = make_server(args.host, args.port)
    print(f"octanex gateway listening on http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop_dispatch_daemon()
        server.server_close()


if __name__ == "__main__":
    main()
