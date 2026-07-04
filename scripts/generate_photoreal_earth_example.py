from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "examples" / "recipes" / "photoreal-earth-space"

Point3 = tuple[float, float, float]
Face = tuple[str, list[int]]


def add_vertex(vertices: list[Point3], p: Point3) -> int:
    vertices.append(p)
    return len(vertices)


def land_score(lon: float, lat: float) -> float:
    # Procedural continent-like masks. This is intentionally lightweight and
    # deterministic; native Octane quality should use a real Earth texture/HDRI.
    def blob(lon0: float, lat0: float, sx: float, sy: float, weight: float) -> float:
        dlon = math.atan2(math.sin(lon - lon0), math.cos(lon - lon0))
        dlat = lat - lat0
        return weight * math.exp(-((dlon / sx) ** 2 + (dlat / sy) ** 2))

    return (
        blob(-2.2, 0.55, 0.50, 0.55, 1.25)  # North America
        + blob(-1.2, -0.35, 0.38, 0.75, 1.05)  # South America
        + blob(0.15, 0.15, 0.36, 0.38, 0.95)  # Africa
        + blob(0.85, 0.55, 0.62, 0.48, 1.2)  # Europe/Asia
        + blob(1.9, -0.45, 0.35, 0.28, 0.95)  # Australia
        + blob(0.0, -1.2, 2.8, 0.22, 0.55)  # Antarctica edge
        + 0.18 * math.sin(5 * lon + 2.3 * math.sin(3 * lat))
    )


def add_uv_sphere(
    vertices: list[Point3],
    faces: list[Face],
    radius: float,
    rings: int,
    segments: int,
    material_for_cell,
    squash: tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> None:
    grid: list[list[int]] = []
    for r in range(rings + 1):
        v_angle = math.pi * r / rings
        lat = math.pi / 2 - v_angle
        row = []
        for s in range(segments):
            lon = 2 * math.pi * s / segments - math.pi
            x = radius * math.sin(v_angle) * math.cos(lon) * squash[0]
            y = radius * math.sin(v_angle) * math.sin(lon) * squash[1]
            z = radius * math.cos(v_angle) * squash[2]
            row.append(add_vertex(vertices, (x, y, z)))
        grid.append(row)
    for r in range(rings):
        lat = math.pi / 2 - math.pi * (r + 0.5) / rings
        for s in range(segments):
            lon = 2 * math.pi * (s + 0.5) / segments - math.pi
            mat = material_for_cell(lon, lat, r, s)
            faces.append((mat, [grid[r][s], grid[r][(s + 1) % segments], grid[r + 1][(s + 1) % segments], grid[r + 1][s]]))


def earth_material(lon: float, lat: float, _r: int, _s: int) -> str:
    score = land_score(lon, lat)
    if abs(lat) > 1.18 and score > 0.32:
        return "mat_polar_ice"
    if score > 0.55:
        return "mat_land"
    if score > 0.40:
        return "mat_shallow_water"
    return "mat_ocean"


def cloud_material(lon: float, lat: float, _r: int, _s: int) -> str:
    band = abs(math.sin(5.0 * lat + 1.8 * math.sin(2 * lon)))
    spiral = abs(math.sin(3.5 * lon + 1.4 * math.cos(4 * lat)))
    if band > 0.82 or (0.55 < spiral < 0.70 and abs(lat) < 0.9):
        return "mat_cloud"
    return "mat_cloud_faint"


def build_scene() -> tuple[str, str]:
    vertices: list[Point3] = []
    faces: list[Face] = []
    add_uv_sphere(vertices, faces, 1.0, rings=44, segments=88, material_for_cell=earth_material)
    add_uv_sphere(vertices, faces, 1.018, rings=32, segments=64, material_for_cell=cloud_material)
    add_uv_sphere(vertices, faces, 1.055, rings=28, segments=56, material_for_cell=lambda *_: "mat_atmosphere")

    obj_lines = ["# Photoreal Earth in space target scene for OctaneX MCP", "mtllib scene.mtl", "o photoreal_earth_space"]
    for x, y, z in vertices:
        obj_lines.append(f"v {x:.5f} {y:.5f} {z:.5f}")
    current = None
    for mat, idxs in faces:
        if mat != current:
            obj_lines.append(f"usemtl {mat}")
            current = mat
        obj_lines.append("f " + " ".join(str(i) for i in idxs))

    mtl = """# Material intent for Octane/PBR translation
newmtl mat_ocean
Kd 0.015 0.110 0.330
Ks 0.45 0.62 0.82
Ns 420

newmtl mat_shallow_water
Kd 0.030 0.300 0.500
Ks 0.35 0.50 0.70
Ns 280

newmtl mat_land
Kd 0.170 0.360 0.140
Ks 0.08 0.08 0.06
Ns 80

newmtl mat_polar_ice
Kd 0.820 0.900 0.960
Ks 0.55 0.60 0.65
Ns 220

newmtl mat_cloud
Kd 0.920 0.950 1.000
Ks 0.30 0.32 0.35
Ns 160
d 0.72

newmtl mat_cloud_faint
Kd 0.700 0.760 0.850
Ks 0.15 0.18 0.22
Ns 80
d 0.18

newmtl mat_atmosphere
Kd 0.080 0.380 1.000
Ks 0.50 0.75 1.000
Ns 300
d 0.22
"""
    return "\n".join(obj_lines) + "\n", mtl


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    obj, mtl = build_scene()
    (OUT / "scene.obj").write_text(obj, encoding="utf-8")
    (OUT / "scene.mtl").write_text(mtl, encoding="utf-8")
    scene = {
        "slug": "photoreal-earth-space",
        "title": "Photoreal Earth in Space",
        "category": "Photoreal/PBR space rendering",
        "purpose": "Demonstrate a high-quality orbital Earth target with ocean/land materials, cloud shells, atmospheric rim glow, and space lighting.",
        "preview_note": "photoreal-preview.png is a generated target/reference render, not a verified native Octane output. Re-render scene.obj/scene.mtl in Octane X for native validation.",
        "camera": {"position": [0.15, -3.15, 1.05], "target": [0.0, 0.0, 0.05], "fov": 34},
        "lighting": {"preset": "space_sun", "intent": "hard distant sunlight from camera-left/front, deep black background, faint blue atmospheric rim"},
        "materials": {
            "mat_ocean": {"kind": "glossy ocean", "color": [0.015, 0.11, 0.33], "roughness": 0.08, "specular": 0.7},
            "mat_shallow_water": {"kind": "glossy shallow water", "color": [0.03, 0.30, 0.50], "roughness": 0.12},
            "mat_land": {"kind": "matte land", "color": [0.17, 0.36, 0.14], "roughness": 0.58},
            "mat_polar_ice": {"kind": "snow/ice", "color": [0.82, 0.90, 0.96], "roughness": 0.25},
            "mat_cloud": {"kind": "translucent cloud", "color": [0.92, 0.95, 1.0], "opacity": 0.72, "roughness": 0.45},
            "mat_cloud_faint": {"kind": "faint translucent cloud", "color": [0.70, 0.76, 0.85], "opacity": 0.18},
            "mat_atmosphere": {"kind": "thin blue transparent shell", "color": [0.08, 0.38, 1.0], "opacity": 0.22, "emission_hint": 0.25}
        },
        "quality_checklist": [
            "Target/reference image shows a recognizable Earth, cloud bands, atmosphere rim, and black space background.",
            "Native Octane output must be saved as octane-preview.png before claiming native photoreal success.",
            "Oceans should be glossy and darker than land; land should not read as flat neon texture.",
            "Cloud shell should remain visibly above the surface without hiding continents entirely.",
            "Atmosphere should read as a thin rim/glow, not a thick opaque shell."
        ],
        "commands": [
            {"op": "import_geometry", "payload": {"path": "examples/recipes/photoreal-earth-space/scene.obj", "format": "obj", "name": "photoreal-earth-space"}},
            {"op": "set_camera", "payload": {"position": [0.15, -3.15, 1.05], "target": [0.0, 0.0, 0.05], "fov": 34}},
            {"op": "set_lighting", "payload": {"preset": "space_sun"}},
            {"op": "start_render", "payload": {"samples": 768, "width": 1280, "height": 720}},
            {"op": "save_preview", "payload": {"path": "examples/recipes/photoreal-earth-space/octane-preview.png", "width": 1280, "height": 720}}
        ]
    }
    (OUT / "scene.json").write_text(json.dumps(scene, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(OUT), "files": ["scene.obj", "scene.mtl", "scene.json"]}, indent=2))


if __name__ == "__main__":
    main()
