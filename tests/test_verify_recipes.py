"""Offline contract checks for the recipe-verification harness.

These run without Octane X. They assert that the reproducibility-contract logic in
``benchmarks.verify_recipes`` correctly accepts valid recipes and rejects the known
blockers (missing OBJ, invalid command, start_render-before-save_preview).
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest import TestCase

import benchmarks.verify_recipes as vr
from benchmarks.verify_recipes import _check_contract, verify_recipe_library

REPO_ROOT = Path(__file__).resolve().parents[1]
RECIPES = REPO_ROOT / "examples" / "recipes"


class TestRecipeContractOffline(TestCase):
    def test_known_verified_recipe_passes_contract(self):
        # math-surface is a known native_octane_verified recipe with a clean command set
        recipe_dir = RECIPES / "math-surface"
        data = json.loads((recipe_dir / "scene.json").read_text())
        ok, errors, warnings, obj_path = _check_contract("math-surface", recipe_dir, data)
        self.assertTrue(ok, f"unexpected contract errors: {errors}")
        self.assertIsNotNone(obj_path)

    def test_recipe_with_start_render_before_save_warns_not_blocks(self):
        # network-graph emits start_render immediately before save_preview (pitfall #9/#10).
        # The live runner strips it, so this must be a *warning*, not a contract failure.
        recipe_dir = RECIPES / "network-graph"
        data = json.loads((recipe_dir / "scene.json").read_text())
        ok, errors, warnings, _ = _check_contract("network-graph", recipe_dir, data)
        self.assertTrue(ok, f"unexpected contract errors: {errors}")
        self.assertTrue(any("pitfall" in w for w in warnings), f"expected pitfall warning, got: {warnings}")

    def test_missing_obj_fails_contract(self):
        # A recipe dir without scene.obj must fail the contract.
        import tempfile

        data = json.loads((RECIPES / "math-surface" / "scene.json").read_text())
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            (td_path / "scene.json").write_text(json.dumps(data))
            ok, errors, warnings, _ = _check_contract("math-surface", td_path, data)
            self.assertFalse(ok)
            self.assertTrue(any("scene.obj" in e for e in errors), f"expected missing scene.obj error, got: {errors}")

    def test_verify_recipe_library_dry_run_counts(self):
        report = verify_recipe_library(dry_run=True)
        self.assertEqual(report["mode"], "dry_run")
        self.assertEqual(report["total"], 18)
        # every recipe ships scene.obj + scene.json + a reference preview, so all should pass contract
        self.assertEqual(report["contract_ok"], 18, report)
        self.assertEqual(report["contract_failed"], 0)

    def test_verify_recipe_library_single_slug(self):
        report = verify_recipe_library(dry_run=True, slug="math-surface")
        self.assertEqual(report["total"], 1)
        self.assertEqual(report["recipes"][0]["slug"], "math-surface")
        self.assertTrue(report["recipes"][0]["contract_ok"])

    def test_live_requires_env_guard(self):
        # Without OCTANEX_LIVE=1, live mode must refuse (no accidental Octane session).
        import os

        os.environ.pop("OCTANEX_LIVE", None)
        with self.assertRaises(RuntimeError):
            verify_recipe_library(dry_run=False, live=True)


if __name__ == "__main__":
    import unittest

    unittest.main()
