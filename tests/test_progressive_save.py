"""Tests for the progressive save_preview envelope (task C1, Python side).

Asserts the command JSON the gateway/MCP tool queues carries the progressive
flags. The Lua bridge edit that *consumes* these flags lives in
``octane_lua/hermes_bridge_oneshot_v2.lua`` (handle_save_preview) and is applied
separately (it is part of an in-flight bridge WIP branch).
"""

import unittest

from octanex_mcp.server import _build_save_preview_envelope as build_env


class TestProgressiveSave(unittest.TestCase):
    def test_progressive_envelope_carries_flags(self):
        env = build_env(progressive=True)
        self.assertTrue(env["progressive"])
        self.assertIn("progressive_path", env)
        self.assertTrue(env["progressive_path"].endswith("preview_progressive.png"))

    def test_non_progressive_envelope_has_no_progressive_path(self):
        env = build_env()
        self.assertFalse(env["progressive"])
        self.assertNotIn("progressive_path", env)

    def test_quality_tier_resolves(self):
        env = build_env(quality="standard")
        # standard tier -> samples 512 / min_samples 24 / timeout 30 (per QUALITY_TIERS)
        self.assertEqual(env["samples"], 512)
        self.assertEqual(env["min_samples"], 24)
        self.assertEqual(env["timeout_seconds"], 30)

    def test_bad_quality_raises(self):
        with self.assertRaises(ValueError):
            build_env(quality="nope")


if __name__ == "__main__":
    unittest.main()
