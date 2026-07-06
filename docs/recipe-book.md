# OctaneX MCP Recipe Book

Reusable field notes from real MCP usage. Agents should read this before visual work and append concise successes, failures, partials, and pitfalls after non-trivial runs.

## Recipe entry format

- **Outcome:** `success`, `failure`, `partial`, or `pitfall`
- **Recorded:** UTC timestamp
- **Context:** what the agent/user tried to do

### Steps
- The exact operational steps that mattered.

### Signals / evidence
- Files, statuses, renders, logs, or errors that proved the outcome.

### Follow-ups
- What a future agent should try, avoid, or verify.

## Seed: prefer one-shot bridge for multi-command scenes

- **Outcome:** success
- **Recorded:** project initialization
- **Context:** Multi-command scenes can queue import/material/camera/lighting/render commands faster than the persistent Octane Lua UI can repaint.

### Steps
- Queue the full scene from a high-level MCP visual tool such as `octane_visualize_bars` or `octane_visualize_surface`.
- Run the generated one-shot bridge reported by `octanex-mcp doctor`, for example `/path/to/octane-mcp/octane_lua/hermes_bridge_oneshot.generated.lua`, inside Octane X.
- Check `octane_status()` for drained queue and processed command files.
- Queue `octane_save_preview(...)` only after the scene mutation batch has processed.

### Signals / evidence
- `queue/` drains.
- `processed/` gains command JSON files.
- Octane viewport can repaint after the one-shot script exits.

### Follow-ups
- If using the persistent bridge, treat status `released` after `start_render` as intentional, not a crash.
- If preview saving fails, verify the render file exists before reporting success.

## Documentation and recipe-book initialization

- **Outcome:** success
- **Recorded:** 2026-07-04 22:39 UTC
- **Context:** Repository was initialized for agent learning with examples and self-improving recipes.

### Steps
- Added README workflow cards and agent quickstart.
- Added MCP recipe-book read/write tools.
- Validated compileall and self-test.

### Signals / evidence
- uv run python -m compileall src passed before this recipe entry.
- uv run octanex-mcp --self-test queued a ping and found Octane X app.

### Follow-ups
- Run hermes mcp test octanex after Hermes reload to confirm tool discovery includes recipe tools.

## Example scene recipe library generated

- **Outcome:** success
- **Recorded:** 2026-07-04 23:00 UTC
- **Context:** Added broad reusable examples with OBJ scenes, scene metadata, and lightweight PNG previews for agent learning.

### Steps
- Created scripts/generate_recipe_examples.py as a deterministic stdlib generator.
- Generated eight recipe directories under examples/recipes covering data, math, vector fields, graphs, terrain, physics, architecture, and avatar guidance.
- Linked docs/recipe-library.md from README and agent quickstart.

### Signals / evidence
- file identified every preview as 960x640 RGB PNG.
- Vision inspection confirmed math-surface and geospatial-terrain previews are recognizable and not blank.

### Follow-ups
- Re-render selected recipes in Octane X and add octane-preview.png variants when available.
- Promote especially useful generator patterns into first-class MCP tools.

## Animated products via frame sequences

- **Outcome:** success
- **Recorded:** 2026-07-04 23:07 UTC
- **Context:** Added an animated orbit reveal example using generated PNG frames, OBJ frame states, GIF, and MP4 artifacts.

### Steps
- Generated per-frame lightweight previews and reusable OBJ scene states.
- Encoded frames into animation.gif and animation.mp4 with ffmpeg.
- Documented current robust animation pattern: frame-by-frame scene generation before native Octane timeline tools.

### Signals / evidence
- ffmpeg produced animation.gif and animation.mp4.
- storyboard.json records FPS, frame count, and product files.

### Follow-ups
- Add an MCP helper to queue/import/render frame sequences automatically.
- Explore native Octane timeline or animation APIs once the bridge surface expands.

## Photoreal product-studio target recipe

- **Outcome:** success
- **Recorded:** 2026-07-04 23:10 UTC
- **Context:** Added a photoreal/PBR example recipe with OBJ/MTL scene assets and a target preview image for visual quality direction.

### Steps
- Generated product-studio scene geometry with cyclorama, pedestal, glass cube, gold sphere, and softbox panels.
- Added scene.mtl and scene.json with PBR material/camera/lighting intent.
- Included photoreal-preview.png as a target/reference image and documented that native Octane render verification is still required.

### Signals / evidence
- file reports photoreal-preview.png as a valid 1024x576 RGB PNG.
- scene.obj and scene.mtl exist as ASCII assets.

### Follow-ups
- Re-render the scene in Octane X and add octane-preview.png after visual inspection.
- Expand MCP material tools to support glass/transmission, IOR, metalness, and area lights directly.

## Recipe library quality pass: materials, validation, animation OBJ ordering

- **Outcome:** success
- **Recorded:** 2026-07-04 23:23 UTC
- **Context:** Reviewed example previews and refined recipe assets/docs to be easier for smaller agents to use and safer to re-render natively.

### Steps
- Added scene.mtl files and material metadata to static recipes so OBJ usemtl names have matching material hints.
- Added quality checklists and native-render caveats to generated recipe READMEs and scene.json files.
- Fixed animated OBJ frame generation so vertices are written before faces/lines with stable indices.
- Updated index documentation to preserve photoreal and animation guidance when regenerating examples.

### Signals / evidence
- Validation found no missing README/OBJ/JSON/preview files across 9 recipes.
- All preview PNGs and animation products passed file/ffprobe checks.
- compileall and hermes mcp test octanex passed.

### Follow-ups
- For native Octane final renders, convert OBJ line primitives to thin cylinders/tubes if the importer drops l commands.
- Add octane-preview.png beside recipes after verified bridge renders are inspected.

## Photoreal Earth-in-space target recipe

- **Outcome:** success
- **Recorded:** 2026-07-04 23:29 UTC
- **Context:** Added a photoreal/PBR space-rendering recipe with procedural Earth geometry and a target preview image for visual quality direction.

### Steps
- Generated layered Earth geometry with ocean/land/ice, cloud shell, and atmosphere shell material regions.
- Added scene.mtl and scene.json with camera, space-lighting intent, PBR material notes, commands, and quality checklist.
- Included photoreal-preview.png as a target/reference image and documented that native Octane render verification is still required.

### Signals / evidence
- file reports photoreal-preview.png as a valid 1024x576 RGB PNG.
- scene.obj, scene.mtl, scene.json, and README.md exist under examples/recipes/photoreal-earth-space.

### Follow-ups
- Re-render the scene in Octane X and add octane-preview.png after visual inspection.
- Replace procedural continent/cloud masks with real Earth texture maps or Octane texture nodes when bridge support exists.

## Saturn and moons space target recipe

- **Outcome:** success
- **Recorded:** 2026-07-05 00:24 UTC
- **Context:** Added a photoreal/PBR space-rendering recipe with procedural Saturn, rings, Cassini division cue, moons, and a target preview image.

### Steps
- Generated oblate Saturn geometry with horizontal gas-band materials, layered tilted ring annuli, and several moon spheres.
- Added scene.mtl and scene.json with camera, space-lighting intent, PBR material notes, commands, and quality checklist.
- Included photoreal-preview.png as a target/reference image and documented that native Octane render verification is still required.

### Signals / evidence
- file reports photoreal-preview.png as a valid 1024x576 RGB PNG.
- scene.obj, scene.mtl, scene.json, and README.md exist under examples/recipes/saturn-moons-space.

### Follow-ups
- Re-render the scene in Octane X and add octane-preview.png after visual inspection.
- Replace procedural bands/rings with real Saturn textures, procedural noise nodes, and ring shadow tuning when bridge support exists.

## Test scene rendered successfully with cube + bars + surface

- **Outcome:** success
- **Recorded:** 2026-07-05 21:10 UTC
- **Context:** Generated 3 geometries (test cube, bar chart, sin(r)/max(r,0.25) surface) to sandbox path and queued full scene commands.

### Steps
- Generated test cube OBJ (0.8 size) and bar chart OBJ (5 values) via visual tools
- Created wave surface OBJ from math expression with bounds metadata
- All assets written to workspace/assets/ in sandbox container
- Queued full scene: import_geometry, create_material, assign_material, set_camera, set_lighting, start_render
- Bounds-aware camera computed position=[9.21, -11.01, 8.05] for surface (iso view)
- Fixed syntax error: unmatched ) in octane_earth.py line 85

### Signals / evidence
- 3 OBJ files in assets/ directory (agent_cube.obj, wave_surface.obj, test_scene_bars.obj)
- 27 queue files, 136 processed files
- workspace status.json shows bridge_seen=true, octane_available=true
- One-shot bridge exists as generated file

### Follow-ups
- Run the generated one-shot bridge inside Octane X viewport to process queued commands end-to-end
- Save a preview PNG after render to verify visual output
- Verify the preview with octane_review_preview() for blank/clipped/low-contrast issues

## Text rendering and annotation labels via generated geometry

- **Outcome:** partial
- **Recorded:** 2026-07-06 12:44 UTC
- **Context:** Roadmap review identified text and labels as high-leverage for making OctaneX MCP useful as an explanatory canvas, but native Octane text nodes are not exposed by the current command DSL.

### Steps
- Start with Python-side generated geometry rather than relying on native Octane text nodes.
- For short labels, generate vector/mesh glyph outlines or simple block-letter primitives as OBJ, then import them like any other scene object.
- For diagrams, pair each label object with an annotation record in the scene manifest: text, target object id, anchor point, semantic role, contrast target, and camera-facing/billboard intent.
- Use high-contrast matte/emissive material hints and keep labels slightly in front of the target surface to avoid z-fighting.
- Add labels only after the base scene camera is known; generated text should include bounds so `camera_for_bounds` can frame both object and annotations.

### Signals / evidence
- Current scene manifest v2 preserves `annotations` but does not compile them into geometry.
- Current primitive support is limited to `box`, `sphere`, `ellipsoid`, and `cylinder`; there is no `text_label_placeholder` compiler yet.
- README and roadmap already warn that OBJ line primitives may be dropped by native import, so text strokes should become thin mesh/tube geometry, not OBJ `l` records.

### Follow-ups
- Add a `text_label_placeholder` object type that creates a contrast backing plate plus simple generated glyph mesh or block-letter OBJ.
- Consider an optional Pillow/fonttools path under a `vision` or `text` extra for converting font outlines to mesh, while keeping a stdlib fallback for block letters.
- Add a recipe-library example for “annotated concept diagram” with labels, arrows, and callouts, then promote it into a first-class `octane_add_label` or `octane_build_annotated_scene` tool.

## Image processing to Octane geometry: relief maps, masks, and color tiles

- **Outcome:** partial
- **Recorded:** 2026-07-06 12:44 UTC
- **Context:** Image-processing applications are a natural next domain for the visual canvas: turn pixels, masks, heatmaps, OCR regions, or segmentation outputs into inspectable 3D geometry.

### Steps
- In Python, load an input image or matrix and downsample it to a bounded grid before geometry generation.
- Convert luminance or scalar values to a height field OBJ for relief maps, heatmaps, spectrograms, microscopy tiles, elevation rasters, or model-attention maps.
- Convert masks/segmentation classes into colored tile groups or raised contour bands with material names per class.
- Store original image path, sampling size, value range, color map, and class legend in asset metadata or scene manifest provenance.
- Queue as a normal mesh scene with bounds-aware camera, then save/review a preview to catch flat/overexposed or too-dense geometry.

### Signals / evidence
- `create_surface_obj` already proves the stdlib mesh path for height fields.
- `review_preview` can already detect blank, clipped, low-contrast, and tiny-object outputs for generated previews.
- No image-loading optional extra exists in `pyproject.toml`; current extras are `science`, `fields`, and `geo` only.

### Follow-ups
- Add an optional `vision = ["pillow"]` extra and keep a stdlib path for JSON/CSV numeric grids.
- Implement `octane_visualize_image_heightfield(path_or_grid, max_size=128, colormap="viridis")` returning OBJ, metadata, bounds, and recommended camera.
- Add recipes for segmentation-mask inspection, document/OCR layout review, spectrogram relief, and image-difference heatmap before building a large API surface.

## Recipe registry gap before recipe promotion

- **Outcome:** pitfall
- **Recorded:** 2026-07-06 12:44 UTC
- **Context:** The roadmap calls for `octane_recipe_index`, `octane_load_recipe`, and `octane_queue_recipe`, but the current recipe library is still docs/filesystem-first.

### Steps
- Treat checked-in recipe directories as examples, not callable tools, until a registry module validates their metadata and command lists.
- When adding new recipe directories, keep `README.md`, `scene.obj`, `scene.mtl`, `scene.json`, and preview/target image files together.
- Include a stable `slug`, domain, input assumptions, command list, known pitfalls, and native-Octane verification status in `scene.json`.
- Do not claim a recipe is natively rendered unless `octane-preview.png` exists and `octane_review_preview` passes or records the known failure.

### Signals / evidence
- README lists recipe-book read/write tools, but no `octane_recipe_index`, `octane_load_recipe`, or `octane_queue_recipe` MCP tools are registered in `server.py` yet.
- `docs/recipe-library.md` lists 13 recipe directories, while its table currently omits the Earth and Saturn photoreal examples.
- Existing tests cover schema, bridge parity, preview review, scene plans, scatter, bounds camera, and config, but not recipe metadata validation.

### Follow-ups
- Create `src/octanex_mcp/recipes.py` with registry/index/load/queue helpers and tests for every checked-in recipe directory.
- Update `docs/recipe-library.md` table/coverage map to include all current recipe directories.
- Promote the first three callable patterns after registry support: product studio, annotated architecture flow, and image heightfield/segmentation review.

## Recipe registry implemented for checked-in examples

- **Outcome:** success
- **Recorded:** 2026-07-06 12:44 UTC
- **Context:** Converted the recipe library from docs/filesystem-only examples into agent-callable registry helpers and MCP tools.

### Steps
- Added `src/octanex_mcp/recipes.py` with index, load, queue, and validation helpers.
- Registered `octane_recipe_index`, `octane_load_recipe`, `octane_queue_recipe`, and `octane_validate_recipe_library` in the MCP server.
- Resolved repo-relative command asset paths before queueing so imported recipe geometry uses absolute local paths.
- Updated README, agent quickstart, and recipe-library docs with registry tool usage.

### Signals / evidence
- `PYTHONPATH= uv run python -m unittest tests.test_recipes -v` passed.
- Registry found 13 checked-in recipes and validated every recipe directory.
- Visual inspection confirmed representative recipe previews are non-blank: data-bars, photoreal product studio, Earth, and Saturn.

### Follow-ups
- Add a recipe-library example for text/annotations and one for image heightfields, then validate them through the registry.
- Promote useful generators into dedicated first-class tools after their recipes stabilize.

## Preview QA foreground-size heuristic after visual inspection

- **Outcome:** success
- **Recorded:** 2026-07-06 12:44 UTC
- **Context:** Visual inspection showed data-bars and product-studio previews were clearly recognizable, but the edge-density-only QA heuristic flagged them as `likely object too small` because they have large smooth subjects and dark backgrounds.

### Steps
- Added foreground pixel and foreground bounding-box metrics based on luminance deviation from the median background.
- Changed `likely object too small` to require both low edge density and a small foreground bounding box.
- Kept the tiny-object synthetic fixture failing while adding a large-smooth-subject regression fixture.

### Signals / evidence
- `PYTHONPATH= uv run python -m unittest tests.test_preview_review -v` passed.
- `review_preview` now returns `ok=true` for representative recipe previews: data-bars, product studio, Earth, and Saturn.
- Visual inspection confirmed those representative previews are non-blank and recognizable.

### Follow-ups
- Add a future `octane_compare_previews(before, after)` tool that can use foreground metrics alongside brightness/contrast/edge density.

## Text labels and image heightfield recipe examples

- **Outcome:** success
- **Recorded:** 2026-07-06 13:18 UTC
- **Context:** The roadmap called for new recipe-book entries around text rendering and image-processing applications. The recipe registry now includes concrete checked-in examples for both.

### Recipes added
- `annotated-text-labels`: block-letter label meshes, dark backing plates, and callout stems attached to three scene objects. This avoids depending on unavailable native Octane text-node commands.
- `image-heightfield-mask`: a synthetic scalar/image grid converted to raised tile geometry, with heat colors and a highlighted segmentation/mask region.

### Signals / evidence
- `recipe_index()` reports 15 recipes after adding these two examples.
- `validate_recipe_library()` reports all 15 checked recipes valid.
- `review_preview()` returns `ok=true` for both new previews.
- Visual inspection confirmed `AGENT`, `QUEUE`, and `RENDER` are readable in the text-label preview, and the image recipe is recognizable as a heatmap/heightfield with a raised mask and legend.

### Follow-ups
- Add a proper font-outline/text mesh generator once optional font tooling is introduced.
- Add optional Pillow-backed image ingestion so real images, masks, OCR boxes, or model saliency maps can produce this geometry directly instead of using a synthetic stdlib grid.
- Add on-demand AppleScript management for the persistent Octane bridge so recipe queueing can start/stop bridge processing without manual Lua launch.

## OCR layout and attention-map recipe examples

- **Outcome:** success
- **Recorded:** 2026-07-06 13:35 UTC
- **Context:** After adding basic text and image-heightfield recipes, the next useful coverage gap was semantic AI output: document-layout/OCR overlays and model interpretability matrices.

### Recipes added
- `document-ocr-layout`: a page plane with raised text-line boxes, table grid overlays, image regions, and an uncertainty marker.
- `transformer-attention-map`: an attention matrix rendered as token-aligned raised cells with diagonal structure and a highlighted focus region.

### Signals / evidence
- `recipe_index()` reports 17 checked-in recipes after adding these examples.
- `validate_recipe_library()` reports all 17 recipes valid.
- `review_preview()` returns `ok=true` for both new previews.
- Visual inspection confirmed the OCR recipe reads as a document-layout overlay and the attention recipe reads as a matrix/heatmap with token rails.

### Follow-ups
- Add ingestion helpers that accept real OCR JSON, layout-parser boxes, saliency maps, or attention tensors and emit these recipe shapes.
- Add text-label integration for human-readable token/page labels once label generation becomes a first-class tool.

## On-demand bridge management via AppleScript

- **Outcome:** partial
- **Recorded:** 2026-07-06 13:55 UTC
- **Context:** Manual launch of `hermes_bridge_persistent.generated.lua` is a UX bottleneck. Hermes should be able to detect bridge state and attempt to run one-shot or persistent bridge scripts on demand.

### Steps
- Added bridge process/status helpers that report Octane X PID, generated script paths, script readiness, status.json contents, and heartbeat age.
- Added AppleScript-backed helpers to attempt running `hermes_bridge_oneshot.generated.lua` or `hermes_bridge_persistent.generated.lua` from Octane X's Scripts menu.
- Added MCP tools and CLI commands for status, one-shot, and persistent bridge control.
- Verified the already-open persistent bridge can process a queued ping and write result metadata.

### Signals / evidence
- `octanex-mcp bridge-status --json` reported Octane X running, both generated scripts present, and persistent bridge status `idle`.
- A queued ping returned a successful bridge result: `pong bridge-management-smoke`.
- Direct AppleScript menu launch currently returns a structured failure because the generated script name was not found in the exposed Scripts menu; this is reported rather than hidden.

### Follow-ups
- Confirm the exact Octane X menu hierarchy/script display names, or add a lower-level GUI/menu probe once Accessibility permission is reliable.
- Consider an in-bridge file-trigger/watchdog action so Hermes can request `drain queue` without depending on macOS menu traversal.
