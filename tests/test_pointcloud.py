"""Tests for core point-cloud readers and particle-cloud scene generation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from octanex_mcp.bridge import Workspace
from octanex_mcp.pointcloud import (
    PointCloudFormatError,
    create_particle_cloud_obj,
    load_point_cloud,
    normalize_points,
    particle_cloud_scene_commands,
    point_cloud_to_asset,
    supported_point_cloud_formats,
)
from octanex_mcp.server import build_mcp

try:
    import xarray as xr  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional dependency gate
    xr = None


class PointCloudTests(unittest.TestCase):
    def test_csv_with_named_columns_loads_and_normalizes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "points.csv"
            source.write_text("x,y,z,label\n0,0,0,a\n10,5,2,b\n", encoding="utf-8")
            loaded = load_point_cloud(source)
            normalized, metadata = normalize_points(loaded["points"])

        self.assertEqual(loaded["metadata"]["point_count"], 2)
        self.assertEqual(loaded["metadata"]["source_bounds"]["max"], [10.0, 5.0, 2.0])
        self.assertEqual(metadata["target_extent"], 6.0)
        self.assertEqual(normalized[0], (-3.0, -1.5, -0.6))
        self.assertEqual(normalized[1], (3.0, 1.5, 0.6))

    def test_xyz_ascii_ply_and_2d_geojson_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "points.xyz").write_text("# example\n1 2 3\n4 5 6\n", encoding="utf-8")
            (root / "points.ply").write_text(
                "ply\nformat ascii 1.0\nelement vertex 2\nproperty float x\nproperty float y\nproperty float z\nend_header\n1 2 3\n4 5 6\n",
                encoding="utf-8",
            )
            (root / "points.geojson").write_text(
                '{"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Point","coordinates":[4,5]}}]}',
                encoding="utf-8",
            )
            xyz = load_point_cloud(root / "points.xyz")
            ply = load_point_cloud(root / "points.ply")
            geojson = load_point_cloud(root / "points.geojson")

        self.assertEqual(xyz["points"], [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        self.assertEqual(ply["points"], xyz["points"])
        self.assertEqual(geojson["points"], [[4.0, 5.0, 0.0]])

    def test_particle_asset_has_spheres_and_safe_render_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Workspace(Path(tmp))
            asset = create_particle_cloud_obj([[0, 0, 0], [1, 1, 1]], name="cloud", point_size=0.2, workspace=workspace)
            commands = particle_cloud_scene_commands(asset, color=[0.1, 0.5, 1.0], preview_path="renders/cloud.png")
            obj = Path(asset["path"]).read_text(encoding="utf-8")

        self.assertEqual(asset["kind"], "particle_cloud")
        self.assertEqual(asset["point_count"], 2)
        self.assertGreater(obj.count("\nv "), 70)
        self.assertEqual([command["op"] for command in commands][-1], "save_preview")
        self.assertNotIn("start_render", [command["op"] for command in commands])
        self.assertEqual(commands[-1]["payload"]["path"], "renders/cloud.png")

    def test_particle_asset_supports_lighter_voxel_primitive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            asset = create_particle_cloud_obj([[0, 0, 0], [1, 1, 1]], name="voxels", primitive="cube", workspace=Workspace(Path(tmp)))
            obj = Path(asset["path"]).read_text(encoding="utf-8")

        self.assertEqual(asset["primitive"], "cube")
        self.assertEqual(obj.count("\nv "), 16)

    def test_point_cloud_asset_caps_source_and_rejects_unknown_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "many.pts"
            source.write_text("\n".join(f"{i} {i + 1} {i + 2}" for i in range(20)), encoding="utf-8")
            asset = point_cloud_to_asset(source, max_points=5, workspace=Workspace(root / "workspace"))
            self.assertTrue(Path(asset["path"]).exists())
            unknown = root / "points.las"
            unknown.write_text("not a LAS file", encoding="utf-8")
            with self.assertRaises(PointCloudFormatError):
                load_point_cloud(unknown)

        self.assertEqual(asset["point_count"], 5)

    def test_netcdf_3d_scalar_field_selects_strongest_samples(self) -> None:
        if xr is None:
            self.skipTest("pointcloud extra not installed")
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "field.nc"
            data = xr.DataArray(
                [[[0.0, 1.0], [2.0, 3.0]], [[4.0, 5.0], [6.0, 99.0]]],
                dims=("z", "y", "x"),
                coords={"z": [0.0, 10.0], "y": [0.0, 20.0], "x": [0.0, 30.0]},
            )
            xr.Dataset({"density": data}).to_netcdf(source)
            loaded = load_point_cloud(source, variable="density", max_points=3)

        self.assertEqual(loaded["metadata"]["format"], "netcdf")
        self.assertEqual(loaded["metadata"]["variable"], "density")
        self.assertEqual(loaded["metadata"]["point_count"], 3)
        self.assertIn([30.0, 20.0, 10.0], loaded["points"])

    def test_tool_registration_and_format_advertisement(self) -> None:
        names = {tool.name for tool in build_mcp()._tool_manager.list_tools()}
        self.assertIn("octane_visualize_point_cloud", names)
        self.assertIn(".csv", supported_point_cloud_formats()["core"])
        self.assertIn(".nc", supported_point_cloud_formats()["optional"])


if __name__ == "__main__":
    unittest.main()