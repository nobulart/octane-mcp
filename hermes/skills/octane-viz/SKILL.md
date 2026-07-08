---
name: octane-viz
description: >-
  If a prompt starts with "Visualise" (case-insensitive, prefix) then
  trigger an OctaneX MCP preview and return the PNG image preview result inline
  in the chat. Produces a REAL OctaneX render via the octanex-mcp project —
  never a model-generated image.
version: 1.1.0
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

### 2. Drain the queue in Octane X

The bridge uses the **one-shot bridge** mode (`hermes_bridge_oneshot.generated`). Run it from
Octane X's Scripts menu, or trigger it:

```bash
osascript -e 'tell application "Octane X" to run script file "MacintoshHD:Users:craig:octanex-mcp:octane_lua:hermes_bridge_oneshot.generated.lua"'
```

Run the one-shot bridge after queueing the scene AND again after queueing the preview save.

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
- If an existing persistent bridge is active, it drains the queue automatically (1 s poll), but prefer one-shot for clean repaint on multi-command batches.
- Clean up: do not leave test command files in `…/OctaneMCP/queue/`.

## Examples

| Prompt | Action |
|--------|--------|
| `Visualise a cube with glossy material` | Construct glossy cube, apply blue material, render, inspect, return real PNG preview |
| `Visualize the data bars scene` | Construct data bars, apply material, render, inspect, return real PNG preview |
| `Visualise with a green torus` | Construct torus, apply green material, render, inspect, return real PNG preview |
| `Visualise it simply` | Construct default cube with glossy blue, render, inspect, return real PNG preview |
| `Visualise the helix with a copper material` | Construct helix, apply copper material, render, inspect, return real PNG preview |
