# Knowledge Graph Topology

![Preview render](preview.png)

- **Category:** Graphs/knowledge
- **Purpose:** Render nodes and links as spatial graph geometry to discuss hubs, bridges, and communities.
- **Starter prompt:** Turn a dependency or knowledge graph into a spatial scene with highlighted hubs.

## Files

- `scene.obj` — reusable geometry scene.
- `scene.json` — command sequence and camera metadata for agents.
- `preview.png` — lightweight generated preview for quick review in GitHub/docs.

## MCP tools to use

- `octane_import_geometry`
- `octane_create_material`

## Steps

1. Generate node cubes and edge polylines from graph layout coordinates.
2. Highlight hub/bridge nodes with a separate material.
3. Use camera angle that separates edge crossings.

## Variations to explore

- Add labels as future billboard/text geometry.
- Use animation to show graph traversal or diffusion.

## Re-render in Octane

1. Import `scene.obj` with `octane_import_geometry(path="examples/recipes/network-graph/scene.obj", name="network-graph")`.
2. Apply camera from `scene.json`.
3. Drain the queue with `octane_lua/hermes_bridge_oneshot_v2.lua`.
4. Save an Octane preview and replace/add it alongside `preview.png` if it teaches a useful lesson.
