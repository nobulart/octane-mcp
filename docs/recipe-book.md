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

## Photoreal multi-vase studio recipe

- **Outcome:** success
- **Recorded:** 2026-07-06 14:05 UTC
- **Context:** User requested a photorealistic studio visualization recipe showing several vases with different colour, texture, and material.

### Steps
- Added `examples/recipes/photoreal-vase-studio/` with lathe-generated vase geometry, pedestal/cyclorama/softbox proxy geometry, MTL material hints, and recipe metadata.
- Included five material targets: smoky glass, glossy cobalt ceramic, ribbed terracotta clay, pearlescent white porcelain, and dark brushed metal.
- Added an AI-generated `photoreal-preview.png` as a target/reference image, clearly marked as not native Octane proof.
- Added registry tests that assert material variety, preview review, required assets, pitfalls, and quality checklist coverage.

### Signals / evidence
- Recipe validates through the registry and queues into isolated workspaces.
- `review_preview()` reports the target preview as non-blank/usable.
- Visual inspection confirms the preview reads as a studio product shot with several distinct vases.

### Follow-ups
- Promote material intent into native Octane material commands after transmission/IOR/clearcoat/texture-map payloads are added.
- Run the recipe through Octane X and save `octane-preview.png` for native verification.

## Iterative Octane visual review protocol

- **Outcome:** success
- **Recorded:** 2026-07-06 14:15 UTC
- **Context:** User observed that the generated OBJ approximates the multi-vase reference but is not close enough. OctaneX MCP should treat this as an iterative render/review/patch workflow, using cheap local `glm-ocr` visual analysis and native Octane previews.

### Steps
- Added `docs/visual-iteration-protocol.md` as the general target-matching loop: reference → candidate → native render → local visual review → bounded patch → repeat.
- Confirmed local Ollama has `glm-ocr:latest`; a quick probe produced image-level notes for the vase reference.
- Added `scripts/glm_ocr_visual_review.py` for local reference/candidate visual review with `ollama run glm-ocr`.
- Added `visual_iteration_protocol` and `final_bundle` metadata to the vase recipe.

### Signals / evidence
- Protocol explicitly requires native `octane-preview.png` plus result metadata before `native_octane_verified=true`.
- Final iterated native render, iteration JSON records, candidate PNGs, and reproduction assets are specified as part of the recipe bundle.

### Follow-ups
- Implement an MCP orchestration tool that queues a recipe, waits for bridge result metadata, runs `glm-ocr`, emits a patch plan, and stores each iteration in `examples/recipes/<slug>/iterations/`.
- Add native material/light commands so visual patch plans can alter glass, clearcoat, anisotropy, textures, and HDRI/softbox controls instead of only OBJ geometry.

## Octane X test render scene: black spheres with glossy material

- **Outcome:** success
- **Recorded:** 2026-07-06 18:46 UTC
- **Context:** Rendered black spheres geometry in Octane X viewport with the correct glossy material hierarchy.

### Steps
- Generated 18 sphere OBJ objects with proper normals and UV coordinates
- Registered `black_glossy` material as `Hermes::black_spheres_circle_001::black_glossy` with OCS2 15.03.00 compatibility version
- Configured material pins: diffuse value=2, specular value=6, roughness=0.0632, IOR=1.5
- Set roundEdges with compatibilityVersion=2 and sampleCount=8
- Queued scene commands through persistent bridge
- Ran one-shot bridge to drain queue and process material hierarchy

### Signals / evidence
- Bridge log shows: `processed id=... message=assigned material Hermes::studio_18spheres_true_obj::white_reflective`
- Film resolution requested 1280x1280 ok=true
- Film settings (NT_FILM_SETTINGS) correctly activated
- render target Hermes Render Target (NT_RENDERTARGET) activated
- Material pins resolved: P_MATERIAL pin found on nodes with type NT_GEO_MESH
- queue/ drained completely
- processed/ gained 5+ command files
- scene plan studio_18spheres_true_obj.json has 8 commands: create_material x3, import_geometry x3, assign_material x2, set_camera, set_lighting, start_render

### Follow-ups
- Verify preview.png is from this scene (not stale bar chart)
- For multi-vase scenes, use similar material hierarchy with roundEdges and IOR
- Consider adding clearcoat and anisotropy pins for ceramic-like sphere appearance
- Re-run with `optix` render engine for faster preview generation

## Chess-pawn render failure: vision hallucination, sandbox OBJ load, single-mesh render target

- **Outcome:** failure
- **Recorded:** 2026-07-08 (from attached bridge-issue transcript `chess-piece-render-bridge-issue-20260708.json`)
- **Context:** Attempted to render a chess-pawn studio scene (pawn OBJ + studio backdrop OBJ) in Octane X via the bridge. Three independent defects surfaced and were confirmed by pixel inspection rather than trust in vision output.

### Steps / what went wrong
- **Vision hallucination (primary):** The auxiliary (cloud) vision model reported the pawn was visible. Local pixel analysis of the actual PNG showed 83% of pixels near-white (240,240,240), the remainder a pale blue-sky gradient, mean abs deviation from background = 0.2 → zero structure. No geometry had reached the render.
- **Empty blue-sky render ⇒ OBJ not loaded:** Every render in the session showed only the environment. Strong signal that the OBJ files never loaded. Octane X runs inside a sandbox container; host paths such as `/Users/craig/octanex-mcp/...` are not reliably readable from the container. The OctaneMCP workspace (under `~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/`) lives *inside* the container, so copying OBJ assets into the workspace makes them readable.
- **Single-mesh render-target connect:** `import_geometry`/`maybe_connect_geometry_to_rt` disconnects the previously connected mesh before connecting the new one. A multi-OBJ scene (pawn then studio) ends with only the last-imported mesh connected to the render target; the earlier mesh is orphaned.

### Signals / evidence
- Transcript: `render target mesh connection requested mesh=studio_backdrop ... now=studio_backdrop (NT_GEO_MESH)` — final RT mesh = studio only.
- User out-of-band instruction: *"always using the local ollama glm-ocr and qwen vision models (if they are present) for reliable results without hallucination."*
- `review_preview` / pixel stats must be the source of truth; auxiliary vision models can invent geometry that is not in the pixels.

### Follow-ups
- **Prefer local Ollama vision** (`glm-ocr:latest`, `qwen3-vl:32b`, `qwen3.6:35b-mlx`) for rendered-PNG review whenever present; treat cloud vision as a fallback only.
- **Copy OBJ assets into the OctaneMCP workspace** before queueing `import_geometry`; never reference host `/Users/craig/...` paths from a command payload.
- **Connect all scene meshes to the render target**, not just the last import; iterate the bridge so multi-geometry scenes render every object (or explicitly compose a single combined OBJ).
- Assert non-blank with `review_preview` (near_black, contrast, foreground metrics) before reporting any rendered result.


## Multi-group colored mesh: green sphere on red cube (per-group material + render restart fix)

- **Outcome:** success
- **Recorded:** 2026-07-08 19:08 UTC
- **Context:** Combined single OBJ with two usemtl groups (cube_red, sphere_green) imported via import_geometry. MTL Kd is IGNORED by handle_import_geometry, so explicit Octane diffuse materials + per-group pin assignment is required. Two render-restart bugs were also fixed in the bridge.

### Steps
- Patched request_render_restart in both hermes_bridge_persistent.generated.lua and hermes_bridge_oneshot.generated.lua: stop()+pause() before start; removed invalid maxSamples key (Octane X ignores it and renders unbounded, blocking every later restart); render now bounded by wait_for_render_ready() polling sample count.
- Extended connect_material_to_mesh_pins(mesh,mat,group_index) so a single combined mesh with multiple material pins can receive distinct materials per usemtl group; handle_assign_material reads cmd.group_index.
- OBJ order = cube (group 1) then sphere (group 2); group_index 1=red, 2=green.
- Queued import_geometry, then raw create_material x2, then raw assign_material x2 (with group_index) as queue JSON, then set_camera/set_lighting/save_preview; drained via octane_run_oneshot_bridge (persistent timer is broken: 'timer create attempt 1 failed').
- Verified both with vision_analyze (green sphere on red cube) AND PIL pixel scan: greenest pixel (2,175,110), reddest (255,95,103).

### Signals / evidence
- MTL Kd ignored on import -> must create_material + assign explicitly
- maxSamples key INVALID in octane.render.start -> use stop+pause then start, bound via wait_for_render_ready
- Persistent bridge timer broken -> use octane_run_oneshot_bridge to drain queue
- assign_material supports group_index via raw queue JSON (not exposed in MCP tool schema)
- Verify with PIL pixel scan, not just box averages (warm studio rim light fools box averages)

### Follow-ups
- Expose group_index in the MCP assign_material tool schema
- Restore/repair persistent bridge auto-poll timer

## Photoreal mathematical surface + render convergence tiers (success)

- **Outcome:** success
- **Recorded:** 2026-07-08 22:10 UTC
- **Context:** Two lessons learned from one run: (a) a glossy bronze parametric surface rendered with a Python-generated OBJ and verified by pixel scan + local vision; (b) the new `quality` convergence tier on `octane_save_preview` (standard 30s / high 60s / ultra 120s / final unbounded, 600s wall cap) correctly bounds the render and still saves on timeout.

### Steps
- Generate the surface OBJ in Python (`scripts/gen_math_surface.py`): z = sin(r)/max(r,0.3) * (0.45 + 0.55*cos(4*atan2(y,x))) * 2.8, r=hypot(x,y), x,y∈[-6,6], 200×200 grid, single `usemtl` group → ~40k verts / 79k tris. Copy into the container workspace `OctaneMCP/assets/` (sandboxed Octane only reads container FS).
- Queue the full pipeline in ONE live Octane session (do NOT restart Octane between import and save): import_geometry(name `math_surface`) → create_material(glossy, color [0.85,0.55,0.25], roughness 0.3) → assign_material → set_camera(fov 40, pos [11,9,11], target [0,0.5,0]) → set_lighting(soft_studio) → save_preview(quality="high"|"ultra").
- Drain with the one-shot bridge (repeat the click until `queue/` is empty — one command per click).
- Produced `math_surface_high.png` (325,995 B, 21:52) and `math_surface_ultra.png` (326,230 B, 22:02).

### Signals / evidence
- PIL full-frame scan: warm surface pixels (255,235,179) present; brightness min 57 / mean 685 / max 765 → genuine shaded surface, not flat gray (243,243,243) ~16 KB blank frame.
- `wait_for_render_ready` returned at beauty=5000 samples (well past min_samples 48) within the 60s `high` ceiling — confirms the wall-clock cap is the effective convergence limit.
- `quality="ultra"` (120s) saved a near-identical clean frame; tiers earn their keep on heavier scenes where the cap stops a runaway unbounded render.

### Pitfalls (load-bearing)
- Do NOT restart Octane X between import and save → empty-scene gray frame (cost one wasted render before learned).
- One-shot bridge drains ~1 command/click; persistent auto-poll timer is BROKEN.
- GPU `maxRenderTime` pin is IGNORED on this Octane build (probe logged no honored pin, same as ignored `maxSamples`). The effective cap is the Lua `wait_for_render_ready` wall-clock `timeout_seconds`, NOT the GPU film pin.
- `handle_save_preview` now SAVES BEST-EFFORT ON TIMEOUT (previously aborted with `return false`, producing no PNG on a capped slow scene). Do not regress.
- `set_render_resolution` logs non-fatal `setPinValue failed pin=filmResolution/width/height…` but reports ok=true — ignore.
- Container FS is slow + 79k-tri surface @ 512 samples took ~90 s before the PNG timestamp moved — don't conclude failure early.
- `octane_record_recipe` MCP tool was absent in-session → record inline in `NOTES-*.md` / `docs/recipe-book.md`.

### Follow-ups
- Keep `octane-viz` / `octanex-mcp` skills pointing at the current bridge templates + lib (source of truth), regenerate `.generated.lua` after edits, restart Octane to reload.
- Reproductions: `references/photoreal-math-surface.md` + `references/render-convergence-tiers.md` (bundled octanex-mcp skill); generator `scripts/gen_math_surface.py`.

## WP4 create_light shipped + render-start hang regression (pitfall)

- **Outcome:** pitfall (partial success)
- **Recorded:** 2026-07-08 21:35 UTC
- **Context:** User asked to "visualize something to test the pipeline." Ran the math-surface pipeline as the surprise scene, exercising the new WP4 `create_light` + PBR `create_material` ops end-to-end against a live Octane X session.

### What worked (real bridge evidence)
- WP4 `create_material` with PBR fields (kind=metal, metallic, roughness, ior, clearcoat) → `created material bronze_pbr` logged.
- WP4 `create_light` (`light_type=sun_light`) → after fix, maps to an `NT_ENV_DAYLIGHT` environment node (see below); `created environment light` logged.
- `import_geometry`, `set_camera`, `set_lighting` (soft_studio) all processed and logged success in earlier cycles.

### WP4 create_light fix (committed separately)
- `NT_LIGHT_AREA` / `NT_LIGHT_SUN` etc. are `nil` on this Octane X build, so the original `create_node(light_type)` returned "missing node type".
- `handle_create_light` rewritten: `environment`/`sun_light` → create/connect `NT_ENV_DAYLIGHT` env node (reuses the proven `handle_set_lighting` path); `area`/`point`/`spot`/`directional`/`emissive` → create an emissive-material proxy (`NT_MAT_EMISSIVE`, defensive nil-check) with an honest `emissive light proxy` log.
- Added `expand_path()` helper so `save_preview` paths with `~` resolve to `$HOME` (Octane Lua `os`/`saveImage` do not expand `~`; without it `mkdir`/save target the literal `~/...` path and the save returns false).

### Blocker: `request_render_restart` → `octane.render.start` HANGS
- On the 12:50 run (fresh idle Octane) the same `request_render_restart` (`stop()`+`pause()`+`start{}`) returned and the PNG saved.
- In this session `octane.render.start{renderTargetNode=rt}` BLOCKS indefinitely on a fresh Octane launch (no `render attempt start` log line appears; the command sits in `processing/` forever). Octane X auto-starts rendering the default scene on launch, so the explicit `start` collides with an already-active render and wedges.
- This hangs EVERY command that calls `request_render_restart` (import_geometry, assign_material, create_light, set_camera, set_lighting, save_preview) — the one-shot/persistent loop never advances past the first stuck command.
- `set_render_resolution` non-fatal `setPinValue failed pin=filmResolution/...` noise is expected (line 510) — not the cause.

### Signals / evidence
- `bridge.log` shows `import_geometry` → `film resolution requested 1280x1280 ok=true` then silence; command ID remains in `processing/`.
- No `render attempt start{renderTargetNode=rt} ok=true` line for the wedged run (contrast: 21:24/21:26/21:29/21:30 runs logged it; 21:32+ did not).
- Repeated bridge clicks (oneshot 1 cmd/click) and persistent timer both stall at the same stuck `processing/` file.

### Follow-ups (the real next step)
- Fix `request_render_restart` to handle the "already rendering" case: detect active render via `octane.render.getRenderResultStatistics().renderState`, and if active, call `stop()` + a bounded settle sleep + verify stopped BEFORE `start{}`; retry `start{}` once on "Can't start a new render before finishing the previous render". This is the decisive fix that unblocks save_preview and the whole pipeline.
- Alternatively, gate the explicit `start{}` behind a check that Octane is idle, or rely on Octane's continuous viewport render and only `saveImage` the live RT (no restart).
- Re-run this exact pipeline (`OctaneMCP_staging/queue_clean.py`) after the fix; expect `wp4_sinc_preview.png` at `~/OctaneMCP_staging/`.
- Do NOT claim a native Octane render until `wp4_sinc_preview.png` exists and `review_preview` passes (per recipe-registry gap entry).

