from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from octanex_mcp.bridge import Workspace
from octanex_mcp.config import OctaneConfig, doctor, initialize_environment
from octanex_mcp.scene import (
    add_scene_object,
    build_scene_commands,
    load_scene_manifest,
    remove_scene_object,
    requeue_scene,
    save_scene_manifest,
    update_scene_object,
)
from octanex_mcp.visuals import create_primitive_obj


class ScenePlanTests(unittest.TestCase):
    def test_scene_plan_expands_to_namespaced_commands(self) -> None:
        plan = {
            "scene_id": "terrain_markers_001",
            "objects": [
                {"id": "surface", "type": "mesh", "path": "/tmp/surface.obj", "material": "terrain_mat"},
            ],
            "materials": [
                {"name": "terrain_mat", "kind": "glossy", "color": [0.2, 0.7, 0.3]},
            ],
            "camera": {"position": [1, -3, 2], "target": [0, 0, 0], "fov": 40},
            "lighting": {"preset": "soft_studio"},
            "render": {"samples": 64, "width": 800, "height": 600},
        }

        commands = build_scene_commands(plan)

        self.assertEqual([cmd["op"] for cmd in commands], [
            "create_material",
            "import_geometry",
            "assign_material",
            "set_camera",
            "set_lighting",
            "start_render",
        ])
        self.assertEqual(commands[0]["payload"]["name"], "Hermes::terrain_markers_001::terrain_mat")
        self.assertEqual(commands[1]["payload"]["name"], "Hermes::terrain_markers_001::surface")
        self.assertEqual(commands[2]["payload"], {
            "object_name": "Hermes::terrain_markers_001::surface",
            "material_name": "Hermes::terrain_markers_001::terrain_mat",
        })

    def test_scene_manifest_is_saved_under_scenes_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp) / "workspace")
            plan = {"scene_id": "demo_scene", "objects": []}

            result = save_scene_manifest(plan, ws)

            path = Path(result["path"])
            self.assertEqual(path.parent, ws.scenes_dir)
            self.assertTrue(path.exists())
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["scene_id"], "demo_scene")
            self.assertEqual(payload["schema_version"], "1.0")

    def test_scene_manifest_v2_defaults_and_preserves_semantic_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp) / "workspace")
            plan = {
                "scene_id": "primitive_demo",
                "intent": "show primitive grammar",
                "objects": [],
                "groups": [{"id": "main", "objects": ["box_1"]}],
                "annotations": [{"id": "label_1", "text": "Box"}],
                "quality_targets": {"preview": "not_blank"},
                "provenance": {"agent": "test"},
            }

            result = save_scene_manifest(plan, ws)

            payload = json.loads(Path(result["path"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["scene_manifest_version"], "2.0")
            self.assertEqual(payload["intent"], "show primitive grammar")
            self.assertEqual(payload["groups"], [{"id": "main", "objects": ["box_1"]}])
            self.assertEqual(payload["annotations"], [{"id": "label_1", "text": "Box"}])
            self.assertEqual(payload["quality_targets"], {"preview": "not_blank"})
            self.assertEqual(payload["provenance"], {"agent": "test"})

    def test_primitive_scene_objects_generate_assets_and_transform_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp) / "workspace")
            plan = {
                "scene_id": "primitive_demo",
                "objects": [
                    {
                        "id": "box_1",
                        "type": "box",
                        "size": [2, 1, 0.5],
                        "material": "matte",
                        "transform": {"translate": [1, 2, 3], "rotate_euler": [0, 0, 45], "scale": [1, 2, 1]},
                        "semantic_role": "primary",
                        "tags": ["primitive"],
                    },
                    {"id": "sphere_1", "type": "sphere", "radius": 0.5, "transform": {"translate": [-1, 0, 0]}},
                ],
                "materials": [{"name": "matte", "kind": "glossy", "color": [0.8, 0.2, 0.1]}],
            }

            result = save_scene_manifest(plan, ws)
            manifest = json.loads(Path(result["path"]).read_text(encoding="utf-8"))
            imports = [cmd for cmd in manifest["commands"] if cmd["op"] == "import_geometry"]

            self.assertEqual(len(imports), 2)
            self.assertTrue(Path(imports[0]["payload"]["path"]).exists())
            self.assertEqual(imports[0]["payload"]["transform"], plan["objects"][0]["transform"])
            self.assertEqual(imports[0]["payload"]["bounds"], manifest["objects"][0]["bounds"])
            self.assertEqual(manifest["objects"][0]["path"], imports[0]["payload"]["path"])
            self.assertEqual(manifest["objects"][0]["format"], "obj")
            self.assertEqual(manifest["objects"][0]["semantic_role"], "primary")
            self.assertEqual(manifest["objects"][0]["tags"], ["primitive"])

    def test_create_primitive_obj_supports_box_sphere_and_cylinder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp) / "workspace")
            for spec in [
                {"id": "box", "type": "box", "size": [1, 2, 3]},
                {"id": "sphere", "type": "sphere", "radius": 1.2},
                {"id": "cylinder", "type": "cylinder", "radius": 0.5, "height": 2.0},
            ]:
                with self.subTest(kind=spec["type"]):
                    asset = create_primitive_obj(spec, scene_id="primitive_demo", workspace=ws)
                    self.assertTrue(Path(asset["path"]).exists())
                    self.assertEqual(asset["format"], "obj")
                    self.assertEqual(asset["kind"], spec["type"])
                    self.assertIn("bounds", asset)
                    self.assertGreater(asset["bounds"]["radius"], 0)

    def test_scene_manifest_can_be_loaded_and_incrementally_edited(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp) / "workspace")
            save_scene_manifest({"scene_id": "editable", "objects": []}, ws)

            added = add_scene_object("editable", {"id": "box_1", "type": "box", "size": [1, 1, 1]}, ws)
            loaded = load_scene_manifest("editable", ws)
            updated = update_scene_object("editable", "box_1", {"transform": {"translate": [1, 2, 3]}}, ws)
            removed = remove_scene_object("editable", "box_1", ws)

            self.assertEqual(added["object_count"], 1)
            self.assertEqual(loaded["scene"]["scene_id"], "editable")
            self.assertEqual(updated["object"]["transform"], {"translate": [1, 2, 3]})
            self.assertEqual(removed["object_count"], 0)

    def test_requeue_scene_loads_saved_manifest_and_queues_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp) / "workspace")
            save_scene_manifest({
                "scene_id": "requeue_demo",
                "objects": [{"id": "box_1", "type": "box", "size": [1, 1, 1]}],
            }, ws)

            result = requeue_scene("requeue_demo", ws)

            self.assertEqual(result["scene_id"], "requeue_demo")
            self.assertEqual(len(result["queued_commands"]), 1)
            self.assertTrue(Path(result["queued_commands"][0]["path"]).exists())

    def test_workspace_and_doctor_include_artifacts_and_scenes_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lua_dir = root / "repo" / "octane_lua"
            lua_dir.mkdir(parents=True)
            (lua_dir / "hermes_bridge_oneshot_v2.lua").write_text('local ROOT = "/old"\n', encoding="utf-8")
            (lua_dir / "hermes_bridge_persistent_v1.lua").write_text('local ROOT = "/old"\n', encoding="utf-8")
            config = OctaneConfig(workspace=root / "workspace", repo_root=root / "repo", app_path=root / "Octane X.app")

            initialize_environment(config)
            checks = {item["name"]: item for item in doctor(config)["checks"]}

            self.assertTrue((config.workspace / "artifacts").exists())
            self.assertTrue((config.workspace / "scenes").exists())
            self.assertTrue(checks["workspace_artifacts"]["ok"])
            self.assertTrue(checks["workspace_scenes"]["ok"])


if __name__ == "__main__":
    unittest.main()
