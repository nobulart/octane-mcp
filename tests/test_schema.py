from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from octanex_mcp.bridge import Workspace, list_commands, write_command
from octanex_mcp.config import OctaneConfig, doctor, initialize_environment
from octanex_mcp.schema import SCHEMA_VERSION, validate_command, validate_queue


class CommandSchemaTests(unittest.TestCase):
    def test_write_command_emits_versioned_valid_envelope_and_results_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp) / "workspace")

            result = write_command("ping", {"message": "hello"}, ws)

            command = json.loads(Path(result["path"]).read_text(encoding="utf-8"))
            self.assertEqual(command["schema_version"], SCHEMA_VERSION)
            self.assertEqual(command["source"], "octanex-mcp")
            self.assertEqual(command["op"], "ping")
            self.assertEqual(command["payload"], {"message": "hello"})
            self.assertIn("created_at", command)
            self.assertEqual(validate_command(command).errors, [])
            self.assertTrue(ws.processing_dir.exists())
            self.assertTrue(ws.results_dir.exists())

    def test_validate_command_rejects_missing_required_payload_fields(self) -> None:
        command = {
            "schema_version": SCHEMA_VERSION,
            "id": "cmd-1",
            "op": "import_geometry",
            "payload": {"format": "obj"},
            "created_at": "2026-01-01T00:00:00Z",
            "source": "octanex-mcp",
        }

        result = validate_command(command)

        self.assertFalse(result.ok)
        self.assertIn("payload.path is required for import_geometry", result.errors)

    def test_validate_command_accepts_required_vector_payload_fields(self) -> None:
        command = {
            "schema_version": SCHEMA_VERSION,
            "id": "cmd-2",
            "op": "set_camera",
            "payload": {"position": [1, 2, 3], "target": [0, 0, 0], "fov": 45},
            "created_at": "2026-01-01T00:00:00Z",
            "source": "octanex-mcp",
        }

        result = validate_command(command)

        self.assertTrue(result.ok, result.errors)

    def test_validate_queue_reports_invalid_json_and_invalid_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp) / "workspace")
            ws.ensure()
            (ws.queue_dir / "bad-json.json").write_text("{", encoding="utf-8")
            (ws.queue_dir / "bad-command.json").write_text(json.dumps({"op": "import_geometry", "payload": {}}), encoding="utf-8")
            write_command("ping", {"message": "ok"}, ws)

            report = validate_queue(ws)

            self.assertFalse(report["ok"])
            self.assertEqual(report["checked"], 3)
            self.assertEqual(report["valid"], 1)
            self.assertEqual(report["invalid"], 2)
            invalid_paths = {Path(item["path"]).name for item in report["items"] if not item["ok"]}
            self.assertEqual(invalid_paths, {"bad-json.json", "bad-command.json"})

    def test_list_commands_includes_processing_and_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp) / "workspace")
            ws.ensure()
            (ws.processing_dir / "processing.json").write_text("{}", encoding="utf-8")
            (ws.results_dir / "result.json").write_text("{}", encoding="utf-8")

            listed = list_commands(ws)

            self.assertEqual(listed["processing"], ["processing.json"])
            self.assertEqual(listed["results"], ["result.json"])

    def test_doctor_checks_processing_and_results_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lua_dir = root / "repo" / "octane_lua"
            lua_dir.mkdir(parents=True)
            (lua_dir / "hermes_bridge_oneshot_v2.lua").write_text('local ROOT = "/old"\n', encoding="utf-8")
            (lua_dir / "hermes_bridge_persistent_v1.lua").write_text('local ROOT = "/old"\n', encoding="utf-8")
            config = OctaneConfig(workspace=root / "workspace", repo_root=root / "repo", app_path=root / "Octane X.app")
            initialize_environment(config)

            result = doctor(config, create=True)

            checks = {item["name"]: item for item in result["checks"]}
            self.assertTrue(checks["workspace_processing"]["ok"])
            self.assertTrue(checks["workspace_results"]["ok"])


if __name__ == "__main__":
    unittest.main()
