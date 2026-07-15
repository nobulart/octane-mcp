#!/usr/bin/env python3
"""Unit test for the Phase B SPlisHSPlasH -> recipe adapter boundary.

This is NOT the live render. It asserts the adapter:
  * loads the committed fixture via scripts/physics_fixture_io.py (no SPlisHSPlasH),
  * emits a scene.json whose contract passes _check_contract offline,
  * maps fixture provenance into the simulation block honestly.
"""
from __future__ import annotations

import json
import importlib
import sys
import tempfile
from pathlib import Path
from unittest import TestCase

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "examples" / "fixtures" / "particles" / "dam-break-small" / "dam-break-small.csv"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))


class TestSplishSplashAdapter(TestCase):
    def test_recipe_generated_and_contract_ok(self):
        # Regenerate into a temp recipe root to guarantee it matches the current
        # adapter + fixture without mutating the checked-in native-promoted recipe.
        import benchmarks.verify_recipes as vr

        gen = importlib.import_module("gen_splishsplash_recipe")

        with tempfile.TemporaryDirectory() as td:
            recipe_root = Path(td) / "recipes"
            stats = gen.main(output_root=recipe_root)
            recipe = recipe_root / "dam-break-splash"
            self.assertTrue(recipe.exists())
            data = json.loads((recipe / "scene.json").read_text())
            self.assertEqual(stats["particles"], 1500)

            ok, errors, warnings, obj_path = vr._check_contract("dam-break-splash", recipe, data)
        self.assertTrue(ok, f"contract errors: {errors}")
        self.assertIsNotNone(obj_path)
        # Provenance honesty
        sim = data["simulation"]
        self.assertEqual(sim["source_library"], "splishsplash")
        self.assertIn("fixture_sha256", sim)
        self.assertEqual(sim["fixture"], str(FIXTURE))
        # Two material families present + one assign_material per particle group.
        kinds = {c.get("op") for c in data["commands"]}
        self.assertIn("create_material", kinds)
        self.assertIn("assign_material", kinds)
        assigns = [c for c in data["commands"] if c.get("op") == "assign_material"]
        self.assertGreaterEqual(len(assigns), 1500, "expected one assign_material per particle")
