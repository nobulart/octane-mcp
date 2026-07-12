from __future__ import annotations

import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "examples" / "recipes" / "earth-moon-space"


def add_vertex(vertices, p):
    vertices.append(p)
    return len(vertices)


def uv_band_sphere(vertices, faces, center, radius, lat0, lat1, segments, material, squash=(1.0, 1.0, 1.0)):
    """Build a LATITUDE BAND of a sphere (contiguous faces) as one usemtl group."""
    cx, cy, cz = center
    rings = max(2, int(round((lat1 - lat0) / math.pi * 48)))
    grid = []
    for r in range(rings + 1):
        v_angle = math.pi * (lat0 + (lat1 - lat0) * r / rings)
        row = []
        for s in range(segments):
            lon = 2 * math.pi * s / segments - math.pi
            x = cx + radius * math.sin(v_angle) * math.cos(lon) * squash[0]
            y = cy + radius * math.sin(v_angle) * math.sin(lon) * squash[1]
            z = cz + radius * math.cos(v_angle) * squash[2]
            row.append(add_vertex(vertices, (x, y, z)))
        grid.append(row)
    for r in range(rings):
        for s in range(segments):
            s1 = (s + 1) % segments
            faces.append((material, [grid[r][s], grid[r][s1], grid[r + 1][s1], grid[r + 1][s]]))


def build_scene():
    vertices = []
    faces = []

    # Earth at origin (r=3): split into 4 contiguous latitude bands -> 4 groups.
    # Pole-to-pole so bands tile the sphere with no gaps.
    E = (0.0, 0.0, 0.0)
    earth_bands = [
        ("earth_ice", 0.0, 0.18),        # north polar cap
        ("earth_land", 0.18, 0.55),      # northern continents
        ("earth_shallow", 0.55, 0.72),   # southern shallow/coast
        ("earth_ocean", 0.72, 1.0),      # south ocean
    ]
    for name, a, b in earth_bands:
        uv_band_sphere(vertices, faces, E, 3.0, a, b, 192, name)

    # Moon at x=9 (r=0.8): 2 contiguous bands -> 2 groups.
    M = (9.0, 0.0, 0.0)
    moon_bands = [
        ("moon_maria", 0.0, 0.5),
        ("moon_highland", 0.5, 1.0),
    ]
    for name, a, b in moon_bands:
        uv_band_sphere(vertices, faces, M, 0.8, a, b, 144, name)

    obj_lines = ["# Earth-Moon space target scene (6 contiguous bands) for OctaneX MCP", "o earth_moon_space"]
    for x, y, z in vertices:
        obj_lines.append(f"v {x:.5f} {y:.5f} {z:.5f}")
    current = None
    for mat, idxs in faces:
        if mat != current:
            obj_lines.append(f"usemtl {mat}")
            current = mat
        obj_lines.append("f " + " ".join(str(i) for i in idxs))

    mtl = """# Material intent ONLY (colors applied via create_material + assign_material(group_index)).
newmtl earth_ocean
Kd 0.02 0.10 0.32
newmtl earth_shallow
Kd 0.04 0.30 0.52
newmtl earth_land
Kd 0.16 0.36 0.14
newmtl earth_ice
Kd 0.85 0.92 0.97
newmtl moon_maria
Kd 0.28 0.27 0.26
newmtl moon_highland
Kd 0.62 0.61 0.58
"""
    return "\n".join(obj_lines) + "\n", mtl


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    obj, mtl = build_scene()
    (OUT / "scene.obj").write_text(obj, encoding="utf-8")
    (OUT / "scene.mtl").write_text(mtl, encoding="utf-8")
    nv = sum(1 for l in obj.splitlines() if l.startswith("v "))
    nf = sum(1 for l in obj.splitlines() if l.startswith("f "))
    nusemtl = sum(1 for l in obj.splitlines() if l.startswith("usemtl "))
    # contiguous block count = number of distinct usemtl groups in order
    blocks = 0
    prev = None
    for l in obj.splitlines():
        if l.startswith("usemtl "):
            if l != prev:
                blocks += 1
                prev = l
    print(f"wrote {OUT/'scene.obj'} verts={nv} faces={nf} usemtl_changes={nusemtl} contiguous_blocks={blocks}")


if __name__ == "__main__":
    main()
