# Radial Math Surface

![Preview render](preview.png)

- **Category:** Mathematics
- **Purpose:** Render a height field for z = sin(r*2.2)/max(r, 0.45) to explain radial damping and singularity protection.
- **Starter prompt:** Show a damped radial wave surface for a math explanation.

## Files

- `scene.obj` — reusable geometry scene.
- `scene.mtl` — material color/roughness hints matching the OBJ `usemtl` names.
- `scene.json` — command sequence and camera metadata for agents.
- `preview.png` — lightweight generated preview for quick review in GitHub/docs.

## MCP tools to use

- `octane_visualize_surface`
- `octane_save_preview`

## Steps

1. Call octane_visualize_surface(expression='sin(r*2.2) / max(r, 0.45)', steps=32).
2. Use one-shot bridge to drain the generated scene sequence.
3. Inspect whether peaks are clipped; reduce expression amplitude if needed.

## Variations to explore

- Overlay sample points or gradient vectors.
- Use surfaces for loss landscapes or potential fields.

## Quality checklist

- Preview is non-blank and recognizable at thumbnail size.
- Camera frames the entire subject with clear margins.
- Materials in `scene.obj` match `scene.mtl` and `scene.json`.
- If Octane drops OBJ line primitives, convert paths/arrows to thin cylinders or tubes for final native renders.
- Record any useful native-render success or failure in `docs/recipe-book.md`.

## Re-render in Octane

1. Import `scene.obj` with `octane_import_geometry(path="examples/recipes/math-surface/scene.obj", name="math-surface")`.
2. Apply camera from `scene.json`.
3. Drain the queue with `octane_lua/hermes_bridge_oneshot_v2.lua`.
4. Save an Octane preview and replace/add it alongside `preview.png` if it teaches a useful lesson.
