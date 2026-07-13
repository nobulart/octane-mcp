# MCP Architecture Flow

![Preview render](preview.png)

- **Category:** Architecture/explanation
- **Purpose:** Turn an architecture diagram into geometry: user, agent, queue, and Octane as spatial blocks connected by flow lines.
- **Starter prompt:** Explain how Hermes MCP commands become Octane scene updates.

## Files

- `scene.obj` — reusable geometry scene.
- `scene.mtl` — material color/roughness hints matching the OBJ `usemtl` names.
- `scene.json` — command sequence and camera metadata for agents.
- `preview.png` — lightweight generated preview for quick review in GitHub/docs.

## MCP tools to use

- `octane_import_geometry`
- `octane_set_camera`

## Steps

1. Use boxes for system components and lines for command flow.
2. Color active or risky steps differently.
3. Add future labels/billboards once text support exists.

## Variations to explore

- Use this as a debugging state diagram.
- Animate command movement by moving small cubes along the flow.

## Quality checklist

- Preview is non-blank and recognizable at thumbnail size.
- Camera frames the entire subject with clear margins.
- Materials in `scene.obj` match `scene.mtl` and `scene.json`.
- If Octane drops OBJ line primitives, convert paths/arrows to thin cylinders or tubes for final native renders.
- Record any useful native-render success or failure in `docs/recipe-book.md`.

## Re-render in Octane

1. Import `scene.obj` with `octane_import_geometry(path="examples/recipes/architecture-flow/scene.obj", name="architecture-flow")`.
2. Apply camera from `scene.json`.
3. Drain the queue once with `octane_lua/hermes_bridge_oneshot.generated.lua`, then poll `queue/` to zero.
4. Save an Octane preview and replace/add it alongside `preview.png` if it teaches a useful lesson.
