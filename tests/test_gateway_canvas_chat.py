"""Tests for the POST /canvas/chat route (agentic query -> Hermes API)."""

import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

sys_path = "/Users/craig/octanex-mcp"
import sys as _sys
if sys_path not in _sys.path:
    _sys.path.insert(0, sys_path)

from octanex_mcp import gateway as gw  # noqa: E402


class ChatRouteTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(__file__).parent / "_tmp_chat_cfg.yaml"
        self.tmp.write_text("model:\n  default: tencent/hy3:free\n")
        os.environ["HERMES_CONFIG"] = str(self.tmp)
        gw.hermes_config.config_path = lambda: self.tmp
        # Point the route at a non-listening port so the proxy is "down".
        self._orig = gw.HERMES_PROXY_URL
        gw.HERMES_PROXY_URL = "http://127.0.0.1:59999/v1/chat/completions"
        self.srv = gw.make_server("127.0.0.1", 0)
        self.t = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.t.start()
        self.port = self.srv.server_address[1]
        self.base = f"http://127.0.0.1:{self.port}"
        # Capture the REAL urlopen so this test client hits the actual
        # gateway, while the mock patches the module attribute the
        # server handler reads (so the handler's proxy call is faked).
        self._real = urllib.request.urlopen

    def tearDown(self):
        self.srv.shutdown()
        self.t.join(timeout=2)
        gw.HERMES_PROXY_URL = self._orig
        if self.tmp.exists():
            self.tmp.unlink()
        os.environ.pop("HERMES_CONFIG", None)

    def _post(self, p, body):
        req = urllib.request.Request(
            self.base + p,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            # Use the captured REAL urlopen (the mock only patches the
            # module attribute the server handler reads, so this test client
            # still hits the actual gateway).
            with self._real(req, timeout=5) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_text_required(self):
        st, bd = self._post("/canvas/chat", {})
        self.assertEqual(st, 400)

    def test_proxy_down_returns_502(self):
        # Port 59999 is not listening -> proxy unavailable.
        st, bd = self._post("/canvas/chat", {"text": "hi", "model": "tencent/hy3:free"})
        self.assertEqual(st, 502)
        self.assertIn("proxy", bd.get("error", "").lower())

    def test_success_forwards_to_proxy(self):
        # Simulate the Hermes proxy returning an OpenAI-shaped completion.
        fake = {
            "choices": [
                {"message": {"role": "assistant", "content": "Roger. Terse reply."}}
            ]
        }
        with mock.patch.object(gw.urllib.request, "urlopen",
                               side_effect=lambda req, timeout=0: _FakeResp(fake)):
            st, bd = self._post(
                "/canvas/chat", {"text": "explain orbits", "model": "tencent/hy3:free"}
            )
        self.assertEqual(st, 200)
        self.assertTrue(bd["ok"])
        self.assertEqual(bd["model"], "tencent/hy3:free")
        self.assertEqual(bd["reply"], "Roger. Terse reply.")

    def test_scene_aware_prompt_and_image(self):
        # The handler must bake the live scene + selection into the system
        # prompt and, when an image is attached, send a multimodal user message.
        captured = {}

        def _fake_urlopen(req, timeout=0):
            captured["body"] = json.loads(req.data.decode())
            return _FakeResp({"choices": [{"message": {"role": "assistant", "content": "ok"}}]})

        scene = {
            "scene_id": "desk-fan",
            "objects": [
                {"id": "desk-fan_3", "type": "mesh", "label": "blades", "material": "mat_3"},
                {"id": "desk-fan_1", "type": "mesh", "label": "base", "material": "mat_1"},
            ],
            "materials": [{"id": "mat_3", "color": "#2233ff"}, {"id": "mat_1", "color": "#888888"}],
        }
        with mock.patch.object(gw.urllib.request, "urlopen", side_effect=_fake_urlopen):
            st, bd = self._post("/canvas/chat", {
                "text": "make the blades green",
                "model": "tencent/hy3:free",
                "scene": scene,
                "selection": "desk-fan_3",
                "image": "data:image/png;base64,AAAA",
            })
        self.assertEqual(st, 200)
        body = captured["body"]
        sysmsg = body["messages"][0]["content"]
        self.assertIn("LIVE SCENE under your control", sysmsg)
        self.assertIn("desk-fan_3", sysmsg)
        self.assertIn("blades", sysmsg)
        self.assertIn("SELECTED object id='desk-fan_3'", sysmsg)
        # Multimodal user content
        user = body["messages"][-1]["content"]
        self.assertIsInstance(user, list)
        self.assertEqual(user[1]["type"], "image_url")
        self.assertEqual(user[1]["image_url"]["url"], "data:image/png;base64,AAAA")


class ChatRoutingTest(unittest.TestCase):
    """_chat_upstream routes local providers to Ollama, others to the proxy."""

    def test_local_provider_routes_to_ollama(self):
        with mock.patch.object(gw.hermes_config, "list_models",
                               return_value={"options": [
                                   {"id": "qwen3.6:35b-mlx", "provider": "local-ollama", "cloud": False},
                                   {"id": "tencent/hy3:free", "provider": "openrouter", "cloud": True},
                               ]}):
            self.assertEqual(gw._chat_upstream("qwen3.6:35b-mlx"), gw.LOCAL_LLM_URL)
            self.assertEqual(gw._chat_upstream("tencent/hy3:free"), gw.HERMES_PROXY_URL)

    def test_unknown_namespaced_id_routes_to_proxy(self):
        # A namespaced id we don't recognize is assumed cloud -> proxy.
        self.assertEqual(gw._chat_upstream("anthropic/unknown"), gw.HERMES_PROXY_URL)

    def test_unknown_bare_id_routes_to_local(self):
        # A bare tag with no namespace is assumed a local Ollama model.
        self.assertEqual(gw._chat_upstream("llama3:8b"), gw.LOCAL_LLM_URL)


class _FakeResp:
    def __init__(self, payload):
        self.status = 200
        self._payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self._payload


if __name__ == "__main__":
    unittest.main()
