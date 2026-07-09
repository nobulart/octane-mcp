# Green Chess Pawn on a Studio Chessboard

A **green glossy chess pawn** standing on an 8×8 **chessboard** under soft
studio lighting. The combined `scene.obj` (10,152 verts) carries three `usemtl`
groups in fixed order, so each material binds by 1-based `group_index`:

| group_index | group     | role              | material            |
|-------------|-----------|-------------------|---------------------|
| 1           | `cb_base` | dark board slab   | near-black glossy   |
| 2           | `cb_light`| cream light squares| warm cream glossy  |
| 3           | `pawn`    | the pawn          | green glossy        |

The render target exposes a single mesh pin, so a multi-object hero shot must
live in one combined OBJ with one group per material — `assign_material` with
`group_index` (in `scene.json` / `fix_recipe_materials.py` style) is the
canonical way to bind them.

## Run

```bash
hermes mcp call octanex octane_queue_recipe --slug green-pawn-board
```

## Notes

- Light squares render as a warm cream (~`[0.86, 0.83, 0.74]`), not white; the
  studio floor is brighter than the lit squares, so a naive "light floor" pixel
  check fails — verify the checkerboard via a horizontal scan-line transition
  count instead (see `scripts/verify_board_preview.py`).
- `octane-preview.png` is the native Octane render. Usable convergence ~30 s; a
  256-spp pass ran ~4 min for a fully clean frame.
- The board OBJ is regenerable with `scripts/gen_pawn_on_board.py`.
