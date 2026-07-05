from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from octanex_mcp.bridge import Workspace
from octanex_mcp.config import OctaneConfig, doctor, initialize_environment
from octanex_mcp.scene import build_scene_commands, save_scene_manifest


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
