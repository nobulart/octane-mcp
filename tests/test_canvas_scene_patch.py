"""Tests for the canvas scene patching helpers (Phase 5 live edits)."""

import unittest

from octanex_mcp import canvas_scene as cs


class TestPatchObject(unittest.TestCase):
    def setUp(self):
        self.scene = cs.plan_scene("orbital decay")

    def test_patch_object_material_color(self):
        out = cs.patch_object(self.scene, "earth", {"material": {"color": "#ff0000"}})
        ok, _ = cs.validate_scene(out)
        self.assertTrue(ok)
        mat = next(m for m in out["materials"] if m["id"] == "blue_planet")
        self.assertEqual(mat["color"], "#ff0000")

    def test_patch_object_scale(self):
        out = cs.patch_object(self.scene, "earth", {"scale": [2, 2, 2]})
        earth = next(o for o in out["objects"] if o["id"] == "earth")
        self.assertEqual(earth["scale"], [2, 2, 2])

    def test_patch_object_opacity(self):
        out = cs.patch_object(self.scene, "earth", {"material": {"opacity": 0.3}})
        mat = next(m for m in out["materials"] if m["id"] == "blue_planet")
        self.assertEqual(mat["opacity"], 0.3)

    def test_patch_unknown_object_raises(self):
        with self.assertRaises(KeyError):
            cs.patch_object(self.scene, "ghost", {"scale": [1, 1, 1]})

    def test_patch_invalid_object_field_rejected(self):
        with self.assertRaises(ValueError):
            cs.patch_object(self.scene, "earth", {"bogus": 1})

    def test_patch_invalid_material_field_rejected(self):
        with self.assertRaises(ValueError):
            cs.patch_object(self.scene, "earth", {"material": {"nope": 1}})

    def test_patch_that_breaks_validation_rejected(self):
        # Remove a material reference validity by pointing at a missing material.
        with self.assertRaises(ValueError):
            cs.patch_object(self.scene, "earth", {"material": "does_not_exist"})


class TestPatchScene(unittest.TestCase):
    def setUp(self):
        self.scene = cs.plan_scene("cube")

    def test_patch_top_level_title(self):
        out = cs.patch_scene(self.scene, {"title": "Renamed"})
        self.assertEqual(out["title"], "Renamed")
        ok, _ = cs.validate_scene(out)
        self.assertTrue(ok)

    def test_patch_camera(self):
        out = cs.patch_scene(self.scene, {"camera": {"position": [1, 1, 1], "target": [0, 0, 0], "fov": 30}})
        self.assertEqual(out["camera"]["fov"], 30)

    def test_patch_disallowed_field_rejected(self):
        with self.assertRaises(ValueError):
            cs.patch_scene(self.scene, {"schema_version": "evil"})


if __name__ == "__main__":
    unittest.main()
