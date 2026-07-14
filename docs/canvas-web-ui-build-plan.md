# OctaneX Web UI Build Plan

**Status:** Implementation plan.  
**Date:** 2026-07-13.  
**Scope:** Agentic Canvas web UI, three.js/WebGL realtime preview, geo/Copernicus path, and Octane quality-render handoff.  
**Related docs:** `docs/canvas-roadmap.md`, `docs/canvas-implementation-roadmap.md`, `docs/visualization-backends-research.md`, `docs/roadmap.md` WP15, `docs/WIP.md` items K/L.

---

## 1. Objective

Build the OctaneX Agentic Canvas as a local-first, agent-controlled 3D workbench:

```text
user intent -> agent scene plan -> live browser 3D preview -> optional Octane quality render -> visual review -> editable scene memory
```

The web UI should become the interactive front end of OctaneX, not just a display surface for Octane PNGs.

The dated `reports/dashboard-proposal/octanex-agentic-canvas.html` proposal had the correct aesthetic and interaction stance: dark render-first canvas, single persistent command bar, corner intent/status pills, reveal-on-demand palette/inspector, and honest progress. This plan keeps that aesthetic but updates the architecture around the current codebase and the newer renderer-backend research.

---

## 2. Core product decision

Use a two-tier render model:

| Tier | Backend | Role |
|---|---|---|
| Realtime | three.js / WebGL | Interactive scene building, camera control, data/math/geometry preview, fast agentic iteration. |
| Geo | CesiumJS or deck.gl | Real globe/maps/terrain/time layers; Copernicus and GIS data as source layers. |
| Quality | Octane X | Photoreal/high-quality final render, studio scenes, glass/metal/atmosphere. |
| Later | Blender, Mitsuba, OSPRay, Godot | Optional backends after WebGL proves the abstraction. |

Therefore: **three.js first**, **Cesium/deck.gl second for geo**, **Copernicus as a data source**, and **Octane retained as the quality tier**.

The interaction loop changes from:

```text
intent -> Octane queue -> wait -> PNG
```

to:

```text
intent -> scene JSON -> immediate WebGL preview
                  |
                  +-> optional Octane quality render -> PNG review
```

This is the main UX unlock: the user sees a useful approximate scene almost immediately, then decides whether to spend Octane time for a final render.

---

## 3. Current implementation baseline

### Already present

#### Native host

`apps/octanex-canvas/Sources/octanex-canvas/main.swift`

- SwiftPM executable, not Electron.
- Opens a native `WKWebView`.
- Loads `apps/octanex-canvas/web/index.html`.
- Starts `octanex_mcp.gateway` as a child process.
- Passes `OCTANEX_RENDER_HOST` through for Mac Studio thin-client rendering.

#### HTTP gateway

`src/octanex_mcp/gateway.py`

Current routes include:

- `GET /health`
- `GET /config`
- `GET /status`
- `GET /preview`
- `POST /mcp/call`
- `POST /intent`
- `POST /remote/render`
- dispatch daemon routes

Current dispatch includes status, recipe index/book/load/queue, preview review, camera/lighting suggestions, geometry import/swap, start/save render, animation build, and promoted recipe wrappers.

#### Web bundle

`apps/octanex-canvas/web/`

Current UI already implements:

- full-bleed viewport;
- bottom command bar;
- status pill;
- `Cmd-K` palette;
- `Cmd-I` inspector;
- `~` focus mode;
- preview polling;
- status polling;
- recipe queueing;
- preview review / suggested camera fix.

#### Verification baseline

Observed 2026-07-13:

```bash
cd apps/octanex-canvas && swift build
# Build complete

PYTHONPATH= uv run python -m unittest tests.test_gateway tests.test_status_schema tests.test_progressive_save -v
# Ran 13 tests ... OK
```

### Missing

The app is currently a **PNG preview viewer + HUD**, not a live 3D renderer.

Missing pieces:

1. Stable browser-hydratable scene JSON.
2. three.js renderer that hydrates that scene JSON.
3. Python-side `WebGLBackend` that emits browser scene JSON from the existing scene DSL.
4. Gateway routes for live scene state and events.
5. Camera/orbit/picking/selection feedback from browser to agent.
6. Inspector controls bound to real scene objects, not only preview review.
7. Geo-specific rendering path.
8. Snapshot path from browser/WKWebView canvas to PNG for existing pixel-review discipline.
9. Better agentic loop: intent planning, tool-plan summaries, scene timeline, and patches.

---

## 4. Design principles

1. **Render-first.** The visual output owns the screen. HUD elements are edge-anchored and dismissible.
2. **One permanent control.** The command bar is the stable entry point for text, voice later, recipes, and references.
3. **Realtime before photoreal.** WebGL gives fast approximate feedback; Octane gives final quality.
4. **Confidence over control.** Show what the system heard, what it built, and what stage it is in.
5. **Honest latency.** Use real queue/status/dispatch/preview state. Do not fake progress.
6. **Local-first.** No cloud requirement for the base path.
7. **Renderer-neutral core.** Browser, geo, and Octane consume a shared scene/intent model rather than becoming separate products.
8. **Verification survives backend changes.** Pixel/structure checks before vision apply to WebGL snapshots as well as Octane PNGs.

---

## 5. Proposed architecture

```text
Craig / Hermes
   |
   v
Intent / command bar
   |
   v
octanex_mcp gateway
   |
   +-- /intent
   |     records intent, then later invokes planner
   |
   +-- /canvas/scene
   |     current browser-hydratable scene JSON
   |
   +-- /canvas/events
   |     camera, selection, drag, and patch events
   |
   +-- /mcp/call
   |     existing MCP-like tool wrapper
   |
   +-- Backend abstraction
         |
         +-- OctaneBackend
         |     existing queue/Lua/PNG path
         |
         +-- WebGLBackend
         |     emits three.js scene JSON
         |
         +-- GeoBackend
               emits Cesium/deck.gl scene config
```

Browser side:

```text
apps/octanex-canvas/web/
  index.html
  app.css
  app.js
  vendor/three.module.js              # initial no-build option
  canvas/
    renderer.js
    sceneStore.js
    controls.js
    selection.js
    snapshot.js
```

Python side:

```text
src/octanex_mcp/
  backends/
    __init__.py
    base.py
    octane_backend.py
    webgl_backend.py
    geo_backend.py                    # later
  canvas_scene.py
  gateway.py
```

Tests:

```text
tests/
  test_backend_protocol.py
  test_webgl_backend.py
  test_canvas_scene_schema.py
  test_gateway_canvas_routes.py
```

---

## 6. Canvas scene JSON contract

Do not make the browser interpret arbitrary Octane commands. Give it a flattened, safe, renderer-neutral scene format.

Initial shape:

```json
{
  "schema_version": "canvas.scene.v1",
  "scene_id": "orbital_decay_demo",
  "title": "Orbital decay timeline",
  "intent": "show me orbital decay as a timeline",
  "units": "arbitrary",
  "camera": {
    "position": [4, 3, 4],
    "target": [0, 0, 0],
    "fov": 45
  },
  "environment": {
    "background": "#070a0e",
    "lighting": "soft_studio"
  },
  "objects": [
    {
      "id": "earth",
      "label": "#1",
      "type": "sphere",
      "position": [0, 0, 0],
      "scale": [1, 1, 1],
      "material": "blue_planet"
    },
    {
      "id": "orbit_path",
      "label": "#2",
      "type": "polyline",
      "points": [[1, 0, 0], [0.7, 0.5, 0], [0.4, 0.6, 0]],
      "radius": 0.015,
      "material": "cyan_emissive"
    }
  ],
  "materials": [
    {
      "id": "blue_planet",
      "color": "#2f8fff",
      "roughness": 0.6,
      "metalness": 0.0,
      "opacity": 1.0
    },
    {
      "id": "cyan_emissive",
      "color": "#35e0d8",
      "emissive": "#35e0d8",
      "emissiveIntensity": 1.5
    }
  ],
  "annotations": [
    {
      "id": "label_decay",
      "text": "decaying orbit",
      "target": "orbit_path"
    }
  ],
  "provenance": {
    "source": "agent",
    "source_instruction_id": "msg_001",
    "created_at": "2026-07-14T12:00:00Z"
  },
  "ledger": [
    {
      "event_id": "evt_001",
      "type": "user_instruction",
      "summary": "show me orbital decay as a timeline",
      "actor": "user",
      "timestamp": "2026-07-14T12:00:00Z"
    },
    {
      "event_id": "evt_002",
      "type": "scene_build",
      "summary": "Created earth and orbit path from the instruction.",
      "actor": "agent",
      "revision_to": "rev_001",
      "affected_objects": ["earth", "orbit_path"]
    }
  ]
}
```

Initial supported object types:

| Type | three.js implementation | Octane mapping |
|---|---|---|
| `box` | `BoxGeometry` | OBJ primitive |
| `sphere` / `ellipsoid` | `SphereGeometry` + scale | OBJ primitive |
| `cylinder` | `CylinderGeometry` | OBJ primitive |
| `mesh` | OBJ/glTF loader later | `import_geometry` |
| `polyline` | tube/line geometry | future tube OBJ |
| `points` | `Points` / instanced spheres | point-cloud path |
| `arrow` | cylinder + cone | future primitive |
| `text_label` | CSS2D / sprite | annotation only |

Keep this schema intentionally smaller than Octane's full command DSL at first.
The `ledger` field is optional in the first implementation, but any committed
scene mutation or render handoff should eventually append a compact event. The
browser may display a short timeline, but Python-owned scene state remains the
canonical record.

---

## 7. Phase plan

### Phase 0 — Stabilise current Canvas app

**Goal:** confirm the current Swift/gateway/web shell is the base.

Tasks:

1. Keep `apps/octanex-canvas` as the host.
2. Add a gateway health/operator indicator.
3. Expose capabilities through the gateway (`octane_capabilities` or `/capabilities`).
4. Add a basic operator panel:
   - gateway running;
   - dispatch loop running;
   - Octane available;
   - queue count;
   - last preview path;
   - render host.

Files:

- `apps/octanex-canvas/web/app.js`
- `apps/octanex-canvas/web/app.css`
- `src/octanex_mcp/gateway.py`
- `tests/test_gateway.py`

Acceptance:

- `swift build` passes.
- Existing gateway/canvas tests pass.
- UI can show gateway status when Octane is not running.
- No change to Octane bridge behavior.

### Phase 1 — Introduce renderer backend abstraction

**Goal:** make Octane one backend, not the architecture.

Tasks:

1. Create `src/octanex_mcp/backends/`.
2. Define a minimal `Backend` protocol.
3. Keep `OctaneBackend` as a thin wrapper over existing functions initially.
4. Implement `WebGLBackend.build(scene)` as a pure conversion to `canvas.scene.v1`.
5. Do not rewrite existing MCP tools yet.

Suggested interface:

```python
class Backend(Protocol):
    name: str

    def build(self, scene: Mapping[str, Any]) -> Mapping[str, Any]:
        ...

    def render_preview(self, scene: Mapping[str, Any]) -> Mapping[str, Any]:
        ...

    def save_png(self, scene: Mapping[str, Any], path: str | None = None) -> Mapping[str, Any]:
        ...
```

Tests:

- `tests/test_backend_protocol.py`
- `tests/test_webgl_backend.py`

Acceptance:

- In-memory fake backend test passes.
- WebGL backend converts a basic sphere/box scene to valid canvas JSON.
- Existing gateway tests still pass.
- No Octane behavior changes.

### Phase 2 — Browser-side three.js renderer

**Goal:** replace PNG-only viewport with a live WebGL scene layer.

Dependency choice:

- Start with a vendored pinned `three.module.js` under `apps/octanex-canvas/web/vendor/` to avoid introducing a Node build step during the proof-of-pipeline.
- Move to Vite/TypeScript only if the JS grows enough to justify it.

Tasks:

1. Add `apps/octanex-canvas/web/canvas/renderer.js`.
2. Add `sceneStore.js`, `controls.js`, `selection.js`, and `snapshot.js` as needed.
3. Update `index.html` with `<canvas id="webgl-canvas">`.
4. Keep `#preview` as optional Octane final-render overlay.
5. Add view modes: `Live`, `Octane Preview`, and `Split`.
6. Hydrate `canvas.scene.v1` into primitives, materials, camera, and labels.
7. Add orbit/pan/zoom and object picking.

Acceptance:

- App shows a live three.js scene with no Octane running.
- User can orbit/pan/zoom.
- `~` hides HUD and leaves pure scene.
- Existing preview PNG mode still works.
- No network/cloud dependency.

### Phase 3 — Gateway canvas routes

**Goal:** bridge Python scene state and browser scene state.

Add routes:

```text
GET  /canvas/scene
POST /canvas/scene
POST /canvas/build
POST /canvas/event
POST /canvas/snapshot
GET  /canvas/history
```

Route behavior:

| Route | Behavior |
|---|---|
| `GET /canvas/scene` | Return latest `canvas.scene.v1`. |
| `POST /canvas/scene` | Store full scene JSON. |
| `POST /canvas/build` | Accept an existing scene plan, convert via `WebGLBackend`, store and return scene. |
| `POST /canvas/event` | Record camera/selection/interaction events. |
| `POST /canvas/snapshot` | Receive PNG data URL or trigger WK snapshot later. |
| `GET /canvas/history` | Return scene/timeline metadata. |

Workspace-local state:

```text
OctaneMCP/
  canvas/
    current.scene.json
    events.jsonl
    snapshots/
      <scene_id>-<ts>.png
```

Tests:

- `tests/test_gateway_canvas_routes.py`
- `tests/test_canvas_scene_schema.py`

Acceptance:

- Browser loads scene from `/canvas/scene`.
- Browser can POST camera/selection events.
- Tests pass without Octane.
- No arbitrary file writes outside workspace.

### Phase 4 — Agentic interaction loop

**Goal:** make the command bar create/change scenes, not only log intent.

Current `/intent` appends to `intents.jsonl`. Keep that audit trail, but add a deterministic first planner before LLM/agent integration.

Stub planner patterns:

| Intent pattern | Output |
|---|---|
| `cube` | cube scene |
| `sphere` | sphere scene |
| `orbit` | sphere + orbital line |
| `bar chart` | bars |
| `terrain` | placeholder terrain grid |
| otherwise | neutral demo scene + intent metadata |

Later agent path:

```text
POST /intent
  -> record user intent
  -> ask agent/planner for scene_plan
  -> run octane_check_scene_plan
  -> WebGLBackend emits canvas.scene.v1
  -> browser updates immediately
  -> optional OctaneBackend queues quality render
```

UI changes:

- Intent pill shows exact interpreted intent.
- Status pill shows `heard -> planning -> live preview -> octane queued -> rendering -> reviewed`.
- Command palette groups recipes, scene templates, and tools by purpose.
- Inspector edits selected object from live scene JSON.

Acceptance:

- Typing “show orbital decay as a timeline” produces a live scene without Octane.
- Browser displays interpreted intent.
- Object selection shows inspector details.
- Inspector edits mutate scene JSON and redraw.

### Phase 5 — Inspector as real scene editor

**Goal:** make `Cmd-I` useful for editing the live scene.

Inspector panels:

1. **Scene** — title, intent, backend, object count, render target.
2. **Selection** — id, label, type, position, scale, material.
3. **Camera** — position, target, FOV, reset to auto-frame.
4. **Materials** — color, opacity, roughness, emissive intensity.
5. **Agent suggestions** — camera too close, object clipped, increase contrast, send to Octane.

Acceptance:

- Select object in 3D view.
- Inspector updates.
- Change color/scale/position.
- Scene redraws.
- Changes can be sent to Octane as a quality render.

### Phase 6 — Octane quality render handoff

**Goal:** make WebGL preview and Octane final render cooperate.

Flow:

```text
Live three.js scene
   |
   +-- Render in Octane
         |
         v
      convert canvas scene / original scene plan
         |
         v
      OctaneBackend queue
         |
         v
      bridge drain
         |
         v
      preview.png
         |
         v
      UI shows final preview / comparison
```

Requirements:

- Preserve original scene plan when possible.
- Do not round-trip through lossy browser JSON if a richer scene plan exists.
- If the scene started in browser-only mode, provide a best-effort Octane export:
  - primitives -> OBJ or native primitive scene plan;
  - materials -> basic PBR;
  - camera/lighting mapped.

UI modes:

- `Live` — WebGL interactive.
- `Final` — Octane PNG.
- `Compare` — split or overlay.
- `Review` — pixel QA / vision summary.

Acceptance:

- A live WebGL scene can be sent to Octane.
- Status shows truthful Octane progress from `status.json`.
- Final PNG appears.
- `octane_review_preview` result is visible in inspector.
- No success is claimed if the PNG is blank or low-deviation.

---

## 8. Geo / Copernicus / Cesium path

The right geo path is not “render Copernicus with Octane first.” It is:

```text
Copernicus / DEM / GeoJSON / KML / NetCDF
   |
   v
Python data adapters
   |
   +-- web geo scene config
   |     -> CesiumJS / deck.gl
   |
   +-- mesh extraction
         -> Octane quality render if needed
```

### Renderer choice

| Need | Preferred renderer |
|---|---|
| ECDO/TPW/global narratives | CesiumJS |
| Impact sites, arcs, point layers | deck.gl |
| Terrain tiles / 3D globe | CesiumJS |
| Fast 2.5D data viz | deck.gl |
| Shareable browser output | either |

### Copernicus role

Copernicus should enter as a data adapter under a later source layer:

```text
src/octanex_mcp/geo_sources/
  copernicus.py
  dem.py
  geojson.py
  kml.py
```

Initial geo scene contract:

```json
{
  "schema_version": "canvas.geo.v1",
  "backend": "cesium",
  "camera": {"lon": 0, "lat": 20, "height": 20000000},
  "layers": [
    {
      "id": "impact_sites",
      "type": "point_layer",
      "data": "assets/impact_sites.geojson",
      "color": "#35e0d8"
    },
    {
      "id": "trajectory",
      "type": "arc_layer",
      "data": "assets/trajectory.json"
    }
  ]
}
```

Geo acceptance:

- Load a small local GeoJSON.
- Render it in the Canvas without Octane.
- Camera fly-to works.
- Layer toggles work.
- Optional: export static PNG for review.
- Later: same data can be converted to OBJ for Octane final render.

---

## 9. Recommended implementation sequence

### Sprint 1 — WebGL proof

1. Add `canvas_scene.py`.
2. Add `backends/base.py`.
3. Add `backends/webgl_backend.py`.
4. Add `/canvas/scene` and `/canvas/build` routes.
5. Add three.js canvas renderer.
6. Render primitive scene live.
7. Keep PNG preview mode intact.

**Definition of done:** app opens and shows a live interactive three.js scene without Octane.

### Sprint 2 — Agentic scene loop

1. Upgrade `/intent` from log-only to deterministic stub planner.
2. Add intent/status timeline.
3. Add object selection.
4. Bind inspector to selected object.
5. Add scene patch route.
6. Add tests for scene updates.

**Definition of done:** user types an intent, gets a live editable scene, selects an object, changes it, and sees the update.

### Sprint 3 — Octane handoff

1. Add “Render in Octane” action.
2. Map WebGL/canvas scene back to existing scene plan or queue commands.
3. Show Octane progress.
4. Show final PNG.
5. Show review result.
6. Add compare mode.

**Definition of done:** live preview -> Octane final render -> QA verdict, with no hidden state.

### Sprint 4 — Geo track

1. Add `canvas.geo.v1`.
2. Spike deck.gl or Cesium.
3. Load one local GeoJSON layer.
4. Add camera fly-to and layer toggle.
5. Research Copernicus adapter requirements against real dataset/API constraints.

**Definition of done:** geospatial data appears as a real interactive web scene, not a static OBJ approximation.

---

## 10. Concrete first PR

### Title

`feat(canvas): add WebGLBackend and live three.js scene route`

### Files to create

```text
src/octanex_mcp/backends/__init__.py
src/octanex_mcp/backends/base.py
src/octanex_mcp/backends/webgl_backend.py
src/octanex_mcp/canvas_scene.py
tests/test_canvas_scene_schema.py
tests/test_webgl_backend.py
```

### Files to modify

```text
src/octanex_mcp/gateway.py
apps/octanex-canvas/web/index.html
apps/octanex-canvas/web/app.js
apps/octanex-canvas/web/app.css
apps/octanex-canvas/README.md
```

### Initial routes

```text
GET  /canvas/scene
POST /canvas/build
```

### Verification

```bash
PYTHONPATH= uv run python -m unittest tests.test_gateway tests.test_canvas_scene_schema tests.test_webgl_backend -v
PYTHONPATH= uv run python -m compileall src
cd apps/octanex-canvas && swift build
```

### Acceptance

- `POST /canvas/build` with a simple sphere scene returns `canvas.scene.v1`.
- Browser displays that scene with three.js.
- Existing preview/status HUD remains functional.
- App still builds via SwiftPM.
- No Octane dependency for this path.

---

## 11. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Browser renderer grows into a second unsynchronised scene system | Keep `canvas.scene.v1` generated from Python; browser hydrates, but core semantics stay server-side. |
| Octane and WebGL materials diverge | Define a small common material subset first: color, opacity, roughness, metalness, emissive. |
| JS complexity grows without tooling | Start vanilla; migrate to Vite/TypeScript only after renderer modules become hard to maintain. |
| Geo scope explodes | Treat geo as separate `canvas.geo.v1`; do not force Cesium concepts into generic scene JSON. |
| Snapshot path gets flaky | First support browser-side `canvas.toDataURL`; later add WKWebView-native snapshot. |
| Agent misinterpretation | Distinguish discussion, proposal, accepted mutation, and render. Show interpreted intent before acting when ambiguity matters; record committed changes in the design ledger. |
| Octane bridge fragility contaminates UI | WebGL path must work fully without Octane; Octane is optional quality tier. |

---

## 12. Bottom line

The Web UI should not be only an Octane dashboard. It should be a realtime agentic 3D canvas with Octane as the final-quality renderer.

Recommended stack:

- **Host:** existing Swift `WKWebView`.
- **Gateway:** existing `octanex_mcp.gateway`, extended.
- **Realtime renderer:** three.js first.
- **Geo renderer:** CesiumJS or deck.gl second.
- **Copernicus:** data-source adapter, not renderer.
- **Final render:** existing Octane queue/bridge.
- **Architecture:** WP15 backend abstraction, implemented minimally and incrementally.

First build target:

> Type an intent, generate a scene JSON, see it live in three.js immediately, then optionally send it to Octane for a quality render and QA review.
