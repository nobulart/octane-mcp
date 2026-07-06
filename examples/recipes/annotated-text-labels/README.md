# Annotated Text Labels

![Preview render](preview.png)

- **Category:** Annotation/text rendering
- **Purpose:** Demonstrate labels, backing plates, and callouts as generated OBJ geometry rather than native Octane text nodes.
- **Starter prompt:** Render an explanatory scene with readable AGENT, QUEUE, and RENDER labels attached to geometry.

## Files

- `scene.obj` — reusable geometry scene.
- `scene.mtl` — material color/roughness hints matching the OBJ `usemtl` names.
- `scene.json` — command sequence, camera metadata, pitfalls, and validation checklist.
- `preview.png` — lightweight generated preview for quick review in GitHub/docs.

## MCP tools to use

- `octane_load_recipe`
- `octane_queue_recipe`
- `octane_import_geometry`
- `octane_review_preview`

## Steps

1. Generate label strokes as small boxes so they survive OBJ import.
2. Place dark backing plates behind bright text for contrast.
3. Attach labels to scene objects with small baseline/callout geometry.
4. Review preview metrics and visually inspect label readability before native success claims.

## Variations to explore

- Use labels for graph nodes, architecture diagrams, data callouts, and warning badges.
- Replace block letters with font-outline meshes under a future optional text/font extra.
- Billboard labels toward camera once scene transform support matures.

## Known pitfalls

- Small text can become unreadable at thumbnail size; use backing plates and short words.
- Native Octane text nodes are not part of the current command DSL, so this recipe uses mesh geometry.
- Avoid OBJ line-only glyphs; use boxes/tubes so labels survive import.

## Quality checklist

- Preview is non-blank and the central idea is recognizable at thumbnail size.
- Scene imports the local scene.obj path listed in commands[].
- Camera frames the entire subject with margin.
- Materials named in OBJ usemtl statements are documented in scene.mtl and scene.json.
- Native Octane output must be saved as octane-preview.png before claiming native render success.

## Re-render in Octane

1. Load or queue this recipe with `octane_load_recipe("annotated-text-labels")` or `octane_queue_recipe("annotated-text-labels")`.
2. Run the one-shot bridge or an on-demand managed persistent bridge action in Octane X.
3. Save an Octane preview and inspect it with `octane_review_preview` before claiming native success.
