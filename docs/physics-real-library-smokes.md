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
| SPlisHSPlasH | `/Users/craig/src/SPlisHSPlasH` | blocked | `pysplishsplash` is not installed. Bounded CMake configure of the real source tree failed: `Could NOT find Eigen3 (missing: EIGEN3_VERSION_OK) (Required is at least version "2.91.0")`; CMake reported Homebrew Eigen at `/opt/homebrew/include/eigen3` but did not parse an acceptable version. |
| Genesis | `/Users/craig/src/Genesis` | blocked | Source-path import failed before any simulation: `ModuleNotFoundError: No module named 'quadrants'`. |
| MPIPyMHD | `/Users/craig/src/MPIPyMHD-Magnetohydrodynamics-Simulation-Framework` | blocked | Source-context import failed before MPI smoke: `ModuleNotFoundError: No module named 'mpi4py'`. |

## Relationship to fixture-first tests

Fixture-first recipe tests assert the stable adapter boundary:

- committed fixtures can be loaded without importing heavyweight simulator runtimes,
- generated `scene.json` files pass the recipe contract,
- provenance metadata records the source library and fixture hash,
- render grammar remains stable for OctaneX promotion.

Real-library smokes assert the external source/runtime state when available:

- Oceananigans currently has a working local Julia runtime smoke,
- SPlisHSPlasH needs either a working `pysplishsplash` install or a fixed CMake/Eigen configuration,
- Genesis needs its Python dependency stack installed, beginning with `quadrants`,
- MPIPyMHD needs `mpi4py` installed in the Python used by the probe.

## Next unblockers

1. **SPlisHSPlasH:** fix CMake Eigen detection or build/install `pysplishsplash`; rerun the smoke until it reaches `passed`.
2. **Genesis:** install/sync the Genesis environment from its `pyproject.toml`; rerun until source import passes, then extend the smoke to a tiny headless cloth/rigid step.
3. **MPIPyMHD:** install `mpi4py` for the probe Python; rerun, then extend from import smoke to a tiny serial/MPI array scatter step.
4. **Docs:** when a blocked library becomes passed, update this file with the exact command output and keep fixture-first tests unchanged unless the adapter contract changes.
