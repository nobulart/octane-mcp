from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from octanex_mcp import scene
from octanex_mcp.bridge import Workspace
from octanex_mcp.scene import (
    add_scene_object,
    build_scene_commands,
    load_scene_manifest,
    remove_scene_object,
    requeue_scene,
    save_scene_manifest,
    update_scene_object,
)


class SceneManifestV2Tests(unittest.TestCase):
    """Tests confirming scene manifest v2 defaults."""

    def test_save_scene_manifest_emits_version_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp) / "workspace")
            manifest = {"scene_id": "demo_v2", "objects": [{"id": "box1", "type": "box", "size": [1,1,1]}]}
            save_scene_manifest(manifest, ws)
            path = list(ws.scenes_dir.glob("*.json"))
            self.assertTrue(path)
            data = json.loads(path[0].read_text(encoding="utf-8"))
            self.assertEqual(data.get("scene_manifest_version"), "2.0")

    def test_update_scene_object_works_and_preserves_other_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp) / "workspace")
            manifest = {"scene_id": "update_test", "objects": [{"id": "box1", "type": "box", "size": [1,1,1]}]}
            add_scene_object("update_test", {"id": "box2", "type": "sphere", "radius": 1.5}, ws)
            updated = update_scene_object("update_test", "box2", {"radius": 2.0, "color": [1, 0.5, 0.3]}, ws)
            self.assertEqual(updated["object"]["radius"], 2.0)
            self.assertEqual(updated["object"]["color"], [1, 0.5, 0.3])


class OctanePatchSceneTests(unittest.TestCase):
    """Tests for octane_patch_scene() with granular updates."""

    def test_patch_camera_updates_camera_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp) / "workspace")
            scene.save_scene_manifest({"scene_id": "patch_test", "objects": []}, ws)
            result = scene.octane_patch_scene(
                "patch_test",
                workspace=ws,
                patch_camera={"position": [1, 2, 3], "fov": 55},
            )
            self.assertTrue(result["patched"])

    def test_patch_lighting_updates_lighting_preset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp) / "workspace")
            scene.save_scene_manifest({"scene_id": "patch_light", "objects": []}, ws)
            result = scene.octane_patch_scene(
                "patch_light",
                workspace=ws,
                patch_lighting={"preset": "brighter_studio", "key_angle": 45},
            )
            self.assertTrue(result["patched"])

    def test_add_materials_adds_new_materials(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp) / "workspace")
            scene.save_scene_manifest({
                "scene_id": "add_mat",
                "objects": [],
                "materials": [{"name": "mat1", "kind": "glossy", "color": [0.5, 0.5, 0.5]}],
            }, ws)
            result = scene.octane_patch_scene(
                "add_mat",
                workspace=ws,
                add_materials=[{"name": "glass_mat", "kind": "glass", "color": [0.8, 0.9, 1.0]}],
            )
            self.assertTrue(result["patched"])
            self.assertIn("added_materials", result)
            self.assertEqual(result["added_materials"], ["glass_mat"])

    def test_update_materials_updates_existing_material(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp) / "workspace")
            scene.save_scene_manifest({
                "scene_id": "update_mat",
                "objects": [],
                "materials": [{"name": "mat1", "kind": "glossy", "color": [0.5, 0.5, 0.5]}],
            }, ws)
            result = scene.octane_patch_scene(
                "update_mat",
                workspace=ws,
                update_materials=[{"name": "mat1", "color": [1.0, 0.5, 0.3]}],
            )
            self.assertTrue(result["patched"])
            self.assertIn("updated_materials", result)
            manifest = json.loads(list(ws.scenes_dir.glob("*.json"))[0].read_text(encoding="utf-8"))
            mat = [m for m in manifest["materials"] if m.get("name") == "mat1"][0]
            self.assertEqual(mat["color"], [1.0, 0.5, 0.3])

    def test_add_objects_adds_new_objects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp) / "workspace")
            scene.save_scene_manifest({
                "scene_id": "add_obj",
                "objects": [{"id": "box1", "type": "box", "size": [1,1,1]}],
            }, ws)
            result = scene.octane_patch_scene(
                "add_obj",
                workspace=ws,
                add_objects=[{"id": "sphere1", "type": "sphere", "radius": 1.0}],
            )
            self.assertTrue(result["patched"])
            self.assertIn("added_objects", result)
            manifest = json.loads(list(ws.scenes_dir.glob("*.json"))[0].read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["objects"]), 2)

    def test_remove_objects_removes_by_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp) / "workspace")
            scene.save_scene_manifest({
                "scene_id": "remove_obj",
                "objects": [
                    {"id": "box1", "type": "box", "size": [1,1,1]},
                    {"id": "sphere1", "type": "sphere", "radius": 1.0},
                ],
            }, ws)
            result = scene.octane_patch_scene(
                "remove_obj",
                workspace=ws,
                remove_objects=["sphere1"],
            )
            self.assertTrue(result["patched"])
            self.assertEqual(result["removed_objects"], ["sphere1"])
            manifest = json.loads(list(ws.scenes_dir.glob("*.json"))[0].read_text(encoding="utf-8"))
            ids = [o["id"] for o in manifest["objects"]]
            self.assertIn("box1", ids)
            self.assertNotIn("sphere1", ids)

    def test_octane_patch_scene_all_sections_together(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp) / "workspace")
            scene.save_scene_manifest({
                "scene_id": "combined",
                "objects": [{"id": "box1", "type": "box", "size": [1,1,1]}],
                "materials": [{"id": "mat1", "kind": "glossy", "color": [0.5, 0.5, 0.5]}],
                "camera": {"position": [0, 0, 0], "fov": 45},
                "lighting": {"preset": "soft_studio"},
                "render": {"samples": 64},
            }, ws)
            result = scene.octane_patch_scene(
                "combined",
                workspace=ws,
                patch_camera={"fov": 60},
                patch_lighting={"preset": "brighter_studio"},
                patch_render={"samples": 128},
                add_materials=[{"id": "glass", "kind": "glass"}],
                add_objects=[{"id": "sphere1", "type": "sphere", "radius": 1.5}],
                remove_objects=[],
            )
            self.assertTrue(result["patched"])


if __name__ == "__main__":
    unittest.main()
