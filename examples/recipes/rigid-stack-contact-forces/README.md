# Rigid Stack Contact Forces

A settled stack of blocks with contact-force glyphs between layers. The downward arrows thicken and shift red→yellow as load increases toward the base — the static load path. Deterministic geometric fixture; arrow scale encodes the computed contact magnitude.

## Usage

1. Import `scene.obj` with `octane_import_geometry(path="examples/recipes/rigid-stack-contact-forces/scene.obj", name="rigid_stack_contact_forces")`.
2. Create + assign materials per `usemtl` group (see table).
3. Set camera, lighting, then `octane_save_preview`.

Regenerate the geometry + metadata with:

```bash
PYTHONPATH= uv run python scripts/gen_physics_sim_recipes.py
```

## Material groups

| material-order | material | kind | color |
| --- | --- | --- | --- |
| 1 | `stack_block_0` | glossy | `[0.55, 0.58, 0.62]` |
| 2 | `stack_block_1` | glossy | `[0.5, 0.55, 0.62]` |
| 3 | `stack_block_2` | glossy | `[0.45, 0.55, 0.6]` |
| 4 | `stack_block_3` | glossy | `[0.4, 0.52, 0.58]` |
| 5 | `stack_block_4` | glossy | `[0.35, 0.5, 0.55]` |
| 6 | `stack_ground` | glossy | `[0.1, 0.11, 0.13]` |
| 7 | `contact_force_0` | glossy | `[0.95, 0.3, 0.12]` |
| 8 | `contact_force_1` | glossy | `[0.95, 0.41, 0.12]` |
| 9 | `contact_force_2` | glossy | `[0.95, 0.52, 0.12]` |
| 10 | `contact_force_3` | glossy | `[0.95, 0.63, 0.12]` |

OBJ stats: 132 vertices, max face index 132 (indices valid).

Camera: position [10.313739, -12.319188, 10.95829] -> target [0.0, 0.0, 2.65], fov 40.0.

## Notes

- This is a **deterministic fixture-first** recipe: the physical state is computed in `scripts/gen_physics_sim_recipes.py` with no external simulator, so it reproduces identically offline.
- OBJ/MTL colours are not sufficient in Octane; the explicit `create_material` + `assign_material` commands in `scene.json` bind every group.
- `native_octane_verified` is `false` until a fresh native Octane preview is promoted.
