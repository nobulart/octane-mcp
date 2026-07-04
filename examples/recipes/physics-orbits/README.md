# Orbital Trajectories

![Preview render](preview.png)

- **Category:** Physics/simulation
- **Purpose:** Show several trajectories around a central body to explain orbital state, phase, or simulation snapshots.
- **Starter prompt:** Visualize N-body or orbit paths with current particle positions.

## Files

- `scene.obj` — reusable geometry scene.
- `scene.mtl` — material color/roughness hints matching the OBJ `usemtl` names.
- `scene.json` — command sequence and camera metadata for agents.
- `preview.png` — lightweight generated preview for quick review in GitHub/docs.

## MCP tools to use

- `octane_import_geometry`
- `octane_start_render`

## Steps

1. Generate trajectory polylines from simulation points.
2. Add small bodies at current timestep.
3. Render with strong depth cues.

## Variations to explore

- Use colors for object classes or energy.
- Export a sequence of OBJ frames for animation.

## Quality checklist

- Preview is non-blank and recognizable at thumbnail size.
- Camera frames the entire subject with clear margins.
- Materials in `scene.obj` match `scene.mtl` and `scene.json`.
- If Octane drops OBJ line primitives, convert paths/arrows to thin cylinders or tubes for final native renders.
- Record any useful native-render success or failure in `docs/recipe-book.md`.

## Re-render in Octane

1. Import `scene.obj` with `octane_import_geometry(path="examples/recipes/physics-orbits/scene.obj", name="physics-orbits")`.
2. Apply camera from `scene.json`.
3. Drain the queue with `octane_lua/hermes_bridge_oneshot_v2.lua`.
4. Save an Octane preview and replace/add it alongside `preview.png` if it teaches a useful lesson.
