# OctaneX MCP — Work In Progress

Living WIP board. Mirror of `docs/roadmap.md` §Status snapshot + §Development
brainstorm, kept as a fast-glance status doc. Last updated **2026-07-16**
against HEAD `08a1cb5` plus the live real-physics-library smokes and Tier 8
MHD benchmark work since then.

## 2026-07-14 fix-log (this steward)

- **Recipe-contract leniency (permanent, no coord push needed):** `earth-hemisphere`'s
  large `scene.obj` is gitignored (size-limited Mac Studio copy) and rebuilt via
  committed `scripts/gen_earth_hemisphere.py`. Both `recipes.py:validate_recipe_library`
  and `benchmarks/verify_recipes.py` now share one `_is_regenerable_recipe`
  helper (`octanex_mcp/recipes.py`) so a missing-but-regenerable OBJ is accepted
  (warning, not failure). Offline contract is **31/32 OK** on a clean checkout
  (only `earth-moon-space` fails — no checked-in preview). Previously the suite
  was green only where the gitignored OBJ happened to exist locally.
- **Hermes model-mirror fix (canvas `/config/models`):** root cause was
  `hermes_config.list_models()` returning `"config unavailable"` whenever PyYAML
  was absent from the gateway venv (laptop) — empty selector though it worked on
  Studio. Fix: declared `pyyaml>=6.0` as a core dep; made `list_models()`
  shape-agnostic (`providers` dict vs `custom_providers` list; `models` dict vs
  list); and made it **cache/proxy-backed** so the selector mirrors the Hermes
  cloud/provider caches + live proxy `/v1/models` even without config.yaml.
  Live endpoint now returns **192 models** (155 local + 37 cloud) with `current`
  detected. `test_hermes_config` 12/12 green.

## Current state (evidence, 2026-07-15)

| Area | State |
|------|-------|
| Repo | `main` = `08a1cb5` (`feat(physics): unblock Genesis + SPlisHSPlasH real-library smokes (all 4 passed)`), tracking `origin/main`; tree clean. |
| Tests | **509 ran / 0 failing / 10 skipped** on a clean checkout via `unittest discover -s tests` — fully green. The 3 pre-existing `test_harness_drain` errors (missing `processing_dir` in factory `SimpleNamespace`) were fixed this run. The previously-failing `test_physics_fixture_io` import path issue was fixed in HEAD. Recipe + benchmark + Lua-parity suite green; `compileall src` clean. |
| Doctor / bridge | `octanex-mcp doctor --json` returned `ok: true`. Octane X bridge status seen as `status=processed`, `render_stage=ready`, `samples_done=256`, `samples_target=256`, last_preview=`recipe_nbody-chaotic-divergence_octane-preview.png`. Bridge module `hermes_bridge_oneshot_v2.lua` in one-shot mode. |
| Recipe library | **54 recipe dirs**. Offline contract pending live re-sweep; `earth-moon-space` remains the known no-preview gap and `earth-hemisphere` is **regenerable** (`scene.obj` gitignored, rebuilt via `scripts/gen_earth_hemisphere.py`; shared `_is_regenerable_recipe` in `recipes.py`). `native_octane_verified` counts pending live sweep. |
| Core mechanics | Broad coverage across schema/dispatch guards, command queue, pixel QA, live scene harvest, scene-plan/live-graph sanity checks, recipe registry, WP6 promoted tools, WP7 geo tool, WP8 animation tool, WP9 corpus/retrieval/iteration, `swap_geometry`, API-corpus/capability/probe tools. This sweep also removes a library-layering trap by lazy-importing `benchmarks.spec` inside `iteration.py` instead of importing repo-root benchmark code at package import time. |
| Documentation corpus | Added/curated `docs/3DXM/` as a 3D-XplorMath / Collected ATOs math-surface grammar reference for the gallery pipeline. Existing `docs/recipe-gap-fill.md` remains the proposal for filling blocked 3DXM surfaces with parametric/Weierstrass meshers. New planning docs: `docs/physical-simulation-recipe-suite.md` and `docs/luisa-render-backend-investigation.md`. |
| Unscaffolded / open | WP12 single-source Lua handler generation, WP13 material/light compatibility registry, live WP7 geo exercise, live WP8 orbit clip with subject + optional ffmpeg encode, Agentic Canvas Phase B status/operator surface, multi-host Studio, visual memory, WP15 renderer-agnostic backend abstraction with LuisaRender QualityBackend spike, and a 3DXM parametric/Weierstrass mesher for non-implicit gallery surfaces. |

**Bottom line:** the repo has grown into a working visual workbench with 30 recipe dirs and a live bridge, but the current closure risk is documentation/test drift after rapid recipe additions. This sweep consolidates that drift and keeps the remaining gaps explicit instead of silently promoting unverified renders.

## Ranked backlog / next steps

1. **0 — Physics render closure (HIGH effort / HIGHEST fit):** all four source
   libraries (Oceananigans, SPlisHSPlasH, Genesis, MPIPyMHD) now pass real-library
   smokes. *First step:* promote one real-library-derived recipe through a native
   OctaneX render and run the Tier 8 MHD diagnostics end-to-end; record acceptance.
2. **I — Capability-driven bridge hardening** (MEDIUM effort / VERY HIGH fit): finish WP12 single-source Lua handler generation and WP13 registry-backed material/light behavior reporting. *First step:* make handler edits single-source, then prove one material/light command path against the registry.
3. **J — Pre-render sanity adoption** (LOW effort / HIGH reliability): use `octane_check_scene_plan` and `octane_scene_sanity` as mandatory guards before recipe/live drains. *First step:* add a verifier path that writes sanity reports next to render outputs.
4. **M — 3DXM parametric/Weierstrass mesher** (MEDIUM-HIGH effort / HIGH research fit): turn `docs/3DXM/` and `docs/recipe-gap-fill.md` into reusable mesh generators for non-implicit math-museum surfaces. *First step:* implement one parametric surface recipe from `docs/3DXM/minimal-surfaces.md` and gate it with pixel QA + local vision.
5. **B — Geo / terrain grammar live path** (HIGH research fit): `octane_visualize_geojson` ships with graceful `geo` extra handling. *Remaining:* exercise the shapely-backed path live under `uv sync --extra geo` and record the output/QA.
6. **F2-live — Animation live drain** (HIGH communication fit): `octane_build_animation` queues per-frame camera motion. *Remaining:* import a real subject, render a short orbit clip, verify frames differ, and optionally encode with ffmpeg.
7. **K — Canvas/status operator surface** (MEDIUM effort / HIGH communication fit): expose bridge readiness, capabilities, queue state, and recipe index in Agentic Canvas. *First step:* status pill + capability panel backed by `/mcp/call`.
8. **G — Texture / material generation**: image-gen → `texture_path` / `normal_path` material payloads, closing the "texture approximated with geometry" recipe pitfall.
9. **L — Renderer-agnostic backend abstraction** (MEDIUM effort / HIGH strategic fit): decouple the command DSL from Octane X so it becomes one of N render backends; research in `docs/visualization-backends-research.md`. *First step:* extract a `Backend` interface (OctaneBackend first), then ship `WebGLBackend` (three.js in Agentic Canvas) as the Phase-1 realtime + shareable win.
10. **N — LuisaRender QualityBackend smoke spike** (MEDIUM effort / HIGH strategic fit): prove the open, local, Metal-backed path before production adapter work. `scripts/spike_luisa_scene.py` now codifies the smoke: it writes a minimal `.luisa` inline-mesh scene, runs `luisa-render-cli -b metal`, converts EXR→PNG, and fails nonzero on blank/flat pixel stats. *Next step:* translate one simple `BenchmarkTask` through the same path.

## Recommended next move

The physics frontier is now **real-library closure**, not LuisaRender (N). All four
source libraries pass local smokes (see `docs/physics-real-library-smokes.md`), so
the high-leverage work is:

1. **Render closure** — ✅ `mhd-orszag-tang-vortex` (MPIPyMHD adapter) promoted:
   native Octane render re-queued from `scene.json` (14 authoritative commands, all
   5 `assign_material` group_index calls), pixel-QA + vision subject-check passed,
   `native_octane_verified` flipped true. Tier 8 `t8_mhd_field_ribbons` rendered
   (pixel-QA ok); `t8_conservation_budget` re-run clean after a shared-queue
   contamination wedged the first attempt. Next: confirm budget PNG + run a second
   real-library recipe (e.g. `oceananigans-shallow-water-front`) through the same path.
2. **Adapter hardening** — wire `dam-break-splash` to the live `pysplishsplash`
   `Simulation` API (not just the headless CLI) and extend Genesis to multi-body/cloth.
3. Keep **I/J** (WP12/WP13 bridge + pre-render sanity) as the reliability spine for
   live Octane work, and **L/WebGLBackend** as the realtime Canvas path.
   LuisaRender (N) is the offline quality tier, now secondary to physics closure.

## PDF Consolidation (docs/3DXM/ — 3DXM Virtual Math Museum)

**Completed 2026-07-13** — Harvested the entire virtualmathmuseum.org geometry museum for the
OctaneX MCP grammar pipeline. 22 PDFs downloaded; 13 redundant PDFs moved to staging, 9 kept
as the core collection. Collected_ATOs.pdf (7 MB) serves as the master index for all exhibits.

| Decision | PDFs | Action |
|---|---|---|
| **Keep (9)** | Collected_ATOs, Surfaces, Space_Curves, Plane_Curves, Conformal_Maps, Fractals, Platonics, Helicoid-Catenoid, Enneper_Surface | Core geometry for OctaneX MCP — unique equation sets, distinct math, direct grammar mapping |
| **Stage (13)** | CatalanHennebergScherk, ConstKSurfofRev, Costa, Fractals_and_Chaos, Helix, Koch_Snowflake, Mandelbrot_Set, MonkeyTorusCyclide, RuledSurfaces, Saddle_Tower, Scherk_w_Handle, Schwarz_H_Family, Torus_Knot | Content covered by Collected_ATOS, Surfaces, or Fractals (verified via MinerU pdftotext extractions) |

MinerU text extractions saved at `docs/3DXM/mineru_text/*.txt` (total 610 KB) for full-text search.

---

## Done recently

- Today — **physics render closure**: re-queued `mhd-orszag-tang-vortex` from
  `scene.json` (14 authoritative commands incl. all 5 `assign_material` group_index
  calls), native Octane render landed (pixel-QA ok, vision subject-check ok),
  `native_octane_verified` flipped true. Tier 8 `t8_mhd_field_ribbons` rendered
  (pixel-QA ok); `t8_conservation_budget` re-run clean after a shared-queue
  contamination (15 stray `assign_material` commands injected mid-run) wedged the
  first attempt — do not assume queue isolation when another agent/steward is live.
- Today — fix(test): `test_verify_recipe_library_dry_run_counts` drift `41→42`
  total / `40→41` contract_ok (new physics recipes); `cathedral` now fails the
  contract on a **real** missing `scene.mtl` — generated the hint MTL from
  `scene.json` MATERIALS so it passes; `earth-moon-space` remains the only
  intentional contract gap (no checked-in preview).
- Today — docs: sync `WIP.md` to HEAD `08a1cb5` (recipe count 54 dirs, physics
  frontier supersedes LuisaRender N) and fix the contradictory summary/"Next
  unblockers" in `docs/physics-real-library-smokes.md` (all 4 libraries pass).
- Today — **re-validated the env blockers (they were stale):**
  - Genesis `import genesis` works (v1.2.2) from its `.venv` with PYTHONPATH
    stripped — the earlier "No module named 'quadrants'" was a Hermes-runtime
    PYTHONPATH *leak* into `.venv/bin/python`, not a missing dep.
  - SPlisHSPlasH: `pysplishsplash` **imports OK** (`.so` present in octanex
    `.venv`); real dam-break scenes ship as **JSON** (`data/Scenes/DamBreakModel.json`
    etc.), consumed via headless `SPHSimulator --no-gui <scene.json>` (the project's
    established segfault-free path). No scene-XML authoring needed.
  - Tier 8: `t8_mhd_field_ribbons` re-ran acceptance on its on-disk render →
    **passed** → flipped `native_octane_verified True`. `t8_conservation_budget`
    render is non-blank but **FAILS** its own `color_family` acceptance (magnetic
    bars at 0.48% of non-bg vs 0.5% min) — left `False`; real geometry/magnitude
    defect, not a flag to flip.
- Today — fix(benchmarks): drain-wait false-negative fixed at root. `run_recipe` /
  `run_task` now detect render completion from the PNG's **fresh mtime**
  (`_wait_for_fresh_preview` in `benchmarks/harness.py`), not the command queue
  (which empties the instant Octane is dispatched, ~200s before convergence).
  `drain_oneshot` now (a) clears orphaned `processing/` files from killed prior
  runs so a stale file can no longer block every future drain, and (b) only waits
  for `queue/` to empty (dispatch confirm), leaving the full `drain_timeout` for
  the PNG wait. Baseline mtime is snapshotted before the drain so a freshly
  written frame registers as new. Verified end-to-end: live vortex render now
  returns `acceptance_passed: true` and auto-promotes (was `acceptance: null`).
- Today — fix(spec): promote `t8_mhd_field_ribbons` to `native_octane_verified=True`
  (evidence-backed; acceptance passes on the live render).
- Today — **physical-simulation roadmap closure (all 4 libraries integrated):**
  - **MHD solver fixed to be genuinely conservative.** The old central-difference
    integrator lost ~45% of total energy over 8 steps (internal energy collapsed to
    ~0) — a real solver defect surfaced by the first live-solve test. Replaced with
    a finite-volume Rusanov scheme in `scripts/mhd_integrator.py` (single source of
    truth for both the MPIPyMHD exporter and `benchmarks/spec.py`). Total energy now
    conserved to round-off (drift ~1e-14%) and stable with CFL-safe dt. Re-rendered
    `mhd-orszag-tang-vortex` (live, 437 KB, acceptance-passing, re-promoted) and
    `t8_conservation_budget` (live, acceptance passes: KE 0.97 / ME 0.011 / IE 0.023
    color families all clear the 0.5% gate). Benchmark tasks carry verification via
    the harness acceptance pass, not a `native_octane_verified` recipe flag.
  - `t8_conservation_budget` geometry: wider bars + tighter camera + min-height floor
    so all three energy families are honestly visible (defect fixed, not masked).
  - **Genesis B5** `genesis-cloth-on-rigid`: built the full fixture-first adapter —
    committed draped fixture (`examples/fixtures/genesis/cloth-on-rigid/`, 65 contact
    verts), shared drape math (`scripts/genesis_cloth_drape.py`), recipe generator
    (`scripts/gen_genesis_cloth_on_rigid_recipe.py`), exporters, and
    `tests/test_genesis_cloth_adapter.py` (2 tests green). Live-rendered + promoted
    via `run_recipe(..., live=True, copy_back=True)`. Genesis is no longer the only
    library with zero integration.
  - Recipe count: 43 dirs, 42/43 contract_ok (`earth-moon-space` the lone intentional
    gap). `test_verify_recipes` count assertion updated 42→43 / 41→42.
- Today — docs: this WIP + `physical-simulation-recipe-suite.md` reflect Phase B
  closure (all four real libraries — Oceananigans, SPlisHSPlasH, MPIPyMHD, Genesis —
  now have native-promoted recipes).
- Today — fix(test): repair `test_harness_drain` (3 errors → OK): add `processing_dir` to the `_ws()` factory's `SimpleNamespace` so `drain_oneshot` can poll the processing slot.
- Today — docs: refresh WIP.md + roadmap.md status snapshots to HEAD `db533a4`, 509 tests, 41 recipe dirs, sample count 256/256.
- Today — fix(test): recipe count drift 31→32 in dry_run parity check (`test_verify_recipes.py`).
- Today — fix(lua): oneshot↔persistent `handle_assign_material` parity (added `request_render_restart` + group-index suffix in oneshot).
- `4de64d1` — canvas: remove duplicate setViewMode def in app.js.
- `642fa21` — canvas: break app.js<->agent.js import cycle (setViewMode).
- `310b2e4` — canvas: split app.js into state.js + agent.js + app.js (shell).
- `f476ba2` — canvas: inline JS bundle into index.html (removes separate app.js fetch).
- `b04b495` — canvas: HTTP/1.1 + Connection: close to defeat fetch-hooking extension truncation.
- `4f9b9ab` — earth-hemisphere v4.1 smooth spheres + LLSVP/plume + off-axis Hermes Camera.
- `3db043e` — README points vase preview at native render.
- `6fcd43a` / `737e8e3` — earth-hemisphere v3 jello cutaway recipe + drain/queue recovery docs.
- `e4c8b3a` — shared-engine dispatch loop (gateway daemon + CLI + cron tick).
- `4ae0e65` — pointcloud merge pipeline and native vase render.
- `c325609` — shared-engine render lock + per-agent job queue.

## 2026-07-14 — get_camera op + render-pipeline defect (this steward)

- **`get_camera` op added (both bridges):** reads the live "Hermes Camera"
  node's `position`/`target`/`fov`/`up` via `getPinValue`, writes
  `results/get_camera.json`. Inverse of `set_camera` — captures a user-set
  viewport angle exactly instead of eyeballing from a screenshot. Added
  symmetrically to `hermes_bridge_oneshot_v2.lua` + `hermes_bridge_persistent_v1.lua`,
  parity 7/7 OK, **live-validated** (round-trip returned `position=[18.74,16.21,9.95]
  target=[2.5,1.4,0.4] fov=42`). Documented in `docs/octane-bridge.md`; skill
  bumped 1.9.14→1.9.15.
- **Canvas camera inheritance wired:** `submitIntent` (agent.js) now pushes
  `state.renderer.getCameraState()` into `octane_set_camera` when a build is
  queued, so Octane inherits the live Three.js viewport. Static-verified only
  (shape match + `node --check`); NOT yet exercised in a real browser.
- **DEFECT FOUND (not fixed this session):** renders come out a flat off-white/
  grey field (`preview.png` uniform `[218,218,218]`, 1 unique color) even for the
  previously-good v4 single-OBJ path. Root cause localized to the material binding,
  not the camera op:
  - `handle_assign_material` calls `connect_material_to_mesh_pins(mesh, mat,
    group_index)` **without the `mat_name_hint` 4th arg**, so the name-match
    branch never fires; it falls to the lone-pin path and `connect_to(mesh,
    "Material", mat)` returns success but the diagnostic shows `material nil ->
    pin Material` — the mesh ends up material-less → invisible.
  - Structural: a single imported OBJ mesh exposes **only ONE `Material` pin**
    (verified `MESH_PINS(1): #1 name=Material type=7`), so multi-group `usemtl`
    → multi-color can never work on one node. Per-group mesh splitting also
    fails because each `import_geometry` call disconnects the previous mesh from
    the RT (RT holds one mesh).
  - `set_lighting` is partially broken (film-pin names wrong: `No pin
    "filmResolution" in NT_FILM_SETTINGS`; still carries a "TEMP INTROSPECTION"
    block). Without a working env the scene renders unlit.
  - Both bridges ALSO carry a pre-existing asymmetric `handle_create_material`
    divergence (oneshot has a "FIX (2026-07-14)" block the persistent lacks) that
    breaks parity until reconciled. NOT introduced by this session's get_camera
    work — flag before editing create_material.
  - **Next fix path:** (1) pass `mat_name_hint = cmd.material_name` at the
    assign call site; (2) connect by pin INDEX, not just name; (3) split OBJ into
    one mesh node per material group and connect ALL to the RT without sibling
    disconnect; (4) repair `set_lighting` env pin names.
