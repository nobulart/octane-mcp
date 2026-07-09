"""Tests for the OCTANEX_RENDER_HOST config flag (task A5)."""

import unittest

from octanex_mcp.config import resolve_config


class TestConfigRenderHost(unittest.TestCase):
    def test_default_render_host_is_localhost(self):
        self.assertEqual(resolve_config({}).render_host, "localhost")

    def test_render_host_env_override(self):
        self.assertEqual(
            resolve_config({"OCTANEX_RENDER_HOST": "mac-studio.local"}).render_host,
            "mac-studio.local",
        )

    def test_empty_render_host_falls_back_to_localhost(self):
        self.assertEqual(resolve_config({"OCTANEX_RENDER_HOST": ""}).render_host, "localhost")


if __name__ == "__main__":
    unittest.main()
