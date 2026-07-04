# OctaneX MCP

A local MCP server that lets Hermes Agent use **Octane X as a shared visual canvas** for geometry, data, math, and concept visualization.

```text
Hermes MCP tool call -> Python MCP server -> JSON command queue -> Octane Lua bridge -> Octane X viewport/render target
```

The bridge intentionally avoids arbitrary Lua execution. The MCP server emits a small allowlisted command DSL, and the Octane-side Lua bridge validates and processes those commands inside Octane X.

## What this is for

Use this project when an agent needs to turn an explanation into a rendered scene:

- data as 3D bar charts or future chart grammars;
- math as surfaces and geometric objects;
- concepts as simple staged scenes;
- Hermes' avatar as a visual guide inside a render;
- quick render/preview/review loops for local visual R&D.

The documentation is written for rapid agentic learning, including smaller local models: start with the workflow cards below, then copy the exact examples.

## Current status

Verified or implemented:

- `octanex-mcp` stdio MCP server.
- Hermes MCP config pattern for `mcp_servers.octanex`.
- Octane X sandbox/container workspace path.
- Ordered JSON command queue plus `inbox.json` compatibility fallback.
- One-shot Lua bridge that drains `queue/*.json` and exits.
- Persistent Lua bridge window with manual `Process next` / `Drain queue` controls and timer fallback notes.
- Scene operations: import mesh, create material, assign material, set camera, set lighting, start/restart render, save preview.
- Visual tools: bar chart, math surface, Hermes avatar face.
- Self-improving recipe book tools: agents can read and append successes, failures, partials, and pitfalls.

Known constraints:

- Octane X is sandboxed on macOS. Hermes must write to the real app-container path, not the apparent `~/OctaneMCP` path.
- Persistent Lua UI can block Octane's viewport refresh. Prefer one-shot queue draining for batches when the viewport looks stale.
- The core Python package stays lightweight: only `mcp` is required. Heavier geometry/science packages should be optional.

## Install and run

From this repo:

```bash
uv sync
PYTHONPATH= uv run octanex-mcp --self-test
```

Hermes config in `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  octanex:
    command: "uv"
    args: ["run", "--project", "/Users/craig/octanex-mcp", "octanex-mcp"]
    timeout: 180
    connect_timeout: 30
```

Restart Hermes or use `/reload-mcp` after config changes, then verify:

```bash
hermes mcp test octanex
```

## Workspace paths

Hermes writes to the real Octane X sandbox container path:

```text
/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/
```

Octane Lua may appear to use this path in scripts:

```text
/Users/craig/OctaneMCP/
```

For reliability, current scripts use the real container path directly.

Important files:

```text
.../OctaneMCP/inbox.json          latest command fallback
.../OctaneMCP/queue/*.json        ordered command queue
.../OctaneMCP/processed/*.json    successful processed commands
.../OctaneMCP/failed/*.json       failed command payloads
.../OctaneMCP/assets/             generated OBJ assets
.../OctaneMCP/renders/            preview/render outputs
.../OctaneMCP/status.json         bridge status/heartbeat
.../OctaneMCP/bridge.log          bridge log
```

## Octane-side bridge scripts

### Preferred batch fallback: one-shot bridge

Open Octane X and run:

```text
/Users/craig/octanex-mcp/octane_lua/hermes_bridge_oneshot_v2.lua
```

This drains all ordered `queue/*.json` commands and exits so Octane's viewport/render loop can repaint. It also falls back to `inbox.json` for older single-command workflows.

### Persistent bridge window

Open Octane X and run:

```text
/Users/craig/octanex-mcp/octane_lua/hermes_bridge_persistent_v1.lua
```

Leave the `Hermes Octane MCP Bridge` window open while using Hermes. If the timer mode is unavailable, use `Process next` for one command or `Drain queue` for a batch. Do **not** add sleep loops to Octane Lua; they run on the UI thread and can freeze Octane X.

If the persistent bridge closes with status `released` after `start_render`, that is intentional: it gives Octane's renderer a chance to repaint.

## MCP tool catalogue

### Status and learning

| Tool | Purpose |
| --- | --- |
| `octane_status()` | App existence, queue, processed/failed files, bridge status. |
| `octane_recipe_book(limit_chars=12000)` | Read local field notes for successes, failures, and pitfalls. |
| `octane_record_recipe(title, outcome, context, steps, signals, follow_ups)` | Append a lesson to `docs/recipe-book.md`. |

### Low-level scene commands

| Tool | Purpose |
| --- | --- |
| `octane_ping(message)` | Queue a bridge ping. |
| `octane_create_test_cube(name, size)` | Generate a cube OBJ and queue import. |
| `octane_import_geometry(path, name, format)` | Queue OBJ/USD/FBX/Alembic import. |
| `octane_create_material(name, kind, color, roughness, metallic)` | Queue material create/update. |
| `octane_assign_material(object_name, material_name)` | Queue material assignment. |
| `octane_set_camera(position, target, fov)` | Queue camera placement. |
| `octane_set_lighting(preset)` | Queue lighting preset. |
| `octane_start_render(samples, width, height)` | Queue render restart and resolution update. |
| `octane_save_preview(path, width, height)` | Queue preview save. |

### Higher-level visual tools

| Tool | Purpose |
| --- | --- |
| `octane_visualize_bars(values, name)` | Build a 3D bar chart OBJ and queue a full scene. |
| `octane_visualize_surface(expression, name, x_min, x_max, y_min, y_max, steps)` | Build a restricted `z=f(x,y)` surface and queue a full scene. |
| `octane_show_avatar(name)` | Show Hermes' geometric avatar face. |
| `octane_build_concept(prompt)` | Deterministic MVP concept scaffold. |

## Workflow cards for agents

### Card 1: Is the bridge alive?

1. Call `octane_status()`.
2. If `bridge_seen` is false, ask the user to run one of the Lua bridge scripts in Octane X.
3. If queue grows but processed does not, run the one-shot bridge.
4. Record any non-obvious fix with `octane_record_recipe(...)`.

### Card 2: Show a simple object

1. Call `octane_create_test_cube(name="agent_cube", size=1.0)`.
2. In Octane X, run `hermes_bridge_oneshot_v2.lua`.
3. Call `octane_start_render(samples=128)` if needed.
4. Call `octane_save_preview()`.
5. Verify the PNG exists before claiming success.

### Card 3: Visualize data quickly

1. Call `octane_visualize_bars(values=[3, 1, 4, 1, 5], name="pi_digits")`.
2. Run/drain the Lua bridge in Octane X.
3. Save a preview.
4. If the framing/materials are poor, adjust the generator or camera and record the lesson.

### Card 4: Visualize a math surface

1. Call `octane_visualize_surface(expression="sin(r) / max(r, 0.25)", steps=36)`.
2. Drain the queue with the one-shot bridge.
3. Save/inspect preview.
4. Keep expressions restricted to `x`, `y`, `r`, `sin`, `cos`, `tan`, `sqrt`, `log`, `exp`, `pow`, `min`, `max`, `abs`, `pi`, and `e`.

### Card 5: Self-improve after use

After any successful, failed, or surprising run, append a concise recipe:

```text
octane_record_recipe(
  title="One-shot bridge fixed stale viewport after bar chart import",
  outcome="success",
  context="Persistent bridge processed queue but Octane viewport stayed stale.",
  steps=[
    "Queued octane_visualize_bars with five values.",
    "Ran hermes_bridge_oneshot_v2.lua inside Octane X.",
    "Restarted render and saved preview."
  ],
  signals=["queue/ drained", "processed/ gained command files", "preview PNG existed"],
  follow_ups=["Prefer one-shot bridge for multi-command visual scenes"]
)
```

Keep entries small and operational. A future local model should be able to copy the pattern directly.

## Development smoke tests

```bash
cd /Users/craig/octanex-mcp
PYTHONPATH= uv run octanex-mcp --self-test
PYTHONPATH= uv run python -m octanex_mcp.client_smoke
PYTHONPATH= uv run python -m compileall src
hermes mcp test octanex
```

`PYTHONPATH=` avoids accidentally importing packages from Hermes' own runtime venv when developing inside the Hermes desktop terminal.

## More docs

- `docs/agent-quickstart.md` — short examples designed for small/local models.
- `docs/recipe-library.md` — broad example scenes with reusable OBJ files, command metadata, and preview renders.
- `docs/recipe-book.md` — self-improving successes, failures, partials, and pitfalls.
- `docs/canvas-roadmap.md` — visual canvas roadmap.
- `docs/local-model-rich-moa.md` — local visual R&D process.

## Example recipe library

Reusable sample scenes live under `examples/recipes/`. Each recipe directory contains:

- `README.md` — prompt, purpose, steps, and variations;
- `scene.obj` — reusable geometry;
- `scene.json` — camera and MCP command sequence metadata;
- `preview.png` or `photoreal-preview.png` — preview/target render for quick review.

Start with `docs/recipe-library.md` when exploring applications beyond the built-in bars/surface/avatar tools.

Animated examples live under `examples/animations/`. The first example, `orbit-reveal`, includes a GitHub-friendly GIF, MP4, PNG frame sequence, OBJ frame states, and storyboard metadata. The current robust animation pattern is frame-by-frame scene generation plus `ffmpeg` encoding; native Octane timeline control can be added later.

---

## Links

- X / Twitter: [@nobulart](https://x.com/nobulart/)
- Support: [Buy me a coffee](https://buymeacoffee.com/nobulart)
