# Green Chess Pawn (Studio)

A single photorealistic **green glossy chess pawn** under soft studio lighting,
generated from a lathed surface-of-revolution OBJ (`scene.obj`, 13,184 verts /
25,856 faces — not a primitive, so it is constructed by lathing a Catmull-Rom
silhouette profile).

## Run

```bash
# queue + render via the bridge (one-shot drains the queue and saves the preview)
hermes mcp call octanex octane_queue_recipe --slug green-pawn
# or drive it live: import_geometry -> create_material -> assign_material -> set_camera -> set_lighting -> save_preview
```

## Notes

- The pawn OBJ is a single `usemtl` group, so `assign_material` binds with no
  `group_index`. Without the explicit `create_material` + `assign_material` the
  pawn renders as Octane's default white/grey — materials must be wired, the
  bridge ignores OBJ/MTL colors.
- `octane-preview.png` is the native Octane render. Usable convergence lands by
  ~30 s; raise `samples` for a fully clean frame.
- The OBJ is also regenerable with `scripts/gen_pawn.py`.
