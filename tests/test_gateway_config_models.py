"""Tests for the GET/POST /config/models gateway routes (agent-model selector)."""

import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from octanex_mcp import gateway as gw

_SAMPLE = """
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
"""


class TestConfigModelsRoutes(unittest.TestCase):
    def setUp(self):
        self.cfg = Path(__file__).parent / "_tmp_gw_config.yaml"
        self.cfg.write_text(_SAMPLE)
        os.environ["HERMES_CONFIG"] = str(self.cfg)
        # Point the bridge at our temp config.
        gw.hermes_config.config_path = lambda: self.cfg
        gw._canvas_scene.clear()
        self.server = gw.make_server("127.0.0.1", 0)
        self.t = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.t.start()
        self.port = self.server.server_address[1]
        self.base = f"http://127.0.0.1:{self.port}"

    def tearDown(self):
        self.server.shutdown()
        self.t.join(timeout=2)
        if self.cfg.exists():
            self.cfg.unlink()
        os.environ.pop("HERMES_CONFIG", None)
        gw.hermes_config.config_path = lambda: Path(os.path.expanduser("~/.hermes/config.yaml"))

    def _get(self, path):
        try:
            with urllib.request.urlopen(f"{self.base}{path}", timeout=5) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def _post(self, path, body):
        req = urllib.request.Request(
            f"{self.base}{path}",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_get_models_lists_options(self):
        status, body = self._get("/config/models")
        self.assertEqual(status, 200)
        ids = [o["id"] for o in body["options"]]
        self.assertIn("qwen3.6:35b", ids)
        self.assertEqual(body["current"], "tencent/hy3:free")

    def test_post_models_sets_default(self):
        status, body = self._post("/config/models", {"model": "qwen3.6:35b"})
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["current"], "qwen3.6:35b")
        # Persisted to the config file surgically.
        self.assertIn("default: qwen3.6:35b", self.cfg.read_text())

    def test_post_models_rejects_unknown(self):
        status, body = self._post("/config/models", {"model": "ghost"})
        self.assertEqual(status, 422)
        self.assertFalse(body["ok"])

    def test_post_models_rejects_empty(self):
        status, body = self._post("/config/models", {"model": ""})
        self.assertEqual(status, 400)
        self.assertFalse(body["ok"])


if __name__ == "__main__":
    unittest.main()
