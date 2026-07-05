from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from octanex_mcp.bridge import Workspace
from octanex_mcp.visuals import create_scatter_obj, scene_commands_for_asset


class ScatterGrammarTests(unittest.TestCase):
    def test_scatter_generator_creates_bounds_and_points(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            asset = create_scatter_obj([[0, 0, 0], [1, 2, 3], [-1, -2, 0.5]], name="demo_scatter", workspace=Workspace(Path(tmp)))
            self.assertTrue(Path(asset["path"]).exists())

        self.assertEqual(asset["kind"], "scatter")
        self.assertEqual(asset["point_count"], 3)
        self.assertEqual(asset["bounds"]["min"], [-1.16, -2.16, -0.176])
        self.assertEqual(asset["bounds"]["max"], [1.16, 2.16, 3.08])

    def test_scatter_scene_commands_use_bounds_camera(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            asset = create_scatter_obj([[10, 0, 0], [12, 2, 1]], workspace=Workspace(Path(tmp)))

        commands = scene_commands_for_asset(asset, material_name="scatter_mat", color=[1, 0.4, 0.1])

        self.assertEqual(commands[3]["op"], "set_camera")
        self.assertEqual(commands[3]["payload"]["target"], asset["bounds"]["center"])

    def test_scatter_rejects_empty_or_malformed_points(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp))
            with self.assertRaises(ValueError):
                create_scatter_obj([], workspace=ws)
            with self.assertRaises(ValueError):
                create_scatter_obj([[1, 2]], workspace=ws)


if __name__ == "__main__":
    unittest.main()
