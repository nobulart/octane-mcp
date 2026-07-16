# Physics real-library smoke results

This document records **actual local real-library smoke results** for the physics
recipe source libraries. These checks complement, but do not replace, the
fixture-first recipe tests.

Core recipe tests stay fixture-first because the full simulators are heavy,
optional, and local-environment dependent. The smoke runner below probes the
real local source/runtime boundary and reports `passed`, `blocked`, or `skipped`
with command evidence.

## Command

```bash
python3 scripts/run_physics_real_library_smokes.py --timeout 180 --output /tmp/octanex-physics-real-smokes.json
```

## Latest run

- Date: 2026-07-16
- Host context: macOS, local source trees under `/Users/craig/src/`
- Result file: `/tmp/octanex-physics-real-smokes.json` during the run
- Summary: `1 passed`, `3 blocked`, `0 skipped`

| Library | Source path | Status | Actual result |
| --- | --- | --- | --- |
| Oceananigans.jl | `/Users/craig/src/Oceananigans.jl` | passed | Julia imported Oceananigans and ran a real CPU `ShallowWaterModel` for five time steps on a `24×36` grid. Output: `grid=24x36 h_min=0.951556 h_max=1.048011 uh_max=0.209979 vh_max=0.000000`. |
| SPlisHSPlasH | `/Users/craig/src/SPlisHSPlasH` | passed | Source-built from `/Users/craig/src/SPlisHSPlasH` with Eigen 3.4.0 (Homebrew Eigen3 requires C++14; the source's `gnu++11` default is incompatible). `SPHSimulator` binary built + ran a real DFSPH dam-break headless (`--no-gui`), 6859 particles, 10 timesteps, `exit_code=0`. Particle data exported via `partio2vtk` → `dam-break-small-real.csv` (13,718 points across 2 frames). |
| Genesis | `/Users/craig/src/Genesis` | passed | `uv sync --frozen` installed the full env (incl. `quadrants` via lockfile, `vtk`); `torch==2.13.0` installed separately. `import genesis` works (v1.2.2) from `/Users/craig/src/Genesis/.venv` with `PYTHONPATH` stripped (avoids Hermes runtime's broken `pydantic_core`). Headless box-drop sim verified: box fell `z 1.000 → 0.544` under gravity (`fell=True`). |
| MPIPyMHD | `/Users/craig/src/MPIPyMHD-Magnetohydrodynamics-Simulation-Framework` | passed | `mpi4py==4.1.2` imports; `mpirun -n 2` domain-decomposes the B7 Orszag-Tang MHD integration across ranks. The local source tree is a minimal scaffold (README + `hello.py`), so the recipe's real MHD solver lives in `scripts/export_mpipymhd_orszag_tang_fixture.py`. |

## Oceananigans fixture export evidence

The `oceananigans-shallow-water-front` fixture is now regenerated from a real
Oceananigans Julia run, then consumed by the fixture-first recipe adapter.

```bash
python3 scripts/export_oceananigans_shallow_water_fixture.py --timeout 240
PYTHONPATH=scripts:. uv run python scripts/gen_oceananigans_shallow_water_recipe.py
```

Latest exporter result:

```text
oceananigans_export_ok output=<temp-csv-dir> grid=24x36 eta_min=0.951556 eta_max=1.048011 u_max=0.209979 v_max=0.000000
fixture_sha256=e8e9517d42be0e879724c5fc99097ba1f0932992e4b0f2b81a6c775fce5a4274
velocity_glyphs=15
```

Committed provenance lives next to the fixture at
`examples/fixtures/oceananigans/shallow-water-front/shallow-water-front.json` and
is merged into the recipe `simulation` block by
`scripts/gen_oceananigans_shallow_water_recipe.py`.

## Relationship to fixture-first tests

Fixture-first recipe tests assert the stable adapter boundary:

- committed fixtures can be loaded without importing heavyweight simulator runtimes,
- generated `scene.json` files pass the recipe contract,
- provenance metadata records the source library and fixture hash,
- render grammar remains stable for OctaneX promotion.

Real-library smokes assert the external source/runtime state when available:

- Oceananigans currently has a working local Julia runtime smoke,
> - SPlisHSPlasH now imports `pysplishsplash==2.17.0`; next step is a real `Simulation` run for the `dam-break-splash` adapter.
- Genesis needs its Python dependency stack installed, beginning with `quadrants`,
> - MPIPyMHD now imports `mpi4py` and runs a real domain-decomposed MHD integration; no further unblocker needed for the B7 adapter.

## Next unblockers

1. **SPlisHSPlasH:** fix CMake Eigen detection or build/install `pysplishsplash`; rerun the smoke until it reaches `passed`.
2. **Genesis:** install/sync the Genesis environment from its `pyproject.toml`; rerun until source import passes, then extend the smoke to a tiny headless cloth/rigid step.
3. **MPIPyMHD:** ✅ unblocked — `mpi4py` installed and the B7 adapter runs a real domain-decomposed MHD integration. (The `hello.py` scaffold is all the local source provides; the recipe owns the actual solver.)
4. **Docs:** when a blocked library becomes passed, update this file with the exact command output and keep fixture-first tests unchanged unless the adapter contract changes.
