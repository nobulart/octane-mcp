"""Tests for the GET /canvas/recipe/<slug> instant-load route."""

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


class RecipeRouteTest(unittest.TestCase):
    def setUp(self):
        self.srv = gw.make_server("127.0.0.1", 0)
        self.t = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.t.start()
        self.port = self.srv.server_address[1]
        self.base = f"http://127.0.0.1:{self.port}"

    def tearDown(self):
        self.srv.shutdown()
        self.t.join(timeout=2)

    def _get(self, p):
        req = urllib.request.Request(self.base + p, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def test_missing_slug_400(self):
        st, raw = self._get("/canvas/recipe/")
        self.assertEqual(st, 400)

    def test_unknown_slug_404(self):
        st, raw = self._get("/canvas/recipe/does-not-exist")
        self.assertEqual(st, 404)
        self.assertFalse(json.loads(raw)["ok"])

    def test_known_slug_returns_scene(self):
        # A recipe that ships with a scene.json in the repo.
        st, raw = self._get("/canvas/recipe/physics-orbits")
        bd = json.loads(raw)
        self.assertEqual(st, 200)
        self.assertTrue(bd["ok"])
        # Octane recipe format: raw scene.json (named materials, commands),
        # plus a preview_url for instant browser display.
        self.assertIn("scene", bd)
        self.assertIn("materials", bd["scene"])
        self.assertIsNotNone(bd.get("preview_url"))

    def test_recipe_preview_served(self):
        st, raw = self._get("/recipe-preview/physics-orbits")
        self.assertEqual(st, 200)
        # PNG magic bytes.
        self.assertEqual(raw[:4], b"\x89PNG")


if __name__ == "__main__":
    unittest.main()
