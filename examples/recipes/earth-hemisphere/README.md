# Cutaway Earth — point-cloud hemisphere

A dense, to-scale point-cloud cutaway of Earth's interior (PREM-style shells) plus
proportionally sparser atmospheric sheaths, rendered as layered translucent "jello"
with a glowing solid inner core. Built from `scripts/gen_earth_hemisphere.py`.

![octane-preview](octane-preview.png)

## What it shows

- **Interior shells** (radial point cloud, jittered for organic edges):
  inner core, outer core, lower mantle, upper mantle, continental + oceanic crust.
- **Cut face**: the flat hemisphere cross-section, layered so the internal structure
  reads clearly (smaller jitter than the shell so layering stays legible).
- **Atmosphere**: four translucent specular sheaths (troposphere → thermosphere) at
  low opacity, fuzzier/larger point radius than the solids.
- **WGS84 oblateness** (centrifugal flattening) is applied; crust is differentiated by
  a deterministic continent mask into lighter continental and darker oceanic tints.

## Materials (v3)

| Layer | Kind | Emission | Opacity | Transmission |
| --- | --- | --- | --- | --- |
| Inner core | glossy | 0.40 | 0.92 | 0.06 |
| Outer core | glossy | 0.26 | 0.50 | 0.40 |
| Lower / upper mantle | glossy | – | 0.40 | 0.55 |
| Crust (cont / ocean) | glossy | – | ~0.6–0.8 | – |
| Atmosphere (×4) | specular | – | 0.12–0.32 | 0.90–0.94 |

The inner core is a **solid glowing** node (high opacity, low transmission) so the
centre reads as hot rather than a hollow void. Mantle is pushed translucent/jello;
atmosphere is a soft fuzzy shell.

## Regenerate the OBJ

The committed `scene.obj` (≈168 MB) is **gitignored** — it is large generated data.
Regenerate locally before rendering:

```bash
PYTHONPATH= uv run python scripts/gen_earth_hemisphere.py \
    --density 0.05 \
    OctaneMCP_staging/earth-hemisphere
# mirror into the sandboxed Octane container assets dir, then drain:
#   cp OctaneMCP_staging/earth-hemisphere/scene.obj \
#      ~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/assets/earth-hemisphere.obj
```

`--density 0.05` is the bounded live-render preset (≈2.19 M vertices). Raise it for
more crust resolution at higher render cost.

## Render

- `scene.json` holds the full command sequence (import → 19 material creates → 19
  assigns → camera → lighting → render → preview at 1280×1280 / 800 spp).
- Drain with `octane_run_oneshot_bridge()` (or the persistent bridge), then poll
  `queue/` to zero.
- **Cost:** ~10–12 min at 800 spp on the full-density OBJ (Mac Studio / Octane X).
  Use the `--density` preset for preview passes.

## Known framing pitfall

At `camera [16.0, 6.4, 20.6]`, `target [0,0,-1]`, the cut plane faces +Z and the
camera looks nearly **head-on down the cut axis**, so the result reads as a flat
disc/wheel rather than a 3D hemisphere. To show the hemisphere bulge *and* the
layered cross-section in perspective, rotate the cut plane (or the camera) ~30–45°
off-axis. This recipe ships the confirmed-material version; an off-axis camera pass
is a recommended next iteration.

## Quality checklist

- [x] Inner core glows (not a dark hollow)
- [x] Mantle reads as translucent layered jello
- [x] Atmosphere sheaths visible as a soft outer shell
- [x] Crust dense enough to read as a surface, not dots
- [ ] Off-axis 3D framing (see pitfall above)
