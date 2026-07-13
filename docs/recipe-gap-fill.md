# Recipe Gap-Fill Targets — Beyond the Minimal-Surface Gallery

**Status:** proposal (not yet implemented). **Date:** 2026-07-13.
**Context:** the 3DXM math-surface gallery (WP9) is 7/37 done; the 20 blocked
+ ~10 unenumerated surfaces need a parametric/Weierstrass mesher (separate
workstream). This doc proposes what to build *instead* / *next* to fill the
visual-grammar gaps OctaneX is meant to cover.

---

## 0. Capability reality check (evidence, 2026-07-13)

**Octane X CAN do (per `docs/OctaneX/` mirror + `docs/reference/material-pins.md`):**
- Hair material + fur (hair strands, scatter on hair vertices)
- Scatter on Surface / Particles / Hair (`ScatteronSurface.md`)
- VDB volumes: Standard Volume medium, smoke/fog (`material-pins.md` L257)
- Media: Absorption / Scattering / RandomWalk / StandardVolume (`material-pins.md` L128,254)
- Texture Displacement (`docs/OctaneX/TextureDisplacement.md`) — heightfield relief
- OSL / gradient / RGB texture nodes (settable); vertex-colour NOT (recipe-book L60)

**What is NOT yet exposed as an MCP tool (tooling gap, confirmed by live
`hermes mcp list-tools octanex` returning no hair/particle/volume/geo matches):**
- No hair/fur scene tool
- No particle-system tool (docs *mention* `octane_visualize_particles`/`octane_visualize_scatter` but they are not confirmed live)
- No VDB/volume ingest tool
- No GeoJSON/KML/GPKG/TIF ingest tool
- No displacement-from-raster tool

**Environment gaps (block real geodata work until installed):**
- `numpy` only. MISSING: `gdal`, `geopandas`, `shapely`, `pyproj`, `rasterio`,
  `netCDF4`, `xarray`, `scipy`, `trimesh`, `pyvista`.
- Per `canvas-roadmap.md` L63-70 these are intended as optional extras
  (`[project.optional-dependencies]` science/geo/physics) — not yet added.

**Conclusion:** the highest-value, lowest-fiction gap-fill is **Earth-data
visualization from real `~/ECDO` files**, but it is gated on (a) installing
geo/science libs and (b) adding 2-3 bridge tools (raster→displacement,
vector→extrude, volume→VDB). Hair/fur/particles/liquids are Octane-native and
need only tool exposure + small Lua/Python glue.

---

## 1. Geo / Earth-data grammar (HIGHEST VALUE — real `~/ECDO` data)

Concrete, existing source files (verified present):

| Target | Source file(s) in `~/ECDO` | Octane mechanism | Lib needed |
|--------|----------------------------|------------------|-----------|
| **Geoid / gravity relief** | `GIS/us_nga_egm2008_1.tif` (real float32 undulation; `EGM2008.tif` is a colour *render*, NOT usable) | TIF→heightfield→Octane mesh | gdal/numpy (DONE, no extra libs) |
| **Crustal structure** | `GIS/CRUST/CRUST1.0-{vp,vs,rho}.r0.1.nc` | VDB volume slice / displacement | netCDF4/xarray |
| **Subduction / GSOCSEQ zones** | `GIS/DATA_GSOCSEQ_MAP_*.tif`, `*.PROB.tif` | probability raster→displaced terrain, heat colour | rasterio |
| **Lithosphere age** | `GIS/AgeOfEarthLithosphere.kmz` | KML→extruded polygons | geopandas/shapely |
| **Antarctic ice/thickness** | `data/BedMachineAntarctica_Simplified.nc` | bed/elevation→displacement mesh | netCDF4 |
| **ECDO site map** | `GIS/ECDO.kmz`, `AncientPorts-Corsica-Sardinia.kml`, `Cradles.kml`, `Coal.kmz`, `Circles.kmz` | KML→3D points/extruded footprints | geopandas |
| **Arizona / regional GIS** | `GIS/Arizona.gpkg`, `Antarctica.qgz` (QGIS projects) | GPKG layers→extrude | geopandas |
| **Climate radiative flux** | `data/CERES_EBAF-TOA_*.nc`, `CERES_SYN1deg*.nc` | lat/lon grid→displaced globe / heatmap sphere | xarray/netCDF4 |
| **Volcano eruptions** | `GIS/E3WebApp_Eruptions1960.csv`, `E3WebApp_HoloceneVolcanoes.csv` | lat/lon→scatter points, time-animated | pandas |
| **Bond events timeline** | `data/2000-2024.csv` (periodic) | timeline/phase portrait | pandas |
| **SWOT altimetry** | `data/D-109532_SWOT_UserHandbook...` + SWOT.nc | river/lake heights→scatter | netCDF4 |
| **Geomagnetic stability** | `ECDO/geomag` (Stone 2026) | ΔV_eff / σ² / H → field/phase viz | numpy (CAREFUL: see §5) |

**Proposed geo recipes (priority order):**
1. `geo-displacement-terrain` — any single-band TIF (EGM2008 / ETOPO1 / GSOCSEQ) → displaced plane, scientific colormap. *Foundation for all geo.*
2. `geo-kml-extrude` — KML/KMZ → extruded footprints + labelled points (ECDO.kmz first).
3. `geo-climate-globe` — CERES NetCDF → displaced sphere (TOA flux heatmap).
4. `geo-volcano-scatter` — eruption CSV → time-animated scatter on a globe.
5. `geo-crust-volume` — CRUST1.0 nc → VDB volume slice (advanced).

---

## 2. Hair / Fur grammar (Octane-native, tooling gap only)

- `material-pins.md` L46: `Hair` material exists. `ScatteronSurface.md`: scatter
  on hair vertices (1 instance/hair vertex).
- **No MCP tool.** Gap-fill = `octane_build_hair(scene, surface, density, length, colour)`
  → generates a hair-strand mesh + HairMaterial, or uses Octane's native hair
  primitive if exposed.
- Proposed recipe: `hair-fur-sample` — a sphere/torus with a fur coat, studio lit.
  Demonstrates the grammar; no external data needed.

## 3. Particle / Instancing grammar

- `octane_visualize_scatter` exists (canvas-roadmap L43, review.md L246).
  `octane_visualize_particles` is *mentioned* (review.md L268) but not confirmed live.
- Proposed recipes:
  - `particles-pointcloud` — large scatter (10k+ pts) from numpy → prove instancing.
  - `particles-trajectory` — N-body / ODE trajectory ribbons (physics grammar).
  - `particles-on-surface` — scatter-on-surface instances (reuses hair/scatter infra).

## 4. Liquids / Volumes / Media grammar

- Media nodes exist (`material-pins.md` L128,254): Absorption, Scattering,
  RandomWalk, StandardVolume. Texture Displacement for fluid surfaces.
- Proposed recipes:
  - `liquid-glass` — specular + RandomWalk medium → refractive glass/water.
  - `volume-smoke` — VDB→Standard Volume medium (needs VDB ingest tool + lib).
  - `volume-cloud` — scattering medium slab.

## 5. Epistemic guardrails (MUST HONOR)

- `ECDO/geomag/AGENTS.md` forbids deterministic forecasts, countdowns,
  "risk scores", or reversal/excursion prediction. Any geomag viz must show
  **probabilistic diagnostics only** (ΔV_eff, σ², H) with the verbatim disclaimer:
  > "All metrics represent probabilistic diagnostics of geomagnetic stability and
  > do not imply deterministic forecasts of excursions or reversals."
- Geo/climate recipes must label axes, units, and sources explicitly
  (provenance per geomag AGENTS.md "traceable to named inputs"). No alarmist
  colour schemes.

## 6. Dependency gates (what to install/build first)

| Gate | Blocks | Action |
|------|--------|--------|
| `rasterio` + `numpy` | all TIF→displacement (§1.1,1.3) | `uv add rasterio` (or pip) |
| `geopandas`/`shapely`/`pyproj` | KML/GPKG extrude (§1.2,1.4,1.8) | `uv add geopandas` |
| `netCDF4`/`xarray` | CRUST/CERES/BedMachine/SWOT (§1.5,1.7,1.9,1.11) | `uv add xarray netcdf4` |
| bridge tool: `octane_raster_displacement` | §1.1-1.3, §4 | new Lua+Python |
| bridge tool: `octane_kml_extrude` | §1.2,1.4,1.8 | new Lua+Python |
| bridge tool: `octane_hair` | §2 | new Lua+Python |
| bridge tool: `octane_volume_vdb` | §1.5, §4 | new Lua+Python + VDB lib |

## 7. Proposed build order (recommended) — PROGRESS

- [x] **1. `geo-displacement-terrain`** from `us_nga_egm2008_1.tif` — DONE (2026-07-13). `scripts/gen_geo_displacement.py` + `scripts/queue_geo_surface.py`, recipe `examples/recipes/egm2008/`. Uses gdal+numpy (already in homebrew python); no new libs needed for TIF-based heightfields.
- [ ] **2. `geo-kml-extrude`** from ECDO.kmz — proves vector path (needs geopandas/shapely).
- [ ] **3. `hair-fur-sample`** — pure Octane-native, no libs, fills §2.
- [ ] **4. `particles-pointcloud`** — proves instancing at scale.
- [ ] **5. `geo-climate-globe`** (CERES) + **`geo-volcano-scatter`** — flagship Earth-data (needs netCDF4/xarray).
- [ ] **6. `liquid-glass` / `volume-smoke`** — media grammar (higher effort, lower urgency).

**Lib status (2026-07-13):** only numpy present. gdal works in homebrew python
(used for the EGM2008 recipe). Still MISSING: geopandas, shapely, netCDF4,
xarray, rasterio, scipy, trimesh, pyvista. These gate steps 2 and 5.
