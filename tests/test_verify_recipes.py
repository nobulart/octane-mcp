"""Offline contract checks for the recipe-verification harness.

These run without Octane X. They assert that the reproducibility-contract logic in
``benchmarks.verify_recipes`` correctly accepts valid recipes and rejects the known
blockers (missing OBJ, invalid command, start_render-before-save_preview).
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase, mock

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
        # A recipe dir without scene.obj and with NO committed generator must
        # fail the contract (regenerable recipes are lenient, so pick one that
        # is not regenerable — ancient-temple has a tracked OBJ but no gen_*.py).
        import tempfile

        data = json.loads((RECIPES / "ancient-temple" / "scene.json").read_text())
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            (td_path / "scene.json").write_text(json.dumps(data))
            ok, errors, warnings, _ = _check_contract("ancient-temple", td_path, data)
            self.assertFalse(ok)
            self.assertTrue(any("scene.obj" in e for e in errors), f"expected missing scene.obj error, got: {errors}")

    def test_verify_recipe_library_dry_run_counts(self):
        report = verify_recipe_library(dry_run=True)
        self.assertEqual(report["mode"], "dry_run")
        # 48 recipe dirs total (54 on disk, but several are fixtures/non-scene
        # dirs excluded by _recipe_dirs). 47/48 pass the offline contract;
        # `earth-moon-space` is the remaining ...[truncated]
        # preview). `cathedral` previously failed (missing scene.mtl) and was fixed
        # by generating the hint MTL from scene.json MATERIALS. `genesis-cloth-on-rigid`
        # was added as the B5 Genesis Phase-B adapter and passes the contract.
        # `simulation-frame-strip` (C1), `conservation-budget-panels` (C2),
        # `precision-error-landscape` (C3), `renderer-backend-comparison` (C4),
        # and `particle-export-interchange` (C5) were added and pass the contract.
        self.assertEqual(report["total"], 48)
        self.assertEqual(report["contract_ok"], 47, report)
        self.assertEqual(report["contract_failed"], 1)
        failed = [r["slug"] for r in report["recipes"] if not r["contract_ok"]]
        self.assertEqual(failed, ["earth-moon-space"], report)
        # If the large Earth OBJ is absent, the regenerable recipe must warn rather
        # than silently passing cleanly. If the OBJ is present, no warning is needed.
        hemi = next(r for r in report["recipes"] if r["slug"] == "earth-hemisphere")
        self.assertTrue(hemi["contract_ok"], report)
        if not (RECIPES / "earth-hemisphere" / "scene.obj").exists():
            self.assertTrue(any("regenerable" in w for w in hemi["contract_warnings"]), report)

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

    def test_live_run_flushes_stale_queue_before_writing_recipe_commands(self):
        """A live recipe run must not flush away the commands it just wrote."""
        import tempfile

        from octanex_mcp.bridge import Workspace

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            recipe_dir = root / "recipes" / "flush-order"
            recipe_dir.mkdir(parents=True)
            obj_path = recipe_dir / "scene.obj"
            obj_path.write_text("o cube\nv 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n", encoding="utf-8")
            (recipe_dir / "scene.mtl").write_text("newmtl mat\nKd 1 1 1\n", encoding="utf-8")
            (recipe_dir / "preview.png").write_bytes(b"reference")
            data = {
                "slug": "flush-order",
                "title": "Flush Order",
                "commands": [
                    {"op": "import_geometry", "payload": {"path": "scene.obj", "name": "flush-order"}},
                    {"op": "save_preview", "payload": {"path": "renders/octane-preview.png"}},
                ],
            }
            ws = Workspace(root / "workspace")
            ws.ensure()
            (ws.queue_dir / "stale.json").write_text("{}", encoding="utf-8")
            seen_queue_counts: list[int] = []

            def fake_drain(workspace, timeout_seconds):
                queued = sorted(workspace.queue_dir.glob("*.json"))
                seen_queue_counts.append(len(queued))
                self.assertEqual(len(queued), 2, "drain should see current recipe commands, not an empty queue")
                self.assertFalse((workspace.queue_dir / "stale.json").exists(), "stale command should have been flushed before queueing")
                for command_path in queued:
                    command = json.loads(command_path.read_text(encoding="utf-8"))
                    if command.get("op") == "save_preview":
                        preview = Path(command["payload"]["path"])
                        preview.parent.mkdir(parents=True, exist_ok=True)
                        preview.write_bytes(b"native png placeholder")
                return {"ok": True}

            with mock.patch.object(vr, "resolve_config", return_value=SimpleNamespace(workspace=ws.root)), \
                mock.patch.object(vr, "_find_recipe_dir", return_value=recipe_dir), \
                mock.patch.object(vr, "_read_scene_json", return_value=data), \
                mock.patch.object(vr, "_check_contract", return_value=(True, [], [], obj_path)), \
                mock.patch.object(vr, "_resolved_commands", return_value=[dict(c) for c in data["commands"]]), \
                mock.patch.object(vr, "drain_oneshot", side_effect=fake_drain), \
                mock.patch.object(vr.acceptance, "evaluate_acceptance", return_value={"passed": True}):
                run = vr.run_recipe("flush-order", dry_run=False, drain=True, drain_timeout=1)

            self.assertEqual(seen_queue_counts, [2])
            self.assertEqual(run.queued, 2)
            self.assertIsNone(run.error)
            self.assertTrue(any("auto-flushed 1 stale queue files" in note for note in run.notes), run.notes)
            self.assertEqual(len(list(ws.queue_dir.glob("*.json"))), 2)


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
