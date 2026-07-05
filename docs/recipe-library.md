# Example Recipe Library

This library gives agents copyable scenes, preview renders, and operational recipes for exploring OctaneX MCP applications. Each recipe includes:

- `scene.obj` reusable geometry;
- `scene.mtl` material hints for OBJ import;
- `scene.json` MCP command/camera metadata;
- `preview.png` or `photoreal-preview.png` generated preview/target render for quick review;
- `README.md` with prompts, steps, variations, and quality checklist.

The previews are intentionally small, deterministic repo-generated renders so they can be reviewed on GitHub and reused without launching Octane. For final quality, run the listed command sequence through the Octane Lua bridge and save an Octane preview next to the sample.

Photoreal target examples may include an external target/reference image. These are visual quality bars, not claims of native Octane success until an `octane-preview.png` is saved and inspected.

Animated products are also possible by generating frame-by-frame scene states. See [`examples/animations/orbit-reveal/`](../examples/animations/orbit-reveal/README.md) for a checked-in GIF/MP4 example with PNG frames and OBJ frame states.

| Recipe | Application area | Slug | Why it matters |
| --- | --- | --- | --- |
| [3D KPI Bar Chart](../examples/recipes/data-bars/README.md) | Data visualization | `data-bars` | Compare a short numeric sequence as spatial bars with a clear baseline and highlight bars above threshold. |
| [Radial Math Surface](../examples/recipes/math-surface/README.md) | Mathematics | `math-surface` | Render a height field for z = sin(r*2.2)/max(r, 0.45) to explain radial damping and singularity protection. |
| [Rotating Vector Field](../examples/recipes/vector-field/README.md) | Math/physics | `vector-field` | Show a 2D rotational vector field lifted into 3D with arrow tips to explain flow direction. |
| [Knowledge Graph Topology](../examples/recipes/network-graph/README.md) | Graphs/knowledge | `network-graph` | Render nodes and links as spatial graph geometry to discuss hubs, bridges, and communities. |
| [Terrain and Site Markers](../examples/recipes/geospatial-terrain/README.md) | Geospatial/science | `geospatial-terrain` | Represent a small terrain tile with highlighted points of interest, suitable for GIS-to-Octane experiments. |
| [Orbital Trajectories](../examples/recipes/physics-orbits/README.md) | Physics/simulation | `physics-orbits` | Show several trajectories around a central body to explain orbital state, phase, or simulation snapshots. |
| [MCP Architecture Flow](../examples/recipes/architecture-flow/README.md) | Architecture/explanation | `architecture-flow` | Turn an architecture diagram into geometry: user, agent, queue, and Octane as spatial blocks connected by flow lines. |
| [Hermes Avatar Guide](../examples/recipes/avatar-guide/README.md) | Agent communication | `avatar-guide` | Place a geometric Hermes guide in a scene with a pointer so agents can direct attention visually. |
| [Wave Interference Field](../examples/recipes/wave-interference-field/README.md) | Math/physics | `wave-interference-field` | Show constructive and destructive interference from two point sources as a height field with source markers. |
| [Render/Vision Feedback Loop](../examples/recipes/vision-feedback-loop/README.md) | Agent workflow | `vision-feedback-loop` | Represent the closed loop where an agent queues geometry, Octane saves a PNG, local vision reviews it, and the next scene patch is chosen. |
| [Photoreal Product Studio](../examples/recipes/photoreal-product-studio/README.md) | Photoreal/PBR rendering | `photoreal-product-studio` | Set a quality target for glass, metal, softbox lighting, camera, and native-render validation. |

## Recommended agent loop

1. Read the recipe README and inspect `preview.png` or the recipe-specific target preview.
2. Reuse or modify `scene.obj` / the generator pattern.
3. Queue import/camera/render commands through MCP.
4. Drain the queue with `octane_lua/hermes_bridge_oneshot_v2.lua`.
5. Save an Octane preview.
6. If the result teaches anything reusable, call `octane_record_recipe(...)` or edit `docs/recipe-book.md`.

## Coverage map

- **Data:** KPI bars.
- **Math:** radial surface and vector field.
- **Graphs:** knowledge/dependency graph.
- **Geospatial:** terrain tile and site markers.
- **Physics:** orbital trajectories.
- **Systems:** MCP architecture flow.
- **Agent communication:** Hermes avatar guide.
- **Feedback loops:** render/vision review loop and corrective camera/material iteration.
- **Photoreal:** product-studio scene with PBR material intent and target render.

## Animation pattern

Current reliable animation flow:

```text
Python generator -> obj_frames/scene_000.obj ... -> frame PNGs -> animation.gif / animation.mp4
```

Native Octane timeline controls are not yet exposed by the MCP. For now, generate one OBJ scene state per frame, render or preview each frame, then encode with `ffmpeg`. This is enough for data stories, trajectory reveals, system-flow explainers, and parameter sweeps.
