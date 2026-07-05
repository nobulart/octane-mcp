from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ONESHOT = ROOT / "octane_lua" / "hermes_bridge_oneshot_v2.lua"
PERSISTENT = ROOT / "octane_lua" / "hermes_bridge_persistent_v1.lua"


def lua_function_body(path: Path, name: str) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"^local function {re.escape(name)}\(", text, flags=re.M)
    if not match:
        raise AssertionError(f"{name} not found in {path}")
    next_match = re.search(r"^local function ", text[match.end():], flags=re.M)
    end = match.end() + next_match.start() if next_match else len(text)
    body = text[match.start():end].strip()
    # Logging labels are bridge-mode specific; handler behavior should match.
    return body.replace("v2 command", "<mode> command").replace("persistent command", "<mode> command")


class LuaBridgeParityTests(unittest.TestCase):
    def test_scene_handler_semantics_match_between_one_shot_and_persistent_bridges(self) -> None:
        for name in [
            "latest_imported_geometry_fallback",
            "handle_import_geometry",
            "handle_create_material",
            "handle_assign_material",
            "handle_set_camera",
            "handle_set_lighting",
            "handle_start_render",
            "handle_save_preview",
            "handle_command",
        ]:
            with self.subTest(function=name):
                self.assertEqual(lua_function_body(ONESHOT, name), lua_function_body(PERSISTENT, name))

    def test_both_bridges_use_phase3_lifecycle_dirs_and_results(self) -> None:
        for path in [ONESHOT, PERSISTENT]:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertIn('local PROCESSING = ROOT .. "/processing"', text)
                self.assertIn('local RESULTS = ROOT .. "/results"', text)
                self.assertIn("write_result(cmd, true", text)
                self.assertIn("write_result(cmd, false", text)

    def test_both_bridges_decode_json_payloads_without_regex_extractors(self) -> None:
        for path in [ONESHOT, PERSISTENT]:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertIn('local JSON = dofile(BRIDGE_DIR .. "lib/json.lua")', text)
                self.assertIn("local decoded, err = JSON.decode(raw)", text)
                self.assertIn("payload = payload", text)
                self.assertIn('"invalid JSON: " .. tostring(parse_err)', text)
                self.assertNotIn("extract_string", text)
                self.assertNotIn("extract_number", text)
                self.assertNotIn("extract_array", text)

    def test_lua_json_decoder_supports_nested_command_payload_shapes(self) -> None:
        text = (ROOT / "octane_lua" / "lib" / "json.lua").read_text(encoding="utf-8")
        self.assertIn("function json.decode(text)", text)
        self.assertIn("json.null = {}", text)
        self.assertIn("if value ~= json.null then obj[key] = value end", text)
        self.assertIn("local function parse_object", text)
        self.assertIn("local function parse_array", text)
        self.assertIn("local function parse_string", text)

    def test_oneshot_bridge_processes_payload_json_and_fails_invalid_json(self) -> None:
        lua = shutil.which("lua")
        if not lua:
            self.skipTest("lua executable not available")

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            for name in ["queue", "processing", "processed", "failed", "results", "renders"]:
                (workspace / name).mkdir(parents=True)

            valid = {
                "schema_version": "1.0",
                "id": "valid-ping",
                "op": "ping",
                "payload": {"message": "from payload", "nested": {"translate": [1, 2, 3]}},
                "created_at": "2026-01-01T00:00:00Z",
                "source": "octanex-mcp",
            }
            (workspace / "queue" / "valid-ping.json").write_text(json.dumps(valid), encoding="utf-8")
            (workspace / "queue" / "bad-json.json").write_text("{", encoding="utf-8")

            env = os.environ.copy()
            env["OCTANEX_MCP_WORKSPACE"] = str(workspace)
            proc = subprocess.run([lua, str(ONESHOT)], cwd=ROOT, env=env, text=True, capture_output=True, timeout=30)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue((workspace / "processed" / "valid-ping.json").exists())
            self.assertTrue((workspace / "failed" / "bad-json.json").exists())

            valid_result = json.loads((workspace / "results" / "valid-ping.json").read_text(encoding="utf-8"))
            bad_result = json.loads((workspace / "results" / "bad-json.json").read_text(encoding="utf-8"))
            self.assertTrue(valid_result["success"])
            self.assertIn("pong from payload", valid_result["message"])
            self.assertFalse(bad_result["success"])
            self.assertIn("invalid JSON", bad_result["message"])


if __name__ == "__main__":
    unittest.main()
