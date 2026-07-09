"""Tests for the WP6 promoted-recipe MCP tools (octane_build_product_studio,
octane_build_planet_scene, octane_visualize_network) and their gateway parity.

WP6 wraps the three strongest *verified* recipes (photoreal-product-studio,
photoreal-earth-space / saturn-moons-space, network-graph) as first-class tools
so a downstream agent or Canvas UI can call by semantic name without knowing the
underlying recipe slugs. Each tool is a thin wrapper over `queue_recipe`, so the
offline behavior is just "write command files into a (temp) workspace queue" —
no Octane session required.

Run with: `PYTHONPATH= uv run python -m unittest tests.test_promoted_recipes`
"""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from octanex_mcp.bridge import Workspace
from octanex_mcp.recipes import queue_recipe
from octanex_mcp.server import build_mcp


def _call_tool(name: str, args: dict) -> dict:
    raw = asyncio.run(build_mcp()._tool_manager.call_tool(name, args))
    text = raw[1]["content"][0]["text"] if isinstance(raw, tuple) else raw
    return json.loads(text)


class PromotedRecipeToolTests(unittest.TestCase):
    def test_tools_register_on_server(self) -> None:
        names = {t.name for t in build_mcp()._tool_manager.list_tools()}
        for tool in (
            "octane_build_product_studio",
            "octane_build_planet_scene",
            "octane_visualize_network",
        ):
            self.assertIn(tool, names)

    def test_build_product_studio_queues_recipe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp) / "ws")
            result = queue_recipe(
                "photoreal-product-studio", workspace=ws, overrides={"start_render": {"samples": 8}}
            )
            self.assertEqual(result["slug"], "photoreal-product-studio")
            self.assertGreater(result["queued_count"], 0)
            self.assertEqual(len(list(ws.queue_dir.glob("*.json"))), result["queued_count"])

    def test_build_planet_scene_defaults_to_earth(self) -> None:
        data = _call_tool("octane_build_planet_scene", {"planet": "earth"})
        self.assertEqual(data["slug"], "photoreal-earth-space")
        self.assertGreater(data["queued_count"], 0)

    def test_build_planet_scene_saturn(self) -> None:
        data = _call_tool("octane_build_planet_scene", {"planet": "saturn"})
        self.assertEqual(data["slug"], "saturn-moons-space")

    def test_build_planet_scene_unknown_planet_falls_back_to_earth(self) -> None:
        data = _call_tool("octane_build_planet_scene", {"planet": "pluto"})
        self.assertEqual(data["slug"], "photoreal-earth-space")

    def test_visualize_network_queues_network_graph(self) -> None:
        data = _call_tool("octane_visualize_network", {})
        self.assertEqual(data["slug"], "network-graph")
        self.assertGreater(data["queued_count"], 0)

    def test_build_product_studio_queues_product_recipe(self) -> None:
        data = _call_tool("octane_build_product_studio", {})
        self.assertEqual(data["slug"], "photoreal-product-studio")
        self.assertGreater(data["queued_count"], 0)

    def test_gateway_parity_product_studio(self) -> None:
        # The HTTP gateway dispatch must agree with the MCP tool on the slug.
        from octanex_mcp import gateway

        result = gateway.call_tool("octane_build_product_studio", {"overrides": {}})
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["result"]["slug"], "photoreal-product-studio")

    def test_gateway_parity_planet_saturn(self) -> None:
        from octanex_mcp import gateway

        result = gateway.call_tool("octane_build_planet_scene", {"planet": "saturn"})
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["result"]["slug"], "saturn-moons-space")


if __name__ == "__main__":
    unittest.main()
