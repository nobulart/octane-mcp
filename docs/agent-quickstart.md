# Agent Quickstart: OctaneX MCP

This is the short path for local/smaller models. Do not infer missing behavior; use the exact recipes here.

## Mental model

```text
MCP tool -> JSON file in queue/ -> Octane Lua bridge -> Octane scene -> optional PNG preview
```

The MCP server does **not** directly control Octane's GUI. It writes safe command files. Octane executes them only after a Lua bridge script is running inside Octane X.

## First checks

1. If this is a fresh checkout, run `PYTHONPATH= uv run octanex-mcp init` and `PYTHONPATH= uv run octanex-mcp doctor` from the repo.
2. In Octane X, open **Preferences** and set **Scripts path** to the repository's Lua script directory:

```text
/path/to/octane-mcp/octane_lua
```

This must be the folder containing `hermes_bridge_oneshot.generated.lua` and `hermes_bridge_persistent.generated.lua`. If scripts do not appear in Octane X after changing the preference, restart Octane X.
3. Call `octane_status()`.
4. Inspect:
   - `app.app_exists` should be true.
   - `commands.status.bridge_seen` tells whether Lua has written `status.json`.
   - `commands.queue` shows commands waiting for Octane.
   - `commands.validation.ok` should be true before asking Octane to process queued commands.
   - `commands.processed` and `commands.failed` show recent outcomes.
   - `commands.results` shows recent per-command result JSON files written by Lua.
5. If commands are queued but not processed, ask the user to run the generated one-shot bridge from Octane X's Scripts menu or from the path shown by `octanex-mcp doctor`, usually:

```text
/path/to/octane-mcp/octane_lua/hermes_bridge_oneshot.generated.lua
```

## Minimal examples

### Ping

```text
octane_ping(message="hello from a local model")
```

Then run the one-shot Lua bridge and check `octane_status()`.

### Cube

```text
octane_create_test_cube(name="local_model_cube", size=1.0)
octane_set_camera(position=[2.5, -3.0, 2.2], target=[0, 0, 0.4], fov=45)
octane_set_lighting(preset="soft_studio")
octane_start_render(samples=128, width=1280, height=1280)
```

Then run the one-shot Lua bridge.

### Bar chart

```text
octane_visualize_bars(values=[2, 7, 1, 8, 2, 8], name="example_bars")
```

This already queues import, material, bounds-aware camera, lighting, and render restart.

### Math surface

```text
octane_visualize_surface(
  expression="sin(r) / max(r, 0.25)",
  name="ripple_surface",
  x_min=-3,
  x_max=3,
  y_min=-3,
  y_max=3,
  steps=36
)
```

Allowed expression names: `x`, `y`, `r`, `abs`, `min`, `max`, `sin`, `cos`, `tan`, `sqrt`, `log`, `exp`, `pow`, `pi`, `e`.

Generated visual assets return `bounds` metadata. Prefer the visual tools' automatic camera over hand-tuned camera positions unless you need a deliberate top/front/side composition.

### Hermes avatar

```text
octane_show_avatar(name="hermes_avatar_face")
```

## Preview workflow

1. Queue a scene command, such as `octane_visualize_bars(...)`.
2. Run the one-shot Lua bridge in Octane X.
3. Queue preview save:

```text
octane_save_preview(width=1280, height=1280)
```

4. Run the one-shot Lua bridge again.
5. Review the saved preview:

```text
octane_review_preview()
```

6. Verify `ok=true` before claiming success. If the review reports `likely_blank`, `likely_clipped`, or low contrast, fix the scene/framing and save another preview.

Default preview path:

```text
~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/renders/
```

## When something goes wrong

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `bridge_seen=false` | Lua bridge has not run yet | Ask user to run one-shot bridge in Octane X. |
| Queue grows, processed does not | Bridge not draining queue | Run `hermes_bridge_oneshot.generated.lua`. |
| `commands.validation.ok=false` | Invalid queued command JSON | Call `octane_validate_queue()` and fix/requeue invalid commands before running Lua. |
| Processed commands but viewport stale | Persistent bridge is blocking repaint | Use one-shot bridge; status `released` is intentional. |
| Preview command says OK but no file | Octane save signature/render target issue | Check `failed/` payload and `bridge.log`; run `octane_review_preview()`; do not claim preview success. |
| Blank render | Mesh pin may be stale | Re-import geometry and ensure `P_MESH` reconnect happens in import only. |
| `octane_review_preview()` reports clipped/blank | Bad render output or poor framing | Adjust camera/material/lighting, rerender, and re-review before claiming success. |

## Self-improvement rule

After any non-trivial use, add a short recipe so future local models learn:

```text
octane_record_recipe(
  title="Short operational lesson",
  outcome="success",  # success, failure, partial, or pitfall
  context="What was attempted and why.",
  steps=["Concrete step 1", "Concrete step 2"],
  signals=["Evidence that proved the outcome"],
  follow_ups=["What to try next time"]
)
```

Before starting a new visual task, read:

```text
octane_recipe_book(limit_chars=12000)
```

Prefer recipes over improvisation when a recipe matches the task.

## Example scene library

For broader applications, inspect `docs/recipe-library.md` and `examples/recipes/` before inventing a scene from scratch. Each example includes a reusable `scene.obj`, `scene.json`, and `preview.png`.

Good first examples:

- `examples/recipes/data-bars/` for metric comparisons.
- `examples/recipes/math-surface/` for function landscapes.
- `examples/recipes/vector-field/` for flow/dynamics explanations.
- `examples/recipes/geospatial-terrain/` for map/terrain scenes.
- `examples/recipes/architecture-flow/` for system diagrams.

Copy a matching recipe, adjust geometry or camera, then record any useful result with `octane_record_recipe(...)`.
