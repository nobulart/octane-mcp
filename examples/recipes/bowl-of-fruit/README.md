# Bowl of Fruit (Studio)

A stylised ceramic bowl filled with glossy fruit: red apples, green apple/lime, orange citrus, lemon, grapes, banana, stems, and leaves under soft studio lighting.

The scene is a **single combined OBJ** with one `usemtl` group per material. This is the reliable pattern for multi-part still-life scenes because the Octane render target exposes one mesh pin; `assign_material` with `group_index` binds the colours.

## Material groups

| group_index | material | kind | color |
| --- | --- | --- | --- |
| 1 | `mat_table` | diffuse | `[0.42, 0.3, 0.22]` |
| 2 | `mat_bowl_ceramic` | glossy | `[0.88, 0.68, 0.46]` |
| 3 | `mat_bowl_highlight` | glossy | `[1.0, 0.83, 0.58]` |
| 4 | `mat_bowl_shadow` | glossy | `[0.54, 0.34, 0.2]` |
| 5 | `mat_red_apple` | glossy | `[0.82, 0.04, 0.03]` |
| 6 | `mat_green_apple` | glossy | `[0.36, 0.78, 0.13]` |
| 7 | `mat_orange` | glossy | `[1.0, 0.43, 0.05]` |
| 8 | `mat_yellow_lemon` | glossy | `[1.0, 0.88, 0.08]` |
| 9 | `mat_deep_red_apple` | glossy | `[0.62, 0.02, 0.035]` |
| 10 | `mat_lime` | glossy | `[0.56, 0.84, 0.1]` |
| 11 | `mat_grapes` | glossy | `[0.38, 0.05, 0.62]` |
| 12 | `mat_banana` | glossy | `[1.0, 0.76, 0.1]` |
| 13 | `mat_stem` | diffuse | `[0.18, 0.09, 0.035]` |
| 14 | `mat_stem` | diffuse | `[0.18, 0.09, 0.035]` |
| 15 | `mat_stem` | diffuse | `[0.18, 0.09, 0.035]` |
| 16 | `mat_leaf` | glossy | `[0.04, 0.42, 0.12]` |
| 17 | `mat_leaf` | glossy | `[0.04, 0.42, 0.12]` |

## Run

```bash
hermes mcp call octanex octane_queue_recipe --slug bowl-of-fruit
```

## Verification

`octane-preview.png` is the native Octane render from the refined persistent-bridge pass on 2026-07-12. Pixel QA reported a 1280×1280 PNG, 744,599 bytes, mean abs deviation 64.459, non-background 99.964%, contrast 74.227, and `likely_blank=false`. Native visual inspection confirmed it reads as a bowl of fruit.

## Notes

- Regenerate geometry and metadata with `PYTHONPATH= uv run python scripts/gen_bowl_of_fruit.py`.
- The banana is stylised from overlapping ellipsoids; it is readable but visibly segmented at close range.
- OBJ/MTL colours are not sufficient in Octane; keep the explicit `create_material` + `assign_material` commands in `scene.json`.
