Below is a codebase/documentation review and proposed next-phase roadmap for **Octane MCP**.

I reviewed the public GitHub repository, README, docs, Python MCP server/bridge/visual generators, Lua one-shot/persistent bridge scripts, and recipe-library docs. I could not run the project locally because the execution environment could not resolve GitHub for cloning, so this is a source/documentation review rather than an executed test pass.

## Executive assessment

This is already a strong **V0/V1 agentic visual-canvas prototype**. The core architecture is sensible: Hermes calls a local MCP server, the Python side writes allowlisted JSON commands, and an Octane Lua bridge drains those commands into Octane X. The README explicitly frames the stack as `Hermes MCP tool call -> Python MCP server -> JSON command queue -> Octane Lua bridge -> Octane X viewport/render target`, and it correctly avoids arbitrary Lua execution by using a small allowlisted DSL. ([GitHub][1])

The strongest design choices are:

1. **Safe indirection through JSON commands**, not raw Lua.
2. **Python-first geometry generation**, keeping Lua as the thin Octane integration layer.
3. **Recipe-book learning**, which is important for smaller local models.
4. **One-shot bridge fallback**, which avoids the Octane UI-thread blocking issue documented in the README.
5. **Concrete visual grammar seeds**: bars, surfaces, avatar, concept scaffold, recipe examples.

The main next-phase need is to convert this from a clever working bridge into a **reliable visual operating layer**: stronger schemas, state tracking, auto-framing, material groups, preview validation, reusable scene graphs, and richer scientific/data grammars.

---

## Current architecture: what is solid

The repository is compact and focused. GitHub shows only a small number of commits and a codebase split mainly between Python and Lua, with folders for docs, examples, Octane Lua scripts, scripts, and `src/octanex_mcp`. ([GitHub][1]) The package metadata keeps the runtime dependency surface minimal: the core project requires only `mcp>=1.2.0`, with optional extras for science, fields, and geospatial work. ([GitHub][2])

The README’s “current status” section says the implemented loop includes the stdio MCP server, Hermes config pattern, Octane X sandbox path, ordered JSON queue, `inbox.json` fallback, one-shot and persistent Lua bridges, scene operations, visual tools, and recipe-book tools. ([GitHub][1]) That matches the code: `server.py` exposes MCP tools for status, recipe reading/recording, ping, geometry import, material creation, material assignment, camera, lighting, render start, preview save, concept build, bar visualization, surface visualization, and avatar display. ([GitHub][3])

The Python bridge has a clear allowlist of command operations, including `import_geometry`, `create_material`, `assign_material`, `set_camera`, `set_lighting`, `start_render`, `save_preview`, `save_scene`, `scene_summary`, and `build_concept`. ([GitHub][4]) It writes commands atomically using a temporary file plus `os.replace`, which is the right pattern for file-queue reliability. ([GitHub][4])

The documentation is also unusually agent-aware. The quickstart tells models not to infer missing behavior, explains that the MCP server does not directly control Octane’s GUI, and gives exact recipes for ping, cube, bars, math surface, preview workflow, and troubleshooting. ([GitHub][5])

---

## Key issues and constraints

### 1. User-specific hardcoded paths are still embedded

The README, quickstart, and Lua scripts reference paths under `/Users/craig/...`, including the real Octane X container path and repo path. ([GitHub][1]) That is fine for your own machine, but it blocks broader adoption and makes agent execution brittle.

**Next improvement:** add a generated config file and environment-variable override:

```text
OCTANEX_MCP_WORKSPACE=/Users/<user>/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP
OCTANEX_MCP_REPO=/path/to/octane-mcp
OCTANEX_APP_PATH=/Applications/Octane X.app
```

Then have Python generate a `octane_lua/config.lua` or inject path constants into a copied bridge script.

### 2. Lua JSON parsing is intentionally minimal but fragile

The one-shot bridge parses JSON using pattern matching functions such as `extract_string`, `extract_number`, and `extract_array`. ([GitHub][6]) This works for flat command payloads, but it will become fragile as soon as commands need nested materials, grouped meshes, labels, transforms, animation tracks, or metadata.

**Next improvement:** use a tiny Lua JSON decoder vendored into `octane_lua/vendor/json.lua`, or restrict command files to a formally defined flat schema and generate flattened payloads consistently. Since the project direction includes richer scene grammars, a real decoder is the better path.

### 3. Command schema validation should move earlier

The Python side checks `op` against `ALLOWED_OPS`, but payloads are loosely typed dictionaries. ([GitHub][4]) MCP tool signatures help, but they do not guarantee that all queued command files remain valid, especially when recipes or future generators emit command sequences.

**Next improvement:** add Pydantic or dataclass-based command schemas, ideally still keeping core dependencies light. Since the package currently avoids heavy dependencies, you could do lightweight manual validation first:

```text
CommandEnvelope:
  id: str
  op: Literal[...]
  payload: typed per op
  created_at: ISO UTC
  schema_version: "1.0"
```

Then add `octane_validate_command()` and `octane_validate_queue()` tools.

### 4. One-shot and persistent bridges are diverging

The persistent bridge already reuses existing mesh/material nodes more than the one-shot bridge does. For example, persistent `handle_import_geometry` checks for an existing node by name, while the one-shot version creates a new mesh node each time. ([GitHub][7]) That creates drift between the two bridges.

**Next improvement:** consolidate shared Lua logic into:

```text
octane_lua/lib/fs.lua
octane_lua/lib/status.lua
octane_lua/lib/json.lua
octane_lua/lib/octane_scene.lua
octane_lua/lib/command_handlers.lua
hermes_bridge_oneshot.lua
hermes_bridge_persistent.lua
```

The one-shot and persistent scripts should differ only in scheduling/UI behavior, not command semantics.

### 5. Preview verification exists, but not full visual QA

The docs correctly insist that agents verify the PNG exists before claiming success. ([GitHub][1]) The Lua `save_preview` handler also tries multiple Octane save signatures and checks file existence. ([GitHub][6]) That is good, but existence is not enough. The next phase needs image-level QA: blank frame detection, clipping detection, render-black detection, object-in-frame checks, and maybe histogram/edge-density heuristics before vision review.

**Next improvement:** add a Python-side `octane_review_preview(path)` helper that reports:

```text
exists
file size
dimensions
mean brightness
contrast
near-black percentage
near-white percentage
edge density
likely blank/clipped flag
```

That will make the render-review loop much more autonomous.

---

## Highest-value next phase enhancements

### Phase 1 — Reliability and portability

This should come before adding lots of new scene types.

**1. Config abstraction**

Replace hardcoded user paths with a resolved workspace/config layer.

Deliverables:

```text
octanex_mcp/config.py
octanex_mcp init
octanex_mcp doctor
octane_lua/hermes_bridge.generated.lua
```

The `doctor` command should check Octane app existence, sandbox path, queue folders, write permissions, bridge status, and preview-save capability.

**2. Formal command schema**

Add schema versioning and payload validation.

Each command should have:

```json
{
  "schema_version": "1.0",
  "id": "...",
  "op": "import_geometry",
  "payload": {},
  "created_at": "...",
  "source": "octanex-mcp"
}
```

Also add a `capabilities` command so the Lua bridge can report which Octane constants/API calls are available.

**3. Queue transaction model**

Current queue/processed/failed folders are a good base. ([GitHub][1]) Add:

```text
processing/
results/
artifacts/
```

Each processed command should write a result JSON containing `success`, `message`, `duration_ms`, `output_paths`, and `octane_node_names`.

**4. Bridge code deduplication**

Unify command handlers between one-shot and persistent scripts. This matters because agent behavior should not change depending on which bridge is running.

---

### Phase 2 — Scene graph grammar

The current visual generators write OBJ assets and then queue import/material/camera/render commands. The roadmap already identifies geometry, data, math, scientific/physics, and avatar grammars as planned visual layers. ([GitHub][8])

The next abstraction should be a **scene plan** object:

```json
{
  "scene_id": "terrain_markers_001",
  "units": "arbitrary",
  "objects": [
    {
      "id": "surface",
      "type": "mesh",
      "path": "...",
      "material": "terrain_mat"
    }
  ],
  "materials": [],
  "camera": {},
  "lighting": {},
  "render": {}
}
```

Then expose:

```text
octane_build_scene(scene_plan)
octane_replace_object(scene_id, object_id, new_asset)
octane_update_camera(scene_id, camera)
octane_save_scene_manifest(scene_id)
```

This will allow stable object IDs, replaceable assets, animation state updates, and systematic review.

---

### Phase 3 — Auto-framing and bounds-aware rendering

The docs already identify auto-framing from generated asset bounds as a best practice and near-term priority. ([GitHub][8]) This should be implemented immediately because it improves every visual output.

Add bounds metadata to every generated asset:

```json
{
  "path": "...",
  "name": "...",
  "bounds": {
    "min": [-1, -1, 0],
    "max": [1, 1, 2],
    "center": [0, 0, 1],
    "radius": 2.3
  }
}
```

Then add:

```text
camera_for_bounds(bounds, view="iso", margin=1.25)
```

This will remove a lot of manual camera tuning and make local model outputs more reliable.

---

### Phase 4 — Rich data/science visual grammars

The current repo has bar charts and math surfaces, while the recipe library already sketches vector fields, network graphs, terrain, orbits, architecture flow, avatar guide, product studio, Earth, and Saturn examples. ([GitHub][9])

The next high-value additions are:

**Data grammar**

```text
octane_visualize_scatter(points, labels=None)
octane_visualize_timeline(events)
octane_visualize_network(nodes, edges)
octane_visualize_heatmap(grid)
octane_visualize_table_as_scene(rows, columns)
```

**Math grammar**

```text
octane_visualize_vector_field(fx, fy, bounds, density)
octane_visualize_parametric_curve(x(t), y(t), z(t))
octane_visualize_implicit_surface(expression)
octane_visualize_phase_portrait(system)
```

**Geospatial/science grammar**

```text
octane_visualize_geojson(path, height_field=None)
octane_visualize_dem_tile(dem_path, exaggeration)
octane_visualize_trajectory(states)
octane_visualize_particles(points, scalar=None)
```

This aligns directly with the documented roadmap for points/vectors/rays, chart grammars, vector fields, trajectories, N-body snapshots, and GeoJSON/KML-derived meshes. ([GitHub][8])

---

### Phase 5 — Material system and labels

Right now material creation and assignment are useful but still basic. The roadmap explicitly calls out multi-material pin assignment by material group name as a near-term priority. ([GitHub][8]) The Lua bridge currently tries to connect materials to all material-looking mesh pins and common fallback pin names. ([GitHub][6])

Next improvements:

```text
OBJ/MTL material groups preserved by name
semantic material registry
per-object material overrides
legend/callout materials
emission materials for labels/markers
```

For labels, avoid relying on Octane text first. Start with generated mesh text or simple billboard planes, then later add native text nodes if Octane’s Lua API supports them reliably.

---

## Documentation improvements

The docs are already practical. The missing piece is a sharper separation between **user install docs**, **agent operation docs**, and **developer architecture docs**.

Suggested doc structure:

```text
README.md
docs/install.md
docs/hermes-config.md
docs/octane-bridge.md
docs/command-schema.md
docs/agent-quickstart.md
docs/visual-grammar.md
docs/troubleshooting.md
docs/recipe-library.md
docs/roadmap.md
```

The current quickstart is good for agents because it includes exact workflows and troubleshooting. ([GitHub][5]) The recipe-library doc is also valuable because it provides copyable scene patterns and explicitly distinguishes small deterministic previews from native Octane success. ([GitHub][9]) I would keep that distinction prominent.

Add two more docs:

**`docs/security-model.md`**

Explain:

```text
No arbitrary Lua execution
Allowlisted commands only
Local filesystem queue
Sandbox path limitations
No network service required
Known trust boundary: local agent can write commands
```

**`docs/command-lifecycle.md`**

Show:

```text
queued -> processing -> processed/failed -> result JSON -> preview/artifact
```

---

## Testing and CI recommendations

The README lists manual smoke tests: `octanex-mcp --self-test`, `client_smoke`, `compileall`, and `hermes mcp test octanex`. ([GitHub][1]) That is enough for V0, but next phase needs automated checks.

Add:

```text
tests/test_command_schema.py
tests/test_workspace_paths.py
tests/test_obj_generation.py
tests/test_surface_expression_safety.py
tests/test_queue_atomicity.py
tests/test_recipe_book.py
tests/test_scene_plan.py
```

Also add GitHub Actions:

```yaml
python -m compileall src
pytest
ruff check
```

Since this project is Mac/Octane-specific, CI cannot test Octane integration fully, but it can test all Python-side generation and command validity.

---

## Specific code-level enhancements

### Python side

1. Add `config.py` for path resolution.
2. Add `schema.py` for command envelope and payload validation.
3. Add `scene.py` for scene plans and bounds.
4. Add `review.py` for PNG/file-level preview checks.
5. Split `visuals.py` into modules as it grows:

```text
visuals/primitives.py
visuals/charts.py
visuals/math.py
visuals/graphs.py
visuals/geospatial.py
visuals/avatar.py
```

6. Replace raw `eval` surface evaluation with AST validation. The current expression evaluator uses `eval` with disabled builtins and an allowlist. ([GitHub][10]) That is acceptable for local MVP use, but AST validation would be more robust and easier to explain in the security model.

### Lua side

1. Vendor or implement proper JSON decoding.
2. Split common handlers out of one-shot and persistent bridge.
3. Add result JSON per command.
4. Add `scene_summary` implementation, not just an allowlisted op.
5. Add bridge capability introspection.
6. Add node cleanup / replace-by-name behavior consistently.
7. Add stable namespace convention, for example:

```text
Hermes::<scene_id>::<object_id>
Hermes::<scene_id>::Camera
Hermes::<scene_id>::Environment
```

---

## Recommended near-term build order

I would do the next phase in this order:

1. **Config + doctor command**
   Make it portable and diagnosable.

2. **Command schema + result files**
   Make every command auditable.

3. **Lua bridge refactor**
   Remove semantic drift between one-shot and persistent modes.

4. **Asset bounds + auto-camera**
   Improve every render immediately.

5. **Preview QA helper**
   Let agents detect blank/clipped renders before claiming success.

6. **Scene plan abstraction**
   Prepare for complex reusable scenes.

7. **Data/math/graph/geospatial visual grammars**
   Add richer capabilities on top of the stable base.

8. **Animation command layer**
   The docs currently describe frame-by-frame OBJ states plus `ffmpeg` as the reliable pattern, with native Octane timeline control left for later. ([GitHub][9]) Keep that for now, but formalize it as `octane_render_sequence()`.

---

## Strategic direction

The best framing for the project is not “control Octane from an LLM.” It is:

**A local agentic visual operating layer for turning reasoning into inspectable rendered state.**

That means the next phase should optimize for:

```text
semantic scene plans
stable object identity
safe command execution
fast preview loops
visual self-correction
recipe accumulation
scientific/data grammar expansion
```

The repo already has the correct conceptual spine. The main work now is engineering hardening: schema, portability, state, diagnostics, and preview-review automation. Once those are in place, the visual grammar can expand quickly without the system becoming brittle.

[1]: https://github.com/nobulart/octane-mcp "GitHub - nobulart/octane-mcp: Octane MCP for Hermes · GitHub"
[2]: https://github.com/nobulart/octane-mcp/blob/main/pyproject.toml "octane-mcp/pyproject.toml at main · nobulart/octane-mcp · GitHub"
[3]: https://raw.githubusercontent.com/nobulart/octane-mcp/main/src/octanex_mcp/server.py "raw.githubusercontent.com"
[4]: https://raw.githubusercontent.com/nobulart/octane-mcp/main/src/octanex_mcp/bridge.py "raw.githubusercontent.com"
[5]: https://raw.githubusercontent.com/nobulart/octane-mcp/main/docs/agent-quickstart.md "raw.githubusercontent.com"
[6]: https://raw.githubusercontent.com/nobulart/octane-mcp/main/octane_lua/hermes_bridge_oneshot_v2.lua "raw.githubusercontent.com"
[7]: https://raw.githubusercontent.com/nobulart/octane-mcp/main/octane_lua/hermes_bridge_persistent_v1.lua "raw.githubusercontent.com"
[8]: https://raw.githubusercontent.com/nobulart/octane-mcp/main/docs/canvas-roadmap.md "raw.githubusercontent.com"
[9]: https://raw.githubusercontent.com/nobulart/octane-mcp/main/docs/recipe-library.md "raw.githubusercontent.com"
[10]: https://raw.githubusercontent.com/nobulart/octane-mcp/main/src/octanex_mcp/visuals.py "raw.githubusercontent.com"
