from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "examples" / "recipes" / "saturn-moons-space"

Point3 = tuple[float, float, float]
Face = tuple[str, list[int]]


def add_vertex(vertices: list[Point3], p: Point3) -> int:
    vertices.append(p)
    return len(vertices)


def add_uv_sphere(
    vertices: list[Point3],
    faces: list[Face],
    center: Point3,
    radius: float,
    rings: int,
    segments: int,
    material_for_cell,
    squash: tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> None:
    cx, cy, cz = center
    grid: list[list[int]] = []
    for r in range(rings + 1):
        v_angle = math.pi * r / rings
        lat = math.pi / 2 - v_angle
        row = []
        for s in range(segments):
            lon = 2 * math.pi * s / segments - math.pi
            x = cx + radius * math.sin(v_angle) * math.cos(lon) * squash[0]
            y = cy + radius * math.sin(v_angle) * math.sin(lon) * squash[1]
            z = cz + radius * math.cos(v_angle) * squash[2]
            row.append(add_vertex(vertices, (x, y, z)))
        grid.append(row)
    for r in range(rings):
        lat = math.pi / 2 - math.pi * (r + 0.5) / rings
        for s in range(segments):
            lon = 2 * math.pi * (s + 0.5) / segments - math.pi
            mat = material_for_cell(lon, lat, r, s)
            faces.append((mat, [grid[r][s], grid[r][(s + 1) % segments], grid[r + 1][(s + 1) % segments], grid[r + 1][s]]))


def saturn_band_material(_lon: float, lat: float, _r: int, _s: int) -> str:
    band = int((lat + math.pi / 2) / math.pi * 11)
    if band in {1, 8}:
        return "mat_saturn_gold"
    if band in {3, 5, 7}:
        return "mat_saturn_cream"
    if band in {4, 6}:
        return "mat_saturn_taupe"
    return "mat_saturn_sand"


def moon_material(name: str):
    return lambda *_: name


def add_ring(
    vertices: list[Point3],
    faces: list[Face],
    inner: float,
    outer: float,
    segments: int,
    mat: str,
    z_offset: float = 0.0,
    tilt_x: float = math.radians(8),
) -> None:
    # Geometry is generated as a tilted annular strip around Saturn. Camera angle
    # provides the large visible ring tilt in the checked-in target preview.
    inner_ids: list[int] = []
    outer_ids: list[int] = []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        for radius, ids in ((inner, inner_ids), (outer, outer_ids)):
            x = radius * math.cos(a)
            y0 = radius * math.sin(a)
            y = y0 * math.cos(tilt_x) - z_offset * math.sin(tilt_x)
            z = y0 * math.sin(tilt_x) + z_offset * math.cos(tilt_x)
            ids.append(add_vertex(vertices, (x, y, z)))
    for i in range(segments):
        faces.append((mat, [inner_ids[i], inner_ids[(i + 1) % segments], outer_ids[(i + 1) % segments], outer_ids[i]]))


def build_scene() -> tuple[str, str]:
    vertices: list[Point3] = []
    faces: list[Face] = []

    add_uv_sphere(vertices, faces, (0.0, 0.0, 0.0), 1.0, 38, 96, saturn_band_material, squash=(1.08, 1.08, 0.86))
    add_ring(vertices, faces, 1.32, 1.62, 160, "mat_ring_inner", z_offset=0.002)
    add_ring(vertices, faces, 1.70, 2.05, 176, "mat_ring_middle", z_offset=0.004)
    add_ring(vertices, faces, 2.13, 2.50, 192, "mat_ring_outer", z_offset=0.006)
    add_ring(vertices, faces, 1.635, 1.685, 160, "mat_cassini_gap", z_offset=0.008)

    moons = [
        ("mat_titan", (2.85, -0.62, 0.34), 0.115, 16, 24),
        ("mat_icy_moon", (-2.35, 0.92, -0.18), 0.070, 12, 18),
        ("mat_gray_moon", (1.35, 1.72, 0.62), 0.052, 12, 18),
        ("mat_icy_moon", (-1.62, -1.58, 0.46), 0.045, 10, 16),
        ("mat_gray_moon", (2.28, 1.08, -0.28), 0.038, 10, 16),
    ]
    for mat, center, radius, rings, segments in moons:
        add_uv_sphere(vertices, faces, center, radius, rings, segments, moon_material(mat))

    obj_lines = ["# Saturn and moons space target scene for OctaneX MCP", "mtllib scene.mtl", "o saturn_moons_space"]
    for x, y, z in vertices:
        obj_lines.append(f"v {x:.5f} {y:.5f} {z:.5f}")
    current = None
    for mat, idxs in faces:
        if mat != current:
            obj_lines.append(f"usemtl {mat}")
            current = mat
        obj_lines.append("f " + " ".join(str(i) for i in idxs))

    mtl = """# Material intent for Octane/PBR translation
newmtl mat_saturn_sand
Kd 0.760 0.570 0.330
Ks 0.20 0.16 0.10
Ns 100

newmtl mat_saturn_cream
Kd 0.950 0.820 0.560
Ks 0.22 0.18 0.12
Ns 120

newmtl mat_saturn_gold
Kd 0.850 0.610 0.260
Ks 0.28 0.20 0.12
Ns 140

newmtl mat_saturn_taupe
Kd 0.520 0.390 0.250
Ks 0.16 0.12 0.08
Ns 80

newmtl mat_ring_inner
Kd 0.820 0.720 0.540
Ks 0.38 0.34 0.28
Ns 180
d 0.78

newmtl mat_ring_middle
Kd 0.690 0.610 0.500
Ks 0.30 0.28 0.24
Ns 140
d 0.70

newmtl mat_ring_outer
Kd 0.560 0.520 0.470
Ks 0.22 0.22 0.20
Ns 100
d 0.58

newmtl mat_cassini_gap
Kd 0.015 0.012 0.010
Ks 0.00 0.00 0.00
Ns 5
d 0.30

newmtl mat_titan
Kd 0.720 0.500 0.260
Ks 0.18 0.14 0.08
Ns 80

newmtl mat_icy_moon
Kd 0.740 0.800 0.880
Ks 0.30 0.34 0.40
Ns 160

newmtl mat_gray_moon
Kd 0.430 0.420 0.400
Ks 0.16 0.16 0.15
Ns 70
"""
    return "\n".join(obj_lines) + "\n", mtl


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    obj, mtl = build_scene()
    (OUT / "scene.obj").write_text(obj, encoding="utf-8")
    (OUT / "scene.mtl").write_text(mtl, encoding="utf-8")
    scene = {
        "slug": "saturn-moons-space",
        "title": "Saturn and Moons in Space",
        "category": "Photoreal/PBR space rendering",
        "purpose": "Demonstrate a high-quality Saturn target with oblate banded planet geometry, layered rings, Cassini division cue, moons, and cinematic space lighting.",
        "preview_note": "photoreal-preview.png is a generated target/reference render, not a verified native Octane output. Re-render scene.obj/scene.mtl in Octane X for native validation.",
        "camera": {"position": [0.35, -4.4, 1.25], "target": [0.0, 0.0, 0.05], "fov": 36},
        "lighting": {"preset": "space_sun", "intent": "hard sunlight from upper-left/front, black star field background, ring shadows and subtle rim lighting"},
        "materials": {
            "mat_saturn_sand": {"kind": "matte gas band", "color": [0.76, 0.57, 0.33], "roughness": 0.62},
            "mat_saturn_cream": {"kind": "matte bright gas band", "color": [0.95, 0.82, 0.56], "roughness": 0.58},
            "mat_saturn_gold": {"kind": "warm gas band", "color": [0.85, 0.61, 0.26], "roughness": 0.55},
            "mat_saturn_taupe": {"kind": "dark gas band", "color": [0.52, 0.39, 0.25], "roughness": 0.66},
            "mat_ring_inner": {"kind": "translucent dusty ice ring", "color": [0.82, 0.72, 0.54], "opacity": 0.78, "roughness": 0.32},
            "mat_ring_middle": {"kind": "translucent dusty ice ring", "color": [0.69, 0.61, 0.50], "opacity": 0.70, "roughness": 0.38},
            "mat_ring_outer": {"kind": "faint outer ring", "color": [0.56, 0.52, 0.47], "opacity": 0.58, "roughness": 0.44},
            "mat_cassini_gap": {"kind": "dark Cassini division cue", "color": [0.015, 0.012, 0.010], "opacity": 0.30},
            "mat_titan": {"kind": "large hazy moon", "color": [0.72, 0.50, 0.26], "roughness": 0.74},
            "mat_icy_moon": {"kind": "icy moon", "color": [0.74, 0.80, 0.88], "roughness": 0.42},
            "mat_gray_moon": {"kind": "rocky moon", "color": [0.43, 0.42, 0.40], "roughness": 0.70}
        },
        "quality_checklist": [
            "Target/reference image shows a recognizable Saturn with tilted rings, Cassini division, moons, and black space background.",
            "Native Octane output must be saved as octane-preview.png before claiming native photoreal success.",
            "Saturn should read as slightly oblate with subtle horizontal color bands, not a perfect flat-colored sphere.",
            "Rings should be thin, layered, and partially translucent with a visible dark division cue.",
            "Moons should remain small scale references and not compete with the planet/rings silhouette."
        ],
        "commands": [
            {"op": "import_geometry", "payload": {"path": "examples/recipes/saturn-moons-space/scene.obj", "format": "obj", "name": "saturn-moons-space"}},
            {"op": "set_camera", "payload": {"position": [0.35, -4.4, 1.25], "target": [0.0, 0.0, 0.05], "fov": 36}},
            {"op": "set_lighting", "payload": {"preset": "space_sun"}},
            {"op": "start_render", "payload": {"samples": 768, "width": 1280, "height": 720}},
            {"op": "save_preview", "payload": {"path": "examples/recipes/saturn-moons-space/octane-preview.png", "width": 1280, "height": 720}}
        ]
    }
    (OUT / "scene.json").write_text(json.dumps(scene, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(OUT), "files": ["scene.obj", "scene.mtl", "scene.json"]}, indent=2))


if __name__ == "__main__":
    main()
