---
name: octanex-mcp
description: Use when configuring, testing, or operating the OctaneX MCP server from Hermes Agent, especially for queue draining, render-ready PNG previews, and local vision review loops.
version: 1.1.0
author: OctaneX MCP contributors
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [octanex, mcp, rendering, vision, lua-bridge]
    related_skills: [octane-viz, octanex-mcp-overview, octanex-mcp-review, octanex-visual-loop]
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

2. Add the MCP server to Hermes config (`~/.hermes/config.yaml`):

   ```yaml
   mcp_servers:
     octanex:
       command: "/opt/homebrew/bin/uv"
       args: ["run", "--project", "/Users/craig/octanex-mcp", "octanex-mcp"]
       timeout: 180
       connect_timeout: 30
   ```

   Use the absolute path to `uv` (`which uv`) so Hermes does not depend on the login shell PATH. Completion: `hermes mcp list` shows `octanex`, and `hermes mcp test octanex` connects after a Hermes reload/restart.

3. In Octane X Preferences, set **Scripts path** to this checkout's `octane_lua/` directory:

   ```text
   /Users/craig/octanex-mcp/octane_lua
   ```

   Completion: Octane X's Script menu shows `hermes_bridge_oneshot.generated` and `hermes_bridge_persistent.generated`. Restart Octane X if the scripts do not appear after changing the preference.

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

   Prefer `hermes_bridge_oneshot.generated` for multi-command scene batches because it exits and lets Octane repaint. Use the persistent bridge only when you need an open window that keeps polling. Reliable trigger:

   ```bash
   osascript -e 'tell application "Octane X" to run script file "MacintoshHD:Users:craig:octanex-mcp:octane_lua:hermes_bridge_oneshot.generated.lua"'
   ```

   **Use `run script file` (Scripts menu / osascript), not `open location`** — `open location` can leave the viewport stale. AppleScript control of Octane X requires automation permission (System Settings -> Privacy -> Automation -> Octane X); verify with `osascript -e 'tell application "Octane X" to get name'`.

   Completion: queued commands move to `processed/` or `failed/`, and `results/*.json` records each outcome. Check `queue/` is empty, not just `processed_count` climbing.

5. Save a PNG preview:

   ```text
   octane_save_preview(width=1280, height=1280, samples=64, min_samples=16, timeout_seconds=10)
   ```

   Completion: the bridge restarts rendering, waits for render statistics to become ready, then writes a PNG under `renders/`. Default path: `~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/renders/`. Run the one-shot bridge again after queueing the preview save.

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

## Bridge Debugging

- If queue grows but nothing is processed, run the one-shot bridge from Octane X's Script menu or via the osascript trigger above.
- If `status.json` is stale, trust current queue/result files over old status.
- If preview save fails immediately after a scene mutation, use the current bridge templates: they call `render.restart()`, wait for `getRenderResultStatistics().beautySamplesPerPixel >= 16`, then `saveImage(path, PNG8)`.
- If geometry appears duplicated or stale, clear the Octane scene before re-importing. Octane appends imported geometry unless the node tree is flushed.
- Persistent bridge may leave the viewport stale (mode cycles active -> one_shot -> closed -> available). Prefer one-shot for batches.

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
