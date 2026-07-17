# Physical Simulation Recipe Suite Plan

> **For Hermes:** Use `development/octanex-visual-recipe-workflows` and `development/octanex-benchmark-suite` before implementing this plan. Use the repo's canonical `unittest` commands, not pytest.

> **Status (2026-07-16):** Phase A implemented + native-promoted; Tier 7 benchmark tasks live-verified; **Phase B complete — all four real libraries (Oceananigans.jl, SPlisHSPlasH, MPIPyMHD, Genesis) now have native-promoted fixture-first recipes**: `dam-break-splash`, `oceananigans-shallow-water-front`, `mhd-orszag-tang-vortex`, and the new `genesis-cloth-on-rigid` (B5). All four are native-promoted through the live recipe verifier (fresh `octane-preview.png` + `native_octane_verified=true`). The MPIPyMHD B7 adapter was upgraded from an analytic snapshot to a real 2D MHD integration (numpy, MPI domain-decomposed when mpi4py is present). Tier 8 MHD diagnostics (`t8_mhd_field_ribbons`, `t8_conservation_budget`) are both native-promoted. The physics roadmap's library-integration goal is met; remaining Phase B items (B4 two-phase droplets, B6 MPM sand, B8 alfven-wave) are optional extensions.
> - `scripts/gen_physics_sim_recipes.py` generates all 5 Phase A recipes
>   (A1–A5) with full contract-correct `scene.json` (incl. `simulation` block),
>   OBJ/MTL, stdlib `preview.png`, READMEs.
> - `scripts/physics_fixture_io.py` + `tests/test_physics_fixture_io.py` provide
>   `.npz`/`.csv` loaders (NumPy fast path + stdlib fallback; 10 unit tests pass).
> - `examples/fixtures/README.md` + a committed `particles/dam-break-small.csv`
>   (1500 particles, 2 phases) establish the fixture boundary.
> - `benchmarks/spec.py` now has **Tier 7** (3 tasks: `t7_advection_diffusion_panels`,
>   `t7_cloth_drape_contact`, `t7_particle_splash_fixture`) — deterministic physics
>   grammar — plus **Tier 8** (2 tasks: `t8_mhd_field_ribbons`, `t8_conservation_budget`)
>   for MHD diagnostics carried by geometry. The active harness totals 17 tasks.
> - **Phase C started:** `simulation-frame-strip` (C1) is landed, offline-verified, and
>   promoted into the harness as **Tier 9** task `t9_simulation_frame_strip` (18 active
>   tasks total). It defines the canonical left-to-right frame-strip animation-preview
>   grammar (8 frames, one material group per frame, cool→warm time-axis ramp) from a
>   deterministic closed-form advection-diffusion pulse — no external simulator. Generator
>   `scripts/gen_simulation_frame_strip_recipe.py`; test `tests/test_frame_strip_recipe.py`.
>   The recipe is **native-promoted** (`native_octane_verified=true`) via the live Octane path.
> - **Phase C continued:** `conservation-budget-panels` (C2) is landed, offline-verified, and
>   **native-promoted**. It reuses the `t8_conservation_budget` MHD grammar as a standalone
>   recipe: kinetic/magnetic/internal energy bars across 9 Orszag-Tang timesteps (near-conservation)
>   plus a red relative-drift (error) panel, from a real MHD trace (`benchmarks.spec._orszag_tang_mhd`).
>   Generator `scripts/gen_conservation_budget_recipe.py`; test `tests/test_conservation_budget_recipe.py`.
>   Active harness total remains **18 tasks** (C2 is a recipe, not a new benchmark tier).
> - Offline suite green: `test_verify_recipes`, `test_recipes`, `test_benchmarks`
>   (17 active tasks), `test_physics_fixture_io`, `test_splishsplash_adapter`,
>   and `test_mpipymhd_adapter`.
> - **Phase B started:** SPlisHSPlasH-style dam-break adapter is landed, offline-verified, and native-promoted.
>   `scripts/gen_splishsplash_recipe.py` consumes the committed fixture
>   (`examples/fixtures/particles/dam-break-small/dam-break-small.csv`, 1500 particles)
>   via `physics_fixture_io.py` with NO runtime SPlisHSPlasH dependency, emits a
>   contract-clean recipe (`examples/recipes/dam-break-splash/`). Provenance is
>   embedded in the `simulation` block. Covered by `tests/test_splishsplash_adapter.py`.
> - Full focused suite green after live promotion and MPIPyMHD fixture addition
>   (`test_verify_recipes`, `test_recipes`, `test_benchmarks`,
>   `test_physics_fixture_io`, `test_splishsplash_adapter`,
>   `test_mpipymhd_adapter`; live gates still require `OCTANEX_LIVE=1`).
> - **Native render status:** Octane bridge/TCC/Scripts-menu issues are cleared for
>   this host. All five Phase A recipes plus `dam-break-splash` were rendered via
>   `benchmarks.verify_recipes --live --copy-back --drain-timeout 300`, passed
>   pixel acceptance, were visually inspected, and now have promoted
>   `octane-preview.png` files with `native_octane_verified=true`.
> - **Benchmark status:** Tier 7 benchmark tasks are native verified. Older
>   README-showcase-era benchmark tasks (`t2_bar_chart`, `t4_architecture_flow`,
>   `t5_math_surface_complex`, `t5_wave_interference`, `t6_earth_space`,
>   `t6_saturn_system`) were removed from active `ALL_TASKS` rather than carried as
>   stale gates.
> - **Real-library smoke layer added:** `scripts/run_physics_real_library_smokes.py`
>   records actual local simulator/runtime status alongside fixture-first tests.
>   Latest documented run: `docs/physics-real-library-smokes.md` — Oceananigans.jl
>   passed a real 5-step CPU `ShallowWaterModel`; SPlisHSPlasH, Genesis, and
>   MPIPyMHD are source-present but blocked by concrete local dependency/configure
>   issues.
> - **B2 real-export path added:**
>   `scripts/export_oceananigans_shallow_water_fixture.jl` runs the real local
>   Oceananigans `ShallowWaterModel`; the Python wrapper packages the CSV bundle
>   into `examples/fixtures/oceananigans/shallow-water-front/shallow-water-front.npz`
>   plus sidecar provenance, which is merged into the recipe `simulation` block.
> - **B7 real-integration adapter landed:** `scripts/export_mpipymhd_orszag_tang_fixture.py`
>   runs a genuine explicit 2D MHD integration (Orszag-Tang initial condition advanced
>   by a flux-based, minmod-limited scheme) and snapshots the evolved fields into a
>   deterministic `.npz` plus provenance sidecar. When `mpi4py`/OpenMPI is present it
>   domain-decomposes the grid across ranks via `Gatherv` (real distributed-MPI run,
>   `mpi_mode: domain_decomposed`); otherwise it falls back to a serial numpy run.
>   `scripts/gen_mpipymhd_orszag_tang_recipe.py` consumes the fixture into
>   `examples/recipes/mhd-orszag-tang-vortex/` with density/pressure surfaces,
>   magnetic/velocity arrow glyphs, explicit material bindings, and `simulation`
>   metadata. Covered by `tests/test_mpipymhd_adapter.py` (asserts `model` starts with
>   `Orszag-Tang MHD integration`; no mpi4py needed for the offline suite).
> - **Next:** B3–B6 adapters (additional SPlisHSPlasH/Genesis fixtures) should keep
>   the same fixture-first contract tests and include/refresh matching real-library
>   smoke evidence when the corresponding runtime is unblocked. The SPlisHSPlasH
>   `dam-break-splash` adapter added `scripts/export_splishsplash_dam_break_fixture.py`
>   with a real-run branch, but `pysplishsplash` is scene-XML driven: constructing
>   fluid/boundary models directly in Python **segfaults** on this binding (observed
>   SIGSEGV during `addFluidModel`/`init`), so the real branch is gated behind an
>   explicit `--scene-xml` and remains blocked until a valid scene file is authored.
>   The default path keeps the committed CSV fixture (deterministic, no solver).

**Goal:** Extend the OctaneX recipe and benchmark harness from static visualisation into a disciplined physical-simulation repertoire: fluids, particles, rigid/soft bodies, magnetohydrodynamics, numerical diagnostics, and simulation-to-render interchange.

**Architecture:** Keep OctaneX as the final visual renderer and the benchmark harness as the pixel-gated regression layer. Simulation libraries generate bounded, deterministic frame/state artifacts outside Octane, then thin adapter scripts convert those artifacts into combined OBJ geometry, material groups, scene metadata, preview PNGs, and optional animation frames. No recipe should depend on a long live simulation during normal verification; every checked-in recipe gets a small deterministic fixture.

**Tech stack:** Current repo `ObjBuilder` / `CombinedObj` / `benchmarks.acceptance`; local sources under `/Users/craig/src/`; optional external candidates such as PySPH, Taichi, REBOUND, Dedalus, FiPy, PyElastica, and Meep for later adapters.

---

## 1. Current state

The harness already has strong visual foundations:

- 17 active benchmark tasks in `benchmarks/spec.py::ALL_TASKS` (Tiers 1–8), all deterministic and pixel-gated.
- Existing physics-adjacent recipes:
  - `physics-orbits`: orbital paths and body positions.
  - `wave-interference-field`: two-source scalar heightfield.
  - `vector-field`: lifted 2D vector field arrows.
  - `earth-hemisphere` and `solid-earth-shells`: physically scaled geoscience cutaways.
  - `photoreal-earth-space`, `earth-moon-space`, `saturn-moons-space`: legacy space-scene staging retained as catalogue recipes, not active benchmark tasks.
- Existing recipe contract in `benchmarks/verify_recipes.py` requires `README.md`, `scene.obj`, `scene.mtl`, `scene.json`, a reference preview, valid command payloads, and honest `native_octane_verified` status.
- Known renderer/harness constraints:
  - multi-object scenes must be one combined OBJ with per-group materials;
  - OBJ/MTL colour alone is not enough, emit `create_material` and `assign_material`;
  - Octane may drop OBJ line primitives, so critical paths/arrows should become tubes, boxes, or mesh ribbons;
  - live rendering must flush the queue first and save through the bridge's actual preview path;
  - pixel QA is authoritative for gatekeeping, vision is supplementary only.

## 2. Local library inventory

Read-only inspection of the provided local paths produced this map:

| Local source | Relevant capability | Recipe value | Integration risk |
| --- | --- | --- | --- |
| `/Users/craig/src/Oceananigans.jl` | Julia finite-volume Boussinesq, nonhydrostatic/hydrostatic/shallow-water ocean dynamics on CPU/GPU | scalar fields, velocity slices, vorticity, free-surface/ocean-column scenes | Julia dependency and runtime cost; use exported NetCDF/JLD2 fixtures rather than live sim in normal tests |
| `/Users/craig/src/SPlisHSPlasH` | C++ SPH fluids, incompressibility solvers, viscosity, surface tension, vorticity, multi-phase, rigid/deformable coupling, VTK/partio export | particle-fluid splashes, dam break, two-phase droplets, foam/spray/bubble point clouds | build/runtime complexity; prefer precomputed small VTK/partio fixtures and Python/stdlib adapters |
| `/Users/craig/src/Genesis` | Python multi-physics platform: rigid, FEM, MPM, PBD/SPH particles, cloth, robotics, sensors; render paths include Nyx/Luisa/Pyrender | rigid-body stacks, robot contact, cloth drape, MPM sand/water, coupled systems | heavy GPU/backend stack; treat as an optional fixture producer and avoid importing Genesis in core repo tests |
| `/Users/craig/src/MPIPyMHD-Magnetohydrodynamics-Simulation-Framework` | Python MPI MHD with NumPy/SciPy; grid fields and magnetic dynamics | magnetic field lines, Orszag-Tang vortex, Alfvén wave, current-sheet reconnection | MPI/runtime dependency; start with serial small grids or saved `.npz` fixtures |
| `/Users/craig/src/y-cruncher v0.8.7.9547-static` | high-precision numerical computation | numerical-precision visualisations, convergence/error landscapes, digit/constant structure | not a physical simulator; useful for numerical-diagnostics recipes only |
| `/Users/craig/src/LuisaRender` | high-performance renderer and scene exporter, Metal backend possible | renderer comparison/interchange, material/path-tracing references | adjacent renderer, not a physics engine; use later for backend abstraction, not first-pass physics fixtures |

## 3. Design principles

1. **Fixture-first, simulation-second.** A recipe should load a deterministic fixture quickly. The expensive source simulator can be documented and scripted separately.
2. **Small canonical states.** Use 32-128 grid slices, 1k-20k particles, or 12-48 frames before attempting high-density native renders.
3. **Visible physical variable per material group.** Encode variable class explicitly: velocity, pressure, vorticity, density, temperature, magnetic-field strength, contact force, strain, etc.
4. **Geometry must carry the claim.** Use heightfields, glyphs, ribbons, shells, particles, contact patches, or stream tubes. Do not rely on labels alone.
5. **Acceptance must be physical enough to catch wrong subjects.** Combine `non_empty`, `review_ok`, `shape_profile`, `color_family`, and custom summary metadata checks where pixel-only criteria cannot see dynamics.
6. **Adapters are owned here; simulators are not.** Write scripts under `scripts/` that consume exported fixtures from local libraries. Do not vendor or modify external source repos.
7. **Every recipe gets a null/comparison hook.** Physical simulation recipes should include one falsification or comparison view where possible: inviscid vs viscous, stable vs unstable, low vs high Reynolds, no-field vs field, collision vs no-collision.

## 4. Proposed suite

### Phase A: Pure-harness deterministic physics fixtures

These require no external simulator and should land first because they harden the recipe contract.

| Priority | Slug | Scene | Physical claim | Geometry | Acceptance focus |
| --- | --- | --- | --- | --- | --- |
| A1 | `fluid-kelvin-helmholtz-slice` | Analytic Kelvin-Helmholtz-like scalar/vorticity slice | shear instability rolls from opposed layers | coloured heightfield + vorticity ribbons | two counter-rotating colour families, non-flat shape profile |
| A2 | `advection-diffusion-pulse` | Gaussian tracer pulse across four time panels | diffusion broadens and lowers peak | four tiled heightfields | left-to-right peak-height monotonic metadata + visible panels |
| A3 | `mass-spring-cloth-drape` | small cloth sheet over sphere using simple Verlet/PBD fixture | gravity + constraints produce sag and contact tenting | triangulated cloth mesh + rigid sphere | cloth above/around sphere, material contrast, silhouette rows |
| A4 | `rigid-stack-contact-forces` | falling/settled block stack with contact-force glyphs | load transfers down the stack | boxes + force arrows + contact heat patches | stacked vertical bounds + red/yellow contact families |
| A5 | `nbody-chaotic-divergence` | two nearly identical 3-body trajectories | sensitive dependence creates diverging paths | tube/ribbon trajectories + endpoint spheres | two path colours diverge from common start |

### Phase B: Local-source-backed fixture adapters

These connect the named local libraries to OctaneX without making core tests depend on their full runtime.

Real-library status is tracked separately in
[`physics-real-library-smokes.md`](physics-real-library-smokes.md). New physics
adapters should include both: (1) fixture-first unit/contract tests that run in
the normal suite, and (2) an optional real-library smoke result that records the
actual local simulator import/configure/run status.

| Priority | Slug | Source | Input fixture | Scene | Adapter output |
| --- | --- | --- | --- | --- | --- |
| B1 | `dam-break-splash` | SPlisHSPlasH-style fixture | committed particle CSV (`examples/fixtures/particles/dam-break-small/`) | SPH dam-break impact against a barrier | instanced spheres, wall, splash envelope, foam particles |
| B2 | `oceananigans-shallow-water-front` | Oceananigans.jl | committed 2D free-surface + velocity snapshot (`examples/fixtures/oceananigans/shallow-water-front/`) | shallow-water front/eddy interaction | surface mesh + arrows + coastline/bathymetry base |
| B3 | `oceananigans-convection-column` | Oceananigans.jl | small exported scalar/velocity slice | convective plumes in a stratified water column | OBJ heightfield, velocity glyphs, temperature colour groups |
| B4 | `splash-two-phase-droplets` | SPlisHSPlasH | two material particle classes | droplet mixing / surface tension | two particle colour families, translucent liquid material |
| B5 | `genesis-cloth-on-rigid` | Genesis | cloth vertex states + rigid body mesh | cloth drapes over a moving rigid object | cloth mesh frames, rigid mesh, contact markers |
| B6 | `genesis-mpm-sand-wheel` | Genesis | particle positions + wheel transform | granular material displaced by a wheel | sand particles + wheel mesh + displacement trail |
| B7 | `mhd-orszag-tang-vortex` | MPIPyMHD | real 2D MHD integration snapshot `.npz` (`examples/fixtures/mpipymhd/orszag-tang-vortex/`) | MHD vortex and compressed magnetic structures | density/pressure heightfields + magnetic/velocity arrow glyphs |
| B8 | `mhd-alfven-wave` | MPIPyMHD | 1D/2D wave field snapshots | propagating Alfvén wave | field-line ribbons + amplitude panels |

### Phase C: Simulation-to-render and numerical-diagnostics recipes

These are less about physical accuracy, more about harness capability and future backend abstraction.

| Priority | Slug | Source | Scene | Why it matters |
| --- | --- | --- | --- | --- |
| C1 | `simulation-frame-strip` | repo-native | 8 frame states laid out as a spatial strip | gives every simulator a standard animation-preview grammar |
| C2 | `conservation-budget-panels` | repo-native / y-cruncher-assisted | mass/energy/error budgets as 3D panels | makes simulation correctness visible, not just beautiful |
| C3 | `precision-error-landscape` | y-cruncher + Python | high-precision reference vs float32/float64 error surface | tests numerical-story visualisation and colour-family acceptance |
| C4 | `renderer-backend-comparison` | LuisaRender + OctaneX | same scene grammar rendered by two backends | supports later renderer-agnostic backend abstraction |
| C5 | `particle-export-interchange` | SPlisHSPlasH / Genesis | same particle cloud via CSV, VTK, partio-derived fixture | hardens import adapters and unit conversion metadata |

## 5. Recipe contract additions for physical simulation

Add a `simulation` block to `scene.json` for new physical recipes. Keep it optional so old recipes remain valid.

Recommended shape:

```json
{
  "simulation": {
    "source_library": "Oceananigans.jl",
    "source_path": "/Users/craig/src/Oceananigans.jl",
    "fixture": "fixtures/oceananigans/convection_column_t0008.npz",
    "physical_variables": ["temperature", "w_velocity", "vorticity"],
    "units": {"length": "m", "time": "s", "temperature": "K"},
    "scale_mapping": {
      "scene_units_per_meter": 0.05,
      "height_scale": 1.2,
      "vector_scale": 0.8
    },
    "time": {"frame": 8, "t_seconds": 1200.0},
    "null_model": "same grid with zero buoyancy flux",
    "limitations": ["downsampled 64x64 slice", "not a live solver verification"]
  }
}
```

Do not add this as a hard validator requirement until at least two recipes use it and the field shape has proven stable.

## 6. Adapter pattern

For each source-backed recipe, create one adapter script in `scripts/` and one recipe directory under `examples/recipes/`.

Adapter script responsibilities:

1. Load a small fixture from `examples/fixtures/<source>/<slug>/` or a user-specified exported simulator file.
2. Downsample deterministically.
3. Convert scalar fields to mesh/heightfield groups, vector fields to arrows/ribbons, particles to spheres or low-poly glyphs, and contacts/constraints to explicit markers.
4. Emit:
   - `scene.obj`
   - `scene.mtl`
   - `scene.json`
   - `preview.png`
   - `README.md`
   - optional `frames/scene_000.obj` etc. for animation strips
5. Verify OBJ indices before writing success.
6. Keep external runtime calls behind flags such as `--from-oceananigans-export`, never required for offline tests.

Implementation guidance:

- Reuse `ObjBuilder.add_surface`, `add_ellipsoid`, `add_arrow`, boxes, and cylinders where possible.
- For particles, prefer instanced sphere meshes with proven face-index checks. Use enough segments for close-up smoothness when the particle shape matters.
- For field lines, use tube/ribbon geometry, not OBJ `l` lines.
- For high-density data, commit a small fixture and document the command that regenerated it from the local source.

## 7. Benchmark harness extension

Do not immediately expand the canonical 18-task suite with every recipe. Add a new physical tier only after Phase A has at least three deterministic tasks.

Proposed benchmark additions:

| Tier | New task | Purpose | Build style |
| --- | --- | --- | --- |
| 7 | `t7_advection_diffusion_panels` | multi-panel scalar evolution | pure deterministic Python field |
| 7 | `t7_cloth_drape_contact` | deformable surface + rigid obstacle | small PBD fixture embedded in builder |
| 7 | `t7_particle_splash_fixture` | particle cloud import and material groups | checked-in small particle fixture |
| 8 | `t8_mhd_field_ribbons` | vector/tensor-field visual grammar | deterministic grid + ribbon mesh |
| 8 | `t8_conservation_budget` | physical correctness diagnostics | generated bars/surfaces from numeric budgets |

Acceptance criteria should remain pixel-only, but tests can also assert generated metadata invariants before render:

- particle count within expected range;
- vector glyph count equals sampled grid sites;
- frame count equals declared `simulation.time.frames`;
- scalar min/max in metadata matches fixture statistics;
- material assignments cover all `usemtl` groups.

## 8. Suggested external additions

These are worth considering after the local-source adapters prove the pattern:

| Library | Role | Why useful |
| --- | --- | --- |
| REBOUND | orbital/N-body dynamics | robust continuation of `physics-orbits`; easy Python fixtures |
| PySPH | Python SPH | simpler install path than SPlisHSPlasH for lightweight SPH fixtures |
| Taichi | GPU-friendly small physics demos | fast MPM/SPH/cloth examples with Python control |
| Dedalus | PDE/spectral fluids | high-quality instability/convection fields |
| FiPy | finite-volume PDEs | compact diffusion/reaction/advection fixtures |
| PyElastica | rods/soft-body dynamics | tendrils, fibers, biological/engineering structures |
| Meep | electromagnetic wave simulation | wave/field scenes adjacent to MHD and optics |
| OpenFOAM or Basilisk | CFD reference cases | higher-fidelity fluids later, heavier ops burden |

Add none of these to `pyproject.toml` core dependencies initially. If needed, create extras or external fixture-generation notes.

## 9. Implementation plan

### Task 1: Add Phase A deterministic generator scaffold

**Objective:** Create a reusable script for pure-harness physical recipes.

**Files:**
- Create: `scripts/gen_physics_sim_recipes.py`
- Create/modify: `examples/recipes/<phase-a-slug>/...`
- Test: `tests/test_verify_recipes.py` count update after recipes are added

**Steps:**
1. Implement helper functions for scalar panels, tube/ribbon paths, force arrows, and simple sphere particles using existing `ObjBuilder` style.
2. Generate `fluid-kelvin-helmholtz-slice` first.
3. Emit material commands with explicit `assign_material` per OBJ group.
4. Generate a deterministic `preview.png` using stdlib or the existing preview approach used by nearby scripts.
5. Run `PYTHONPATH= uv run python -m unittest tests.test_verify_recipes -v` and update expected counts honestly.

### Task 2: Add a physical simulation metadata convention

**Objective:** Document and test the optional `simulation` metadata shape.

**Files:**
- Modify: `docs/recipe-library.md`
- Modify: `examples/recipes/fluid-kelvin-helmholtz-slice/scene.json`
- Test: add lightweight assertions only if a stable helper is introduced

**Steps:**
1. Add a short section to `docs/recipe-library.md` describing the optional `simulation` block.
2. Include `source_library`, `physical_variables`, `units`, `scale_mapping`, `time`, and `limitations` in the new recipe.
3. Do not make old recipes fail for missing `simulation`.

### Task 3: Build source-backed fixture loader utilities

**Objective:** Prepare adapters without taking runtime dependencies on external libraries.

**Files:**
- Create: `scripts/physics_fixture_io.py`
- Create: `examples/fixtures/README.md`
- Test: new `unittest` module if helpers become non-trivial

**Steps:**
1. Support `.npz` grids and `.csv` particles first using stdlib + optional NumPy where already available in the active environment.
2. Keep VTK/partio/JLD2 support behind documented conversion commands until dependencies are confirmed.
3. Add explicit fixture provenance metadata.

### Task 4: Implement first Oceananigans adapter recipe

**Objective:** Convert one exported Oceananigans field slice into a rendered Octane recipe.

**Files:**
- Create: `scripts/gen_oceananigans_recipe.py`
- Create: `examples/recipes/oceananigans-convection-column/`
- Create: `examples/fixtures/oceananigans/convection-column/`

**Steps:**
1. Start from a tiny `.npz` fixture with temperature and vertical velocity arrays.
2. Emit temperature heightfield and velocity arrows.
3. Include provenance in README: generated from exported Oceananigans data, not a live solver run.
4. Verify contract offline.

### Task 5: Implement first particle fixture recipe

**Objective:** Establish the particle-cloud grammar before using SPlisHSPlasH or Genesis live exports.

**Files:**
- Create: `scripts/gen_particle_splash_recipe.py`
- Create: `examples/recipes/splash-dam-break-particles/`
- Create: `examples/fixtures/particles/dam-break-small.csv`

**Steps:**
1. Use a small CSV fixture with `x,y,z,phase,velocity` columns.
2. Convert particles to smooth enough spheres or compact glyphs.
3. Add wall/barrier geometry and foam/spray material families.
4. Add OBJ index verification because particle recipes are index-bug-prone.

### Task 6: Add benchmark Tier 7 only after recipes prove stable

**Objective:** Promote stable physical recipes into `benchmarks/spec.py` as deterministic tasks.

**Files:**
- Modify: `benchmarks/spec.py`
- Modify: `docs/benchmark-suite.md`
- Modify: `tests/test_benchmarks.py`

**Steps:**
1. Add `TIER_TITLES[7]`.
2. Add 2-3 `BenchmarkTask`s with deterministic builders.
3. Update `test_all_tasks_have_unique_slugs` expected count.
4. Run `PYTHONPATH= uv run python -m unittest tests.test_benchmarks -v`.

## 10. Testing and validation

Minimum checks for docs/plan-only changes:

```bash
PYTHONPATH= uv run python -m unittest tests.test_benchmarks tests.test_verify_recipes -v
```

Minimum checks after adding recipe directories:

```bash
PYTHONPATH= uv run python scripts/gen_physics_sim_recipes.py
PYTHONPATH= uv run python -m unittest tests.test_verify_recipes -v
PYTHONPATH= uv run python -m unittest tests.test_benchmarks -v
```

Minimum live checks before claiming native success:

```bash
PYTHONPATH= uv run octanex-mcp doctor
OCTANEX_LIVE=1 PYTHONPATH=scripts:. uv run python -m benchmarks.verify_recipes --live --copy-back --slug <slug> --drain-timeout 300
PYTHONPATH= uv run python -m unittest tests.test_verify_recipes -v
```

Do not mark `native_octane_verified=true` until a fresh native PNG passes pixel acceptance and is newer than its generated geometry.

## 11. Risks

| Risk | Mitigation |
| --- | --- |
| External simulators are heavy or unavailable in a fresh checkout | Commit tiny fixtures and keep simulator execution optional/documented |
| Physical scenes look like generic art rather than simulation output | Include variable legends, null/comparison panels, and physical metadata |
| Particle OBJ size explodes | Start with 1k-5k particles; downsample by physical class; use glyph LOD |
| VTK/partio/JLD2 readers add dependency sprawl | Convert externally to `.npz`/`.csv` first; defer native readers |
| Pixel QA misses semantic physics | Add metadata invariants in unit tests and use vision/eye review only as supplementary evidence |
| Bridge material binding silently fails | Always emit `create_material` + `assign_material` for every `usemtl` group |
| Animation ambitions outrun static recipe contract | Use frame-strip and selected keyframes first, then add full animation workflows |

## 12. Acceptance criteria for the suite

The physical simulation suite is usable when:

- at least five Phase A recipes pass the offline recipe contract;
- at least three local-source-backed recipes exist with committed tiny fixtures (`dam-break-splash`, `oceananigans-shallow-water-front`, and `mhd-orszag-tang-vortex`);
- every new physical recipe includes the optional `simulation` metadata block;
- every recipe has explicit material bindings and a reference preview;
- at least two recipes have native Octane previews promoted with fresh mtimes;
- `docs/recipe-library.md` has a Physical Simulation coverage section;
- Tier 7 benchmark tasks exist only after the recipe grammar is stable and pass `tests.test_benchmarks` offline.

## 13. Suggested next task

**Phase A, B, C1 (`simulation-frame-strip`), C2 (`conservation-budget-panels`), C3
(`precision-error-landscape`), C4 (`renderer-backend-comparison`), and C5
(`particle-export-interchange`) are landed + offline-verified + **native-promoted**
(18 active benchmark tasks; native Octane promotion done for all five Phase A, the four Phase B
library adapters — `dam-break-splash`, `genesis-cloth-on-rigid` (B5),
`mhd-orszag-tang-vortex`, `oceananigans-shallow-water-front` — plus all five Phase C recipes).**
The Phase C sweep is complete.
in priority order:

1. **Remaining Phase B optional extensions** (`oceananigans-convection-column` B3,
   `splash-two-phase-droplets` B4, `genesis-mpm-sand-wheel` B6, `mhd-alfven-wave` B8) only
   when the corresponding local runtime is unblocked — keep the fixture-first pattern:
   committed tiny fixture, adapter unit test, optional real-library smoke evidence, offline
   recipe-contract verification, and only then native Octane promotion.
2. **LuisaRender follow-up (from C4)**: reverse-engineer a valid LuisaRender scene SDL so the
   `renderer-backend-comparison` recipe gains a genuine second (non-OctaneX) render.