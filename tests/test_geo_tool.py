"""Tests for the WP7 geo MCP tool (octane_visualize_geojson) and its helpers.

The shapely-backed `geojson_to_obj` path requires the optional `geo` extra, which
is not part of the core install. These tests assert:

* the tool registers on the MCP server;
* the tool degrades gracefully (exact install hint, no traceback) when the extra
  is missing -- the correct offline behavior in a bare environment;
* `geo_asset_to_scene_commands` builds a valid bounds-camera command list without
  any optional dependency;
* the happy path (shapely present) queues asset + render commands.

Run with: `PYTHONPATH= uv run python -m unittest tests.test_geo_tool`
"""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from octanex_mcp import geo
from octanex_mcp.geo import geo_asset_to_scene_commands, is_geo_available
from octanex_mcp.server import build_mcp


def _call_geo(geojson):
    """Call the tool and return parsed dict (FastMCP call_tool returns the text)."""
    raw = asyncio.run(build_mcp()._tool_manager.call_tool("octane_visualize_geojson", {"geojson": geojson}))
    text = raw[1]["content"][0]["text"] if isinstance(raw, tuple) else raw
    return json.loads(text)


class GeoToolTests(unittest.TestCase):
    def test_tool_registers_on_server(self) -> None:
        names = {t.name for t in build_mcp()._tool_manager.list_tools()}
        self.assertIn("octane_visualize_geojson", names)

    def test_geo_asset_to_scene_commands_builds_bounds_camera(self) -> None:
        asset = {
            "path": "/tmp/geo_x.obj",
            "name": "geo_x",
            "bounds": {"center": [0.0, 0.0, 0.25], "radius": 3.0},
        }
        commands = geo_asset_to_scene_commands(asset, color=[0.1, 0.2, 0.3])
        ops = [c["op"] for c in commands]
        self.assertEqual(ops[0], "import_geometry")
        self.assertEqual(commands[0]["payload"]["path"], asset["path"])
        self.assertIn("create_material", ops)
        self.assertIn("assign_material", ops)
        self.assertIn("set_camera", ops)
        self.assertIn("start_render", ops)
        # Bounds camera should be derived from the asset bounds, not crash.
        self.assertIn("position", commands[ops.index("set_camera")]["payload"])

    def test_tool_graceful_missing_extra(self) -> None:
        # In a bare env shapely is absent -> the tool must report the install hint
        # and queue nothing, never raise a traceback.
        if is_geo_available():
            self.skipTest("geo extra is installed; testing happy path instead")
        sample = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
        data = _call_geo(sample)
        self.assertIn("error", data)
        self.assertIn("geo", data["error"].lower())
        self.assertEqual(data.get("hint"), "uv sync --extra geo")
        self.assertEqual(data.get("queued_commands"), [])

    def test_tool_happy_path_queues_commands(self) -> None:
        if not is_geo_available():
            self.skipTest("geo extra not installed; cannot exercise real geojson path")
        from shapely.geometry import Polygon

        geom = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        data = _call_geo(geom)
        self.assertNotIn("error", data)
        self.assertIn("asset", data)
        self.assertTrue(data["queued_commands"], data)
        # Assert the OBJ actually exists on disk.
        self.assertTrue(Path(data["asset"]["path"]).exists())


if __name__ == "__main__":
    unittest.main()
