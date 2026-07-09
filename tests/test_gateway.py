"""Tests for the OctaneX Agentic Canvas HTTP gateway (task G0)."""

import json
import threading
import urllib.request

from octanex_mcp import gateway as gw


def test_call_tool_status_ok():
    r = gw.call_tool("octane_status", {})
    assert r["ok"] is True
    assert isinstance(r["result"], dict)


def test_call_tool_unknown_tool():
    r = gw.call_tool("does_not_exist", {})
    assert r["ok"] is False
    assert "unknown tool" in r["error"]


def test_call_tool_validate_command_serializes_dataclass():
    r = gw.call_tool(
        "octane_validate_command",
        {"command": {"op": "import_geometry", "payload": {"path": "assets/cube.obj", "format": "obj", "name": "cube"}}},
    )
    assert r["ok"] is True
    assert isinstance(r["result"], dict)


def test_to_jsonable_dataclass():
    from dataclasses import dataclass

    @dataclass
    class Foo:
        a: int
        b: str

    assert gw._to_jsonable(Foo(1, "x")) == {"a": 1, "b": "x"}


def test_http_server_mcp_call_and_status():
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
        assert body["ok"] is True

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/status", timeout=5) as resp:
            status = json.loads(resp.read())
        assert isinstance(status, dict)

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/config", timeout=5) as resp:
            cfg = json.loads(resp.read())
        assert "render_host" in cfg
    finally:
        server.shutdown()
        t.join(timeout=2)
