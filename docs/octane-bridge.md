# Octane Lua bridge architecture

OctaneX MCP has two supported Octane-side bridge modes:

- `hermes_bridge_oneshot_v2.lua` drains queued commands and exits so Octane can repaint/render without a modal bridge window staying active.
- `hermes_bridge_persistent_v1.lua` keeps a small manual/timer window open for `Process next` and `Drain queue` workflows.

The modes should differ only in scheduling and UI behavior. Scene command semantics must stay aligned.

Both bridges decode command files with the shared `octane_lua/lib/json.lua` decoder. Keep payload parsing JSON-based; do not reintroduce regex/string extraction for command fields. Invalid JSON should move to `failed/` and write a failed result record with an `invalid JSON` message.

## Octane X Scripts path preference

Octane X only shows/runs Lua scripts from the directory configured in its Preferences. After `octanex-mcp init` generates the portable bridge copies, set Octane X's **Preferences → Scripts path** to this repository's Lua script directory:

```text
/Users/craig/octanex-mcp/octane_lua
```

That directory contains the generated bridge entrypoints:

```text
hermes_bridge_oneshot.generated.lua
hermes_bridge_persistent.generated.lua
```

If the repo is configured with `OCTANEX_MCP_REPO`, use `$OCTANEX_MCP_REPO/octane_lua`. Restart Octane X if the **Script** menu does not refresh after changing the preference.

## Shared semantic surface

The following handler functions are guarded by `tests/test_lua_bridge_parity.py` and should remain behaviorally identical between one-shot and persistent bridges:

```text
latest_imported_geometry_fallback
handle_import_geometry
handle_create_material
handle_assign_material
handle_set_camera
handle_get_camera
handle_set_lighting
handle_start_render
handle_save_preview
handle_command
```

`get_camera` (added 2026-07-14) reads the live "Hermes Camera" node's
`position` / `target` / `fov` / `up` pins via `getPinValue` and writes the pose
to `results/get_camera.json`. It is the inverse of `set_camera`: capture a
user-set viewport angle exactly (instead of eyeballing it from a screenshot)
so it can be re-applied. Wired into both bridges; parity-guarded.

If you change one of these in either bridge, update the other bridge in the same patch and run:

```bash
PYTHONPATH= uv run python -m unittest tests.test_lua_bridge_parity -v
```

## Lifecycle

Both bridges now use the same command lifecycle directories:

```text
queue/ -> processing/ -> processed/ or failed/ -> results/
```

Each processed command writes one `results/<command_id>.json` file with success/error metadata. Agents should inspect `results/`, `failed/`, and `bridge.log` before claiming a render or scene operation succeeded.

## Current duplication boundary

The bridge scripts still contain some duplicated Lua because Octane X runs user-selected scripts directly and this keeps the runnable files mostly self-contained. The shared JSON decoder is the first extracted runtime module; parity tests are the guardrail against semantic drift while more helpers move into `octane_lua/lib/*.lua` modules.

## Workspace and generated files

By default, the Python MCP server writes commands to the real Octane X sandbox container path:

```text
~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/
```

`octanex-mcp init` creates the workspace directories, writes the JSON/Lua config files, and generates portable bridge entrypoints with the resolved workspace path injected.

Important generated files:

```text
~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/octanex-mcp.config.json
/path/to/repo/octane_lua/config.generated.lua
/path/to/repo/octane_lua/hermes_bridge_oneshot.generated.lua
/path/to/repo/octane_lua/hermes_bridge_persistent.generated.lua
```

Runtime state lives under the workspace:

```text
queue/*.json        queued commands
processing/*.json   command currently being handled
processed/*.json    successful processed commands
failed/*.json       failed command payloads
results/*.json      per-command result metadata
renders/*.png       preview/render outputs
status.json         bridge heartbeat/state
bridge.log          bridge diagnostics
```

## Environment variables

The supported configuration variables are:

| Variable | Purpose |
| --- | --- |
| `OCTANEX_MCP_WORKSPACE` | Override the command queue workspace visible to Octane Lua. |
| `OCTANEX_MCP_REPO` | Override the repository root used to locate/generate Lua bridge scripts. |
| `OCTANEX_APP_PATH` | Override the Octane X `.app` bundle path. |
| `OCTANE_APP_PATH` | Legacy alias used only as the default for `OCTANEX_APP_PATH`. |

After changing path variables, rerun:

```bash
PYTHONPATH= uv run octanex-mcp init
PYTHONPATH= uv run octanex-mcp doctor
```

## Running the bridge

Use Octane X's configured **Script** menu to run one of the generated bridge files:

| Mode | Script | Usage |
| --- | --- | --- |
| One-shot | `hermes_bridge_oneshot.generated.lua` | Preferred batch path. Drains the **entire** queued command set in one run, renders, and exits so Octane can repaint. |
| Persistent | `hermes_bridge_persistent.generated.lua` | Opens a small bridge window for manual `Process next` / `Drain queue` use. |

> **One click = whole queue.** The one-shot bridge drains *all* queued commands in a single run (verified live: an 8-command recipe rendered + saved from one drain). Do not loop "one click per command".

For agent workflows, queue commands from MCP, ask the user to run the one-shot script inside Octane X, then inspect `processed/`, `failed/`, `results/`, `status.json`, and any saved preview before reporting success.

## On-demand bridge management from Hermes

The MCP server includes macOS helpers for reducing manual bridge work:

```bash
PYTHONPATH= uv run octanex-mcp bridge-status --json
PYTHONPATH= uv run octanex-mcp run-oneshot --dry-run --json
PYTHONPATH= uv run octanex-mcp run-oneshot --json
PYTHONPATH= uv run octanex-mcp start-persistent --json
```

Equivalent MCP tools:

- `octane_bridge_process_status()`
- `octane_run_oneshot_bridge(dry_run=false, timeout_seconds=15)`
- `octane_start_persistent_bridge(dry_run=false, timeout_seconds=15)`

These helpers open Octane X if needed and use AppleScript/System Events to click a matching generated bridge script in Octane X's **Script** menu. They return the generated AppleScript, stdout/stderr, current bridge status, and next-step guidance on failure.

Known limitations:

- **macOS Accessibility (TCC) for the Hermes agent-runtime python, NOT `Hermes.app`, is the #1 launch blocker** (CORRECTED 2026-07-09). `osascript` is spawned by the `octanex-mcp` server, which is a child of the **Hermes agent runtime** (`/Users/craig/.hermes/hermes-agent/venv/bin/python`) — a separate process from the `Hermes.app` GUI. macOS evaluates the Accessibility entitlement on that runtime binary, so granting `Hermes.app` alone does NOT clear `-1719`. Grant Accessibility to the runtime python (or, if it is hard to select, to the Terminal/app that launches Hermes), then restart Hermes. `run_bridge_script` now returns `tcc_blocked: true` with this exact fix instead of a misleading "script not found" error.
- **TCC token is cached against the live process tree — re-adding alone does NOT clear `-1719` (VERIFIED 2026-07-12).** Re-adding the binary to Accessibility in System Settings updates the *stored* policy, but macOS keeps evaluating the *cached* token of the already-running process. Observed: after re-adding the runtime python, `osascript scripts/relaunch_octane_oneshot.applescript` still returned `assistive access denied (-1719)` from the *same* live Hermes session. The grant only took effect after a full **Hermes restart** (and the terminal/tab that spawned `osascript`, since TCC walks up to the nearest granted ancestor). Fix sequence: remove + re-add the binary, **then restart Hermes** (and the spawning terminal), then re-run. Do not expect a re-add to hot-swap the token on a running process.
- A standalone relaunch+click driver lives at `scripts/relaunch_octane_oneshot.applescript` (quit Octane → relaunch → click `Script > hermes_bridge_oneshot.generated`). Verified live with TCC granted + Hermes restarted it returns `clicked hermes_bridge_oneshot.generated via Script` (exit 0). **No manual "Hermes Render Target" re-select is required** — the Lua bridge activates the render target itself (live log: `activated render target Hermes Render Target` → `render start requested` → PNG saved). A full suite of composable control scripts (launch / `File▸New` / run-oneshot / run-persistent / cancel / shutdown / status / drain / flush) lives in `scripts/octane_*.applescript`, documented in `scripts/octane_control.md`.
- If Octane X's **Script** menu (singular) does not expose the generated file names, the helper reports a structured failure instead of pretending the bridge ran. The menu is named "Script", not "Scripts".
- If the persistent bridge is already open, queued commands can still process through that window/timer even when menu automation is unavailable.

