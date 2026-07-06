from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from octanex_mcp.bridge_control import bridge_script, octane_process_status, render_run_bridge_applescript, run_bridge_script
from octanex_mcp.config import OctaneConfig
from octanex_mcp.server import build_mcp


class BridgeControlTests(unittest.TestCase):
    def make_config(self, root: Path) -> OctaneConfig:
        repo = root / "repo"
        lua = repo / "octane_lua"
        lua.mkdir(parents=True)
        workspace = root / "workspace"
        app = root / "Octane X.app"
        app.mkdir()
        (lua / "hermes_bridge_oneshot.generated.lua").write_text("-- oneshot\n", encoding="utf-8")
        (lua / "hermes_bridge_persistent.generated.lua").write_text("-- persistent\n", encoding="utf-8")
        return OctaneConfig(workspace=workspace, repo_root=repo, app_path=app)

    def test_bridge_script_resolves_generated_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = self.make_config(Path(tmp))

            oneshot = bridge_script(config, "one-shot")
            persistent = bridge_script(config, "persistent")

        self.assertEqual(oneshot.mode, "oneshot")
        self.assertEqual(oneshot.menu_name, "hermes_bridge_oneshot.generated.lua")
        self.assertEqual(persistent.menu_name, "hermes_bridge_persistent.generated.lua")

    def test_bridge_script_rejects_unknown_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = self.make_config(Path(tmp))
            with self.assertRaisesRegex(ValueError, "oneshot"):
                bridge_script(config, "timer")

    def test_render_applescript_targets_octane_scripts_menu(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = self.make_config(Path(tmp))
            script = render_run_bridge_applescript(config, bridge_script(config, "oneshot"))

        self.assertIn("open -a", script)
        self.assertIn("hermes_bridge_oneshot.generated.lua", script)
        self.assertIn("Scripts", script)
        self.assertIn("Preferences -> Scripts path", script)

    def test_run_bridge_dry_run_reports_script_without_executing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = self.make_config(Path(tmp))

            result = run_bridge_script("persistent", config=config, dry_run=True)

        self.assertTrue(result["ok"], result)
        self.assertTrue(result["dry_run"])
        self.assertTrue(result["script_exists"])
        self.assertEqual(result["mode"], "persistent")
        self.assertIn("hermes_bridge_persistent.generated.lua", result["apple_script"])

    def test_process_status_reports_script_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = self.make_config(Path(tmp))

            status = octane_process_status(config)

        self.assertTrue(status["app_exists"])
        self.assertTrue(status["script_exists"]["oneshot"])
        self.assertTrue(status["script_exists"]["persistent"])
        self.assertIn("running", status)

    def test_mcp_exposes_bridge_control_tools(self) -> None:
        tool_names = {tool.name for tool in build_mcp()._tool_manager.list_tools()}

        self.assertIn("octane_bridge_process_status", tool_names)
        self.assertIn("octane_run_bridge", tool_names)
        self.assertIn("octane_run_oneshot_bridge", tool_names)
        self.assertIn("octane_start_persistent_bridge", tool_names)


if __name__ == "__main__":
    unittest.main()
