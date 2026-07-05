# Octane Lua bridge architecture

OctaneX MCP has two supported Octane-side bridge modes:

- `hermes_bridge_oneshot_v2.lua` drains queued commands and exits so Octane can repaint/render without a modal bridge window staying active.
- `hermes_bridge_persistent_v1.lua` keeps a small manual/timer window open for `Process next` and `Drain queue` workflows.

The modes should differ only in scheduling and UI behavior. Scene command semantics must stay aligned.

Both bridges decode command files with the shared `octane_lua/lib/json.lua` decoder. Keep payload parsing JSON-based; do not reintroduce regex/string extraction for command fields. Invalid JSON should move to `failed/` and write a failed result record with an `invalid JSON` message.

## Octane X Scripts path preference

Octane X only shows/runs Lua scripts from the directory configured in its Preferences. After `octanex-mcp init` generates the portable bridge copies, set Octane X's **Preferences → Scripts path** to this repository's Lua script directory:

```text
/path/to/octane-mcp/octane_lua
```

That directory should contain the generated bridge entrypoints:

```text
hermes_bridge_oneshot.generated.lua
hermes_bridge_persistent.generated.lua
```

If the repo is configured with `OCTANEX_MCP_REPO`, use `$OCTANEX_MCP_REPO/octane_lua`. Restart Octane X if the Scripts menu does not refresh after changing the preference.

## Shared semantic surface

The following handler functions are guarded by `tests/test_lua_bridge_parity.py` and should remain behaviorally identical between one-shot and persistent bridges:

```text
latest_imported_geometry_fallback
handle_import_geometry
handle_create_material
handle_assign_material
handle_set_camera
handle_set_lighting
handle_start_render
handle_save_preview
handle_command
```

If you change one of these in either bridge, update the other bridge in the same patch and run:

```bash
PYTHONPATH= uv run python -m unittest tests.test_lua_bridge_parity -v
```

## Lifecycle

Both bridges now use the same command lifecycle directories:

```text
queue/ -> processing/ -> processed/ or failed/ -> results/
```

Each processed command should write one `results/<command_id>.json` file with success/error metadata. Agents should inspect `results/`, `failed/`, and `bridge.log` before claiming a render or scene operation succeeded.

## Current duplication boundary

The bridge scripts still contain some duplicated Lua because Octane X runs user-selected scripts directly and this keeps the runnable files mostly self-contained. The shared JSON decoder is the first extracted runtime module; parity tests are the guardrail against semantic drift while more helpers move into `octane_lua/lib/*.lua` modules.
