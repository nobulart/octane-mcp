# Simulation Frame Strip (8 frames)

Define the repo-native animation-preview grammar: a spatial strip of N discrete simulation states, one per frame, laid out left-to-right so a single static render communicates time evolution. Here the state is a closed-form advection-diffusion pulse (same field as the Phase A recipe) advanced through 8 evenly spaced time indices. Each frame is its own material group bound to a cool->warm ramp encoding the time axis. Deterministic and external-simulator-free, so it is the template every future per-frame export adapter maps onto.

## Frame grammar

This recipe is the canonical **animation-preview** layout for the suite:

- `frames`: a spatial strip laid out **left-to-right in increasing time**.
- one `usemtl` **group per frame**, each bound to its own material.
- a cool->warm colour **ramp encodes the time axis** (8 frames, t=0 cool -> t=T warm).
- a shared base slab anchors the composition.

Downstream per-frame export adapters (later Phase C / simulator exports) must emit exactly this layout so a single render communicates evolution.

## Usage

1. Import `scene.obj` with `octane_import_geometry(path="examples/recipes/simulation-frame-strip/scene.obj", name="simulation_frame_strip")`.
2. Create + assign materials per `usemtl` group (see table).
3. Set camera, lighting, then `octane_save_preview`.

Regenerate the geometry + metadata with:

```bash
PYTHONPATH=scripts:. uv run python scripts/gen_simulation_frame_strip_recipe.py
```

## Material groups

| material-order | material | kind | color |
| --- | --- | --- | --- |
| 1 | `frame_00` | glossy | `[0.15, 0.7, 0.95]` |
| 2 | `frame_01` | glossy | `[0.25, 0.6642857142857144, 0.85]` |
| 3 | `frame_02` | glossy | `[0.35, 0.6285714285714286, 0.75]` |
| 4 | `frame_03` | glossy | `[0.44999999999999996, 0.5928571428571429, 0.6499999999999999]` |
| 5 | `frame_04` | glossy | `[0.5499999999999999, 0.5571428571428572, 0.55]` |
| 6 | `frame_05` | glossy | `[0.65, 0.5214285714285715, 0.44999999999999996]` |
| 7 | `frame_06` | glossy | `[0.75, 0.48571428571428577, 0.35]` |
| 8 | `frame_07` | glossy | `[0.85, 0.45, 0.25]` |
| 9 | `strip_base` | diffuse | `[0.06, 0.07, 0.09]` |

OBJ stats: 4616 vertices, max face index 4616 (indices valid).

Camera: position [45.917202, -40.213603, 27.02077] -> target [12.25, 0.0, -0.100032], fov 40.0.

## Notes

- This is a **deterministic, repo-native** recipe: the physical state is computed in `scripts/gen_simulation_frame_strip_recipe.py` with no external simulator, so it reproduces identically offline.
- `native_octane_verified` is `false` until a fresh native Octane preview is promoted.
