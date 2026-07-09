# OctaneX MCP — Work In Progress

Living WIP board. Mirror of `docs/roadmap.md` §Status snapshot + §Development
brainstorm, kept as a fast-glance status doc. Last updated **2026-07-09** (steward run `d1d0e37`).

## Current state (evidence, 2026-07-09 — steward run d1d0e37)

| Area | State |
|------|-------|
| Repo | `main` = `d1d0e37` (HEAD; tree clean at steward start; harness regression-guard commits `a2fccb9`/`d1d0e37` landed since `2fbc567`) |
| Tests | **216 passed / 4 skipped** (offline `python -m unittest discover -s tests`) — green. 1 skip because optional `geo` extra absent. Up from 199 (the `2fbc567` snapshot) — harness commits added tests. |
| Octane X | running (healthy bridge: `status=processed`, `last_event="save_preview … octane-preview.png"`, status age ~20 min). Not wedged. |
| Benchmarks | 18/18 native-Octane verified (Tiers 1–6) — per roadmap §benchmark-suite recorded table; not re-rendered this run |
| Recipe library | **18 recipe dirs, 18 `native_octane_verified=true`, 0 unverified.** `avatar-guide` closed this run via live Octane render (real native PNG, passed pixel QA + vision subject check). |
| Core mechanics | solid: bridge, schema, pixel-QA, render-review loop, scene v2, PBR mats/lights, bounds-camera, recipe registry, **WP7 geo grammar (`geo.py` + `octane_visualize_geojson` tool shipped)**, **WP8 animation model started (`animation.py`)**, **WP9 corpus + iteration loop + `octane_find_grammar` (shipped)**, WP6 promoted tools |
| Unscaffolded | WP7 geo **live-`geo`-extra** path, WP8 **MCP tool + bridge bake** (model only so far), WP6 live end-to-end of promoted tools, Canvas Phase B+ wiring, Studio multi-host, visual memory |

**Bottom line:** reliability + core mechanics are proven. The gap is
*surface area + closure* — ergonomic surface (animation tool/bake, geo live
exercise, canvas UI, autonomous loop) remain the open work. **Recipe library is
now 18/18 `native_octane_verified`** (`avatar-guide` closed 2026-07-09 via live
Octane render). Recipe-count "drift" was a scan artifact (§Recipe library row).

## Backlog (from brainstorm 2026-07-09)

Ranked by effort × strategic fit (reviewer's call — none committed yet):

1. **A — Recipe verification (close the last gap)** (LOW effort / HIGH integrity): 1 unverified recipe remains (`avatar-guide`). Its prior native render was near-black (failed QA); re-render live and, if it passes pixel QA, flip `native_octane_verified=true` + append `docs/recipe-book.md`. *First step:* `verify_recipe_library(live=True, copy_back=True, slug='avatar-guide')` against a running Octane session.
2. **B — Geo / terrain grammar live path** (HIGH strategic fit; **MCP tool SHIPPED**): `octane_visualize_geojson` registers on the MCP server (graceful `GeoDependencyError` → `uv sync --extra geo` hint; tests in `tests/test_geo_tool.py` + `tests/test_geo_grammar.py`). *Remaining:* exercise the shapely-backed path live under a `geo` extra env.
3. **C — Agentic Canvas app** (biggest unbuilt): Phase B wiring — connect `gateway.read_status()` + `/mcp/call` to a live dashboard (intent command bar → `octane_build_concept` / `octane_queue_recipe`; status pill from `render_stage`). Phase A slice (shell + viewport + command bar + `OCTANEX_RENDER_HOST` flag) from `docs/canvas-implementation-roadmap.md`. Swift/JS workstream.
4. **D — Autonomous loop**: bounded 2-iteration `octane_render_review_loop` over one recipe, driven end-to-end.
5. **F2 — Animation tool + bridge bake** (WP8, continuation; HIGH north-star fit, additive): expose the `animation.py` model as an MCP tool (`octane_build_animation`/`octane_queue_animation`) that emits the per-frame `set_camera` bake plan into the bridge queue, and add a Lua-side consumer (requires Octane restart + parity — flag for the user). First slice can reuse `build_bake_plan` + existing `octane_save_preview` per frame, writing zero-padded `frame_*.png`; optional ffmpeg encode via injected encoder (no hard dep).
6. **G — Texture gen**: image-gen → `texture_path` / `normal_path` on materials, closing the "texture approximated with geometry" recipe pitfall.
7. **E — Recipe promotion** (WP6) — **DONE**; first-class tools shipped + tested. Removing from active backlog.

## Recommended next move

**A (close the last honesty gap) → then B live-`geo` path.** `avatar-guide` is the
only remaining `native_octane_verified=false`; a live `verify_recipe_library(live=True,
copy_back=True, slug='avatar-guide')` flips it if the re-render passes pixel QA,
making the library 18/18. The earlier "12/20 / 8 unverified" drift was a scan
artifact (non-recipe dirs counted); truth is 17/18. B's tool is shipped +
offline-green; the shapely live path needs a `uv sync --extra geo` env. C (Canvas)
is a separate Swift/JS workstream. WP8 model shipped this run (F→F2): the next
animation step is the MCP tool + bridge bake.

## In progress / this session

_WP6 promoted-recipe tools shipped (uncommitted, +9 tests). Bridge status `failed` (preview-save) — open item for the user. WP7 geo MCP tool `octane_visualize_geojson` shipped at `b96bf2e`. WP9 iteration loop committed at `b96bf2e`. Recipe-verified count corrected to 13/18 (5 unverified)._

## Done recently

- **WP8 animation DSL — first slice (steward run d1d0e37, uncommitted):** added `src/octanex_mcp/animation.py` (pure stdlib, no heavy deps — ffmpeg stays an external tool, encoder injected). `CameraKeyframe`/`AnimationManifest` model; `sample_camera` (linear interp + hold-clamp), `camera_command` (Octane `set_camera` envelope), `build_bake_plan` (per-frame render schedule), `frame_paths`, `encode_frames` (injected-encoder only), `orbit_manifest` (circular camera orbit as a 25-keyframe polyline arc, not a 2-point chord). New `tests/test_animation.py` (13 tests, all pass). Suite now **216 passed / 4 skipped** (was 199/4 — +13 animation tests; the +4 vs 203 came from the harness commits `a2fccb9`/`d1d0e37`). `compileall` clean; `build_mcp()` boots (44 tools) with no `benchmarks`/`scripts`/`tests` imports added to `animation.py` (§6 layering holds — verified via AST scan + `import octanex_mcp.animation`). No Lua edits, no deps; core install unchanged. Next WP8 step (F2): MCP tool + bridge bake emitting the per-frame camera commands.
- **Stale-test regression fix (steward run 2fbc567, uncommitted):** Phase-1 caught the offline suite RED — `test_recipe_index_lists_checked_in_recipes_with_required_metadata` asserted `data-bars["native_octane_verified"] is False`, but `data-bars` was genuinely promoted to verified by the WP6 honesty work (`c572ace`, real `octane-preview.png` present, confirmed via `_recipe_dirs` ground-truth). Corrected the assertion to `assertTrue(...)` with a provenance comment. Suite restored to **199 passed / 4 skipped** (0 failures). Pure `tests/` change; no library import touched, so §6 server-boot layering is unaffected (`doctor` already confirmed the server path is sound). No Lua edits, no deps.
- **WP6 recipe promotion — first-class tools (steward run 1a17f19, uncommitted):** closed backlog item E. Added three promoted MCP tools in `src/octanex_mcp/server.py` — `octane_build_product_studio` (→ `photoreal-product-studio`), `octane_build_planet_scene` (`planet='earth'`→`photoreal-earth-space`, `'saturn'`→`saturn-moons-space`, unknown falls back to earth), `octane_visualize_network` (→ `network-graph`) — each a thin wrapper over `queue_recipe`. Registered the same three in `gateway.py`'s `DISPATCH` for HTTP Canvas parity. New `tests/test_promoted_recipes.py` (9 tests: registration ×3, slug resolution for earth/saturn/unknown, queue-write, and 2 gateway-parity checks). Suite now **199 passed / 4 skipped** (was 190/4). `compileall` clean; `build_mcp()` boots (44 tools) with no `benchmarks`/`scripts`/`tests` imports added to `server.py`/`gateway.py` (§6 layering holds). No Lua edits, no heavy deps, core install unchanged.
- **WP7 geo grammar — first slice** (steward run c90d84c, uncommitted): added
  `src/octanex_mcp/geo.py` + `tests/test_geo_grammar.py`. Two offline-testable
  ops: `elevation_grid_to_obj` (pure-Python DEM/grid → height-field OBJ, no
  extra) and `geojson_to_obj` (shapely-backed GeoJSON/Polygon/LineString/Point →
  extruded OBJ, gated behind the optional `geo` extra with a `GeoDependencyError`
  + `uv sync --extra geo` hint). Plus `geo_asset_to_scene_commands` (bounds
  camera) so geo assets drop into the render-review pipeline. Suite: **166 passed /
  3 skipped** (was 158/1 — +8 geo tests; shapely path skipped because the extra
  is not installed in this env). No Lua edits, no heavy deps, core install
  unchanged.
- **WP9 — reference-anchored corpus + `octane_find_grammar`** (shipped 2026-07-09,
  `c90d84c`→`6cad9b5`, pushed): added `src/octanex_mcp/corpus.py` (manifest model +
  registry/index/load/validate + `find_grammar` descriptor retrieval) and
  `scripts/harvest_commons.py` (Wikimedia Commons harvest → pixel-QA filter →
  derive acceptance spec). Three real bugs fixed during live run: (1) MCP server
  import crash (`corpus.py` importing `benchmarks` — relocated pixel-QA to
  `octanex_mcp.acceptance`); (2) JPEG magic-byte trap (Commons serves JPEG despite
  `.png` thumburl — `normalize_to_png` sniff + Pillow transcode, behind `harvest`
  extra, centralized in `harvest_subject`); (3) broken foreground check
  (`foreground_bbox_area_percent` always ~100% → gated on `foreground_pixel_percent`).
  Corpus seeded with 6 real CC-licensed Commons refs; `octane_find_grammar` retrieves
  them live (40-tool server verified via `hermes mcp test octanex`). Remaining:
  iteration-loop (warm-start render → converge → auto-promote to `benchmarks/spec.py`).
- **WP9 — Wikidata subject-match enrichment (shipped 2026-07-09):** added
  `src/octanex_mcp/wikidata.py` + `tests/test_wikidata.py` (12 tests, all pass). The
  Commons image search returns the first title-matching file, not a verified
  single-subject photo — live runs returned a *butterfly* for "yellow banana" and a
  *flag* for "green leaf". The gate now anchors on the query HEAD NOUN (color/material
  descriptors stripped), checks the resolved file's Commons **categories** for a
  substring match, and **fails CLOSED**: a file whose categories lack the noun is
  rejected before it enters the corpus; an unverifiable lookup (429/uncategorized)
  is rejected too, never silently accepted. Network is injectable + backoff-decorated
  so the matcher is offline-testable and the harvest is resumable. Wired into
  `harvest_subject`/`harvest_batch` (fail-closed on gate). Full suite 179 pass / 3 skip.
- **WP9 — iteration loop (shipped 2026-07-09):** added `src/octanex_mcp/iteration.py`
  + `tests/test_iteration.py` (7 tests, all pass). Closes the corpus→benchmark loop:
  `build_candidate_scene()` turns a harvested entry's *derived* acceptance grammar
  (dominant hue → material color, iso camera, soft studio) into an Octane scene spec;
  `iterate_entry()` renders it (injectable `render_fn`; `live_render_fn` drains Octane
  via `benchmarks.harness`), evaluates against the entry's own `derived_acceptance`,
  and applies bounded material/lighting tweaks on cheap failures (near-black,
  low-contrast, missing color family) — halting as `needs_human` only on genuine
  structural failures (shape_profile with a non-empty render, or object-too-small/
  clipped). `promote_entry()` writes `octane-preview.png` + `promotion.json` +
  a paste-ready `promotion_snippet.py` into the entry dir, flips `status=converged`,
  and appends a generated `BenchmarkTask` to `PROMOTED_TASKS`. Full suite now
  186 pass / 3 skip. Live drain path is not exercised in CI (needs an Octane session);
  the offline path is fully covered.
- **A (live) — recipe verification fix + vision tier** (2026-07-09): found the 5
  "verified-but-wrong" recipes were failing because the Octane bridge ignores OBJ
  `usemtl`/MTL colors — materials only reach the mesh via explicit
  `create_material` + `assign_material`. The 4 photoreal/space recipes emitted zero
  `create_material` (relied on MTL, which is ignored); `geospatial-terrain` emitted
  materials but no `assign_material`. Added `scripts/fix_recipe_materials.py`
  (idempotent: derives `usemtl` groups from `scene.obj`, emits a `create_material`
  per group with color/kind from each recipe's `materials` block, then an
  `assign_material` with the correct 1-based `group_index`), ran it on the 5 broken
  recipes. Added an **opt-in vision-against-intent tier** to the acceptance harness
  (`benchmarks/vision_check.py` + wired into `benchmarks/verify_recipes.py` via
  `--vision-check`): after pixel QA passes, a vision model confirms the PNG actually
  shows the recipe's stated subject and **blocks promotion** on a wrong-subject
  verdict (no real model call in the offline test suite — `vision_fn` is injected).
  Re-rendered the 5 fixed recipes live; all 5 now render correct color-dependent
  subjects (Earth, Saturn, product studio, 5 vases, terrain). Full 18-recipe
  `copy_back` sweep running to flip `native_octane_verified` on every recipe that
  passes pixel QA. New tests: `tests/test_verify_recipes.py::TestVisionTierOffline`.
- **Test-framework reconciliation** (committed 2026-07-09): Plato's 4 merged
  pytest-style test files (`test_gateway`, `test_config_render_host`,
  `test_progressive_save`, `test_status_schema`) converted to `unittest.TestCase`
  to match the repo's explicit `python -m unittest` policy (harness.py). Replaced
  `pytest.raises` → `assertRaises` and `tmp_path`/`monkeypatch` → `tempfile` +
  `mock.patch.object`. Full suite now collects **136 tests** (122 + 14), all pass
  under the canonical command — previously his 14 were silently 0 under unittest.
  Minor cosmetic `ResourceWarning` (unclosed listening socket in gateway teardown)
  pre-exists and is out of scope.
- `5d928ac` fix(bridge): render-restart retry loop unblocks Tier 3–6 renders; 18/18 benchmarks live.
- `760e34b` docs(canvas): ticket-ready implementation roadmap + proposal cross-link.
- `fc566cf` feat(benchmarks): progressive visualisation suite + Tier 1–2 live verification.
- **A (live) — recipe verification fix + vision tier** (2026-07-09): found the 5
  "verified-but-wrong" recipes were failing because the Octane bridge ignores OBJ
  `usemtl`/MTL colors — materials only reach the mesh via explicit
  `create_material` + `assign_material`. The 4 photoreal/space recipes emitted zero
  `create_material` (relied on MTL, which is ignored); `geospatial-terrain` emitted
  materials but no `assign_material`. Added `scripts/fix_recipe_materials.py`
  (idempotent: derives `usemtl` groups from `scene.obj`, emits a `create_material`
  per group with color/kind from each recipe's `materials` block, then an
  `assign_material` with the correct 1-based `group_index`), ran it on the 5 broken
  recipes. Added an **opt-in vision-against-intent tier** to the acceptance harness
  (`benchmarks/vision_check.py` + wired into `benchmarks/verify_recipes.py` via
  `--vision-check`): after pixel QA passes, a vision model confirms the PNG actually
  shows the recipe's stated subject and **blocks promotion** on a wrong-subject
  verdict (no real model call in the offline test suite — `vision_fn` is injected).
  Re-rendered the 5 fixed recipes live; all 5 now render correct color-dependent
  subjects (Earth, Saturn, product studio, 5 vases, terrain). Full 18-recipe
  `copy_back` sweep running to flip `native_octane_verified` on every recipe that
  passes pixel QA. New tests: `tests/test_verify_recipes.py::TestVisionTierOffline`.

## Proposed next steps (reviewer recommendations)

Prioritised against the roadmap's open work packages + brainstorm backlog. Each
item states the concrete first action so a smaller model (or Plato) can pick it up.

1. **Run direction A live — close the 16-recipe honesty gap.** Highest integrity
   payoff; harness is built and contract-OK. First action: execute against a
   running Octane session, batch the 6 network/data-viz recipes first
   (`network-graph`, `pca-3d`, `correlation-heatmap`, `scatter-plot`, `bar-chart`,
   `histogram`) to validate the live path fast, then the rest. Promote only those
   that pass pixel QA (`copy_back=True`).
2. **WP6 recipe promotion (B of brainstorm).** Wrap the 3 strongest verified
   recipes as first-class tools: `octane_build_product_studio`,
   `octane_build_planet_scene`, `octane_visualize_network`. Files:
   `src/octanex_mcp/recipes.py`, `server.py`, `tests/test_recipes.py`.
3. **WP7 geo/terrain grammar (C of brainstorm).** GeoJSON/DEM → combined OBJ behind
   `uv sync --extra geo` (shapely), with graceful "extra missing" failure per the
   dependency policy. Highest research fit (ECDO/TPW/impact-structure).
4. **Canvas Phase B wiring (builds on Plato's Phase A).** Connect the gateway's
   `read_status()` + `/mcp/call` to a live dashboard: intent command bar →
   `octane_build_concept` / `octane_queue_recipe`, status pill from `render_stage`.
   Files: `apps/octanex-canvas/web/*`, `gateway.py`.
5. **WP8 animation DSL (F of brainstorm).** Camera-orbit keyframe manifest +
   optional ffmpeg encode; bounded first slice only.
6. **Texture gen (G of brainstorm).** image-gen → `texture_path`/`normal_path` on
   materials, closing the "texture approximated with geometry" recipe pitfall.
7. **H — Reference-anchored corpus expansion** (new brainstorm direction):
   `reference_to_acceptance()` + `scripts/harvest_commons.py` + `corpus.py` +
   `corpus/<slug>/` manifest. Pure-Python, offline-testable, builds on the
   existing `octane_render_review_loop` (WP5). Highest compounding leverage once
   A's verification harness pattern is proven.

**Recommended sequence:** (1) first — it is the only remaining honesty gap and is
already coded. Then (2) or (3) for ergonomics/research leverage; (4) is a parallel
Swift/JS workstream Plato can own. (5)/(6) are later.
