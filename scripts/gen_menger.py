#!/usr/bin/env python3
"""Generate a Menger sponge as a single combined OBJ.

The Menger sponge is the 3D analogue of the Sierpinski carpet: start with a cube,
subdivide into 3x3x3 = 27 subcubes, remove the centre subcube and the centre of
each face (the 7 "cross" subcubes), then recurse on the 20 survivors. At depth d
there are 20^d subcubes.

OBJ contract (octanex-mcp bridge, 2026-07-15):
  - One combined OBJ; the importer makes ONE material pin per distinct `usemtl`.
  - Per-vertex colours are IGNORED on this build -> bind materials by name.
  - We emit a SINGLE `o`/`g`/`usemtl` block (one material) with a shared vertex
    pool. Flat shading uses per-face vertex normals (24 verts/cube).
  - Validate: max face index < vertex count.

Usage:
  gen_menger.py [depth=3] [target_half=2.5] [obj_path=assets/menger.obj]
"""
import sys
import os
import json
import numpy as np

ROOT = "/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP"
ASSET_DIR = os.path.join(ROOT, "assets")
os.makedirs(ASSET_DIR, exist_ok=True)

DEPTH = int(sys.argv[1]) if len(sys.argv) > 1 else 3
TARGET_HALF = float(sys.argv[2]) if len(sys.argv) > 2 else 2.5
OBJ_PATH = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ASSET_DIR, "menger.obj")
MANIFEST_PATH = os.path.join(
    os.path.dirname(OBJ_PATH), os.path.splitext(os.path.basename(OBJ_PATH))[0] + "_manifest.json")


def is_occupied(x: int, y: int, z: int, depth: int) -> bool:
    """Menger removal rule: a cell is removed if, at SOME recursion level, at
    least two of its three base-3 digits equal 1. That removes the centre
    subcube (1,1,1) and the six face-centre subcubes (e.g. 1,1,0 / 1,0,1 /
    0,1,1 and their +2 variants) = 7 of 27, leaving 20 survivors per axis.
    Recursing gives 20^d cubes (8000 at depth 3), not 26^d (17576)."""
    for _ in range(depth):
        ones = (x % 3 == 1) + (y % 3 == 1) + (z % 3 == 1)
        if ones >= 2:
            return False
        x //= 3
        y //= 3
        z //= 3
    return True


# 4 CCW-from-outside corner offsets (unit half) per face, with the face normal.
FACES = [
    ((1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1), (1, 0, 0)),    # +X
    ((-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1), (-1, 0, 0)),  # -X
    ((-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1), (0, 1, 0)),    # +Y
    ((-1, -1, -1), (-1, -1, 1), (1, -1, 1), (1, -1, -1), (0, -1, 0)),  # -Y
    ((-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1), (0, 0, 1)),    # +Z
    ((-1, -1, -1), (-1, 1, -1), (1, 1, -1), (1, -1, -1), (0, 0, -1)),  # -Z
]


def main() -> dict:
    n = 3 ** DEPTH
    cell = (2.0 * TARGET_HALF) / n
    half = cell / 2.0

    verts: list[tuple[float, float, float]] = []
    norms: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int]] = []

    for x in range(n):
        for y in range(n):
            for z in range(n):
                if not is_occupied(x, y, z, DEPTH):
                    continue
                cx = (x + 0.5 - n / 2.0) * cell
                cy = (y + 0.5 - n / 2.0) * cell
                cz = (z + 0.5 - n / 2.0) * cell
                base = len(verts)
                for face in FACES:
                    c0, c1, c2, c3, nrm = face
                    for dx, dy, dz in (c0, c1, c2, c3):
                        verts.append((cx + dx * half, cy + dy * half, cz + dz * half))
                        norms.append(nrm)
                # 6 faces * 2 tris, CCW (0,1,2)(0,2,3) referencing this cube's verts
                for f in range(6):
                    o = base + f * 4
                    faces.append((o + 0, o + 1, o + 2))
                    faces.append((o + 0, o + 2, o + 3))

    assert faces and max(max(f) for f in faces) < len(verts), "face index out of range"
    nv, nf = len(verts), len(faces)

    lines = ["# Menger sponge depth=%d (%d cubes)" % (DEPTH, nv // 24), "o menger", "g menger",
             "usemtl mat_sponge"]
    for (x, y, z) in verts:
        lines.append("v %.6f %.6f %.6f" % (x, y, z))
    for (nx, ny, nz) in norms:
        lines.append("vn %.6f %.6f %.6f" % (nx, ny, nz))
    for (a, b, c) in faces:
        lines.append("f %d//%d %d//%d %d//%d" % (a + 1, a + 1, b + 1, b + 1, c + 1, c + 1))

    with open(OBJ_PATH, "w") as fh:
        fh.write("\n".join(lines) + "\n")

    manifest = {
        "obj": OBJ_PATH, "depth": DEPTH, "cubes": nv // 24,
        "verts": nv, "faces": nf, "target_half": TARGET_HALF,
        "materials": {"mat_sponge": [0.16, 0.34, 0.86]},
    }
    with open(MANIFEST_PATH, "w") as fh:
        json.dump(manifest, fh, indent=2)

    print("OBJ:", OBJ_PATH, "cubes=%d verts=%d faces=%d" % (nv // 24, nv, nf))
    print("manifest:", MANIFEST_PATH)
    return manifest


if __name__ == "__main__":
    main()
