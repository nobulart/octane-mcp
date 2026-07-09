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


if __name__ == "__main__":
    unittest.main()
