---
name: octanex-mcp
description: Use when configuring, testing, or operating the OctaneX MCP server from Hermes Agent, especially for queue draining, render-ready PNG previews, and local vision review loops.
version: 1.3.0
author: OctaneX MCP contributors
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [octanex, mcp, rendering, vision, lua-bridge]
    related_skills: [octane-viz, octanex-mcp-overview, octanex-mcp-review, octanex-visual-loop, octanex-module]
---

# OctaneX MCP

## Overview

OctaneX MCP lets Hermes Agent use Octane X as a local visual canvas. Hermes queues allow-listed JSON commands through the Python MCP server, Octane X runs the Lua bridge from `octane_lua/`, and results come back as command JSON plus PNG previews that can be reviewed with local vision.

> **Core mental model:** `MCP tool / write_command -> JSON file in queue/ -> Octane Lua bridge (run inside Octane X GUI) -> Octane scene -> optional PNG preview`. The Python MCP server does **not** directly control Octane's GUI. It writes safe command files; Octane executes them only after a Lua bridge script is running inside Octane X.

## When to Use

Use this skill when an agent needs to:

- configure a fresh Hermes/OctaneX MCP setup;
- queue and drain Octane scene commands;
- create a quick geometry/data/math visualization;
- trigger a PNG preview and review it locally;
- debug a queue that is not being picked up by Octane X.

Do not use this skill for arbitrary Lua execution. The bridge is intentionally an allow-listed command DSL.

## Setup Checklist

1. Initialize the repo and generated Lua scripts (from the repo root `/Users/craig/octanex-mcp`):

   ```bash
   cd /Users/craig/octanex-mcp
   uv run octanex-mcp init
   uv run octanex-mcp doctor
   ```

   Completion: `doctor` reports `Overall: ok`, the workspace, generated bridges, and the Octane X app path. (Verified: `doctor` checks the app bundle, lua dir, all workspace subdirs, and workspace writability.)

2. Register the MCP server with Hermes. The dedicated CLI command writes the
   `mcp_servers` block for you. (Note: an agent's automated `patch` of
   `~/.hermes/config.yaml` is blocked by the Hermes config guardrail, but
   `hermes config set` / `hermes mcp add` / manual edits are all fine.)

   ```bash
   hermes mcp add octanex --command /Users/craig/octanex-mcp/run_octanex_mcp.sh --connect-timeout 30
   ```

   `run_octanex_mcp.sh` does `exec env -u PYTHONPATH uv run --project /Users/craig/octanex-mcp octanex-mcp`.
   The `env -u PYTHONPATH` is **mandatory**: the Hermes agent runtime exports
   `PYTHONPATH=…/hermes-agent/venv/…` which would otherwise force the spawned server to load the Hermes
   venv's broken `pydantic_core` and crash with `RuntimeError: mcp package is not installed`. Under a clean
   env the project `.venv` (mcp 1.26.0) imports fine.

   Completion: `hermes mcp list` shows `octanex` (✓ enabled) and `hermes mcp test octanex`
   connects and enumerates the tools (currently **39** `octane_*` tools). MCP
   servers are discovered at startup, so start a new Hermes session (or use
   `/reload-mcp`) to use them.

   Equivalent `config.yaml` block (hand-edit or `hermes config set` — note
   `args` must be a real empty list, not the string `"[]"`):

   ```yaml
   mcp_servers:
     octanex:
       command: "/Users/craig/octanex-mcp/run_octanex_mcp.sh"
       args: []
       timeout: 180
       connect_timeout: 30
   ```

3. In Octane X Preferences, set **Scripts path** to this checkout's `octane_lua/` directory:

   ```text
   /Users/craig/octanex-mcp/octane_lua
   ```

   Completion: Octane X's Script menu shows `hermes_bridge_oneshot.generated` and `hermes_bridge_persistent.generated`. Restart Octane X if the scripts do not appear after changing the preference.

   > **If the Script menu is absent**, do NOT assume the preference is wrong first — without the Accessibility grant below you cannot even *inspect* the menu (every probe returns `-1719`), so the menu looks missing. Fix the permission, then re-check.

4. **macOS Accessibility for the process that runs `osascript` (launch prerequisite — the #1 fresh-setup blocker).** The bridge is launched by UI-scripting Octane X's Script menu via `osascript`, which the OctaneX MCP **server** spawns. macOS evaluates the Accessibility (TCC) entitlement on the *process whose descendant runs `osascript`* — for this project that is the **Hermes agent runtime**, NOT `Hermes.app` the GUI:

   - Process tree: the `octanex-mcp` server (`…/octanex-mcp/.venv/bin/python3`) is a child of `uv run` → `/Users/craig/.hermes/hermes-agent/venv/bin/python` (PID 924, the Hermes **agent runtime**). `Hermes.app` (the desktop GUI) is a *separate* process and is NOT in this chain.
   - **Grant Accessibility to `/Users/craig/.hermes/hermes-agent/venv/bin/python`** (the agent runtime binary), not `Hermes.app`. Adding `Hermes.app` alone will NOT clear `-1719` because the osascript caller is the runtime python.
   - If the binary is awkward to select in the TCC UI, grant Accessibility to the **Terminal** app you launch Hermes from as a fallback, or to the parent `uv`/shell — TCC walks up to the nearest granted ancestor of the osascript caller.
   - Verify: `osascript -e 'tell application "System Events" to tell process "Octane X" to get name of every menu bar item'` must return the menu list (incl. `"Script"`) instead of `-1719`.
   - On `-1719` the bridge now returns `tcc_blocked: true` with the exact fix instead of the old misleading `"script not found"` `-2700`.

   > **CORRECTED 2026-07-09 (this session):** the previously-documented target `Hermes.app` is wrong for this deployment — the MCP server runs under the agent-runtime python, so that binary (or its shell/terminal ancestor) must be granted Accessibility. A live `-1719` against a supposedly-granted `Hermes.app` is the tell.

## Standard Agent Loop

1. Verify the toolchain before any render:

   ```bash
   cd /Users/craig/octanex-mcp && uv run octanex-mcp doctor
   ```

   Also confirm Octane X is actually running — the GUI session is mandatory for a real render:

   ```bash
   pgrep -fl "Octane X" || echo "Octane X NOT running — ask the user to launch it"
   ```

2. Read status (via MCP once registered, or directly):

   ```text
   octane_status()
   ```

   Completion: note queue counts, bridge status (`commands.status.bridge_seen`), and workspace path. `app.app_exists` must be true and `commands.validation.ok` should be true before asking Octane to process queued commands.

3. Queue a scene, for example:

   ```text
   octane_visualize_bars(values=[3, 1, 4, 1, 5], name="pi_digits")
   ```

   Completion: command JSON files appear under the workspace queue. If the MCP layer is not yet registered, you can still write a real command file directly:

   ```bash
   cd /Users/craig/octanex-mcp
   uv run python -c "
   from octanex_mcp.bridge import Workspace, write_command
   ws = Workspace(); ws.ensure()
   res = write_command('ping', {'message': 'hello'}, ws)
   print('QUEUED', res['command_id'], res.get('path'))
   "
   ```

   This lands a real file in `~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/queue/`. The Lua bridge (run by the user in Octane X) drains it.

4. Drain the queue in Octane X.

   Prefer `hermes_bridge_oneshot.generated` for multi-command scene batches because it exits and lets Octane repaint. Use the persistent bridge only when you need an open window that keeps polling.

   **Preferred trigger (code path, handles TCC):** `drain_oneshot()` in `src/octanex_mcp/bridge_control.py` clicks Octane X's **Script** menu item (`hermes_bridge_oneshot.generated`) via System Events UI scripting and waits for the queue to drain. The MCP `octane_run_oneshot_bridge` tool calls this. It returns `{"ok": true}` on success or `{"tcc_blocked": true, "error": "-1719 ..."}` if macOS Accessibility is missing for `Hermes.app` (see Setup step 4).

   **Raw AppleScript fallback** (only if the MCP server is down):
   ```bash
   osascript -e 'tell application "System Events" to tell process "Octane X" to click menu item "hermes_bridge_oneshot.generated" of menu 1 of menu bar item "Script" of menu bar 1'
   ```
   The menu is named **"Script"** (singular), not "Scripts". Do **not** use `tell app "Octane X" to run script file ...` — that path is unreliable here; UI-script the menu item instead.

   **One click drains the ENTIRE queue** (the oneshot processes every queued command in timestamp order, then renders and returns). Do NOT loop "one click per command" — that was an outdated note. Poll `…/OctaneMCP/queue/` once after the click; it should be empty (verified live: an 8-command recipe rendered + saved in a single drain).

   Completion: queued commands move to `processed/` or `failed/`, and `results/*.json` records each outcome. Check `queue/` is empty, not just `processed_count` climbing.

5. Save a PNG preview. Pass a convergence tier via `quality` so the render
   stops at a time budget instead of running unbounded:

   ```text
   octane_save_preview(width=1280, height=1280, quality="standard")   # 30s cap
   octane_save_preview(quality="high")                                 # 60s
   octane_save_preview(quality="ultra")                                # 120s
   octane_save_preview(quality="final")                                # unbounded; 600s wall cap
   ```

   Tiers (defined in `models.QUALITY_TIERS`) set `max_render_time` +
   `timeout_seconds` + `min_samples` + `samples`. Raw `samples` /
   `min_samples` / `timeout_seconds` / `max_render_time` override the tier when
   given. On the wall-clock cap the current frame is saved best-effort. Because
   the GPU `maxRenderTime` pin is ignored (see gotchas), the real cap is
   `timeout_seconds` via `wait_for_render_ready`.

   Completion: the bridge restarts rendering, waits for render statistics (or
   the timeout) to become ready, then writes a PNG under `renders/`. Default
   path: `~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/renders/`. Run
   the one-shot bridge again after queueing the preview save.

6. Review the PNG locally:

   ```text
   octane_review_preview(path="/path/to/preview.png")
   ```

   Completion: use `ok`, `issues`, `metrics`, and recommended actions before claiming the visual result is good. `ok=true` means it passed QA; `likely_blank`/`likely_clipped`/low contrast means re-render.

## Local Vision Inspection (every rendered PNG)

SOUL.md mandates inspecting every rendered product before delivery. Use `vision_analyze`:

- Prefer the **native-vision path** when the active model is a local Ollama vision model (`qwen3-vl:32b`, `qwen3.6:35b-mlx`, `glm-ocr`) — fully local.
- Otherwise the **auxiliary vision model** (`glm-ocr:latest`) is used.

Pitfall (observed): the auxiliary backend **loops its answer** on open-ended questions and intermittently 404s on `.png`/base64. Workarounds:

- Downscale first: `sips -s format jpeg -Z 768 in.png --out small.jpg`, then point `vision_analyze` at `small.jpg`.
- Ask ONE tight factual question; **take only the first line** of the reply.

## Render Protocol (mandatory before any live render)

A non-clean Octane session is the root cause of blank / near-black / stale
renders. Before every live render (and between scenes), follow this exact
sequence (refined 2026-07-09 per operator guidance — the key addition is
**starting the lua command queue before each drain**):

1. **Check Octane X is running.** If not, `open -a "Octane X"`. Do not proceed
   without the GUI session.
2. **Reset the workspace to startup default** — UI-script `File → New` in Octane
   X (clears any in-memory scene from a prior run). AppleScript:
   `tell application "System Events" to tell process "Octane X" to click menu
   item "New" of menu 1 of menu bar item "File" of menu bar 1`.
3. **Start the renderer (lua command queue).** Ensure Octane's lua/command-queue
   listener is active (the persistent bridge window / render node is live) so
   queued commands will actually execute when drained.
4. **Flush any stale queue** with one one-shot bridge click (Script menu), even
   if you think the queue is empty. A leftover command from a prior run will
   otherwise execute against your fresh scene and corrupt it.
5. **Build the scene and queue the scene commands** (import → material → camera
   → light → render-start → save-preview).
6. **Start the renderer (lua command queue)** again — re-affirm the listener is
   active before processing this scene's commands.
7. **Process the queue** with another one-shot bridge click (Script menu). One
   click drains the ENTIRE queue, then renders.
8. **Return to step 2** for the next scene (reset → flush → build → drain). Do
   NOT pile scenes into one uncleared session.

> **Octane is fast:** basic scenes are acceptably converged for preview
> evaluation after only **1–2 s**; complex scenes after **5–10 s**. Do not set
> long `max_render_time`/`timeout_seconds` caps "to be safe" — they only delay
> the PNG and tempt an early "failed" conclusion. A short standard-tier save is
> sufficient for a QA pass; use high/ultra only when the preview genuinely needs
> more samples.

> **Pitfall — stale queue → near-black frame.** If a render comes back
> near-black (`mean_dev≈0`, triggers `mostly near-black`) with no obvious scene
> error, suspect a stale queue or leftover scene, NOT a material bug. Run steps
> 2–4 (reset + start queue + flush) and re-queue. The 2026-07-09 `avatar-guide`
> failure was exactly this: a stale scene + un-drained queue, not a recipe
> defect.

## Bridge Debugging

- If queue grows but nothing is processed, run the one-shot bridge from Octane X's Script menu or via the osascript trigger above.
- If `status.json` is stale, trust current queue/result files over old status.
- If preview save fails immediately after a scene mutation, use the current bridge templates: they call `render.restart()`, wait for `getRenderResultStatistics().beautySamplesPerPixel >= 16`, then `saveImage(path, PNG8)`.
- If geometry appears duplicated or stale, clear the Octane scene before re-importing. Octane appends imported geometry unless the node tree is flushed.
- Persistent bridge may leave the viewport stale (mode cycles active -> one_shot -> closed -> available). Prefer one-shot for batches.

## Materials, Import & Render-Restart Gotchas

These are the non-obvious failure modes that produce a black render or a
render that never finishes:

- **MTL `Kd` is IGNORED on `import_geometry`.** Octane creates one material pin
  per `usemtl` group but leaves each with a default **black** material. Baking
  colors into a companion `.mtl` file does nothing. You must `create_material`
  (diffuse, explicit `color`) and `assign_material` to the imported mesh.
- **Multi-group mesh = distinct colors requires `group_index`.** A single
  combined OBJ with several `usemtl` groups (e.g. a red cube + green sphere)
  has one material pin per group, but `assign_material` paints **all** pins with
  one material. The MCP `assign_material` tool schema does NOT expose
  `group_index`. Workaround: write the command file directly into
  `…/OctaneMCP/queue/` with `"payload": {"object_name": …, "material_name": …,
  "group_index": N}` where `N` is 1-based and matches OBJ group write order
  (the bridge's `connect_material_to_mesh_pins` filters by it).
- **`import_geometry` connects only the LAST imported mesh** to the render
  target, so earlier imports become orphaned. For multi-part scenes, emit ONE
  combined OBJ (all groups in one file) rather than several imports.
- **`maxSamples` is an INVALID key for `octane.render.start` on this Octane
  build.** Including it is silently ignored, so the render runs **unbounded**;
  the next `save_preview` is then rejected with *"Can't start a new render before
  finishing the previous render."* Bridge fix: `stop()` + `pause()` before
  `start`, and bound convergence by polling sample count via `wait_for_render_ready()`.
- **`maxRenderTime` (and `maxSamples`) GPU film pins are NOT honored on this
  Octane build** — confirmed live by a probe in `runtime.set_max_render_time`:
  every candidate pin (`P_MAX_RENDER_TIME`, `maxRenderTime`, `maxTime`,
  `maxRenderTimeSeconds`) returned falsy and produced no log line. The render
  does **not** auto-stop on a sample/time cap. The **effective convergence cap
  is the Lua `wait_for_render_ready()` wall-clock `timeout_seconds`** — set the
  time budget there, not via a film pin. Convergence tiers defined in
  `models.QUALITY_TIERS` resolve their budget into `timeout_seconds`
  (see `references/render-convergence-tiers.md`).
- **`handle_save_preview` saves the frame BEST-EFFORT on timeout — do not
  revert.** An earlier version returned `false` (aborting the save) when the
  wall-clock cap was hit, so a capped render on a slow scene produced **no PNG
  at all**. The current handler logs the timeout and still calls `saveImage`.
  Preserve the save-on-timeout path if you touch this handler.
  If you edit a bridge Lua file, Octane caches the script in memory — **restart
  the Octane X app** to reload the patched bridge.
- **Persistent bridge auto-poll timer is BROKEN** (`timer create attempt 1
  failed: bad argument #1 to 'create'`). It will not drain the queue on its own.
  Always drain with `octane_run_oneshot_bridge` (MCP) or the osascript one-shot
  trigger — it processes every queued command in timestamp order, then returns.
  Do not rely on the persistent bridge to auto-drain.

**Drain detail (corrected 2026-07-09):** the one-shot bridge drains the
**entire queue in one click** — it processes every queued command in timestamp
order, then renders and returns. (An earlier note claimed "~1 command per click /
repeat until empty"; that is wrong for the current oneshot and was removed — one
click + a single queue-empty poll is sufficient.) If
`octane_run_oneshot_bridge` throws `ClosedResourceError` (transient MCP blip),
fall back to the raw osascript menu-click above — same effect, no MCP server —
and do NOT keep re-calling the MCP tool until the server self-recovers (~45–75 s).
- If the raw osascript `run script file` returns AppleScript error **-1700** ("Can't make some data into the expected type"), Octane X is in a non-receptive state (mid-render modal / busy). Retry after `tell application "Octane X" to activate`; if it persists, the only recovery is restarting Octane X (purges the loaded scene — re-queue the full pipeline) or reusing an already-produced render if one exists.

- **`set_render_resolution` logs non-fatal `setPinValue failed pin=filmResolution/
  width/height/... (No pin ... in NT_FILM_SETTINGS)`** but reports `ok=true`.
  Ignore these warnings.

**CRITICAL — do NOT restart Octane X between `import_geometry` and `save_preview`.**
A restart purges the in-memory scene, so the import that ran in the old session
is gone; material/camera/lighting/save then execute against an empty scene →
uniform gray frame `(243,243,243)`, ~16 KB, and a long wasted render. Restart
Octane X ONLY to reload a *patched bridge*, and do it *before* queueing any scene
command. Queue the entire import→…→save_preview pipeline in ONE live Octane
session, then drain.

- **Container FS is slow and high-sample renders are long.** After the save
  command drains, a 79k-tri surface @ 512 samples took ~90 s before the PNG
  timestamp moved. Allow 60–120 s before checking the PNG; don't conclude
  failure early.
- **`octane_record_recipe` MCP tool was absent** in a recent session
  ("Unknown tool"). Record recipes inline in `NOTES-*.md` / `docs/recipe-book.md`
  rather than blocking on that tool.

> End-to-end reproduction for a multi-color combined mesh (green sphere on red
> cube), including raw queue JSON with `group_index` and the verification
> numbers, is in `references/multi-group-colored-mesh.md`. A reusable generator
> for the combined cube+sphere OBJ is `scripts/gen_green_sphere_red_cube.py`
> (committed in the repo root).
> A photoreal mathematical surface (sinc + azimuthal ridge, glossy bronze,
> verified by full-frame pixel scan) is reproduced in
> `references/photoreal-math-surface.md`; its parametrised OBJ generator is
> `scripts/gen_math_surface.py`.
> The render convergence quality-tier system (`standard`/`high`/`ultra`/`final`),
> the confirmed `maxRenderTime`-ignored finding, and the live high-tier test
> result are captured in `references/render-convergence-tiers.md`.

## Bridge Source Architecture & Patching a Bridge Bug

This is the part that is easy to get wrong: **the bridge Lua is generated, and
the generation source is what you must edit for any permanent fix.**

- `octane_lua/hermes_bridge_oneshot.generated.lua` and
  `hermes_bridge_persistent.generated.lua` are the files Octane X actually runs.
  They are **gitignored** (`octane_lua/*.generated.lua`) and are produced by
  `octanex-mcp init`, which copies templates into them.
- Templates (tracked + committed — these are the source of truth):
  `hermes_bridge_oneshot_v2.lua` → `oneshot.generated.lua`;
  `hermes_bridge_persistent_v1.lua` → `persistent.generated.lua`.
- `octane_lua/lib/runtime.lua` and `octane_lua/lib/handlers.lua` are the shared
  source layer the generated files were authored from. The generated files
  **inline everything** (they do NOT `dofile` the lib files), so the lib files
  are a parallel copy, not a live dependency — keep them in sync with the
  templates.

**Correct sequence to fix a bridge bug (order matters):**

1. Edit the template file(s) (`hermes_bridge_oneshot_v2.lua` and/or
   `hermes_bridge_persistent_v1.lua`) AND `lib/runtime.lua` / `lib/handlers.lua`
   for the function you are changing.
2. Regenerate: `uv run octanex-mcp init` (re-copies templates →
   `.generated.lua`). This **overwrites** any direct edit you made to a
   `.generated.lua`.
3. Restart Octane X (`osascript -e 'quit app "Octane X"'` then
   `open -a "Octane X"`) so the Lua bridge is re-read from disk into Octane's
   memory.
4. Commit the template + lib edits. The `.generated.lua` diffs are gitignored
   and should not be committed.

**Anti-pattern (cost real rework this session):** hand-editing a
`.generated.lua`, getting a working render, then committing. The fix is
invisible to git and lost the next time anyone runs `init`. Always port into
the templates + lib first, then regenerate.

> The bridge fixes described in "Materials, Import & Render-Restart Gotchas"
> live in `request_render_restart` and `connect_material_to_mesh_pins` — edit
> those in the templates + `lib/runtime.lua`, not in the generated files.

## Objective color verification

`vision_analyze` can loop on open-ended questions (take only the first line).
For a definitive check, run a full-frame hue scan
(`scripts/verify_render_colors.py`, if present in the skill dir; otherwise use
the inline scan pattern from the recipe book under "Multi-group colored mesh")
— a naive box average over lit geometry is fooled by warm studio rim light (a
green sphere's lit edge reads tan). The script reports per-hue pixel counts and
the most-saturated example pixel.

```bash
# If the skill ships the script:
env -u PYTHONPATH /tmp/pixcheck/bin/python scripts/verify_render_colors.py \
    --path renders/preview.png --step 2
# Otherwise run the equivalent inline scan with any Pillow venv:
env -u PYTHONPATH /tmp/pixcheck/bin/python - <<'PY'
from PIL import Image
im = Image.open("renders/preview.png").convert("RGB")
W,H = im.size; px = im.load()
green=red=0; gbest=(0,0,0); rbest=(0,0,0)
for y in range(0,H,2):
    for x in range(0,W,2):
        r,g,b = px[x,y]
        if g>120 and g>r+25 and g>b+10:
            green+=1
            if g>gbest[1]: gbest=(r,g,b)
        if r>120 and r>g+25 and r>b+10:
            red+=1
            if r>rbest[0]: rbest=(r,g,b)
print("green px:",green,"best",gbest,"| red px:",red,"best",rbest)
PY
```

(The `env -u PYTHONPATH` is required only because the Hermes runtime's
`PYTHONPATH` forces a broken venv; use any venv that has Pillow. The technique
is documented in the recipe book under "Multi-group colored mesh".)

## Live Recipe Verification (benchmarks/verify_recipes.py)

To verify a recipe actually renders in native Octane (not just passes the offline
contract check), use the harness — it mirrors the OBJ into the container, rewrites
import/save paths to the container FS, drains, and pixel-accepts the PNG:

```bash
OCTANEX_LIVE=1 uv run python -m benchmarks.verify_recipes --slug network-graph
# or the library sweep (all 18):
OCTANEX_LIVE=1 uv run python -m benchmarks.verify_recipes --live
```

**Two non-obvious traps this harness now handles (learned 2026-07-09):**

- **Render-wait budget, not a hardcoded poll.** The PNG-write wait must honor the
  render budget (`drain_timeout`), NOT a short fixed poll. An earlier 15 s hard
  cap returned before the render converged and accepted a blank/partial frame as
  "passed". The fix waits `max(30, drain_timeout)` seconds for the PNG.
- **Wait for a FRESH PNG.** Before each run, delete any existing
  `recipe_<slug>_octane-preview.png` so the acceptance check cannot pass on a
  stale frame from a previous run. Per-recipe unique filenames prevent collision
  across a batch.
- **Verify recipe slugs before batching.** The recipe registry slugs are not
  always the obvious names (e.g. `data-bars`, not `bar-chart`; there is no
  `histogram`/`scatter-plot`/`correlation-heatmap`/`pca-3d`). Enumerate real
  slugs first: `uv run python -c "from octanex_mcp.recipes import _recipe_dirs; from pathlib import Path; print([d.name for d in _recipe_dirs(Path('examples/recipes'))])"`.
- **Promotion (`--copy-back`) flips `native_octane_verified` on a real pass.**
  Add `--copy-back` to copy the live PNG back into the recipe dir as
  `octane-preview.png` AND set `native_octane_verified=true` in `scene.json`.
  The harness promotes ONLY when pixel QA passes (`acceptance.passed`); a
  wrong-subject-but-pixel-OK render is NOT promoted on pixel alone.
- **Opt-in vision-against-intent gate (`--vision-check`).** After pixel QA passes,
  a vision model confirms the PNG shows the recipe's stated `intent` and BLOCKS
  promotion on a wrong-subject verdict. The vision call is injected (`vision_fn`),
  so the offline test suite never touches a real model. For autonomous live runs,
  pass a real vision callable (the built-in shim imports `hermes_tools.vision_analyze`,
  which is not available inside `uv run` — call the vision tool from the agent
  runtime and pass it as `vision_fn`). The role of this gate: pixel QA cannot catch
  a grey-shape-wrong-subject render (see `docs/recipe-book.md` "5 color-dependent
  recipes rendered wrong").

```bash
# library sweep + promote verified recipes to native_octane_verified=true:
OCTANEX_LIVE=1 uv run python -m benchmarks.verify_recipes --live --copy-back --drain-timeout 150
# same, with the opt-in vision gate (promotes ONLY on pixel+vision pass):
OCTANEX_LIVE=1 uv run python -m benchmarks.verify_recipes --live --copy-back --vision-check --drain-timeout 150
```

Completion: `acceptance.passed == True` on a fresh PNG, confirmed by a
`vision_analyze` spot-check before declaring the recipe verified.

## Verification Checklist

- [ ] `uv run octanex-mcp doctor` reports `Overall: ok` and expected paths.
- [ ] `hermes mcp list` shows `octanex`; `hermes mcp test octanex` connects.
- [ ] Octane X is running (`pgrep -fl "Octane X"`).
- [ ] Queue files move to `processed/` after running a bridge.
- [ ] `octane_save_preview` produces a non-empty PNG file under `renders/`.
- [ ] `octane_review_preview` returns `ok=true` with actionable metrics.
- [ ] `vision_analyze` (local) confirms the PNG matches intent before delivery.
- [ ] Any new pitfall is recorded in `docs/recipe-book.md` or a recipe README.
- [ ] No test command files left behind in `…/OctaneMCP/queue/`.

## Related

- `octane-viz` — prompt-prefix ("Visualise") trigger skill.
- `octanex-mcp-overview` — full tool/launch reference (AppleScript + Computer Use + Vision trio).
- `octanex-mcp-review` — architecture review notes.
- `octanex-visual-loop` — the end-to-end local visual loop mandated by SOUL.md.
