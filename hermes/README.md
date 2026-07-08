# Hermes assets for OctaneX MCP

This directory contains optional Hermes Agent helpers for using this repo on a fresh or updated system.

## Skill

Copy or symlink the skill into your Hermes skills directory, then start a new Hermes session or run `/reload-skills`:

```bash
mkdir -p ~/.hermes/skills/local-rendering
ln -s "$(pwd)/hermes/skills/octanex-mcp" ~/.hermes/skills/local-rendering/octanex-mcp
```

The skill gives agents the operational loop for configuring the MCP server, draining the Octane Lua bridge, saving render-ready PNG previews, and reviewing them with local vision.

## Profile/config snippet

`profiles/octanex/config.yaml` is a minimal profile overlay/snippet that registers the OctaneX MCP server for a dedicated `octanex` Hermes profile. It points at the bundled `run_octanex_mcp.sh` launcher, which strips the Hermes runtime `PYTHONPATH` so the server uses its own `.venv` (with `mcp`/`pydantic_core`) instead of Hermes' broken one. Replace `/ABSOLUTE/PATH/TO/octanex-mcp` with this checkout path, or generate an equivalent profile config:

```bash
hermes profile create octanex
hermes --profile octanex config set mcp_servers.octanex.command "/ABSOLUTE/PATH/TO/octanex-mcp/run_octanex_mcp.sh"
hermes --profile octanex config set mcp_servers.octanex.args "[]"
hermes --profile octanex config set mcp_servers.octanex.connect_timeout 30
```

> Do NOT use `command: uv` / bare `uv run` in a profile — Hermes spawns the MCP subprocess with its own runtime `PYTHONPATH`, which crashes the server on import (`No module named 'pydantic_core._pydantic_core'`). The launcher fixes this.

## Smoke test

```bash
PYTHONPATH= uv run octanex-mcp init
PYTHONPATH= uv run octanex-mcp doctor
hermes mcp list        # shows `octanex` (✓ enabled)
hermes mcp test octanex
```

Inside Octane X, set the Scripts path to this repo's `octane_lua/` directory and run `hermes_bridge_oneshot.generated.lua` for batch drains.
