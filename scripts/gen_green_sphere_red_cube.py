import math, os

ROOT = "/Users/craig/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP"
asset_dir = os.path.join(ROOT, "assets")
os.makedirs(asset_dir, exist_ok=True)

obj_path = os.path.join(asset_dir, "green_sphere_red_cube.obj")
mtl_path = os.path.join(asset_dir, "green_sphere_red_cube.mtl")

# ---- MTL ----
mtl = """# green sphere upon red cube
newmtl red_cube
Kd 0.85 0.10 0.10
Ks 0.18 0.18 0.18
Ns 40
newmtl green_sphere
Kd 0.10 0.80 0.20
Ks 0.30 0.30 0.30
Ns 60
"""
with open(mtl_path, "w") as f:
    f.write(mtl)

verts = []
norms = []
faces = []

def add_vertex(x, y, z, nx, ny, nz):
    verts.append((x, y, z))
    norms.append((nx, ny, nz))
    return len(verts) - 1

def emit_quad(idxs, group):
    faces.append((group, [idxs[0], idxs[1], idxs[2]]))
    faces.append((group, [idxs[0], idxs[2], idxs[3]]))

# ---- Cube centered at origin, half-extent 1 (y from -1 to 1) ----
h = 1.0
cube_faces = [
    ((h, -h, -h), (h, h, -h), (h, h, h), (h, -h, h), (1, 0, 0)),
    ((-h, -h, h), (-h, h, h), (-h, h, -h), (-h, -h, -h), (-1, 0, 0)),
    ((-h, h, -h), (-h, h, h), (h, h, h), (h, h, -h), (0, 1, 0)),
    ((-h, -h, h), (-h, -h, -h), (h, -h, -h), (h, -h, h), (0, -1, 0)),
    ((-h, -h, h), (h, -h, h), (h, h, h), (-h, h, h), (0, 0, 1)),
    ((h, -h, -h), (-h, -h, -h), (-h, h, -h), (h, h, -h), (0, 0, -1)),
]
for c0, c1, c2, c3, n in cube_faces:
    i0 = add_vertex(*c0, *n); i1 = add_vertex(*c1, *n); i2 = add_vertex(*c2, *n); i3 = add_vertex(*c3, *n)
    emit_quad([i0, i1, i2, i3], "red_cube")

# ---- Sphere resting on cube top ----
r = 1.1
cy = h + r
stacks = 32
slices = 48
grid = [[None] * (slices + 1) for _ in range(stacks + 1)]
for i in range(stacks + 1):
    theta = math.pi * i / stacks
    for j in range(slices + 1):
        phi = 2 * math.pi * j / slices
        x = r * math.sin(theta) * math.cos(phi)
        y = r * math.cos(theta)
        z = r * math.sin(theta) * math.sin(phi)
        nx, ny, nz = x / r, y / r, z / r
        grid[i][j] = add_vertex(x, y + cy, z, nx, ny, nz)
for i in range(stacks):
    for j in range(slices):
        a = grid[i][j]; b = grid[i + 1][j]; c = grid[i + 1][j + 1]; d = grid[i][j + 1]
        faces.append(("green_sphere", [a, b, c]))
        faces.append(("green_sphere", [a, c, d]))

lines = []
lines.append("# green sphere upon red cube")
lines.append(f"mtllib {os.path.basename(mtl_path)}")
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

with open(obj_path, "w") as f:
    f.write("\n".join(lines) + "\n")

print("OBJ verts:", len(verts), "norms:", len(norms), "faces(tri):", len(faces))
print("OBJ size bytes:", os.path.getsize(obj_path))
print("MTL size bytes:", os.path.getsize(mtl_path))
print("OBJ path:", obj_path)
print("MTL path:", mtl_path)
