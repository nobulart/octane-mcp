# Cutaway Earth — point-cloud hemisphere

A dense, to-scale point-cloud cutaway of Earth's interior (PREM-like shells) plus
proportionally sparser atmospheric sheaths, rendered as layered translucent "jello"
with a glowing solid inner core. **Particles are smooth spheres** (8-segment), the
interior is ~30% less dense than a solid fill and homogenised with global jitter,
and **LLSVP thermochemical provinces + mantle-plume tendrils** are modelled as
CMB-rooted upwellings. Built from `scripts/gen_earth_hemisphere.py`.

![octane-preview](octane-preview.png)

## What it shows

- **Interior shells** (radial point cloud of smooth spheres, jittered for organic
  edges): inner core, outer core, lower mantle, upper mantle, continental + oceanic
  crust.
- **Cut face**: the flat hemisphere cross-section, layered so the internal structure
  reads clearly (smaller jitter than the shell so layering stays legible).
- **Atmosphere**: four translucent specular sheaths (troposphere → thermosphere) at
  low opacity, fuzzier/larger point radius than the solids.
- **LLSVP provinces + mantle plumes** (CMB-rooted dynamics): two broad magenta
  thermochemical piles at the core-mantle boundary (~3480 km) extending ~1300 km
  into the lower mantle, with thin gold buoyant tendrils rising from their edges
  toward the mid-upper mantle. Plumes initiate at LLSVP edges, per the geodynamics
  literature.
- **WGS84 oblateness** (centrifugal flattening) is applied; crust is differentiated by
  a deterministic continent mask into lighter continental and darker oceanic tints.

## Materials (v4)

| Layer | Kind | Emission | Opacity | Transmission |
| --- | --- | --- | --- | --- |
| Inner core | glossy | 0.40 | 0.92 | 0.06 |
| Outer core | glossy | 0.26 | 0.50 | 0.40 |
| Lower / upper mantle | glossy | – | 0.40 | 0.55 |
| Crust (cont / ocean) | glossy | – | ~0.6–0.8 | – |
| **LLSVP province** | glossy | 0.18 | 0.55 | 0.30 |
| **Plume tendril** | glossy | 0.45 | 0.92 | 0.05 |
| Atmosphere (×4) | specular | – | 0.12–0.32 | 0.90–0.94 |

The inner core is a **solid glowing** node (high opacity, low transmission) so the
centre reads as hot rather than a hollow void. Mantle is pushed translucent/jello;
atmosphere is a soft fuzzy shell. LLSVP/plume are distinct magenta + gold so the
deep-mantle dynamics read against the orange core.

## Generation knobs (v4)

- `SPHERE_SEGMENTS = 8` — smooth spheres (4 read as faceted icosahedrons in closeup).
- `INTERIOR_DENSITY_SCALE = 0.70` — ~30% fewer particles in the four solid shells.
- `JITTER_GLOBAL = 0.05` — uniform positional jitter on *every* particle, breaking
  the golden-angle lattice so volumes read homogeneous (no grid pattern).
- `blob_cloud` / `plume_tendril` — LLSVP provinces + wavy plume conduits, both
  constrained to the rendered (lower) hemisphere so no structure floats in the
  cut-away void.

## Regenerate the OBJ

The committed `scene.obj` (≈458 MB) is **gitignored** — it is large generated data.
Regenerate locally before rendering:

```bash
PYTHONPATH= uv run python scripts/gen_earth_hemisphere.py \
    --density 0.05 \
    OctaneMCP_staging/earth-hemisphere-v4
# mirror into the sandboxed Octane container assets dir, then drain:
#   cp OctaneMCP_staging/earth-hemisphere-v4/scene.obj \
#      ~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/assets/earth-hemisphere-v4.obj
```

`--density 0.05` is the bounded live-render preset (~254k particles, ~6.1 M verts).
Raise it for more crust resolution at higher render cost.

## Render

- `scene.json` holds the full command sequence (import → 23 material creates → 23
  assigns → camera → lighting → render → preview at 1280×1280 / 800 spp).
- Drain with `octane_run_oneshot_bridge()` (or the persistent bridge), then poll
  `queue/` to zero. The bridge saves the default `octane-preview.png`; promote it to
  the job-specific path after the render converges. `scripts/_drain_v4.py` automates
  this (recovers strays, full-queue assert, promotes preview + writes `done.json`).
- **Cost:** ~12–15 min at 800 spp on the full-density OBJ (Mac Studio / Octane X).
  Use the `--density` preset for preview passes.

## Camera (off-axis "Hermes Camera")

The recipe ships an **off-axis** camera (position `[-8.982, -19.818, 13.783]`,
target `[-0.062, -0.095, -1.137]`, fov 28, focus 27.632) so the hemisphere reads as
a 3D bulge *with* the layered cut face in perspective — not the flat head-on disc
that the earlier `camera [16.0, 6.4, 20.6]` produced. This resolved the long-standing
framing pitfall; the off-axis pass is now the default.

## Quality checklist

- [x] Inner core glows (not a dark hollow)
- [x] Mantle reads as translucent layered jello
- [x] Atmosphere sheaths visible as a soft outer shell
- [x] Crust dense enough to read as a surface, not dots
- [x] Particles are smooth spheres (not faceted)
- [x] Interior ~30% less dense (net, after +20% request) + homogenised jitter (no grid)
- [x] LLSVP provinces + plume tendrils visible, rooted at CMB, inside the body
- [x] Off-axis 3D framing (Hermes Camera) — no longer a head-on disc
