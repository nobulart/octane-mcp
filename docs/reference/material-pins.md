# Material / Light pin reference (derived from docs/OctaneX/ mirror)

**Purpose.** A structured, bridge-consumable catalog of OctaneRender material and
light *parameters* (input pins), extracted from the local manual mirror in
`docs/OctaneX/`. This is the human-readable **vocabulary** the `octanex-mcp`
material DSL needs. It answers the open question in
`docs/octane-lua-api-bridge-review.md` (Phase 4 — material/light compatibility
registry) and closes the `docs/visual-iteration-protocol.md` gap ("the bridge
does not yet expose rich native material controls for transmission, IOR,
clearcoat, anisotropy, texture maps, or procedural glazes").

**Critical caveat — names, not codes.** The manual gives **pin display names**
only. The Lua bridge needs the exact `A_*` attribute constants (e.g.
`A_TRANSMISSION`, `A_INDEX_OF_REFRACTION`) and node-type constants (`NT_*`).
Those are **not** in the manual — they come from the live API corpus
(`octane_lua/export_api_docs_v2.lua` → `octane.help.constants`).

> Division of labor: **this file = pin vocabulary/structure**; the live corpus =
> `A_*`/`NT_*` codes. The bridge's `materials.py` should map manual pin names →
> corpus constants at runtime, not hardcode strings guessed from the manual.

**Source.** All entries cite the `docs/OctaneX/<Page>.md` file they were taken
from. Each page is a clean export of the OT oy Standalone Edition manual
(lastmod 2025-06-02). Note: this is the **Standalone** manual, not Octane
X–specific; the shared engine is the same, but on macOS the GUI app is Octane X
(see `docs/octane-x-no-cli.md`).

---

## 1. Material family index

From `Materials.md` (the canonical family list). Right-click Nodegraph →
Materials category to add.

| Family | Manual page | Typical use |
|---|---|---|
| Diffuse | `DiffuseMaterial.md` | dull/non-reflective; also light-emitting meshes |
| Glossy | `GlossyMaterial.md` | plastics, metals (default clear-coat-ish) |
| Metallic | `MetallicMaterial.md` | colored (full-spectrum) reflections |
| Specular | `SpecularMaterial.md` | glass, water, transparent |
| Universal | `UniversalMaterial.md` | PBR/Substance maps; uber-material |
| Toon | `ToonMaterial.md` | cartoon/flat shaded (needs Toon light) |
| Layered | `LayeredMaterial.md` | base + up to 8 material layers |
| Mix | `MixMaterial.md` | blend any two materials |
| Composite | `CompositeMaterial.md` | mask-blend several materials |
| Hair | `HairMaterial.md` | hair/fur |
| Null | `NullMaterial.md` | invisible surface carrying a medium |
| Portal | `PortalMaterial.md` | opening to aid light sampling |
| Shadow Catcher | `ShadowCatcherMaterial.md` | captures shadows only |
| Clipping | `ClippingMaterial.md` | clipping volume for other objects |
| Standard Surface | (Autodesk Standard Surface spec) | USD/MaterialX-aligned |
| Material X | `MaterialX.md` | MaterialX graphs |
| Toon Ramp | `ToonRamp.md` | drives Toon diffuse/specular ramp |

---

## 2. Universal material — the recommended default PBR target

From `UniversalMaterial.md`. Most complete pin set; Glossy (Metallic=0) and
Metallic (Metallic=1) are specializations of it.

### Transmission Layer
| Pin | Accept | Notes |
|---|---|---|
| Transmission | color/texture | light passing through via refraction |
| Transmission Type | enum | Specular / Diffuse / Thin Wall / Thin Wall (Diffuse) |

### Base Layer
| Pin | Accept | Notes |
|---|---|---|
| Albedo | value/texture | base color |
| Diffuse BRDF Model | enum | Lambertian / Octane / Oren-Nayar |
| Metallic | float 0–1 | blends dielectric↔metallic |
| Metallic Edge Tint | color | Artistic & IOR+Color modes only |

### Specular Layer
| Pin | Accept | Notes |
|---|---|---|
| Specular | color | glossy reflection color |
| BSDF Model | enum | 5 models (Glossy/Specular) |

### Roughness / Anisotropy
| Pin | Accept | Notes |
|---|---|---|
| Roughness | value/texture | specular + transmission roughness |
| Anisotropy | float −1..1 | 0 = isotropic |
| Rotation | float | anisotropic rotation |
| Spread | float | specular BSDF tail |

### IOR
| Pin | Accept | Notes |
|---|---|---|
| Dielectric IOR | float | Fresnel for specular/transmission |
| Dielectric 1/IOR Map | texture | per-texel 1/IOR override |
| Metallic Reflection Mode | enum | Artistic / IOR+Color / RGB IOR |
| Metallic IOR (R) | complex | red 650 nm |
| Metallic IOR (G) | complex | green 550 nm |
| Metallic IOR (B) | complex | blue 450 nm |
| Allow Caustics | bool | photon-tracing kernel |

### Coating Layer
| Pin | Accept | Notes |
|---|---|---|
| Coating | color | coating color |
| Coating Roughness | float | |
| Coating IOR | float | |
| Coating Bump | grayscale tex | |
| Coating Normal | RGB tex | |

### Thin Film Layer
| Pin | Accept | Notes |
|---|---|---|
| Film Width | float | thickness |
| Film IOR | float | |

### Sheen Layer
| Pin | Accept | Notes |
|---|---|---|
| Sheen | color | |
| Sheen Roughness | float | |
| Sheen Bump | grayscale tex | |
| Sheen Normal | RGB tex | |

### Transmission Properties
| Pin | Accept | Notes |
|---|---|---|
| Dispersion Coefficient | float | Cauchy B |
| Medium | medium node | Absorption/Scattering/RandomWalk/StandardVolume/Volume |
| Opacity | grayscale tex | |
| Fake Shadows | bool | architectural glass |
| Affect Alpha | bool | refraction → alpha |
| Emission | emission node | Mesh emitter |
| Shadow Catcher | bool | |
| Custom AOV / Channel | | R/G/B/all |

### Geometric Properties (shared across families)
| Pin | Accept | Notes |
|---|---|---|
| Bump | grayscale tex | height map |
| Bump Height | float | 0 disables; negative inverts |
| Normal | RGB tex | precedence over Bump |
| Displacement | tex | needs UVs; works with Texture Image node only |
| Smooth | bool | normal interpolation |
| Smooth Shadow Terminator | bool | |
| Round Edges | bool | shading effect |
| Priority | int | overlap resolution |
| Material Layer | layer node | add layer above base |

---

## 3. Glossy material (`GlossyMaterial.md`)

Diffuse-based shiny. `MetallicMaterial.md` is a close sibling (full-color
specular). Both share: Diffuse, Specular, Diffuse BRDF Model (3), BRDF Model
(6 for Glossy), Roughness, Anisotropy, Rotation, Spread, Film Width, Film IOR,
Sheen, Sheen Roughness, Index Of Refraction, Allow Caustics, Opacity, Bump,
Bump Height, Normal, Displacement, Smooth, Smooth Shadow Terminator, Round
Edges, Priority, Custom AOV(+Channel), Material Layer.

Glossy-specific notes:
- Diffuse BRDF Model: Lambertian / Octane (velvet sheen) / Oren-Nayar.
- 6 BRDF models for Glossy (see `BRDFModels.md` for microfacet: GGX longer tail).
- Index Of Refraction drives Fresnel; <1 disables Fresnel.
- A black Diffuse + Roughness 0 + Index 0 ⇒ perfect mirror.

---

## 4. Specular material (`SpecularMaterial.md`)

Glass/water. Distinct pins:
| Pin | Notes |
|---|---|
| Reflection | with IOR tunes reflectivity |
| Transmission | color/tex; 1 = transparent; ≠ Opacity |
| BRDF Model | 5 models |
| Roughness | blurs reflection + transparency |
| Index Of Refraction | vacuum 1.0, water 1.33 |
| Dispersion Coefficient | coloration in transmission/caustics |
| Dispersion Mode | how IOR/dispersion interpreted |
| Thin wall | ray exits immediately (no medium) |
| Fake Shadows | architectural glass |
| Affect Alpha | refraction → alpha |
| Medium | Absorption/RandomWalk/Scattering/StandardVolume/Volume |

---

## 5. Metallic material (`MetallicMaterial.md`)

| Pin | Notes |
|---|---|
| Diffuse Color | reflection channel base |
| Specular Color | metallic color; <0 IOR ⇒ Fresnel |
| Edge Tint | Artistic / IOR+Color modes |
| Specular Map | blend diffuse↔specular |
| BRDF Model | 4 models |
| Roughness / Anisotropy / Rotation / Spread | as Glossy |
| Metallic Reflection Mode | Artistic / IOR+Color / RGB IOR |
| Index Of Refraction (R/G/B) | complex n−k·i; RGB mode |
| Sheen / Sheen Roughness / Film Width / Film IOR | |

---

## 6. Diffuse material (`DiffuseMaterial.md`)

| Pin | Notes |
|---|---|
| Diffuse | albedo |
| Transmission | mixed with diffuse, indirect light |
| BRDF Model | 3 (Lambertian/Octane/Oren-Nayar) |
| Roughness | velvet sheen at 1 |
| Medium | Absorption/RandomWalk/Scattering/StandardVolume/Volume |
| Emission | Blackbody or Texture emission (Mesh emitter) |
| Shadow Catcher | |

---

## 7. Toon material (`ToonMaterial.md`)

Requires a Toon light (`ToonLighting.md`); Toon Ramp drives diffuse/specular.
| Pin | Notes |
|---|---|
| Diffuse | albedo |
| Specular | coating-like highlight; 0 = none |
| Roughness | |
| Toon Lighting Mode | Camera direction / Octane Toon Lights |
| Toon Diffuse Ramp | albedo color/float range |
| Toon Specular Ramp | specular range |
| Outline Color | contour edges |
| Outline Thickness | 0 = no outline |

---

## 8. Layered / Mix / Composite

- `LayeredMaterial.md`: Base Material + Layer 1–8 (up to 8). Recreates Glossy
  (Diffuse+Specular layer), Metallic (Diffuse+Metallic layer), PBR metal/rough.
- `MixMaterial.md`: Material A + Material B + Amount (value/color/tex).
- `CompositeMaterial.md`: Add Input (several materials) + Material Mask per
  input; first pin = base; mask fallback = material Opacity.
- `DiffuseLayer.md`: Enabled, Diffuse, Transmission, BRDF Model, Roughness,
  Bump, Bump Height, Normal, Layer Opacity — a single layer unit for Layered.
- `SpecularLayer.md`: specular-layer unit (see page).
- `MaterialLayers.md` / `MaterialLayerGroup.md`: layer system details.

---

## 9. Medium sub-nodes (`Mediums.md`)

Attach to Medium pin of Diffuse / Specular / Null / Universal. Best with Path
Tracing or PMC kernel.
| Medium node | Notes |
|---|---|
| Absorption | absorption only |
| Scattering | absorption + scattering + emission |
| Random Walk | realistic SSS |
| Schlick Phase Function | controls scatter direction |
| Standard Volume | VDB grid channels |
| Volume Medium / Gradient | VDB smoke/fog; Gradient variant |

Note: Specular+medium — set Reflection low (0.1–0.2). Null material = invisible
surface carrying a medium (replaces IOR=1/refl=0/trans=1 specular hack).

---

## 10. Light families (`LightTypes.md`, `Lighting.md`)

Seven physical light types in the Lights category. (Toon Directional/Point
covered under `ToonShading.md`.)
| Light | Page | Notes |
|---|---|---|
| Area | `QuadLight.md` | Quad area light; works with Spotlight Distribution |
| Spot | `SpotlightDistribution.md` | cone via Orientation/Direction/Target, Cone Angle, Hardness, Normalize Power |
| Daylight (env) | `DaylightEnvironment.md` | sun/sky; lon/lat, date/time, turbidity, models (Octane/Preetham/Nishita/Hosek-Wilkie) |
| Texture (env) | `TextureEnvironment.md` | HDRI background + importance sampling |
| Planetary (env) | `PlanetaryEnvrionment.md` | |
| IES | `IESLighting.md` | IES profile |
| Visible env | `TheVisibleEnvironment.md` | backplate/reflections/refractions |
| Blackbody | `BlackBody.md` | emission color temperature |
| Directional | `DirectionalLight.md` | |
| Sphere | `SphereLight.md` | |
| Analytic | `AnalyticLight.md` | |
| AI Light | `AILight.md` | |
| Light linking | `LightLinkingandLightExclusion.md` | include/exclude per object |

Environment is typically wired to the Render Target's Environment / Visible
Environment pins (`RenderTargetNode.md`). Also see `LightMixer.md`,
`InstanceHighlight.md`, `VolumetricSpotlight.md`.

**Bridge gap (live-build decision):** which of these are real native Lua light
nodes vs the current env/emissive proxy fallback — `octane_lua/lib/handlers.lua`
`handle_create_light()` notes native light constants can be nil on this build.
Resolve with `octane_probe_types` against the active Octane X build, then record
in capability metadata (Phase 4 acceptance).

---

## 11. What the bridge should do with this

1. `materials.py` builds a **pin→A_* constant** resolver at runtime from the live
   corpus; this file supplies the *human names* it must accept in payloads.
2. `create_material` payload fields map 1:1 to the pin tables above (group by
   layer: base / specular / roughness / IOR / coating / thinfilm / sheen /
   transmission / geometric).
3. A command that sets an unknown pin → capability warning, not silent drop.
4. Medium and Light are first-class sub-DSLs (`create_medium`, `create_light`)
   keyed off §9 / §10.
5. Texture-map inputs (Diffuse/Albedo/Bump/Normal/Opacity/Coating…) accept an
   `image_path` or a procedural node reference — wire through `octane_import_geometry`
   / texture node creation once those ops exist.

---

## 12. Provenance

- Extracted 2026-07-12 from `docs/OctaneX/*.md` (430-page manual mirror, commit
  `e253d93`).
- Pin names are verbatim from the manual's "Parameters" sections.
- `A_*`/`NT_*` Lua constants: **not present here** — see live corpus
  (`OctaneMCP/api/octane_lua_api.<build>.json`, generated by
  `octane_lua/export_api_docs_v2.lua`).
- Re-extract if `docs/OctaneX/` is regenerated from a newer manual build.
