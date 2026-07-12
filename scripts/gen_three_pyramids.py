"""Generate a three-pyramids OBJ (one combined mesh, three usemtl groups).

Three Egyptian-style square-base pyramids of differing size + color, seated on a
dark studio floor, arranged in a shallow arc. Face format uses explicit vertex
normals (f v//vn) which Octane honors for smooth/flat shading.
"""
import math
import os

ROOT = "/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP"
asset_dir = os.path.join(ROOT, "assets")
os.makedirs(asset_dir, exist_ok=True)

obj_path = os.path.join(asset_dir, "three_pyramids.obj")
mtl_path = os.path.join(asset_dir, "three_pyramids.mtl")

# Colors (RGB 0..1): warm gold, cool teal, amber-red
MTL = """# three pyramids
newmtl pyr_gold
Kd 0.85 0.62 0.20
Ks 0.25 0.25 0.25
Ns 45
newmtl pyr_teal
Kd 0.15 0.55 0.55
Ks 0.20 0.20 0.20
Ns 40
newmtl pyr_red
Kd 0.75 0.22 0.18
Ks 0.22 0.22 0.22
Ns 42
newmtl studio_floor
Kd 0.06 0.06 0.07
Ks 0.05 0.05 0.05
Ns 10
"""

verts: list[tuple[float, float, float]] = []
norms: list[tuple[float, float, float]] = []
faces: list[tuple[str, list[int]]] = []


def add_v(x, y, z, nx, ny, nz):
    verts.append((x, y, z))
    norms.append((nx, ny, nz))
    return len(verts) - 1


def pyramid(group, cx, cz, base, h, rot=0.0):
    """Square-base pyramid centered at (cx,cz) on y=0, apex at y=h."""
    # base corners (CCW from top view), rotated about Y
    cosr, sinr = math.cos(rot), math.sin(rot)
    corners = []
    for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        lx, lz = sx * base, sz * base
        x = cx + lx * cosr + lz * sinr
        z = cz - lx * sinr + lz * cosr
        corners.append((x, 0.0, z))
    apex = (cx, h, cz)
    # base normal down, side normals outward
    base_n = (0, -1, 0)
    # Triangle fan for the base (two tris)
    b0 = add_v(*corners[0], *base_n)
    b1 = add_v(*corners[1], *base_n)
    b2 = add_v(*corners[2], *base_n)
    b3 = add_v(*corners[3], *base_n)
    faces.append((group, [b0, b2, b1]))  # wound so normal points down
    faces.append((group, [b0, b3, b2]))
    # four side faces (apex + two base corners)
    a = add_v(*apex, *(0, 1, 0))  # apex normal up-ish placeholder; true per-face below
    for i in range(4):
        c0 = corners[i]
        c1 = corners[(i + 1) % 4]
        # outward normal for this face
        mx, mz = (c0[0] + c1[0]) / 2 - cx, (c0[2] + c1[2]) / 2 - cz
        nl = math.hypot(mx, mz) or 1.0
        e = (c1[0] - c0[0], 0.0, c1[2] - c0[2])
        el = math.hypot(e[0], e[2]) or 1.0
        ny = base / h  # slope: higher if steeper
        fn = (mx / nl, ny, mz / nl)
        fl = math.hypot(fn[0], fn[1], fn[2]) or 1.0
        fn = (fn[0] / fl, fn[1] / fl, fn[2] / fl)
        v0 = add_v(c0[0], c0[1], c0[2], *fn)
        v1 = add_v(c1[0], c1[1], c1[2], *fn)
        faces.append((group, [v0, a, v1]))


def floor(group, half=9.0):
    n = (0, 1, 0)
    y = -0.02
    c = [
        (-half, y, -half),
        (half, y, -half),
        (half, y, half),
        (-half, y, half),
    ]
    i0 = add_v(*c[0], *n)
    i1 = add_v(*c[1], *n)
    i2 = add_v(*c[2], *n)
    i3 = add_v(*c[3], *n)
    faces.append((group, [i0, i1, i2]))
    faces.append((group, [i0, i2, i3]))


# Three pyramids in a shallow arc, varying size + color
pyramid("pyr_gold", cx=-4.2, cz=-1.0, base=1.4, h=3.4, rot=0.18)
pyramid("pyr_teal", cx=0.0, cz=0.6, base=1.9, h=4.6, rot=-0.10)
pyramid("pyr_red", cx=4.4, cz=-0.8, base=1.15, h=2.7, rot=-0.22)
floor("studio_floor", half=7.0)

lines = ["# three pyramids on a dark studio floor", f"mtllib {os.path.basename(mtl_path)}"]
for (x, y, z) in verts:
    lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")
for (nx, ny, nz) in norms:
    lines.append(f"vn {nx:.6f} {ny:.6f} {nz:.6f}")
cur = None
for (group, tri) in faces:
    if group != cur:
        lines.append(f"usemtl {group}")
        cur = group
    fstr = " ".join(f"{v + 1}//{v + 1}" for v in tri)
    lines.append(f"f {fstr}")

with open(mtl_path, "w") as f:
    f.write(MTL)
with open(obj_path, "w") as f:
    f.write("\n".join(lines) + "\n")

print("OBJ verts:", len(verts), "norms:", len(norms), "faces(tri):", len(faces))
print("OBJ bytes:", os.path.getsize(obj_path), "MTL bytes:", os.path.getsize(mtl_path))
print("OBJ path:", obj_path)
