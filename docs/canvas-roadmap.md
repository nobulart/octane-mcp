# Octane Canvas Roadmap

Goal: make Octane X a shared visual canvas for Hermes and Craig — a place to render geometry, data, math, physical systems, maps, concepts, and Hermes' own visual presence.

## Current verified loop

```text
Hermes/Python generator -> OBJ asset -> MCP queue -> Octane Lua bridge -> render target -> PNG preview -> Hermes vision review
```

Verified capabilities:

- geometry import through `NT_GEO_MESH`;
- render target mesh connection via `P_MESH`;
- camera/environment setup;
- renderer start/run request;
- PNG preview saving and file verification;
- Hermes-side visual review of the saved render.

## Visual grammars to build

### 1. Geometry grammar

- Points, vectors, rays, planes, basis frames, transforms.
- Curves/tubes, arrows/cones, surfaces, volumes.
- Bounding boxes and auto-camera framing.

### 2. Data grammar

- Bar charts, scatter plots, heatmaps, network graphs, timelines.
- Semantic colors and legends.
- Streaming/update protocol: stable node names plus replaceable asset files.

### 3. Math grammar

- z=f(x,y) surfaces, implicit surfaces, vector fields, phase portraits.
- Optimization landscapes with trajectory overlays.
- Linear algebra scenes: eigenspaces, matrix transforms, manifolds.

### 4. Scientific/physics grammar

- Particle systems, fields, trajectories, N-body snapshots.
- Meshes from NumPy/SciPy/PyVista/Open3D/trimesh.
- Geospatial meshes from GeoJSON/KML via shapely/geopandas/pyproj.

### 5. Hermes avatar grammar

- A geometric non-human face/guide that can appear in scenes.
- Emotion states: curious, warning, explaining, done.
- Pointers: gaze, thought blocks, arrows toward the object under discussion.

## Near-term implementation priorities

1. Multi-material pin assignment by material group name, with no noisy fallback warnings.
2. Auto-framing from generated asset bounds.
3. Add cylinder/cone/tube primitives for arrows and graph edges.
4. Add `octane_show_avatar` and use avatar as scene guide.
5. Add NumPy-backed mesh generators while keeping dependencies optional.
6. Add preview-review loop: render, inspect, automatically adjust camera/materials.

## Dependency policy

Keep the core MCP server light. Add optional extras later:

```toml
[project.optional-dependencies]
science = ["numpy", "scipy", "networkx", "trimesh"]
geo = ["shapely", "pyproj", "geopandas"]
physics = ["numpy", "scipy"]
```

Core generators should degrade gracefully when optional packages are absent.
