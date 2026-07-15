# OctaneX MCP — Benchmark Suite & Testing Protocol

A progressive, machine-checkable visualisation benchmark used to *develop* the
Octane MCP bridge. Each task is a deterministic scene spec with pixel-based
acceptance criteria. When a task renders correctly and passes acceptance, it is
promoted into the native-Octane recipe book (`docs/recipe-book.md`) as a
reproducible, verified example.

> **Design principle: pixel truth, not model opinion.**
> A render is judged by decoded RGB pixels only (stdlib PNG reader in
> `octanex_mcp.review`). No vision model ever decides pass/fail — they have
> hallucinated empty frames as correct before (see the chess-pawn entry in
> `docs/recipe-book.md`). The vision model is allowed only as a *human-facing*
> caption, never as a gate.

---

## 1. Why this exists

The bridge improves with use, but "use" must be measurable. This suite gives us:

* **A regression net** — if a Lua/Python change breaks a tier, the offline
  tests fail immediately (OBJ generation, index integrity, acceptance logic,
  queue marshalling) without needing Octane.
* **A development ladder** — 21 tasks across 7 tiers, from a single glossy cube
  to a Saturn system and deterministic physical-simulation fixtures, each
  isolating one failure mode.
* **A verified recipe feeder** — successful live runs are dumped straight into
  `docs/recipe-book.md` with the exact command sequence, so future agents
  inherit working scenes instead of re-discovering them.

---

## 2. Architecture

```
benchmarks/
  spec.py        18 BenchmarkTask defs + deterministic build() per task.
                 Each build() returns a combined-OBJ scene spec with materials,
                 per-group assignments, camera, lighting, save, acceptance.
  acceptance.py  Pixel-level checks (non_empty, review_ok, color_present/absent,
                 color_family, shape_profile, bright_fraction, file_size). No PIL, no vision.
  harness.py     run_task() / run_tier() / run_all(): mirror OBJ into the
                 container, queue the full command sequence, drain the one-shot
                 bridge, poll for the PNG, evaluate acceptance, report.
tests/
  test_benchmarks.py  Offline always-run tests + live-gated (OCTANEX_LIVE=1).
conftest.py     Makes benchmarks/ and src/octanex_mcp importable under pytest.
```

### Render pipeline (what the harness drives)

```
spec.build()  ──►  combined OBJ (+materials, +per-group assignments)
   │
   ├─ mirror OBJ  ──►  <container>/assets/bench_<mesh>.obj   (pitfall #14)
   │
   ├─ queue  ──►  import_geometry → create_material ×N →
   │            assign_material(group_index) ×N → set_camera →
   │            set_lighting → save_preview(path)             (pitfall #9/#10)
   │
   ├─ drain  ──►  one-shot Lua bridge click, then poll queue empty (pitfall #18)
   │
   └─ verify ──►  decode PNG → acceptance.evaluate() → PASS/FAIL
```

**Single-mesh rule.** Octane connects one mesh per render target; the bridge
disconnects the previous mesh on each `import_geometry`. So multi-object scenes
must be **one combined OBJ** with per-group (`o`/`usemtl`) materials. This is
handled centrally by `CombinedObj` in `spec.py` so no task gets the off-by-one
face-index bug (#13/#19) that silently yields a blank frame.

---

## 3. Tiers (progressive complexity)

| Tier | Name | Tasks | What it isolates |
|------|------|-------|------------------|
| 1 | Foundations | `t1_glossy_cube`, `t1_metallic_sphere`, `t1_surface_field` | Single primitive smoke test; material + iso camera; empty-frame detection. |
| 2 | Composition & framing | `t2_bar_chart`, `t2_multi_material`, `t2_scatter` | Multiple meshes, per-group material assignment, camera framing of multi-object bounds. |
| 3 | Lighting & materials | `t3_glass_like`, `t3_emissive`, `t3_product_studio` | PBR transmission/ior/opacity, emissive glow, cyclorama product shot. |
| 4 | Multi-object scene graphs | `t4_architecture_flow`, `t4_network_graph`, `t4_annotated_diagram` | 6–12 meshes, hierarchy, flow arrows; e.g. the MCP pipeline as a scene. |
| 5 | Data & math | `t5_math_surface_complex`, `t5_wave_interference`, `t5_vector_field` | Dense surfaces (60×60), two-source interference, rotational vector field. |
| 6 | Photoreal / stress | `t6_vase_studio`, `t6_earth_space`, `t6_saturn_system` | High face counts, multi-material families, translucent shells, oblate bodies. |
| 7 | Physical simulation fixtures | `t7_advection_diffusion_panels`, `t7_cloth_drape_contact`, `t7_particle_splash_fixture` | Deterministic physics grammar: advection–diffusion panels, PBD cloth drape, seeded particle splash. Offline-verified; native render pending. |

21 tasks total. Each is enumerated in `benchmarks/spec.py::ALL_TASKS`.

---

## 4. Acceptance criteria (pixel-based)

Defined per task in its `acceptance` list. Kinds:

* **non_empty** — `min_mean_dev` + `min_nonbg`%: frame is not black/empty.
* **review_ok** — uses `octanex_mcp.review.review_preview()` diagnostics; fails
  on named issues (`mostly near-black`, `likely object too small`, …).
* **color_present** / **color_absent** — fraction of pixels within `tol` of a
  target RGB (0–1). Confirms the right material colour actually rendered.
* **shape_profile** — number of rows containing silhouette structure (rejects
  featureless blobs).
* **bright_fraction** — `min_near_white`% for emissive/clipped highlights.
* **file_size** — guards against a 0-byte / corrupt PNG.

All checks run on decoded pixels only. A task passes only when **every**
criterion passes.

---

## 5. Running the suite

> The test file is **pure `unittest`** (the project has no `pytest` dependency).
> Run it with `python -m unittest`, not `pytest`.

### Offline (fast, no Octane — runs in CI / pre-render)
```bash
PYTHONPATH= uv run python -m unittest tests.test_benchmarks -v
```
Validates: spec determinism, OBJ index integrity for all 21 tasks, the
`CombinedObj` offset logic, acceptance logic on synthetic PNGs, and the
harness mirror+queue side-effects against a fake container.

### Live (needs Octane X running + container mounted)
```bash
# Tier 1-2 smoke + framing (bounded; ~3-6 min depending on samples)
OCTANEX_LIVE=1 uv run python -m unittest tests.test_benchmarks -v -k live

# A single task
OCTANEX_LIVE=1 uv run python -c "
from benchmarks.harness import run_task
from benchmarks.spec import get_task
r = run_task(get_task('t1_glossy_cube'), drain=True, drain_timeout=120)
print(r.as_dict())
"
```

### Whole-suite live run (long; Tier 6 uses `ultra` quality)
```bash
OCTANEX_LIVE=1 uv run python -m unittest tests.test_benchmarks -v -k live  # all tiers
```
Use `harness.run_all(tiers=[...])` from Python for custom subsets.

---

## 5b. Live status (recorded results)

| Tier | Task | Native Octane | Notes |
|------|------|---------------|-------|
| 1 | `t1_glossy_cube` | ✅ verified | `soft_studio`, PASS on pixels. |
| 1 | `t1_metallic_sphere` | ✅ verified | `metallic=1.0` renders silvery (no env map); fixed to `metallic=0.55` → reads gold. `color_family` criterion. |
| 1 | `t1_surface_field` | ✅ verified | `sin(r)/r` radial bronze surface. |
| 2 | `t2_bar_chart` | ✅ verified | 5 cyan bars, single combined OBJ. |
| 2 | `t2_multi_material` | ✅ verified | red cube + green sphere (two groups). |
| 2 | `t2_scatter` | ✅ verified | orange points in 3D space. |
| 3 | `t3_glass_like` | ✅ verified | transmission/ior/opacity sphere. |
| 3 | `t3_emissive` | ✅ verified | chromatic cyan+amber rim glow; `bright_fraction.min_near_white` 3.0→0.5. |
| 3 | `t3_product_studio` | ✅ verified | cyclorama + clearcoat red hero; `color_family` red. |
| 4 | `t4_architecture_flow` | ✅ verified | User/Agent/Queue/Octane blocks + flow arrows; `color_family` blue. |
| 4 | `t4_network_graph` | ✅ verified | 6 nodes / 8 edges spatial graph (vision-confirmed). |
| 4 | `t4_annotated_diagram` | ✅ verified | labelled diagram primitives. |
| 5 | `t5_math_surface_complex` | ✅ verified | z=f(x,y) surface; `shape_profile` 37 rows. |
| 5 | `t5_wave_interference` | ✅ verified | teal interference surface; `color_family` teal. |
| 5 | `t5_vector_field` | ✅ verified | 15 orange arrow glyphs; `color_family` orange. |
| 6 | `t6_vase_studio` | ✅ verified | three vases on studio cyclorama. |
| 6 | `t6_earth_space` | ✅ verified | blue Earth + atmosphere rim in space; `color_family` blue. |
| 6 | `t6_saturn_system` | ✅ verified | planet + ring + moon. |
| 7 | `t7_advection_diffusion_panels` | ✅ verified | 4-panel tracer, peak-decay + broadening; `color_family` teal + `shape_profile`. |
| 7 | `t7_cloth_drape_contact` | ✅ verified | PBD cloth draped over sphere; corrected gravity axis + fresh mesh name avoids stale import collision. |
| 7 | `t7_particle_splash_fixture` | ✅ verified | seeded liquid + foam particle families; dual `color_family` criteria. |

**21/21 Tier 1–7 tasks render natively and pass pixel acceptance. Tier 7 was verified live on 2026-07-15; recipe promotion remains tracked separately from benchmark-task verification.**

**Lessons (also in `docs/recipe-book.md`):**
* **Deferred render start is the current protection against render-restart
  collisions.** Scene-assembly handlers wire the render target with
  `do_start=false`; only `save_preview` starts the render after camera, geometry,
  materials, and lighting are present. Keep a full pipeline in one queue and use
  one one-shot drain.
* `soft_studio` lighting is strongly cool-blue; exact-RGB `color_present` is the
  wrong gate for lit PBR — use `color_family` (hue-distance tolerant).
* `metallic=1.0` without an environment map does not read as its base colour.
* Emissive glow is chromatic, not white — tune `bright_fraction.min_near_white`
  down (~0.5) or add a luminance-based check.
* Queue must contain the COMPLETE command set (import + every material +
  assignment + camera + lighting + save); partially purged queues silently
  render neutral/blank.
* AppleScript launch uses Octane X's **Script** menu (singular). It requires
  Accessibility for the Hermes agent-runtime Python, not `Hermes.app`; a single
  `octane_run_oneshot_bridge` click drains the full queue. The persistent bridge
  timer is not a reliable auto-drain path.

---

## 6. Developer workflow (using the suite to improve the bridge)

1. **Pick a failing task** (offline parity first, then the live run that fails
   acceptance).
2. **Read its spec** in `benchmarks/spec.py` — the OBJ, materials, camera, and
   acceptance are fully spelled out.
3. **Reproduce** with the single-task live command above; inspect the PNG with
   `mcp__octanex__octane_review_preview` (pixel QA) and, for *human* context
   only, the vision model.
4. **Fix the bridge** (Lua handler, `visuals.py`, schema) and re-run that one task.
5. **Promote on success**: append a compact entry to `docs/recipe-book.md`
   (title, outcome, context, steps, signals, follow_ups) and flip
   `BenchmarkTask.native_octane_verified = True`. The recipe is now part of the
   verified corpus for future agents.

---

## 7. Pitfalls encoded into the harness

These known bridge bugs are explicitly defended against by the harness/spec so
they surface as test failures instead of silent blank frames:

* **#9 / #10** — `save_preview` must be the *final* op; never also emit
  `start_render` before it (we only queue `save_preview`).
* **#13 / #19** — combined-OBJ face indices must be globally offset; validated
  by `harness._validate_obj_indices` and exercised in the offline tests.
* **#14** — OBJ is mirrored into the container `assets/` because Octane cannot
  read host repo paths; `import_geometry` receives the container path.
* **#18** — one-shot bridge drains the queue (used for full end-to-end capture)
  rather than the persistent bridge that returns early.
* **#20** — `assign_material` passes `group_index` at the top level so the Lua
  handler picks the right `o` group.

---

## 8. Extending the suite

Add a `BenchmarkTask` to `benchmarks/spec.py::ALL_TASKS` with a deterministic
`build()` that returns the spec contract (see module docstring). Keep the
acceptance criteria pixel-based. The offline tests auto-cover any new slug; the
live gate picks it up by tier. Record the new task's design intent in this doc's
tier table if it isolates a new failure mode.
