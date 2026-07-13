# Photoreal Multi-Vase Studio

A product-studio recipe for five vases with intentionally varied silhouettes, colours, texture treatments, and material intent -- smoky glass, cobalt ceramic, ribbed terracotta, pearlescent white porcelain, and dark brushed metal.

![Native Octane render of the five-vase studio](octane-preview.png)

> **Note on the reference image.** `target-preview.png` (formerly `photoreal-preview.png`) is an **AI-generated target/reference** showing the intended look. It is **not** a native Octane render and must never be shown as the recipe's legitimate preview. The hero image above (`octane-preview.png`) is the real native render produced from this recipe's geometry.

## Geometry convention

The scene OBJ is authored **Y-up** (Octane's native world), so vases stand upright and the camera in `scene.json` uses true `[x, y, z]` coordinates. The previous release used a Z-up OBJ with a mismatched camera convention, which produced a broken native render.

## Material groups

| group_index | material | kind | color |
| --- | --- | --- | --- |
| 1 | `mat_stone_pedestal` | diffuse | `[0.52, 0.5, 0.46]` |
| 2 | `mat_warm_cyclorama` | diffuse | `[0.7, 0.64, 0.56]` |
| 3 | `mat_shadow` | diffuse | `[0.05, 0.05, 0.06]` |
| 4 | `mat_softbox` | diffuse | `[1.0, 0.97, 0.9]` |
| 5 | `mat_softbox` | diffuse | `[1.0, 0.97, 0.9]` |
| 6 | `mat_softbox` | diffuse | `[1.0, 0.97, 0.9]` |
| 7 | `mat_smoky_glass` | specular | `[0.22, 0.32, 0.36]` |
| 8 | `mat_cobalt_ceramic` | glossy | `[0.02, 0.12, 0.72]` |
| 9 | `mat_terracotta_ribbed` | diffuse | `[0.74, 0.3, 0.14]` |
| 10 | `mat_white_porcelain` | glossy | `[0.9, 0.86, 0.78]` |
| 11 | `mat_dark_brushed_metal` | metallic | `[0.08, 0.08, 0.09]` |

## Run

```bash
hermes mcp call octanex octane_queue_recipe --slug photoreal-vase-studio
```

## Regenerate

```bash
PYTHONPATH= uv run python scripts/gen_photoreal_vase_studio.py
```

## Notes

- The terracotta vase's ribbing is real geometry (sinusoidal radius modulation in the lathe), not a texture hint.
- OBJ/MTL colours are only hints; Octane colour correctness depends on the explicit `create_material` + `assign_material` commands in `scene.json`.
- Verify the native output via bridge result metadata plus an inspected `octane-preview.png`.
