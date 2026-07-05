---
name: octanex-mcp
description: Use when configuring, testing, or operating the OctaneX MCP server from Hermes Agent, especially for queue draining, render-ready PNG previews, and local vision review loops.
version: 1.0.0
author: OctaneX MCP contributors
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [octanex, mcp, rendering, vision, lua-bridge]
    related_skills: []
---

# OctaneX MCP

## Overview

OctaneX MCP lets Hermes Agent use Octane X as a local visual canvas. Hermes queues allow-listed JSON commands through the Python MCP server, Octane X runs the Lua bridge from `octane_lua/`, and results come back as command JSON plus PNG previews that can be reviewed with local vision.

## When to Use

Use this skill when an agent needs to:

- configure a fresh Hermes/OctaneX MCP setup;
- queue and drain Octane scene commands;
- create a quick geometry/data/math visualization;
- trigger a PNG preview and review it locally;
- debug a queue that is not being picked up by Octane X.

Do not use this skill for arbitrary Lua execution. The bridge is intentionally an allow-listed command DSL.

## Setup Checklist

1. Initialize the repo and generated Lua scripts:

   ```bash
   PYTHONPATH= uv run octanex-mcp init
   PYTHONPATH= uv run octanex-mcp doctor
   ```

   Completion: `doctor` reports the workspace, generated bridges, and Octane X app path.

2. Add the MCP server to Hermes config:

   ```yaml
   mcp_servers:
     octanex:
       command: "uv"
       args: ["run", "--project", "/ABSOLUTE/PATH/TO/octanex-mcp", "octanex-mcp"]
       timeout: 180
       connect_timeout: 30
   ```

   Completion: `hermes mcp test octanex` succeeds after Hermes reload/restart.

3. In Octane X Preferences, set Scripts path to this checkout's `octane_lua/` directory.

   Completion: Octane X's Script menu shows `hermes_bridge_oneshot.generated` and `hermes_bridge_persistent.generated`.

## Standard Agent Loop

1. Read status:

   ```text
   octane_status()
   ```

   Completion: note queue counts, bridge status, and workspace path.

2. Queue a scene, for example:

   ```text
   octane_visualize_bars(values=[3, 1, 4, 1, 5], name="pi_digits")
   ```

   Completion: command JSON files appear under the workspace queue.

3. Drain the queue in Octane X.

   Prefer `hermes_bridge_oneshot.generated` for multi-command scene batches because it exits and lets Octane repaint. Use the persistent bridge only when you need an open window that keeps polling.

   Completion: queued commands move to `processed/` or `failed/`, and `results/*.json` records each outcome.

4. Save a PNG preview:

   ```text
   octane_save_preview(width=1280, height=1280, samples=64, min_samples=16, timeout_seconds=10)
   ```

   Completion: the bridge restarts rendering, waits for render statistics to become ready, then writes a PNG under `renders/`.

5. Review the PNG locally:

   ```text
   octane_review_preview(path="/path/to/preview.png")
   ```

   Completion: use `ok`, `issues`, `metrics`, and recommended actions before claiming the visual result is good.

## Bridge Debugging

- If queue grows but nothing is processed, run the one-shot bridge from Octane X's Script menu.
- If `status.json` is stale, trust current queue/result files over old status.
- If preview save fails immediately after a scene mutation, use the current bridge templates: they call `render.restart()`, wait for `getRenderResultStatistics().beautySamplesPerPixel >= 16`, then `saveImage(path, PNG8)`.
- If geometry appears duplicated or stale, clear the Octane scene before re-importing. Octane appends imported geometry unless the node tree is flushed.

## Verification Checklist

- [ ] `PYTHONPATH= uv run octanex-mcp doctor` reports expected paths.
- [ ] `hermes mcp test octanex` succeeds.
- [ ] Queue files move to `processed/` after running a bridge.
- [ ] `octane_save_preview` produces a non-empty PNG file.
- [ ] `octane_review_preview` can decode the PNG and returns actionable metrics.
- [ ] Any new pitfall is recorded in `docs/recipe-book.md` or a recipe README.
