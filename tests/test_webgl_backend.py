"""Tests for the WebGLBackend and the shared Backend protocol."""

import unittest

from octanex_mcp.backends import Backend, FakeBackend, WebGLBackend, build_scene
from octanex_mcp import canvas_scene as cs


class TestBackendProtocol(unittest.TestCase):
    def test_fake_backend_satisfies_protocol(self):
        # FakeBackend must be a valid Backend (structural + nominal).
        self.assertIsInstance(FakeBackend(), Backend)
        self.assertEqual(FakeBackend().name, "fake")

    def test_webgl_backend_satisfies_protocol(self):
        self.assertIsInstance(WebGLBackend(), Backend)
        self.assertEqual(WebGLBackend().name, "webgl")

    def test_build_scene_passes_webgl_through(self):
        scene = cs.default_scene()
        out = build_scene(WebGLBackend(), scene)
        self.assertEqual(out["schema_version"], "canvas.scene.v1")
        self.assertEqual(out["scene_id"], scene["scene_id"])

    def test_build_scene_rejects_invalid_webgl_output(self):
        # A plan the WebGLBackend cannot normalise into a valid scene must raise.
        bad = {"objects": [{"id": "x", "type": "nope", "material": "ghost"}]}
        with self.assertRaises(ValueError):
            build_scene(WebGLBackend(), bad)


class TestWebGLBackend(unittest.TestCase):
    def setUp(self):
        self.b = WebGLBackend()

    def test_build_returns_valid_v1(self):
        out = self.b.build(cs.default_scene())
        ok, errors = cs.validate_scene(out)
        self.assertTrue(ok, errors)
        self.assertEqual(out["schema_version"], "canvas.scene.v1")

    def test_build_forwards_objects_and_materials(self):
        scene = cs.plan_scene("orbital decay")
        out = self.b.build(scene)
        ids = {o["id"] for o in out["objects"]}
        mat_ids = {m["id"] for m in out["materials"]}
        self.assertIn("orbit_path", ids)
        self.assertIn("cyan_emissive", mat_ids)
        # Every object references a defined material.
        for o in out["objects"]:
            if "material" in o:
                self.assertIn(o["material"], mat_ids)

    def test_build_strips_unknown_fields(self):
        scene = cs.default_scene()
        scene["objects"][0]["bogus_field"] = "x"
        scene["random_top_level"] = "y"
        out = self.b.build(scene)
        self.assertNotIn("bogus_field", out["objects"][0])
        self.assertNotIn("random_top_level", out)

    def test_build_emits_defaults_when_missing(self):
        scene = {"scene_id": "minimal", "objects": [], "materials": []}
        out = self.b.build(scene)
        self.assertIn("camera", out)
        self.assertIn("environment", out)
        self.assertIn("provenance", out)

    def test_render_preview_supported(self):
        res = self.b.render_preview(cs.default_scene())
        self.assertTrue(res["ok"])
        self.assertTrue(res["supported"])

    def test_save_png_not_supported(self):
        res = self.b.save_png(cs.default_scene())
        self.assertTrue(res["ok"])
        self.assertFalse(res["supported"])


if __name__ == "__main__":
    unittest.main()
