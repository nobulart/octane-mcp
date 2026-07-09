# OctaneX MCP — Work In Progress

Living WIP board. Mirror of `docs/roadmap.md` §Status snapshot + §Development
brainstorm, kept as a fast-glance status doc. Last updated **2026-07-09**.

## Current state (evidence, 2026-07-09)

| Area | State |
|------|-------|
| Repo | `main` = `8eeca59`, ahead 3 of `origin/main` (not pushed) |
| Tests | 136 passed / 1 skipped (offline `python -m unittest discover -s tests`) — green |
| Octane X | running; persistent bridge; 135 processed / 0 failed; no wedge |
| Benchmarks | 18/18 native-Octane verified (Tiers 1–6) |
| Recipe library | 18 recipes; 2 verified, 16 target/reference only (offline contract harness passes 18/18; live verify pending) |
| Core mechanics | solid: bridge, schema, pixel-QA, render-review loop, scene v2, PBR mats/lights, bounds-camera, recipe registry |
| Unscaffolded | WP6 promoted tools, WP7 geo grammar, WP8 animation, Canvas Phase B+ wiring, Studio multi-host, visual memory |

**Bottom line:** reliability + core mechanics are proven. The gap is
*surface area + closure* — high-level ergonomics (promoted tools, domain
grammars, canvas UI, autonomous loop) and recipe-library verification are
unfinished.

## Backlog (from brainstorm 2026-07-09)

Ranked by effort × strategic fit (reviewer's call — none committed yet):

1. **A — Recipe verification** (LOW effort / HIGH integrity): live-verify the 16
   unverified recipes, flip `native_octane_verified`, append `docs/recipe-book.md`.
   *First step:* a `verify-recipe-library` loop reusing `benchmarks/harness.run_task`
   over `examples/recipes/*`.
2. **B — Geo / terrain grammar** (HIGH strategic fit): GeoJSON / DEM /
   elevation-grid → combined OBJ with bounds + camera, behind `uv sync --extra geo`.
   *First step:* one `shapely`-backed GeoJSON→mesh op with graceful extra-missing
   failure (per WP7 dependency policy).
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

**A → then B and/or C.** A is cheap and restores full honesty; B is the
highest-leverage fit for ECDO / TPW / impact-structure research; C is the biggest
step toward the shared visual communication medium. A + B are Python-only and
offline-testable; C is a separate Swift workstream.

## In progress / this session

_No open build — direction A committed; see Done recently._

## Done recently

- **A — Recipe verification harness** (committed 2026-07-09): added
  `benchmarks/verify_recipes.py` + `tests/test_verify_recipes.py`. Offline contract
  check passes for all 18 recipes; live runner reuses `drain_oneshot` +
  `acceptance` (mirrors OBJ, rewrites paths, strips `start_render` per pitfall
  #9/#10, #14). `copy_back=True` promotes a recipe (copies PNG + flips
  `native_octane_verified`) only after a real native render passes pixel QA. Dry-run
  verified: 18/18 contract-OK.
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

**Recommended sequence:** (1) first — it is the only remaining honesty gap and is
already coded. Then (2) or (3) for ergonomics/research leverage; (4) is a parallel
Swift/JS workstream Plato can own. (5)/(6) are later.
