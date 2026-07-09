"""Tests for the progressive save_preview envelope (task C1, Python side).

Asserts the command JSON the gateway/MCP tool queues carries the progressive
flags. The Lua bridge edit that *consumes* these flags lives in
``octane_lua/hermes_bridge_oneshot_v2.lua`` (handle_save_preview) and is applied
separately (it is part of an in-flight bridge WIP branch).
"""

from octanex_mcp.server import _build_save_preview_envelope as build_env


def test_progressive_envelope_carries_flags():
    env = build_env(progressive=True)
    assert env["progressive"] is True
    assert "progressive_path" in env
    assert env["progressive_path"].endswith("preview_progressive.png")


def test_non_progressive_envelope_has_no_progressive_path():
    env = build_env()
    assert env["progressive"] is False
    assert "progressive_path" not in env


def test_quality_tier_resolves():
    env = build_env(quality="standard")
    # standard tier -> samples 512 / min_samples 24 / timeout 30 (per QUALITY_TIERS)
    assert env["samples"] == 512
    assert env["min_samples"] == 24
    assert env["timeout_seconds"] == 30


def test_bad_quality_raises():
    import pytest

    with pytest.raises(ValueError):
        build_env(quality="nope")
