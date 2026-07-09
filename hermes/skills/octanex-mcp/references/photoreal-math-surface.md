# Photoreal mathematical 3D surface — reproduction

Goal prompt: *"Visualise a photorealistic mathematical 3D surface."*

## Outcome
Real Octane X render: `OctaneMCP/renders/math_surface.png` (1280×1280, ~327 KB), glossy bronze sinc+azimuthal-ridge surface, 40k verts / 79k tris, verified by full-frame pixel scan + `vision_analyze`.

## Pipeline (queue ALL in one live Octane session)
1. Generate the OBJ in Python — `scripts/gen_math_surface.py` (parametrised; single `usemtl` group → one material pin, no `group_index` needed). Copy into the container workspace `OctaneMCP/assets/` (sandboxed Octane only reads container FS).
2. MCP queue, in order:
   - `import_geometry` (obj, name `math_surface`)
   - `create_material` (glossy, color `[0.85,0.55,0.25]`, roughness 0.3)
   - `assign_material` (object `math_surface`, material `math_surface_mat`)
   - `set_camera` (fov 40, pos `[11,9,11]`, target `[0,0.5,0]`)
   - `set_lighting` (preset `soft_studio`)
   - `save_preview` (1280×1280, samples 512, min_samples 256)
3. Drain with the one-shot bridge (repeat the click until `queue/` is empty — see pitfall #2).
4. Wait 60–120 s; verify PNG.

## Signals / pitfalls (the load-bearing part)
1. **Do NOT restart Octane X between `import_geometry` and the save command.** Restart purges the in-memory scene; later commands then run against an empty scene → uniform gray frame `(243,243,243)`, ~16 KB. Restart Octane X only to reload a *patched bridge*, and do it *before* queueing any scene command. Cost one wasted blank render before this was learned.
2. **One-shot bridge drains the ENTIRE queue in one click** (verified live: an 8-command recipe rendered + saved from a single drain). Poll `queue/` once after the click; it should be empty. The old "1 command per click" note was wrong for the current oneshot.
3. **`octane_run_oneshot_bridge` can throw `ClosedResourceError`** (transient MCP server blip). Reliable fallback: `from octanex_mcp.bridge_control import run_bridge_script; run_bridge_script("oneshot")` — it builds an AppleScript that **clicks the script from Octane's Script menu** (singular "Script"; runs it as Lua). Do NOT use `osascript -e 'tell app "Octane X" to run script file …'` — that form compiles the Lua as AppleScript and dies with `-2741` ("Expected end of line, but found ="). The menu-click path returns `clicked hermes_bridge_oneshot.generated via Script`, rc 0.
4. **`set_render_resolution` logs non-fatal** `setPinValue failed pin=filmResolution/width/height/... (No pin ... in NT_FILM_SETTINGS)` but reports `ok=true`. Ignore.
5. **Container FS is slow & render is long.** After the save command drains, a 79k-tri surface @ 512 samples takes ~90 s before the PNG timestamp moves. Don't conclude failure early.
6. **`octane_record_recipe` MCP tool was absent** ("Unknown tool") in-session. Record recipes inline in `NOTES-*.md` / `docs/recipe-book.md` instead of blocking on it.
7. **Prefer generating the OBJ yourself over the black-box `octane_visualize_surface`** — full control of function/resolution/normals, and it sidesteps the MTL-ignored quirk (explicit material still required).
8. **`save_preview` `path` must be inside the Octane X container, not the repo tree.** Sandboxed Octane X (Mac App Store build) can only read/write inside `~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/...`. Pointing `path` at e.g. `/Users/craig/octanex-mcp/...` makes the render *run* but the save fail downstream (`saveImage3: number expected, got table` → command lands in `failed/`, no PNG). Fix: write to `…/OctaneMCP/renders/<name>.png`, then `cp` it into the repo. Confirmed by a wasted ultra render that produced a 0-byte repo file.

## Verify (don't trust a pretty thumbnail)
- PIL full-frame scan: real surface → brightness min ~60, max ~765, warm pixels `(255,235,179)` present; blank frame → min==mean==max ~729 and tiny file.
- `vision_analyze`: confirm curved surface with shading/depth, centered, well-framed.
