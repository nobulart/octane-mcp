---
name: octane-viz
description: >-
  If a prompt starts with "Visualise" (case-insensitive, prefix) then
  trigger an OctaneX MCP preview and return the PNG image preview result inline in the chat.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [octane-x, viz, preview, mcp, image, visualise]
    pattern: prompt starts with "Visualise"
---

# OctaneX Visualisation Skill

## Trigger

Detect prompts that start with `Visualise` (case-insensitive).

The skill is triggered when the prompt prefix matches "Visualise" (accepting "Visualize" as a variant). On trigger, the default action is to trigger an OctaneX MCP preview and return the PNG image preview result inline in the chat.

### Examples of Triggering Prompts

- `Visualise a cube with glossy material`
- `Visualize the data bars scene`
- `Visualise with a green torus`
- `Visualise the helix with a copper material`
- `Visualise it simply`

### Non-Triggering Examples

- `Here is the result`
- `Please review the scene`

## Behaviour

When triggered, execute these steps in order:

### 1. Prepare the scene

- **Shape**: If the prompt contains an object/shape name (box, sphere, tetrahedron, torus, cylinder, pyramid, helix, etc.), construct that geometry using Octane X's standard shapes.
- **Material**: If the prompt includes a material or colour hint (glossy, gold, green, cyan, magenta, copper, etc.), apply it to the geometry. Otherwise construct a default glossy cube (size=3, centred) with a glossy-blue material.
- **Camera**: Position the camera according to the object's bounding box to ensure good framing.
- **Lighting**: Apply soft-studio lighting preset.
- **Render**: Start a render with reasonable defaults (samples=64, width=1280, height=1280).
- **Save PNG**: Capture the preview as a PNG and return it inline in the chat.

### 2. Return the result

- Provide the PNG image preview result inline in the chat.
- Include a brief caption with the material and colour if they were specified in the prompt.

## Implementation Notes

- The bridge uses the one-shot bridge mode (`hermes_bridge_oneshot.generated`).
- The preview is returned inline in the conversation chat.
- Works with both one-shot and persistent bridge modes.
- If an existing bridge is active (persistent mode), it drains the queue automatically.

## Examples

| Prompt | Action |
|--------|--------|
| `Visualise a cube with glossy material` | Construct glossy cube, apply blue material, return PNG preview |
| `Visualize the data bars scene` | Construct data bars, apply material, return PNG preview |
| `Visualise with a green torus` | Construct torus, apply green material, return PNG preview |
| `Visualise it simply` | Construct default cube with glossy blue, return PNG preview |
| `Visualise the helix with a copper material` | Construct helix, apply copper material, return PNG preview |
