# Render convergence quality tiers (OctaneX MCP)

## What it is
`octane_save_preview` accepts a `quality` preset that sets a wall-clock
convergence ceiling. Defined in `src/octanex_mcp/models.py` as `QUALITY_TIERS`,
resolved in `src/octanex_mcp/server.py` `octane_save_preview`.

| tier     | max_render_time | timeout_seconds | min_samples | samples  |
|----------|-----------------|-----------------|-------------|----------|
| fast     | 6               | 10              | 64          | 500      |
| preview  | 10              | 10              | 16          | 256      |
| standard | 30              | 30              | 24          | 512      |
| high     | 60              | 60              | 48          | 1024     |
| ultra    | 120             | 120             | 96          | 2048     |
| final    | 0 (unlimited)   | 600             | 1024        | 1000000  |

Omitting `quality` resolves to the `fast` creator default. Raw `samples` /
`min_samples` / `timeout_seconds` / `max_render_time` override
the tier when passed explicitly (resolution keeps the explicit value if it
differs from the tool default; otherwise uses the tier value).

## Why (the load-bearing fix)
`handlers.lua` `handle_save_preview` previously returned `false` on timeout
(`if not ready then return false, ready_msg, nil end`), so a capped render on a
slow scene produced **no PNG at all**. Now it logs the timeout and still calls
`saveImage` (best-effort save). Do not regress this.

## CONFIRMED: GPU `maxRenderTime` pin is ignored
`runtime.set_max_render_time` probes `P_MAX_RENDER_TIME`, `maxRenderTime`,
`maxTime`, `maxRenderTimeSeconds`. On this Octane build every candidate returns
falsy — same class as the known-ignored `maxSamples`. The probe logs:

```
max_render_time: no honored pin on this Octane build (maxRenderTime ignored); relying on timeout_seconds wall-clock cap
```

**Effective convergence cap = Lua `wait_for_render_ready` wall-clock
`timeout_seconds`**, NOT the GPU film pin. The feature still works because the
render stops at the timeout and the frame is saved. Do not add GPU-pin-based
time caps expecting them to fire.

## Verification points
- `models.QUALITY_TIERS` keys: fast / preview / standard / high / ultra / final (asserted by the
  server import smoke test).
- Live test: `octane_save_preview(quality="high")` on the loaded math-surface
  scene -> PNG `math_surface_high.png` (~326 KB); `wait_for_render_ready`
  returned at beauty=5000 samples within the 60 s ceiling. Vision + full-frame
  pixel scan confirmed a genuine shaded bronze surface (not blank).
- `uv run pytest tests/test_schema.py tests/test_lua_bridge_parity.py
  tests/test_config.py` pass.

## Where to edit
- Tier values: `models.py` `QUALITY_TIERS` + `DEFAULT_QUALITY`.
- Tool signature / resolution: `server.py` `octane_save_preview`.
- Film pin probe: `runtime.lua` `set_max_render_time` + `request_render_restart`.
- Save-on-timeout: `handlers.lua` `handle_save_preview`.
- After editing bridge Lua, regenerate `.generated.lua` (`uv run octanex-mcp
  init`) and restart Octane X; verify the new path actually ran via a unique
  `append_log` line before trusting a real render (a lib/template edit that
  reaches no log output may not be loaded).
