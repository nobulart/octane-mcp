# OctaneX MCP Roadmap for Smaller Agent Models

This roadmap is a practical implementation guide for smaller coding models working on `octanex-mcp`. It updates the attached next-phase plan against the current repository state. Several quick wins from the earlier reviews are already implemented, so this file focuses on the next useful work rather than repeating completed tasks.

## Status snapshot (2026-07-08)

**Shipped (previously listed under Priority A — do not redo):**

- **WP1 — Shared Lua runtime/handler extraction.** `octane_lua/lib/runtime.lua` and `octane_lua/lib/handlers.lua` exist and are the documented source of truth; the one-shot/persistent entrypoints route through `handle_command`. Note: the entrypoint scripts still *inline* their own handler copies (the parity test enforces byte-identical inline copies), so `lib/handlers.lua` is currently reference-only. Handler edits must be mirrored into both `hermes_bridge_oneshot_v2.lua` and `hermes_bridge_persistent_v1.lua` and kept identical.
- **WP2 — `octane_patch_scene`.** Implemented in `src/octanex_mcp/scene.py` / `bridge.py`.
- **WP3 — Preview comparison + richer QA.** `compare_previews()` implemented in `src/octanex_mcp/review.py`.
- **WP5 — Render-review orchestration.** `octane_render_review_loop()` implemented in `src/octanex_mcp/server.py` (+ `bridge.py`/`recipes.py`).

**Still open:**

- **WP4 — Native material/light controls.** Done: PBR material fields (`transmission`/`ior`/`opacity`/`clearcoat`/`anisotropy`/`emission`/textures) wired through `create_material` validation + defensive Lua pin-setting; new `create_light` op + `octane_create_light` tool with `area_light`/`sun_light`/`point_light`/`spot_light`/`directional_light`/`environment`/`emissive` types, registered in both bridge dispatch tables and kept parity-identical. Material presets on the Python side remain a follow-up (WP4 task 3).
- **WP6 — Recipe promotion, WP7 — science/geo grammar, WP8 — animation DSL.** Not started.

## How smaller models should use this file

Before changing code:

1. Run `git status --short` and do not overwrite user changes.
2. Read the relevant source and tests listed in the task card.
3. Make one small PR-sized change at a time.
4. Add or update tests in the same PR.
5. Run the exact verification commands in the task card.
6. Do not claim a native Octane render succeeded unless there is both bridge result metadata and an actual preview file produced by Octane.
7. Keep the core install lightweight. New heavy dependencies must be optional extras.

Recommended local verification pattern:

```bash
PYTHONPATH= uv run python -m unittest discover -s tests
PYTHONPATH= uv run python -m compileall src
PYTHONPATH= uv run octanex-mcp doctor --json
```

Use narrower tests during iteration, then run the full test command before reporting done.

---

## Current implementation baseline

The repository already has more than the old review baseline:

- Typed command validation lives in `src/octanex_mcp/models.py` and is delegated through `src/octanex_mcp/schema.py`.
- `octane_schema()` exists and returns operations, examples, limits, and path rules.
- Queue lifecycle directories include `queue`, `processing`, `processed`, `failed`, `results`, `artifacts`, `assets`, `renders`, and `scenes`.
- Commands are written atomically through `write_command()`.
- Lua bridges now include a self-contained JSON decoder and parse full command payloads rather than the earliest regex-only parser.
- Scene manifest v2 defaults exist in `src/octanex_mcp/scene.py`: `intent`, `units`, `groups`, `annotations`, `quality_targets`, and `provenance`.
- Scene editing tools exist for load, add object, update object, remove object, and requeue.
- Primitive scene objects currently compile to OBJ for `box`, `sphere`, `ellipsoid`, and `cylinder`.
- Preview QA exists in `src/octanex_mcp/review.py` with brightness, contrast, near-black/near-white, edge density, foreground bounding-box, diagnosis, and camera/lighting suggestions.
- Recipe registry tools exist in `src/octanex_mcp/recipes.py`: index, load, queue, and validate.
- README documents the MCP tool catalogue and the current bridge workflow.
- Tests cover command schema, scene plans, preview review, recipes, bridge control, bounds camera, scatter grammar, config, and Lua bridge parity.

Important current constraints:

- The shared `lib/runtime.lua`/`lib/handlers.lua` exist as documented source of truth, but the one-shot/persistent entrypoints still *inline* handler copies (parity test enforces byte-identical copies). Lua handler edits must be made in BOTH entrypoints and kept identical, or the parity test fails.
- Scene manifest v2 is present but not yet rich enough for the full desired grammar: no cones, tubes, arrows, polyline tubes, point clouds, text-label placeholders, timelines, or complete patch grammar.
- Material/light payloads remain shallow compared with actual Octane material needs — WP4 is the active fix (PBR fields + light ops).
- Recipe tools can index/load/queue recipes, but recipe promotion into dedicated high-level tools is not complete (WP6).
- Optional science/geo/fields visualizers are mostly still roadmap items (WP7).
- Animation is documented as frame-sequence examples, but there is not yet an MCP animation DSL (WP8).

---

## North-star objective

Make OctaneX MCP an agent-readable, agent-editable visual workbench:

1. An agent describes a scene semantically.
2. The MCP server validates the scene and command contracts.
3. Assets are generated with bounds metadata.
4. Commands are queued safely.
5. The bridge executes only allowlisted actions in Octane X.
6. Result metadata and preview files are checked before success is claimed.
7. Preview QA suggests bounded camera, lighting, render, material, or scene patches.
8. Successful loops become reusable recipes or promoted tools.

---

## Priority order

### Priority A — Do next

1. Extract shared Lua runtime and handlers.
2. Complete scene manifest v2 grammar and add general patching.
3. Add preview comparison and richer QA recommendations.
4. Expand native material/light schema and bridge handling.
5. Turn the render-review loop into an explicit orchestration tool.

### Priority B — High leverage after A

1. Promote common recipes into high-level MCP tools.
2. Add optional science/data/geo visual grammar modules.
3. Add frame-sequence animation tools.
4. Store per-iteration render-review evidence in recipe directories.

### Priority C — Strategic later

1. Native Octane timeline controls.
2. Renderer-agnostic scene backend abstraction.
3. Blender/Houdini/Unreal backends.
4. Visual memory and semantic recipe retrieval.
5. Multi-agent designer/critic/renderer workflows.

---

# Work package 1 — Shared Lua runtime and handler extraction

## Goal

Make one-shot and persistent bridge behavior identical except for scheduling/UI. The current scripts work, but large duplicated Lua blocks make future material, transform, preview, and animation changes error-prone.

## Files to inspect first

- `octane_lua/hermes_bridge_oneshot_v2.lua`
- `octane_lua/hermes_bridge_persistent_v1.lua`
- `octane_lua/lib/json.lua`
- `tests/test_lua_bridge_parity.py`
- `src/octanex_mcp/config.py`
- `docs/octane-bridge.md`

## Tasks

1. Create `octane_lua/lib/runtime.lua`.
   - File read/write helpers.
   - JSON escaping/result writing.
   - Status/heartbeat writing.
   - Queue listing and lifecycle moves: `queue -> processing -> processed|failed`.
   - Logging helper.
2. Create `octane_lua/lib/handlers.lua`.
   - Shared `handle_import_geometry`.
   - Shared `handle_create_material`.
   - Shared `handle_assign_material`.
   - Shared `handle_set_camera`.
   - Shared `handle_set_lighting`.
   - Shared `handle_start_render`.
   - Shared `handle_save_preview`.
   - Shared `handle_command` dispatcher.
3. Keep `hermes_bridge_oneshot_v2.lua` and `hermes_bridge_persistent_v1.lua` as user-facing entrypoints.
4. Generated bridge scripts must still work from Octane X's configured Scripts directory.
5. If Octane cannot reliably `require` repo-local modules, keep generation/inlining support in `octanex-mcp init`, but make the source-of-truth code live in `lib/`.
6. Update parity tests so they assert the two entrypoints use the same handler/runtime source or generated chunks.
7. Add fixtures for:
   - valid ping;
   - invalid op;
   - invalid JSON;
   - nested payload command;
   - `save_preview` command with readiness controls.

## Acceptance criteria

- One-shot and persistent bridge still process the same command files.
- Invalid JSON is moved to `failed/` and produces clear result metadata.
- Handler changes are made in one shared location.
- Existing generated bridge flow from `PYTHONPATH= uv run octanex-mcp init` still works.
- `tests/test_lua_bridge_parity.py` passes.
- Full unittest discovery passes.

## Suggested verification

```bash
PYTHONPATH= uv run python -m unittest tests.test_lua_bridge_parity tests.test_config tests.test_bridge_control
PYTHONPATH= uv run python -m unittest discover -s tests
PYTHONPATH= uv run octanex-mcp init >/tmp/octanex-init.json
PYTHONPATH= uv run octanex-mcp doctor --json >/tmp/octanex-doctor.json
```

---

# Work package 2 — Complete scene manifest v2 and patch grammar

## Goal

Make `octane_build_scene(scene_plan)` the main reliable interface for non-trivial visual work. A smaller model should be able to modify a saved scene without rebuilding everything from scratch.

## Files to inspect first

- `src/octanex_mcp/scene.py`
- `src/octanex_mcp/visuals.py`
- `src/octanex_mcp/server.py`
- `tests/test_scene_plan.py`
- `tests/test_bounds_camera.py`
- `tests/test_scatter_grammar.py`
- `README.md`

## Current state

Implemented:

- Manifest defaults for v2 fields.
- Namespaced object/material IDs.
- Build/save/load/add/update/remove/requeue operations.
- Primitive OBJ generation for `box`, `sphere`, `ellipsoid`, and `cylinder`.
- Transform metadata is passed through to import payloads, but primitive generation currently uses translate/scale only.

Missing or incomplete:

- General `octane_patch_scene(scene_id, patch)` tool.
- JSON Patch-style operations or explicit patch grammar.
- Primitive support for `cone`, `tube`, `arrow`, `polyline_tube`, `surface`, `point_cloud`, and `text_label_placeholder`.
- Rotation application during primitive mesh generation.
- Group/annotation semantics beyond preservation in manifest.
- Stable manifest-relative asset paths.

## Tasks

1. Add an explicit patch grammar.

   Recommended grammar:

   ```json
   {
     "operations": [
       {"op": "add_object", "object": {}},
       {"op": "update_object", "object_id": "box_1", "changes": {}},
       {"op": "remove_object", "object_id": "box_1"},
       {"op": "set_camera", "camera": {}},
       {"op": "set_lighting", "lighting": {}},
       {"op": "set_render", "render": {}},
       {"op": "add_annotation", "annotation": {}},
       {"op": "update_annotation", "annotation_id": "label_1", "changes": {}},
       {"op": "remove_annotation", "annotation_id": "label_1"}
     ]
   }
   ```

2. Implement `patch_scene(scene_id, patch, workspace=Workspace())` in `scene.py`.
3. Expose MCP tool `octane_patch_scene(scene_id, patch)` in `server.py`.
4. Add primitive builders in `visuals.py` for:
   - `cone`;
   - `tube`;
   - `arrow`;
   - `polyline_tube`;
   - `point_cloud`.
5. For `surface`, reuse or adapt existing `create_surface_obj()` behavior so manifest objects can request a surface.
6. For `text_label_placeholder`, create simple block/stroke placeholder geometry and document that true text requires future font/curve support.
7. Add rotation support if simple and bounded. If not, explicitly document that `rotate_euler` is preserved for Octane/native handling but not applied to generated primitive OBJ yet.
8. Save generated asset paths in a consistent manifest-relative form plus a resolved path if needed.

## Acceptance criteria

- A scene can be saved, loaded, patched, and requeued.
- Object IDs remain stable across patches.
- Patch operations fail with clear errors for unknown object/annotation IDs.
- Generated assets include bounds metadata.
- Existing `octane_build_scene()` stays backward compatible.
- Tests cover each new primitive type and the patch grammar.

## Suggested verification

```bash
PYTHONPATH= uv run python -m unittest tests.test_scene_plan tests.test_bounds_camera tests.test_scatter_grammar
PYTHONPATH= uv run python -m unittest discover -s tests
PYTHONPATH= uv run python -m compileall src
```

---

# Work package 3 — Preview QA v2.5: comparison, clipping, and recommended patches

## Goal

Upgrade `octane_review_preview()` from single-image passive diagnosis to an actionable review layer that can guide one bounded correction.

## Files to inspect first

- `src/octanex_mcp/review.py`
- `src/octanex_mcp/server.py`
- `tests/test_preview_review.py`
- `docs/visual-iteration-protocol.md`
- `examples/recipes/*/scene.json`

## Current state

Implemented:

- PNG decoding with stdlib only.
- Brightness, contrast, near-black, near-white, edge density.
- Foreground pixel and foreground bounding-box metrics.
- Diagnosis with likely causes and recommended actions.
- Camera and lighting fix helpers.

Missing or incomplete:

- Multi-preview comparison.
- Explicit clipped-at-frame-edge estimate.
- Excessive empty-frame estimate beyond tiny-object heuristic.
- Optional Pillow-backed mode under an extra.
- Patch outputs shaped exactly for `octane_patch_scene()`.

## Tasks

1. Add `compare_previews(before, after)` in `review.py`.
   - Return `before`, `after`, metric deltas, and `improved: true|false`.
   - Improvement can be simple: fewer severe issues, better non-clipped brightness, adequate contrast, better foreground bbox.
2. Expose MCP tool `octane_compare_previews(before, after)`.
3. Add edge clipping metrics.
   - Estimate foreground pixels within a margin of image edges.
   - Report `foreground_edge_touch_percent` or similar.
   - Add issue `likely object clipped at frame edge` when foreground touches too many edges.
4. Add `excessive empty frame` issue when foreground bbox is very small but contrast/edges show an object exists.
5. Make `suggest_camera_fix()` return a patch compatible with the patch grammar from Work package 2.
6. Make `suggest_lighting_fix()` return a patch compatible with the patch grammar from Work package 2.
7. Optional later: add `[project.optional-dependencies].vision = ["Pillow"]` and use Pillow when installed, but preserve the stdlib fallback.

## Acceptance criteria

- Dark renders suggest lighting/exposure actions.
- Overexposed renders suggest reducing exposure/environment intensity.
- Tiny objects suggest tighter camera framing.
- Clipped objects suggest increasing camera distance or framing margin.
- Before/after comparison reports whether the new render improved.
- Synthetic PNG tests cover the new issues.

## Suggested verification

```bash
PYTHONPATH= uv run python -m unittest tests.test_preview_review
PYTHONPATH= uv run python -m unittest discover -s tests
PYTHONPATH= uv run python -m compileall src
```

---

# Work package 4 — Native material and light controls

## Goal

Move beyond simple glossy colors so product, planet, glass, ceramic, metal, atmosphere, and softbox scenes can be controlled through the MCP schema instead of hidden OBJ/MTL hints.

## Files to inspect first

- `src/octanex_mcp/models.py`
- `src/octanex_mcp/schema.py`
- `src/octanex_mcp/server.py`
- `octane_lua/hermes_bridge_oneshot_v2.lua`
- `octane_lua/hermes_bridge_persistent_v1.lua`
- `tests/test_schema.py`
- `tests/test_lua_bridge_parity.py`
- `examples/recipes/photoreal-product-studio/scene.json`
- `examples/recipes/photoreal-vase-studio/scene.json`
- `examples/recipes/photoreal-earth-space/scene.json`
- `examples/recipes/saturn-moons-space/scene.json`

## Tasks

1. Extend `create_material` payload validation with optional fields:
   - `diffuse` or `albedo` color;
   - `metallic`;
   - `roughness`;
   - `specular`;
   - `transmission`;
   - `ior`;
   - `emission`;
   - `opacity`;
   - `texture_path`;
   - `normal_path`;
   - `clearcoat`;
   - `anisotropy`.
2. Keep backwards compatibility with existing `color` payloads.
3. Add material presets on the Python side:
   - `glass`;
   - `brushed_metal`;
   - `matte_plastic`;
   - `ceramic`;
   - `water`;
   - `atmosphere_shell`;
   - `emissive_panel`.
4. Add light commands to schema and bridge:
   - `create_area_light`;
   - `create_sun_light`;
   - `create_environment`;
   - `set_hdr_environment`.
5. Extend Lua material handler carefully and defensively.
   - If an Octane pin is unavailable, return a warning in result metadata instead of crashing.
   - Do not add arbitrary Lua execution.
6. Make bridge result files report material/light creation status and warnings.
7. Update recipe metadata to use explicit material/light intent where possible.

## Acceptance criteria

- Existing material commands still validate and run.
- New material fields validate ranges and safe paths.
- Product/vase recipes can express glass, ceramic, metal, and softbox intent through command payloads.
- Earth/Saturn recipes can express atmosphere shell and sun/environment lighting intent.
- Lua bridge acknowledges unsupported pins clearly.
- Tests cover schema validation and parity for new ops.

## Suggested verification

```bash
PYTHONPATH= uv run python -m unittest tests.test_schema tests.test_lua_bridge_parity tests.test_recipes
PYTHONPATH= uv run python -m unittest discover -s tests
PYTHONPATH= uv run python -m compileall src
```

---

# Work package 5 — Render-review orchestration tool

## Goal

Create the first explicit closed-loop tool. It should queue work, check available evidence, review previews, and return exact next actions without pretending Octane-side work happened automatically.

## Files to inspect first

- `src/octanex_mcp/server.py`
- `src/octanex_mcp/scene.py`
- `src/octanex_mcp/bridge.py`
- `src/octanex_mcp/bridge_control.py`
- `src/octanex_mcp/review.py`
- `src/octanex_mcp/recipes.py`
- `tests/test_bridge_control.py`
- `tests/test_preview_review.py`
- `docs/visual-iteration-protocol.md`

## Tool to add

```text
octane_render_review_loop(scene_plan, max_iterations=2, quality_goal=None)
```

## Required behavior

The tool should return a state object, not a fake success message:

```json
{
  "scene_id": "...",
  "iteration": 1,
  "queued": [],
  "required_user_action": "Run octane_lua/hermes_bridge_oneshot.generated.lua inside Octane X",
  "preview_path": "...",
  "review": {},
  "recommended_patch": {},
  "done": false,
  "evidence": {
    "result_files": [],
    "preview_exists": false
  }
}
```

## Tasks

1. Save the scene manifest.
2. Queue scene commands.
3. Return bridge action instructions if result metadata does not yet exist.
4. If preview exists, run `review_preview()`.
5. If preview fails QA, include one recommended patch only.
6. If a patch is returned, shape it for `octane_patch_scene()`.
7. Record enough metadata that the next call can continue from the same scene/iteration.
8. Do not block waiting for Octane X unless a separate, explicit bridge-control action is available and has evidence.

## Acceptance criteria

- The loop never claims render success without a result file and preview evidence.
- The loop gives precise next user/bridge action.
- Failed previews produce one bounded patch suggestion.
- Successful previews produce a recipe-book-ready summary.
- Tests simulate missing-preview, failed-preview, and passing-preview states with temporary workspaces.

## Suggested verification

```bash
PYTHONPATH= uv run python -m unittest tests.test_preview_review tests.test_bridge_control
PYTHONPATH= uv run python -m unittest discover -s tests
PYTHONPATH= uv run python -m compileall src
```

---

# Work package 6 — Promote recipe patterns into first-class tools

## Goal

Convert the strongest checked-in examples into direct MCP tools so small models do not need to manually read recipe JSON for common tasks.

## Files to inspect first

- `src/octanex_mcp/recipes.py`
- `src/octanex_mcp/server.py`
- `tests/test_recipes.py`
- `docs/recipe-library.md`
- `examples/recipes/*/scene.json`

## Current state

Implemented:

- `octane_recipe_index()`.
- `octane_load_recipe(slug)`.
- `octane_queue_recipe(slug, overrides=None)`.
- `octane_validate_recipe_library()`.

Missing:

- `octane_promote_recipe(slug, tool_name)` or an explicit promotion workflow.
- Dedicated tools for common recipe classes.

## Tools to add first

Start with these because the recipe library already has examples and tests:

1. `octane_build_product_studio(...)`
2. `octane_build_planet_scene(body="earth|saturn", ...)`
3. `octane_visualize_network(...)`
4. `octane_visualize_terrain(...)`
5. `octane_visualize_vector_field(...)`

## Tasks

1. Build promoted tools as thin wrappers over recipe loading plus typed overrides.
2. Return generated asset paths, queued command IDs, expected bridge action, and preview path.
3. Keep recipe metadata as the source of learning/pitfalls.
4. Add tests that each promoted tool validates commands in an isolated temporary workspace.
5. Update README tool catalogue.

## Acceptance criteria

- Hermes can list recipes without filesystem reading.
- Hermes can queue common recipe families by intent, not only slug.
- At least three existing recipes are wrapped by first-class MCP tools.
- Each promoted tool has tests for asset existence and command validation.

## Suggested verification

```bash
PYTHONPATH= uv run python -m unittest tests.test_recipes
PYTHONPATH= uv run python -m unittest discover -s tests
PYTHONPATH= uv run python -m compileall src
```

---

# Work package 7 — Optional data, math, science, and geo grammars

## Goal

Expand the visual grammar while keeping the base package dependency-light.

## Files to inspect first

- `pyproject.toml`
- `src/octanex_mcp/visuals.py`
- `src/octanex_mcp/server.py`
- `tests/test_scatter_grammar.py`
- `examples/recipes/*/scene.json`

## Dependency policy

Keep base install stdlib plus `mcp`. Use optional extras:

- `science`: `numpy`, `trimesh`, `networkx`
- `fields`: `scipy`
- `geo`: `shapely`
- possible future `vision`: `Pillow`

If an optional dependency is missing, the MCP tool should fail gracefully with exact install guidance, for example:

```text
This tool needs the science extra. Run: uv sync --extra science
```

## Tools to add

Core/stdout-only or stdlib-friendly:

- `octane_visualize_point_cloud(points, values=None, ...)`
- `octane_visualize_polyline_tube(points, radius=...)`
- `octane_visualize_arrows(vectors, ...)`

Science extra:

- `octane_visualize_vector_field(vectors, ...)`
- `octane_visualize_scalar_field(grid, ...)`
- `octane_visualize_mesh(vertices, faces, ...)`
- `octane_visualize_network(nodes, edges, ...)`

Fields extra:

- `octane_visualize_potential_field(...)`
- `octane_visualize_optimization_landscape(...)`
- `octane_visualize_phase_portrait(...)`

Geo extra:

- `octane_visualize_geojson(path_or_geojson, z_field=None, ...)`
- `octane_visualize_terrain_grid(elevation_grid, ...)`
- `octane_visualize_tracks(lines, ...)`
- `octane_visualize_sites(points, labels=None, ...)`

## Acceptance criteria

- Missing extras fail with install guidance, not import tracebacks.
- Generated outputs compile to OBJ plus metadata.
- Every tool returns bounds and recommended camera.
- At least one recipe exists per optional domain.
- Tests cover graceful missing-extra behavior without requiring all extras.

## Suggested verification

```bash
PYTHONPATH= uv run python -m unittest tests.test_scatter_grammar tests.test_bounds_camera
PYTHONPATH= uv run python -m unittest discover -s tests
PYTHONPATH= uv run python -m compileall src
```

If extras are installed:

```bash
PYTHONPATH= uv run --extra science python -m unittest discover -s tests
PYTHONPATH= uv run --extra geo python -m unittest discover -s tests
```

---

# Work package 8 — Animation DSL

## Goal

Add a simple animation layer before attempting native Octane timeline integration.

## Files to inspect first

- `examples/animations/orbit-reveal/`
- `docs/recipe-library.md`
- `src/octanex_mcp/scene.py`
- `src/octanex_mcp/server.py`
- `src/octanex_mcp/visuals.py`
- `tests/`

## MVP tools

- `octane_create_animation_plan(scene_id, fps, frames, duration)`
- `octane_add_keyframes(scene_id, object_id, keyframes)`
- `octane_generate_frame_sequence(animation_id)`
- `octane_queue_animation_frames(animation_id, frame_range=None)`
- `octane_encode_animation(animation_id, format="mp4|gif")`

## Manifest shape

```json
{
  "animation_id": "orbit_reveal",
  "scene_id": "saturn",
  "fps": 24,
  "frames": 120,
  "tracks": [
    {
      "object_id": "camera",
      "property": "position",
      "keyframes": []
    }
  ],
  "outputs": {
    "frames_dir": "...",
    "gif": "...",
    "mp4": "..."
  }
}
```

## Tasks

1. Store animation manifests under `workspace/artifacts/animations/<animation_id>/` or a repo example directory when explicitly generating examples.
2. Support camera orbit and object rotation first.
3. Generate per-frame scene manifests or per-frame OBJ states.
4. Queue frame imports/renders with deterministic command IDs.
5. Use `ffmpeg` only if available. If unavailable, return exact install guidance and leave frames intact.
6. Update docs with the frame-sequence pattern.

## Acceptance criteria

- Orbit reveal can be regenerated via MCP.
- Frame manifests include per-frame scene/object paths.
- Encoding is optional and fails gracefully if `ffmpeg` is unavailable.
- Tests cover manifest creation and frame path generation without requiring Octane X.

## Suggested verification

```bash
PYTHONPATH= uv run python -m unittest discover -s tests
PYTHONPATH= uv run python -m compileall src
```

---

# Cross-cutting guardrails

These apply to every work package:

1. Do not add arbitrary Lua execution.
2. Do not let MCP tools write outside the configured workspace unless explicitly writing repo docs/examples.
3. Preserve `schema_version = "1.0"` for compatibility unless a deliberate migration is implemented.
4. Add internal revisions when needed, such as `COMMAND_SCHEMA_REVISION`.
5. Keep one-shot bridge as the preferred reliable batch path.
6. Every queued command should eventually have a result file or failed-file record.
7. Every generated visual asset should include bounds metadata.
8. High-level tools should return:
   - generated asset paths;
   - queued command IDs;
   - expected next user/bridge action;
   - status/result locations;
   - preview path if known.
9. Do not mark recipes `native_octane_verified=true` unless an inspected native `octane-preview.png` and result metadata are present.
10. Update `docs/recipe-book.md`, `docs/visual-iteration-protocol.md`, or recipe README files after discovering non-obvious bridge behavior.

---

# Suggested PR sequence

## PR 1 — Lua runtime extraction

Focus:

- `octane_lua/lib/runtime.lua`
- `octane_lua/lib/handlers.lua`
- one-shot/persistent bridge entrypoints
- parity tests

Stop when existing bridge behavior is preserved.

## PR 2 — Scene patch grammar and primitives

Focus:

- `patch_scene()`
- `octane_patch_scene()`
- new primitive OBJ generators
- scene tests

Stop when saved scenes can be patched and requeued.

## PR 3 — Preview comparison and patch-shaped suggestions

Focus:

- `compare_previews()`
- clipped/empty-frame metrics
- patch-shaped camera/lighting suggestions
- preview tests

Stop when QA can recommend one bounded correction.

## PR 4 — Material/light schema expansion

Focus:

- extended material validation
- material presets
- light ops
- Lua handler support and warnings
- recipe metadata updates

Stop when recipes can express photoreal intent without relying only on MTL hints.

## PR 5 — Render-review loop

Focus:

- `octane_render_review_loop()`
- evidence checks
- continuation state
- tests with temporary workspaces

Stop when the tool honestly reports whether bridge/user action is required.

## PR 6 — Recipe promotion tools

Focus:

- wrappers for product studio, planet scenes, network, terrain, vector fields
- README tool catalogue updates
- recipe tests

Stop when at least three high-value recipes can be queued by direct tool calls.

## PR 7 — Optional science/geo grammar

Focus:

- missing-extra behavior
- core point cloud/polyline/arrows
- optional domain tools
- one recipe per optional domain

Stop when dependency boundaries are clean and tests pass without extras.

## PR 8 — Animation DSL

Focus:

- animation manifests
- keyframe tracks
- frame sequence generation
- optional encoding

Stop when orbit reveal is reproducible through MCP tooling.

---

# Definition of next-phase complete

The next phase is complete when a smaller model can reliably:

1. Read `octane_schema()` and create a valid command or scene plan.
2. Save a typed scene manifest with stable IDs.
3. Generate OBJ assets with bounds.
4. Queue a scene and report the exact bridge action needed.
5. Detect whether bridge results and preview evidence exist.
6. Review a preview for blank, clipped, dark, tiny, or low-contrast output.
7. Produce one patch-shaped correction.
8. Requeue the correction.
9. Record the final lesson in recipe metadata or the recipe book.
10. Avoid overclaiming native Octane success without evidence.

At that point, OctaneX MCP is no longer just a command queue. It is a reliable local visual workbench that smaller and larger agents can both operate safely.
