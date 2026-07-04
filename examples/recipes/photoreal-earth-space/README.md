# Photoreal Earth in Space

![Photoreal Earth target preview](photoreal-preview.png)

- **Category:** Photoreal/PBR space rendering
- **Purpose:** Demonstrate a high-quality orbital Earth target with oceans, land, cloud shells, atmospheric rim glow, black space, and sunlight direction.
- **Starter prompt:** Render a photoreal planet Earth in deep space with detailed oceans, continents, cloud bands, a thin blue atmospheric rim, and cinematic sunlight.

## Files

- `scene.obj` — reusable procedural Earth sphere with ocean/land/cloud/atmosphere material regions.
- `scene.mtl` — material intent for ocean, shallow water, land, ice, translucent clouds, and atmosphere.
- `scene.json` — camera, lighting, PBR material notes, quality checklist, and MCP command sequence.
- `photoreal-preview.png` — photoreal target/reference image for visual review.

## Important note

`photoreal-preview.png` is a generated target/reference render for teaching and visual direction. It is **not yet a verified native Octane output** from the bridge. Use it as a quality bar, then re-render `scene.obj`/`scene.mtl` in Octane X and add `octane-preview.png` once the native render has been verified.

The checked-in geometry uses procedural continent/cloud masks so it stays lightweight and deterministic. For final hero renders, replace those masks with real NASA Blue Marble-style texture maps or Octane procedural texture nodes when the bridge exposes texture wiring.

## MCP tools to use

- `octane_import_geometry`
- `octane_set_camera`
- `octane_set_lighting`
- `octane_start_render`
- `octane_save_preview`

## Steps

1. Import `scene.obj` with `octane_import_geometry(path="examples/recipes/photoreal-earth-space/scene.obj", name="photoreal-earth-space")`.
2. Apply the camera from `scene.json`.
3. Use a hard directional sun/space lighting setup. If `space_sun` is unavailable, start with `soft_studio`, then manually tune toward black background and camera-left sunlight.
4. Drain the queue with `octane_lua/hermes_bridge_oneshot_v2.lua`.
5. Save a native Octane preview and compare it with `photoreal-preview.png`.

## What agents should learn

Photoreal planet renders need layered material intent:

- ocean: dark, glossy, subtly specular;
- land: rough, muted, non-neon colors;
- clouds: separate translucent shell above the surface;
- atmosphere: thin transparent/emissive blue rim, not a solid sphere;
- lighting: hard sunlight plus deep black space and a readable terminator.

## Quality checklist

- Target/reference image shows recognizable Earth, cloud bands, atmosphere rim, and black space background.
- Native Octane output must be saved as `octane-preview.png` before claiming native photoreal success.
- Oceans should be glossy and darker than land.
- Cloud shell should remain visibly above the surface without hiding continents entirely.
- Atmosphere should read as a thin rim/glow, not a thick opaque shell.
- If the procedural continents are too stylized, replace them with real Earth texture maps before using the render as a hero image.

## Variations to explore

- Add a Moon sphere and orbital distance scale annotation.
- Create day/night versions with city-light emissive texture hints.
- Add camera flyby animation using the frame-sequence pattern.
- Replace procedural masks with real equirectangular Earth textures once texture-node support is exposed.
- Add scientific overlays: latitude/longitude grid, satellite tracks, aurora bands, or weather fronts.
