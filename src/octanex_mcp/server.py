from __future__ import annotations

import argparse
import json
from typing import Any, Dict, Optional

from .bridge import (
    Workspace,
    concept_to_commands,
    create_simple_obj,
    list_commands,
    octane_app_status,
    read_recipe_book,
    read_status,
    record_recipe_entry,
    write_command,
)
from .visuals import create_avatar_face_obj, create_bar_chart_obj, create_surface_obj, scene_commands_for_asset

try:
    from mcp.server.fastmcp import FastMCP
except Exception:  # pragma: no cover - exercised when deps are missing
    FastMCP = None  # type: ignore


def _json(data: Dict[str, Any]) -> str:
    return json.dumps(data, indent=2)


def build_mcp() -> Any:
    if FastMCP is None:
        raise RuntimeError("mcp package is not installed. Run: uv sync")

    mcp = FastMCP("octanex-mcp")

    @mcp.tool()
    def octane_status() -> str:
        """Return Octane X app, bridge heartbeat, and command queue status."""
        return _json({"app": octane_app_status(), "commands": list_commands()})

    @mcp.tool()
    def octane_recipe_book(limit_chars: int = 12000) -> str:
        """Read the local OctaneX MCP recipe book of successes, failures, and reusable patterns."""
        return _json(read_recipe_book(limit_chars=limit_chars))

    @mcp.tool()
    def octane_record_recipe(
        title: str,
        outcome: str,
        context: str,
        steps: list[str],
        signals: Optional[list[str]] = None,
        follow_ups: Optional[list[str]] = None,
    ) -> str:
        """Append a compact success/failure note to docs/recipe-book.md for future agents."""
        return _json(record_recipe_entry(
            title=title,
            outcome=outcome,
            context=context,
            steps=steps,
            signals=signals or [],
            follow_ups=follow_ups or [],
        ))

    @mcp.tool()
    def octane_ping(message: str = "hello from Hermes") -> str:
        """Queue a ping command for the Octane Lua bridge."""
        return _json(write_command("ping", {"message": message}))

    @mcp.tool()
    def octane_create_test_cube(name: str = "mcp_cube", size: float = 1.0) -> str:
        """Create a small OBJ cube asset and queue an import_geometry command."""
        asset = create_simple_obj(name=name, size=size)
        queued = write_command("import_geometry", {"path": asset["path"], "format": "obj", "name": asset["name"]})
        return _json({"asset": asset, "command": queued})

    @mcp.tool()
    def octane_import_geometry(path: str, name: Optional[str] = None, format: str = "auto") -> str:
        """Queue an import_geometry command for OBJ/USD/FBX/Alembic/etc."""
        return _json(write_command("import_geometry", {"path": path, "format": format, "name": name}))

    @mcp.tool()
    def octane_create_material(
        name: str,
        kind: str = "glossy",
        color: Optional[list[float]] = None,
        roughness: float = 0.25,
        metallic: float = 0.0,
    ) -> str:
        """Queue a material creation/update command."""
        return _json(write_command("create_material", {
            "name": name,
            "kind": kind,
            "color": color or [0.8, 0.8, 0.8],
            "roughness": roughness,
            "metallic": metallic,
        }))

    @mcp.tool()
    def octane_assign_material(object_name: str, material_name: str) -> str:
        """Queue a material assignment command."""
        return _json(write_command("assign_material", {"object_name": object_name, "material_name": material_name}))

    @mcp.tool()
    def octane_set_camera(position: list[float], target: list[float], fov: float = 45.0) -> str:
        """Queue a camera placement command."""
        return _json(write_command("set_camera", {"position": position, "target": target, "fov": fov}))

    @mcp.tool()
    def octane_set_lighting(preset: str = "soft_studio") -> str:
        """Queue a lighting preset command."""
        return _json(write_command("set_lighting", {"preset": preset}))

    @mcp.tool()
    def octane_start_render(samples: int = 128, width: int = 1280, height: int = 1280) -> str:
        """Queue a render start/restart command."""
        return _json(write_command("start_render", {"samples": samples, "width": width, "height": height}))

    @mcp.tool()
    def octane_save_preview(path: Optional[str] = None, width: int = 1280, height: int = 1280) -> str:
        """Queue a preview image save command."""
        return _json(write_command("save_preview", {"path": path, "width": width, "height": height}))

    @mcp.tool()
    def octane_build_concept(prompt: str) -> str:
        """Queue a high-level concept build request plus deterministic starter scene commands."""
        results = []
        cube = create_simple_obj(name="concept_anchor_cube", size=1.0)
        results.append(write_command("import_geometry", {"path": cube["path"], "format": "obj", "name": cube["name"]}))
        for cmd in concept_to_commands(prompt):
            results.append(write_command(cmd["op"], cmd["payload"]))
        return _json({"queued_commands": results, "status": read_status()})

    @mcp.tool()
    def octane_visualize_bars(values: list[float], name: str = "visual_bar_chart") -> str:
        """Visualize numeric values as a 3D bar chart in Octane."""
        asset = create_bar_chart_obj(values, name=name)
        material_name = f"{asset['name']}_cyan_material"
        commands = scene_commands_for_asset(asset, material_name=material_name, color=[0.05, 0.75, 1.0])
        results = [write_command(cmd["op"], cmd["payload"]) for cmd in commands]
        return _json({"asset": asset, "queued_commands": results, "status": read_status()})

    @mcp.tool()
    def octane_visualize_surface(
        expression: str = "sin(r) / max(r, 0.25)",
        name: str = "visual_math_surface",
        x_min: float = -3.0,
        x_max: float = 3.0,
        y_min: float = -3.0,
        y_max: float = 3.0,
        steps: int = 36,
    ) -> str:
        """Visualize z=f(x,y) as a 3D surface. Expression may use x, y, r and safe math funcs."""
        asset = create_surface_obj(expression, name=name, x_range=(x_min, x_max), y_range=(y_min, y_max), steps=steps)
        material_name = f"{asset['name']}_gold_material"
        commands = scene_commands_for_asset(asset, material_name=material_name, color=[1.0, 0.62, 0.12])
        results = [write_command(cmd["op"], cmd["payload"]) for cmd in commands]
        return _json({"asset": asset, "queued_commands": results, "status": read_status()})

    @mcp.tool()
    def octane_show_avatar(name: str = "hermes_avatar_face") -> str:
        """Show Hermes' geometric avatar face as a scene guide in Octane."""
        asset = create_avatar_face_obj(name=name)
        commands = scene_commands_for_asset(asset, material_name=f"{asset['name']}_warm_light", color=[0.88, 0.95, 1.0])
        commands[3] = {"op": "set_camera", "payload": {"position": [0, -4.5, 2.0], "target": [0, 0, 1.35], "fov": 38}}
        results = [write_command(cmd["op"], cmd["payload"]) for cmd in commands]
        return _json({"asset": asset, "queued_commands": results, "status": read_status()})

    return mcp


def self_test() -> Dict[str, Any]:
    ws = Workspace()
    ws.ensure()
    cube = create_simple_obj("self_test_cube", 0.5, ws)
    ping = write_command("ping", {"message": "self-test"}, ws)
    return {"ok": True, "app": octane_app_status(), "cube": cube, "ping": ping, "commands": list_commands(ws)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Octane X MCP server")
    parser.add_argument("--self-test", action="store_true", help="create workspace and queue a ping without starting MCP stdio")
    args = parser.parse_args()
    if args.self_test:
        print(_json(self_test()))
        return
    build_mcp().run()


if __name__ == "__main__":
    main()
