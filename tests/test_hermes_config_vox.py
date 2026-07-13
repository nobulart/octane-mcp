"""Tests for the VOX voice-mode bridge (canvas voice-conversation toggle)."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from octanex_mcp import hermes_config as hc


SAMPLE_CONFIG = """
model:
  default: tencent/hy3:free
  provider: nous
custom_providers:
  - name: local-ollama
    models:
      qwen3.6:35b:
        context_length: 262144
"""


class TestGetVox(unittest.TestCase):
    def setUp(self):
        self.path = Path(tempfile.NamedTemporaryFile(suffix=".yaml", delete=False).name)
        self.path.write_text(SAMPLE_CONFIG)

    def tearDown(self):
        if self.path.exists():
            self.path.unlink()

    def test_default_off(self):
        res = hc.get_vox(self.path)
        self.assertFalse(res["enabled"])
        self.assertIn("terse", res["contract"])

    def test_reads_existing_flag(self):
        self.path.write_text(SAMPLE_CONFIG + "vox:\n  enabled: true\n")
        self.assertTrue(hc.get_vox(self.path)["enabled"])


class TestSetVox(unittest.TestCase):
    def setUp(self):
        self.path = Path(tempfile.NamedTemporaryFile(suffix=".yaml", delete=False).name)
        self.path.write_text(SAMPLE_CONFIG)

    def tearDown(self):
        if self.path.exists():
            self.path.unlink()

    def test_enable_inserts_block(self):
        res = hc.set_vox(True, self.path)
        self.assertTrue(res["enabled"])
        text = self.path.read_text()
        self.assertIn("vox:", text)
        self.assertIn("enabled: true", text)
        # Surgical: providers untouched.
        self.assertIn("custom_providers:", text)
        self.assertIn("qwen3.6:35b", text)

    def test_disable_writes_false(self):
        hc.set_vox(True, self.path)
        res = hc.set_vox(False, self.path)
        self.assertFalse(res["enabled"])
        self.assertIn("enabled: false", self.path.read_text())

    def test_toggle_existing_block(self):
        self.path.write_text(SAMPLE_CONFIG + "vox:\n  enabled: false\nother: keep\n")
        hc.set_vox(True, self.path)
        text = self.path.read_text()
        self.assertIn("enabled: true", text)
        self.assertIn("other: keep", text)

    def test_idempotent_noop_returns_ok(self):
        # Setting the flag to its current value is a no-op, not an error.
        self.path.write_text(SAMPLE_CONFIG + "vox:\n  enabled: true\n")
        res = hc.set_vox(True, self.path)
        self.assertTrue(res["enabled"])


if __name__ == "__main__":
    unittest.main()
