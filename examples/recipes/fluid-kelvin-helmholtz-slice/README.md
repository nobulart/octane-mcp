# Kelvin–Helmholtz Shear-Layer Slice

Show shear instability: two opposed horizontal layers (upper/lower tracer) roll into counter-rotating vortex tubes at the interface, the classic Kelvin–Helmholtz billow. Built from a deterministic analytic tanh/sin tracer field plus interface ribbons — no live solver required.

## Usage

1. Import `scene.obj` with `octane_import_geometry(path="examples/recipes/fluid-kelvin-helmholtz-slice/scene.obj", name="fluid_kelvin_helmholtz_slice")`.
2. Create + assign materials per `usemtl` group (see table).
3. Set camera, lighting, then `octane_save_preview`.

Regenerate the geometry + metadata with:

```bash
PYTHONPATH= uv run python scripts/gen_physics_sim_recipes.py
```

## Material groups

| material-order | material | kind | color |
| --- | --- | --- | --- |
| 1 | `kh_base` | glossy | `[0.07, 0.08, 0.1]` |
| 2 | `kh_tracer` | glossy | `[0.12, 0.55, 0.92]` |
| 3 | `kh_vort_up` | glossy | `[0.95, 0.45, 0.12]` |
| 4 | `kh_vort_dn` | glossy | `[0.95, 0.78, 0.12]` |

OBJ stats: 12624 vertices, max face index 12624 (indices valid).

Camera: position [22.04428, -26.330667, 17.657892] -> target [0.0, 0.0, -0.1], fov 42.0.

## Notes

- This is a **deterministic fixture-first** recipe: the physical state is computed in `scripts/gen_physics_sim_recipes.py` with no external simulator, so it reproduces identically offline.
- OBJ/MTL colours are not sufficient in Octane; the explicit `create_material` + `assign_material` commands in `scene.json` bind every group.
- `native_octane_verified` is `false` until a fresh native Octane preview is promoted.
