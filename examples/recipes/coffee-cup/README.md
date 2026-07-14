# Designer Coffee Cup with Dark Black Brew and Rainbow Bubbles

![Native Octane X render](octane-preview.png)

An elegant designer coffee cup in warm off-white glazed ceramic: a hollow surface-of-revolution body with a swept-tube handle, standing on a wide matching saucer on a dark table. Inside, a near-black glossy coffee is studded with a few clear iridescent rainbow bubbles. Rendered with soft-studio lighting.

## Geometry convention

Authored **Y-up** (Octane native). The cup body is a true hollow lathe (outer wall + reversed-winding inner wall + rim annulus) so the interior and brew are visible from the slightly-above camera angle.

## Material groups

| order | material | kind | color |
| --- | --- | --- | --- |
| 1 | `mat_table` | diffuse | `[0.06, 0.05, 0.05]` |
| 2 | `mat_saucer` | glossy | `[0.88, 0.85, 0.8]` |
| 3 | `mat_cup` | glossy | `[0.93, 0.9, 0.83]` |
| 4 | `mat_brew` | glossy | `[0.02, 0.018, 0.015]` |
| 5 | `mat_bubble` | glossy | `[0.9, 0.9, 0.9]` |

## Run

```bash
hermes mcp call octanex octane_queue_recipe --slug coffee-cup
```

Then drain Octane X via **Script -> `hermes_bridge_oneshot.generated`**; one click drains the full queue.

## Pitfalls (learned 2026-07-14)

- **Drain wedge on cold-relaunched Octane.** The oneshot bridge WEDGES at
  `set_lighting`/`save_preview` when Octane was just relaunched. The Lua script
  blocks inside `octane.render.start{}` for the render duration, so any *extra*
  MCP click is ignored while it is busy and the queue never fully drains; the
  PNG write then races and produces a blank-white ~12 KB frame. **Reliable
  pattern:** exactly ONE bridge click per fresh Octane process, then POLL the
  disk for `coffee_cup_octane-preview.png` (up to ~120 s, `samples_done: 600`)
  WITHOUT re-clicking. Trust `bridge.log` `save_preview preview saved` + the PNG
  mtime, not `status.json` age (it lags).
- **Froth hides the black.** A pale froth/crema disc sitting above the dark brew
  disc reads as latte/cream and hides the near-black brew. Keep the dark brew
  disc unobscured.
- **Rainbow bubbles.** The OBJ importer collapses distinct `mat_bubble_N`
  `usemtl` names into ONE mesh pin, so per-bubble material nodes can't carry 7
  hues. Keep a single `mat_bubble` and bake each bubble's hue as a PER-VERTEX
  colour (`v x y z r g b`) — the importer applies vertex colour reliably.
