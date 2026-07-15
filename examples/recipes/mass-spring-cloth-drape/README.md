# Mass-Spring Cloth Drape over a Sphere

A small cloth sheet solved with Verlet integration + distance constraints (PBD-style) drapes under gravity and tents over a rigid sphere. The sag and contact curvature are emergent from the solver, not sculpted. Deterministic, no external physics engine.

## Usage

1. Import `scene.obj` with `octane_import_geometry(path="examples/recipes/mass-spring-cloth-drape/scene.obj", name="mass_spring_cloth_drape")`.
2. Create + assign materials per `usemtl` group (see table).
3. Set camera, lighting, then `octane_save_preview`.

Regenerate the geometry + metadata with:

```bash
PYTHONPATH= uv run python scripts/gen_physics_sim_recipes.py
```

## Material groups

| material-order | material | kind | color |
| --- | --- | --- | --- |
| 1 | `cloth_sphere` | glossy | `[0.3, 0.32, 0.36]` |
| 2 | `cloth_sheet` | glossy | `[0.85, 0.3, 0.35]` |

OBJ stats: 1984 vertices, max face index 1984 (indices valid).

Camera: position [16.25165, -23.849191, 13.869006] -> target [-0.740483, -3.553032, 0.180899], fov 42.0.

## Notes

- This is a **deterministic fixture-first** recipe: the physical state is computed in `scripts/gen_physics_sim_recipes.py` with no external simulator, so it reproduces identically offline.
- OBJ/MTL colours are not sufficient in Octane; the explicit `create_material` + `assign_material` commands in `scene.json` bind every group.
- `native_octane_verified` is `false` until a fresh native Octane preview is promoted.
