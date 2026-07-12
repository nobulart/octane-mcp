from __future__ import annotations

import re
import unittest
from pathlib import Path

from octanex_mcp.models import ALLOWED_OPS, PAYLOAD_VALIDATORS
from octanex_mcp.schema import command_schema

ROOT = Path(__file__).resolve().parents[1]
ONESHOT = ROOT / "octane_lua" / "hermes_bridge_oneshot_v2.lua"
PERSISTENT = ROOT / "octane_lua" / "hermes_bridge_persistent_v1.lua"

# These commands are accepted by the Lua bridge's generic acknowledgement path
# rather than a concrete scene-building handler. Keep this list intentional and
# small so new bridge-capable ops must add explicit dispatch.
LUA_ACK_ONLY_OPS = {
    "open_or_create_project",
    "pause_render",
    "save_scene",
    "scene_summary",
    "build_concept",
}


def lua_dispatched_ops(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^local function handle_command\(cmd\)(.*?)^end", text, flags=re.M | re.S)
    if not match:
        raise AssertionError(f"handle_command not found in {path}")
    return set(re.findall(r'cmd\.op == "([^"]+)"', match.group(1)))


class BridgeContractParityTests(unittest.TestCase):
    def test_python_command_contract_sets_match(self) -> None:
        self.assertEqual(set(command_schema()["operations"]), ALLOWED_OPS)
        self.assertEqual(set(PAYLOAD_VALIDATORS), ALLOWED_OPS)

    def test_lua_dispatch_sets_match_between_bridges(self) -> None:
        self.assertEqual(lua_dispatched_ops(ONESHOT), lua_dispatched_ops(PERSISTENT))

    def test_lua_dispatch_plus_explicit_ack_set_covers_python_allowed_ops(self) -> None:
        handled = lua_dispatched_ops(ONESHOT)
        self.assertEqual(handled | LUA_ACK_ONLY_OPS, ALLOWED_OPS)
        self.assertFalse(handled & LUA_ACK_ONLY_OPS)

    def test_scene_harvest_is_explicitly_dispatched_not_generic_acknowledged(self) -> None:
        self.assertIn("scene_harvest", lua_dispatched_ops(ONESHOT))
        self.assertIn("scene_harvest", lua_dispatched_ops(PERSISTENT))
        self.assertNotIn("scene_harvest", LUA_ACK_ONLY_OPS)


if __name__ == "__main__":
    unittest.main()
