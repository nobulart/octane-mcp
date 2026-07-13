#!/usr/bin/env python3
"""gen_geo_displacement.py — real raster -> heightfield OBJ for OctaneX.

Reads a single-band raster (GeoTIFF / any GDAL-readable) and builds a
subdivided-plane heightfield mesh. z = normalized(value) * vscale.
No vertex colours / textures (the OctaneX importer + bridge ignore them;
see docs/recipe-book.md L60) — the result is a single-material relief.

Usage:
  gen_geo_displacement.py <in.tif> <out.obj> [grid=256] [vscale=1.0] [name=geo]

Requires: gdal + numpy (present in the homebrew python stack used for
image/geometry work; NOT the Hermes venv).
"""
import sys, math
import numpy as np
from osgeo import gdal


def load_band(path):
    gdal.UseExceptions()
    ds = gdal.Open(path)
    band = ds.GetRasterBand(1)
    arr = band.ReadAsArray().astype(np.float32)
    # Nodata / inf / nan -> ignore when normalizing.
    nd = band.GetNoDataValue()
    if nd is not None:
        arr[arr == nd] = np.nan
    arr[~np.isfinite(arr)] = np.nan
    return arr


def downsample(arr, grid):
    """Average-pool arr to grid x grid (handles non-divisible sizes)."""
    h, w = arr.shape
    sy, sx = max(1, h // grid), max(1, w // grid)
    # trim to multiple
    arr = arr[: sy * grid, : sx * grid]
    pooled = arr.reshape(grid, sy, grid, sx).mean(axis=(1, 3))
    return pooled


def write_obj(arr, path, vscale, name):
    grid = arr.shape[0]
    # Normalize to [0,1] over finite values, then center.
    finite = arr[np.isfinite(arr)]
    lo, hi = (finite.min(), finite.max()) if finite.size else (0.0, 1.0)
    span = (hi - lo) if hi > lo else 1.0
    z = np.where(np.isfinite(arr), (arr - lo) / span, 0.0) * vscale
    # Map grid -> unit plane centered at origin, z up.
    verts = []
    for j in range(grid):
        for i in range(grid):
            x = (i / (grid - 1) - 0.5) * 2.0
            y = (j / (grid - 1) - 0.5) * 2.0
            verts.append((x, y, z[j, i]))
    with open(path, "w") as f:
        f.write(f"# geo heightfield {name}: {grid}x{grid} from raster\n")
        for (x, y, zz) in verts:
            f.write(f"v {x:.6f} {y:.6f} {zz:.6f}\n")
        # faces (two triangles per cell)
        for j in range(grid - 1):
            for i in range(grid - 1):
                a = j * grid + i + 1
                b = j * grid + i + 2
                c = (j + 1) * grid + i + 1
                d = (j + 1) * grid + i + 2
                f.write(f"f {a} {b} {d}\n")
                f.write(f"f {a} {d} {c}\n")
    n_verts = len(verts)
    n_faces = 2 * (grid - 1) * (grid - 1)
    return n_verts, n_faces, lo, hi


def main():
    if len(sys.argv) < 3:
        print("usage: gen_geo_displacement.py <in.tif> <out.obj> [grid=256] [vscale=1.0] [name=geo]")
        sys.exit(2)
    in_path = sys.argv[1]
    out_path = sys.argv[2]
    grid = int(sys.argv[3]) if len(sys.argv) > 3 else 256
    vscale = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    name = sys.argv[5] if len(sys.argv) > 5 else "geo"

    arr = load_band(in_path)
    if arr.size == 0:
        print(f"ERROR: no data in {in_path}")
        sys.exit(1)
    arr = downsample(arr, grid)
    nv, nf, lo, hi = write_obj(arr, out_path, vscale, name)
    print(f"wrote {out_path}: {grid}x{grid} grid, {nv} verts, {nf} faces "
          f"(z normalized from [{lo:.3g}, {hi:.3g}] * vscale={vscale})")


if __name__ == "__main__":
    main()
