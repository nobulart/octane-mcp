"""Tests for the Hermes config model bridge (canvas agent-model selector)."""

import unittest
from pathlib import Path

from octanex_mcp import hermes_config as hc


SAMPLE_CONFIG = """
model:
  default: tencent/hy3:free
  provider: nous
custom_providers:
  - name: local-ollama
    base_url: http://localhost:11434/v1
    model: qwen3.6:35b
    discover_models: true
    models:
      qwen3.6:35b:
        context_length: 262144
        supports_vision: true
        supports_tools: true
        supports_thinking: true
      devstral-2:latest:
        context_length: 393216
        supports_tools: true
"""


class TestListModels(unittest.TestCase):
    def setUp(self):
        self.path = Path(__file__).parent / "_tmp_hermes_config.yaml"
        self.path.write_text(SAMPLE_CONFIG)

    def tearDown(self):
        if self.path.exists():
            self.path.unlink()

    def test_lists_provider_models(self):
        res = hc.list_models(self.path)
        ids = [o["id"] for o in res["options"]]
        self.assertIn("qwen3.6:35b", ids)
        self.assertIn("devstral-2:latest", ids)

    def test_current_default_included(self):
        res = hc.list_models(self.path)
        self.assertEqual(res["current"], "tencent/hy3:free")
        self.assertIn("tencent/hy3:free", [o["id"] for o in res["options"]])

    def test_capabilities_parsed(self):
        res = hc.list_models(self.path)
        q = next(o for o in res["options"] if o["id"] == "qwen3.6:35b")
        self.assertTrue(q["capabilities"]["vision"])
        self.assertTrue(q["capabilities"]["thinking"])
        self.assertEqual(q["context_length"], 262144)

    def test_missing_config_is_graceful(self):
        res = hc.list_models(Path("/nonexistent/hermes_config.yaml"))
        self.assertEqual(res["options"], [])
        self.assertIn("error", res)


class TestSetCurrentModel(unittest.TestCase):
    def setUp(self):
        self.path = Path(__file__).parent / "_tmp_hermes_config.yaml"
        self.path.write_text(SAMPLE_CONFIG)

    def tearDown(self):
        if self.path.exists():
            self.path.unlink()

    def test_set_known_model(self):
        res = hc.set_current_model("devstral-2:latest", self.path)
        self.assertEqual(res["current"], "devstral-2:latest")
        # Surgical: only model.default changed, rest preserved.
        text = self.path.read_text()
        self.assertIn("default: devstral-2:latest", text)
        self.assertIn("custom_providers:", text)
        self.assertIn("qwen3.6:35b", text)

    def test_unknown_model_rejected(self):
        from octanex_mcp import hermes_config as hc
        with self.assertRaises(ValueError):
            hc.set_current_model("ghost-model", self.path)

    def test_preserves_comments_and_order(self):
        hc.set_current_model("devstral-2:latest", self.path)
        text = self.path.read_text()
        # Comments and structure untouched (config is not re-dumped).
        self.assertIn("custom_providers:", text)
        self.assertIn("discover_models: true", text)


if __name__ == "__main__":
    unittest.main()
