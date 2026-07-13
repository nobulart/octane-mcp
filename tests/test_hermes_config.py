"""Tests for the Hermes config model bridge (canvas agent-model selector)."""

import json
import os
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
        # Fake the Hermes cache dir with a curated cloud catalog.
        self.cache = Path(__file__).parent / "_tmp_hermes_cache"
        self.cache.mkdir(exist_ok=True)
        (self.cache / "model_catalog.json").write_text(json.dumps({
            "version": 1,
            "providers": {
                "openrouter": {"models": [
                    {"id": "anthropic/claude-fable-5", "description": "reasoning"},
                    {"id": "openai/gpt-5.6-sol", "description": ""},
                ]},
                "nous": {"models": [
                    {"id": "qwen3.6:35b"},
                ]},
            },
        }))
        (self.cache / "provider_models_cache.json").write_text(json.dumps({
            "copilot": {"fp": "x", "at": 0, "models": ["gpt-5.4", "gpt-5-mini"]},
        }))
        os.environ["HERMES_CACHE"] = str(self.cache)

    def tearDown(self):
        if self.path.exists():
            self.path.unlink()
        import shutil
        if self.cache.exists():
            shutil.rmtree(self.cache)
        os.environ.pop("HERMES_CACHE", None)

    def test_lists_provider_models(self):
        res = hc.list_models(self.path)
        ids = [o["id"] for o in res["options"]]
        self.assertIn("qwen3.6:35b", ids)
        self.assertIn("devstral-2:latest", ids)

    def test_merges_cloud_catalog(self):
        res = hc.list_models(self.path)
        ids = {o["id"] for o in res["options"]}
        # Curated cloud catalog (openrouter + nous).
        self.assertIn("anthropic/claude-fable-5", ids)
        self.assertIn("openai/gpt-5.6-sol", ids)
        # Live provider cache (copilot).
        self.assertIn("gpt-5.4", ids)
        self.assertIn("gpt-5-mini", ids)

    def test_cloud_flag_and_selectable(self):
        res = hc.list_models(self.path)
        by_id = {o["id"]: o for o in res["options"]}
        cloud = by_id["anthropic/claude-fable-5"]
        self.assertTrue(cloud["cloud"])
        # Nous Portal is authed in this harness -> selectable; openrouter gated.
        self.assertTrue(by_id["qwen3.6:35b"]["cloud"] is False)
        self.assertTrue(by_id.get("openai/gpt-5.6-sol", {}).get("selectable") is False)
        # Local models are always selectable.
        self.assertTrue(by_id["qwen3.6:35b"]["selectable"] is True)

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
        self.cache = Path(__file__).parent / "_tmp_hermes_cache"
        self.cache.mkdir(exist_ok=True)
        (self.cache / "model_catalog.json").write_text(json.dumps({
            "version": 1, "providers": {"openrouter": {"models": [{"id": "openai/gpt-5.6-sol"}]}},
        }))
        os.environ["HERMES_CACHE"] = str(self.cache)

    def tearDown(self):
        if self.path.exists():
            self.path.unlink()
        import shutil
        if self.cache.exists():
            shutil.rmtree(self.cache)
        os.environ.pop("HERMES_CACHE", None)

    def test_set_known_model(self):
        res = hc.set_current_model("devstral-2:latest", self.path)
        self.assertEqual(res["current"], "devstral-2:latest")
        text = self.path.read_text()
        self.assertIn("default: devstral-2:latest", text)
        self.assertIn("custom_providers:", text)
        self.assertIn("qwen3.6:35b", text)

    def test_set_cloud_model(self):
        # A cloud model from the catalog is a valid, known option.
        res = hc.set_current_model("openai/gpt-5.6-sol", self.path)
        self.assertEqual(res["current"], "openai/gpt-5.6-sol")
        self.assertIn("default: openai/gpt-5.6-sol", self.path.read_text())

    def test_unknown_model_rejected(self):
        with self.assertRaises(ValueError):
            hc.set_current_model("ghost-model", self.path)

    def test_preserves_comments_and_order(self):
        hc.set_current_model("devstral-2:latest", self.path)
        text = self.path.read_text()
        self.assertIn("custom_providers:", text)
        self.assertIn("discover_models: true", text)


if __name__ == "__main__":
    unittest.main()
