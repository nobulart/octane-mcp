# Realtime Visualization Backend Options for octanex-mcp

**Status:** Research report, decision input. Date: 2026-07-13.
**Author:** Hermes (research pass for Craig).
**Companion docs:** `docs/canvas-roadmap.md`, `docs/canvas-implementation-roadmap.md`,
`docs/visual-grammar.md`, `README.md`.

---

## 0. Why this report exists

`octanex-mcp` today is *one thing*: a bridge that drives **Octane X** (a closed Otoy
binary) as the render backend for an agentic visual canvas. The pipeline is:

```
Hermes / Python generator -> OBJ asset -> MCP command queue
  -> Octane Lua bridge (UI-scripted via AppleScript)
  -> Octane X render target -> PNG preview -> Hermes vision review
```

Octane is a strong *photoreal* tier, but its integration has structural costs that are
independent of the agent's visualization logic:

- **No CLI, no plugin API.** Octane X is driven by UI-scripting its Scripts menu
  (`osascript` → AppleScript → TCC Accessibility on the agent-runtime python). This is
  the single largest source of fragility in the project (see `octanex-mcp-project`
  skill, TCC `-1719` / `-2741` history).
- **macOS sandbox pathing.** The bridge must write to the real Container FS path, not
  the apparent `~/OctaneMCP`. `saveImage` re-bases absolute paths unpredictably.
- **Slow per-frame drain.** `save_preview` does a blocking `render.start{}` +
  `wait_for_render_ready`; an orbit bake is ~2.5 min/frame.
- **Licensing friction.** The project is BSL-1.1 (commercial restrictions until 2030).
- **Single-renderer coupling.** The "Agentic Canvas" (`apps/octanex-canvas`, Swift +
  WKWebView) is a *thin display client* for Octane's PNG — it does not itself render.
  There is currently no second visualization channel.

This report surveys **open-source realtime/interactive visualization options** that could
serve as (a) a second, more robust backend behind the *same* command DSL, (b) a realtime
channel the WKWebView canvas could host directly, or (c) a quality-tier open replacement
for Octane's path tracing. The recommendation is an architectural one: **decouple the
scene-graph DSL from the renderer**, so Octane becomes one of N backends.

---

## 1. Evaluation criteria (derived from the project's actual needs)

| # | Criterion | Why it matters here |
|---|-----------|---------------------|
| C1 | Local-first / privacy | Core project posture; no forced cloud. |
| C2 | Scriptable from Hermes | Must be drivable via MCP/stdio/Python, not just a GUI. |
| C3 | Photoreal quality | Octane's differentiator; a replacement must justify losing it. |
| C4 | Realtime / interactive | The "shared visual communication medium" goal; the canvas should react live. |
| C5 | Shareability | X/social posting, URL-based viewing; WebGL wins here. |
| C6 | License compatibility | BSL core + data CC-BY-NC-SA; avoid viral conflicts where possible. |
| C7 | macOS friendliness | Octane's sandbox/AppleScript pain is the thing to beat. |
| C8 | Grammar coverage | Geometry / Data / Math / Science / Geo / Avatar grammars (`visual-grammar.md`). |
| C9 | Integration effort | Reuse the existing command DSL + queue; prefer additive work. |

---

## 2. Candidate backends

### A. Octane X (status quo) — keep as the photoreal tier
- **What:** Otoy's GPU path tracer, macOS-native, embedded in the current pipeline.
- **Fit:** Unmatched photoreal (glass/metal/atmosphere) for the product-studio, planet,
  and photoreal-recipe grammars.
- **Pros:** Best visual quality; established recipe library; benchmark suite.
- **Cons:** Closed binary, no CLI/plugin, fragile AppleScript/TCC bridge, slow per-frame,
  BSL license, single-machine (ssh to mac-studio is a workaround).
- **Recommendation:** Retain as the **quality tier**, not the only backend.

### B. Blender + Eevee Next (bpy) — strongest open photoreal/near-Octane backend
- **What:** Fully open-source (GPL) 3D suite. `bpy` Python API runs headless
  (`--background`) or live. **Eevee Next** (Blender 4.2 LTS+) is a real-time deferred
  viewport with shadows, GI, volumetrics — close to realtime preview.
- **Fit:** Direct replacement class for Octane: import OBJ/USD/glTF, geometry nodes,
  materials, cameras, render to PNG. `bpy-widget` even embeds a live Eevee Next viewport
  in Jupyter (zero-copy to browser) — proof of realtime-in-browser Blender.
- **MCP maturity:** There is an **official Blender MCP lab** (natural-language interface
  to `bpy`) *and* a mature community `BlenderMCP` server exposing the full `bpy` API
  (modeling, materials, animation, rendering) over MCP. The integration pattern is
  already solved by the ecosystem.
- **Pros:** Open source; no AppleScript/TCC hack (Blender is a normal scriptable app);
  headless + live; geometry nodes for parametric grammars; USD/glTF pipelines.
- **Cons:** **GPL** — a viral license that conflicts with octanex's BSL/Apache-2030
  trajectory; heavier runtime than a browser canvas; Eevee is not path-traced
  (Cycles is the quality fallback but is slow like Octane).
- **Integration sketch:** New `BlenderBackend` that translates the existing command DSL
  into `bpy` calls (or reuses `BlenderMCP`'s tools); renders PNG into the same
  `renders/` workspace; Hermes vision review unchanged.

### C. WebGL / three.js (browser) — the realtime + shareable channel
- **What:** `three.js` (WebGL2) and `WebGPURenderer` (WebGPU) run in any browser.
  `react-three-fiber` (R3F) + `drei` are the declarative React bindings; `TSL` is the
  shader-graph layer. Server-side screenshots use headless Chrome (`Playwright`/
  `Puppeteer`) capturing a WebGL context to PNG.
- **Fit:** This is the natural evolution of the **existing** `apps/octanex-canvas`
  WKWebView shell. Today it only *displays* Octane's PNG; it could instead **host live
  three.js scenes** generated from the same command DSL — true realtime, interactive
  (rotate/zoom/pan), and URL-shareable.
- **Pros:** Realtime + interactive (C4 maxed); trivially shareable (C5 maxed); no
  native-app/sandbox issues (C7); MIT-licensed (C6 clean); huge ecosystem
  (R3F, drei, three-mesh-bvh, postprocessing); great for Data/Math grammars and as a
  fast preview tier in front of Octane.
- **Cons:** Not photoreal like Octane (PBR but no path-traced GI/CAUSTICS); headless
  PNG capture needs a browser + GPU (Swift's `WKWebView` can snapshot directly on-device,
  which sidesteps the headless-Chrome problem for local use).
- **Integration sketch:** Add a `WebGLBackend` that emits a self-contained HTML/JS bundle
  (or a scene JSON the canvas hydrates) from the DSL; the WKWebView canvas renders it
  live and can snapshot to PNG for Hermes review. This turns the canvas from a PNG viewer
  into a *live renderer*.

### D. Godot 4 (Vulkan) — open interactive-scene engine
- **What:** MIT-licensed open game engine with a real-time Vulkan renderer, GDScript,
  and a scene/node graph. Multiple **Godot MCP servers** exist (GDScript- or
  WebSocket/JSON-RPC-based) that let an agent create scenes, write scripts, inspect a
  running game, and build 3D environments from an editor or headless instance.
- **Fit:** Best for **concept-as-interactive-scene** and animated/staged grammars
  (architecture flow, agent loop, physics orbits).
- **Pros:** MIT (C6 clean); realtime; built-in physics/animation; headless render to
  image; strong MCP ecosystem already.
- **Cons:** Less suited to photoreal product/planet stills than Octane/Blender;
  GDScript/editor model is a different paradigm from the OBJ+command-DSL approach;
  more engine to learn for the agent.
- **Integration sketch:** `GodotBackend` mapping DSL nodes → Godot scenes; or use an
  existing Godot MCP server as the transport.

### E. Scientific Python viz (Open3D, PyVista/VTK, VisPy, trimesh) — headless analysis+render
- **What:** `Open3D` (point clouds, meshes, RGB-D), `PyVista` (VTK wrapper, meshes +
  offscreen render), `VisPy` (OpenGL, large data), `trimesh` (already an octanex
  optional dep for mesh grouping). All render to PNG headlessly and are Python-native.
- **Fit:** The **Science/geometry-generation** backend. Excellent for point clouds,
  meshes from NumPy/SciPy/PyVista, N-body snapshots, and as the *geometry source* feeding
  other backends (already in `canvas-roadmap.md` deps: `trimesh`, `shapely`, `geopandas`).
- **Pros:** No GUI/sandbox issues; first-class Python (C2); best-in-class for scientific
  data; complementary, not competing.
- **Cons:** Not realtime-interactive (offline render); not photoreal; visualization
  aesthetics are plainer than Octane/three.js.
- **Integration sketch:** Not a "replacement" — fold these into the **generator layer**
  so any backend (Octane/Blender/WebGL) can consume their meshes.

### F. Geospatial web (CesiumJS, deck.gl, KeplerGL, MapLibre) — purpose-built Geo grammar
- **What:** `CesiumJS` (3D globes, terrain, time-dynamic), `deck.gl` (GPU-accelerated
  layers over maps), `KeplerGL` (exploration), `MapLibre GL` (vector maps). All
  open-source, WebGL/WebGPU.
- **Fit:** The Geo grammar (`geospatial-terrain` recipe, GeoJSON/KML pipelines) is
  currently *hacked* by extruding GeoJSON into OBJ for Octane. These engines do geo
  natively and far better (real globes, fly-to, layers, time sliders).
- **Pros:** Purpose-built for geo; realtime; browser-shareable; integrate naturally into
  the WebGL canvas (C above).
- **Cons:** Domain-specific (not a general viz backend); requires geo data plumbing.
- **Integration sketch:** A `GeoBackend` that targets CesiumJS/deck.gl inside the WebGL
  canvas, fed by the existing `shapely`/`geopandas`/`pyproj` generators.

### G. Open path tracers (Mitsuba 3, OSPRay / Intel OIDN) — quality-tier Octane replacement
- **What:** `Mitsuba 3` (Python-driven, differentiable, spectral/path tracing),
  `OSPRay` (Intel, large-scene scientific ray tracing), `Intel OIDN` (denoiser).
- **Fit:** If the goal is Octane-quality GI *without* the Otoy binary or BSL license.
  Mitsuba 3 is scriptable end-to-end from Python — ideal for research-grade,
  reproducible renders.
- **Pros:** Open source; reproducible/parameterized; differentiable (research edge);
  no macOS-sandbox bridge needed.
- **Cons:** Not realtime (offline quality tier, like Octane's `final`); more setup;
  smaller agent/MCP ecosystem than Blender.
- **Integration sketch:** `QualityBackend` alongside Octane; useful where Octane is
  unavailable or licensing is a blocker.

### H. WebGPU engines (Babylon.js, PlayCanvas, wgpu/Bevy) — modern realtime
- **What:** `Babylon.js` (mature, TypeScript, data-viz-friendly, open), `PlayCanvas`
  (open WebGL/WebGPU engine), `wgpu`/`Bevy` (Rust native realtime).
- **Fit:** C is the pragmatic pick for the canvas; Babylon.js is the more
  "engine-grade" WebGPU alternative (scenes, physics,-post FX) if three.js proves
  limiting. `wgpu`/`Bevy` are relevant only if a native Rust renderer is ever wanted
  (out of scope for now).
- **Pros:** WebGPU compute, modern, open (Babylon/PlayCanvas MIT).
- **Cons:** More effort than three.js for the same canvas win; smaller immediate payoff.
- **Integration sketch:** Drop-in alternative renderer behind the WebGLBackend if needed.

---

## 3. Comparison matrix

Legend: ● strong · ◐ partial · ○ weak. Criteria C1–C9 per §1.

| Backend | C1 local | C2 script | C3 photoreal | C4 realtime | C5 share | C6 license | C7 macOS | C8 grammar | C9 effort |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **A. Octane X** (now) | ● | ○ (AppleScript) | ● | ○ | ○ | BSL | ○ (sandbox) | broad | n/a |
| **B. Blender+Eevee** | ● | ● (bpy/MCP) | ◐ (Eevee/Cycles) | ◐ | ○ | GPL | ● | broad | med |
| **C. WebGL/three.js** | ● | ● (JS/Py) | ○ | ● | ● | MIT | ● | data/math/geo | low |
| **D. Godot 4** | ● | ● (MCP) | ○ | ● | ○ | MIT | ● | concept/scene | med |
| **E. Open3D/PyVista** | ● | ● (Py) | ○ | ○ | ○ | BSD/MIT | ● | science/gen | low (gen) |
| **F. Cesium/deck.gl** | ● | ● (JS) | ○ | ● | ● | BSD/MIT | ● | geo | low (geo) |
| **G. Mitsuba/OSPRay** | ● | ● (Py) | ● | ○ | ○ | BSD | ● | quality | med |
| **H. Babylon/PlayCanvas** | ● | ● (JS) | ◐ | ● | ● | MIT | ● | data/scene | med |

---

## 4. Recommended architecture: renderer abstraction

Do **not** rewrite octanex-mcp. Add a **backend interface** behind the *existing* command
DSL and queue, so Octane becomes one of N backends:

```
Hermes / generator -> scene-graph DSL (already exists)
        |
        v
   octanex-mcp server  -- dispatches to a Backend adapter -->
        |                                   |
        |-- OctaneBackend  (status quo)      |
        |-- BlenderBackend (bpy / BlenderMCP)|
        |-- WebGLBackend  (three.js in canvas)   -> live + PNG
        |-- GeoBackend    (Cesium/deck.gl)        -> live + PNG
        |-- QualityBackend(Mitsuba/OSPRay)        -> offline PNG
        |
        v
   shared renders/ workspace + Hermes vision review (unchanged)
```

- The generators (OBJ, NumPy, shapely, trimesh) become **backend-agnostic geometry
  sources** (they already are, mostly).
- Each backend implements: `build(scene)`, `render(preview)`, `save_png()`, returning the
  same artifacts the Octane path does, so `octane_review_preview` / vision review stay put.
- The WKWebView canvas upgrades from "PNG viewer" to "live WebGL host" — the highest-leverage
  single change for the *shared visual communication medium* goal.

---

## 5. Phased proposal for further development

**Phase 0 — Backend interface (foundation).** Extract the current Octane command handling
into a `Backend` protocol; `OctaneBackend` is the first impl. No behavior change.

**Phase 1 — WebGL/three.js channel (highest leverage, lowest effort).**
Upgrade `apps/octanex-canvas` to render live three.js scenes from the DSL; snapshot to PNG
for Hermes review. Gives realtime + shareable *now*, with zero AppleScript dependency.
Covers Data/Math grammars immediately.

**Phase 2 — GeoBackend (CesiumJS/deck.gl).** Move the Geo grammar off "extrude GeoJSON to
OBJ" onto a real globe/map, inside the same canvas.

**Phase 3 — BlenderBackend (optional quality/photoreal open tier).** Add `bpy`/BlenderMCP
as an open photoreal alternative to Octane; resolves the BSL + AppleScript fragility for
users who don't have/want Octane. (License note: keep Blender integration in a clearly
separated module to avoid GPL contamination of the core BSL package.)

**Phase 4 — QualityBackend (Mitsuba/OSPRay).** For research-grade reproducible renders
where Octane is undesirable.

**Defer:** Godot (D) and WebGPU-native (H) unless a specific interactive-scene or
engine-grade need emerges.

---

## 6. Risks & open questions

- **License:** Blender is GPL — isolate it behind a process boundary (subprocess/MCP),
  never import `bpy` into the BSL core package. Mitsuba/OSPRay/three.js/Babylon are
  BSD/MIT and safe to depend on directly.
- **WebGL headless PNG on macOS:** `WKWebView` can snapshot on-device (no headless Chrome
  needed) — verify this works for the canvas before assuming a browser-server path.
- **DSL expressiveness:** current DSL is Octane-shaped (materials/pins). A `WebGLBackend`
  needs a flattened subset (meshes + transforms + basic PBR + camera); map the DSL down,
  don't expand it yet.
- **Verification discipline:** keep the pixel/structure-before-vision rule from
  `AGENTS.md` for *every* backend, not just Octane.
- **Scope creep:** the canvas roadmap already has 4 phases; the WebGL channel is the one
  addition that pays back across grammars — do it before adding more backends.

---

## 7. References & evidence notes

- Searches (2026-07-13) confirmed: **official Blender MCP lab** + community **BlenderMCP**
  server; **bpy-widget** (live Eevee Next in Jupyter); **react-three-fiber** / three.js
  serverless WebGL rendering patterns; multiple **Godot MCP** servers (Coding-Solo,
  FunplayAI, others); **WebGPU/Bevy** and **three.js WebGPURenderer** migration material;
  **CesiumJS/deck.gl/KeplerGL/MapLibre** as the geospatial web stack; **Mitsuba 3 /
  OSPRay** as open path tracers.
- **Evidence caveat:** `web_extract` (Firecrawl) was unavailable this session, so
  version-specific claims (e.g. exact Blender MCP tool counts, Eevee Next feature set) were
  drawn from search summaries + project knowledge, not page-level verification. Re-verify
  specific API details before Phase 3 implementation.
- Project-internal context: `docs/canvas-roadmap.md` (grammars), `docs/visual-grammar.md`,
  `apps/octanex-canvas/README.md` (thin-client design), `README.md` (current pipeline),
  and the `octanex-mcp-project` skill (TCC/AppleScript fragility, per-frame drain cost).
</content>
</invoke>
