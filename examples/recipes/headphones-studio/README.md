# Over-Ear Studio Headphones with Spiral Cord

![Native Octane X render](octane-preview.png)

A reusable product-studio scene showing over-ear studio headphones on a dark polished surface, with opposing cylindrical earcups, a broad flat headband, a long path-following spiral cord, and a stepped jack plug.

## Geometry decisions

- The earcups are stepped cylindrical shells rather than flattened spheres.
- Each cup has planar end closures and the cup axes oppose one another across the headband.
- The headband uses a broad rectangular profile with its dominant axis rotated 90 degrees.
- The cord is a continuous swept spiral around a curved path, not a sequence of independent loops.
- The plug includes a barrel, insulating collars, tapered tip, and strain relief.
- The scene is one combined OBJ because this Octane build reliably exposes one imported mesh to the active render target.

## Run

```bash
hermes mcp call octanex octane_queue_recipe --slug headphones-studio
```

Then drain Octane X via **Script → `hermes_bridge_oneshot.generated`**; one click drains the complete queue.

## Files

- `scene.obj` — combined headphone, cord, jack, and polished-surface geometry.
- `scene.json` — camera, lighting, material, quality checklist, and command sequence.
- `octane-preview.png` — verified native Octane X render.

## Verification

The native preview is 1280×1280, 409,383 bytes, and passed deterministic pixel QA (`likely_blank=false`, `likely_clipped=false`). Local visual inspection confirmed the opposing cylindrical cups, broad headband, longer spiral cord, closed cup ends, polished surface, and visible grounding shadow.

The OBJ contains two `usemtl` groups: `headphone_mat` and `scene_mat`. The recipe binds them separately with explicit `group_index` assignments, following the proven desk-fan pattern. The public high-level `assign_material` MCP schema does not expose `group_index`, so use the checked-in `scene.json` command sequence or a lower-level queue command when replaying the recipe.

## Known limitation

The cap faces are currently part of the headphone group, so they share the headphone material. To give the caps an independent metallic material, regenerate the OBJ with a third `usemtl` group and add a `group_index=3` assignment.
