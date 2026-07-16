#!/usr/bin/env python3
"""Unit tests for the Phase B Genesis -> recipe adapter boundary.

Fixture-first: exercises deterministic fixture export + recipe generation without
requiring a live Genesis solve (the committed JSON fixture is the boundary, and
the local Genesis build does not yet expose a stable CLOTH/RIGID Python entity API).
"""
from __future__ import annotations

import importlib
import json
import sys
import tempfile
from pathlib import Path
from unittest import TestCase

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "examples" / "fixtures" / "genesis" / "cloth-on-rigid" / "cloth-on-rigid.json"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))


class TestGenesisClothOnRigidAdapter(TestCase):
    def test_fixture_is_deterministic_and_drapes(self):
        exporter = importlib.import_module("export_genesis_cloth_on_rigid_fixture")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out1 = root / "a.json"
            out2 = root / "b.json"
            m1 = exporter.main_to(out1)
            m2 = exporter.main_to(out2)

        self.assertEqual(m1["fixture_sha256"], m2["fixture_sha256"])
        self.assertEqual(m1["grid"], [24, 24])
        self.assertGreater(m1["contact_count"], 0, "cloth must actually drape onto the sphere")
        # the committed fixture sidecar carries the Genesis provenance
        sidecar = FIXTURE.with_suffix(".prov.json")
        prov = json.loads(sidecar.read_text(encoding="utf-8")) if sidecar.exists() else json.loads(out1.read_text())
        self.assertEqual(prov["source_library"], "Genesis")
        # the fixture file itself carries the draped vertex data
        fdata = json.loads(FIXTURE.read_text(encoding="utf-8")) if FIXTURE.exists() else json.loads(out1.read_text())
        self.assertIn("vertices", fdata)
        self.assertIn("contact_vertex_indices", fdata)

    def test_recipe_generated_and_contract_ok(self):
        import benchmarks.verify_recipes as vr

        gen = importlib.import_module("gen_genesis_cloth_on_rigid_recipe")

        with tempfile.TemporaryDirectory() as td:
            recipe_root = Path(td) / "recipes"
            stats = gen.main(output_root=recipe_root)
            recipe = recipe_root / "genesis-cloth-on-rigid"
            self.assertTrue(recipe.exists())
            data = json.loads((recipe / "scene.json").read_text())
            ok, errors, warnings, obj_path = vr._check_contract("genesis-cloth-on-rigid", recipe, data)

        self.assertTrue(ok, f"contract errors: {errors}")
        self.assertIsNotNone(obj_path)
        self.assertGreaterEqual(stats["contact_markers"], 1)
        self.assertEqual(stats["grid"], [24, 24])

        sim = data["simulation"]
        self.assertEqual(sim["source_library"], "Genesis")
        self.assertTrue(sim["fixture"].endswith("examples/fixtures/genesis/cloth-on-rigid/cloth-on-rigid.json"))
        self.assertIn("fixture_sha256", sim)
        self.assertIn("cloth_vertex_positions", sim["physical_variables"])
        self.assertTrue(sim["model"].startswith("analytic drape"))

        commands = data["commands"]
        assigns = [c for c in commands if c.get("op") == "assign_material"]
        groups = {c["payload"]["material_name"] for c in assigns}
        self.assertIn("cloth_mat", groups)
        self.assertIn("rigid_mat", groups)
        self.assertIn("contact_mat", groups)
        self.assertFalse(data["native_octane_verified"])


if __name__ == "__main__":
    import unittest

    unittest.main()
