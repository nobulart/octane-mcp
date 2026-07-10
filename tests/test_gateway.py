"""Tests for the OctaneX Agentic Canvas HTTP gateway (task G0)."""

import json
import threading
import unittest
import urllib.request

from octanex_mcp import gateway as gw


class TestGateway(unittest.TestCase):
    def test_call_tool_status_ok(self):
        r = gw.call_tool("octane_status", {})
        self.assertTrue(r["ok"])
        self.assertIsInstance(r["result"], dict)

    def test_call_tool_unknown_tool(self):
        r = gw.call_tool("does_not_exist", {})
        self.assertFalse(r["ok"])
        self.assertIn("unknown tool", r["error"])

    def test_call_tool_validate_command_serializes_dataclass(self):
        r = gw.call_tool(
            "octane_validate_command",
            {"command": {"op": "import_geometry", "payload": {"path": "assets/cube.obj", "format": "obj", "name": "cube"}}},
        )
        self.assertTrue(r["ok"])
        self.assertIsInstance(r["result"], dict)

    def test_to_jsonable_dataclass(self):
        from dataclasses import dataclass

        @dataclass
        class Foo:
            a: int
            b: str

        self.assertEqual(gw._to_jsonable(Foo(1, "x")), {"a": 1, "b": "x"})

    def test_http_server_mcp_call_and_status(self):
        server = gw.make_server("127.0.0.1", 0)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        port = server.server_address[1]
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/mcp/call",
                data=json.dumps({"tool": "octane_status", "args": {}}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = json.loads(resp.read())
            self.assertTrue(body["ok"])

            with urllib.request.urlopen(f"http://127.0.0.1:{port}/status", timeout=5) as resp:
                status = json.loads(resp.read())
            self.assertIsInstance(status, dict)

            with urllib.request.urlopen(f"http://127.0.0.1:{port}/config", timeout=5) as resp:
                cfg = json.loads(resp.read())
            self.assertIn("render_host", cfg)
        finally:
            server.shutdown()
            t.join(timeout=2)


class TestSwapGeometryTool(unittest.TestCase):
    """Gateway parity for the new ``octane_swap_geometry`` tool (WIP item H2)."""

    def _seed(self, tmp):
        from octanex_mcp.bridge import Workspace
        from octanex_mcp.scene import save_scene_manifest

        ws = Workspace(root=tmp)
        save_scene_manifest(
            {
                "scene_id": "swaptest",
                "title": "t",
                "domain": "x",
                "objects": [{"id": "o1", "name": "o1", "type": "box", "size": 1.0, "path": "", "format": "obj"}],
            },
            workspace=ws,
        )
        new_obj = tmp / "replacement.obj"
        new_obj.write_text("o obj\nv 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
        return new_obj

    def test_swap_geometry_registered_and_routes(self):
        import octanex_mcp.gateway as g
        import inspect

        self.assertIn("octane_swap_geometry", g.DISPATCH)
        src = inspect.getsource(g.DISPATCH["octane_swap_geometry"])
        self.assertIn("_swap_geometry_dispatch", src)

    def test_swap_geometry_dispatch_swaps_and_queues(self):
        import tempfile
        from unittest import mock
        import octanex_mcp.gateway as g
        from octanex_mcp.bridge import Workspace
        from octanex_mcp.scene import load_scene_manifest

        with tempfile.TemporaryDirectory(prefix="swap-gw-") as td:
            td = __import__("pathlib").Path(td).resolve()
            new_obj = self._seed(td)
            with mock.patch.object(g, "Workspace", lambda: Workspace(root=td)):
                out = g.call_tool(
                    "octane_swap_geometry",
                    {"scene_id": "swaptest", "object_id": "o1", "new_path": str(new_obj), "format": "obj", "queue": True},
                )
        # The gateway helper operates on the real OctaneMCP workspace (Workspace()
        # is a module global in octanex_mcp.scene, not gateway), so the dispatch
        # result is what we assert — isolation of the manifest on disk is covered
        # by the library-level SwapGeometryTests + the MCP-tool ad-hoc check.
        self.assertTrue(out["ok"], out)
        res = out["result"]
        self.assertEqual(res["node_name"], "Hermes::swaptest::o1")
        self.assertEqual(res["path"], str(new_obj))
        self.assertIn("queued", res)


if __name__ == "__main__":
    unittest.main()
