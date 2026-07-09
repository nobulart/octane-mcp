from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from octanex_mcp.bridge import Workspace
from octanex_mcp import geo
from octanex_mcp.geo import (
    GeoDependencyError,
    elevation_grid_to_obj,
    geo_asset_to_scene_commands,
    geojson_to_obj,
    is_geo_available,
    require_geo,
)


class ElevationGridTests(unittest.TestCase):
    def test_simple_grid_produces_bounds_and_obj(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            grid = [
                [0.0, 1.0, 0.0],
                [1.0, 2.0, 1.0],
                [0.0, 1.0, 0.0],
            ]
            asset = elevation_grid_to_obj(grid, name="demo_grid", workspace=Workspace(Path(tmp)))
            self.assertTrue(Path(asset["path"]).exists())
            self.assertEqual(asset["kind"], "elevation_grid")
            self.assertEqual(asset["rows"], 3)
            self.assertEqual(asset["cols"], 3)
            # Highest point is the center (2.0 * z_scale default 1.0)
            self.assertAlmostEqual(asset["bounds"]["max"][2], 2.0, places=3)
            self.assertAlmostEqual(asset["bounds"]["min"][2], -0.05, places=3)  # base slab below 0

    def test_z_scale_applied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            grid = [[3.0]]
            asset = elevation_grid_to_obj(grid, name="peak", z_scale=2.0, workspace=Workspace(Path(tmp)))
            self.assertAlmostEqual(asset["bounds"]["max"][2], 6.0, places=3)

    def test_empty_grid_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp))
            with self.assertRaises(ValueError):
                elevation_grid_to_obj([], workspace=ws)
            with self.assertRaises(ValueError):
                elevation_grid_to_obj([[]], workspace=ws)

    def test_elevation_scene_commands_use_bounds_camera(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            grid = [[0.0, 1.0], [1.0, 0.0]]
            asset = elevation_grid_to_obj(grid, workspace=Workspace(Path(tmp)))
        commands = geo_asset_to_scene_commands(asset, material_name="terrain_mat")
        self.assertEqual(commands[0]["op"], "import_geometry")
        self.assertEqual(commands[0]["payload"]["path"], asset["path"])
        self.assertEqual(commands[3]["op"], "set_camera")
        self.assertEqual(commands[3]["payload"]["target"], asset["bounds"]["center"])
        # Camera sits above/away from the surface to frame it (z above bounds max).
        self.assertGreater(commands[3]["payload"]["position"][2], asset["bounds"]["max"][2])


class GeoDependencyGateTests(unittest.TestCase):
    def test_is_geo_available_returns_bool(self) -> None:
        self.assertIn(is_geo_available(), (True, False))

    def test_geojson_without_extra_raises(self) -> None:
        if is_geo_available():
            self.skipTest("geo extra installed; cannot exercise missing-extra path here")
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp))
            with self.assertRaises(GeoDependencyError):
                geojson_to_obj({"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}, workspace=ws)
            # require_geo also raises
            with self.assertRaises(GeoDependencyError):
                require_geo()


class GeoJsonTests(unittest.TestCase):
    def test_geojson_polygon_extrudes_when_extra_present(self) -> None:
        if not is_geo_available():
            self.skipTest("geo extra not installed; shapely-backed path skipped")
        with tempfile.TemporaryDirectory() as tmp:
            polygon = {
                "type": "Polygon",
                "coordinates": [[[0.0, 0.0], [2.0, 0.0], [2.0, 1.0], [0.0, 1.0], [0.0, 0.0]]],
            }
            asset = geojson_to_obj(polygon, name="plot", workspace=Workspace(Path(tmp)))
            self.assertTrue(Path(asset["path"]).exists())
            self.assertEqual(asset["kind"], "geojson")
            self.assertEqual(asset["geometry_count"], 1)
            # Bounds span the polygon footprint plus the extruded wall height.
            self.assertAlmostEqual(asset["bounds"]["max"][0], 2.0, places=2)
            self.assertAlmostEqual(asset["bounds"]["max"][2], asset["z_extrude"], places=2)

    def test_geojson_feature_collection(self) -> None:
        if not is_geo_available():
            self.skipTest("geo extra not installed; shapely-backed path skipped")
        with tempfile.TemporaryDirectory() as tmp:
            fc = {
                "type": "FeatureCollection",
                "features": [
                    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [0.0, 0.0]}},
                    {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]}},
                ],
            }
            asset = geojson_to_obj(fc, name="fc", workspace=Workspace(Path(tmp)))
            self.assertEqual(asset["geometry_count"], 2)
            self.assertTrue(Path(asset["path"]).exists())


if __name__ == "__main__":
    unittest.main()
