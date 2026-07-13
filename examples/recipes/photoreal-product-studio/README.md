# Photoreal Product Studio

![Photoreal target preview](photoreal-preview.png)

- **Category:** Photoreal/PBR rendering
- **Purpose:** Demonstrate a high-quality product-rendering target scene with glass, metal, softboxes, pedestal, and a dark cyclorama backdrop.
- **Starter prompt:** Render a premium studio product shot of a translucent cyan glass cube and brushed gold sphere on a matte charcoal pedestal with softbox reflections and shallow depth of field.

## Files

- `scene.obj` — reusable studio product geometry.
- `scene.mtl` — material intent for glass, gold metal, matte pedestal, backdrop, and light panels.
- `scene.json` — camera, lighting, PBR material notes, and MCP command sequence.
- `photoreal-preview.png` — photoreal target/reference image for visual review.

## Important note

`photoreal-preview.png` is a generated target/reference render for teaching and visual direction. It is **not yet a verified native Octane output** from the bridge. Use it as a quality bar, then re-render `scene.obj`/`scene.mtl` in Octane X and add `octane-preview.png` once the native render has been verified.

## MCP tools to use

- `octane_import_geometry`
- `octane_set_camera`
- `octane_set_lighting`
- `octane_start_render`
- `octane_save_preview`

## Steps

1. Import `scene.obj` with `octane_import_geometry(path="examples/recipes/photoreal-product-studio/scene.obj", name="photoreal-product-studio")`.
2. Apply the camera from `scene.json`.
3. Use `soft_studio` lighting, then increase samples for final quality (`512+`).
4. Drain the queue once with `octane_lua/hermes_bridge_oneshot.generated.lua`, then poll `queue/` to zero.
5. Save a native Octane preview and compare it with `photoreal-preview.png`.

## What agents should learn

Photoreal examples need more than geometry:

- material intent: glass/transmission, metalness, roughness, IOR;
- lighting intent: large softboxes and reflected highlights;
- camera intent: product-photo perspective and shallow depth of field;
- validation: do not claim photoreal success until a native render exists and is inspected.

## Quality checklist

- Target/reference image is visibly photoreal and free of text/watermarks.
- Native Octane output must be saved as `octane-preview.png` before claiming native photoreal success.
- Glass cube should read as transmissive/refractive, not opaque cyan plastic.
- Gold sphere should read as metallic with realistic roughness and reflected softboxes.
- Product should remain centered, grounded by contact shadows, and framed with enough negative space for documentation thumbnails.

## Variations to explore

- Replace the cube/sphere with imported product CAD or USD assets.
- Add procedural labels or scale indicators as separate geometry.
- Produce side-by-side `target`, `native Octane`, and `iteration notes` images.
- Add HDRI/environment presets once the bridge supports richer lighting controls.
