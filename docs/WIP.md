# OctaneX MCP — Work In Progress

Living WIP board. Mirror of `docs/roadmap.md` §Status snapshot + §Development
brainstorm, kept as a fast-glance status doc. Last updated **2026-07-10** (re-grounded against HEAD `8606d92`). The "16-recipe honesty gap" framing in this board is STALE — the library is 20/22 verified; the 2 remaining gaps are live-render closure items (see §Direction A live-closure status).

## Current state (evidence, 2026-07-10 — steward run 7d30b26)

| Area | State |
|------|-------|
| Repo | `main` = `7d30b26` (HEAD; tree **clean**). Recent: `swap_geometry` MCP tool + gateway (H2, `7d30b26`), bridge canonical-node fix (`888329c`), WP6 chess recipes (`b29cd45`), `swap_geometry` primitive (`2e0f00e`), WP8 math-surface gap fix (`3bbdc62`) |
| Tests | **237 ran / 0 failures / 4 skipped** (offline `python -m unittest discover -s tests`, project venv). Green. 4 skipped (live render; `geo` extra ×2; lua parity). `compileall src` clean; `doctor --json` clean (with `OCTANEX_MCP_WORKSPACE` override). **1 stale test fixed this run** (was over-asserting "all recipes verified"). |
| Octane X | not exercised this run (headless cron host). Live drains + `earth-moon-space` native render remain open (user-owned). Default OctaneMCP workspace is large enough that `octane_status`/`read_status`/`validate_queue` **hang** on this host — use `OCTANEX_MCP_WORKSPACE=<small dir>`. |
| Server boot | `run_octanex_mcp.sh` (PYTHONPATH unset) boots `build_mcp()`. (Earlier red runs were an env artifact: `uv run` inherited the Hermes-runtime venv — broken `pydantic_core`, no `mcp`. Fix: `uv run --project /Users/craig/octanex-mcp` with `PYTHONPATH`/`VIRTUAL_ENV` unset.) |
| Benchmarks | 18/18 native-Octane verified (Tiers 1–6) — per roadmap §benchmark-suite recorded table (not re-rendered this run). |
| Recipe library | **22 recipe dirs; 20 `native_octane_verified=true` (each carries an `octane-preview.png`); 2 honestly-declared pending.** Pending: `earth-moon-space` (no PNG on disk) + `helicoid-spiral` (PNG present but BLANK — 94% near-white, the documented render-target failure mode, so correctly pending). Ground truth via `_recipe_dirs` + `scene.json` + pixel QA on the committed PNG. The old "18/18" / "21/22" / "16-recipe gap" lines were all stale. |
| Core mechanics | solid: bridge, schema, pixel-QA, render-review loop, scene v2, PBR mats/lights, bounds-camera, recipe registry, WP6 promoted tools, WP7 geo (`octane_visualize_geojson`), WP8 animation model+tool, WP9 corpus + `octane_find_grammar` + iteration loop, `swap_geometry` streaming primitive + `octane_swap_geometry` tool. |
| Unscaffolded | `earth-moon-space` native render + `helicoid-spiral` re-render after a fresh Octane restart (the 2 honest gaps), WP6/WP8 **live end-to-end drains**, WP7 **live-`geo` exercise**, Agentic Canvas Phase B+, Studio multi-host, visual memory |

**WP8 live-drain notes (this session):** the `octane_build_animation` tool was drained live. Found + fixed a path bug: `build_animation_commands` must emit a **relative** `renders/frame_XXXX.png` path (matching how `octane_save_preview` writes `octane-preview.png`). An absolute `/…/OctaneMCP/renders/…` path is re-based by Octane's `saveImage` to the sandbox `Data/renders/`, losing the `OctaneMCP` segment; a relative `renders/…` resolves correctly under `OctaneMCP/renders/`. The empty-scene orbit shows camera motion against an empty stage — the tool is a camera-motion primitive; pair with an imported mesh for a subject.
**Bottom line:** reliability + core mechanics are solid, and recipe-library honesty is now explicit rather than inflated: **20/22 verified**, with 2 live-render closure items still open. The remaining open work is live closure + surface area/polish.

## Backlog (from brainstorm 2026-07-09, re-ranked 2026-07-09 run 3ad0094)

Ranked by effort × strategic fit (reviewer's call — none committed yet):

1. **A — Recipe verification (close the honest gaps)** (LOW effort / HIGH integrity): the remaining gaps are **`earth-moon-space`** (`scene.json` declares `native_octane_verified=false`, no preview PNG on disk) and **`helicoid-spiral`** (`scene.json` declares false because the committed PNG is a blank frame). Re-render them live after confirming Octane is running a fresh bridge script, and if they pass pixel QA, flip the flags + append `docs/recipe-book.md`. The old "18/18 verified" / "math-surface gap" lines in this board were stale — `math-surface` is closed and the library now holds 22 recipes. *First step:* `verify_recipe_library(live=True, copy_back=True, slug='earth-moon-space')`, then `slug='helicoid-spiral'`, against a running Octane session (user-owned; needs Octane).
2. **B — Geo / terrain grammar live path** (HIGH strategic fit; **MCP tool SHIPPED**): `octane_visualize_geojson` registers on the MCP server (graceful `GeoDependencyError` → `uv sync --extra geo` hint; tests in `tests/test_geo_tool.py` + `tests/test_geo_grammar.py`). *Remaining:* exercise the shapely-backed path live under a `geo` extra env.
3. **C — Agentic Canvas app** (biggest unbuilt): Phase B wiring — connect `gateway.read_status()` + `/mcp/call` to a live dashboard (intent command bar → `octane_build_concept` / `octane_queue_recipe`; status pill from `render_stage`). Phase A slice (shell + viewport + command bar + `OCTANEX_RENDER_HOST` flag) from `docs/canvas-implementation-roadmap.md`. Swift/JS workstream.
4. **D — Autonomous loop**: bounded 2-iteration `octane_render_review_loop` over one recipe, driven end-to-end.
5. **F2-live — Animation live drain** (WP8 continuation; HIGH north-star fit): the `octane_build_animation` tool is shipped (queues per-frame `set_camera` + `frame_XXXX.png` `save_preview`); the next step is a **live Octane drain** to render a real orbit clip, confirm the frames land, and (optionally) wire ffmpeg encode via the injected encoder. No Lua edit required for the drain.
6. **G — Texture gen**: image-gen → `texture_path` / `normal_path` on materials, closing the "texture approximated with geometry" recipe pitfall.
7. **E — Recipe promotion** (WP6) — **DONE**; first-class tools shipped + tested. Removing from active backlog.
8. **H2 — Expose `swap_geometry` as an MCP tool + gateway entry** — **DONE** (2026-07-10). `octane_swap_geometry(scene_id, object_id, new_path, format, queue)` tool added in `server.py` + a `gateway.py` `DISPATCH` entry (`_swap_geometry_dispatch`), mirroring `octane_import_geometry`. New `tests/test_gateway.py::TestSwapGeometryTool` covers registration + swap-and-queue. The library primitive (`src/octanex_mcp/scene.py::swap_geometry`) is now callable from Hermes and Canvas. No Lua edit, no deps.

## Recommended next move

**Live closure first (user-owned, needs Octane session):** (1) the two honest recipe gaps are **`earth-moon-space`** and **`helicoid-spiral`** — re-render them live to flip `native_octane_verified=true`; (2) run a real Octane drain of `octane_build_animation` to render a genuine orbit clip. Both require a live Octane session, not code — the autonomous steward cannot do them. For safe code work the steward can take next: **B live-`geo` exercise** (needs `uv sync --extra geo`, still offline-testable after sync) or deepen C/E surface.

## In progress / this session

_No uncommitted library work this run. Re-grounded the docs snapshot against HEAD `8606d92`. Recipe-verified ground truth: **20/22** `native_octane_verified=true` (each with a real `octane-preview.png`); **2 honestly-declared pending** — `earth-moon-space` (no PNG) and `helicoid-spiral` (PNG on disk but a blank frame: mean RGB ~242, 94% near-white, the documented render-target failure). The old "21/22 / lone gap" line was stale._

## Done recently

- **Streaming data-grammar primitive — `swap_geometry` (shipped this run, uncommitted):** added `src/octanex_mcp/scene.py::swap_geometry(scene_id, object_id, new_path, format='obj', queue=False)`. Replaces an object's OBJ asset **in place while preserving its stable node name** (`Hermes::scene::object`) — the *replaceable-asset-files* half of the north-star streaming protocol (`docs/canvas-roadmap.md` §2). Reuses the existing `import_geometry` op (no schema/Lua change); flips the object to `type=mesh` so `build_scene_commands` does not regenerate/overwrite the swapped path; emits a schema-valid `swap_command` envelope (optionally queued). New `tests/test_scene_plan.py::SwapGeometryTests` (4 tests: stable-name preserved, missing-file rejected, unknown-object rejected, queue-writes-command). Suite now **234 passed / 5 skipped** (was 230/4). No Lua edit, no deps. **Now ALSO exposed as `octane_swap_geometry` MCP tool + gateway `DISPATCH` entry (2026-07-10, H2 closed).**
- **WP8 animation DSL — first slice (steward run d1d0e37, uncommitted):** added `src/octanex_mcp/animation.py` (pure stdlib, no heavy deps — ffmpeg stays an external tool, encoder injected). `CameraKeyframe`/`AnimationManifest` model; `sample_camera` (linear interp + hold-clamp), `camera_command` (Octane `set_camera` envelope), `build_bake_plan` (per-frame render schedule), `frame_paths`, `encode_frames` (injected-encoder only), `orbit_manifest` (circular camera orbit as a 25-keyframe polyline arc, not a 2-point chord). New `tests/test_animation.py` (13 tests, all pass). Suite now **216 passed / 4 skipped** (was 199/4 — +13 animation tests; the +4 vs 203 came from the harness commits `a2fccb9`/`d1d0e37`). `compileall` clean; `build_mcp()` boots (44 tools) with no `benchmarks`/`scripts`/`tests` imports added to `animation.py` (§6 layering holds — verified via AST scan + `import octanex_mcp.animation`). No Lua edits, no deps; core install unchanged. Next WP8 step (F2): MCP tool + bridge bake emitting the per-frame camera commands.
- **Stale-test regression fix (steward run 2fbc567, uncommitted):** Phase-1 caught the offline suite RED — `test_recipe_index_lists_checked_in_recipes_with_required_metadata` asserted `data-bars["native_octane_verified"] is False`, but `data-bars` was genuinely promoted to verified by the WP6 honesty work (`c572ace`, real `octane-preview.png` present, confirmed via `_recipe_dirs` ground-truth). Corrected the assertion to `assertTrue(...)` with a provenance comment. Suite restored to **199 passed / 4 skipped** (0 failures). Pure `tests/` change; no library import touched, so §6 server-boot layering is unaffected (`doctor` already confirmed the server path is sound). No Lua edits, no deps.
- **Stale-test fix — recipe-library "all verified" assertion (steward run 7d30b26, uncommitted):** Phase-1 caught the offline suite RED again — `test_validate_recipe_library_reports_every_checked_in_recipe_ok` asserted *every* recipe had a preview PNG (commenting "all 18/18 verified"), but the library has grown to **22 recipes** and `earth-moon-space` is **honestly declared pending** (`native_octane_verified:false`, no preview). Patched to assert the real honesty contract: any recipe declaring `native_octane_verified=true` must carry a preview; declared-pending recipes are exempt (the gap stays visible in `recipe_index`, not masked). Pure `tests/` change; §6 layering unaffected. Suite now **237 ran / 0 failures / 4 skipped** (was 1 failure). Also documented the env caveat: `uv run` must target the project venv (`uv run --project /Users/craig/octanex-mcp`, `PYTHONPATH`/`VIRTUAL_ENV` unset) — the Hermes agent-runtime venv has a broken `pydantic_core` + no `mcp`, which otherwise makes the whole suite error with "mcp package is not installed".
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
