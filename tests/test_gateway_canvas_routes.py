"""Tests for the new /canvas/scene and /canvas/build gateway routes (first PR)."""

import json
import threading
import unittest
import urllib.error
import urllib.request

from octanex_mcp import gateway as gw


class TestCanvasRoutes(unittest.TestCase):
    def setUp(self):
        # Reset the module-level scene store between tests.
        gw._canvas_scene.clear()
        self.server = gw.make_server("127.0.0.1", 0)
        self.t = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.t.start()
        self.port = self.server.server_address[1]
        self.base = f"http://127.0.0.1:{self.port}"

    def tearDown(self):
        gw._canvas_scene.clear()
        self.server.shutdown()
        self.t.join(timeout=2)

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

    def test_get_scene_empty_before_build(self):
        status, body = self._get("/canvas/scene")
        self.assertEqual(status, 404)
        self.assertFalse(body["ok"])

    def test_build_with_intent_returns_v1(self):
        status, body = self._post("/canvas/build", {"intent": "show me a cube"})
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["schema_version"], "canvas.scene.v1")
        self.assertEqual(body["scene"]["objects"][0]["type"], "box")

    def test_build_with_explicit_scene_plan(self):
        plan = {
            "scene_id": "manual",
            "objects": [{"id": "a", "type": "sphere", "material": "m"}],
            "materials": [{"id": "m", "color": "#fff"}],
        }
        status, body = self._post("/canvas/build", {"scene": plan})
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["scene"]["scene_id"], "manual")

    def test_build_invalid_plan_rejected_422(self):
        status, body = self._post("/canvas/build", {"scene": {"objects": [{"id": "x", "type": "bad", "material": "ghost"}]}})
        self.assertEqual(status, 422)
        self.assertFalse(body["ok"])
        self.assertIn("invalid", body["error"])

    def test_get_scene_returns_built_scene(self):
        self._post("/canvas/build", {"intent": "orbital decay"})
        status, body = self._get("/canvas/scene")
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["scene"]["scene_id"], "orbital_decay")

    def test_build_empty_intent_falls_back_to_demo(self):
        # No intent, no scene -> planner returns the neutral demo (still valid).
        status, body = self._post("/canvas/build", {})
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["scene"]["objects"][0]["type"], "box")

    def test_patch_object_color_updates_scene(self):
        self._post("/canvas/build", {"intent": "orbital decay"})
        status, body = self._post(
            "/canvas/patch", {"object_id": "earth", "changes": {"material": {"color": "#ff0000"}}}
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        mat = next(m for m in body["scene"]["materials"] if m["id"] == "blue_planet")
        self.assertEqual(mat["color"], "#ff0000")
        # The stored scene reflects the patch too.
        _, stored = self._get("/canvas/scene")
        stored_mat = next(m for m in stored["scene"]["materials"] if m["id"] == "blue_planet")
        self.assertEqual(stored_mat["color"], "#ff0000")

    def test_patch_no_scene_404(self):
        status, body = self._post(
            "/canvas/patch", {"object_id": "earth", "changes": {"scale": [2, 2, 2]}}
        )
        self.assertEqual(status, 404)
        self.assertFalse(body["ok"])

    def test_patch_invalid_field_422(self):
        self._post("/canvas/build", {"intent": "cube"})
        status, body = self._post(
            "/canvas/patch", {"object_id": "cube", "changes": {"bogus": 1}}
        )
        self.assertEqual(status, 422)
        self.assertFalse(body["ok"])

    def test_patch_top_level_title(self):
        self._post("/canvas/build", {"intent": "cube"})
        status, body = self._post("/canvas/patch", {"changes": {"title": "Renamed"}})
        self.assertEqual(status, 200)
        self.assertEqual(body["scene"]["title"], "Renamed")


if __name__ == "__main__":
    unittest.main()
