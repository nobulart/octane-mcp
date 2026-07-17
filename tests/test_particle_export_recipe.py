#!/usr/bin/env python3
"""Unit tests for the Phase C particle-export-interchange recipe (C5).

Fixture-first + repo-native: the same SPlisHSPlasH-derived particle cloud is
emitted as CSV, VTK PolyData, and partio .bgeo, then rendered in OctaneX as
instanced spheres (one group per phase). Asserts:
  * the OctaneX recipe passes the offline contract with per-phase materials;
  * OBJ face indices stay within the vertex count;
  * CSV + VTK round-trips reproduce the original point set exactly (stdlib);
  * the partio .bgeo is verified by the brew `partinfo` CLI (real round-trip:
    Number of particles == 1500, attributes position/v/phase);
  * the reference preview is a decodable PNG.
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


class TestParticleExportRecipe(TestCase):
    def test_generated_recipe_passes_contract(self):
        gen = importlib.import_module("gen_particle_export_recipe")
        with tempfile.TemporaryDirectory() as td:
            recipe_root = Path(td) / "recipes"
            gen.main(output_root=recipe_root)
            recipe = recipe_root / "particle-export-interchange"
            self.assertTrue(recipe.exists())
            for fn in ("scene.obj", "scene.mtl", "scene.json", "cloud.csv",
                       "cloud.vtu", "cloud.bgeo", "preview.png", "README.md"):
                self.assertTrue((recipe / fn).exists(), f"missing {fn}")
            data = json.loads((recipe / "scene.json").read_text())
            ok, errors, _w, _o = vr._check_contract("particle-export-interchange", recipe, data)
            self.assertTrue(ok, f"contract errors: {errors}")
            self.assertIsNotNone(_o)

    def test_committed_recipe_dir_passes_contract(self):
        recipe = REPO / "examples" / "recipes" / "particle-export-interchange"
        if not recipe.exists():
            self.skipTest("recipe not generated yet")
        data = json.loads((recipe / "scene.json").read_text())
        ok, errors, _w, _o = vr._check_contract("particle-export-interchange", recipe, data)
        self.assertTrue(ok, f"contract errors: {errors}")
        self.assertIsNotNone(_o)

    def test_obj_indices_in_range(self):
        recipe = REPO / "examples" / "recipes" / "particle-export-interchange"
        obj_text = (recipe / "scene.obj").read_text()
        vcount = sum(1 for ln in obj_text.splitlines() if ln.startswith("v "))
        max_idx = 0
        for ln in obj_text.splitlines():
            if ln.startswith("f "):
                for tok in ln.split()[1:]:
                    max_idx = max(max_idx, int(tok.split("/")[0]))
        self.assertGreater(vcount, 0)
        self.assertLessEqual(max_idx, vcount)

    def test_interchange_roundtrips_equal(self):
        """CSV + VTK reproduce the original cloud; partio verified via brew CLI."""
        gen = importlib.import_module("gen_particle_export_recipe")
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            res = gen._interchange_ok(tdp)
            self.assertTrue(res["csv_roundtrip"], "CSV round-trip mismatch")
            self.assertTrue(res["vtk_roundtrip"], "VTK round-trip mismatch")
            self.assertEqual(res["count"], 1500)
            partio = res["partio"]
            self.assertTrue(partio["available"], f"partinfo unavailable: {partio.get('error')}")
            self.assertTrue(partio["verified"], f"partio verify failed: {partio.get('error')}")
            self.assertEqual(partio["count"], 1500, "partio particle count mismatch")

    def test_octanex_backend_native_flag_and_materials(self):
        recipe = REPO / "examples" / "recipes" / "particle-export-interchange"
        data = json.loads((recipe / "scene.json").read_text())
        commands = data["commands"]
        assigns = {c["payload"]["material_name"] for c in commands if c.get("op") == "assign_material"}
        creates = {c["payload"]["name"] for c in commands if c.get("op") == "create_material"}
        self.assertTrue(assigns.issubset(creates), "an assigned material lacks create_material")
        self.assertEqual(len(assigns), 2, "expected liquid + foam groups")
        self.assertIsInstance(data.get("native_octane_verified"), bool)
        self.assertTrue(data["native_octane_verified"],
                        "recipe should be native-promoted after live verification")
        # interchange metadata records all three formats
        fmts = data["simulation"]["interchange_formats"]
        self.assertIn("csv", fmts)
        self.assertIn("vtk", fmts)
        self.assertIn("partio_bgeo", fmts)

    def test_committed_preview_is_valid_png(self):
        recipe = REPO / "examples" / "recipes" / "particle-export-interchange"
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


if __name__ == "__main__":
    import unittest
    unittest.main()
