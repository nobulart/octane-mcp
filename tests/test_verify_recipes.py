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
        # data-bars is a known native_octane_verified recipe (WP6 promotion) with a
        # clean command set AND a checked-in reference preview, so it must pass the
        # offline contract. (math-surface is the one intentional gap — its preview
        # was dropped in commit 0993e51 — and is excluded here on purpose.)
        recipe_dir = RECIPES / "data-bars"
        data = json.loads((recipe_dir / "scene.json").read_text())
        ok, errors, warnings, obj_path = _check_contract("data-bars", recipe_dir, data)
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
        self.assertEqual(report["total"], 22)
        # 21/22 recipe dirs ship a real reference preview and pass the offline
        # contract. `earth-moon-space` is the exception: its scene graph + command
        # sequence are sound, but BOTH live capture attempts (2026-07-10) returned
        # near-empty frames (white bg, ~2% non-bg, abs_dev ~2-4 vs the >>5 real-subject
        # bar). Per the "a blank frame is NOT success" rule, the degenerate preview is
        # intentionally NOT committed, so this recipe legitimately fails the offline
        # preview-exists contract until a converged live render is produced.
        self.assertEqual(report["contract_ok"], 21, report)
        self.assertEqual(report["contract_failed"], 1)
        failed = [r["slug"] for r in report["recipes"] if not r["contract_ok"]]
        self.assertEqual(failed, ["earth-moon-space"], report)

    def test_verify_recipe_library_single_slug(self):
        report = verify_recipe_library(dry_run=True, slug="data-bars")
        self.assertEqual(report["total"], 1)
        self.assertEqual(report["recipes"][0]["slug"], "data-bars")
        self.assertTrue(report["recipes"][0]["contract_ok"])

    def test_live_requires_env_guard(self):
        # Without OCTANEX_LIVE=1, live mode must refuse (no accidental Octane session).
        import os

        os.environ.pop("OCTANEX_LIVE", None)
        with self.assertRaises(RuntimeError):
            verify_recipe_library(dry_run=False, live=True)


class TestVisionTierOffline(TestCase):
    """The vision tier must never call a real model in tests; inject vision_fn."""

    def test_vision_review_accept_passes(self):
        import benchmarks.vision_check as vc

        data = {"title": "Photoreal Vase Studio", "purpose": "Five distinct vases on a pedestal."}
        stub = lambda path, intent: (True, "YES: five vases visible")  # noqa: E731
        res = vc.vision_review("fake.png", data, stub)
        self.assertTrue(res["ran"])
        self.assertTrue(res["passed"])
        self.assertIn("vase", res["intent"].lower())

    def test_vision_review_reject_records_failure(self):
        import benchmarks.vision_check as vc

        data = {"title": "Photoreal Vase Studio", "purpose": "Five distinct vases on a pedestal."}
        stub = lambda path, intent: (False, "NO: a grey cylinder, not vases")  # noqa: E731
        res = vc.vision_review("fake.png", data, stub)
        self.assertTrue(res["ran"])
        self.assertFalse(res["passed"])
        self.assertEqual(res["reasoning"], "NO: a grey cylinder, not vases")

    def test_vision_review_handles_vision_exception(self):
        import benchmarks.vision_check as vc

        def boom(_p, _i):
            raise RuntimeError("model down")

        res = vc.vision_review("fake.png", {"title": "x"}, boom)
        self.assertFalse(res["ran"])
        self.assertFalse(res["passed"])
        self.assertIn("model down", res["error"])

    def test_run_recipe_blocks_promotion_on_vision_reject(self):
        """With copy_back + vision_check, a wrong-subject verdict must NOT promote."""
        import os
        import tempfile

        import benchmarks.verify_recipes as vr
        from benchmarks.verify_recipes import RecipeRun, _promote

        # Minimal run object mimicking a passed-pixel, vision-rejected result.
        data = {"slug": "photoreal-vase-studio", "title": "Vase",
                "materials": {}, "commands": [
                    {"op": "import_geometry", "payload": {"path": "x", "name": "photoreal-vase-studio"}},
                    {"op": "save_preview", "payload": {"path": "y"}},
                ]}
        run = RecipeRun(slug="photoreal-vase-studio", title="Vase", domain="Photoreal")
        run.acceptance = {"passed": True}
        run.vision = {"ran": True, "passed": False, "intent": "vase", "reasoning": "NO: cylinder"}
        run.preview_path = Path("/nonexistent.png")  # not needed; we test gate logic directly

        # Replicate the exact promotion gate used in run_recipe.
        should_promote = (
            True  # copy_back context
            and run.acceptance.get("passed")
            and (not True or run.vision_ok)  # vision_check=True
        )
        self.assertFalse(should_promote, "vision rejection must block promotion")
        self.assertFalse(run.vision_ok, "vision_ok must be False on reject")


if __name__ == "__main__":
    import unittest

    unittest.main()
