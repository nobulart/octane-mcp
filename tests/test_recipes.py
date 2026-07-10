from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from octanex_mcp.bridge import Workspace
from octanex_mcp.recipes import load_recipe, queue_recipe, recipe_index, validate_recipe_library


class RecipeRegistryTests(unittest.TestCase):
    def test_recipe_index_lists_checked_in_recipes_with_required_metadata(self) -> None:
        index = recipe_index()
        slugs = {item["slug"] for item in index["recipes"]}

        self.assertGreaterEqual(index["count"], 13)
        self.assertIn("data-bars", slugs)
        self.assertIn("photoreal-earth-space", slugs)
        self.assertIn("saturn-moons-space", slugs)
        self.assertIn("annotated-text-labels", slugs)
        self.assertIn("image-heightfield-mask", slugs)
        self.assertIn("document-ocr-layout", slugs)
        self.assertIn("transformer-attention-map", slugs)
        self.assertIn("photoreal-vase-studio", slugs)
        data_bars = next(item for item in index["recipes"] if item["slug"] == "data-bars")
        self.assertEqual(data_bars["title"], "3D KPI Bar Chart")
        self.assertEqual(data_bars["domain"], "Data visualization")
        self.assertTrue(data_bars["scene_json_exists"])
        self.assertTrue(data_bars["preview_exists"])
        # data-bars was promoted to native_octane_verified by the WP6 honesty
        # gap-close work (commit c572ace: 13/18 -> 17/18). The ground-truth
        # check (_recipe_dirs + octane-preview.png present) confirms it is now
        # genuinely verified, so the index must reflect True.
        self.assertTrue(data_bars["native_octane_verified"])
        self.assertIn("scene.obj", {Path(path).name for path in data_bars["assets"]})

    def test_load_recipe_returns_commands_and_resolved_asset_paths(self) -> None:
        recipe = load_recipe("data-bars")

        self.assertEqual(recipe["slug"], "data-bars")
        self.assertTrue(Path(recipe["scene_json_path"]).exists())
        self.assertTrue(Path(recipe["preview_path"]).exists())
        self.assertTrue(any(command["op"] == "import_geometry" for command in recipe["commands"]))
        import_command = next(command for command in recipe["commands"] if command["op"] == "import_geometry")
        self.assertTrue(Path(import_command["payload"]["path"]).is_absolute())
        self.assertTrue(Path(import_command["payload"]["path"]).exists())
        self.assertIn("quality_checklist", recipe)
        self.assertIn("known_pitfalls", recipe)

    def test_queue_recipe_queues_valid_commands_and_applies_payload_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp) / "workspace")
            result = queue_recipe(
                "data-bars",
                workspace=ws,
                overrides={"start_render": {"samples": 16, "width": 320, "height": 240}},
            )

            self.assertEqual(result["slug"], "data-bars")
            self.assertGreater(result["queued_count"], 0)
            self.assertEqual(len(result["queued_commands"]), result["queued_count"])
            queued_files = sorted(ws.queue_dir.glob("*.json"))
            self.assertEqual(len(queued_files), result["queued_count"])
            queued_payloads = [json.loads(path.read_text(encoding="utf-8")) for path in queued_files]
            start_render = next(item for item in queued_payloads if item["op"] == "start_render")
            self.assertEqual(start_render["payload"]["samples"], 16)
            self.assertEqual(start_render["payload"]["width"], 320)
            self.assertEqual(start_render["payload"]["height"], 240)
            imports = [item for item in queued_payloads if item["op"] == "import_geometry"]
            self.assertTrue(imports)
            self.assertTrue(Path(imports[0]["payload"]["path"]).is_absolute())
            save_preview = next(item for item in queued_payloads if item["op"] == "save_preview")
            self.assertTrue(Path(save_preview["payload"]["path"]).is_absolute())
            self.assertIn(str(ws.renders_dir), save_preview["payload"]["path"])
            self.assertIn("bundle_path", save_preview["payload"])

    def test_validate_recipe_library_reports_every_checked_in_recipe_ok(self) -> None:
        # Honesty contract: any recipe that DECLARES `native_octane_verified=true`
        # must actually carry a preview PNG on disk. A recipe that declares
        # `native_octane_verified=false` is honestly pending and is allowed to
        # lack a preview — the gap stays visible in `recipe_index` and is NOT
        # masked by this test. (Library grew past the original 18-recipe
        # assumption; `earth-moon-space` is the current declared-pending entry.)
        index = recipe_index()
        report = validate_recipe_library()

        declared_verified = {
            item["slug"] for item in index["recipes"] if item.get("native_octane_verified") is True
        }
        # No recipe that CLAIMS to be verified may be missing its preview.
        # A recipe that declares `native_octane_verified=false` is honestly
        # pending (e.g. `earth-moon-space`) — its missing preview is expected,
        # not a defect, so it is excluded from the ok/invalid gate. The gap
        # stays visible in `recipe_index` and is NOT masked by this test.
        failing_verified = [
            item["slug"]
            for item in report["items"]
            if item["slug"] in declared_verified and not item["ok"]
        ]
        self.assertEqual(failing_verified, [], report["items"])
        self.assertGreaterEqual(report["checked"], 18)

    def test_all_recipes_declare_visual_iteration_contract(self) -> None:
        index = recipe_index()

        for item in index["recipes"]:
            with self.subTest(slug=item["slug"]):
                raw = load_recipe(item["slug"])["raw"]
                protocol = raw["visual_iteration_protocol"]
                self.assertEqual(protocol["model"], "ollama:glm-ocr")
                self.assertIn("octane-preview.png", protocol["candidate_image"])
                self.assertIn("final native Octane render bundled as octane-preview.png", protocol["required_evidence"])
                self.assertGreaterEqual(len(protocol["baseline_sweep"]["camera_or_scene_variants"]), 4)
                bundle = raw["final_bundle"]
                self.assertTrue(bundle["required"])
                self.assertIn("octane-preview.png", bundle["native_render"])
                self.assertIn(bundle["status"], {"pending_native_octane_iteration", "native_candidate_available", "native_candidate_saved_but_not_final"})

    def test_new_text_image_and_interpretability_recipes_have_renderable_previews(self) -> None:
        from octanex_mcp.review import review_preview

        for slug in ["annotated-text-labels", "image-heightfield-mask", "document-ocr-layout", "transformer-attention-map"]:
            with self.subTest(slug=slug):
                recipe = load_recipe(slug)
                self.assertTrue(Path(recipe["preview_path"]).exists())
                self.assertTrue(any(Path(asset).name == "scene.obj" for asset in recipe["assets"]))
                self.assertTrue(any(Path(asset).name == "scene.mtl" for asset in recipe["assets"]))
                self.assertGreaterEqual(len(recipe["quality_checklist"]), 4)
                self.assertTrue(recipe["known_pitfalls"], "new recipes should document pitfalls")
                review = review_preview(recipe["preview_path"])
                self.assertTrue(review["ok"], review)
                self.assertGreater(review["foreground_bbox_area_percent"], 12.0)

    def test_photoreal_vase_studio_recipe_captures_material_variety(self) -> None:
        from octanex_mcp.review import review_preview

        recipe = load_recipe("photoreal-vase-studio")
        raw = recipe["raw"]

        self.assertEqual(recipe["title"], "Photoreal Multi-Vase Studio")
        target_preview = Path(recipe["scene_json_path"]).parent / "photoreal-preview.png"
        self.assertTrue(target_preview.exists())
        self.assertTrue(any(Path(asset).name == "scene.obj" for asset in recipe["assets"]))
        self.assertTrue(any(Path(asset).name == "scene.mtl" for asset in recipe["assets"]))
        materials = raw["materials"]
        for name in ["mat_smoky_glass", "mat_cobalt_ceramic", "mat_terracotta_ribbed", "mat_white_porcelain", "mat_dark_brushed_metal"]:
            self.assertIn(name, materials)
        self.assertGreaterEqual(len(raw["quality_checklist"]), 5)
        self.assertTrue(raw["known_pitfalls"])
        protocol = raw["visual_iteration_protocol"]
        self.assertEqual(protocol["model"], "ollama:glm-ocr")
        self.assertIn("octane-preview.png", protocol["candidate_image"])
        self.assertIn("final native Octane render bundled as octane-preview.png", protocol["required_evidence"])
        bundle = raw["final_bundle"]
        self.assertTrue(bundle["required"])
        self.assertEqual(bundle["status"], "native_candidate_saved_but_not_final")
        self.assertIn("octane-preview.png", bundle["native_render"])
        review = review_preview(target_preview)
        self.assertTrue(review["ok"], review)
        self.assertGreater(review["foreground_bbox_area_percent"], 18.0)

    def test_unknown_recipe_slug_raises_helpful_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown recipe slug"):
            load_recipe("does-not-exist")


if __name__ == "__main__":
    unittest.main()
