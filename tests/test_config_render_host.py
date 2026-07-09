"""Tests for the OCTANEX_RENDER_HOST config flag (task A5)."""

from octanex_mcp.config import resolve_config


def test_default_render_host_is_localhost():
    cfg = resolve_config({})
    assert cfg.render_host == "localhost"


def test_render_host_env_override():
    cfg = resolve_config({"OCTANEX_RENDER_HOST": "mac-studio.local"})
    assert cfg.render_host == "mac-studio.local"


def test_empty_render_host_falls_back_to_localhost():
    cfg = resolve_config({"OCTANEX_RENDER_HOST": ""})
    assert cfg.render_host == "localhost"
