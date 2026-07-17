"""Offline tests for the LuisaRender scene compiler (no CLI required)."""

from __future__ import annotations

import unittest

from octanex_mcp import canvas_scene as cs
from octanex_mcp.backends.luisa import compile_scene


class TestLuisaCompileOffline(unittest.TestCase):
    """Scene → .luisa text generation. No luisa-render-cli needed."""

    def test_default_scene_compiles(self):
        scene = cs.default_scene()
        text, sidecars = compile_scene(scene, spp=4, resolution=(64, 64))
        self.assertIn("Surface neutral_matte : Matte", text)
        self.assertIn("Shape cube : InlineMesh", text)
        self.assertIn("Camera camera : Pinhole", text)
        self.assertIn("spp { 4 }", text)
        self.assertIn("resolution { 64, 64 }", text)
        self.assertIn("integrator : MegaPath", text)
        self.assertIn("environment : Null {}", text)
        # Box is emitted inline — no sidecars.
        self.assertEqual(sidecars, [])

    def test_bar_scene_compiles_five_boxes(self):
        scene = cs.plan_scene("bar chart")
        text, sidecars = compile_scene(scene, spp=4, resolution=(64, 64))
        self.assertEqual(text.count("Shape bar_"), 5)
        # Planner sets roughness=0.5 → Matte (per documented mapping).
        self.assertIn("Surface bar_mat_0 : Matte", text)
        # Camera from the plan: above + back, target slightly above origin.
        self.assertIn("position { 0, 4, 9 }", text)
        self.assertEqual(sidecars, [])

    def test_low_roughness_maps_to_plastic(self):
        scene = cs.default_scene()
        scene["materials"][0]["roughness"] = 0.2
        text, _ = compile_scene(scene, spp=4, resolution=(64, 64))
        self.assertIn("Surface neutral_matte : Plastic", text)

    def test_emissive_material_gets_shape_light(self):
        scene = cs.plan_scene("orbital decay")
        text, sidecars = compile_scene(scene, spp=4, resolution=(64, 64))
        # Emissive cyan orbit path should produce a light block.
        self.assertIn("light : Diffuse {", text)
        self.assertIn("emission : Constant {", text)
        # Sphere (earth) goes to a Mesh shape with a sidecar OBJ.
        self.assertIn("Shape earth : Mesh", text)
        fnames = [f for f, _ in sidecars]
        self.assertTrue(any(f.endswith("_sphere.obj") for f in fnames))

    def test_metal_material_uses_named_metal(self):
        scene = cs.default_scene()
        scene["materials"][0]["metalness"] = 0.9
        scene["materials"][0]["roughness"] = 0.2
        text, _ = compile_scene(scene, spp=4, resolution=(64, 64))
        self.assertIn("Surface neutral_matte : Metal", text)
        self.assertIn('eta { "Al" }', text)

    def test_opacity_below_one_uses_glass(self):
        scene = cs.default_scene()
        scene["materials"][0]["opacity"] = 0.5
        text, _ = compile_scene(scene, spp=4, resolution=(64, 64))
        self.assertIn("Surface neutral_matte : Glass", text)
        self.assertIn("eta : Constant", text)

    def test_text_label_is_skipped(self):
        scene = cs.default_scene()
        scene["objects"].append({
            "id": "lbl",
            "type": "text_label",
            "position": [0, 1, 0],
            "material": "neutral_matte",
        })
        text, _ = compile_scene(scene, spp=4, resolution=(64, 64))
        self.assertNotIn("Shape lbl", text)

    def test_polyline_emits_nodes_and_links(self):
        scene = {
            "schema_version": "canvas.scene.v1",
            "scene_id": "pline",
            "camera": {"position": [0, 2, 4], "target": [0, 0, 0], "fov": 45},
            "environment": {},
            "objects": [{
                "id": "path",
                "type": "polyline",
                "points": [[0, 0, 0], [1, 0, 0], [1, 1, 0]],
                "radius": 0.05,
                "material": "m",
            }],
            "materials": [{"id": "m", "color": "#35e0d8"}],
        }
        text, sidecars = compile_scene(scene, spp=4, resolution=(64, 64))
        # 3 nodes + 2 links = 5 shape headers containing "Shape path_"
        self.assertEqual(text.count("Shape path_"), 5)
        self.assertEqual(len(sidecars), 5)

    def test_resolution_and_spp_configurable(self):
        scene = cs.default_scene()
        text, _ = compile_scene(scene, spp=256, resolution=(1920, 1080))
        self.assertIn("spp { 256 }", text)
        self.assertIn("resolution { 1920, 1080 }", text)

    def test_every_shape_has_explicit_transform(self):
        # Grammar grounding check: glass-of-water + tungsten2luisa both always
        # attach `transform : Matrix { m { 16 floats } }` to every Shape.
        scene = cs.plan_scene("bar chart")
        text, _ = compile_scene(scene, spp=4, resolution=(64, 64))
        shape_count = text.count("Shape ")
        transform_count = text.count("transform : Matrix {")
        self.assertGreater(shape_count, 0)
        self.assertEqual(shape_count, transform_count)


if __name__ == "__main__":
    unittest.main()
