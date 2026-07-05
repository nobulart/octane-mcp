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

`profiles/octanex/config.yaml` is a minimal profile overlay/snippet. Replace `/ABSOLUTE/PATH/TO/octanex-mcp` with this checkout path, or generate an equivalent config with:

```bash
hermes profile create octanex
hermes --profile octanex config set mcp_servers.octanex.command uv
```

Then edit `~/.hermes/profiles/octanex/config.yaml` to include the args from the snippet.

## Smoke test

```bash
PYTHONPATH= uv run octanex-mcp init
PYTHONPATH= uv run octanex-mcp doctor
hermes mcp test octanex
```

Inside Octane X, set the Scripts path to this repo's `octane_lua/` directory and run `hermes_bridge_oneshot.generated.lua` for batch drains.
