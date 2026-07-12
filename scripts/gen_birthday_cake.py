#!/usr/bin/env python3
"""Generate a birthday-cake OBJ with plate, two icing tiers, drips, a candle,
a flame, and rainbow sprinkles.

Each part is a single ``usemtl`` group carrying its own material so the Octane
bridge can bind colors by 1-based ``group_index``. Faces are produced in LOCAL
1-indexed coordinates inside each primitive and then REBASED onto the running
global vertex offset by ``write_obj`` — without that rebasing every group after
the first collapses onto the early vertices (the bug this rewrite fixes).
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


def cylinder(r_top, r_bot, h, y0, seg=RAD_SEG):
    """World-space verts + LOCAL 1-indexed faces for an axis-aligned cylinder."""
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
    # bottom cap fan (local verts)
    a0 = 1
    for ci in range(nc):
        ci2 = (ci + 1) % nc
        faces.append((bottom_c + 1, a0 + ci, a0 + ci2))
    # top cap fan
    a0 = (nr - 1) * nc + 1
    for ci in range(nc):
        ci2 = (ci + 1) % nc
        faces.append((top_c + 1, a0 + ci2, a0 + ci))
    return verts, faces


def sphere(cx, cy, cz, r, seg=SPH_SEG):
    """World-space verts + LOCAL 1-indexed faces for a UV sphere."""
    verts = []
    for i in range(seg + 1):
        phi = math.pi * i / seg
        for j in range(seg):
            theta = 2 * math.pi * j / seg
            x = cx + r * math.sin(phi) * math.cos(theta)
            z = cz + r * math.sin(phi) * math.sin(theta)
            y = cy + r * math.cos(phi)
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


def box(cx, cy, cz, w, h, d):
    """World-space verts + LOCAL 1-indexed faces for an axis-aligned box."""
    hw, hh, hd = w / 2, h / 2, d / 2
    verts = [
        (cx - hw, cy - hh, cz - hd), (cx + hw, cy - hh, cz - hd),
        (cx + hw, cy - hh, cz + hd), (cx - hw, cy - hh, cz + hd),
        (cx - hw, cy + hh, cz - hd), (cx + hw, cy + hh, cz - hd),
        (cx + hw, cy + hh, cz + hd), (cx - hw, cy + hh, cz + hd),
    ]
    faces = [
        (1, 2, 3), (1, 3, 4), (5, 7, 6), (5, 8, 7),
        (1, 4, 8), (1, 8, 5), (2, 6, 7), (2, 7, 3),
        (4, 3, 7), (4, 7, 8), (1, 5, 6), (1, 6, 2),
    ]
    return verts, faces


def main():
    groups = []  # (name, world_verts, local_faces)

    # --- plate ---
    groups.append(("mat_plate", *box(0, 0.06, 0, 2.8, 0.12, 2.8)))

    # --- two icing tiers ---
    groups.append(("mat_icing_lower", *cylinder(1.35, 1.25, 0.85, 0.12)))
    groups.append(("mat_icing_upper", *cylinder(0.95, 0.88, 0.75, 0.97)))

    # --- drips hanging over each tier rim, split across 3 color groups ---
    drip_specs = [
        ("mat_drip_a", 1.27, 0.86, [0, 60, 150, 240, 320]),
        ("mat_drip_b", 1.27, 0.84, [30, 100, 200, 280]),
        ("mat_drip_c", 0.90, 1.62, [15, 80, 160, 235, 300]),
    ]
    for gname, radius, y, angs in drip_specs:
        vparts = []  # collect verts/faces across the angles then merge
        allv, allf = [], []
        for k, deg in enumerate(angs):
            a = math.radians(deg)
            cx, cz = radius * math.cos(a), radius * math.sin(a)
            sv, sf = sphere(cx, y, cz, 0.14)
            # rebase this sphere's faces into the merged face list
            off = len(allv)
            allv.extend(sv)
            for f in sf:
                allf.append(tuple(x + off for x in f))
        groups.append((gname, allv, allf))

    # --- candle on upper tier ---
    groups.append(("mat_candle", *cylinder(0.09, 0.08, 0.9, 1.72)))

    # --- flame ---
    groups.append(("mat_flame", *sphere(0, 2.62, 0, 0.14)))

    # --- rainbow sprinkles scattered on the upper tier top ---
    colors = {
        "mat_sprinkle1": (1.0, 0.2, 0.2),
        "mat_sprinkle2": (0.2, 0.8, 0.2),
        "mat_sprinkle3": (0.2, 0.4, 1.0),
        "mat_sprinkle4": (1.0, 0.8, 0.1),
        "mat_sprinkle5": (1.0, 0.4, 0.7),
        "mat_sprinkle6": (0.0, 0.9, 0.9),
        "mat_sprinkle7": (1.0, 0.5, 0.0),
        "mat_sprinkle8": (0.6, 0.0, 0.8),
    }
    sprinkle_pts = [
        (0.05, 1.55, 0.0), (-0.2, 1.5, 0.1), (0.15, 1.6, -0.15), (-0.05, 1.52, -0.25),
        (0.0, 1.6, 0.25), (-0.3, 1.55, -0.05), (0.25, 1.5, 0.05), (-0.1, 1.58, -0.4),
    ]
    for idx, (x, y, z) in enumerate(sprinkle_pts, start=1):
        name = f"mat_sprinkle{idx}"
        groups.append((name, *box(x, y, z, 0.11, 0.07, 0.11)))

    # --- material colors (consumed by the command-pipeline / recipe authoring) ---
    materials = {
        "mat_plate": {"kind": "glossy", "color": [0.92, 0.92, 0.95], "roughness": 0.3},
        "mat_icing_lower": {"kind": "glossy", "color": [0.95, 0.55, 0.7], "roughness": 0.35},
        "mat_icing_upper": {"kind": "glossy", "color": [0.98, 0.65, 0.8], "roughness": 0.35},
        "mat_drip_a": {"kind": "glossy", "color": [0.5, 0.9, 0.75], "roughness": 0.3},
        "mat_drip_b": {"kind": "glossy", "color": [0.98, 0.85, 0.3], "roughness": 0.3},
        "mat_drip_c": {"kind": "glossy", "color": [0.4, 0.7, 0.95], "roughness": 0.3},
        "mat_candle": {"kind": "diffuse", "color": [0.95, 0.95, 0.9]},
        "mat_flame": {"kind": "glossy", "color": [1.0, 0.55, 0.1], "roughness": 0.2},
    }
    for i in range(1, 9):
        materials[f"mat_sprinkle{i}"] = {
            "kind": "glossy", "color": list(colors[f"mat_sprinkle{i}"]), "roughness": 0.4
        }

    # --- write combined OBJ with global rebasing ---
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    lines = ["# birthday cake OBJ (combined, multi-group)"]
    gidx = 0
    for name, verts, faces in groups:
        gidx += 1
        lines.append(f"o {name}")
        lines.append(f"usemtl {name}")
        lines.append(f"g {name}")
        off = len(lines)  # not used; we count v lines on the fly
        # write verts
        vstart = sum(1 for l in lines if l.startswith("v ")) + 1
        lines.extend(f"v {x:.5f} {y:.5f} {z:.5f}" for (x, y, z) in verts)
        base = vstart - 1  # global index of first local vertex
        for f in faces:
            lines.append("f " + " ".join(str(base + x) for x in f))
    with open(OUT, "w") as fh:
        fh.write("\n".join(lines) + "\n")

    # also write a companion materials json next to it for the pipeline
    mat_json = os.path.join(os.path.dirname(OUT), "birthday_cake.materials.json")
    with open(mat_json, "w") as fh:
        json.dump(materials, fh, indent=2)

    print(f"wrote {OUT} ({len(groups)} groups, {sum(len(v) for _,v,_ in groups)} verts)")


if __name__ == "__main__":
    main()
