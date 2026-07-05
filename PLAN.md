I reviewed the current repo state and used Grok’s review as the strategic prompt. The repo has already implemented several of Grok’s “quick wins,” so the plan below focuses on the next useful phase rather than re-listing completed work. 

# OctaneX MCP — Next-Phase Development Plan for Hermes / GPT-5.5 Codex

## Source context

This plan is based on the current `nobulart/octane-mcp` repository plus the attached Grok review. The repo now has a working local MCP server, versioned JSON command queue, one-shot and persistent Octane Lua bridge modes, queue lifecycle directories, preview review, scene manifests, recipe-book tooling, bounds-aware camera placement, and first-pass visual grammars. The README lists the current verified features, including queue validation, processing/result directories, one-shot and persistent bridge support, scene operations, bars/surfaces/avatar/scatter visual tools, bounds metadata, and recipe-book tools.

The attached Grok review correctly identifies the broader trajectory: OctaneX MCP should evolve from a working bridge into a robust agentic visual canvas with stronger schemas, richer visual grammars, visual QA, animation, reusable recipes, and eventually renderer-agnostic abstractions. 

---

# 0. Current baseline

## Already present

* MCP server entry point: `octanex-mcp = "octanex_mcp.server:main"`.
* Lightweight core dependency policy: only `mcp` is required.
* Optional extras already exist for `science`, `fields`, and `geo`: `numpy`, `trimesh`, `networkx`, `scipy`, `shapely`.
* Workspace lifecycle directories: `queue`, `processing`, `processed`, `failed`, `results`, `artifacts`, `assets`, `renders`, `scenes`.
* Atomic command write pattern: temp file then `os.replace` into `queue`, plus `inbox.json` compatibility.
* Shallow versioned command validation in `schema.py`.
* Scene manifest support with namespaced object/material IDs like `Hermes::<scene>::<object>`.
* Preview QA via a stdlib PNG reader with brightness, contrast, near-black, near-white, and edge-density metrics.
* Bounds-aware camera placement for generated visual assets.
* First-class MCP tools for status, validation, queueing, bars, surfaces, scatter plots, avatar face, preview review, scene manifests, and recipe-book read/write.
* Recipe library with data, math, graph, geospatial, physics, architecture, avatar, photoreal product, Earth, Saturn, and animation examples.
* Lua bridge parity tests for one-shot and persistent handler semantics.

## Key remaining constraints

* Command validation is still shallow and hand-written rather than typed per-operation models.
* Lua command parsing still uses regex/string extraction rather than full JSON decoding.
* The bridge scripts still contain duplicated Lua logic, with parity tests acting as the guardrail.
* Scene manifests support mesh objects, materials, camera, lighting, and render settings, but not rich primitive grammars, transforms, grouping, annotations, timelines, or incremental scene patches.
* Preview QA can detect blank/clipped/low-contrast PNGs, but it does not yet provide corrective recommendations, composition checks, object visibility estimates, or multi-preview comparisons.
* Animation is currently frame-sequence based; native Octane timeline controls are not exposed.

---

# 1. Development objective

Move OctaneX MCP from a working beta bridge into a reliable agentic rendering workbench.

The next phase should optimize for:

1. **Reliability** — commands validate before queueing, bridge failures are diagnosable, and agents can trust lifecycle/result metadata.
2. **Composable scene grammar** — agents should emit semantic scene plans, not only isolated low-level commands.
3. **Closed-loop visual iteration** — render, review, diagnose, patch, re-render.
4. **Recipe promotion** — successful recipe patterns should become first-class tools.
5. **Domain expansion without core bloat** — keep the base install lean while enabling science, geo, graph, and animation extras.

---

# 2. Recommended phase structure

## Phase 1 — Hardening and typed command contracts

### Goal

Replace shallow ad hoc command validation with durable typed contracts while preserving the current JSON queue format.

### Tasks

1. Add `src/octanex_mcp/models.py`.
2. Use Pydantic if acceptable, or dataclass-based typed validators if core dependency strictness must remain unchanged.
3. Define typed envelopes:

   * `CommandEnvelope`
   * `CommandResult`
   * `SceneManifest`
   * `AssetMetadata`
   * `PreviewReview`
4. Define typed payloads:

   * `PingPayload`
   * `ImportGeometryPayload`
   * `CreateMaterialPayload`
   * `AssignMaterialPayload`
   * `SetCameraPayload`
   * `SetLightingPayload`
   * `StartRenderPayload`
   * `SavePreviewPayload`
   * `SceneSummaryPayload`
   * `BuildConceptPayload`
5. Keep `schema_version = "1.0"` for compatibility, but introduce an internal `COMMAND_SCHEMA_REVISION`.
6. Make `validate_command()` delegate to typed validators.
7. Add strict range checks:

   * `samples > 0`
   * `width` / `height` within safe limits
   * `fov` between 5 and 120
   * color arrays length 3 or 4, values 0–1
   * material roughness/metallic 0–1
   * path must be absolute or workspace-relative, no `..` traversal for generated assets
8. Add `octane_schema()` MCP tool returning the supported command schema, operation list, and examples.
9. Update docs and tests.

### Acceptance criteria

* Existing tests pass.
* New tests reject malformed payloads that currently pass shallow validation.
* `octane_validate_command()` returns stable structured error codes, not only prose.
* `octane_schema()` gives Hermes/Codex enough information to synthesize valid commands without reading source.

---

## Phase 2 — Lua JSON robustness and bridge runtime extraction

### Goal

Make the Octane bridge less brittle by replacing regex parsing and reducing duplicated Lua logic.

### Current issue

The one-shot bridge currently extracts command fields with regex helpers such as `extract_string`, `extract_number`, and `extract_array`, then builds a partial command table. This is workable for the current limited payloads, but it will become fragile as scene manifests, arrays, nested objects, transforms, material maps, and animation commands grow.

### Tasks

1. Add `octane_lua/lib/json.lua`.

   * Prefer a small self-contained permissively licensed Lua JSON decoder.
   * Vendor it clearly with license header.
   * Avoid network/runtime dependencies.
2. Add `octane_lua/lib/runtime.lua`.

   * File helpers.
   * Status/result writers.
   * Queue lifecycle functions.
   * Command validation helpers.
3. Add `octane_lua/lib/handlers.lua`.

   * Shared implementations of import/material/camera/lighting/render/preview handlers.
4. Keep `hermes_bridge_oneshot_v2.lua` and `hermes_bridge_persistent_v1.lua` as runnable entrypoints.
5. Generated bridge scripts should inline or load shared libs safely from the configured `octane_lua/lib` path.
6. Preserve parity tests, but change them to assert shared handler import/use rather than large duplicated function bodies.
7. Add bridge smoke-test fixtures:

   * valid ping
   * invalid op
   * invalid JSON
   * import geometry command
   * save preview command
   * nested payload command

### Acceptance criteria

* One-shot and persistent bridges still process the same command files.
* Full JSON payloads survive intact into Lua command handlers.
* Parity tests pass.
* Invalid JSON moves to `failed/` and writes a result file with a clear error.
* Existing generated bridge flow from `octanex-mcp init` still works.

---

## Phase 3 — Scene manifest v2 and incremental editing

### Goal

Turn `octane_build_scene(scene_plan)` into the main agent interface for non-trivial visual work.

### Current baseline

`scene.py` already normalizes a scene plan, namespaces objects/materials, saves a manifest, and queues commands. It currently supports mesh objects, materials, camera, lighting, and render settings.

### Scene manifest v2 fields

Add:

```json
{
  "schema_version": "1.0",
  "scene_manifest_version": "2.0",
  "scene_id": "example",
  "intent": "one sentence visual purpose",
  "units": "arbitrary|meters|kilometers|normalized",
  "objects": [],
  "materials": [],
  "groups": [],
  "annotations": [],
  "camera": {},
  "lighting": {},
  "render": {},
  "quality_targets": {},
  "provenance": {}
}
```

### Object model additions

Support:

* `id`
* `type`
* `name`
* `path`
* `format`
* `material`
* `transform`

  * `translate`
  * `rotate_euler`
  * `scale`
* `visible`
* `semantic_role`
* `bounds`
* `tags`

### New primitive object types

Add Python-side mesh generation for:

* `box`
* `sphere`
* `ellipsoid`
* `cylinder`
* `cone`
* `tube`
* `arrow`
* `polyline_tube`
* `surface`
* `point_cloud`
* `text_label_placeholder`

Keep all primitives compiled to OBJ initially for bridge simplicity.

### Incremental editing tools

Add MCP tools:

* `octane_load_scene_manifest(scene_id)`
* `octane_patch_scene(scene_id, patch)`
* `octane_add_object(scene_id, object_spec)`
* `octane_update_object(scene_id, object_id, changes)`
* `octane_remove_object(scene_id, object_id)`
* `octane_requeue_scene(scene_id)`

Use JSON Patch-style operations or a small explicit patch grammar.

### Acceptance criteria

* A scene can be built, saved, loaded, patched, and requeued.
* Object IDs remain stable across edits.
* Generated assets include manifest-relative paths and bounds.
* Existing `octane_build_scene()` remains backward compatible.
* Recipe examples can be represented as scene manifest v2.

---

## Phase 4 — Visual QA v2 and autonomous correction hints

### Goal

Upgrade `octane_review_preview()` from passive metrics to actionable visual diagnosis.

### Current baseline

`review_preview()` already decodes PNGs and reports blank, clipped, low-contrast, brightness, contrast, near-black/white percentage, and edge density.

### Tasks

1. Add `PreviewDiagnosis` with:

   * `ok`
   * `severity`
   * `issues`
   * `metrics`
   * `likely_causes`
   * `recommended_actions`
2. Add composition checks:

   * blank/near-blank
   * overexposed/underexposed
   * low contrast
   * likely object too small
   * likely object clipped at frame edge
   * excessive empty frame
3. Add optional Pillow-backed mode under an extra:

   * `uv sync --extra vision`
   * keep stdlib fallback.
4. Add multi-preview comparison:

   * `octane_compare_previews(before, after)`
   * report whether the new render improved brightness/contrast/edge density.
5. Add correction helpers:

   * `octane_suggest_camera_fix(preview_review, asset_bounds)`
   * `octane_suggest_lighting_fix(preview_review)`
6. Update workflow cards so Hermes always:

   * queues scene
   * drains bridge
   * saves preview
   * reviews preview
   * applies one correction patch if QA fails
   * records recipe if the correction worked

### Acceptance criteria

* Preview review returns machine-actionable recommendations.
* For a dark render, the tool suggests lighting/exposure/camera actions.
* For a clipped render, it suggests increasing camera distance or margin.
* For a tiny object, it suggests tighter framing.
* Tests include synthetic PNG fixtures.

---

## Phase 5 — Promote recipe patterns into first-class tools

### Goal

Convert the strongest checked-in examples into MCP tools so agents can invoke them directly.

### Current baseline

The recipe library documents copyable scenes, previews, material hints, command metadata, and quality checklists.  The recipe book records operational lessons and follow-ups.

### New tools

Implement:

* `octane_recipe_index()`
* `octane_load_recipe(slug)`
* `octane_queue_recipe(slug, overrides=None)`
* `octane_promote_recipe(slug, tool_name)`
* `octane_visualize_vector_field(...)`
* `octane_visualize_network(...)`
* `octane_visualize_terrain(...)`
* `octane_visualize_orbits(...)`
* `octane_build_product_studio(...)`
* `octane_build_planet_scene(body="earth|saturn", ...)`

### Recipe metadata standard

Each recipe should expose:

```json
{
  "slug": "photoreal-product-studio",
  "title": "Photoreal Product Studio",
  "domain": "photoreal",
  "inputs": {},
  "assets": [],
  "commands": [],
  "quality_checklist": [],
  "known_pitfalls": [],
  "native_octane_verified": false
}
```

### Acceptance criteria

* Hermes can list recipes without reading the filesystem manually.
* Hermes can queue a recipe scene from its slug.
* At least three existing recipes become first-class MCP tools.
* Each promoted tool has tests for asset generation and command validation.

---

## Phase 6 — Data, math, science, and geo grammar expansion

### Goal

Build a practical visual grammar layer while keeping the core package small.

### Keep core stdlib

The base install should continue to support:

* bars
* surfaces
* scatter plots
* primitive meshes
* camera/bounds
* simple recipes

### Add optional extras-backed modules

#### `science`

Use `numpy`, `trimesh`, `networkx`.

Tools:

* `octane_visualize_vector_field(vectors, ...)`
* `octane_visualize_scalar_field(grid, ...)`
* `octane_visualize_point_cloud(points, values=None, ...)`
* `octane_visualize_mesh(vertices, faces, ...)`
* `octane_visualize_network(nodes, edges, ...)`

#### `fields`

Use `scipy`.

Tools:

* `octane_visualize_potential_field(...)`
* `octane_visualize_optimization_landscape(...)`
* `octane_visualize_phase_portrait(...)`

#### `geo`

Use `shapely`.

Tools:

* `octane_visualize_geojson(path_or_geojson, z_field=None, ...)`
* `octane_visualize_terrain_grid(elevation_grid, ...)`
* `octane_visualize_tracks(lines, ...)`
* `octane_visualize_sites(points, labels=None, ...)`

### Acceptance criteria

* Missing optional dependencies fail gracefully with install guidance.
* All generated outputs compile to OBJ plus metadata.
* All new tools return bounds and recommended camera.
* At least one recipe exists per optional domain.

---

## Phase 7 — Materials, lights, and photoreal controls

### Goal

Expose enough Octane material/light control to move beyond simple glossy color assignments.

### Tasks

1. Extend material payload schema:

   * `diffuse`
   * `albedo`
   * `metallic`
   * `roughness`
   * `specular`
   * `transmission`
   * `ior`
   * `emission`
   * `opacity`
   * `texture_path`
   * `normal_path`
2. Add material presets:

   * glass
   * brushed metal
   * matte plastic
   * ceramic
   * water
   * atmosphere shell
   * emissive panel
3. Add light commands:

   * `create_area_light`
   * `create_sun_light`
   * `create_environment`
   * `set_hdr_environment`
4. Add photoreal scene helpers:

   * studio cyclorama
   * softbox rig
   * product pedestal
   * space lighting rig
   * atmosphere shell rig
5. Add preview QA checks specific to photoreal targets:

   * no totally black object silhouettes unless intended
   * highlight clipping under threshold
   * material presence confirmed in manifest

### Acceptance criteria

* Product-studio recipe can be generated through MCP without hand-written MTL reliance.
* Earth/Saturn recipes have explicit material/light intent in commands.
* Bridge result files report material/light creation status.

---

## Phase 8 — Animation DSL

### Goal

Provide a simple animation layer before attempting full native Octane timeline integration.

### Current baseline

The docs describe a reliable frame-sequence animation flow: Python generator to OBJ frames, then PNG/GIF/MP4.

### MVP animation tools

* `octane_create_animation_plan(scene_id, fps, frames, duration)`
* `octane_add_keyframes(scene_id, object_id, keyframes)`
* `octane_generate_frame_sequence(animation_id)`
* `octane_queue_animation_frames(animation_id, frame_range=None)`
* `octane_encode_animation(animation_id, format="mp4|gif")`

### Animation manifest

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

### Acceptance criteria

* Orbit reveal can be regenerated via MCP.
* At least camera orbit and object rotation are supported.
* Generated frame manifests include per-frame scene/object paths.
* Encoding is optional and fails gracefully if `ffmpeg` is unavailable.

---

## Phase 9 — Agent closed-loop workflow

### Goal

Make the project feel like an autonomous visual co-pilot, not just a render bridge.

### New orchestration tool

Add:

`octane_render_review_loop(scene_plan, max_iterations=2, quality_goal=None)`

Workflow:

1. Save scene manifest.
2. Queue scene commands.
3. Ask user/agent to drain one-shot bridge if needed.
4. Queue preview save.
5. Review preview.
6. If QA fails, patch camera/lighting/render settings.
7. Requeue patch.
8. Save final review record.
9. Record recipe entry if useful.

Because the bridge still requires Octane-side execution, the tool should return explicit next actions rather than pretending to complete work that requires the user to run the Lua bridge.

### Result object

```json
{
  "scene_id": "...",
  "iteration": 1,
  "queued": [],
  "required_user_action": "Run hermes_bridge_oneshot.generated.lua inside Octane X",
  "preview_path": "...",
  "review": {},
  "recommended_patch": {},
  "done": false
}
```

### Acceptance criteria

* The loop never claims a render succeeded unless result/preview evidence exists.
* The loop gives precise user actions when Octane-side bridge execution is required.
* Failed previews produce a patch suggestion.
* Successful previews produce a recipe-book-ready summary.

---

# 3. Engineering priorities

## Priority A — Must do next

1. Typed command/result models.
2. Lua JSON parsing.
3. Scene manifest v2 with transforms and primitives.
4. Preview QA v2 with recommendations.
5. Recipe index/load/queue tools.

## Priority B — High leverage

1. Shared Lua runtime extraction.
2. Incremental scene patching.
3. Vector field, network, terrain, and orbit visualizers.
4. Material/light command expansion.
5. Animation frame-sequence toolchain.

## Priority C — Strategic later

1. Native Octane timeline API.
2. Renderer-agnostic backend abstraction.
3. Blender/Houdini/Unreal target backends.
4. Visual memory and semantic retrieval.
5. Multi-agent designer/critic/render workflows.

---

# 4. Suggested implementation order for Codex

## PR 1 — Typed schemas and stricter validation

Files likely touched:

* `src/octanex_mcp/schema.py`
* `src/octanex_mcp/models.py`
* `src/octanex_mcp/server.py`
* `tests/test_schema.py`
* `README.md`

Deliverables:

* Typed command envelope and payload validators.
* Structured validation errors.
* `octane_schema()` MCP tool.
* Backward-compatible queue format.

## PR 2 — Lua JSON decoder and bridge parser replacement

Files likely touched:

* `octane_lua/hermes_bridge_oneshot_v2.lua`
* `octane_lua/hermes_bridge_persistent_v1.lua`
* `octane_lua/lib/json.lua`
* `octane_lua/lib/runtime.lua`
* `tests/test_lua_bridge_parity.py`
* `docs/octane-bridge.md`

Deliverables:

* Replace regex parsing with real JSON decoding.
* Keep bridge entrypoints runnable.
* Preserve result/failed lifecycle.

## PR 3 — Scene manifest v2 and primitives

Files likely touched:

* `src/octanex_mcp/scene.py`
* `src/octanex_mcp/visuals.py`
* `src/octanex_mcp/server.py`
* `tests/test_scene.py`
* `docs/scene-manifest.md`

Deliverables:

* Primitive mesh generation.
* Transform support.
* Groups/annotations.
* Scene patching tools.

## PR 4 — Preview QA v2

Files likely touched:

* `src/octanex_mcp/review.py`
* `src/octanex_mcp/server.py`
* `tests/test_review.py`
* `README.md`

Deliverables:

* Actionable diagnoses.
* Synthetic PNG test fixtures.
* Camera/lighting correction suggestions.

## PR 5 — Recipe registry and promoted tools

Files likely touched:

* `src/octanex_mcp/recipes.py`
* `src/octanex_mcp/server.py`
* `docs/recipe-library.md`
* `examples/recipes/*/scene.json`
* `tests/test_recipes.py`

Deliverables:

* `octane_recipe_index()`
* `octane_load_recipe()`
* `octane_queue_recipe()`
* Promote at least three recipe patterns to MCP tools.

---

# 5. Codex guardrails

When implementing, preserve these invariants:

1. Do not add arbitrary Lua execution.
2. Do not let MCP tools write outside the configured workspace except for the repo-local recipe book/docs when explicitly intended.
3. Keep the base install lightweight.
4. Optional scientific/geospatial dependencies must remain optional.
5. Do not claim native Octane render success unless the bridge produced result metadata and a preview exists.
6. Keep one-shot bridge as the preferred reliable batch path.
7. Every queued command must have a result file or a failed-file record.
8. Every generated visual asset must include bounds metadata.
9. Every high-level tool should return:

   * generated asset paths
   * queued command IDs
   * expected next user/bridge action
   * status/result locations
10. Update recipe-book or docs after any non-obvious bridge behavior is discovered.

---

# 6. Definition of “next phase complete”

The next phase is complete when Hermes/GPT-5.5 Codex can reliably:

1. Ask for a scene in semantic terms.
2. Generate a typed scene manifest.
3. Validate it.
4. Generate assets.
5. Queue the scene.
6. Tell the user exactly which Octane bridge action is required.
7. Read result metadata.
8. Save and review a preview.
9. Suggest a corrective patch if the preview is poor.
10. Requeue the correction.
11. Record the lesson as a reusable recipe.

At that point, OctaneX MCP becomes more than a command queue. It becomes an agent-readable, agent-editable, visually self-improving rendering workspace.
