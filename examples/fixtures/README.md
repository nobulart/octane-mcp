# Physical-simulation fixtures

This directory holds **small, committed, deterministic fixtures** that recipe
adapters consume. They are the boundary between heavy external simulators
(`/Users/craig/src/*`) and the OctaneX recipe pipeline.

## Rules

- Each fixture is a *tiny export* from a source simulator, not the simulator
  itself. The source library is never imported by the repo's tests.
- Loaders live in `scripts/physics_fixture_io.py` (stdlib `.csv` + `.npz`,
  with a NumPy fast path when available). No recipe depends on a live solver.
- Layout: `examples/fixtures/<source>/<slug>/<file>`.
- Recorded provenance (sha256, shape, loader) is embedded into each recipe's
  `simulation` block so the claim "generated from exported X data, not a live
  solver run" is verifiable.

## Sources tracked

| source dir | upstream | recipe(s) |
| --- | --- | --- |
| `oceananigans/` | Oceananigans.jl | `oceananigans-convection-column`, `oceananigans-shallow-water-front` (Phase B) |
| `splash/` | SPlisHSPlasH | `splash-dam-break-particles`, `splash-two-phase-droplets` (Phase B) |
| `genesis/` | Genesis | `genesis-cloth-on-rigid`, `genesis-mpm-sand-wheel` (Phase B) |
| `mhd/` | MPIPyMHD | `mhd-orszag-tang-vortex`, `mhd-alfven-wave` (Phase B) |
| `particles/` | (synthetic / SPlisHSPlasH-derived) | `dam-break-small/dam-break-small.csv` — dam-break splash fixture (1500 particles, liquid+foam phases); consumed by `scripts/gen_splishsplash_recipe.py` (Phase B adapter). |

## Generating a fixture from a source simulator (outside this repo)

```bash
# Oceananigans.jl -> npz (run inside the Julia project, export a 2-D slice)
#   using Oceananigans, JLD2, NPZ
#   ... run a short simulation ...
#   NPZ.write("examples/fixtures/oceananigans/convection-column/t0008.npz";
#             temperature=T_scalar[1, :, :], w_velocity=w[1, :, :])
#
# SPlisHSPlasH -> csv (convert a VTK/partio frame with a small helper)
#   x,y,z,phase,vx,vy,vz   # phase: 0 = liquid, 1 = foam/spray
```

Commit only the small exported file. Do NOT vendor or modify the upstream
source repos.
