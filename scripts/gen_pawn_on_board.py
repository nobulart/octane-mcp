#!/usr/bin/env python3
"""Generate a combined chessboard + pawn OBJ (single mesh, 3 usemtl groups).

Groups are emitted in a fixed order so the Octane bridge's assign_material
group_index maps deterministically:
  1 = cb_base  (dark board base)
  2 = cb_light (cream/white squares)
  3 = pawn     (lathed green pawn, lifted to sit on the board)
The render target exposes ONE mesh pin, so a multi-object hero shot must live
in a single combined OBJ with one group per material.
"""
import math
import os
import sys

PAWN_PROFILE = [
    (0.00, 0.00), (0.85, 0.00), (0.86, 0.10), (0.78, 0.16),
    (0.52, 0.26), (0.50, 0.34), (0.30, 0.50), (0.27, 0.95),
    (0.27, 1.00), (0.34, 1.06), (0.47, 1.13), (0.33, 1.21),
    (0.30, 1.30), (0.52, 1.55), (0.61, 1.80), (0.56, 2.00),
    (0.34, 2.15), (0.00, 2.20),
]
SEG = 96
PAWN_Y = 0.04  # lift so the base sits on the tile top (tiles top at y=0.04)


def catmull(p0, p1, p2, p3, t):
    t2 = t * t
    t3 = t2 * t
    r = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
    y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
    return r, y


def pawn_rings(samples_per_seg=6):
    pts = []
    n = len(PAWN_PROFILE)
    for i in range(n - 1):
        p0 = PAWN_PROFILE[max(0, i - 1)]
        p1 = PAWN_PROFILE[i]
        p2 = PAWN_PROFILE[i + 1]
        p3 = PAWN_PROFILE[min(n - 1, i + 2)]
        for s in range(samples_per_seg):
            pts.append(catmull(p0, p1, p2, p3, s / samples_per_seg))
    pts.append(PAWN_PROFILE[-1])
    rings = []
    for (r, y) in pts:
        ring = [(r * math.cos(2 * math.pi * j / SEG), y + PAWN_Y, r * math.sin(2 * math.pi * j / SEG)) for j in range(SEG)]
        rings.append(ring)
    return rings


def box(cx, cy, cz, sx, sy, sz):
    """Return 8 verts + 12 triangulated faces (indices relative to a base offset)."""
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    v = [
        (cx - hx, cy - hy, cz - hz), (cx + hx, cy - hy, cz - hz),
        (cx + hx, cy - hy, cz + hz), (cx - hx, cy - hy, cz + hz),
        (cx - hx, cy + hy, cz - hz), (cx + hx, cy + hy, cz - hz),
        (cx + hx, cy + hy, cz + hz), (cx - hx, cy + hy, cz + hz),
    ]
    f = [
        (1, 2, 3), (1, 3, 4),       # bottom
        (5, 7, 6), (5, 8, 7),       # top
        (1, 5, 6), (1, 6, 2),       # -x
        (2, 6, 7), (2, 7, 3),       # +x
        (3, 7, 8), (3, 8, 4),       # +z
        (4, 8, 5), (4, 5, 1),       # -z
    ]
    return v, f


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
        "~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/assets/pawn_on_board.obj")
    verts = []
    groups = []  # list of (group_name, [face_idx_triples])

    def add_group(name, group_verts, group_faces):
        base = len(verts)
        for v in group_verts:
            verts.append(v)
        faces = [(base + a, base + b, base + c) for (a, b, c) in group_faces]
        groups.append((name, faces))

    # Group 1: dark board base (8.6 x 0.2 x 8.6, top at y=0)
    bv, bf = box(0, -0.1, 0, 8.6, 0.2, 8.6)
    add_group("cb_base", bv, bf)

    # Group 2: light squares (32 tiles), top at y=0.04
    light_v, light_f = [], []
    for f in range(8):
        for r in range(8):
            if (f + r) % 2 != 0:
                continue
            cx, cz = f - 3.5, r - 3.5
            v, fa = box(cx, 0.01, cz, 0.96, 0.06, 0.96)
            base = len(light_v)
            light_v.extend(v)
            light_f.extend([(base + a, base + b, base + c) for (a, b, c) in fa])
    add_group("cb_light", light_v, light_f)

    # Group 3: pawn (lathed), lifted by PAWN_Y
    pr = pawn_rings()
    pawn_v = [v for ring in pr for v in ring]
    # Build pawn faces in LOCAL 1-indexed coords (1..nr*SEG); add_group rebases
    # them to the global vertex range, exactly like the cb_light boxes above.
    nr = len(pr)
    pawn_f = []
    pid = lambda ri, ci: 1 + ri * SEG + ci
    apex = nr * SEG  # last local pawn vertex (top center, r==0)
    for ri in range(nr - 1):
        for ci in range(SEG):
            cn = (ci + 1) % SEG
            a, b, c, d = pid(ri, ci), pid(ri, cn), pid(ri + 1, cn), pid(ri + 1, ci)
            if ri == 0:
                pawn_f.append((1, b, c))  # bottom fan (first local vert is axis)
            elif ri == nr - 2:
                pawn_f.append((a, b, apex))
            else:
                pawn_f.append((a, b, c))
                pawn_f.append((a, c, d))
    add_group("pawn", pawn_v, pawn_f)

    lines = ["# chessboard + pawn, combined surface-of-revolution scene", "o pawn_board"]
    for (x, y, z) in verts:
        lines.append(f"v {x:.5f} {y:.5f} {z:.5f}")
    for (name, faces) in groups:
        lines.append(f"g {name}")
        lines.append(f"usemtl {name}")
        for (a, b, c) in faces:
            lines.append(f"f {a} {b} {c}")
    text = "\n".join(lines) + "\n"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        fh.write(text)
    print(f"wrote {out}  verts={len(verts)} groups={[(g[0], len(g[1])) for g in groups]}")


if __name__ == "__main__":
    main()
