# OctaneX MCP — Work In Progress

Living WIP board. Mirror of `docs/roadmap.md` §Status snapshot + §Development
brainstorm, kept as a fast-glance status doc. Last updated **2026-07-09**.

## Current state (evidence, 2026-07-09 — WP9 shipped through 6cad9b5)

| Area | State |
|------|-------|
| Repo | `main` = `6cad9b5` (pushed to `origin/main`) |
| Tests | 166 passed / 3 skipped (offline `python -m unittest discover -s tests`) — green |
| Octane X | running (pid 67403); bridge status `processed`, last event `save_preview`; status age ~2413s, no wedge/failed |
| Benchmarks | 18/18 native-Octane verified (Tiers 1–6) |
| Recipe library | 18 recipes; **13/18 `native_octane_verified=true`** (5 remain: `annotated-text-labels`, `architecture-flow`, `avatar-guide`, `data-bars`, `document-ocr-layout`) |
| Core mechanics | solid: bridge, schema, pixel-QA, render-review loop, scene v2, PBR mats/lights, bounds-camera, recipe registry, **WP7 geo grammar first slice**, **WP9 corpus + `octane_find_grammar` (shipped)** |
| Unscaffolded | WP6 promoted tools, WP7 geo live-path, WP8 animation, Canvas Phase B+ wiring, Studio multi-host, visual memory, WP9 iteration-loop / Wikidata enrichment |

**Bottom line:** reliability + core mechanics are proven. The gap is
*surface area + closure* — high-level ergonomics (promoted tools, domain
grammars, canvas UI, autonomous loop) and recipe-library verification (5 recipes
still unverified) are the remaining work.

## Backlog (from brainstorm 2026-07-09)

Ranked by effort × strategic fit (reviewer's call — none committed yet):

1. **A — Recipe verification** (LOW effort / HIGH integrity): live-verify the 16
   unverified recipes, flip `native_octane_verified`, append `docs/recipe-book.md`.
   *First step:* a `verify-recipe-library` loop reusing `benchmarks/harness.run_task`
   over `examples/recipes/*`.
2. **B — Geo / terrain grammar** (HIGH strategic fit; FIRST SLICE SHIPPED this run): `src/octanex_mcp/geo.py` now has pure-Python `elevation_grid_to_obj` (DEM/grid→height-field) + shapely-gated `geojson_to_obj` (GeoJSON/points/lines/polygons→extruded OBJ) with graceful `GeoDependencyError` + `uv sync --extra geo` hint, plus `geo_asset_to_scene_commands`. *Remaining first-step:* add a thin MCP tool `octane_geojson_to_scene` exposing `geojson_to_obj` + bounds camera; exercise the shapely path under a `geo` extra env.
3. **C — Agentic Canvas app** (biggest unbuilt): Phase A slice — shell + full-bleed
   viewport + intent command bar + `OCTANEX_RENDER_HOST` Studio flag
   (from `docs/canvas-implementation-roadmap.md`).
4. **D — Autonomous loop**: bounded 2-iteration `octane_render_review_loop` over one
   recipe, driven end-to-end.
5. **E — Recipe promotion** (WP6): wrap the 3 strongest recipes as first-class tools
   (`octane_build_product_studio`, `octane_build_planet_scene`, `octane_visualize_network`).
6. **F — Animation DSL** (WP8): camera-orbit keyframe manifest + optional ffmpeg encode.
7. **G — Texture gen**: image-gen → `texture_path` / `normal_path` on materials,
   closing the "texture approximated with geometry" recipe pitfall.

## Recommended next move

**B (geo live-path) → then close recipe honesty gap.** B's pure-Python slice
is shipped and offline-green; the shapely-backed `geojson_to_obj` path needs a
`uv sync --extra geo` env to exercise live, and then a thin MCP tool
(`octane_geojson_to_scene`) to expose it. The 5 still-unverified recipes
(`annotated-text-labels`, `architecture-flow`, `avatar-guide`, `data-bars`,
`document-ocr-layout`) remain the only remaining honesty gap. C (Canvas) is a
separate Swift/JS workstream.

## In progress / this session

_WP7 geo grammar first slice landed (uncommitted); see Done recently. Direction A's 5-recipe fix + vision tier is committed. Live recipe sweep sits at 13/18._

## Done recently

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
  iteration-loop + Wikidata enrichment (subject-match tightening).
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
