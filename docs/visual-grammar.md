# Visual grammar

OctaneX MCP visual tools generate deterministic OBJ assets first, then queue safe Octane commands to import, shade, frame, light, and render them.

## Asset metadata

Generated assets should include bounds metadata:

```json
{
  "path": "/.../assets/visual_math_surface.obj",
  "name": "visual_math_surface",
  "kind": "surface",
  "bounds": {
    "min": [-3.2, -3.2, -1.6],
    "max": [3.2, 3.2, 1.6],
    "center": [0.0, 0.0, 0.0],
    "radius": 4.8
  }
}
```

Bounds are computed from emitted OBJ vertices, rounded to six decimal places, and travel with the asset dict returned by Python generators.

## Bounds-aware camera

Use `camera_for_bounds(bounds, view="iso", margin=1.35, fov=45.0)` instead of hardcoded camera positions for generated geometry.

Supported view presets:

| View | Use |
| --- | --- |
| `iso` | Default three-quarter view for charts, surfaces, and general scenes. |
| `front` | Face-on view for avatars, panels, labels, and planar arrangements. |
| `top` | Overhead view for maps, heatmaps, vector fields, and diagrams. |
| `side` | Profile view for timelines, trajectories, and layered depth. |

`scene_commands_for_asset()` automatically inserts a bounds-aware `set_camera` command when the asset includes `bounds`.

## Current deterministic generators

- `create_bar_chart_obj()` / `octane_visualize_bars()`
- `create_scatter_obj()` / `octane_visualize_scatter()`
- `create_surface_obj()` / `octane_visualize_surface()`
- `create_avatar_face_obj()` / `octane_show_avatar()`
- `create_simple_obj()` / `octane_create_test_cube()`

When adding new visual grammars, return `bounds` in the generated asset and let `scene_commands_for_asset()` frame it unless the grammar needs a deliberate alternate view.

For reusable multi-object scenes, compile assets into a semantic scene plan and use `octane_build_scene(scene_plan)`. See `docs/scene-plan.md`.
