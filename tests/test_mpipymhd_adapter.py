#!/usr/bin/env python3
"""Unit tests for the Phase B MPIPyMHD -> recipe adapter boundary.

These tests stay fixture-first: they exercise deterministic exporter packaging and
recipe generation without requiring mpi4py/OpenMPI during the normal suite.
"""
from __future__ import annotations

import importlib
import json
import sys
import tempfile
from pathlib import Path
from unittest import TestCase

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "examples" / "fixtures" / "mpipymhd" / "orszag-tang-vortex" / "orszag-tang-vortex.npz"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))


class TestMPIPyMHDAdapter(TestCase):
    def test_exporter_writes_deterministic_orszag_tang_fixture(self):
        exporter = importlib.import_module("export_mpipymhd_orszag_tang_fixture")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out1 = root / "a.npz"
            out2 = root / "b.npz"
            meta1 = exporter.export_fixture(out1, grid_size=12, time_steps=3)
            meta2 = exporter.export_fixture(out2, grid_size=12, time_steps=3)

            self.assertEqual(meta1["fixture_sha256"], meta2["fixture_sha256"])
            self.assertEqual(meta1["grid_shape"], [12, 12])
            self.assertEqual(meta1["source_library"], "MPIPyMHD")
            self.assertEqual(meta1["model"], "Orszag-Tang analytic MHD snapshot")
            self.assertEqual(meta1["time_steps"], 3)
            arrays = exporter.load_fixture_arrays(out1)
            self.assertEqual(sorted(arrays), ["Bx", "By", "density", "pressure", "vx", "vy"])
            self.assertEqual(arrays["density"]["shape"], (12, 12))
            self.assertGreater(meta1["magnetic_energy"], 0.0)
            self.assertGreater(meta1["kinetic_energy"], 0.0)

    def test_recipe_generated_and_contract_ok(self):
        import benchmarks.verify_recipes as vr

        gen = importlib.import_module("gen_mpipymhd_orszag_tang_recipe")

        with tempfile.TemporaryDirectory() as td:
            recipe_root = Path(td) / "recipes"
            stats = gen.main(output_root=recipe_root)
            recipe = recipe_root / "mhd-orszag-tang-vortex"
            self.assertTrue(recipe.exists())
            data = json.loads((recipe / "scene.json").read_text())
            ok, errors, warnings, obj_path = vr._check_contract("mhd-orszag-tang-vortex", recipe, data)

        self.assertTrue(ok, f"contract errors: {errors}")
        self.assertIsNotNone(obj_path)
        self.assertEqual(stats["grid_shape"], [32, 32])
        self.assertGreater(stats["magnetic_glyphs"], 20)

        sim = data["simulation"]
        self.assertEqual(sim["source_library"], "MPIPyMHD")
        self.assertEqual(sim["fixture"], str(FIXTURE))
        self.assertIn("fixture_sha256", sim)
        self.assertEqual(sim["fixture_arrays"], ["Bx", "By", "density", "pressure", "vx", "vy"])
        self.assertEqual(sim["model"], "Orszag-Tang analytic MHD snapshot")
        self.assertIn("magnetic_field", sim["physical_variables"])

        commands = data["commands"]
        assigns = [c for c in commands if c.get("op") == "assign_material"]
        groups = {c["payload"]["material_name"] for c in assigns}
        self.assertIn("density_mat", groups)
        self.assertIn("magnetic_mat", groups)
        self.assertIn("velocity_mat", groups)
        self.assertFalse(data["native_octane_verified"])


if __name__ == "__main__":
    import unittest

    unittest.main()
