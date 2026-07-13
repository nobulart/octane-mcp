"""Tests for the GET/POST /config/vox gateway routes + /intent voice flag."""

import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys_path = "/Users/craig/octanex-mcp"
import sys as _sys
if sys_path not in _sys.path:
    _sys.path.insert(0, sys_path)

from octanex_mcp import gateway as gw  # noqa: E402


class VoxRoutesTest(unittest.TestCase):
    def setUp(self):
        # Point hermes_config at a temp config so we don't touch the real one.
        self.tmp = Path(__file__).parent / "_tmp_vox_config.yaml"
        self.tmp.write_text("model:\n  default: tencent/hy3:free\n")
        os.environ["HERMES_CONFIG"] = str(self.tmp)
        gw.hermes_config.config_path = lambda: self.tmp
        gw._canvas_scene.clear()
        self.srv = gw.make_server("127.0.0.1", 0)
        self.t = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.t.start()
        self.port = self.srv.server_address[1]
        self.base = f"http://127.0.0.1:{self.port}"

    def tearDown(self):
        self.srv.shutdown()
        self.t.join(timeout=2)
        if self.tmp.exists():
            self.tmp.unlink()
        os.environ.pop("HERMES_CONFIG", None)

    def _get(self, p):
        with urllib.request.urlopen(self.base + p, timeout=5) as r:
            return r.status, json.loads(r.read())

    def _post(self, p, body):
        req = urllib.request.Request(
            self.base + p,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_get_default_off(self):
        st, bd = self._get("/config/vox")
        self.assertEqual(st, 200)
        self.assertFalse(bd["enabled"])
        self.assertIn("terse", bd["contract"])

    def test_post_enable_persists(self):
        st, bd = self._post("/config/vox", {"enabled": True})
        self.assertEqual(st, 200)
        self.assertTrue(bd["enabled"])
        self.assertIn("enabled: true", self.tmp.read_text())
        # GET now reflects it.
        _, bd2 = self._get("/config/vox")
        self.assertTrue(bd2["enabled"])

    def test_post_disable(self):
        self._post("/config/vox", {"enabled": True})
        st, bd = self._post("/config/vox", {"enabled": False})
        self.assertEqual(st, 200)
        self.assertFalse(bd["enabled"])

    def test_post_rejects_nonbool(self):
        st, _ = self._post("/config/vox", {"enabled": "yes"})
        self.assertEqual(st, 400)
        st, _ = self._post("/config/vox", {})
        self.assertEqual(st, 400)

    def test_intent_records_voice_flag(self):
        # Send a voice-flagged intent; assert it lands in intents.jsonl.
        ws_root = gw.Workspace().root
        log = ws_root / "intents.jsonl"
        if log.exists():
            log.unlink()
        st, bd = self._post("/intent", {"text": "show me a sphere", "voice": True})
        self.assertEqual(st, 200)
        lines = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
        self.assertTrue(any(e.get("voice") is True and e["text"] == "show me a sphere" for e in lines))
        # And a non-voice intent records voice: false.
        self._post("/intent", {"text": "now a cube", "voice": False})
        lines = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
        self.assertTrue(any(e.get("voice") is False and e["text"] == "now a cube" for e in lines))
        log.unlink()


if __name__ == "__main__":
    unittest.main()
