---
name: octanex-mcp
description: Use when configuring, testing, or operating the OctaneX MCP server from Hermes Agent, especially for queue draining, render-ready PNG previews, and local vision review loops.
version: 1.9.16
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
- debug a queue that is not being picked up by Octane X;
- build, test, or extend the Agentic Canvas dashboard (HTTP gateway + Swift/WKWebView host + web bundle).

Do not use this skill for arbitrary Lua execution. The bridge is intentionally an allow-listed command DSL.

## Human scene labels (#N) & scope→domain resolution

The human can address scene objects by a stable badge (``#N`` for objects,
``#Gk`` for groups) instead of opaque names. Built 2026-07-10.

- **Stable ids live in the manifest.** `src/octanex_mcp/scene.py`
  `_assign_stable_ids` seeds a `uid` from the object `id` (so node names
  stay `Hermes::<scene>::<id>` and the bridge `find_item_by_name` +
  `swap_geometry` stable-node contract is preserved), minting `oNNNN` only
  when no id exists. A never-renumbering `labels`/`group_labels` map
  (`#N → uid`) is preserved across add/remove — **dead badges are
  dropped (gap left), not shifted**, so "#43" never silently points at a
  different object.
- **`scene.py` `resolve_label_refs`** parses `#43`, `#1 and #3`,
  `#6 through #10`, `#G2` (groups expand to member uids) → uid list.
- **`src/octanex_mcp/annotation.py`** projects each labelled object's
  `bounds.center` through the scene `camera` (pure-stdlib look-at +
  perspective, no numpy) and draws `#N` markers onto a rendered PNG via
  `octane_annotate_preview` (MCP tool). The raster step needs Pillow
  (`uv sync --extra harvest`); if absent it still returns the computed
  label layout + an install hint. No Lua/bridge change required.

### Edge-case precedent (do NOT re-litigate)

A property word like **"resolution" is NOT inherently ambiguous**. The scope
decides the domain, encoded in `src/octanex_mcp/intent/disambiguate.py`
(`resolve(text, object_refs=...)`):

- object/group scope (`#N`, `#Gk`) → **object domain** (mesh tessellation),
  high confidence, **no confirm**. "increase the resolution of #1" = mesh.
- render/canvas scope (`output`, `canvas`, `render`) → **render domain**
  (W×H, spp). "set output resolution to 4k" = render.
- **no scope** → default (render, statistically common) + `needs_confirm=True`.
  Only *this* case is genuinely ambiguous. The same table generalizes to
  size / quality / smoothing / sharpness / detail / density.

Phases still to build (post-2026-07-10 spike): (3) grouping + mesh
modifiers routing "resolution→mesh" to `swap_geometry` with a subdivided
OBJ; (4) object keyframe animation (extend `animation.py` + new Lua op);
(5) NL sugar over the resolver/ref parser.

### Phase 3 shipped (2026-07-10): grouping + mesh modifiers

- `src/octanex_mcp/meshmod.py` (gated on optional `science` extra = `trimesh`,
  mirrors `geo.py`/`shapely`): `subdivide_obj` (resolution → Loop subdiv,
  `max_faces` cap 200k), `smooth_obj` (pure-numpy umbrella Laplacian; no scipy
  dep), `merge_objs` (grouping). Each writes a new OBJ to `assets/` and returns
  `{path, bounds, ...}`. Missing extra → `MeshDependencyError` + `uv sync
  --extra science` hint (never import-crash).
- `scene.py` `group_objects(scene_id, refs, ...)`: resolves `#6 through #10 and
  #54` → uids → `merge_objs`, replaces members with one merged node, records a
  `#Gk` group entry. `modify_objects(scene_id, refs, modifier, ...)`:
  `resolution`/`smooth` per node via `swap_geometry` (stable node name kept).
- MCP tools `octane_group_objects`, `octane_modify_objects`. Tests:
  `tests/test_meshmod.py` (9, real trimesh; dependency-missing path guarded).

### Phase 4 shipped (2026-07-10): object transform animation (#N-driven)

The visual-grammar model now extends across the scene pipeline — objects,
materials, lights, cameras, and scene edits share one transform/keyframe
grammar. Phase 4 delivers object animation; the same `set_object_transform`
op generalizes to animating materials/lights/cameras/scene state later.

- **New op `set_object_transform`** in `models.ALLOWED_OPS` + `SetObjectTransformPayload`
  (needs `object_name` + ≥1 of `translation`/`rotation_euler`/`scale`). Handler added to
  BOTH bridge templates (`hermes_bridge_oneshot_v2.lua`, `hermes_bridge_persistent_v1.lua`)
  **and** `lib/handlers.lua` (reference copy). Regenerate with `uv run octanex-mcp init`
  — the templates are the source of truth, NOT `lib/handlers.lua`.
- `animation.py`: `ObjectKeyframe`/`ObjectAnimationManifest`, `EASING` table
  (`linear`/`ease_in_out_quad`/`ease_in_quad`/`ease_out_quad`/`ease_in_out_cubic`),
  `sample_object` (eased interpolation), `build_object_animation_commands`
  (per-frame `set_object_transform` + `save_preview`, absolute frame index preserved
  so sub-ranges compose), `object_rotate_manifest` / `object_translate_manifest`.
  `_parse_frame` accepts ints OR timecode strings (`"00:00:16:08"` SMPTE, `"2.5"` sec);
  `fps` defaults to **24** (common standard) when unspecified.
- `scene.animate_objects(scene_id, refs, motion, ...)`: `motion` = rotate/translate/scale;
  resolves `#N`/`#Gk` → node names → bakes + queues per-frame commands. Requires the
  scene nodes to already exist in Octane (build the scene first). One one-shot click
  drains the whole queue (same as `octane_build_animation`).
- MCP tool `octane_animate_objects`. "rotate #54 by 104 degrees over frames 400-1000
  with quadratic in-out" → `motion=rotate, degrees=104, start_frame=400, end_frame=1000,
  easing=ease_in_out_quad`. Tests: `tests/test_object_animation.py` (18).
- **Bridge edit rule (re-learned):** the generated `*.generated.lua` are BUILT FROM the
  `*_v2`/`*_v1` TEMPLATES. Editing only `lib/handlers.lua` does NOT reach the bridge —
  you must edit both templates + regenerate. Parity guard: `tests/test_lua_bridge_parity`.

## Setup Checklist

1. Initialize the repo and generated Lua scripts (from the repo root `/Users/craig/octanex-mcp`):

   ```bash
   cd /Users/craig/octanex-mcp
   uv run octanex-mcp init
   uv run octanex-mcp doctor
   ```

   Completion: `doctor` reports `Overall: ok`, the workspace, generated bridges, and the Octane X app path. (Verified: `doctor` checks the app bundle, lua dir, all workspace subdirs, and workspace writability.)

2. Register the MCP server with Hermes (sanctioned CLI path):

   > Direct edits to `~/.hermes/config.yaml` are **blocked** by the Hermes config guardrail
   > ("Refusing to write to Hermes config file"). Use `hermes mcp add` — it writes `mcp_servers` for you.

   ```bash
   printf 'y\n' | hermes mcp add octanex --command /Users/craig/octanex-mcp/run_octanex_mcp.sh --connect-timeout 30
   ```

   `run_octanex_mcp.sh` does `exec env -u PYTHONPATH uv run --project /Users/craig/octanex-mcp octanex-mcp`.
   The `env -u PYTHONPATH` is **mandatory**: the Hermes agent runtime exports
   `PYTHONPATH=…/hermes-agent/venv/…` which would otherwise force the spawned server to load the Hermes
   venv's broken `pydantic_core` and crash with `RuntimeError: mcp package is not installed`. Under a clean
   env the project `.venv` (mcp 1.26.0) imports fine.

   Completion: `hermes mcp list` shows `octanex` (✓ enabled, 48 tools) and `hermes mcp test octanex`
   enumerates the tools. Start a new Hermes session to use them.

   (Equivalent hand-edited config block, if the guardrail ever allowed it:
   `mcp_servers: octanex: command: /Users/craig/octanex-mcp/run_octanex_mcp.sh`.)

3. In Octane X Preferences, set **Scripts path** to this checkout's `octane_lua/` directory:

   ```text
   /Users/craig/octanex-mcp/octane_lua
   ```

   Completion: Octane X's Script menu shows `hermes_bridge_oneshot.generated` and `hermes_bridge_persistent.generated`. Restart Octane X if the scripts do not appear after changing the preference.

   > **If the Script menu is absent**, do NOT assume the preference is wrong first — without the Accessibility grant below you cannot even *inspect* the menu (every probe returns `-1719`), so the menu looks missing. Fix the permission, then re-check.

4. **macOS Accessibility (TCC) — the #1 launch blocker.** The bridge is launched by UI-scripting Octane X's Script menu via `osascript`, which the OctaneX MCP **server** spawns. The RELIABLE fix (confirmed by live process inspection 2026-07-10 — the `octanex-mcp` server PID 36709 runs under `/Users/craig/octanex-mcp/.venv/bin/python3` ← `uv` (PID 36708) ← the Hermes **agent-runtime** python (PID 36706, `/Users/craig/.hermes/hermes-agent/venv/bin/python`)):

   - **Grant Accessibility to the Hermes agent-runtime python** — `/Users/craig/.hermes/hermes-agent/venv/bin/python` (⌘⇧G-paste the path into the TCC file picker), or to the shell/terminal app that launches Hermes. TCC evaluates the entitlement on that runtime binary, which is the ancestor of the `osascript` caller.
   - **Do NOT grant `Hermes.app` alone.** `Hermes.app` is NOT in the `octanex-mcp` server's process ancestry (the server spawns from the agent-runtime python via `uv`, not from the GUI app). Granting `Hermes.app` does NOT clear `-1719` — a live `-1719` against a supposedly-granted `Hermes.app` is exactly the tell that the wrong target was granted. The earlier "grant `Hermes.app`" guidance (2026-07-10) is **RETRACTED**: it was wrong.
   - **Full relaunch is mandatory.** TCC re-evaluates the entitlement per process launch. A long-running Hermes/MCP process spawned *before* the grant keeps its old (denied) token until it restarts. Grant → quit Hermes entirely → reopen. (A plain `/reload-mcp` is not enough; the app process itself must restart.)
   - Verify: `osascript -e 'tell application "System Events" to tell process "Octane X" to get name of every menu bar item'` must return the menu list (incl. `"Script"`) instead of `-1719`. Also `osascript -e 'tell application "System Events" to return count of menu bar items of menu bar 1 of process "Octane X"'` must return a number (e.g. `7`), not `-1719`.
   - On `-1719` the bridge returns `tcc_blocked: true` with the exact fix instead of the old misleading `"script not found"` `-2700`.

## Octane X has NO command-line Lua entry point

Do **not** attempt `open -a "Octane X" --args <script.lua>` or any `octane://` URL / `.lua` double-click launch — **none of these work**, and this is a product boundary, not a bug to work around. Verified by inspecting the installed app (2026-07-12, see `docs/octane-x-no-cli.md`):

- The main `Octane X` binary has **zero** references to script execution, `argv` parsing, `no-gui`, or URL/Apple-Event handlers. It is a pure Cocoa/Metal GUI app.
- `Info.plist` registers **no** URL scheme and **no** document-type handlers.
- The Lua engine exists only inside `octanesdk.framework` (`LuaScriptingComponent::runScript`), but the app's `main()` never wires `argv` → `runScript`.
- The `--no-gui -s script.lua` invocation seen in OTOY docs is for **OctaneRender Standalone** (Linux/Windows) — there is **no Mac CLI standalone**.

Consequently: the Script-menu / `osascript` path used here is the *only* supported way to run Lua in Octane X on macOS. A real GUI session is mandatory; there is no headless/CI path. If you find yourself wanting a CLI, the realistic options are OctaneRender Standalone on Linux/Windows, Render Network dispatch, or staying on the Script-menu path.

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

   **Never use `run script file` on the `.lua` bridge.** AppleScript will try to compile the Lua source as AppleScript and die with `-2741` ("Expected end of line, but found ="). The reliable trigger clicks the script from Octane's **Script** menu (which runs it as Lua):

   ```bash
   uv run python -c "from octanex_mcp.bridge_control import run_bridge_script; print(run_bridge_script('oneshot')['stdout'])"
   # -> clicked hermes_bridge_oneshot.generated via Script
   ```

   (Equivalent raw AppleScript: a `tell application "System Events" … click menu item …` block targeting the Script menu — see `bridge_control.render_run_bridge_applescript`.) AppleScript control of Octane X requires automation permission (System Settings -> Privacy -> Automation -> Octane X); verify with `osascript -e 'tell application "Octane X" to get name'`.

   Completion: queued commands move to `processed/` or `failed/`, and `results/*.json` records each outcome. Check `queue/` is empty, not just `processed_count` climbing.

   **Canonical drain rule — ONE click, then poll, never re-click on a timer.**
   A single oneshot click runs the Lua drain loop, which processes the ENTIRE
   queue (assembly + `save_preview`) in one pass and writes the frame. After the
   click returns `ok`, poll `…/OctaneMCP/queue/` for 0 files and wait for the
   PNG. Do **NOT** loop one click per command, and do **NOT** re-click while the
   queue is empty — a second click while `save_preview` is actively rendering is
   ignored, and re-clicking after the queue empties restarts/kills that render.
   Only re-click on a *genuine failed click* (see error taxonomy below), capped.

   **Warm-engine reset between recipes (do not cold-relaunch).** To clear the
   in-memory scene so `request_render_restart` does not wedge on stale nodes,
   use the dedicated tool (this is File ▸ New on the running Octane, NOT a
   quit/open-a relaunch which leaves the engine cold and re-wedges the drain):

   ```text
   octane_reset_octane_scene()       # {ok:true} or {ok:false, kind:...}
   ```

   **Application-control error taxonomy** (the control layer classifies these
   so the agent branches instead of blindly retrying):

   | Symptom / code | Class | Action |
   |---|---|---|
   | `osascript` hangs then raises `TimeoutExpired` | `timed_out` | Octane busy/unresponsive modal. Wait, then retry **once**; if it persists, restart Octane. |
   | `-1719` assistive access denied | `tcc_blocked` | Grant Accessibility to the **Hermes agent-runtime python** (`/Users/craig/.hermes/hermes-agent/venv/bin/python` — the osascript caller, NOT `Hermes.app`), or the shell/terminal that launches Hermes, then **fully quit + relaunch Hermes**. Do NOT grant `Hermes.app` — it is not in the octanex-mcp server's process ancestry and will NOT clear `-1719`. The 2026-07-10 "grant `Hermes.app`" guidance is RETRACTED (wrong). |
   | `-1700` can't make data into expected type | `busy` | Octane mid-render/modal. Wait for the render to settle; do NOT re-click blindly. |
   | `-2741` expected end of line | `wrong_trigger` | Historically caused by `run script file` on Lua. **Also** caused (2026-07-10) by a real AppleScript **syntax bug** in the generated launcher: `if (exists process "Octane X")` written at the *top level* (outside `tell application "System Events"`) — that is a compile error on this Octane build. **FIXED in `src/octanex_mcp/bridge_control.py`** (`render_launch_and_run_applescript` now wraps the probe in `tell application "System Events"` and adds an activate+settle before probing the menu bar, absorbing transient `-1728`). If you still see `-2741`, the running server has stale code — restart Hermes so it reloads the fixed module. |
   | `Could not find <script> in Script menu` | `script_not_found` | Set Octane Preferences ▸ Scripts path → repo `octane_lua/`, then restart Octane. |

   The bridge launch now also **waits for Octane X's menu bar to become UI-ready**
   after `open -a` (up to `LAUNCH_READINESS_WAIT_SECONDS`, default 10s) *inside the
   same AppleScript* — eliminating the cold-launch race where a fixed `delay 0.5`
   probed the menu before Octane had loaded it, producing a false "script not found".

5. Save a PNG preview. Pass a convergence tier via `quality` so the render
   stops at a time budget instead of running unbounded:

   ```text
   octane_save_preview(quality="fast")                                 # 6s render cap, 10s wall cap; creator default
   octane_save_preview(quality="preview")                              # 10s cap (fast sweep)
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

A non-clean Octane session is a common cause of blank / near-black / stale
renders. Before every live render (and between scenes), follow this exact
sequence:

1. **Check Octane X is running.** If not, `open -a "Octane X"`. Do not proceed
   without the GUI session.
2. **Reset the workspace to startup default** — UI-script `File → New` in Octane
   X (clears any in-memory scene from a prior run). AppleScript:
   `tell application "System Events" to tell process "Octane X" to click menu
   item "New" of menu 1 of menu bar item "File" of menu bar 1`.
3. **Flush is an operator escape hatch, NOT a default step.** The filesystem
   scheduler (`src/octanex_mcp/scheduler.py`) now makes `queue/` strictly the
   "currently draining" staging for one job at a time. **Do NOT call
   `octane_flush_queue()` before queueing in the multi-agent/shared-engine case —
   it moves other agents' pending commands to backup and breaks their jobs.** Only
   flush to recover from a genuinely wedged/orphaned global queue, and prefer
   `octane_job_queue()` to inspect first. For shared-engine rendering use the
   scheduler tools:
   - `octane_submit_job(commands, preview_path)` — enqueue a complete scene
     build; never flushes others.
   - `octane_render_job()` — the SINGLE render path: promotes the oldest queued
     job under `render.lock`, drains via the lock-aware `octane_drain.applescript`,
     and writes `jobs/<id>/done.json` so completion survives a SIGTERM'd
     controller. On hard drain failure the job is marked failed and the lock
     released for retry.
   - `octane_job_status(job_id)` / `octane_job_queue()` — poll state + outputs.
   The `render.lock` lease (default 300s, 30s heartbeat) makes the engine
   shareable: a second agent calling `octane_render_job()` while another holds a
   live lease gets `promoted_job_id: null` (busy) instead of double-driving
   Octane. The hand-rolled `osascript scripts/octane_drain.applescript` is also
   lock-aware (refuses to drain if another agent holds a live lease).
   **Auto-serving the queue (DispatchLoop):** to let agents just submit and
   have the engine drain itself, run `python3 scripts/dispatch_loop.py
   --dispatch` (long-lived, for mac-studio launchd) or `--tick` (cron).
   The gateway also auto-starts a daemon with `--dispatch`, controllable via
   `POST /dispatch/start|stop|status` and `POST /dispatch/tick` (one unit,
   safe no-op under a live lease). The render.lock serializes the gateway
   daemon, the CLI, and any cron tick — so the engine is never double-driven
   even if all three run. A killed driver cannot strand a job: the next driver
   reclaims the stale lease and re-promotes from `jobs/<id>/commands/`.
4. **Build and queue the complete scene pipeline** (import → material → camera
   → light → save-preview). When using the scheduler, queue into a job
   (`octane_submit_job`) rather than the bare global `queue/`.
5. **Process the queue** with one `octane_run_oneshot_bridge` / Script-menu click
   (or `octane_render_job`, which does the dispatch + drain). One click drains
   the ENTIRE queue, including `save_preview`.
6. **Poll** `…/OctaneMCP/jobs/<id>/done.json` for a shared-engine job (not just
   `queue/` for zero) to confirm completion, then wait for the PNG. Do not
   re-click while `save_preview` is rendering.
7. **Return to step 2** for the next scene (reset → build → drain). Do NOT pile
   scenes into one uncleared session.

### Recipe live-promotion pitfall (2026-07-15)

For checked-in recipes, use the verified live path:

```bash
OCTANEX_LIVE=1 PYTHONPATH=scripts:. uv run python -m benchmarks.verify_recipes \
  --live --copy-back --slug <slug> --drain-timeout 300
```

Load-bearing details from the 2026-07-15 bridge repair:

- `benchmarks.verify_recipes.run_recipe()` must flush stale global queue files
  **before** writing that recipe's commands. Flushing after queueing deletes the
  render job, and the one-shot bridge drains zero commands.
- On this Octane X build, `octane.render.start{renderTargetNode=rt}` is
  effectively synchronous: it may block the Lua drain until the frame is ready,
  but it is also the call that causes sampling to advance. `restart()` /
  `continue()` alone returned `ok=true` while stats stayed `beauty=0 state=0`.
  Therefore recipe promotion needs a long enough drain budget (`--drain-timeout
  300` worked for `mass-spring-cloth-drape` and `dam-break-splash`).
- `octane.render.saveImage(path, octane.imageSaveType.PNG8)` is the successful
  save path once a real frame exists. `saveImage2{...}` table form was rejected
  by this build (`string expected, got table`) and should remain a fallback, not
  the primary path.
- Lua keyword trap: call `octane.render["continue"]()` rather than
  `octane.render.continue()`; this Lua parser treats bare `continue` as a syntax
  error near `and`, breaking both generated bridges.

> **CRITICAL — after the bridge populates the node tree, the Hermes Render
> Target node MUST be selected and the renderer MUST be explicitly started, or
> the run silently produces a near-black/empty frame.** The one-shot bridge's
> Lua handlers call `octane.project.setSelection{rt}` (`activate_render_target`)
> and `request_render_restart` (`start_render`) for you, but this must happen
> *against a fully-populated node tree*. If a frame comes back near-black
> (`mean_dev≈0`) with no scene error, the cause is almost always one of:
> (a) a stale queue / leftover scene (steps 2–3), or (b) incomplete scene
> assembly. Re-run the complete import→material→camera→light→`save_preview`
> pipeline; `save_preview` performs the final render start after the scene is
> wired. Confirm `octane_status` shows `octane_node_available=true` before draining.

> **Octane is fast:** basic scenes are acceptably converged for preview
> evaluation after only **1–2 s**; complex scenes after **5–10 s**. Do not set
> long `max_render_time`/`timeout_seconds` caps "to be safe" — they only delay
> the PNG and tempt an early "failed" conclusion. A short standard-tier save is
> sufficient for a QA pass; use high/ultra only when the preview genuinely needs
> more samples.

> **Pitfall — stale queue → near-black frame.** If a render comes back
> near-black (`mean_dev≈0`, triggers `mostly near-black`) with no obvious scene
> error, suspect a stale queue or leftover scene, NOT a material bug. Run steps
> 2–3 (reset + flush) and re-queue. The 2026-07-09 `avatar-guide`
> failure was exactly this: a stale scene + un-drained queue, not a recipe
> defect.

## Bridge Debugging

- If queue grows but nothing is processed, run the one-shot bridge from Octane X's Script menu or via the osascript trigger above.
- If `status.json` is stale, trust current queue/result files over old status.
- If preview save fails immediately after a scene mutation, use the current bridge templates: they call `render.restart()`, wait for `getRenderResultStatistics().beautySamplesPerPixel >= 16`, then `saveImage(path, PNG8)`.
- If geometry appears duplicated or stale, clear the Octane scene before re-importing. Octane appends imported geometry unless the node tree is flushed.
- Persistent bridge may leave the viewport stale (mode cycles active -> one_shot -> closed -> available). Prefer one-shot for batches.

**Known-stuck-state recovery (a hung command blocks the whole queue):** If a
command sits in `processing/` and `queue/` stops draining (no new `bridge.log`
lines, status stuck on `draining queue`), a handler is almost certainly blocked
inside `request_render_restart` → `octane.render.start` (see the render-start
hang gotcha above). Do NOT keep clicking — the loop only advances after the
stuck command returns or is removed. Recovery: move the orphaned `processing/*.json`
to a backup dir (Octane won't re-process them, and `processed_or_failed_exists()`
won't skip new commands because IDs differ), then requeue the remaining pipeline.
If the hang recurs on a fresh Octane launch, the render-start logic itself is
wedged (Octane auto-rendering on launch) — fix `request_render_restart`, don't
keep brute-forcing clicks.

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
- **Product headphones recipe pattern:** for a reusable over-ear product scene,
  use stepped cylindrical cup shells with explicit planar end caps, orient the
  cup axes to oppose across the headband, and model the headband as a broad flat
  profile rather than a round tube. A coiled cable should be a swept spiral
  around a curved path with a decaying radius; repeated independent loops read
  as beads or a spring detached from the product. See
  `examples/recipes/headphones-studio/` and `docs/recipe-book.md`.
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
- **`create_light` light node types are NIL on this Octane build.** `octane.NT_LIGHT_AREA`
  / `NT_LIGHT_SUN` / etc. evaluate to `nil`, so the original
  `create_node(light_type)` returned "missing node type for <name>". The current
  `handle_create_light` maps `light_type` `environment`/`sun_light` → a
  `NT_ENV_DAYLIGHT` environment node (reusing the proven `handle_set_lighting`
  path) and `area`/`point`/`spot`/`directional`/`emissive` → an `NT_MAT_EMISSIVE`
  proxy material with an honest "emissive light proxy" log. Do NOT reintroduce a
  raw `create_node(light_type)` for light types — it will fail on this build.
- **`~` in paths is NOT expanded by Octane Lua — apply `expand_path()` EVERYWHERE
  a path flows into Octane.** `save_preview` already used `expand_path(cmd.path)`,
  but `handle_import_geometry` did NOT, so a `~/...` import path was passed verbatim
  to `setAttribute(A_FILENAME,...)` and failed with `No such file` (the pipeline
  then aborted after 1 command). Octane's `os` and `octane.render.saveImage` also
  don't expand `~`, so `~/OctaneMCP_staging/x.png` makes `mkdir`/`saveImage` target
  a literal `~/...` directory and `saveImage` returns `false` (no file written).
  Always run `expand_path()` on `cmd.path` in BOTH `handle_import_geometry` and
  `handle_save_preview`; prefer absolute paths in the driver.
- **`octane.render.start{renderTargetNode=rt}` BLOCKS indefinitely if issued while
  the engine is still rendering — and the wedge blocks the whole queue.** Symptom:
  a command sits in `processing/` forever, `bridge.log` shows `film resolution
  requested ... ok=true` then SILENCE (no `render attempt start` line), and `queue/`
  stops draining. **The one-shot loop never advances past a hung command — do NOT
  keep clicking blindly; a hung command blocks the WHOLE queue.**

  **Root cause (corrected this session):** the *symptom* is real but the cause was
  misattributed. `request_render_restart` is called by *every* scene-assembly
  handler (`import_geometry`, `create_material`, `set_camera`, `set_lighting`,
  `save_preview`). Two failure modes abort the whole one-shot **drain script** (not
  just one command):
  (1) **No-camera crash** — `octane.render.start{renderTargetNode=rt}` hard-errors
  when no camera is wired to the RT yet (the camera is connected later, in
  `set_camera`); and
  (2) **Unprotected hard error** — any Lua error *anywhere* in `request_render_restart`
  (e.g. in `ensure_render_target_defaults` / `activate_render_target` /
  `set_render_resolution` / camera detection) throws out of the function and kills
  the script, so the **remaining queued commands are stranded and never processed**.
  The earlier "blocks forever" framing is only one manifestation; the load-bearing
  failure is the unguarded crash that ends the loop early.

  **The decisive fix is CODE-level (crash-proof the drain), not just operational:**
  1. **(Legacy) Paced drain — no longer needed.** Before the crash-proof fix the
     one-shot loop aborted after one command, so a paced click-per-command driver
     (`scripts/drain_paced.py`) was the workaround. With the crash-proof
     `request_render_restart`, a single oneshot click drains the entire queue; the
     paced driver is now unnecessary. Keep it only to interoperate with an unpatched
     bridge. Condensed runbook: `references/render-wedge-runbook.md`.
  2. **Warm-engine rule.** A `quit`/`open -a` relaunch leaves the render engine
     *cold*, and `start{rt}` wedges even on an otherwise-idle Octane. To reload a
     patched bridge you must restart Octane — do it BEFORE queueing any scene command,
     then run the whole pipeline in that ONE warm session. Do NOT `quit`/`open -a`
     mid-debug to "recover" from a wedge; that just cold-relaunches the engine and
     re-wedges. Reset between renders with **File ▸ New** (AppleScript) on the
     *running* Octane, not a cold relaunch.
  3. `expand_path(cmd.path)` in `handle_import_geometry` (see `~` pitfall above) so
     a `~/...` import path resolves instead of failing with `No such file`.
  4. **Crash-proof `request_render_restart` itself (the load-bearing fix).** Wrap the
     *entire* function body in a single `pcall` that logs an entry line
     (`request_render_restart: entered samples=...`) and, in the `pcall` error
     branch, logs `request_render_restart: HARD ERROR caught: <err>` and returns
     `(false, "request_render_restart crashed: "..err)`. That way NO internal error
     can abort the drain loop. Inside the pcall, add a **camera guard**: read the RT's
     connected camera label; if empty, log `no camera on RT; deferring start{} to
     save_preview` and `return true, "deferred"` — so `start{}` only ever runs at
     `save_preview`, after `set_camera` has connected the camera. The live templates
     carry this shape; the parity test still requires the `request_render_restart`
     substring contract inside `handle_save_preview` (do not remove it).
  5. **DEFERRED-START fix (the actual resolution of the 18-recipe sweep wedge,
     applied 2026-07-09 — this is the bit that makes a batch sweep work).** Even with
     the pcall + camera guard, the per-command `octane.render.start{}` in
     `request_render_restart` **BLOCKS for the render duration** on this Octane build.
     While the bridge script is busy in `start{}`, a re-click is ignored (Octane won't
     run a second bridge script), so `save_preview` strands and the queue never fully
     empties. Fix: `request_render_restart(samples, width, height, do_start)` where
     `do_start` defaults `true`. **Scene-assembly handlers** (`import_geometry`,
     `create_material`, `set_camera`, `set_lighting`, `create_light`) call it with
     `do_start=false` — they only wire the RT/camera/materials and return
     immediately (no `start{}`). **Only `handle_save_preview` passes `do_start=true`**
     and performs the single real `start{}` + `wait_for_render_ready` + `saveImage`.
     With this, a oneshot click drains all 7 assembly commands instantly, then
     `save_preview` does the one ~10 s render and saves. Verified: an 18-recipe sweep
     now promotes 17/18 with one oneshot click per recipe (re-click once only if
     `save_preview` is still in `queue/` — never needed during the assembly phase).
     When you edit `request_render_restart`, add the identical `do_start` text to
     BOTH templates (parity rule) and keep `handle_save_preview`'s call at the default.
  5. **DEFERRED-START fix (the actual resolution of the 18-recipe sweep wedge,
     applied 2026-07-09 — this is the bit that makes a batch sweep work).** Even with
     the pcall + camera guard, the per-command `octane.render.start{}` in
     `request_render_restart` **BLOCKS for the render duration** on this Octane build.
     While the bridge script is busy in `start{}`, a re-click is ignored (Octane won't
     run a second bridge script), so `save_preview` strands and the queue never fully
     empties. Fix: `request_render_restart(samples, width, height, do_start)` where
     `do_start` defaults `true`. **Scene-assembly handlers** (`import_geometry`,
     `create_material`, `set_camera`, `set_lighting`, `create_light`) call it with
     `do_start=false` — they only wire the RT/camera/materials and return
     immediately (no `start{}`). **Only `handle_save_preview` passes `do_start=true`**
     and performs the single real `start{}` + `wait_for_render_ready` + `saveImage`.
     With this, a oneshot click drains all 7 assembly commands instantly, then
     `save_preview` does the one ~10 s render and saves. Verified: an 18-recipe sweep
     now promotes 17/18 with one oneshot click per recipe (re-click once only if
     `save_preview` is still in `queue/` — never needed during the assembly phase).
     When you edit `request_render_restart`, add the identical `do_start` text to
     BOTH templates (parity rule) and keep `handle_save_preview`'s call at the default.

  (Full diagnostic log lines are in
  `references/wp4-create-light-and-render-start-hang.md`; a condensed runbook with
  copy-paste diagnostic commands is in `references/render-wedge-runbook.md`; the
  reusable paced-drain driver is `scripts/drain_paced.py`. The corrected root cause,
  the crash-proof `request_render_restart` shape, and the blank-detection pixel
  stats are in `references/blank-render-and-drain-crash.md`; the blank checker is
  `scripts/verify_render_not_blank.py`.)
- **Persistent bridge auto-poll timer is BROKEN** (`timer create attempt 1
  failed: bad argument #1 to 'create'`). It will not drain the queue on its own.
  Always drain with `octane_run_oneshot_bridge` (MCP) or the osascript one-shot
  trigger — it processes every queued command in timestamp order, then returns.
  Do not rely on the persistent bridge to auto-drain.
- **Persistent bridge SILENT-EXIT (observed 2026-07-12).** Stacking several
  import→render cycles on the persistent bridge in ONE session wedged the render
  engine and then **crashed the bridge window with no surfaced error**: the final
  frame was a plain blue/environment field (no geometry), `bridge.log` ended at
  `save attempt saveImage ... ok=true`, and `processing/` was left holding the
  `save_preview` command. `octane_status` may still report `octane_available:true`.
  **Recovery = full Octane X quit+reopen** (File ▸ Quit, NOT just File ▸ New — File
  ▸ New clears the scene but does not reset a wedged engine), then flush + re-queue
  a fresh pipeline and do ONE clean one-shot drain. **Prefer a cold Octane between
  major geometry regenerations** (each new OBJ formula = one fresh session); do not
  re-import over a long-lived scene. The bridge should guard `wait_for_render_ready`
  + `handle_save_preview` so an `engine-busy` or **empty-mesh** state returns a
  structured error instead of dying silently (code fix still pending).
- **Queue script MUST be single-source with `scene.json`.** A queue driver that
  hardcodes its own `MATS`/camera list will silently DIVERGE from the recipe
  (observed: a `set_camera` change did not take because the queue fed its own
  stale camera). Make the queue script READ `materials` + `camera` from
  `scene.json` and resolve the `commands` list from it, so the OBJ groups and the
  recipe can never drift. The bridge consumes ONLY the `commands` list; the
  top-level `camera`/`materials` fields are documentation — keep them equal to the
  `set_camera` command payload (assert it).
- **Clarification (verified 2026-07-09):** the *manual launch* of the persistent
  bridge works — `octane_start_persistent_bridge` returns `ok:true` and clicks
  `hermes_bridge_persistent.generated` from the Script menu once TCC is granted.
  The broken part is ONLY the idle auto-poll timer, so after a manual launch it
  still will not continuously drain an open queue (this session processed ~6
  commands then stalled at `set_camera`). For a full multi-command pipeline,
  prefer the oneshot bridge (one click drains all 8).

**Drain-loop detail (one click now drains the whole queue):** since the
crash-proof `request_render_restart` fix, the one-shot bridge's `while guard < 50`
loop re-snapshots `queue/` and processes **every** enqueued command in a single
Script-menu click — it no longer aborts after one command. The old "~1 command per
click, click N times until empty" pattern was a *symptom* of the unguarded
`request_render_restart` crash killing the loop early; that crash is gone. So:
enqueue the full pipeline, fire ONE `octane_run_oneshot_bridge` (or
`run_bridge_script('oneshot')`), and the queue should empty in one pass. Still
poll `…/OctaneMCP/queue/` to confirm it hit 0 (watch the file count, not just
`processed_count`). If `octane_run_oneshot_bridge` throws `ClosedResourceError`
(transient MCP blip), fall back to the raw osascript menu-click above — same
effect, no MCP server — and do NOT keep re-calling the MCP tool until the server
self-recovers (~45–75 s).
- If the Script-menu click (via `run_bridge_script("oneshot")`) returns AppleScript error **-1700** ("Can't make some data into the expected type"), Octane X is in a non-receptive state (mid-render modal / busy). Retry after `tell application "Octane X" to activate`; if it persists, the only recovery is restarting Octane X (purges the loaded scene — re-queue the full pipeline) or reusing an already-produced render if one exists. (Distinct from `-2741`, the compile error you get if you mistakenly use `run script file` on the Lua bridge.)

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
- **`octane_record_recipe` appends a compact lesson to `docs/recipe-book.md`.** Use
  it after a verified success, failure, or reusable pitfall; do not write
  untracked `NOTES-*.md` files as a substitute.

> End-to-end reproduction for a multi-color combined mesh (green sphere on red
> cube), including raw queue JSON with `group_index` and the verification
> numbers, is in `references/multi-group-colored-mesh.md`. A reusable generator
> for the combined cube+sphere OBJ is `scripts/gen_green_sphere_red_cube.py`
> (committed in the repo root).
> A photoreal mathematical surface (sinc + azimuthal ridge, glossy bronze,
> verified by full-frame pixel scan) is reproduced in
> `references/photoreal-math-surface.md`; its parametrised OBJ generator is
> `scripts/gen_math_surface.py`.
> The render convergence quality-tier system (`fast`/`preview`/`standard`/`high`/`ultra`/`final`),
> the confirmed `maxRenderTime`-ignored finding, and the live high-tier test
> result are captured in `references/render-convergence-tiers.md`.
> The WP4 `create_light` env/emissive mapping fix and the `octane.render.start`
> render-start hang (incl. diagnostic log lines + the `request_render_restart`
> idle-detection fix) are captured in
> `references/wp4-create-light-and-render-start-hang.md`.

## Live-verification gate: macOS TCC / Accessibility (VERIFIED 2026-07-10)

A real Octane render — and therefore any honest `native_octane_verified` flip —
requires the bridge to actually launch. That launch is gated by macOS
Accessibility (TCC). **The reliable fix (confirmed by live process inspection
2026-07-10) is to grant the Hermes agent-runtime python and fully relaunch
Hermes** — NOT `Hermes.app`, and NOT the `uv` python binaries.

- **Grant the Hermes agent-runtime python** (`/Users/craig/.hermes/hermes-agent/venv/bin/python`, ⌘⇧G-paste the path). That binary is the ancestor of the `osascript` caller: `octanex-mcp` server (under `octanex-mcp/.venv`) ← `uv` ← the agent-runtime python. TCC evaluates the entitlement on that runtime binary, so granting it clears `-1719`.
- **Do NOT grant `Hermes.app`.** It is NOT in the octanex-mcp server's process ancestry (the server spawns from the agent-runtime python via `uv`, not from the GUI app). Granting `Hermes.app` was tested 2026-07-10 and did NOT clear `-1719`. The 2026-07-10 "grant `Hermes.app`" guidance is **RETRACTED** (it was wrong; a live `-1719` against a supposedly-granted `Hermes.app` is the tell).
- **Full Hermes relaunch is mandatory.** TCC re-evaluates per process launch; a process spawned before the grant keeps its denied token. Grant → quit Hermes entirely → reopen. `/reload-mcp` alone is insufficient.
- If the grant is missing or stale, every launch fails with `osascript error -1719: assistive access denied`. The bridge/queue/`request_render_restart` are fine — only the OS permission stops the click.

**Traps (still valid):**
- **`run_recipe(..., drain_timeout=N)` HANGS on TCC denial.** Never start a live sweep without first confirming TCC is green.
- **`bridge_status` can be hours-stale** during a TCC block (launch never ran). Trust the launch response's `tcc_blocked: true` field over cached `status.json`.

**Fix (user action — agent cannot grant):** System Settings → Privacy & Security →
Accessibility → grant the Hermes agent-runtime python (`/Users/craig/.hermes/hermes-agent/venv/bin/python`; re-add + enable refreshes a stale token),
then **fully quit and relaunch Hermes**. Confirm with a dry
`octane_run_oneshot_bridge` → expect `ok: true` with `stdout: "clicked … via Script"`, not `tcc_blocked`.

Only after a green launch should you enqueue a recipe, run the oneshot bridge,
and gate the `native_octane_verified` flip on a real pixel-QA pass. Condensed
diagnostic + recovery: `references/live-verify-tcc-gate.md`.

**Proven end-to-end path (2026-07-10):** the `-2741` AppleScript syntax bug
**fixed in `src/octanex_mcp/bridge_control.py`** (top-level `exists process`
wrapped in `tell application "System Events"`; activate+settle before menu
probe absorbs transient `-1728`) **plus the agent-runtime-python TCC grant + full
Hermes relaunch**. With both in place, `octane_run_oneshot_bridge` autonomously
clicks the bridge, drains the entire queue, and `save_preview` writes a real
frame (verified: a 17-command photoreal butterfly scene rendered end-to-end with
zero manual clicks, surviving an OOM crash + recovery). Condensed recovery:
`references/butterfly-session-recovery.md`.

## Agentic Canvas Dashboard (thin native client)

A separate subsystem renders an `Agentic Canvas` UI — a native Swift `WKWebView`
window that talks to a small **HTTP gateway** instead of injecting UI into Octane X.

**Architecture (the load-bearing rule):** the OctaneX MCP server (`server.py`) is
**stdio-only** and owned by Hermes — there is NO HTTP endpoint. The dashboard
cannot call MCP tools directly. So the gateway (`src/octanex_mcp/gateway.py`,
runnable as `octanex-gateway` or `python -m octanex_mcp.gateway --port 8731`) is a
**separate process** that wraps the project's *library functions* and serves them
over `http://127.0.0.1:8731`. It never touches Hermes's MCP registration.

**CRITICAL gotcha — `@mcp.tool` closures are NOT importable:** every MCP tool is
a nested function inside `build_mcp()`, so `from octanex_mcp.server import
octane_queue_recipe` fails. The gateway dispatches via the *underlying
module-level* functions instead:

| UI calls tool           | Dispatch target (importable)                                                        |
|-------------------------|------------------------------------------------------------------------------------|
| octane_status           | `bridge.octane_app_status` + `bridge.list_commands`                                |
| octane_queue_recipe     | `recipes.queue_recipe`                                                             |
| octane_recipe_book/index/load | `bridge.read_recipe_book` / `recipes.recipe_index` / `recipes.load_recipe` |
| octane_validate_command/queue | `schema.validate_command` / `schema.validate_queue`                        |
| octane_review_preview / suggest_*_fix | `review.review_preview` / `review.suggest_camera_fix` / `review.suggest_lighting_fix` |
| octane_scene_sanity    | `sanity.analyze_scene_graph` over `bridge.scene_harvest` (LIVE graph, pre-render gate) |
| octane_check_scene_plan | `sanity.analyze_scene_plan` (OFFLINE manifest, pre-build gate; includes camera-framing math) |
| octane_save_preview     | `server._build_save_preview_envelope` (module-level!) → `bridge.write_command("save_preview", …)` |
| octane_import_geometry / start_render / set_camera | `bridge.write_command(…)`                                   |

**Pre-render sanity gate (report-only):** `octane_scene_sanity` harvests the
live OctaneX node graph and runs `analyze_scene_graph` — catches
no render-target / no camera / camera-not-wired-to-RT / no light-or-environment /
mesh-missing-geometry / mesh-unassigned-material / orphan material / zero-or-negative
node scale **before** spending GPU on `octane_save_preview`. Complementary to the
post-render pixel QA in `octane_review_preview`. `octane_check_scene_plan`
runs the same gate offline against a scene manifest *before* building, and additionally
does camera-framing math from per-object `bounds` (camera inside / too-far / too-close
→ empty or clipped frame). Both are report-only: they never mutate the scene or
block a render; the agent decides whether to proceed. `strict=True` escalates
likely-blank signals (no lighting, camera unwired) from warnings to errors.

When adding a dashboard-callable tool, wire it in `gateway.DISPATCH` (point at the
library function, NOT the MCP closure). Do NOT try to import the decorated function.

**Gateway endpoints:** `POST /mcp/call {"tool","args"}` → `{"ok","result"|"error"}`;
`GET /status` → the Lua bridge `status.json` (`Workspace().status_path`);
`GET /preview[?progressive=1]` → `renders/preview.png` / `preview_progressive.png`;
`POST /intent {"text"}` → appends to `intents.jsonl` (agent-loop handoff);
`GET /config` → `{render_host, workspace}`; static web bundle from `WEB_DIR`
(default `apps/octanex-canvas/web`).

**Swift host:** `apps/octanex-canvas/` (SwiftPM `Package.swift` + `Sources/.../main.swift`).
`swift build` then `swift run` opens the `WKWebView`, loads `web/index.html`, and
launches the gateway as a child process (passing through `OCTANEX_RENDER_HOST`).
`apps/.build/` is gitignored — never commit Swift build artifacts.

**Web bundle:** `apps/octanex-canvas/web/{index.html,app.css,app.js}` (vanilla, no
framework). Polls `/preview` (full-bleed) + `/status` (truthful pill); `⌘K`
palette → `octane_recipe_book` + `octane_queue_recipe`; `⌘I` inspector →
`octane_review_preview` + `octane_suggest_camera_fix` + `octane_set_camera`;
`~` focus mode; `localStorage` continuity. All input funnels through one
`submitIntent(text)` so voice/drag-drop can drop in later.

**New config / features (dashboard-driven):**
- `OCTANEX_RENDER_HOST` env → `OctaneConfig.render_host` (default `localhost`).
  Gateway `run_remote_bridge_and_pull()` `ssh`+`scp`s the preview back from a
  Studio renderer (thin-client path; `scp` pull preferred over lazy backup sync).
- `octane_save_preview(progressive=True)` adds `progressive:true` + `progressive_path`
  to the command JSON (Lua `handle_save_preview` emits an early low-spp frame).
  Shared via `server._build_save_preview_envelope` so MCP tool and gateway stay in parity.

**WIP-respecting rule (project convention):** `octane_lua/hermes_bridge_*_v2/_v1.lua`
templates, `docs/recipe-book.md`, and `benchmarks/*` frequently carry **uncommitted
user WIP** (`git status` shows them modified). These are source-of-truth bridge
files — do NOT hand-edit or clobber them inside a larger task. If a task needs a
Lua-side change but those files are WIP-owned, implement the Python/Swift/web parts
and hand back a precise patch for the Lua edit; let the user commit their WIP first.
After any bridge Lua edit, run `PYTHONPATH=. uv run python -m unittest tests.test_lua_bridge_parity -v`.

**Tests:** `tests/test_gateway.py`, `tests/test_config_render_host.py`,
`tests/test_progressive_save.py`, `tests/test_status_schema.py`. Run with
`PYTHONPATH=. uv run python -m pytest tests/test_gateway.py tests/test_config_render_host.py tests/test_progressive_save.py tests/test_status_schema.py`.

> Dispatch table detail, endpoint contracts, the progressive / status.json schema
> contract, and a minimal run recipe are in `references/dashboard-gateway.md`.

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

**PARITY CONSTRAINT (hard rule — the #1 bridge-edit pitfall):** the two bridge
templates (`hermes_bridge_oneshot_v2.lua` and `hermes_bridge_persistent_v1.lua`)
must keep a large set of handler functions **textually identical**. The parity
test `tests/test_lua_bridge_parity.py` asserts equality for: `handle_save_preview`,
`handle_command`, `handle_import_geometry`, `handle_create_material`,
`handle_assign_material`, `handle_set_camera`, `handle_get_camera`,
`handle_set_lighting`,
`handle_start_render`, `wait_for_render_ready`, `render_stat_number`,
`sleep_seconds`, `ensure_connected_node`, `ensure_render_target_defaults`,
`latest_imported_geometry_fallback`. The ONLY tolerated difference is the log
label (`"v2 command"` vs `"persistent command"`), which the harness normalizes.
So:

- If you add code inside any parity-checked function, you MUST add the
  **identical text** to BOTH templates (same literals, same line shape), or the
  parity test fails and the build is blocked. A stray `v2`/`persistent` string
  *inside the body* breaks it.
- `write_status(state, extra, stage_info)` is NOT parity-checked and the two
  files already differ (persistent also emits `processed_count`/`failed_count`
  and calls `update_label`). You can extend it independently per file — but keep
  the core JSON keys consistent so the dashboard maps them.
- `test_save_preview_waits_for_render_readiness_before_saving` **enforces specific
  substrings** inside `handle_save_preview`: `request_render_restart(cmd.samples
  or 64`, `wait_for_render_ready(cmd.min_samples or 16`, `pre-save render
  readiness ok=`, and `octane.render.saveImage(path, cvalue)`. Do NOT remove or
  restructure those lines.

> **Stale-claim trap (learned the hard way this session):** any note/legacy
> memory asserting "`handle_save_preview` does NOT call `request_render_restart`"
> is WRONG as of the `5d928ac` bridge fix — current code DOES call
> `request_render_restart` in `handle_save_preview`, and the parity test enforces
> it. **Always trust the live code + the parity test over any cached claim.**
> Before editing a bridge handler, re-read the actual function body and the
> relevant parity assertions in `tests/test_lua_bridge_parity.py`.

> The parity-checked set, the substring contract, the `write_status` schema, and
> the real Lua-side progressive/`status.json` contract are detailed in
> `references/dashboard-gateway.md`.

> The bridge fixes described in "Materials, Import & Render-Restart Gotchas"
> live in `request_render_restart` and `connect_material_to_mesh_pins` — edit
> those in the templates + `lib/runtime.lua`, not in the generated files.

## Honest blank-render detection (pixel stats, not vision)

A blank/geometry-less frame is the most common *silent* failure — and **`vision_analyze`
is unreliable at catching it**: across a live sweep the auxiliary model flip-flopped,
calling a uniform gray gradient "a clean render" one pass and "blank" the next. **Never
flip `native_octane_verified` or call a recipe "verified" on a vision verdict alone.**

Use a hard pixel discriminator instead. Reference values observed for this engine's
blank output:

| signal | blank gray frame | real geometry |
|---|---|---|
| mean RGB | ~ (146,146,146) | scene-dependent, lower spread |
| std dev | ~ 28 | higher |
| non-background % | 100% (uniform fill) | varies |
| **edge energy** (mean gradient magnitude) | ~ 1.06 | >> 1 (sharp bars/edges) |

`edge energy` = mean of `sqrt(gx^2+gy^2)` over the luminance gradient. A blank gradient
has edge energy ≈ 1.0; any real mesh/bars pushes it well above. The reusable checker is
`scripts/verify_render_not_blank.py` (edge-energy + nonbg% + mean-dev), the same logic
that caught 18 falsely-flagged blank recipes this session. Gate `native_octane_verified`
flag-flips in `benchmarks/verify_recipes.py` on a **real pixel-QA pass**, not on a
"passed" boolean from a broken metric.

**Nuance — pixel-QA confirms NON-blank, not GOOD FRAMING.** Edge energy / nonbg%
only detect a blank or geometry-less frame. A verified render can still be
mis-framed: this session `data-bars` passed pixel-QA (edge energy ≈ 1.16, real
bars present) yet showed only ~3 of 8 bars because the camera was too close.
ALWAYS also vision-check composition/framing before calling a recipe done.

**Diagnostic — grey field with horizontal lines is a REAL render, not a blank.**
If the preview shows a near-uniform grey field crossed by horizontal bands, that
is a correctly-rendered scene with the **camera too close / inside the subject**
(oversized geometry filling the frame), NOT the uniform blank-gradient failure
(edge energy ≈ 1.06, no bands). Treat "grey + horizontal lines" as a framing bug
to fix via `octane_set_camera` / bounds-aware camera, not as a bridge or blank
failure. The auto-framing fix is still a TODO (compare asset bounds to camera
position/distance and pull back) — do not report it as a verification failure.

**Batch-sweep isolation — NEVER run more than one sweep driver at once.**
`benchmarks/sweep.py` (and `verify_recipes.run_recipe`) all share ONE Octane
container (`~/Library/Containers/.../OctaneMCP/`). Launching the sweep more than
once (e.g. multiple `background=true` launches, or a `notify_on_complete`
re-launch stacking on a still-running process) makes the concurrent processes
fight over the queue: each clears + re-queues its own recipe, so the queue count
climbs instead of draining and every per-recipe timer expires with
`queue_left=N`. Symptom: `queue_left` grows past the 8 a single recipe should
have. Fix: `pkill -f benchmarks/sweep.py` until `ps` shows zero, fully clear the
container via its safe workspace reset/backup helpers (do **not** use `rm -f` on
the shared queue), then launch EXACTLY ONE sweep process. The honest sweep driver
(`benchmarks/sweep.py`) is fraud-proof: it clears the container + does a File▸New
scene reset between recipes, deletes any pre-existing `recipe_<slug>_*.png` so a
pass can only credit a freshly-written file (mtime > run start), and flips
`native_octane_verified` ONLY on a real pixel-QA pass. Never trust a sweep that
promotes in seconds — that is the stale-PNG fraud pattern.

> Repo-side equivalent produced this session: `benchmarks/png_stats.py`
> (edge-energy + nonbg% + mean-dev) — keep it in parity with
> `scripts/verify_render_not_blank.py`.

> The corrected root cause, the crash-proof `request_render_restart` shape, and the
> full diagnostic numbers are in `references/blank-render-and-drain-crash.md`.
> The end-to-end `data-bars` verification (8/8 drain, launch sequence, `run_recipe`
> return-shape gotcha, dual-template parity-edit technique, framing nuance) is in
> `references/data-bars-verified-and-pitfalls.md`. The fraud-proof live sweep driver,
> its fresh-mtime anti-fraud gate, the 17/18 result, and the single-process rule are
> `references/honest-recipe-sweep.md`, `references/binary-png-merge-resolution.md`.

## Resolving diverged-branch binary preview PNG conflicts

When merging two branches that both rendered the same `examples/recipes/*/octane-preview.png`
previews, every preview is a **binary add/add conflict** — git cannot auto-merge them and
`git merge-tree` lists them as `CONFLICT (add/add)`. Text files (server.py, scene.json,
acceptance.py, bridge templates) usually merge cleanly; only the PNGs genuinely conflict.
Do NOT coin-flip which side wins — resolve each by the project's own pixel discriminator.

**Restore both sides' blobs and compare metrics:**

```bash
git diff --name-only --diff-filter=U          # U = unmerged; PNGs + any real text conflict
# :2 = HEAD (local), :3 = origin (remote)
for p in examples/recipes/<slug>/octane-preview.png; do
  git show ":2:$p" > /tmp/pngcmp/<slug>.HEAD.png
  git show ":3:$p" > /tmp/pngcmp/<slug>.origin.png
done
# png_stats.py is PURE STDLIB — run with python3, NOT `uv run` (uv swallows stderr)
python3 benchmarks/png_stats.py /tmp/pngcmp/<slug>.HEAD.png /tmp/pngcmp/<slug>.origin.png
```

**Decision rule (per recipe):** both sides are normally *valid, non-blank* renders (the
blank-detection section proves edge-energy, not vision, is authoritative). Pick the more
structured render — higher `EDGE energy std` and `nonbg_pct`. The one case that justifies
keeping **local over remote**: remote's PNG is a near-flat gradient (`edge_std` ≈ 0.5–0.7,
the blank-HDRI signature) while local is real (`edge_std` ≈ 3–5). In the 2026-07-09 merge
this held for exactly one recipe (`photoreal-product-studio`: local 4.92 vs remote 0.72 →
kept local); all other 14 took remote (the more-structured render each time).

**Apply + clear the conflict:**

```bash
git checkout --theirs examples/recipes/*/octane-preview.png   # take remote for all
git checkout --ours  examples/recipes/photoreal-product-studio/octane-preview.png  # override
git add examples/recipes/            # clears the U (unmerged) status
stat -f "%z" examples/recipes/photoreal-product-studio/octane-preview.png  # verify bytes
```

**Real text conflict in `benchmarks/acceptance.py`** (seen this session): remote relocated
the pixel-QA logic into `src/octanex_mcp/acceptance.py` and turned `benchmarks/acceptance.py`
into a shim re-export. Take remote (`git checkout --theirs benchmarks/acceptance.py`) and
verify it imports: `PYTHONPATH= uv run python -c "import benchmarks.acceptance"`.

> Recipe-level metric table + the one-recipe override is condensed in
> `references/binary-png-merge-resolution.md`.

## Proving a merge introduced no new test failures

A red `unittest discover` after a merge does NOT mean the merge broke the suite — the
failures may pre-exist on either branch. Before "fixing" anything, prove ownership with
two throwaway worktrees (git worktree leaves your main checkout untouched):

```bash
git worktree add -q /tmp/origin-main origin/main
git worktree add -q /tmp/local-pre <your-pre-merge-tip-sha>   # old HEAD before merge
cd /tmp/origin-main && PYTHONPATH= uv run python -m unittest <TestClass>
cd /tmp/local-pre   && PYTHONPATH= uv run python -m unittest <TestClass>
# capture "FAIL:" lines from each; diff against the merged result
git worktree remove /tmp/origin-main --force
git worktree remove /tmp/local-pre --force
```

In the 2026-07-09 merge, `discover` reported 5 failures, but this proved all 5 already
existed on the **local** pre-merge tip (origin had only 1 — a stale data-bars assertion the
remote WP6 promotion never updated). The merge introduced **zero** new breakage. The 5 were
stale test expectations contradicting the project's *deliberately chosen* honest state
(17/18 verified; `math-surface` excluded by a known contract gap). Resolution: align the
tests to the honest state (expect 17/18, `math-surface` as the known gap; data-bars
`native_octane_verified=true`) rather than revert the honest commits.

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

## Verification Checklist

- [ ] `uv run octanex-mcp doctor` reports `Overall: ok` and expected paths.
- [ ] `hermes mcp list` shows `octanex`; `hermes mcp test octanex` connects.
- [ ] Octane X is running (`pgrep -fl "Octane X"`).
- [ ] Queue files move to `processed/` after running a bridge.
- [ ] `octane_save_preview` produces a non-empty PNG file under `renders/`.
- [ ] `octane_review_preview` returns `ok=true` with actionable metrics.
- [ ] `vision_analyze` (local) confirms the PNG matches intent before delivery.
- [ ] (Dashboard) `PYTHONPATH=. uv run python -m pytest tests/test_gateway.py tests/test_config_render_host.py tests/test_progressive_save.py tests/test_status_schema.py` passes.
- [ ] (Dashboard) `swift build` in `apps/octanex-canvas` succeeds.
- [ ] (Dashboard) gateway serves `/mcp/call`, `/status`, `/preview`, and the web bundle (`curl -s localhost:8731/` → index.html).
- [ ] Any new pitfall is recorded in `docs/recipe-book.md` or a recipe README.
- [ ] No test command files left behind in `…/OctaneMCP/queue/`.

## Recipe recording & skill-sync upkeep

Recording a non-trivial run is mandatory per the self-improvement loop. After
every visual success (or instructive failure), do BOTH of these:

### Record the recipe
1. Append an entry to `docs/recipe-book.md` in the established format (Outcome /
   Recorded / Context / Steps / Signals / Pitfalls / Follow-ups). Keep it
   concise and evidence-led — pixel stats, sample counts, file sizes, log lines —
   not prose.
2. Refresh `examples/recipes/<name>/`:
   - `scene.obj` — **regenerate from the canonical generator** (`scripts/gen_*.py`);
     never hand-edit a stale OBJ. A recipe dir can hold a *different formula's*
     OBJ than what was actually rendered; regenerate to match the live generator,
     then copy it into the container `OctaneMCP/assets/`.
   - `scene.json` — camera/material/tier metadata matching the real pipeline.
   - `octane-preview.png` — a REAL Octane render (copy a produced PNG, or queue
     `save_preview` with a `quality` tier). `preview.png` — downscaled doc copy
     (`sips -s format png -Z 768 octane-preview.png --out preview.png`).
   - `README.md` — the actual one-live-session queue pipeline + tier table + gotchas.

### Skill source and deployment
`hermes/skills/<name>/` is the committed source of truth. Keep its `SKILL.md` and
linked references internally consistent, bump `version:` when they change, and
deploy/reload the installed Hermes skill through the host's normal skill-install
workflow. Do not make an unreviewed second source of truth in a profile directory.

## Related

- `octane-viz` — prompt-prefix ("Visualise") trigger skill.
- `octanex-mcp-overview` — full tool/launch reference (AppleScript + Computer Use + Vision trio).
- `octanex-mcp-review` — architecture review notes.
- `octanex-visual-loop` — the end-to-end local visual loop mandated by SOUL.md.
