"""Tests for the canvas.scene.v1 schema and the deterministic stub planner."""

import unittest

from octanex_mcp import canvas_scene as cs


class TestSchemaValidate(unittest.TestCase):
    def test_default_scene_valid(self):
        ok, errors = cs.validate_scene(cs.default_scene())
        self.assertTrue(ok, errors)
        self.assertEqual(errors, [])

    def test_missing_schema_version_rejected(self):
        scene = cs.default_scene()
        del scene["schema_version"]
        ok, _ = cs.validate_scene(scene)
        self.assertFalse(ok)

    def test_unknown_object_type_rejected(self):
        scene = cs.default_scene()
        scene["objects"][0]["type"] = "banana"
        ok, errors = cs.validate_scene(scene)
        self.assertFalse(ok)
        self.assertTrue(any("banana" in e for e in errors))

    def test_missing_material_rejected(self):
        scene = cs.default_scene()
        scene["objects"][0]["material"] = "ghost"
        ok, errors = cs.validate_scene(scene)
        self.assertFalse(ok)
        self.assertTrue(any("ghost" in e for e in errors))

    def test_missing_camera_field_rejected(self):
        scene = cs.default_scene()
        del scene["camera"]["target"]
        ok, _ = cs.validate_scene(scene)
        self.assertFalse(ok)


class TestPlanner(unittest.TestCase):
    def _assert_valid(self, scene):
        ok, errors = cs.validate_scene(scene)
        self.assertTrue(ok, errors)

    def test_cube_intent(self):
        s = cs.plan_scene("show me a cube")
        self._assert_valid(s)
        self.assertEqual(s["objects"][0]["type"], "box")

    def test_sphere_intent(self):
        s = cs.plan_scene("render a sphere")
        self._assert_valid(s)
        self.assertEqual(s["objects"][0]["type"], "sphere")

    def test_orbit_intent(self):
        s = cs.plan_scene("show orbital decay as a timeline")
        self._assert_valid(s)
        types = {o["type"] for o in s["objects"]}
        self.assertIn("polyline", types)
        self.assertIn("sphere", types)

    def test_bar_chart_intent(self):
        s = cs.plan_scene("make a bar chart of the data")
        self._assert_valid(s)
        self.assertTrue(all(o["type"] == "box" for o in s["objects"]))
        self.assertGreater(len(s["objects"]), 1)

    def test_terrain_intent(self):
        s = cs.plan_scene("load the terrain heightmap")
        self._assert_valid(s)
        self.assertGreater(len(s["objects"]), 0)

    def test_unknown_intent_falls_back_to_demo(self):
        s = cs.plan_scene("do something weird")
        self._assert_valid(s)
        self.assertEqual(s["objects"][0]["type"], "box")

    def test_intent_preserved_in_scene(self):
        s = cs.plan_scene("orbital decay")
        self.assertEqual(s["intent"], "orbital decay")


if __name__ == "__main__":
    unittest.main()
