# N-Body Chaotic Divergence (3-Body)

Two near-identical three-body systems integrated from the same initial conditions except a 1e-3 velocity perturbation on one body. Their paths start together and visibly diverge — sensitive dependence on initial conditions. Deterministic symplectic integration, no live solver.

## Usage

1. Import `scene.obj` with `octane_import_geometry(path="examples/recipes/nbody-chaotic-divergence/scene.obj", name="nbody_chaotic_divergence")`.
2. Create + assign materials per `usemtl` group (see table).
3. Set camera, lighting, then `octane_save_preview`.

Regenerate the geometry + metadata with:

```bash
PYTHONPATH= uv run python scripts/gen_physics_sim_recipes.py
```

## Material groups

| material-order | material | kind | color |
| --- | --- | --- | --- |
| 1 | `nb_t0_b0` | glossy | `[0.95, 0.35, 0.3]` |
| 2 | `nb_t0_b1` | glossy | `[0.3, 0.75, 0.95]` |
| 3 | `nb_t0_b2` | glossy | `[0.55, 0.95, 0.45]` |
| 4 | `nb_t1_b0` | glossy | `[0.865, 0.44499999999999995, 0.41000000000000003]` |
| 5 | `nb_t1_b1` | glossy | `[0.41000000000000003, 0.7249999999999999, 0.865]` |
| 6 | `nb_t1_b2` | glossy | `[0.585, 0.865, 0.515]` |
| 7 | `nb_path_t0_b0` | glossy | `[0.95, 0.35, 0.3]` |
| 8 | `nb_path_t0_b1` | glossy | `[0.3, 0.75, 0.95]` |
| 9 | `nb_path_t0_b2` | glossy | `[0.55, 0.95, 0.45]` |
| 10 | `nb_path_t1_b0` | glossy | `[0.865, 0.44499999999999995, 0.41000000000000003]` |
| 11 | `nb_path_t1_b1` | glossy | `[0.41000000000000003, 0.7249999999999999, 0.865]` |
| 12 | `nb_path_t1_b2` | glossy | `[0.585, 0.865, 0.515]` |

OBJ stats: 13434 vertices, max face index 13434 (indices valid).

Camera: position [7.217433, -6.801144, 4.863934] -> target [1.179446, 0.410896, 0.0], fov 45.0.

## Notes

- This is a **deterministic fixture-first** recipe: the physical state is computed in `scripts/gen_physics_sim_recipes.py` with no external simulator, so it reproduces identically offline.
- OBJ/MTL colours are not sufficient in Octane; the explicit `create_material` + `assign_material` commands in `scene.json` bind every group.
- `native_octane_verified` is `false` until a fresh native Octane preview is promoted.
