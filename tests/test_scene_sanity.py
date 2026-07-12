from __future__ import annotations

import unittest

from octanex_mcp import sanity


def _graph(*nodes: dict) -> dict:
    return {"nodes": list(nodes), "count": len(nodes)}


# A render target the bridge canonically names "Hermes Render Target".
RT = {"type": "Render Target", "name": "Hermes Render Target", "connected": ["Hermes Camera"]}
CAM = {"type": "Camera", "name": "Hermes Camera", "connected": ["Hermes Render Target"],
        "position": [5, 5, 5], "target": [0, 0, 0]}
SUN = {"type": "Daylight", "name": "Hermes Environment", "connected": []}


class LiveGraphTests(unittest.TestCase):
    def test_healthy_graph_passes(self) -> None:
        mesh = {"type": "Mesh", "name": "M", "has_geometry": True,
                 "has_material": True, "connected": ["Mat"]}
        mat = {"type": "Material", "name": "Mat", "connected": ["M"]}
        rep = sanity.analyze_scene_graph(_graph(RT, CAM, SUN, mesh, mat))
        self.assertTrue(rep.ok)
        self.assertEqual(rep.errors, [])
        self.assertEqual(rep.warnings, [])

    def test_missing_render_target_is_error(self) -> None:
        rep = sanity.analyze_scene_graph(_graph(CAM, SUN))
        self.assertFalse(rep.ok)
        codes = {i.code for i in rep.errors}
        self.assertIn("no_render_target", codes)

    def test_missing_camera_is_error(self) -> None:
        rep = sanity.analyze_scene_graph(_graph(RT, SUN))
        self.assertIn("no_camera", {i.code for i in rep.errors})

    def test_camera_not_wired_to_rt_is_warning_unless_strict(self) -> None:
        cam = {"type": "Camera", "name": "C", "connected": []}
        rep = sanity.analyze_scene_graph(_graph(RT, cam, SUN))
        self.assertNotIn("camera_not_connected_to_rt", {i.code for i in rep.errors})
        self.assertIn("camera_not_connected_to_rt", {i.code for i in rep.warnings})
        rep_s = sanity.analyze_scene_graph(_graph(RT, cam, SUN), strict=True)
        self.assertIn("camera_not_connected_to_rt", {i.code for i in rep_s.errors})

    def test_no_light_is_warning_unless_strict(self) -> None:
        mesh = {"type": "Mesh", "name": "M", "has_geometry": True, "has_material": True}
        rep = sanity.analyze_scene_graph(_graph(RT, CAM, mesh))
        self.assertIn("no_light_environment", {i.code for i in rep.warnings})
        rep_s = sanity.analyze_scene_graph(_graph(RT, CAM, mesh), strict=True)
        self.assertIn("no_light_environment", {i.code for i in rep_s.errors})

    def test_mesh_missing_geometry_or_material_is_error(self) -> None:
        m1 = {"type": "Mesh", "name": "M1", "has_geometry": False, "has_material": True, "connected": []}
        m2 = {"type": "Mesh", "name": "M2", "has_geometry": True, "has_material": False, "connected": []}
        rep = sanity.analyze_scene_graph(_graph(RT, CAM, SUN, m1, m2))
        codes = {i.code for i in rep.errors}
        self.assertIn("mesh_missing_geometry", codes)
        self.assertIn("mesh_unassigned_material", codes)

    def test_orphan_material_is_warning(self) -> None:
        mat = {"type": "Material", "name": "Orphan", "connected": []}
        rep = sanity.analyze_scene_graph(_graph(RT, CAM, SUN, mat))
        self.assertIn("orphan_material", {i.code for i in rep.warnings})

    def test_zero_or_negative_scale_is_error(self) -> None:
        mesh = {"type": "Mesh", "name": "BadScale", "has_geometry": True,
                 "has_material": True, "scale": [0.0, -1.0, 2.0]}
        rep = sanity.analyze_scene_graph(_graph(RT, CAM, SUN, mesh))
        self.assertIn("scale_zero_or_negative", {i.code for i in rep.errors})

    def test_malformed_harvest_reports_error_not_raises(self) -> None:
        rep = sanity.analyze_scene_graph({})
        self.assertFalse(rep.ok)
        self.assertIn("harvest_malformed", {i.code for i in rep.errors})

    def test_type_matching_is_fuzzy(self) -> None:
        # Octane locale/build variants should still classify.
        self.assertTrue(sanity._is_render_target("Render Target"))
        self.assertTrue(sanity._is_render_target("RenderTarget"))
        self.assertTrue(sanity._is_camera("Camera"))
        self.assertTrue(sanity._is_light("Sun Light"))
        self.assertTrue(sanity._is_environment("Environment"))
        self.assertTrue(sanity._is_mesh("Geometry Mesh"))


class ManifestPlanTests(unittest.TestCase):
    def _plan(self, **overrides) -> dict:
        base = {
            "scene_id": "demo",
            "objects": [
                {"id": "box", "type": "box", "size": [2, 1, 0.5],
                 "material": "matte",
                 "bounds": {"center": [0.0, 0.0, 0.0], "radius": 2.0}},
            ],
            "materials": [{"name": "matte", "kind": "glossy"}],
            "camera": {"position": [4, 4, 4], "target": [0, 0, 0], "fov": 45},
            "lighting": {"preset": "soft_studio"},
        }
        base.update(overrides)
        return base

    def test_healthy_plan_passes(self) -> None:
        rep = sanity.analyze_scene_plan(self._plan())
        self.assertTrue(rep.ok)

    def test_no_camera_is_error(self) -> None:
        rep = sanity.analyze_scene_plan(self._plan(camera={}))
        self.assertIn("no_camera", {i.code for i in rep.errors})

    def test_invalid_camera_vectors_are_errors(self) -> None:
        rep = sanity.analyze_scene_plan(self._plan(
            camera={"position": [1, 2], "target": [0, 0, 0]}))
        self.assertIn("camera_position_invalid", {i.code for i in rep.errors})
        rep2 = sanity.analyze_scene_plan(self._plan(
            camera={"position": [1, 2, 3], "target": "nope"}))
        self.assertIn("camera_target_invalid", {i.code for i in rep2.errors})

    def test_mesh_object_missing_path_is_error(self) -> None:
        bad = self._plan(objects=[{"id": "m", "type": "mesh", "material": "matte"}])
        rep = sanity.analyze_scene_plan(bad)
        self.assertIn("object_missing_path", {i.code for i in rep.errors})

    def test_primitive_object_needs_no_path(self) -> None:
        # A 'box' primitive has its OBJ generated at build time.
        rep = sanity.analyze_scene_plan(self._plan())
        self.assertNotIn("object_missing_path", {i.code for i in rep.errors})

    def test_unused_material_is_warning(self) -> None:
        plan = self._plan(materials=[{"name": "matte"}, {"name": "unused"}])
        rep = sanity.analyze_scene_plan(plan)
        self.assertIn("material_unused", {i.code for i in rep.warnings})

    def test_zero_scale_transform_is_error(self) -> None:
        objs = [{"id": "b", "type": "box", "transform": {"scale": [0, 1, 1]}}]
        rep = sanity.analyze_scene_plan(self._plan(objects=objs))
        self.assertIn("scale_zero_or_negative", {i.code for i in rep.errors})

    def test_camera_too_far_flags_tiny_object(self) -> None:
        plan = self._plan(camera={"position": [60, 60, 60], "target": [0, 0, 0], "fov": 45})
        rep = sanity.analyze_scene_plan(plan)
        self.assertIn("camera_too_far", {i.code for i in rep.errors})

    def test_camera_inside_geometry_is_error(self) -> None:
        plan = self._plan(camera={"position": [0, 0, 0.1], "target": [0, 0, 0], "fov": 45})
        rep = sanity.analyze_scene_plan(plan)
        self.assertIn("camera_inside_geometry", {i.code for i in rep.errors})

    def test_camera_too_close_warns_clip(self) -> None:
        plan = self._plan(camera={"position": [1.0, 1.0, 1.0], "target": [0, 0, 0], "fov": 45})
        rep = sanity.analyze_scene_plan(plan)
        # radius 2, margin fit ~ 2.4; distance ~1.73 < 0.6*fit => too close
        self.assertIn("camera_too_close", {i.code for i in rep.warnings})

    def test_no_lighting_is_warning_unless_strict(self) -> None:
        rep = sanity.analyze_scene_plan(self._plan(lighting={}))
        self.assertIn("no_light_environment", {i.code for i in rep.warnings})
        rep_s = sanity.analyze_scene_plan(self._plan(lighting={}), strict=True)
        self.assertIn("no_light_environment", {i.code for i in rep_s.errors})

    def test_report_serializes_to_dict(self) -> None:
        rep = sanity.analyze_scene_plan(self._plan())
        d = rep.as_dict()
        self.assertIn("ok", d)
        self.assertIn("issues", d)
        self.assertIn("summary", d)
        self.assertEqual(d["summary"]["errors"], len(rep.errors))


if __name__ == "__main__":
    unittest.main()
