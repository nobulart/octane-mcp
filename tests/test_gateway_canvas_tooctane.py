"""Tests for the POST /canvas/to-octane handoff route (Phase 6)."""

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


# A representative canvas.scene.v1 emitted by the live WebGL planner.
SAMPLE_SCENE = {
    "schema_version": "canvas.scene.v1",
    "scene_id": "toctane_test",
    "intent": "a red sphere",
    "units": "arbitrary",
    "camera": {"position": [4, 3, 4], "target": [0, 0, 0], "fov": 45},
    "environment": {"background": "#070a0e", "lighting": "soft_studio"},
    "objects": [
        {"id": "earth", "label": "#1", "type": "sphere", "position": [0, 0, 0],
         "scale": [1, 1, 1], "material": "red_matte"},
    ],
    "materials": [
        {"id": "red_matte", "color": "#ff0000", "roughness": 0.8, "metalness": 0.0},
    ],
}


class ToOctaneRouteTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(__file__).parent / "_tmp_tooctane_config.yaml"
        self.tmp.write_text("model:\n  default: tencent/hy3:free\n")
        os.environ["HERMES_CONFIG"] = str(self.tmp)
        gw.hermes_config.config_path = lambda: self.tmp
        # Seed the live scene so the route has something to hand off.
        gw._canvas_scene.clear()
        gw._canvas_scene.update(SAMPLE_SCENE)
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
        # Clean any queue/manifest the route wrotes into the workspace.
        ws = gw.Workspace()
        for p in (ws.root / "queue").glob("*") if (ws.root / "queue").exists() else []:
            try:
                p.unlink()
            except OSError:
                pass

    def _post(self, p, body):
        req = urllib.request.Request(
            self.base + p,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_no_scene_404(self):
        gw._canvas_scene.clear()
        st, bd = self._post("/canvas/to-octane", {})
        self.assertEqual(st, 404)

    def test_handoff_dry_run(self):
        # dry_run avoids invoking osascript/Octane; the queue + bridge
        # planning still execute, proving the scene->queue->bridge wiring.
        # The route now answers 202 (async): it flushes+queues, starts the
        # background drain+render, and returns immediately with progress hints.
        st, bd = self._post("/canvas/to-octane", {"dry_run": True})
        self.assertEqual(st, 202, msg=bd)
        self.assertTrue(bd["ok"])
        self.assertTrue(bd["async"])
        self.assertEqual(bd["scene_id"], "toctane_test")
        self.assertGreaterEqual(bd["queued_commands"], 1)


if __name__ == "__main__":
    unittest.main()
