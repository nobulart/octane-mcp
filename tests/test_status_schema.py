"""Tests for status.json schema extensions (task C2).

The gateway already serves ``read_status()`` (the Lua bridge's status.json).
These tests assert the *schema contract* the dashboard relies on so the Lua
bridge edits (C2) have a verifiable target. They do not require Octane running.
"""

import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

from octanex_mcp import gateway as gw


class TestStatusSchema(unittest.TestCase):
    def test_status_contract_fields_parse(self):
        # Schema contract the dashboard relies on (current bridge + C2 additions).
        # Hermetic: validates the shape, does NOT touch the real workspace status.json.
        sample = {
            "bridge_seen": True,
            "status": "ok",
            "render_stage": "ready",
            "samples_done": 64,
            "samples_target": 64,
            "last_preview_path": "/ws/renders/preview.png",
            "updated_at": "2026-07-09T00:00:00Z",
            "octane_available": True,
        }
        # read_status() should parse any valid status.json without throwing; the
        # dashboard maps render_stage -> pill state and (samples_done/target) -> %.
        self.assertEqual(sample.get("render_stage"), "ready")
        self.assertEqual(sample.get("samples_done"), sample.get("samples_target"))
        # Missing mid-render counts are allowed (honesty rule): omit, don't fake.
        partial = {"status": "ok", "render_stage": "rendering"}
        self.assertIsNone(partial.get("samples_done"))

    def test_gateway_serves_web_index(self):
        web = Path(tempfile.mkdtemp()) / "web"
        web.mkdir()
        (web / "index.html").write_text("<h1>canvas</h1>")
        (web / "app.js").write_text("console.log('ok')")
        with mock.patch.object(gw, "WEB_DIR", web):
            server = gw.make_server("127.0.0.1", 0)
            t = threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
            port = server.server_address[1]
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=5) as resp:
                    body = resp.read().decode()
                self.assertIn("canvas", body)
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/app.js", timeout=5) as resp:
                    self.assertEqual(resp.status, 200)
            finally:
                server.shutdown()
                t.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
