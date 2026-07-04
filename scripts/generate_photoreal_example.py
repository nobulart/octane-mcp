from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "examples" / "recipes" / "photoreal-product-studio"


def add_vertex(vertices: list[tuple[float, float, float]], p: tuple[float, float, float]) -> int:
    vertices.append(p)
    return len(vertices)


def add_box(vertices: list[tuple[float, float, float]], faces: list[tuple[str, list[int]]], center, size, mat: str) -> None:
    cx, cy, cz = center
    sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
    pts = [
        (cx - sx, cy - sy, cz - sz), (cx + sx, cy - sy, cz - sz),
        (cx + sx, cy + sy, cz - sz), (cx - sx, cy + sy, cz - sz),
        (cx - sx, cy - sy, cz + sz), (cx + sx, cy - sy, cz + sz),
        (cx + sx, cy + sy, cz + sz), (cx - sx, cy + sy, cz + sz),
    ]
    ids = [add_vertex(vertices, p) for p in pts]
    for face in ([0, 1, 2, 3], [4, 7, 6, 5], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [4, 0, 3, 7]):
        faces.append((mat, [ids[i] for i in face]))


def add_uv_sphere(vertices: list[tuple[float, float, float]], faces: list[tuple[str, list[int]]], center, radius: float, mat: str, rings: int = 18, segments: int = 36) -> None:
    cx, cy, cz = center
    grid: list[list[int]] = []
    for r in range(rings + 1):
        v = math.pi * r / rings
        row = []
        for s in range(segments):
            u = 2 * math.pi * s / segments
            row.append(add_vertex(vertices, (
                cx + radius * math.sin(v) * math.cos(u),
                cy + radius * math.sin(v) * math.sin(u),
                cz + radius * math.cos(v),
            )))
        grid.append(row)
    for r in range(rings):
        for s in range(segments):
            faces.append((mat, [grid[r][s], grid[r][(s + 1) % segments], grid[r + 1][(s + 1) % segments], grid[r + 1][s]]))


def add_curved_backdrop(vertices: list[tuple[float, float, float]], faces: list[tuple[str, list[int]]]) -> None:
    # A simple cyclorama-like backdrop: floor bends upward into a rear wall.
    rows = []
    width = 6.0
    segments_x = 8
    segments_y = 16
    for y_i in range(segments_y + 1):
        t = y_i / segments_y
        y = -2.4 + t * 5.2
        if t < 0.55:
            z = -0.04
        else:
            bend = (t - 0.55) / 0.45
            z = -0.04 + 3.2 * (1 - math.cos(bend * math.pi / 2))
            y = 0.45 + 1.2 * math.sin(bend * math.pi / 2)
        row = []
        for x_i in range(segments_x + 1):
            x = -width / 2 + width * x_i / segments_x
            row.append(add_vertex(vertices, (x, y, z)))
        rows.append(row)
    for y_i in range(segments_y):
        for x_i in range(segments_x):
            faces.append(("mat_charcoal", [rows[y_i][x_i], rows[y_i][x_i + 1], rows[y_i + 1][x_i + 1], rows[y_i + 1][x_i]]))


def build_scene() -> tuple[str, str]:
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[str, list[int]]] = []
    add_curved_backdrop(vertices, faces)
    add_box(vertices, faces, (0, -0.35, 0.18), (2.9, 1.45, 0.36), "mat_pedestal")
    add_box(vertices, faces, (-0.55, -0.55, 0.86), (0.78, 0.78, 0.78), "mat_cyan_glass")
    add_uv_sphere(vertices, faces, (0.62, -0.48, 0.92), 0.44, "mat_brushed_gold")
    add_box(vertices, faces, (-1.95, -0.05, 1.85), (0.06, 0.06, 1.25), "mat_light_panel")
    add_box(vertices, faces, (1.95, -0.05, 1.75), (0.06, 0.06, 1.05), "mat_light_panel")

    obj_lines = ["# Photoreal product studio target scene for OctaneX MCP", "mtllib scene.mtl", "o photoreal_product_studio"]
    for x, y, z in vertices:
        obj_lines.append(f"v {x:.5f} {y:.5f} {z:.5f}")
    current = None
    for mat, idxs in faces:
        if mat != current:
            obj_lines.append(f"usemtl {mat}")
            current = mat
        obj_lines.append("f " + " ".join(str(i) for i in idxs))

    mtl = """# Material intent for Octane/PBR translation
newmtl mat_charcoal
Kd 0.025 0.028 0.035
Ks 0.2 0.2 0.2
Ns 80

newmtl mat_pedestal
Kd 0.12 0.12 0.13
Ks 0.35 0.35 0.35
Ns 120

newmtl mat_cyan_glass
Kd 0.05 0.75 1.0
Ks 0.9 0.95 1.0
Ns 500
d 0.42

newmtl mat_brushed_gold
Kd 1.0 0.62 0.16
Ks 1.0 0.84 0.42
Ns 360

newmtl mat_light_panel
Kd 1.0 0.96 0.86
Ks 0.0 0.0 0.0
Ns 10
"""
    return "\n".join(obj_lines) + "\n", mtl


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    obj, mtl = build_scene()
    (OUT / "scene.obj").write_text(obj, encoding="utf-8")
    (OUT / "scene.mtl").write_text(mtl, encoding="utf-8")
    scene = {
        "slug": "photoreal-product-studio",
        "title": "Photoreal Product Studio",
        "category": "Photoreal/PBR rendering",
        "purpose": "Demonstrate a high-quality product-rendering target scene with glass, metal, softboxes, pedestal, and cyclorama backdrop.",
        "preview_note": "photoreal-preview.png is a generated target/reference render, not a verified Octane output. Re-render the OBJ/MTL scene in Octane X for native validation.",
        "camera": {"position": [2.6, -4.2, 2.0], "target": [0.05, -0.35, 0.85], "fov": 38},
        "lighting": {"preset": "soft_studio", "intent": "large softboxes left/right, dark studio, glossy reflections, shallow depth-of-field"},
        "materials": {
            "mat_cyan_glass": {"kind": "specular/glass", "color": [0.05, 0.75, 1.0], "transmission": 0.7, "roughness": 0.03, "ior": 1.45},
            "mat_brushed_gold": {"kind": "metallic", "color": [1.0, 0.62, 0.16], "metallic": 1.0, "roughness": 0.18},
            "mat_pedestal": {"kind": "matte", "color": [0.12, 0.12, 0.13], "roughness": 0.55},
            "mat_charcoal": {"kind": "matte backdrop", "color": [0.025, 0.028, 0.035], "roughness": 0.7}
        },
        "commands": [
            {"op": "import_geometry", "payload": {"path": "examples/recipes/photoreal-product-studio/scene.obj", "format": "obj", "name": "photoreal-product-studio"}},
            {"op": "set_camera", "payload": {"position": [2.6, -4.2, 2.0], "target": [0.05, -0.35, 0.85], "fov": 38}},
            {"op": "set_lighting", "payload": {"preset": "soft_studio"}},
            {"op": "start_render", "payload": {"samples": 512, "width": 1280, "height": 720}},
            {"op": "save_preview", "payload": {"path": "examples/recipes/photoreal-product-studio/octane-preview.png", "width": 1280, "height": 720}}
        ]
    }
    (OUT / "scene.json").write_text(json.dumps(scene, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(OUT), "files": ["scene.obj", "scene.mtl", "scene.json"]}, indent=2))


if __name__ == "__main__":
    main()
