# 3D KPI Bar Chart

![Preview render](preview.png)

- **Category:** Data visualization
- **Purpose:** Compare a short numeric sequence as spatial bars with a clear baseline and highlight bars above threshold.
- **Starter prompt:** Visualize quarterly or experiment metrics as a 3D bar chart, highlighting unusually high values.

## Files

- `scene.obj` — reusable geometry scene.
- `scene.json` — command sequence and camera metadata for agents.
- `preview.png` — lightweight generated preview for quick review in GitHub/docs.

## MCP tools to use

- `octane_visualize_bars`
- `octane_save_preview`

## Steps

1. Call octane_visualize_bars(values=[4,9,2,7,5,11,3,8], name='kpi_bars').
2. Drain the queue with the one-shot Lua bridge.
3. Save a preview and inspect framing/contrast.

## Variations to explore

- Use negative values to show below-baseline bars.
- Map categories to materials once multi-material assignment is richer.

## Re-render in Octane

1. Import `scene.obj` with `octane_import_geometry(path="examples/recipes/data-bars/scene.obj", name="data-bars")`.
2. Apply camera from `scene.json`.
3. Drain the queue with `octane_lua/hermes_bridge_oneshot_v2.lua`.
4. Save an Octane preview and replace/add it alongside `preview.png` if it teaches a useful lesson.
