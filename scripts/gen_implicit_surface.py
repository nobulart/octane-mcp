#!/usr/bin/env /usr/bin/python3
"""Generate a triply-periodic / implicit minimal surface as a plain single-
material OBJ (no groups, no bands, no vertex colours). Single-material render
path only -- Octane X on this build ignores baked vc and cannot set texture
node colours, so the only working colour is the material diffuse (solid).

Usage: gen_implicit.py <out.obj> <name> <formula> [res=132] [target_radius=2.5] [periods=1]
formula: gyroid | schwarz | neovius | lidinoid | schwarz_pd | diamond | sphere
periods: number of fundamental periods per axis. 1 = a SINGLE manifold (one
  fundamental domain) matching the math-museum reference; >1 tiles multiple cells.

CRITICAL: marching_cubes over a periodic field at level 0 yields disconnected
fragments (boundary artifacts). We keep ONLY the largest connected component so
the result is a single manifold, matching the canonical unit-cell reference.
"""
import sys
import numpy as np
from collections import deque
from skimage import measure

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/surface.obj"
NAME = sys.argv[2] if len(sys.argv) > 2 else "surface"
FORMULA = sys.argv[3] if len(sys.argv) > 3 else "gyroid"
RES = int(sys.argv[4]) if len(sys.argv) > 4 else 132
TARGET_RADIUS = float(sys.argv[5]) if len(sys.argv) > 5 else 2.5
PERIODS = float(sys.argv[6]) if len(sys.argv) > 6 else 1.0

# One fundamental period of the implicit field is 2*pi. Sample `periods`
# periods per axis so periods=1 yields a single connected manifold (one cell).
HALF = np.pi * PERIODS
dom = np.linspace(-HALF, HALF, RES)
X, Y, Z = np.meshgrid(dom, dom, dom, indexing="ij")

if FORMULA == "gyroid":
    F = np.sin(X)*np.cos(Y) + np.sin(Y)*np.cos(Z) + np.sin(Z)*np.cos(X)
elif FORMULA in ("schwarz", "schwarz_p"):
    # Schwarz P (primitive) approximation (Wikipedia): cos x + cos y + cos z = 0
    F = np.cos(X) + np.cos(Y) + np.cos(Z)
elif FORMULA == "schwarz_h":
    # Schwarz H (hexagonal) approximation (Wikipedia): sin x cos y cos z
    #   + cos x sin y cos z + cos x cos y sin z = 0
    F = (np.sin(X)*np.cos(Y)*np.cos(Z)
         + np.cos(X)*np.sin(Y)*np.cos(Z)
         + np.cos(X)*np.cos(Y)*np.sin(Z))
elif FORMULA == "schwarz_pd":
    F = (np.cos(X)*np.cos(Y)*np.cos(Z)
         - np.sin(X)*np.sin(Y)*np.sin(Z))
elif FORMULA == "neovius":
    # Canonical Neovius (Wikipedia): 3(cos x + cos y + cos z) + 4 cos x cos y cos z = 0
    F = 3*(np.cos(X) + np.cos(Y) + np.cos(Z)) + 4*np.cos(X)*np.cos(Y)*np.cos(Z)
elif FORMULA == "lidinoid":
    c = np.cos
    s = np.sin
    F = (0.5*(s(2*X)*c(Y)*s(Z) + s(2*Y)*c(Z)*s(X) + s(2*Z)*c(X)*s(Y))
         - 0.5*(c(2*X)*c(2*Y) + c(2*Y)*c(2*Z) + c(2*Z)*c(2*X)) + 0.3)
elif FORMULA == "diamond":
    s = np.sin
    c = np.cos
    F = (s(X)*s(Y)*s(Z) + s(X)*c(Y)*c(Z) + c(X)*s(Y)*c(Z) + c(X)*c(Y)*s(Z))
elif FORMULA == "sphere":
    r = 1.6
    F = X**2 + Y**2 + Z**2 - r*r
else:
    F = np.sin(X)*np.cos(Y) + np.sin(Y)*np.cos(Z) + np.sin(Z)*np.cos(X)

verts, faces, normals, _ = measure.marching_cubes(
    F, level=0.0, spacing=(dom[1]-dom[0],)*3,
    gradient_direction="ascent", allow_degenerate=False)

# --- keep only the largest connected component (single manifold) ---
if len(faces) > 0:
    adj = [set() for _ in range(len(verts))]
    for a, b, c in faces:
        adj[a] |= {b, c}; adj[b] |= {a, c}; adj[c] |= {a, b}
    seen = set(); comps = []
    for s in range(len(verts)):
        if s in seen:
            continue
        q = deque([s]); seen.add(s); comp = []
        while q:
            u = q.popleft(); comp.append(u)
            for v in adj[u]:
                if v not in seen:
                    seen.add(v); q.append(v)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    keep = set(comps[0])
    faces = np.array([f for f in faces if f[0] in keep and f[1] in keep and f[2] in keep])
    # reindex
    remap = {old: new for new, old in enumerate(sorted(keep))}
    verts = verts[np.array(sorted(keep))]
    faces = np.array([[remap[v] for v in f] for f in faces])

# centre + scale
cx, cy, cz = verts.mean(axis=0)
verts = verts - np.array([cx, cy, cz])
maxr = np.max(np.sqrt((verts ** 2).sum(axis=1)))
verts = verts * (TARGET_RADIUS / maxr)

with open(OUT, "w") as f:
    f.write(f"# {FORMULA} (plain, single material, largest component)\n")
    f.write(f"o {NAME}\n")
    for v in verts:
        f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
    for tri in faces:
        f.write(f"f {tri[0]+1} {tri[1]+1} {tri[2]+1}\n")

print(f"wrote {OUT}: {len(verts)} verts, {len(faces)} faces ({FORMULA}, single manifold)")
