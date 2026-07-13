# Point-cloud and particle-field visualisation

## Objective

Make scientific point fields, gridded scalar fields, and simulation output
renderable in OctaneX without pretending that a bounded proxy cloud is a native
participating medium. The first tool is deliberately small and inspectable;
large-cloud storage, animation, and VDB conversion are separate stages.

## Current implemented slice

`octane_visualize_point_cloud` loads a source, normalizes it to a bounded scene,
and queues a one-mesh particle-cloud render. It supports:

| Source | Status | Notes |
|---|---|---|
| CSV / TSV | core | Header columns default to `x`, `y`, `z`; configurable at the MCP boundary. |
| XYZ / PTS / whitespace text | core | First three values per non-comment line. |
| ASCII PLY | core | Vertex `x`, `y`, `z`; binary PLY intentionally rejected. |
| JSON / GeoJSON Points | core | GeoJSON 2D points receive `z=0`. |
| NetCDF (`.nc`, `.nc4`, `.cdf`) | optional `pointcloud` extra | A 3D scalar field, after an optional `time` slice; highest-magnitude finite values become the bounded proxy cloud. |

Install optional NetCDF support with:

```bash
uv sync --extra pointcloud
```

The current proxy has a hard `max_points <= 4096` cap. It is a safety boundary
for OBJ size and render time, **not** a claim that the original dataset is small.
Each generated asset records its source bounds, selected variable/time, source
shape, normalization scale, and selected point count.

### Implemented instancing primitives

- `sphere` — default low-poly sphere; a soft, volumetric reading.
- `cube` — voxel-field diagnostic; far lighter than sphere geometry and useful
  for broad structural checks.

Both preserve coordinate selection and camera framing. The current bridge has
one imported mesh connected to the render target, so this is one combined OBJ
rather than native renderer instancing. It is suitable for hundreds to a few
thousand review particles, not a final billion-particle renderer.

## Demonstrated source

A real trial loaded `/Users/craig/ECDO/plume/data/plume_unforced.nc`, variable
`b` (buoyancy), `time_index=20`, and selected 320 strongest-magnitude finite
voxels from its `32 × 32 × 32` scalar field. The native Octane viewport
converged at 5000 spp and showed a fully framed particle structure. The bridge
saved no PNG because this Octane build's `saveImage` returned false after the
completed viewport render; the review preview was therefore captured from the
live viewport and kept separate from a bridge-saved render artifact.

## Standard visual feature matrix

These should be modelled as independent **data channels**, **selection rules**,
and **visual encodings**. Do not overload one scalar or material field to mean
several things at once.

| Feature | Data needed | Useful mappings | Initial status |
|---|---|---|---|
| Scalar value | `value` per point/voxel | threshold, opacity, radius, hue/colour band | selection is implemented; renderer-side per-point style is pending |
| Velocity | `u,v,w` vector or `speed` | particle trails, anisotropic ellipsoids, arrow glyphs, speed threshold | ingest/schema next |
| Acceleration | temporal velocity derivatives | radius, emissive intensity, event highlighting | derived-channel next |
| Density / concentration | scalar field | particle count, radius, opacity, VDB density | top-magnitude proxy works; true density medium pending |
| Proximity | distance to surface, seed, or other particles | colour bands, collision highlights, culling | derived-channel next |
| Vorticity / divergence / strain | vector-field derivatives | curls, glyph orientation, thresholded event clouds | derived-channel next |
| Temperature / pressure / salinity / composition | scalar fields | palette bands, threshold surface, emissive hot spots | scalar-selection path is reusable |
| Time / simulation step | frame coordinate | animated sequence, trails, temporal difference | NetCDF time selection is implemented; sequence writer pending |
| IDs / categories | particle attributes | discrete shape/material classes | schema and group generation pending |
| Uncertainty / confidence | sigma, ensemble spread | opacity, size, stipple density | derived-channel next |

### Colour mapping policy

The current Octane build cannot reliably set texture/vertex-colour nodes, so
per-particle continuous colour ramps are not yet honest. Until that capability
exists, use one of these explicit alternatives:

1. **Selection + one solid material** — current reliable path. Render one
   thresholded subset at a time, with an honest legend external to the mesh.
2. **Discrete material bins** — split points into a small number of OBJ material
   groups (for example 5–8 quantiles) and assign solid materials by group. This
   is a near-term bridge-compatible path, but needs a `material_group` asset
   builder and validation of group-index assignments.
3. **Texture/vertex-colour path** — only after a live capability probe proves
   texture node wiring works. Do not promise continuous ramps before then.

## Large-cloud and simulation architecture

For liquids, gases, plasmas, granular matter, CFD, SPH, molecular dynamics, N-body,
weather, seismic wavefields, ocean models, or field simulations, the source data
must remain source-backed. Loading an entire time series into Python or expanding
every point to OBJ geometry is the wrong architecture.

### Proposed layers

1. **Dataset catalog** — durable metadata only: URI/path, format, variable names,
   coordinate axes/units, timestep count, content hash, provenance, and supported
   derived channels. This is the correct form of "memory" for vast datasets.
2. **Frame reader** — lazy, chunk-aware read of one timestep or spatial region.
   Prefer xarray+dask/Zarr for NetCDF/HDF5 collections; never materialize the full
   temporal cube by default.
3. **Selection engine** — deterministic filters and samplers: threshold,
   percentile, stratified spatial sample, top-K magnitude, ROI clip, Poisson-like
   spacing, and seed/trajectory selection. Persist its parameters with each render.
4. **Derived-field engine** — compute speed, acceleration, proximity, gradients,
   vorticity, divergence, density estimates, and uncertainty as named channels.
   Cache chunk outputs keyed by dataset hash + parameters, not in session memory.
5. **Representation adapter** — choose the appropriate visual proxy per budget:
   voxel cubes, spheres, ellipsoids aligned to velocity, streamlines/trails,
   isosurfaces, or native VDB volumes.
6. **Renderer adapter** — use combined OBJ proxy scenes for review; migrate dense
   fields to native instancing or VDB once the bridge exposes those capabilities.
7. **Animation manifest** — references dataset + variable + frame selection +
   mapping recipe. It queues one frame at a time and preserves frame metadata,
   avoiding simultaneous writes to Octane's shared queue.

### Explicit scale tiers

| Tier | Typical size | Representation | Storage and execution rule |
|---|---:|---|---|
| Review | ≤ 4k points | combined OBJ spheres/cubes | current implementation |
| Dense proxy | 4k–250k points | native instancing or batched meshes | build only after live bridge proof |
| Field | 3D/4D scalar grid | VDB / isosurface / sparse proxy | requires `create_medium` + VDB ingest |
| Simulation archive | millions–billions × many frames | source-backed NetCDF/Zarr/Parquet + catalog | lazy chunks; never all in RAM or OBJ |

## Next implementation sequence

1. Add a **dataset catalog** and `octane_inspect_point_cloud` metadata tool; no
   rendering side effect.
2. Add scalar selection modes (`top_abs`, positive/negative thresholds,
   percentiles, stratified sample) and persist their provenance.
3. Add discrete material bins for scalar ranges; validate group assignments and
   produce a legend specification.
4. Add vector channels and primitives: velocity-aligned ellipsoids, arrows,
   streamlines, and temporal trails.
5. Add a sequential NetCDF animation driver which renders one time step at a
   time and checks each captured frame before encoding.
6. Design a `create_medium` + VDB ingest contract for genuine fog/smoke/liquid
   density fields. This is the path for true volumetrics, not a particle proxy.
7. Add source-backed cache/catalog support with Zarr/dask only after a benchmark
   defines memory, IO, and render-budget acceptance criteria.

## Guardrails

- A particle proxy is not a physical volume, and a selected top-K cloud is not
  the full scalar field. State the selection rule in each render.
- Preserve axes, units, timestep, variable name, thresholds, and source path in
  render metadata.
- Do not claim a colour mapping works per point until vertex/texture or discrete
  material bins are actually wired and visually verified.
- Keep Octane work sequential: there is one shared renderer queue.
- Native VDB/media work must use a real bridge operation and a real rendered
  preview; do not substitute synthetic imagery.
