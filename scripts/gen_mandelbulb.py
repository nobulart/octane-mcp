#!/usr/bin/env python3
"""Generate a Mandelbulb (the iconic 3D fractal) as a single combined OBJ whose
surface is partitioned into N radius bands, each emitted as its own
`o`/`g`/`usemtl` group so it can be bound to a distinct material by name.

Colour contract (octanex-mcp bridge, 2026-07-15):
  - The Octane X OBJ importer exposes ONE material INPUT pin per UNIQUE
    `usemtl` name. Bind with create_material + assign_material matched by name.
  - Per-vertex colours are IGNORED on this build -> never rely on them.
  - Emit ONE `o <group> + usemtl <mat> + g <group>` PER material group
    (a single shared `o` renders BLANK).
  - Validate: max face index must be <= vertex count.

Usage:
  gen_mandelbulb.py [n_colors=7] [power=8] [res=150] [target_radius=2.5]
"""
import sys
import os
import math
import numpy as np
from skimage import measure

ROOT = "/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP"
ASSET_DIR = os.path.join(ROOT, "assets")
os.makedirs(ASSET_DIR, exist_ok=True)

N_COLORS = int(sys.argv[1]) if len(sys.argv) > 1 else 7
POWER = float(sys.argv[2]) if len(sys.argv) > 2 else 8.0
RES = int(sys.argv[3]) if len(sys.argv) > 3 else 150
TARGET_RADIUS = float(sys.argv[4]) if len(sys.argv) > 4 else 2.5

OBJ_PATH = sys.argv[5] if len(sys.argv) > 5 else os.path.join(ASSET_DIR, "mandelbulb.obj")
MANIFEST_PATH = os.path.join(os.path.dirname(OBJ_PATH), os.path.splitext(os.path.basename(OBJ_PATH))[0] + "_manifest.json")

# ---- Mandelbulb orbit-trap scalar field (vectorized) ----
# field(p) = min orbit radius over escape iterations. Inside the bulb the orbit
# stays near the origin (small trap); outside it escapes (large trap). The
# isosurface field == TRAP_LEVEL approximates the bulb boundary.
TRAP_LEVEL = 0.85
DOMAIN = 1.30
MAX_ITER = 10
ESCAPE = 2.0

dom = np.linspace(-DOMAIN, DOMAIN, RES)
X, Y, Z = np.meshgrid(dom, dom, dom, indexing="ij")
cx, cy_0, cz_0 = X.ravel().copy(), Y.ravel().copy(), Z.ravel().copy()
zx, zy, zz = cx.copy(), cy_0.copy(), cz_0.copy()
trap = np.full(cx.shape, np.inf, dtype=np.float64)
dr = np.ones(cx.shape, dtype=np.float64)

for _ in range(MAX_ITER):
    r2 = zx * zx + zy * zy + zz * zz
    r = np.sqrt(r2)
    np.minimum(trap, r, out=trap)
    escaped = r > ESCAPE
    # polar coords (guard r==0)
    safe_r = np.where(r > 1e-12, r, 1e-12)
    theta = np.arccos(np.clip(zz / safe_r, -1.0, 1.0))
    phi = np.arctan2(zy, zx)
    zr = r ** POWER
    theta_p = theta * POWER
    phi_p = phi * POWER
    dr = (r ** (POWER - 1.0)) * POWER * dr + 1.0
    sx = np.sin(theta_p) * np.cos(phi_p)
    sy = np.sin(theta_p) * np.sin(phi_p)
    sz = np.cos(theta_p)
    nzx = zr * sx + cx
    nzy = zr * sy + cy_0
    nzz = zr * sz + cz_0
    mask = ~escaped
    zx[mask] = nzx[mask]
    zy[mask] = nzy[mask]
    zz[mask] = nzz[mask]

field = trap.reshape(X.shape)
verts, faces, normals, _ = measure.marching_cubes(
    field, level=TRAP_LEVEL, spacing=(dom[1] - dom[0],) * 3,
    gradient_direction="ascent", allow_degenerate=False)

# world coords
spacing = dom[1] - dom[0]
verts = verts * spacing + dom[0]

# centre + scale to target radius
c = verts.mean(axis=0)
verts = verts - c
maxr = np.max(np.sqrt((verts ** 2).sum(axis=1)))
verts = verts * (TARGET_RADIUS / maxr)

# ---- partition surface into radius bands ----
rad = np.sqrt((verts ** 2).sum(axis=1))
rmin, rmax = rad.min(), rad.max()
# band index per vertex
band_of_vert = np.minimum(
    (N_COLORS - 1),
    ((rad - rmin) / (rmax - rmin + 1e-9) * N_COLORS).astype(int))

# reindex faces so each band's vertices are emitted contiguously (per-object block)
# We keep a global vertex pool but emit per-band `o`/`g`/`usemtl` blocks; OBJ
# face indices may reference any global vertex, which is valid.
faces = faces.astype(int)
max_idx = faces.max()
assert max_idx < len(verts), f"face index {max_idx} >= verts {len(verts)}"

# colours: vivid rainbow (HSV hue sweep)
def hsv_to_rgb(h, s, v):
    i = int(h * 6.0) % 6
    f = h * 6.0 - int(h * 6.0)
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)
    r, g, b = [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)][i]
    return (r, g, b)

materials = {}
lines = ["# Mandelbulb (power=%.1f) coloured by radius band" % POWER, "o mandelbulb"]
for b in range(N_COLORS):
    hue = b / max(1, (N_COLORS - 1)) * 0.85  # red -> violet
    col = hsv_to_rgb(hue, 0.85, 1.0)
    materials["mat_band_%d" % b] = [round(x, 3) for x in col]

# emit vertices + normals (shared pool)
for (x, y, z) in verts:
    lines.append("v %.6f %.6f %.6f" % (x, y, z))
for (nx, ny, nz) in normals:
    lines.append("vn %.6f %.6f %.6f" % (nx, ny, nz))

# emit per-band face blocks
cur = None
band_counts = {}
for f in faces:
    b = int(round(band_of_vert[f].mean()))  # band by face centroid
    key = "mat_band_%d" % b
    if key != cur:
        lines.append("usemtl %s" % key)
        lines.append("o band_%d" % b)
        lines.append("g band_%d" % b)
        cur = key
        band_counts[b] = band_counts.get(b, 0) + 1
    fstr = " ".join("%d//%d" % (v + 1, v + 1) for v in f)
    lines.append("f %s" % fstr)

with open(OBJ_PATH, "w") as fh:
    fh.write("\n".join(lines) + "\n")

import json
manifest = {
    "obj": OBJ_PATH,
    "n_colors": N_COLORS,
    "power": POWER,
    "target_radius": TARGET_RADIUS,
    "verts": int(len(verts)),
    "faces": int(len(faces)),
    "radius_min": float(rmin), "radius_max": float(rmax),
    "band_counts": band_counts,
    "materials": materials,
}
with open(MANIFEST_PATH, "w") as fh:
    json.dump(manifest, fh, indent=2)

print("OBJ:", OBJ_PATH, "verts=%d faces=%d" % (len(verts), len(faces)))
print("radius min/range: %.3f / %.3f" % (rmin, rmax - rmin))
print("band_counts:", band_counts)
print("materials:", materials)
print("manifest:", MANIFEST_PATH)
