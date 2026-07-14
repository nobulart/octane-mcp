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
        # Local models are always selectable.
        self.assertTrue(by_id["qwen3.6:35b"]["cloud"] is False)
        self.assertTrue(by_id["qwen3.6:35b"]["selectable"] is True)
        # Cloud selectability is now gated on Hermes proxy reachability, not a
        # per-provider key assumption. In the test env the proxy is down, so
        # cloud models are disabled; when the proxy is up they're all usable.
        self.assertEqual(by_id["openai/gpt-5.6-sol"]["selectable"], hc._hermes_proxy_reachable())

    def test_cloud_selectable_when_proxy_up(self):
        # Simulate the Hermes proxy being reachable: every cloud model becomes
        # selectable (the canvas routes all cloud/Nous models through it).
        orig = hc._hermes_proxy_reachable
        hc._hermes_proxy_reachable = lambda *a, **k: True
        try:
            res = hc.list_models(self.path)
        finally:
            hc._hermes_proxy_reachable = orig
        disabled = [o["id"] for o in res["options"] if o.get("selectable") is False]
        self.assertEqual(disabled, [], "all models selectable when proxy reachable")
        cloud = [o for o in res["options"] if o.get("cloud")]
        self.assertTrue(cloud, "has cloud models")
        self.assertTrue(all(o["selectable"] for o in cloud))

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

    def test_yaml_missing_still_surfaces_cloud_list(self):
        # Regression: on the laptop the gateway venv has no PyYAML, so
        # hermes_config.yaml is None. The canvas must NOT return an empty
        # "config unavailable" error — it should mirror the Hermes cloud
        # model caches (the dynamic list) regardless of yaml availability.
        orig = hc.yaml
        hc.yaml = None
        try:
            res = hc.list_models(self.path)
        finally:
            hc.yaml = orig
        ids = [o["id"] for o in res["options"]]
        self.assertIn("anthropic/claude-fable-5", ids, "cloud catalog surfaced without yaml")
        self.assertIn("gpt-5.4", ids, "provider cache surfaced without yaml")
        self.assertNotIn("error", res, "yaml absence is not a fatal error")
        # The config.yaml local models are skipped (can't parse), but cloud
        # models are still present — the selector is never empty.
        self.assertGreater(len(res["options"]), 0)


    def test_missing_config_is_graceful(self):
        # No config.yaml on disk: the canvas must still mirror the Hermes
        # cloud/models caches (the dynamic list) rather than returning an empty
        # "config unavailable" error. This is exactly the failure mode on the
        # laptop where the gateway venv lacks PyYAML but the caches exist.
        res = hc.list_models(Path("/nonexistent/hermes_config.yaml"))
        ids = [o["id"] for o in res["options"]]
        self.assertIn("anthropic/claude-fable-5", ids, "cloud catalog still surfaced")
        self.assertIn("gpt-5.4", ids, "provider cache still surfaced")
        # current default is unknown (no config to read) but never fatal.
        self.assertIsNone(res["current"])
        self.assertNotIn("error", res, "missing config is not an error")


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
