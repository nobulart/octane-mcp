#!/usr/bin/env python3
"""Unit tests for the Phase C conservation-budget-panels recipe (C2).

Fixture-first + repo-native: reuses the real Orszag-Tang MHD trace but is
deterministic and offline-verifiable. Asserts the conservation-budget grammar:
  * kinetic / magnetic / internal energy bars + a red drift (error) panel;
  * every bar group bound by a distinct create_material + assign_material;
  * OBJ face indices within the vertex count;
  * near-conservation metadata (total energy drift stays small);
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


class TestConservationBudgetRecipe(TestCase):
    def test_generated_recipe_passes_contract(self):
        gen = importlib.import_module("gen_conservation_budget_recipe")
        with tempfile.TemporaryDirectory() as td:
            recipe_root = Path(td) / "recipes"
            gen.main(output_root=recipe_root)
            recipe = recipe_root / "conservation-budget-panels"
            self.assertTrue(recipe.exists())
            for fn in ("scene.obj", "scene.mtl", "scene.json", "preview.png", "README.md"):
                self.assertTrue((recipe / fn).exists(), f"missing {fn}")
            data = json.loads((recipe / "scene.json").read_text())
            ok, errors, _w, _o = vr._check_contract("conservation-budget-panels", recipe, data)
            self.assertTrue(ok, f"contract errors: {errors}")
            self.assertIsNotNone(_o)

    def test_committed_recipe_dir_passes_contract(self):
        recipe = REPO / "examples" / "recipes" / "conservation-budget-panels"
        if not recipe.exists():
            self.skipTest("recipe not generated yet")
        data = json.loads((recipe / "scene.json").read_text())
        ok, errors, _w, _o = vr._check_contract("conservation-budget-panels", recipe, data)
        self.assertTrue(ok, f"contract errors: {errors}")
        self.assertIsNotNone(_o)

    def test_obj_indices_in_range(self):
        recipe = REPO / "examples" / "recipes" / "conservation-budget-panels"
        obj_text = (recipe / "scene.obj").read_text()
        vcount = sum(1 for ln in obj_text.splitlines() if ln.startswith("v "))
        max_idx = 0
        for ln in obj_text.splitlines():
            if ln.startswith("f "):
                for tok in ln.split()[1:]:
                    max_idx = max(max_idx, int(tok.split("/")[0]))
        self.assertGreater(vcount, 0)
        self.assertLessEqual(max_idx, vcount)

    def test_budget_grammar_invariants(self):
        recipe = REPO / "examples" / "recipes" / "conservation-budget-panels"
        data = json.loads((recipe / "scene.json").read_text())
        commands = data["commands"]
        assigns = {c["payload"]["material_name"] for c in commands if c.get("op") == "assign_material"}
        for fam in ("kinetic_mat", "magnetic_mat", "internal_mat", "drift_mat"):
            self.assertIn(fam, assigns, f"missing family group {fam}")
        self.assertIn("floor_mat", assigns)
        creates = {c["payload"]["name"] for c in commands if c.get("op") == "create_material"}
        self.assertTrue(assigns.issubset(creates), "an assigned material lacks create_material")

        sim = data["simulation"]
        self.assertEqual(sim["scale_mapping"]["steps"], len(sim["budget_rows"]))
        self.assertEqual(sim["scale_mapping"]["families"],
                         ["kinetic", "magnetic", "internal", "drift"])
        # near-conservation: max relative drift across steps stays small (< 5%)
        drifts = [r["drift_rel"] for r in sim["budget_rows"]]
        self.assertLess(max(drifts), 0.05, f"MHD energy drift too large: {max(drifts):.4f}")
        # The recipe is now native-promoted (live render passed pixel acceptance
        # and copied back a fresh octane-preview.png), so the flag is True.
        self.assertIsInstance(data["native_octane_verified"], bool)
        self.assertTrue(data["native_octane_verified"],
                        "recipe should be native-promoted after live verification")

    def test_committed_preview_is_valid_png_with_families(self):
        """Reference preview must be a decodable PNG carrying the 4 family bands."""
        import sys
        from PIL import Image  # project venv; optional but preferred

        recipe = REPO / "examples" / "recipes" / "conservation-budget-panels"
        png = (recipe / "preview.png").read_bytes()
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        w, h, bitdepth, colour_type = struct.unpack(">IIBB", png[16:26])
        self.assertEqual(colour_type, 2)
        self.assertEqual(bitdepth, 8)
        # decode IDAT + strip per-scanline filter bytes (type 0 = None)
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
        # 4 horizontal bands; sample one central pixel per band
        bands = 4
        bw = w // bands
        seen = []
        for bi in range(bands):
            cx = bi * bw + bw // 2
            seen.append(tuple(rows[h // 2][cx * 3:cx * 3 + 3]))
        self.assertGreaterEqual(len(set(seen)), 3, f"preview bands not distinct ({seen})")


if __name__ == "__main__":
    import unittest
    unittest.main()
