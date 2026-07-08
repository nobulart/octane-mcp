# Multi-group colored mesh (e.g. green sphere on red cube)

Reproduction notes for rendering a single OBJ with several distinctly-colored
`usemtl` groups through octanex-mcp. Verified in one session; captured as a
recipe-book success entry.

## Key mechanics (why naive attempts fail)

1. **`import_geometry` ignores the OBJ's `.mtl` `Kd`.** Octane creates one
   material pin per `usemtl` group but leaves each with a default **black**
   material. Baking colors into a companion MTL produces a black render.
2. **`assign_material` paints every material pin with one material.** A
   combined mesh with group 1 (cube) + group 2 (sphere) needs two colors, so a
   single assign is wrong. The MCP `assign_material` tool schema has no
   `group_index`; inject it via raw queue JSON instead.
3. **`import_geometry` connects only the LAST imported mesh** to the render
   target. Use ONE combined OBJ for multi-part scenes.
4. **`octane.render.start{ maxSamples=… }` is silently invalid** on this Octane
   build → render runs unbounded, blocking the next `save_preview`
   ("Can't start a new render before finishing the previous render"). Bridge
   must `stop()`+`pause()` before `start` and bound via `wait_for_render_ready()`.
5. **Persistent bridge auto-poll timer is broken** → drain with the one-shot
   bridge.

## Sequence

1. Generate one combined OBJ (cube group written first = group 1, sphere second
   = group 2). Workspace path must live inside the sandbox container:
   `~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/assets/`.
2. Queue `import_geometry` (name + container path + format `obj`).
3. Write `create_material` command files (diffuse, explicit `color` RGB 0..1):
   ```json
   {"schema_version":"1.0","op":"create_material",
    "payload":{"name":"mat_red_cube","kind":"diffuse","color":[0.85,0.10,0.10]}}
   {"schema_version":"1.0","op":"create_material",
    "payload":{"name":"mat_green_sphere","kind":"diffuse","color":[0.10,0.80,0.20]}}
   ```
4. Write `assign_material` files with `group_index` (1-based, OBJ group order):
   ```json
   {"schema_version":"1.0","op":"assign_material",
    "payload":{"object_name":"green_sphere_red_cube","material_name":"mat_red_cube","group_index":1}}
   {"schema_version":"1.0","op":"assign_material",
    "payload":{"object_name":"green_sphere_red_cube","material_name":"mat_green_sphere","group_index":2}}
   ```
5. Queue `set_camera` / `set_lighting(soft_studio)` / `save_preview`
   (min_samples ~200, samples ~256, 1280x1280).
6. Drain via `octane_run_oneshot_bridge` (processes queue in timestamp order).

## Verification (objective)

```bash
env -u PYTHONPATH /tmp/pixcheck/bin/python scripts/verify_render_colors.py \
    --path renders/green_sphere_red_cube.png --step 2
```

Expected: red-dominant ~21% of pixels (reddest ~= (255,95,103)),
green-dominant ~4% (greenest ~= (2,175,110)). A naive box average over the
sphere's lit edge reads tan under warm studio light -- only the full-frame scan
is reliable.

## Bridge files patched (this session) — and WHERE the fix must live

The functions below were changed. **Edit them in the source templates + shared
lib, NOT in the `.generated.lua` files** — the generated files are gitignored
and overwritten by `octanex-mcp init`:

- `request_render_restart`: `stop()`+`pause()` before `start`; dropped invalid
  `maxSamples` key.
- `connect_material_to_mesh_pins(mesh, mat, group_index)` added (filters by
  group index; `connect_material_to_all_mesh_pins` now delegates to it with
  `nil`).
- `handle_assign_material` reads `cmd.group_index or cmd.payload.group_index`.

Edit locations (tracked, committed):
- templates: `octane_lua/hermes_bridge_persistent_v1.lua`,
  `octane_lua/hermes_bridge_oneshot_v2.lua`
- shared source: `octane_lua/lib/runtime.lua`, `octane_lua/lib/handlers.lua`

After editing the templates + lib: `uv run octanex-mcp init` regenerates the
gitignored `.generated.lua` files, then **restart Octane X** (it caches Lua in
memory). Commit only the template + lib edits.

> See SKILL.md "Bridge Source Architecture & Patching a Bridge Bug" for the full
> correct sequence and the anti-pattern (hand-editing a `.generated.lua` that is
> then clobbered by `init`).
