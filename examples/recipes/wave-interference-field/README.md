# Wave Interference Field

![Preview render](preview.png)

- **Category:** Math/physics
- **Purpose:** Show constructive and destructive interference from two point sources as a height field with source markers.
- **Starter prompt:** Explain two-source wave interference as a rendered surface with highlighted emitters.

## Files

- `scene.obj` — reusable geometry scene.
- `scene.mtl` — material color/roughness hints matching the OBJ `usemtl` names.
- `scene.json` — command sequence and camera metadata for agents.
- `preview.png` — lightweight generated preview for quick review in GitHub/docs.

## MCP tools to use

- `octane_visualize_surface`
- `octane_import_geometry`
- `octane_save_preview`

## Steps

1. Generate a height field from two damped radial cosine sources.
2. Import the scene and use the camera metadata from scene.json.
3. Save and review a PNG preview; the ripple extrema should remain visible without clipping.

## Variations to explore

- Animate phase offsets as frame sequences.
- Map amplitude sign to separate materials once per-face material assignment is richer.

## Quality checklist

- Preview is non-blank and recognizable at thumbnail size.
- Camera frames the entire subject with clear margins.
- Materials in `scene.obj` match `scene.mtl` and `scene.json`.
- If Octane drops OBJ line primitives, convert paths/arrows to thin cylinders or tubes for final native renders.
- Record any useful native-render success or failure in `docs/recipe-book.md`.

## Re-render in Octane

1. Import `scene.obj` with `octane_import_geometry(path="examples/recipes/wave-interference-field/scene.obj", name="wave-interference-field")`.
2. Apply camera from `scene.json`.
3. Drain the queue with `octane_lua/hermes_bridge_oneshot_v2.lua`.
4. Save an Octane preview and replace/add it alongside `preview.png` if it teaches a useful lesson.
