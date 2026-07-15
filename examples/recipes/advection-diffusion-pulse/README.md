# Advection–Diffusion Pulse (4 Panels)

Show a Gaussian tracer pulse advected by a uniform flow while diffusing: each panel is a later time. The peak height drops and the pulse widens left-to-right — visible evidence of the diffusion term, not just translation. Deterministic closed-form solution, no solver required.

## Usage

1. Import `scene.obj` with `octane_import_geometry(path="examples/recipes/advection-diffusion-pulse/scene.obj", name="advection_diffusion_pulse")`.
2. Create + assign materials per `usemtl` group (see table).
3. Set camera, lighting, then `octane_save_preview`.

Regenerate the geometry + metadata with:

```bash
PYTHONPATH= uv run python scripts/gen_physics_sim_recipes.py
```

## Material groups

| material-order | material | kind | color |
| --- | --- | --- | --- |
| 1 | `ad_base` | glossy | `[0.06, 0.07, 0.09]` |
| 2 | `ad_panel_0` | glossy | `[0.15, 0.45, 0.95]` |
| 3 | `ad_panel_1` | glossy | `[0.2, 0.7, 0.85]` |
| 4 | `ad_panel_2` | glossy | `[0.45, 0.8, 0.45]` |
| 5 | `ad_panel_3` | glossy | `[0.85, 0.7, 0.25]` |

OBJ stats: 9224 vertices, max face index 9224 (indices valid).

Camera: position [36.65074, -43.777273, 29.474087] -> target [0.0, 0.0, -0.05012], fov 40.0.

## Notes

- This is a **deterministic fixture-first** recipe: the physical state is computed in `scripts/gen_physics_sim_recipes.py` with no external simulator, so it reproduces identically offline.
- OBJ/MTL colours are not sufficient in Octane; the explicit `create_material` + `assign_material` commands in `scene.json` bind every group.
- `native_octane_verified` is `false` until a fresh native Octane preview is promoted.
