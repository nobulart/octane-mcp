from __future__ import annotations

import re
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


if __name__ == "__main__":
    unittest.main()
