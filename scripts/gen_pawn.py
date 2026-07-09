#!/usr/bin/env python3
"""Generate a smooth chess-pawn OBJ by lathing a Catmull-Rom profile (surface of revolution)."""
import math
import os
import sys

# (radius r, height y) control points for the pawn silhouette (axis = Y).
# Bottom and top terminate on the axis (r == 0) so the lathe is solid-capped.
PROFILE = [
    (0.00, 0.00),  # bottom center
    (0.85, 0.00),  # base outer bottom
    (0.86, 0.10),  # base foot lip
    (0.78, 0.16),  # base side
    (0.52, 0.26),  # base shoulder
    (0.50, 0.34),  # stem root
    (0.30, 0.50),  # stem taper
    (0.27, 0.95),  # stem thin
    (0.27, 1.00),  # stem pre-collar
    (0.34, 1.06),  # collar rise
    (0.47, 1.13),  # collar ring (max)
    (0.33, 1.21),  # collar fall
    (0.30, 1.30),  # neck
    (0.52, 1.55),  # head flare
    (0.61, 1.80),  # head equator
    (0.56, 2.00),  # head upper
    (0.34, 2.15),  # head crown
    (0.00, 2.20),  # top center
]

SEGMENTS = 128  # radial resolution


def catmull_rom(p0, p1, p2, p3, t):
    t2 = t * t
    t3 = t2 * t
    r = 0.5 * (
        (2 * p1[0])
        + (-p0[0] + p2[0]) * t
        + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
        + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
    )
    y = 0.5 * (
        (2 * p1[1])
        + (-p0[1] + p2[1]) * t
        + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
        + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
    )
    return r, y


def build_profile(samples_per_seg=6):
    pts = []
    n = len(PROFILE)
    for i in range(n - 1):
        p0 = PROFILE[max(0, i - 1)]
        p1 = PROFILE[i]
        p2 = PROFILE[i + 1]
        p3 = PROFILE[min(n - 1, i + 2)]
        for s in range(samples_per_seg):
            t = s / samples_per_seg
            pts.append(catmull_rom(p0, p1, p2, p3, t))
    pts.append(PROFILE[-1])
    return pts


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
        "~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/assets/green_pawn.obj"
    )
    prof = build_profile()
    rings = []
    for (r, y) in prof:
        ring = []
        for j in range(SEGMENTS):
            a = 2 * math.pi * j / SEGMENTS
            x = r * math.cos(a)
            z = r * math.sin(a)
            ring.append((x, y, z))
        rings.append(ring)

    verts = []
    for ring in rings:
        verts.extend(ring)

    def vid(ri, ci):
        return ri * SEGMENTS + ci + 1  # OBJ is 1-indexed

    faces = []
    nr = len(rings)
    for ri in range(nr - 1):
        for ci in range(SEGMENTS):
            cnext = (ci + 1) % SEGMENTS
            a = vid(ri, ci)
            b = vid(ri, cnext)
            c = vid(ri + 1, cnext)
            d = vid(ri + 1, ci)
            if ri == 0:
                # bottom cap: triangle fan to first ring (vertex 1 is axis point)
                faces.append((1, b, c))
            elif ri == nr - 2:
                # top cap: triangle fan from last ring to apex (last vertex)
                apex = nr * SEGMENTS
                faces.append((a, b, apex))
            else:
                faces.append((a, b, c))
                faces.append((a, c, d))

    lines = ["# chess pawn, lathed surface of revolution", "o pawn", "usemtl pawn"]
    for (x, y, z) in verts:
        lines.append(f"v {x:.5f} {y:.5f} {z:.5f}")
    lines.append("g pawn")
    for f in faces:
        lines.append("f " + " ".join(str(i) for i in f))
    text = "\n".join(lines) + "\n"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        fh.write(text)
    print(f"wrote {out}  verts={len(verts)} faces={len(faces)}")


if __name__ == "__main__":
    main()
