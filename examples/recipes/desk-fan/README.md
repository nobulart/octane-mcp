# Desk Fan with Cord and Plug

![Native Octane X render](octane-preview.png)

A stylised desk fan with three blue blades, a tubular front/back guard cage, stand/base, tubular black power cord, plug body, and two brass prongs under soft studio lighting.

The scene is a **single combined OBJ** with repeated `usemtl` groups for each modeled part. This preserves the one-mesh render-target constraint while letting `assign_material(group_index=...)` bind cage, blades, cord, plug, and metal details separately.

## Material groups

| material-order | material | kind | color |
| --- | --- | --- | --- |
| 1 | `mat_base` | glossy | `[0.1, 0.12, 0.14]` |
| 2 | `mat_stand` | metallic | `[0.7, 0.72, 0.74]` |
| 3 | `mat_motor` | glossy | `[0.12, 0.15, 0.18]` |
| 4 | `mat_cage` | metallic | `[0.62, 0.66, 0.7]` |
| 5 | `mat_blade` | glossy | `[0.2, 0.46, 0.88]` |
| 6 | `mat_hub` | metallic | `[0.93, 0.86, 0.54]` |
| 7 | `mat_cord` | glossy | `[0.015, 0.015, 0.018]` |
| 8 | `mat_prong` | metallic | `[0.9, 0.86, 0.72]` |

## Run

```bash
hermes mcp call octanex octane_queue_recipe --slug desk-fan
```

Then drain Octane X via **Script -> `hermes_bridge_oneshot.generated`**; one click drains the full queue.

## Verification

`octane-preview.png` is the native Octane X render from the 2026-07-13 rerender (shortened blades, live capture from the committed OBJ). Pixel QA reported a 1280x1280 PNG, 789,208 bytes, sampled non-background 93.06%, edge_std 28.54, and `likely_blank=false`. The preview mtime is newer than `scene.obj`. Visual inspection confirmed the fan, cage guard, shorter blue blades inside the cage, tubular cord, plug, and brass prongs are visible and in focus.

## Notes

- Regenerate geometry and metadata with `PYTHONPATH= uv run python scripts/gen_desk_fan.py`.
- The OBJ contains 82 `usemtl` groups; `scene.json` emits one `assign_material` per group index, including repeated materials for separate cage wires/tubes.
- The cage uses front and rear torus rings, radial wires, and depth ties; keep it as tubes, not flat strips or bead-only rings.
- The cord is intentionally modeled as a real tube after review; do not flatten it back into a rectangular strip.
- The scene sets a camera `focus_distance` because the first render showed thin-lens depth-of-field blur.
- OBJ/MTL colours are not sufficient in Octane; keep the explicit `create_material` + `assign_material` commands in `scene.json`.
