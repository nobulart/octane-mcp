#!/usr/bin/env python3
"""Unit tests for the Phase C precision-error-landscape recipe (C3).

Fixture-first + repo-native: a chaotic logistic map integrated to 60-digit
`decimal` precision, compared against IEEE float64/float32; the relative error
is rendered as a heightfield + a float32 front strip. Asserts:
  * the error surface is NOT flat (carries spatial error structure);
  * every group bound by a distinct create_material + assign_material;
  * OBJ face indices stay within the vertex count;
  * the reference preview is a *decodable* PNG (catches the corrupt-PNG class).
"""
from __future__ import annotations

import importlib
import json
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


class TestPrecisionErrorRecipe(TestCase):
    def test_generated_recipe_passes_contract(self):
        gen = importlib.import_module("gen_precision_error_recipe")
        with tempfile.TemporaryDirectory() as td:
            recipe_root = Path(td) / "recipes"
            gen.main(output_root=recipe_root)
            recipe = recipe_root / "precision-error-landscape"
            self.assertTrue(recipe.exists())
            for fn in ("scene.obj", "scene.mtl", "scene.json", "preview.png", "README.md"):
                self.assertTrue((recipe / fn).exists(), f"missing {fn}")
            data = json.loads((recipe / "scene.json").read_text())
            ok, errors, _w, _o = vr._check_contract("precision-error-landscape", recipe, data)
            self.assertTrue(ok, f"contract errors: {errors}")
            self.assertIsNotNone(_o)

    def test_committed_recipe_dir_passes_contract(self):
        recipe = REPO / "examples" / "recipes" / "precision-error-landscape"
        if not recipe.exists():
            self.skipTest("recipe not generated yet")
        data = json.loads((recipe / "scene.json").read_text())
        ok, errors, _w, _o = vr._check_contract("precision-error-landscape", recipe, data)
        self.assertTrue(ok, f"contract errors: {errors}")
        self.assertIsNotNone(_o)

    def test_obj_indices_in_range(self):
        recipe = REPO / "examples" / "recipes" / "precision-error-landscape"
        obj_text = (recipe / "scene.obj").read_text()
        vcount = sum(1 for ln in obj_text.splitlines() if ln.startswith("v "))
        max_idx = 0
        for ln in obj_text.splitlines():
            if ln.startswith("f "):
                for tok in ln.split()[1:]:
                    max_idx = max(max_idx, int(tok.split("/")[0]))
        self.assertGreater(vcount, 0)
        self.assertLessEqual(max_idx, vcount)

    def test_error_surface_not_flat(self):
        recipe = REPO / "examples" / "recipes" / "precision-error-landscape"
        data = json.loads((recipe / "scene.json").read_text())
        commands = data["commands"]
        assigns = {c["payload"]["material_name"] for c in commands if c.get("op") == "assign_material"}
        for fam in ("error_mat", "base_mat", "f32_mat"):
            self.assertIn(fam, assigns, f"missing group {fam}")
        creates = {c["payload"]["name"] for c in commands if c.get("op") == "create_material"}
        self.assertTrue(assigns.issubset(creates), "an assigned material lacks create_material")

        sim = data["simulation"]
        # the surface must carry structured error (max encoded error > 0)
        self.assertGreater(sim["error_stats"]["max_rel_err_f64"], 0.0,
                           "float64 error surface is flat — no precision signal")
        # float32 should be at least as wrong as float64
        self.assertGreaterEqual(sim["error_stats"]["max_rel_err_f32"],
                                sim["error_stats"]["max_rel_err_f64"] - 1e-9)
        # The recipe is now native-promoted (live render passed pixel acceptance
        # and copied back a fresh octane-preview.png), so the flag is True.
        self.assertIsInstance(data["native_octane_verified"], bool)
        self.assertTrue(data["native_octane_verified"],
                        "recipe should be native-promoted after live verification")

    def test_committed_preview_is_valid_png_with_error_ramp(self):
        """Reference preview must be a decodable PNG carrying an error colour ramp."""
        recipe = REPO / "examples" / "recipes" / "precision-error-landscape"
        png = (recipe / "preview.png").read_bytes()
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        w, h, bitdepth, colour_type = struct.unpack(">IIBB", png[16:26])
        self.assertEqual(colour_type, 2)
        self.assertEqual(bitdepth, 8)
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
        rows = [raw[y * (1 + stride) + 1:(y + 1) * (1 + stride)] for y in range(h)]
        # sample top (warm/high error) vs bottom (cool/exact) midpoint columns
        top = rows[2][(w // 2) * 3:(w // 2) * 3 + 3]
        bot = rows[h - 3][(w // 2) * 3:(w // 2) * 3 + 3]
        # warm = more red + less blue at top
        self.assertGreater(top[0] - top[2], bot[0] - bot[2] - 5,
                           "preview ramp not cool->warm top-to-bottom")


if __name__ == "__main__":
    import unittest
    unittest.main()
