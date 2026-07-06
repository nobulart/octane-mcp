# Document OCR Layout Inspection

![Preview render](preview.png)

- **Category:** Document AI/OCR
- **Purpose:** Represent OCR/document-layout output as raised boxes for text lines, tables, images, and uncertain detections.
- **Starter prompt:** Visualize a document parser result with text regions, table cells, image regions, and a highlighted low-confidence area.

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

1. Normalize page coordinates into a flat document plane.
2. Represent text lines, table grid cells, image blocks, and warnings with distinct materials.
3. Raise low-confidence or conflicting regions so they are visible from the review camera.
4. Record parser confidence/coordinate provenance in scene metadata before native rendering.

## Variations to explore

- Use real OCR bounding boxes from PDFs or screenshots.
- Animate before/after parser corrections.
- Add text labels once the annotation recipe becomes a first-class generator.

## Known pitfalls

- OCR coordinate systems often use top-left origins; normalize axes before generating geometry.
- Thin boxes can z-fight with the page plane; keep raised overlays above the paper surface.
- Too many text boxes can clutter the scene; group or downsample rows for previews.

## Quality checklist

- Preview is non-blank and the central idea is recognizable at thumbnail size.
- Scene imports the local scene.obj path listed in commands[].
- Camera frames the entire subject with margin.
- Materials named in OBJ usemtl statements are documented in scene.mtl and scene.json.
- Native Octane output must be saved as octane-preview.png before claiming native render success.

## Re-render in Octane

1. Load or queue this recipe with `octane_load_recipe("document-ocr-layout")` or `octane_queue_recipe("document-ocr-layout")`.
2. Run the one-shot bridge or an on-demand managed persistent bridge action in Octane X.
3. Save an Octane preview and inspect it with `octane_review_preview` before claiming native success.
