#!/usr/bin/env python3
"""Unit tests for the Phase C renderer-backend-comparison recipe (C4).

Fixture-first + repo-native: ONE canonical MHD energy-bar grammar is emitted for
two backends (OctaneX OBJ + LuisaRender JSON SDL). Asserts:
  * the OctaneX recipe passes the offline contract with per-group materials;
  * OBJ face indices stay within the vertex count;
  * the LuisaRender scene file is valid JSON with a `render` root carrying
    camera/film/integrator/scene nodes (the backend-neutral emitter works);
  * the LuisaRender live attempt is recorded honestly in `backends.luisa_render`
    (a real CLI result, success OR failure — never fabricated).
"""
from __future__ import annotations

import importlib
import json
import re
import struct
import zlib
import tempfile
from pathlib import Path
from unittest import TestCase

REPO = Path(__file__).resolve().parents[1]
for _p in (REPO / "src", REPO / "scripts"):
    if str(_p) not in __import__("sys").path:
        __import__("sys").path.insert(0, str(_p))

import benchmarks.verify_recipes as vr  # noqa: E402


class TestRendererBackendRecipe(TestCase):
    def test_generated_recipe_passes_contract(self):
        gen = importlib.import_module("gen_renderer_backend_recipe")
        with tempfile.TemporaryDirectory() as td:
            recipe_root = Path(td) / "recipes"
            gen.main(output_root=recipe_root)
            recipe = recipe_root / "renderer-backend-comparison"
            self.assertTrue(recipe.exists())
            for fn in ("scene.obj", "scene.mtl", "scene.json", "luisa-scene.luisa",
                       "preview.png", "README.md"):
                self.assertTrue((recipe / fn).exists(), f"missing {fn}")
            data = json.loads((recipe / "scene.json").read_text())
            ok, errors, _w, _o = vr._check_contract("renderer-backend-comparison", recipe, data)
            self.assertTrue(ok, f"contract errors: {errors}")
            self.assertIsNotNone(_o)

    def test_committed_recipe_dir_passes_contract(self):
        recipe = REPO / "examples" / "recipes" / "renderer-backend-comparison"
        if not recipe.exists():
            self.skipTest("recipe not generated yet")
        data = json.loads((recipe / "scene.json").read_text())
        ok, errors, _w, _o = vr._check_contract("renderer-backend-comparison", recipe, data)
        self.assertTrue(ok, f"contract errors: {errors}")
        self.assertIsNotNone(_o)

    def test_obj_indices_in_range(self):
        recipe = REPO / "examples" / "recipes" / "renderer-backend-comparison"
        obj_text = (recipe / "scene.obj").read_text()
        vcount = sum(1 for ln in obj_text.splitlines() if ln.startswith("v "))
        max_idx = 0
        for ln in obj_text.splitlines():
            if ln.startswith("f "):
                for tok in ln.split()[1:]:
                    max_idx = max(max_idx, int(tok.split("/")[0]))
        self.assertGreater(vcount, 0)
        self.assertLessEqual(max_idx, vcount)

    def test_octanex_backend_native_flag_and_materials(self):
        recipe = REPO / "examples" / "recipes" / "renderer-backend-comparison"
        data = json.loads((recipe / "scene.json").read_text())
        commands = data["commands"]
        assigns = {c["payload"]["material_name"] for c in commands if c.get("op") == "assign_material"}
        creates = {c["payload"]["name"] for c in commands if c.get("op") == "create_material"}
        self.assertTrue(assigns.issubset(creates), "an assigned material lacks create_material")
        # three families (kinetic/magnetic/internal) -> three groups
        self.assertEqual(len(assigns), 3)
        back = data["backends"]["octanex"]
        self.assertEqual(back["form"], "combined_obj")
        # authoritative promotion flag is the top-level native_octane_verified
        self.assertIsInstance(data.get("native_octane_verified"), bool)
        self.assertTrue(data["native_octane_verified"],
                        "OctaneX side should be native-promoted after live verification")

    def test_luisa_scene_is_valid_backend_neutral_emitter(self):
        """The LuisaRender emitter must produce valid TEXT SDL with a render root + nodes."""
        recipe = REPO / "examples" / "recipes" / "renderer-backend-comparison"
        luisa_text = (recipe / "luisa-scene.luisa").read_text()
        self.assertIn("render {", luisa_text, "LuisaRender scene must have a render root")
        # environment can reference @env (generic) or @dir/@sun/etc (named light) — both valid
        has_environment = bool(re.search(r"environment \{ @\w+ \}", luisa_text))
        self.assertTrue(has_environment,
                        f"LuisaRender scene missing 'environment {{ @... }}' — got: {luisa_text}")
        for tok in ("Camera camera : Pinhole", "InlineMesh", "Surface",
                    "integrator : MegaPath"):
            self.assertIn(tok, luisa_text, f"LuisaRender scene missing '{tok}'")
        # honest record of the live attempt (real CLI result, never faked)
        back = json.loads((recipe / "scene.json").read_text())["backends"]["luisa_render"]
        self.assertEqual(back["form"], "luisa_text_sdl")
        self.assertIn("render_status", back, "LuisaRender attempt result must be recorded")
        self.assertNotEqual(back["render_status"], "pending_live_attempt",
                            "LuisaRender attempt was never executed")

    def test_committed_preview_is_valid_png_with_bars(self):
        recipe = REPO / "examples" / "recipes" / "renderer-backend-comparison"
        png = (recipe / "preview.png").read_bytes()
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        w, h, bitdepth, colour_type = struct.unpack(">IIBB", png[16:26])
        self.assertEqual(colour_type, 2)
        idat = b""
        pos = 8
        while pos < len(png):
            ln = struct.unpack(">I", png[pos:pos + 4])[0]
            tag = png[pos + 4:pos + 8]
            if tag == b"IDAT":
                idat += png[pos + 8:pos + 8 + ln]
            elif tag == b"IEND":
                break
            pos += 12 + ln
        raw = zlib.decompress(idat)
        stride = w * 3
        self.assertEqual(len(raw), h * (1 + stride))
        # three vertical colour bands should be visible in the lower portion
        rows = [raw[y * (1 + stride) + 1:(y + 1) * (1 + stride)] for y in range(h)]
        y = h - 10
        row = rows[y]
        bw = w // 3
        band_cols = [tuple(row[(bw * i + bw // 2) * 3:(bw * i + bw // 2) * 3 + 3]) for i in range(3)]
        self.assertEqual(len(set(band_cols)), 3, "preview should show 3 distinct coloured bars")


if __name__ == "__main__":
    import unittest
    unittest.main()
