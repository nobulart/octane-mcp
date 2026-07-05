from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

from octanex_mcp.bridge import Workspace, create_simple_obj
from octanex_mcp.visuals import camera_for_bounds, create_bar_chart_obj, create_surface_obj, scene_commands_for_asset


class BoundsCameraTests(unittest.TestCase):
    def test_generated_bar_chart_includes_bounds_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            asset = create_bar_chart_obj([1, -2, 3], name="bounded_bars", workspace=Workspace(Path(tmp)))

        bounds = asset["bounds"]
        self.assertEqual(bounds["min"], [-1.85, -0.6, -1.733333])
        self.assertEqual(bounds["max"], [1.85, 0.55, 2.6])
        self.assertEqual(bounds["center"], [0.0, -0.025, 0.433333])
        self.assertGreater(bounds["radius"], 2.4)

    def test_surface_bounds_cover_scaled_height_field_and_base(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            asset = create_surface_obj("x + y", name="bounded_surface", x_range=(-1, 1), y_range=(-2, 2), steps=8, workspace=Workspace(Path(tmp)))

        bounds = asset["bounds"]
        self.assertEqual(bounds["min"], [-1.2, -2.2, -1.6])
        self.assertEqual(bounds["max"], [1.2, 2.2, 1.6])
        self.assertAlmostEqual(bounds["center"][2], 0.0, places=6)
        self.assertGreater(bounds["radius"], 2.7)

    def test_camera_for_bounds_uses_center_and_margin(self) -> None:
        bounds = {"min": [-1, -1, 0], "max": [1, 1, 2], "center": [0, 0, 1], "radius": math.sqrt(3)}

        camera = camera_for_bounds(bounds, view="front", margin=2.0, fov=35)

        self.assertEqual(camera["target"], [0.0, 0.0, 1.0])
        self.assertEqual(camera["fov"], 35)
        self.assertAlmostEqual(camera["position"][0], 0.0, places=6)
        self.assertLess(camera["position"][1], -6.0)
        self.assertAlmostEqual(camera["position"][2], 1.0, places=6)

    def test_scene_commands_use_asset_bounds_for_camera(self) -> None:
        asset = {
            "path": "/tmp/bounded.obj",
            "name": "bounded",
            "bounds": {"min": [-2, -1, 0], "max": [2, 1, 4], "center": [0, 0, 2], "radius": 3.0},
        }

        commands = scene_commands_for_asset(asset, material_name="mat", color=[1, 1, 1])

        camera = commands[3]
        self.assertEqual(camera["op"], "set_camera")
        self.assertEqual(camera["payload"]["target"], [0.0, 0.0, 2.0])
        self.assertGreater(camera["payload"]["position"][2], 2.0)

    def test_simple_cube_includes_bounds_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            asset = create_simple_obj("bounded_cube", 2.0, Workspace(Path(tmp)))

        self.assertEqual(asset["bounds"]["min"], [-1.0, -1.0, -1.0])
        self.assertEqual(asset["bounds"]["max"], [1.0, 1.0, 1.0])
        self.assertEqual(asset["bounds"]["center"], [0.0, 0.0, 0.0])
        self.assertAlmostEqual(asset["bounds"]["radius"], math.sqrt(3), places=6)


if __name__ == "__main__":
    unittest.main()
