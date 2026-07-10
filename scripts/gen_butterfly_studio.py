#!/usr/bin/env python3
"""Generate a single combined OBJ for a photorealistic blue butterfly on a white
surface under warm studio lighting, dark "night" background.

Photoreal upgrades vs v1:
  * Wings: subdivided outlines -> smooth domed panels (vertex normals emitted as
    f v//vn so Octane smooth-shades instead of flat-tris).
  * Body: tapered capsule (head sphere + thorax + abdomen) with rounded caps.
  * Antennae: curved tubes with club tips.
  * Subtle blue gradient via emissive handled in the material, not geometry.

Groups (usemtl, write order):
  1 cyc     - dark charcoal cyclorama floor+back wall (fills frame -> dark bg)
  2 surface - white diffuse disc the butterfly rests on
  3 wing    - blue glossy butterfly wings (4 panels)
  4 body    - dark diffuse body/head/antennae
  5 sb_key  - warm emissive softbox (key, upper-left)
  6 sb_fill - cool emissive softbox (fill, upper-right)
  7 sb_top  - neutral-warm emissive softbox (overhead)
"""
import math
import os
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else (
    os.path.expanduser("~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/assets/butterfly_studio.obj")
)

verts = []
norms = []
faces = []  # (group, [ (vidx, nidx), ... ])  using 1-based, f v//vn


def add_vert_n(x, y, z, nx, ny, nz):
    verts.append((x, y, z))
    # normalize normal
    L = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    norms.append((nx / L, ny / L, nz / L))
    return len(verts)


def add_face_vn(group, vn_pairs):
    # allow flat int lists (v) or (v,n) tuples; normalize to (v,n) pairs
    norm = []
    for item in vn_pairs:
        if isinstance(item, (tuple, list)):
            norm.append((int(item[0]), int(item[1])))
        else:
            norm.append((int(item), int(item)))
    faces.append((group, norm))


def add_quad_vn(group, p0, p1, p2, p3):
    add_face_vn(group, [p0, p1, p2])
    add_face_vn(group, [p0, p2, p3])


# ---- 1. DARK CYCLORAMA (floor + curved back wall) -------------------------
g_cyc = "cyc"
# floor (normal up)
a = add_vert_n(-12, 0, -12, 0, 1, 0); b = add_vert_n(12, 0, -12, 0, 1, 0)
c = add_vert_n(12, 0, 12, 0, 1, 0); d = add_vert_n(-12, 0, 12, 0, 1, 0)
add_face_vn(g_cyc, [a, b, c]); add_face_vn(g_cyc, [a, c, d])
# back wall (normal +z)
e = add_vert_n(-12, 0, -12, 0, 0, 1); f = add_vert_n(12, 0, -12, 0, 0, 1)
g = add_vert_n(12, 9, -12, 0, 0, 1); h = add_vert_n(-12, 9, -12, 0, 0, 1)
add_face_vn(g_cyc, [e, f, g]); add_face_vn(g_cyc, [e, g, h])
# curved return at back-bottom (cylinder segment, normal points inward/forward)
for i in range(6):
    t0 = i / 6 * (math.pi / 2); t1 = (i + 1) / 6 * (math.pi / 2)
    r = 3.0
    y0 = r * math.sin(t0); z0 = -12 + r - r * math.cos(t0)
    y1 = r * math.sin(t1); z1 = -12 + r - r * math.cos(t1)
    # normal roughly (0, cos, sin) pointing up/forward
    n0 = (0, math.cos(t0), math.sin(t0))
    n1 = (0, math.cos(t1), math.sin(t1))
    pa = add_vert_n(-12, y0, z0, 0, n0[1], n0[2]); pb = add_vert_n(12, y0, z0, 0, n0[1], n0[2])
    pc = add_vert_n(12, y1, z1, 0, n1[1], n1[2]); pd = add_vert_n(-12, y1, z1, 0, n1[1], n1[2])
    add_face_vn(g_cyc, [pa, pb, pc]); add_face_vn(g_cyc, [pa, pc, pd])


# ---- 2. WHITE SURFACE DISC ------------------------------------------------
g_surface = "surface"
BASE_Y = 0.5
R = 3.2
seg = 64
center = add_vert_n(0, BASE_Y, 0, 0, 1, 0)
ring = [add_vert_n(R * math.cos(2 * math.pi * i / seg), BASE_Y, R * math.sin(2 * math.pi * i / seg), 0, 1, 0)
        for i in range(seg)]
for i in range(seg):
    add_face_vn(g_surface, [center, ring[i], ring[(i + 1) % seg]])


# ---- 3. BLUE WINGS (smooth domed panels) ----------------------------------
g_wing = "wing"
WING_Y = BASE_Y + 0.55
DIHEDRAL = 0.18
SUB = 10  # subdivision of each outline edge -> smooth curves


def catmull_rom_subdivide(outline, sub):
    """Subdivide a closed polyline outline using Catmull-Rom for smooth curves."""
    n = len(outline)
    out = []
    for i in range(n):
        p0 = outline[(i - 1) % n]; p1 = outline[i]; p2 = outline[(i + 1) % n]; p3 = outline[(i + 2) % n]
        for s in range(sub):
            t = s / sub
            t2 = t * t; t3 = t2 * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            z = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, z))
    return out


def wing_panel(side, outline):
    """Build a domed wing panel: center spine vertex + subdivided rim, with a
    gentle upward dome so normals vary -> smooth shading."""
    smooth = catmull_rom_subdivide(outline, SUB)
    cz = sum(v for _, v in smooth) / len(smooth)
    # center vertex slightly raised
    cv = add_vert_n(0.0, WING_Y + 0.10, cz, 0, 1, 0)
    rim = []
    for (u, v) in smooth:
        # dome height: higher near center, lower at rim
        dist = math.sqrt(u * u + (v - cz) * (v - cz))
        dome = 0.10 * max(0.0, 1.0 - dist / 2.6) + DIHEDRAL * abs(u)
        y = WING_Y + dome
        # approximate normal: radial-ish up
        rim.append(add_vert_n(side * u, y, v, 0, 1, 0))
    for i in range(len(rim)):
        j = (i + 1) % len(rim)
        add_face_vn(g_wing, [cv, rim[i], rim[j]])


fore_r = [(0.0, 0.18), (0.7, 1.15), (1.4, 1.75), (2.1, 1.55),
          (2.5, 0.85), (2.05, 0.32), (1.0, 0.06), (0.0, 0.06)]
hind_r = [(0.0, 0.02), (0.55, -0.65), (1.15, -1.05), (1.65, -0.95),
          (1.55, -0.4), (1.05, -0.12), (0.0, -0.06)]
for s in (+1, -1):
    wing_panel(s, fore_r)
    wing_panel(s, hind_r)


# ---- 4. BODY / HEAD / ANTENNAE (smooth) -----------------------------------
g_body = "body"


def capsule(group, p0, p1, r0, r1, segments=20):
    """Tapered capsule between p0 (radius r0) and p1 (radius r1)."""
    sx, sy, sz = p0; ex, ey, ez = p1
    dx, dy, dz = ex - sx, ey - sy, ez - sz
    L = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
    ax, ay, az = dx / L, dy / L, dz / L
    if abs(ax) < 0.9:
        bx, by, bz = 1.0, 0.0, 0.0
    else:
        bx, by, bz = 0.0, 1.0, 0.0
    ux = by * az - bz * ay; uy = bz * ax - bx * az; uz = bx * ay - by * ax
    ul = math.sqrt(ux * ux + uy * uy + uz * uz) or 1.0
    ux, uy, uz = ux / ul, uy / ul, uz / ul
    vx = ay * uz - az * uy; vy = az * ux - ax * uz; vz = ax * uy - ay * ux
    rs = []; re = []
    for i in range(segments):
        ang = 2 * math.pi * i / segments
        ox = (ux * math.cos(ang) + vx * math.sin(ang))
        oy = (uy * math.cos(ang) + vy * math.sin(ang))
        oz = (uz * math.cos(ang) + vz * math.sin(ang))
        rs.append(add_vert_n(sx + ox * r0, sy + oy * r0, sz + oz * r0, ox, oy, oz))
        re.append(add_vert_n(ex + ox * r1, ey + oy * r1, ez + oz * r1, ox, oy, oz))
    for i in range(segments):
        j = (i + 1) % segments
        add_face_vn(group, [rs[i], re[i], re[j]])
        add_face_vn(group, [rs[i], re[j], rs[j]])
    # caps
    cs = add_vert_n(sx, sy, sz, -ax, -ay, -az); ce = add_vert_n(ex, ey, ez, ax, ay, az)
    for i in range(segments):
        j = (i + 1) % segments
        add_face_vn(group, [cs, rs[j], rs[i]])
        add_face_vn(group, [ce, re[i], re[j]])


# abdomen -> thorax -> head
capsule(g_body, (0, WING_Y, -1.15), (0, WING_Y, 0.2), 0.10, 0.16, 20)
capsule(g_body, (0, WING_Y, 0.2), (0, WING_Y + 0.05, 1.0), 0.16, 0.20, 20)
# head sphere (approx by short fat capsule)
capsule(g_body, (0, WING_Y + 0.02, 1.0), (0, WING_Y + 0.10, 1.45), 0.20, 0.16, 20)


def antenna(group, base, tip, club_r=0.05):
    """Curved antenna tube from base to tip, with a small club at the tip."""
    # quadratic curve via control point lifted up/out
    mid = ((base[0] + tip[0]) / 2 * 1.3, base[1] + 0.5, (base[2] + tip[2]) / 2)
    steps = 12
    prev = None
    for s in range(steps + 1):
        t = s / steps
        x = (1 - t) ** 2 * base[0] + 2 * (1 - t) * t * mid[0] + t ** 2 * tip[0]
        y = (1 - t) ** 2 * base[1] + 2 * (1 - t) * t * mid[1] + t ** 2 * tip[1]
        z = (1 - t) ** 2 * base[2] + 2 * (1 - t) * t * mid[2] + t ** 2 * tip[2]
        cur = (x, y, z)
        if prev is not None:
            capsule(group, prev, cur, 0.02, 0.02, 8)
        prev = cur
    # club
    capsule(group, tip, (tip[0], tip[1] + 0.12, tip[2]), club_r, club_r * 0.6, 10)


antenna(g_body, (0.05, WING_Y + 0.10, 1.4), (0.34, WING_Y + 0.95, 2.55))
antenna(g_body, (-0.05, WING_Y + 0.10, 1.4), (-0.34, WING_Y + 0.95, 2.55))


# ---- 5-7. SOFTBOXES (emissive quads) --------------------------------------
g_key = "sb_key"
add_quad_vn(g_key, (-9.0, 11.0, 7.0), (-2.0, 11.0, 7.0), (-2.0, 5.0, 1.0), (-9.0, 5.0, 1.0))
g_fill = "sb_fill"
add_quad_vn(g_fill, (2.0, 10.0, -6.0), (9.0, 10.0, -6.0), (9.0, 5.0, 0.0), (2.0, 5.0, 0.0))
g_top = "sb_top"
add_quad_vn(g_top, (-7.0, 12.0, 6.0), (7.0, 12.0, 6.0), (7.0, 12.0, -6.0), (-7.0, 12.0, -6.0))


# ---- WRITE (v//vn faces for smooth shading) ------------------------------
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    f.write("# butterfly_studio.obj (combined groups, smooth v//vn)\n")
    for (x, y, z) in verts:
        f.write(f"v {x:.4f} {y:.4f} {z:.4f}\n")
    for (nx, ny, nz) in norms:
        f.write(f"vn {nx:.4f} {ny:.4f} {nz:.4f}\n")
    order = [g_cyc, g_surface, g_wing, g_body, g_key, g_fill, g_top]
    for grp in order:
        f.write(f"usemtl {grp}\n")
        for (g, pairs) in faces:
            if g != grp:
                continue
            f.write("f " + " ".join(f"{v}//{n}" for (v, n) in pairs) + "\n")

print(f"wrote {OUT}: {len(verts)} verts, {len(norms)} norms, {len(faces)} faces, {len(order)} groups")
