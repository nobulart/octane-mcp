#!/usr/bin/env python3
"""Generate a birthday-cake OBJ with a round board, two icing tiers, frosting
drips that hang over each rim, a candle, a teardrop flame, and rod-shaped rainbow
sprinkles.

Realism notes (v2):
  - The board is a round thin cylinder (a cake drum), not a square slab.
  - Drips are teardrop lobes: a sphere scaled tall and drooping below the rim so
    the overhang actually reads on screen.
  - Sprinkles are short rods (thin cylinders) lying on the icing at random tilts,
    the way real sprinkles sit, instead of little cubes.
  - The flame is a tall teardrop (scaled spheroid) in a hot orange.
  - Icing uses satin (higher roughness) rather than slick plastic.

Each part is a single ``usemtl`` group carrying its own material so the Octane
bridge can bind colors by 1-based ``group_index``. Faces are produced in LOCAL
1-indexed coordinates inside each primitive and then REBASED onto the running
global vertex offset by ``write_obj`` — without that rebasing every group after
the first collapses onto the early vertices (the bug v1 fixed).
"""
import json
import math
import os
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    "~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/assets/birthday_cake.obj"
)

RAD_SEG = 96
SPH_SEG = 40


def rotate_y(v, a):
    c, s = math.cos(a), math.sin(a)
    return (v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c)


def rotate_x(v, a):
    c, s = math.cos(a), math.sin(a)
    return (v[0], v[1] * c - v[2] * s, v[1] * s + v[2] * c)


def rotate_z(v, a):
    c, s = math.cos(a), math.sin(a)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c, v[2])


def transform_verts(verts, rotate=None, translate=(0, 0, 0)):
    out = []
    for v in verts:
        if rotate is not None:
            for fn, ang in rotate:
                v = fn(v, ang)
        out.append((v[0] + translate[0], v[1] + translate[1], v[2] + translate[2]))
    return out


def cylinder(r_top, r_bot, h, y0, seg=RAD_SEG):
    """Upright cylinder, world-space verts + LOCAL 1-indexed faces."""
    verts = []
    count = max(3, int(abs(r_top - r_bot) / 0.02) + 3)
    rings = []
    for i in range(count):
        t = i / (count - 1)
        r = r_bot + t * (r_top - r_bot)
        ring = []
        for j in range(seg):
            a = 2 * math.pi * j / seg
            ring.append((r * math.cos(a), y0 + t * h, r * math.sin(a)))
        rings.append(ring)
    for ring in rings:
        verts.extend(ring)
    bottom_c = len(verts)
    verts.append((0.0, y0, 0.0))
    top_c = len(verts)
    verts.append((0.0, y0 + h, 0.0))
    nr, nc = len(rings), seg
    faces = []
    for ri in range(nr - 1):
        for ci in range(nc):
            ci2 = (ci + 1) % nc
            a = ri * nc + ci + 1
            b = ri * nc + ci2 + 1
            c = (ri + 1) * nc + ci2 + 1
            d = (ri + 1) * nc + ci + 1
            faces.append((a, b, c))
            faces.append((a, c, d))
    a0 = 1
    for ci in range(nc):
        ci2 = (ci + 1) % nc
        faces.append((bottom_c + 1, a0 + ci, a0 + ci2))
    a0 = (nr - 1) * nc + 1
    for ci in range(nc):
        ci2 = (ci + 1) % nc
        faces.append((top_c + 1, a0 + ci2, a0 + ci))
    return verts, faces


def spheroid(cx, cy, cz, r, sx=1.0, sy=1.0, sz=1.0, seg=SPH_SEG):
    """Ellipsoid (teardrop when sy != sx). World verts + LOCAL faces."""
    verts = []
    for i in range(seg + 1):
        phi = math.pi * i / seg
        for j in range(seg):
            theta = 2 * math.pi * j / seg
            x = cx + r * sx * math.sin(phi) * math.cos(theta)
            z = cz + r * sz * math.sin(phi) * math.sin(theta)
            y = cy + r * sy * math.cos(phi)
            verts.append((x, y, z))
    nr, nc = seg + 1, seg
    faces = []
    for ri in range(nr - 1):
        for ci in range(nc):
            ci2 = (ci + 1) % nc
            a = ri * nc + ci + 1
            b = ri * nc + ci2 + 1
            c = (ri + 1) * nc + ci2 + 1
            d = (ri + 1) * nc + ci + 1
            faces.append((a, b, c))
            faces.append((a, c, d))
    return verts, faces


def rod(cx, cy, cz, r, length, tilt_x=0.0, tilt_z=0.0, seg=20):
    """A thin cylinder lying along Y, then tilted and translated -> a sprinkle."""
    half = length / 2.0
    verts = []
    rings = []
    for i in range(2):
        y = -half + i * length
        ring = []
        for j in range(seg):
            a = 2 * math.pi * j / seg
            ring.append((r * math.cos(a), y, r * math.sin(a)))
        rings.append(ring)
    for ring in rings:
        verts.extend(ring)
    bottom_c = len(verts)
    verts.append((0.0, -half, 0.0))
    top_c = len(verts)
    verts.append((0.0, half, 0.0))
    nc = seg
    faces = []
    for ci in range(nc):
        ci2 = (ci + 1) % nc
        a = ci + 1
        b = ci2 + 1
        c = nc + ci2 + 1
        d = nc + ci + 1
        faces.append((a, b, c))
        faces.append((a, c, d))
        faces.append((bottom_c + 1, a, b))
        faces.append((top_c + 1, c, d))
    rotate = []
    if tilt_x:
        rotate.append((rotate_x, tilt_x))
    if tilt_z:
        rotate.append((rotate_z, tilt_z))
    verts = transform_verts(verts, rotate, (cx, cy, cz))
    return verts, faces


def main():
    groups = []  # (name, world_verts, local_faces)

    # --- round cake board (a cake drum) ---
    groups.append(("mat_plate", *cylinder(1.55, 1.55, 0.07, 0.0)))

    # --- two icing tiers (slight taper) ---
    groups.append(("mat_icing_lower", *cylinder(1.32, 1.24, 0.85, 0.07)))
    groups.append(("mat_icing_upper", *cylinder(0.93, 0.87, 0.75, 0.92)))

    # --- frosting drips hanging over each tier rim (teardrops drooping down) ---
    # Each drip: an ellipsoid scaled tall, positioned so its top sits at the rim
    # and it hangs ~0.18 below. Three color groups for visual variety.
    drip_specs = [
        ("mat_drip_a", 1.28, 0.92, 0.16, [0, 38, 70, 115, 152, 200, 250, 300, 340]),
        ("mat_drip_b", 1.28, 0.92, 0.14, [18, 58, 95, 135, 178, 225, 275, 318]),
        ("mat_drip_c", 0.90, 1.67, 0.15, [12, 50, 88, 130, 172, 220, 270, 312, 352]),
    ]
    for gname, radius, rim_y, droop, angs in drip_specs:
        allv, allf = [], []
        for k, deg in enumerate(angs):
            a = math.radians(deg)
            cx, cz = radius * math.cos(a), radius * math.sin(a)
            # teardrop: scaled sphere, drooping so bottom is rim_y - droop
            cy = rim_y - droop * 0.45
            sv, sf = spheroid(cx, cy, cz, 0.15, sx=0.85, sy=1.5, sz=0.85)
            off = len(allv)
            allv.extend(sv)
            for f in sf:
                allf.append(tuple(x + off for x in f))
        groups.append((gname, allv, allf))

    # --- candle on upper tier ---
    groups.append(("mat_candle", *cylinder(0.085, 0.075, 0.9, 1.67)))

    # --- flame: bright teardrop rising from the wick ---
    groups.append(("mat_flame", *spheroid(0, 2.57, 0, 0.13, sx=0.7, sy=1.7, sz=0.7)))

    # --- rainbow sprinkles: short rods scattered on the icing tops ---
    sprinkle_defs = [
        ("mat_sprinkle1", (1.0, 0.2, 0.2)),
        ("mat_sprinkle2", (0.2, 0.8, 0.2)),
        ("mat_sprinkle3", (0.2, 0.4, 1.0)),
        ("mat_sprinkle4", (1.0, 0.8, 0.1)),
        ("mat_sprinkle5", (1.0, 0.4, 0.7)),
        ("mat_sprinkle6", (0.0, 0.9, 0.9)),
        ("mat_sprinkle7", (1.0, 0.5, 0.0)),
        ("mat_sprinkle8", (0.6, 0.0, 0.8)),
    ]
    # positions: a few on the lower tier top, most on the upper tier top
    rng = 1234
    import random
    random.seed(rng)
    lower_pts = [(1.0 * math.cos(a), 0.94, 1.0 * math.sin(a))
                 for a in [0.3, 1.7, 3.0, 4.4, 5.5]]
    upper_pts = [(0.62 * math.cos(a), 1.69, 0.62 * math.sin(a))
                 for a in [0.2, 0.9, 1.6, 2.3, 3.0, 3.8, 4.5, 5.2, 5.9]]
    pts = lower_pts + upper_pts
    for idx, (name, _color) in enumerate(sprinkle_defs, start=1):
        x, y, z = pts[(idx - 1) % len(pts)]
        # tiny random offset so they don't stack
        x += random.uniform(-0.05, 0.05)
        z += random.uniform(-0.05, 0.05)
        tilt_x = random.uniform(-0.9, 0.9)
        tilt_z = random.uniform(-0.9, 0.9)
        groups.append((name, *rod(x, y, z, 0.022, 0.2, tilt_x, tilt_z)))

    # --- material colors (consumed by the command-pipeline / recipe authoring) ---
    materials = {
        "mat_plate": {"kind": "glossy", "color": [0.90, 0.90, 0.93], "roughness": 0.45},
        "mat_icing_lower": {"kind": "glossy", "color": [0.93, 0.52, 0.66], "roughness": 0.5},
        "mat_icing_upper": {"kind": "glossy", "color": [0.97, 0.63, 0.78], "roughness": 0.5},
        "mat_drip_a": {"kind": "glossy", "color": [0.55, 0.92, 0.78], "roughness": 0.4},
        "mat_drip_b": {"kind": "glossy", "color": [0.98, 0.86, 0.35], "roughness": 0.4},
        "mat_drip_c": {"kind": "glossy", "color": [0.45, 0.72, 0.96], "roughness": 0.4},
        "mat_candle": {"kind": "diffuse", "color": [0.96, 0.96, 0.92]},
        # brighter, hotter orange for the flame core
        "mat_flame": {"kind": "glossy", "color": [1.0, 0.6, 0.12], "roughness": 0.15},
    }
    for i in range(1, 9):
        materials[f"mat_sprinkle{i}"] = {
            "kind": "glossy", "color": list(sprinkle_defs[i - 1][1]), "roughness": 0.45
        }

    # --- write combined OBJ with global rebasing ---
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    lines = ["# birthday cake OBJ (combined, multi-group) v2"]
    for name, verts, faces in groups:
        lines.append(f"o {name}")
        lines.append(f"usemtl {name}")
        lines.append(f"g {name}")
        vstart = sum(1 for l in lines if l.startswith("v ")) + 1
        lines.extend(f"v {x:.5f} {y:.5f} {z:.5f}" for (x, y, z) in verts)
        base = vstart - 1
        for f in faces:
            lines.append("f " + " ".join(str(base + x) for x in f))
    with open(OUT, "w") as fh:
        fh.write("\n".join(lines) + "\n")

    mat_json = os.path.join(os.path.dirname(OUT), "birthday_cake.materials.json")
    with open(mat_json, "w") as fh:
        json.dump(materials, fh, indent=2)

    print(f"wrote {OUT} ({len(groups)} groups, {sum(len(v) for _, v, _ in groups)} verts)")


if __name__ == "__main__":
    main()
