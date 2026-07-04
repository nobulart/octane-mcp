# Local-Model Rich MoA for Visual R&D

## Philosophy

You're on an M3 Ultra Mac Studio with local LLMs. Treat this as your **visual prototyping lab** — build, test, render, iterate quickly with no cloud dependency.

### Core principles

| Principle | Why it matters |
|-----------|----------------|
| **Python-first generation** | Write geometry generators in Python; generate OBJ assets for Octane. No Lua-side heavy math needed. |
| **Render → Preview → Inspect loop** | Render a PNG, save it, inspect it with vision. If not right, fix and retry. |
| **Local LLM orchestration** | Spawn subagents per task — each gets fresh context, runs independently, returns distilled summary. |
| **Progressive complexity** | Start with OBJ primitives → add trimesh → add USD scene graphs as needed. |
| **Cheap experiments** | Anything that takes more than 2 minutes to render or compile is too slow for iteration. |

---

## Visual R&D Workflow

```text
PLAN → PROTOTYPE → QUICK RENDER → INSPECT → ADJUST → FINALIZE
   ↓        ↓           ↓          ↓         ↓         ↓
  doc    Python gen.   <10s PNG   Hermes      OBJ       render
                                   vision     asset     +save
```

### Step 1: Plan (doc)

Write a one-page spec:

- **Goal**: What do we want the user to see/understand?
- **Geometry type**: Points? Curves? Surfaces? Mesh? Graph?
- **Key visual elements**: Colors, materials, labels, focus points.
- **Camera framing**: ISO? Top-down? Close-up? Auto-frame from bounds?

### Step 2: Prototype (Python)

Use existing primitives or write a short generator:

```python
# Example: quick mesh builder for prototype
def my_mesh():
    b = ObjBuilder("my_prototype")
    b.add_box(...)
    b.add_surface(...)
    return workspace.assets_dir / "my_prototype.obj"
```

### Step 3: Quick Render (<10s PNG)

Use the bridge’s existing command queue:

- `import_geometry` → material → `set_camera` (pre-tuned or auto) → `start_render` → `save_preview`
- Total wall time: usually <30 seconds end-to-end.

### Step 4: Inspect (Hermes vision)

- Look at the saved PNG in the context window.
- Identify framing, material, geometry issues.
- Decide next adjustment loop count (1-3 iterations max).

### Step 5: Adjust

Fix the generator and repeat steps 2-4 until satisfied.

### Step 6: Finalize

- Commit generator as reusable module (`visuals.py`, `network_visuals.py`, etc.).
- Export to higher fidelity if needed (PLY/USD/GLB after OBJ verified).

---

## Local LLM Orchestration Strategy

| Task type | Tool | Why |
|-----------|------|-----|
| **Generator prototyping** | Single terminal + visual feedback loop | Fastest for small changes. |
| **Cross-document research** | `subagent-driven-development` skill | Spawns separate agents per source; no context pollution. |
| **Large-world physics simulation preview** | Local Python + numpy/scipy + renders | Keep heavy computation in Python, use Octane for visualization only. |
| **Animation sequence planning** | Manim CE (3B1B style) or procedural mesh morphing | Use specialized tool; convert final frames if needed. |

### Delegation policy

- **One task per subagent** — no nesting.
- **Context limit**: Each subagent runs with <5 minutes, self-contained.
- **Review gates**: Implementer → spec compliance → code quality → integration.

---

## Dependency Stack

| Layer | Packages | When to use |
|-------|----------|-------------|
| **Core** | `mcp>=1.2.0` | Default; only required for MCP server. No geometry math. |
| **MVP science** | `numpy`, `trimesh`, `networkx` | Bar charts, parametric surfaces, graphs. |
| **Fields/physics** | `scipy` | ODE integration, interpolation, scientific fields. |
| **Geospatial** | `shapely`, `geopandas` | GeoJSON/KML → 3D meshes for maps. |
| **Heavy viz** | `pyvista`, `open3d` | VTK/point cloud heavy visualizations; defer until OBJ proven insufficient. |

Install extras on-demand:

```bash
uv add -E science numpy trimesh networkx
uv add -E fields scipy
uv add -E geo shapely geopandas
```

### Lazy loading

Generators should import optional deps only when needed and provide clear fallbacks:

```python
def my_optional_visual():
    try:
        import trimesh
        ...
    except ImportError:
        raise RuntimeError("Install with: uv add -E science numpy trimesh")
```

---

## Octane Bridge Best Practices

| Practice | Why |
|----------|-----|
| **Stable semantic IDs** | Use `Hermes/<layer>/<object_id>` for meshes so Lua can find and replace them. |
| **Auto-frame from bounds** | Compute camera from asset min/max; avoid hand-tuning every time. |
| **Single RT geometry connection** | Only `import_geometry` should touch `P_MESH`; `set_camera` must not reconnect mesh. |
| **Preview-save reliability** | Ensure renderer is running before saving preview; check file exists. |
| **Material by semantic group** | OBJ uses `usemtl`, assign to Octane mesh dynamic pins at runtime or create materials directly in pin owner. |

---

## Avatar/Visual Grammar Design

A Hermes avatar should:

- Be visually distinct from user-generated geometry.
- Support multiple emotional/explanatory states (neutral, explaining, thinking, warning).
- Use semantic colors (cyan=helpful, gold=insight, amber=warning, red=error).
- Have components: face plate, eyes, mouth, halo, pointer, callout panels.

### States

| State | Eyes | Mouth | Halo | Pointer |
|-------|------|-------|--------|---------|
| neutral | horizontal, cyan | flat | steady blue | off |
| explaining | one bright, one normal | open stacked bars | gold | on (toward target) |
| thinking | angled inward/down | small “?” arc | pulsing | off |
| success | wide | upward smile arc | expanded gold | off |
| warning | asymmetric | zigzag, amber | flicker amber | on |
| error | narrowed red | broken segments | cracked red | off |

---

## Iteration Targets

| Phase | Goal | Success criteria |
|-------|------|------------------|
| V1 (now) | Geometry/data grammar |OBJ bar charts, surfaces, graphs render cleanly. |
| V2 | Physics/fields grammar | Vector fields, trajectories render clearly. |
| V3 | Large-world LOD | Chunked OBJs import and frame by camera FOV. |
| V4 | Avatar conductor | Hermes appears next to generated scene elements with pointing/callouts. |

---

## Quick Check for Visual Quality

Before accepting a visual:

- [ ] **Label visible**: Are axes, titles, key points readable?
- [ ] **Framing correct**: Does the camera show the interesting part without clipping?
- [ ] **Material contrast**: Different parts use distinct colors/tints?
- [ ] **Depth cues**: Shadows/ambient occlusion give 3D volume?
- [ ] **No render artifacts**: No black planes, missing faces, obvious normals issues?

---

## Summary: Local Model Richness

You have:

- **Octane X** for near-real-time rendered geometry (GPU-accelerated).
- **Local LLMs** (glm-5.2-mlx-nvfp4, qwen3-coder-next Q8_0) for reasoning, planning, and subagent orchestration.
- **Python/numpy/trimesh** for fast geometry generation with minimal dependencies.
- **Vision inspection** of saved PNG previews for visual verification.

This is a full local visualization studio — no cloud APIs needed. Every loop finishes in seconds, not minutes or hours.

The only limit is your imagination and the speed of Python-to-OBJ-to-Octane pipeline.
