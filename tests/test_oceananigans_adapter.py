#!/usr/bin/env python3
"""Unit test for the Phase B Oceananigans -> recipe adapter boundary.

This is not a live render. It asserts the adapter consumes a committed `.npz`
fixture with no Julia/Oceananigans runtime dependency, emits a recipe whose
offline contract passes, and preserves honest simulation provenance.
"""
from __future__ import annotations

import importlib
import json
import sys
import tempfile
from pathlib import Path
from unittest import TestCase

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "examples" / "fixtures" / "oceananigans" / "shallow-water-front" / "shallow-water-front.npz"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))


class TestOceananigansAdapter(TestCase):
    def test_recipe_generated_and_contract_ok(self):
        import benchmarks.verify_recipes as vr

        gen = importlib.import_module("gen_oceananigans_shallow_water_recipe")

        with tempfile.TemporaryDirectory() as td:
            recipe_root = Path(td) / "recipes"
            stats = gen.main(output_root=recipe_root)
            recipe = recipe_root / "oceananigans-shallow-water-front"
            self.assertTrue(recipe.exists())
            data = json.loads((recipe / "scene.json").read_text())

            ok, errors, warnings, obj_path = vr._check_contract(
                "oceananigans-shallow-water-front", recipe, data
            )

        self.assertTrue(ok, f"contract errors: {errors}")
        self.assertIsNotNone(obj_path)
        self.assertEqual(stats["grid_shape"], [24, 36])
        self.assertEqual(stats["velocity_glyphs"], 6)

        sim = data["simulation"]
        self.assertEqual(sim["source_library"], "Oceananigans.jl")
        self.assertEqual(sim["fixture"], str(FIXTURE))
        self.assertIn("fixture_sha256", sim)
        self.assertEqual(sim["fixture_arrays"], ["bathymetry", "eta", "u", "v"])
        self.assertIn("free_surface_eta", sim["physical_variables"])

        commands = data["commands"]
        assigns = [c for c in commands if c.get("op") == "assign_material"]
        groups = {c["payload"]["material_name"] for c in assigns}
        self.assertEqual(
            groups,
            {
                "bathymetry_mat",
                "cold_water_mat",
                "front_water_mat",
                "warm_water_mat",
                "coastline_mat",
                "velocity_mat",
            },
        )
        self.assertGreaterEqual(len(assigns), 6)
        self.assertFalse(data["native_octane_verified"])
