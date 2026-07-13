# Analog Wristwatch with Linked Metal Strap (two-tone)

![Native Octane X render](octane-preview.png)

A two-tone analog wristwatch: brushed-steel case, gold bezel and crown, deep-blue glossy dial, white radial hour markers, polished silver hour/minute hands pinned at the dial center, a red second hand with counterweight, and a linked steel/gold bracelet extending up and down from the lugs.

## Material groups

| order | material | kind | color |
| --- | --- | --- | --- |
| 1 | `mat_steel` | metallic | `[0.8, 0.82, 0.86]` |
| 2 | `mat_gold` | metallic | `[0.88, 0.71, 0.36]` |
| 3 | `mat_dial` | glossy | `[0.05, 0.13, 0.34]` |
| 4 | `mat_marker` | glossy | `[0.95, 0.95, 0.91]` |
| 5 | `mat_hand` | metallic | `[0.92, 0.93, 0.95]` |
| 6 | `mat_second` | glossy | `[0.82, 0.07, 0.07]` |

## Run

```bash
hermes mcp call octanex octane_queue_recipe --slug wristwatch
```

Then drain Octane X via **Script -> `hermes_bridge_oneshot.generated`**; one click drains the full queue.
