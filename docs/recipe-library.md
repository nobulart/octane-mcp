# Example Recipe Library

This library gives agents copyable scenes, preview renders, and operational recipes for exploring OctaneX MCP applications. Each recipe includes:

- `scene.obj` reusable geometry;
- `scene.json` MCP command/camera metadata;
- `preview.png` lightweight generated render for quick review;
- `README.md` with prompts, steps, and variations.

The previews are intentionally small, deterministic repo-generated renders so they can be reviewed on GitHub and reused without launching Octane. For final quality, run the listed command sequence through the Octane Lua bridge and save an Octane preview next to the sample.

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

## Recommended agent loop

1. Read the recipe README and inspect `preview.png`.
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
