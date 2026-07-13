# Hermes Avatar Guide

![Preview render](preview.png)

- **Category:** Agent communication
- **Purpose:** Place a geometric Hermes guide in a scene with a pointer so agents can direct attention visually.
- **Starter prompt:** Render Hermes as a non-human guide pointing at an object or idea.

## Files

- `scene.obj` — reusable geometry scene.
- `scene.mtl` — material color/roughness hints matching the OBJ `usemtl` names.
- `scene.json` — command sequence and camera metadata for agents.
- `preview.png` — lightweight generated preview for quick review in GitHub/docs.

## MCP tools to use

- `octane_show_avatar`
- `octane_import_geometry`

## Steps

1. Call octane_show_avatar for the standard avatar.
2. Add target geometry and pointer/callout blocks.
3. Use color states: cyan helpful, gold insight, amber warning, red error.

## Variations to explore

- Add emotion-state variants.
- Use pointer geometry to highlight data points or errors.

## Quality checklist

- Preview is non-blank and recognizable at thumbnail size.
- Camera frames the entire subject with clear margins.
- Materials in `scene.obj` match `scene.mtl` and `scene.json`.
- If Octane drops OBJ line primitives, convert paths/arrows to thin cylinders or tubes for final native renders.
- Record any useful native-render success or failure in `docs/recipe-book.md`.

## Re-render in Octane

1. Import `scene.obj` with `octane_import_geometry(path="examples/recipes/avatar-guide/scene.obj", name="avatar-guide")`.
2. Apply camera from `scene.json`.
3. Drain the queue once with `octane_lua/hermes_bridge_oneshot.generated.lua`, then poll `queue/` to zero.
4. Save an Octane preview and replace/add it alongside `preview.png` if it teaches a useful lesson.
