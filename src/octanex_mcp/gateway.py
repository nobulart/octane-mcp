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
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Dict, Optional

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
from octanex_mcp.scene import swap_geometry

WEB_DIR_DEFAULT = Path(__file__).resolve().parents[2] / "apps" / "octanex-canvas" / "web"
WEB_DIR = Path(os.environ.get("OCTANEX_GATEWAY_WEB_DIR", str(WEB_DIR_DEFAULT)))


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
    def _send_json(self, obj: Any, code: int = 200) -> None:
        body = json.dumps(_to_jsonable(obj), indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", _CONTENT_TYPES["json"])
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, data: bytes, content_type: str, code: int = 200) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
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
        if path == "/status":
            self._send_json(read_status())
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
            entry = {"ts": datetime.now(timezone.utc).isoformat(), "text": text}
            log = Workspace().root / "intents.jsonl"
            try:
                with log.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(entry) + "\n")
            except OSError:
                pass
            self._send_json({"ok": True, "queued": True, "text": text})
            return
        if path == "/remote/render":
            self._send_json(run_remote_bridge_and_pull(), code=200)
            return
        self._send_json({"ok": False, "error": "unknown route"}, code=404)

    # --- static ------------------------------------------------------------ #
    def _serve_static(self, path: str) -> None:
        if path in ("", "/"):
            path = "/index.html"
        target = (WEB_DIR / path.lstrip("/")).resolve()
        if not str(target).startswith(str(WEB_DIR.resolve())):
            self._send_json({"ok": False, "error": "forbidden"}, code=403)
            return
        if not target.exists() or not target.is_file():
            self._send_json({"ok": False, "error": "not found"}, code=404)
            return
        ctype = _CONTENT_TYPES.get(target.suffix.lstrip("."), "application/octet-stream")
        self._send_bytes(target.read_bytes(), ctype)

    def log_message(self, *args: Any) -> None:  # quiet
        return


def make_server(host: str = "127.0.0.1", port: int = 8731) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), Handler)


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="OctaneX Agentic Canvas HTTP gateway")
    ap.add_argument("--port", type=int, default=int(os.environ.get("OCTANEX_GATEWAY_PORT", "8731")))
    ap.add_argument("--host", default=os.environ.get("OCTANEX_GATEWAY_HOST", "127.0.0.1"))
    args = ap.parse_args()
    server = make_server(args.host, args.port)
    print(f"octanex gateway listening on http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
