#!/usr/bin/env python3
"""Generate a smooth photoreal math surface OBJ for OctaneX MCP render.

Function: f(x,y) = sin(R)/max(R,0.3) * (0.6 + 0.4*cos(4*atan2(y,x))) * 1.8
  - sinc -> classic rippling central peak, smooth radial decay
  - cosine ridge term -> lobed/flower-like azimuthal modulation (more visual interest than bare sinc)
  - scaled to sit nicely in a [-6,6]^2 domain, amplitude ~[-2.5, 2.5]

Writes a single usemtl group (surface_mat) so import_geometry creates ONE
material pin; a single Octane glossy material is assigned (no group_index needed).
Smooth-shaded: per-vertex normals (averaged), no faceted facets.
"""
import math
import json
import os

TX = 200          # grid resolution (TX x TX quads -> (TX-1)^2*2 tris)
DOM = 6.0         # x,y in [-DOM, DOM]
ZSCALE = 2.8

def f(x, y):
    r = math.hypot(x, y)
    sinc = math.sin(r) / max(r, 0.3)
    ridge = 0.45 + 0.55 * math.cos(4.0 * math.atan2(y, x))
    return sinc * ridge * ZSCALE

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ws = os.path.join(os.path.dirname(here), "OctaneMCP_staging")
    os.makedirs(ws, exist_ok=True)
    name = "math_surface"
    obj = os.path.join(ws, f"{name}.obj")

    # grid coordinates
    xs = [ -DOM + (2*DOM)*i/(TX-1) for i in range(TX) ]
    ys = [ -DOM + (2*DOM)*j/(TX-1) for j in range(TX) ]
    zs = [[ f(xs[i], ys[j]) for j in range(TX) ] for i in range(TX)]

    lines = ["# Photoreal math surface: sinc(r) * (0.6+0.4*cos(4*theta))", "o surface", f"usemtl {name}_mat"]

    # vertices (1-indexed): v[i][j] at index 1 + i*TX + j
    for i in range(TX):
        for j in range(TX):
            lines.append(f"v {xs[i]:.5f} {zs[i][j]:.5f} {ys[j]:.5f}")  # Octane: X right, Y up, Z toward cam

    # simple per-vertex normals = normalized gradient cross (good enough, smooth)
    def normal_at(i, j):
        il = max(i-1, 0); ir = min(i+1, TX-1)
        jd = max(j-1, 0); ju = min(j+1, TX-1)
        # tangent along x (i) and z (j)
        dx = (xs[ir]-xs[il], zs[ir][j]-zs[il][j], 0.0)
        dz = (0.0, zs[i][ju]-zs[i][jd], ys[ju]-ys[jd])
        # normal = dz x dx  (so it points up for positive height)
        nx = dz[1]*dx[2] - dz[2]*dx[1]
        ny = dz[2]*dx[0] - dz[0]*dx[2]
        nz = dz[0]*dx[1] - dz[1]*dx[0]
        L = math.hypot(nx, ny, nz) or 1.0
        return (nx/L, ny/L, nz/L)
    for i in range(TX):
        for j in range(TX):
            n = normal_at(i, j)
            lines.append(f"vn {n[0]:.4f} {n[1]:.4f} {n[2]:.4f}")

    def vidx(i, j):
        return 1 + i*TX + j
    # faces (two triangles per quad), with normals
    for i in range(TX-1):
        for j in range(TX-1):
            a = vidx(i, j); b = vidx(i+1, j); c = vidx(i+1, j+1); d = vidx(i, j+1)
            lines.append(f"f {a}//{a} {b}//{b} {c}//{c}")
            lines.append(f"f {a}//{a} {c}//{c} {d}//{d}")

    with open(obj, "w") as fh:
        fh.write("\n".join(lines) + "\n")

    # scene metadata helper (for camera framing / notes)
    meta = {
        "name": name,
        "domain": [-DOM, DOM],
        "z_range": [min(min(row) for row in zs), max(max(row) for row in zs)],
        "tris": (TX-1)*(TX-1)*2,
        "verts": TX*TX,
    }
    with open(os.path.join(ws, f"{name}.meta.json"), "w") as fh:
        json.dump(meta, fh, indent=2)

    print(f"WROTE {obj}")
    print(f"  verts={meta['verts']} tris={meta['tris']} z_range={meta['z_range']}")

if __name__ == "__main__":
    main()
