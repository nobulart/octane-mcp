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
- Run `/Users/craig/octanex-mcp/octane_lua/hermes_bridge_oneshot_v2.lua` inside Octane X.
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
