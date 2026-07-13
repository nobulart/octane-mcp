# OctaneX Agentic Canvas (native host)

Thin native Swift + `WKWebView` shell that renders the Agentic Canvas web bundle
and (optionally) launches the local HTTP gateway. No Electron, no Octane-plugin
UI injection.

## Build & run

```sh
cd apps/octanex-canvas
swift build
swift run
```

The app will:

1. Open a window hosting `web/index.html` via `WKWebView`.
2. Launch `octanex_mcp.gateway` (the localhost HTTP wrapper over the MCP tools)
   as a child process, so the web bundle has an endpoint to call.
3. Pass through `OCTANEX_RENDER_HOST` if set in the app's environment, enabling
   the Mac Studio thin-client path.

## Mac Studio thin client

```sh
OCTANEX_RENDER_HOST=mac-studio.local swift run
```

Requires shared-key SSH to the host named by `OCTANEX_RENDER_HOST` and the same
OctaneMCP workspace layout on both machines (the gateway `scp`s the preview back).

## Overrides

- `OCTANEX_WEB_DIR` — point at a different web bundle directory.
- `OCTANEX_GATEWAY_WEB_DIR` / `OCTANEX_GATEWAY_PORT` — gateway-side knobs.

## Live WebGL tier (no Octane required)

The viewport is a realtime three.js scene layer, not just an Octane PNG viewer.
The flow is:

```
intent -> POST /canvas/build -> WebGLBackend emits canvas.scene.v1
       -> browser hydrates scene with three.js (immediate, no Octane)
       -> (optional) Final mode renders in Octane and shows the PNG overlay
```

- `web/canvas/renderer.js` — hydration + orbit/pan/zoom + object picking.
- `web/vendor/three.module.js` — vendored, pinned (no Node build step yet).
- View modes (bottom-left toggle): **Live** (WebGL), **Final** (Octane PNG),
  **Split** (WebGL left / Octane right).

### Gateway routes (canvas)

| Route | Behavior |
|---|---|
| `GET  /canvas/scene` | Current `canvas.scene.v1` (404 until a build runs). |
| `POST /canvas/build` | Accept `{intent}` or `{scene}`; `WebGLBackend` emits `canvas.scene.v1`, stored server-side and returned. 422 on invalid plan. |

### Python modules

- `src/octanex_mcp/canvas_scene.py` — `canvas.scene.v1` schema, validation, and
  the deterministic stub planner (`plan_scene`) used until the LLM/agent loop lands.
- `src/octanex_mcp/backends/` — `Backend` protocol, `FakeBackend` (tests), and
  `WebGLBackend` (pure conversion to `canvas.scene.v1`).

## Notes

- Packaged as a SwiftPM executable (not a `.app` bundle) for scriptability; if
  `WKWebView` needs entitlements/signing later, wrap in an Xcode target.
- The gateway is a *separate process* from the Hermes-registered stdio MCP
  server, so this app never disturbs Hermes's MCP registration.
