---
name: octane-viz
description: >-
  If a prompt starts with "Visualise" (case-insensitive, prefix) then
  trigger an OctaneX MCP preview and return the PNG image preview result inline
  in the chat. Produces a REAL OctaneX render via the octanex-mcp project —
  never a model-generated image.
version: 1.3.1
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [octane-x, viz, preview, mcp, image, visualise]
    pattern: prompt starts with "Visualise"
    related_skills: [octanex-mcp, octanex-visual-loop, octanex-mcp-overview]
---

# OctaneX Visualisation Skill

## Trigger

Detect prompts that start with `Visualise` (case-insensitive).

The skill is triggered when the prompt prefix matches "Visualise" (accepting "Visualize" as a variant). On trigger, the default action is to produce a **real OctaneX render** via the octanex-mcp project and return the PNG preview inline in the chat.

### Examples of Triggering Prompts

- `Visualise a cube with glossy material`
- `Visualize the data bars scene`
- `Visualise with a green torus`
- `Visualise the helix with a copper material`
- `Visualise it simply`

### Non-Triggering Examples

- `Here is the result`
- `Please review the scene`

## Hard rule (SOUL.md)

A "Visualise…" prompt MUST produce a real OctaneX render. A model-generated image
(`image_generate`, `ollama-image-gen`, `comfyui`) is **never** the delivered product. Local
image generation may only be used as: (a) a planning **reference** image, or (b) a clearly
**labeled fallback** when Octane X is genuinely unavailable. If Octane X cannot run, state that
explicitly and stop — do not silently substitute a synthetic image.

## Behaviour

When triggered, execute these steps in order:

### 0. Confirm the toolchain (before anything else)

```bash
cd /Users/craig/octanex-mcp
uv run octanex-mcp doctor          # expect "Overall: ok"
pgrep -fl "Octane X" || echo "Octane X NOT running — ask the user to launch it"
```

If `doctor` fails or Octane X is not running, surface the blocker to the user. Do not fabricate a render.

### 1. Prepare the scene

- **Shape**: If the prompt contains an object/shape name (box, sphere, tetrahedron, torus, cylinder, pyramid, helix, etc.), construct that geometry using Octane X's standard shapes.
- **Material**: If the prompt includes a material or colour hint (glossy, gold, green, cyan, magenta, copper, etc.), apply it to the geometry. Otherwise construct a default glossy cube (size=3, centred) with a glossy-blue material.
- **Camera**: Use bounds-aware automatic framing (the visual tools compute camera from asset bounds) unless a deliberate top/front/side composition is wanted.
- **Lighting**: Apply soft-studio lighting preset.
- **Render**: Queue a render with reasonable defaults (samples=64, width=1280, height=1280).
- **Save PNG**: Queue `octane_save_preview` to capture the preview as a PNG under `~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/renders/`.

Map prompts to tools:

| Prompt | OctaneX tool |
|--------|--------------|
| `Visualise a cube with glossy material` | `octane_create_test_cube` + `octane_create_material` + `octane_assign_material` + render |
| `Visualize the data bars scene` | `octane_visualize_bars(...)` |
| `Visualise with a green torus` | torus geometry + green material + render |
| `Visualise it simply` | default glossy-blue cube + render |
| `Visualise the helix with a copper material` | helix geometry + copper material + render |

### 1.5. Render protocol (do this every time — prevents near-black/stale renders)

Follow the mandatory 8-step sequence from the `octanex-mcp` skill **Render
Protocol** section: (1) confirm Octane X running; (2) `File → New` reset;
(3) start the renderer (lua command queue); (4) one one-shot bridge click to
flush any stale queue; (5) queue the scene; (6) start the renderer (lua command
queue) again; (7) one-shot bridge click to drain; (8) repeat from (2) for the
next scene. **Octane is fast** — basic scenes converge for preview QA in
**1–2 s**, complex in **5–10 s**; do not over-cap render time. A stale queue or
leftover scene (not a material bug) is the usual cause of a near-black frame.

### 2. Drain the queue in Octane X

The bridge uses the **one-shot bridge** mode (`hermes_bridge_oneshot.generated`). Run it from
Octane X's Script menu, or trigger it via the control layer (which handles TCC + classification):

```bash
uv run python -c "from octanex_mcp.bridge_control import run_bridge_script; print(run_bridge_script('oneshot')['stdout'])"
# -> clicked hermes_bridge_oneshot.generated via Script
```

**Never use `run script file` on the `.lua` bridge** — AppleScript tries to compile the Lua as AppleScript and dies with `-2741` ("Expected end of line, but found ="). Use the Scripts-menu click (above) which runs it as Lua.

**Canonical drain rule — ONE click, then poll, never re-click on a timer.** A single oneshot click runs the Lua drain loop and processes the ENTIRE queue (assembly + `save_preview`) in one pass. After queueing the full pipeline, fire ONE `octane_run_oneshot_bridge` (or `run_bridge_script('oneshot')`), then poll `…/OctaneMCP/queue/` to confirm it hit 0. Do NOT loop one click per command, and do NOT re-click while the queue is empty — a second click while `save_preview` is rendering is ignored and would kill that render. Only re-click on a *genuine failed click*, capped.

**Warm-engine reset between recipes** (File ▸ New on the running Octane, NOT a cold quit/open-a relaunch):

```text
octane_reset_octane_scene()       # {ok:true} or {ok:false, kind:...}
```

**Application-control error taxonomy** (the control layer classifies these so the agent branches instead of blindly retrying):

| Symptom / code | Class | Action |
|---|---|---|
| `osascript` hangs then raises `TimeoutExpired` | `timed_out` | Octane busy/unresponsive modal. Wait, then retry once; if it persists, restart Octane. |
| `-1719` assistive access denied | `tcc_blocked` | Grant Accessibility to the **Hermes agent-runtime python** (`/Users/craig/.hermes/hermes-agent/venv/bin/python` — the osascript caller, NOT `Hermes.app`), or the shell/terminal that launches Hermes. |
| `-1700` can't make data into expected type | `busy` | Octane mid-render/modal. Wait for the render to settle; do NOT re-click blindly. |
| `-2741` expected end of line | `wrong_trigger` | You used `run script file` on Lua; use the Scripts-menu click path instead. |
| `Could not find <script> in Scripts menu` | `script_not_found` | Set Octane Preferences ▸ Scripts path → repo `octane_lua/`, then restart Octane. |

The launch now waits for Octane X's menu bar to become UI-ready after `open -a` (inside the same AppleScript), eliminating the cold-launch race that produced false "script not found".

**CRITICAL — never restart Octane X between `import_geometry` and `save_preview`.**
A restart purges the in-memory scene, so later commands render against an empty
scene → uniform gray `(243,243,243)` frame, ~16 KB, wasting a long render.
Restart Octane X only to reload a patched bridge, and do it *before* queueing any
scene command. Queue the whole import→…→save pipeline in ONE live session.

### 3. Inspect the render locally (vision gate)

Before returning the PNG, inspect it with `vision_analyze`:

- Downscale first: `sips -s format jpeg -Z 768 <preview>.png --out small.jpg`, then analyze `small.jpg`.
- Ask ONE tight factual question; take only the first line of the reply (auxiliary model loops on open-ended questions).
- Verify framing, scale, labels, subject correctness, and intent match. On mismatch, iterate the scene/render.

### 4. Return the result

- Provide the **real OctaneX preview PNG** inline in the chat.
- Include a brief caption with the material and colour if they were specified in the prompt.
- Report the actual file path, size, and timestamp of the PNG.

## Implementation Notes

- The preview is returned inline in the conversation chat.
- Works with both one-shot and persistent bridge modes.
- **Always drain the queue with the one-shot bridge** (`octane_run_oneshot_bridge` or the osascript one-shot trigger). The persistent bridge's auto-poll timer is **broken** (`timer create attempt 1 failed`), so it will NOT drain on its own — do not rely on it to auto-drain. Prefer one-shot for clean repaint on multi-command batches.
- **Materials with distinct colors:** `import_geometry` ignores MTL `Kd` (objects render black), and `assign_material` paints every group pin with one material. For a multi-color object, emit ONE combined OBJ with `usemtl` groups, `create_material` each color, then assign per-group — but the MCP `assign_material` tool lacks `group_index`, so write the queue JSON directly with `"payload": {"object_name":…, "material_name":…, "group_index": N}`. See `octanex-mcp` → Materials/Import gotchas.
- Clean up: do not leave test command files in `…/OctaneMCP/queue/`.

## Examples

| Prompt | Action |
|--------|--------|
| `Visualise a cube with glossy material` | Construct glossy cube, apply blue material, render, inspect, return real PNG preview |
| `Visualize the data bars scene` | Construct data bars, apply material, render, inspect, return real PNG preview |
| `Visualise with a green torus` | Construct torus, apply green material, render, inspect, return real PNG preview |
| `Visualise it simply` | Construct default cube with glossy blue, render, inspect, return real PNG preview |
| `Visualise the helix with a copper material` | Construct helix, apply copper material, render, inspect, return real PNG preview |
| `Visualise a photorealistic mathematical 3D surface` | Generate a parametric surface OBJ in Python (`octanex-mcp` → `scripts/gen_math_surface.py`), `import_geometry` + explicit glossy material + `assign_material` + camera/lighting + `save_preview`; drain repeatedly until `queue/` empty, then verify. See `octanex-mcp` → `references/photoreal-math-surface.md`. |