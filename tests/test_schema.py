from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from octanex_mcp.bridge import Workspace, list_commands, write_command
from octanex_mcp.config import OctaneConfig, doctor, initialize_environment
from octanex_mcp.models import ALLOWED_OPS, PAYLOAD_VALIDATORS
from octanex_mcp.schema import SCHEMA_VERSION, command_schema, validate_command, validate_queue


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

    def test_validate_command_returns_structured_error_codes_for_range_failures(self) -> None:
        command = {
            "schema_version": SCHEMA_VERSION,
            "id": "cmd-ranges",
            "op": "start_render",
            "payload": {"samples": 0, "width": 99999, "height": -1},
            "created_at": "2026-01-01T00:00:00Z",
            "source": "octanex-mcp",
        }

        result = validate_command(command)

        self.assertFalse(result.ok)
        codes = {error["code"] for error in result.error_details}
        self.assertIn("payload.samples.out_of_range", codes)
        self.assertIn("payload.width.out_of_range", codes)
        self.assertIn("payload.height.out_of_range", codes)

    def test_save_preview_accepts_render_readiness_controls(self) -> None:
        command = {
            "schema_version": SCHEMA_VERSION,
            "id": "cmd-preview-ready",
            "op": "save_preview",
            "payload": {"path": "renders/preview.png", "width": 960, "height": 960, "samples": 64, "min_samples": 16, "timeout_seconds": 10},
            "created_at": "2026-01-01T00:00:00Z",
            "source": "octanex-mcp",
        }

        result = validate_command(command)

        self.assertTrue(result.ok, result.errors)

    def test_validate_command_rejects_unsafe_paths_colors_and_camera_ranges(self) -> None:
        commands = [
            ("import_geometry", {"path": "../escape.obj"}, "payload.path.unsafe"),
            ("save_preview", {"path": "renders/../escape.png"}, "payload.path.unsafe"),
            (
                "create_material",
                {"name": "bad", "color": [1.2, 0, 0], "roughness": -0.1, "metallic": 1.5},
                "payload.color.out_of_range",
            ),
            ("set_camera", {"position": [1, 2, 3], "target": [0, 0, 0], "fov": 121}, "payload.fov.out_of_range"),
        ]

        for op, payload, expected_code in commands:
            with self.subTest(op=op):
                command = {
                    "schema_version": SCHEMA_VERSION,
                    "id": f"cmd-{op}",
                    "op": op,
                    "payload": payload,
                    "created_at": "2026-01-01T00:00:00Z",
                    "source": "octanex-mcp",
                }

                result = validate_command(command)

                self.assertFalse(result.ok)
                self.assertIn(expected_code, {error["code"] for error in result.error_details})

    def test_command_schema_lists_operations_examples_and_limits(self) -> None:
        schema = command_schema()

        self.assertEqual(schema["schema_version"], SCHEMA_VERSION)
        self.assertEqual(set(schema["operations"]), ALLOWED_OPS)
        self.assertEqual(set(PAYLOAD_VALIDATORS), ALLOWED_OPS)
        self.assertIn("start_render", schema["operations"])
        self.assertEqual(schema["operations"]["start_render"]["fields"]["samples"]["min"], 1)
        self.assertEqual(schema["operations"]["save_preview"]["fields"]["min_samples"]["min"], 0)
        self.assertEqual(schema["operations"]["save_preview"]["fields"]["timeout_seconds"]["max"], 600)
        self.assertEqual(schema["operations"]["set_camera"]["fields"]["fov"]["max"], 120)
        self.assertIn("import_geometry", schema["examples"])

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
