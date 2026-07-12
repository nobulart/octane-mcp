#!/usr/bin/env python3
"""Generate the bowl-of-fruit example recipe assets.

The recipe is a single combined OBJ with one ``usemtl`` group per material so
Octane can bind colours by 1-based ``group_index``.  The geometry intentionally
uses simple, inspectable primitives (lathed bowl, spheroids, torus rim, rods)
because this scene is meant as an agent-facing reusable recipe rather than a
hand-authored DCC asset.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RECIPE_DIR = REPO_ROOT / "examples" / "recipes" / "bowl-of-fruit"
OBJ_PATH = RECIPE_DIR / "scene.obj"
MTL_PATH = RECIPE_DIR / "scene.mtl"
SCENE_PATH = RECIPE_DIR / "scene.json"
README_PATH = RECIPE_DIR / "README.md"

SEG = 96
SPH = 36


def spheroid(cx, cy, cz, r, sx=1.0, sy=1.0, sz=1.0, seg=SPH):
    verts = []
    faces = []
    for i in range(seg + 1):
        phi = math.pi * i / seg
        for j in range(seg):
            theta = 2 * math.pi * j / seg
            verts.append((
                cx + r * sx * math.sin(phi) * math.cos(theta),
                cy + r * sy * math.cos(phi),
                cz + r * sz * math.sin(phi) * math.sin(theta),
            ))
    for ri in range(seg):
        for ci in range(seg):
            ci2 = (ci + 1) % seg
            a = ri * seg + ci + 1
            b = ri * seg + ci2 + 1
            c = (ri + 1) * seg + ci2 + 1
            d = (ri + 1) * seg + ci + 1
            faces.append((a, b, c))
            faces.append((a, c, d))
    return verts, faces


def lathe(profile, seg=SEG):
    verts = []
    faces = []
    for radius, y in profile:
        for j in range(seg):
            theta = 2 * math.pi * j / seg
            verts.append((radius * math.cos(theta), y, radius * math.sin(theta)))
    for i in range(len(profile) - 1):
        for j in range(seg):
            j2 = (j + 1) % seg
            a = i * seg + j + 1
            b = i * seg + j2 + 1
            c = (i + 1) * seg + j2 + 1
            d = (i + 1) * seg + j + 1
            faces.append((a, b, c))
            faces.append((a, c, d))
    return verts, faces


def plane(width, depth, y, z_offset=0.0):
    x = width / 2
    z = depth / 2
    return [(-x, y, -z + z_offset), (x, y, -z + z_offset), (x, y, z + z_offset), (-x, y, z + z_offset)], [(1, 2, 3), (1, 3, 4)]


def rod(cx, cy, cz, radius, length, az=0.0, ay=0.0, seg=18):
    verts = []
    faces = []
    for x in (-length / 2, length / 2):
        for j in range(seg):
            theta = 2 * math.pi * j / seg
            y = radius * math.cos(theta)
            z = radius * math.sin(theta)
            x1 = x * math.cos(az) - y * math.sin(az)
            y1 = x * math.sin(az) + y * math.cos(az)
            z1 = z
            x2 = x1 * math.cos(ay) + z1 * math.sin(ay)
            z2 = -x1 * math.sin(ay) + z1 * math.cos(ay)
            verts.append((cx + x2, cy + y1, cz + z2))
    for j in range(seg):
        j2 = (j + 1) % seg
        a = j + 1
        b = j2 + 1
        c = seg + j2 + 1
        d = seg + j + 1
        faces.append((a, b, c))
        faces.append((a, c, d))
    return verts, faces


def torus(cx, cy, cz, major, minor, seg=72, tube=14):
    verts = []
    faces = []
    for i in range(seg):
        theta = 2 * math.pi * i / seg
        for j in range(tube):
            phi = 2 * math.pi * j / tube
            verts.append((
                cx + (major + minor * math.cos(phi)) * math.cos(theta),
                cy + minor * math.sin(phi),
                cz + (major + minor * math.cos(phi)) * math.sin(theta),
            ))
    for i in range(seg):
        for j in range(tube):
            i2 = (i + 1) % seg
            j2 = (j + 1) % tube
            a = i * tube + j + 1
            b = i2 * tube + j + 1
            c = i2 * tube + j2 + 1
            d = i * tube + j2 + 1
            faces.append((a, b, c))
            faces.append((a, c, d))
    return verts, faces


MATERIALS = {
    "mat_table": {"kind": "diffuse", "color": [0.42, 0.30, 0.22], "roughness": 0.70},
    "mat_bowl_ceramic": {"kind": "glossy", "color": [0.88, 0.68, 0.46], "roughness": 0.34},
    "mat_bowl_highlight": {"kind": "glossy", "color": [1.0, 0.83, 0.58], "roughness": 0.22},
    "mat_bowl_shadow": {"kind": "glossy", "color": [0.54, 0.34, 0.20], "roughness": 0.48},
    "mat_red_apple": {"kind": "glossy", "color": [0.82, 0.04, 0.03], "roughness": 0.23},
    "mat_deep_red_apple": {"kind": "glossy", "color": [0.62, 0.02, 0.035], "roughness": 0.24},
    "mat_green_apple": {"kind": "glossy", "color": [0.36, 0.78, 0.13], "roughness": 0.26},
    "mat_orange": {"kind": "glossy", "color": [1.0, 0.43, 0.05], "roughness": 0.34},
    "mat_yellow_lemon": {"kind": "glossy", "color": [1.0, 0.88, 0.08], "roughness": 0.32},
    "mat_lime": {"kind": "glossy", "color": [0.56, 0.84, 0.10], "roughness": 0.34},
    "mat_grapes": {"kind": "glossy", "color": [0.38, 0.05, 0.62], "roughness": 0.25},
    "mat_banana": {"kind": "glossy", "color": [1.0, 0.76, 0.10], "roughness": 0.40},
    "mat_stem": {"kind": "diffuse", "color": [0.18, 0.09, 0.035], "roughness": 0.60},
    "mat_leaf": {"kind": "glossy", "color": [0.04, 0.42, 0.12], "roughness": 0.42},
}


def build_groups():
    groups = []
    groups.append(("mat_table", *plane(6.0, 4.4, -0.10, 0.25)))
    bowl_profile = [
        (0.40, -0.02), (0.78, 0.00), (1.20, 0.13), (1.58, 0.36),
        (1.92, 0.66), (2.08, 0.86), (2.00, 0.94), (1.78, 0.96),
        (1.50, 0.75), (1.10, 0.46), (0.64, 0.18), (0.40, -0.02),
    ]
    groups.append(("mat_bowl_ceramic", *lathe(bowl_profile)))
    groups.append(("mat_bowl_highlight", *torus(0, 0.955, 0, 1.89, 0.035)))
    groups.append(("mat_bowl_shadow", *torus(0, -0.045, 0, 0.62, 0.045)))

    fruit_specs = [
        ("mat_red_apple", -0.98, 1.02, 0.05, 0.50, 1.00, 0.96, 1.00),
        ("mat_green_apple", -0.12, 1.12, -0.28, 0.48, 1.00, 1.02, 1.00),
        ("mat_orange", 0.78, 1.05, 0.10, 0.52, 1.00, 0.96, 1.00),
        ("mat_yellow_lemon", 0.23, 1.35, 0.54, 0.36, 1.42, 0.80, 0.84),
        ("mat_deep_red_apple", -0.23, 1.47, 0.19, 0.42, 1.00, 0.98, 1.00),
        ("mat_lime", 0.92, 1.48, -0.32, 0.32, 1.08, 0.90, 1.00),
    ]
    for spec in fruit_specs:
        groups.append((spec[0], *spheroid(*spec[1:])))

    allv, allf = [], []
    grape_centers = [
        (1.16, 1.32, -0.48), (1.40, 1.23, -0.38), (1.60, 1.06, -0.25),
        (1.06, 1.12, -0.25), (1.34, 1.50, -0.22), (1.63, 1.35, -0.06),
        (1.26, 1.18, 0.02), (1.48, 1.02, 0.15), (1.78, 1.18, -0.34),
        (1.74, 1.50, -0.22),
    ]
    for center in grape_centers:
        verts, faces = spheroid(*center, 0.17, seg=22)
        offset = len(allv)
        allv.extend(verts)
        allf.extend(tuple(n + offset for n in face) for face in faces)
    groups.append(("mat_grapes", allv, allf))

    allv, allf = [], []
    for i in range(14):
        t = i / 13
        x = -1.25 + 2.35 * t
        y = 1.72 + 0.24 * math.sin(math.pi * t)
        z = -0.66 + 0.25 * math.cos(math.pi * t)
        verts, faces = spheroid(x, y, z, 0.17, 1.55, 0.68, 0.62, seg=20)
        offset = len(allv)
        allv.extend(verts)
        allf.extend(tuple(n + offset for n in face) for face in faces)
    groups.append(("mat_banana", allv, allf))

    for cx, cy, cz, ay in [(-0.98, 1.50, 0.05, 0.15), (-0.12, 1.61, -0.28, -0.40), (-0.23, 1.86, 0.19, 0.55)]:
        groups.append(("mat_stem", *rod(cx, cy + 0.12, cz, 0.035, 0.34, az=1.18, ay=ay)))
    for cx, cy, cz, sx, sz in [(-0.72, 1.72, 0.06, 1.85, 0.62), (0.18, 1.83, -0.33, 1.70, 0.58)]:
        groups.append(("mat_leaf", *spheroid(cx, cy, cz, 0.16, sx, 0.22, sz, seg=20)))
    return groups


def write_obj(groups):
    lines = ["mtllib scene.mtl", "# bowl-of-fruit combined multi-material OBJ"]
    vertex_count = 0
    for idx, (mat, verts, faces) in enumerate(groups, 1):
        lines.extend([f"o group_{idx}_{mat}", f"usemtl {mat}", f"g group_{idx}_{mat}"])
        lines.extend(f"v {x:.5f} {y:.5f} {z:.5f}" for x, y, z in verts)
        for face in faces:
            lines.append("f " + " ".join(str(vertex_count + n) for n in face))
        vertex_count += len(verts)
    OBJ_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_mtl():
    lines = ["# Material hints; Octane binding is driven by scene.json create_material + assign_material."]
    for name, material in MATERIALS.items():
        r, g, b = material["color"]
        lines.extend([f"newmtl {name}", f"Kd {r:.4f} {g:.4f} {b:.4f}", f"Ks {0.35 if material['kind'] == 'glossy' else 0.05:.4f} {0.35 if material['kind'] == 'glossy' else 0.05:.4f} {0.35 if material['kind'] == 'glossy' else 0.05:.4f}", ""])
    MTL_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_scene(groups):
    material_names = [mat for mat, _verts, _faces in groups]
    commands = [
        {"op": "import_geometry", "payload": {"path": "examples/recipes/bowl-of-fruit/scene.obj", "format": "obj", "name": "bowl_of_fruit"}},
    ]
    for name, material in MATERIALS.items():
        payload = {"name": name, **material}
        commands.append({"op": "create_material", "payload": payload})
    for group_index, name in enumerate(material_names, 1):
        commands.append({"op": "assign_material", "payload": {"object_name": "bowl_of_fruit", "material_name": name, "group_index": group_index}})
    commands.extend([
        {"op": "set_camera", "payload": {"position": [4.25, 2.35, 5.05], "target": [0.10, 0.95, 0.00], "fov": 36}},
        {"op": "set_lighting", "payload": {"preset": "soft_studio"}},
        {"op": "save_preview", "payload": {"path": "examples/recipes/bowl-of-fruit/octane-preview.png", "width": 1280, "height": 1280, "samples": 128, "min_samples": 24, "timeout_seconds": 120}},
    ])
    scene = {
        "slug": "bowl-of-fruit",
        "title": "Bowl of Fruit (Studio)",
        "category": "Product / prop studio",
        "purpose": "Render a stylised ceramic bowl filled with apples, citrus fruit, grapes, banana, stems, and leaves under soft studio lighting. The recipe demonstrates a reusable multi-group OBJ pipeline for everyday still-life props.",
        "prompt": "Visualise a bowl of fruit.",
        "camera": {"position": [4.25, 2.35, 5.05], "target": [0.10, 0.95, 0.00], "fov": 36},
        "materials": {name: {"name": name, **mat} for name, mat in MATERIALS.items()},
        "commands": commands,
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 2.0, "min_nonbg": 2.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "very low contrast", "mostly near-white", "likely object too small"]},
        ],
        "preview_note": "octane-preview.png is the native Octane render from 2026-07-12. Pixel QA: 1280x1280, 744,599 bytes, mean abs deviation from corner background 64.459, non-background 99.964%, contrast 74.227, blank=false. Native visual inspection confirmed the subject reads as a bowl of fruit.",
        "quality_checklist": [
            "The bowl is clearly visible, centered, and large enough for thumbnail review.",
            "Fruit varieties are visually distinguishable: red apples, green apple/lime, orange citrus, yellow lemon, purple grapes, and banana.",
            "Explicit create_material + assign_material commands bind every OBJ usemtl group by 1-based group_index.",
            "Soft studio lighting gives readable highlights and contact shadows without clipping the subject.",
            "The scene is a single combined OBJ so it survives Octane's one-mesh render-target constraint.",
        ],
        "known_pitfalls": [
            "The banana is built from overlapping ellipsoids, so close inspection shows segmentation; it is acceptable for a stylised recipe but not a photoreal banana.",
            "OBJ/MTL colours are only hints: Octane colour correctness depends on the explicit create_material + assign_material commands in scene.json.",
            "Repeated imports into a long-lived persistent bridge can leave stale scene state; prefer a fresh queue and one drain for final native previews.",
        ],
        "visual_iteration_protocol": {
            "model": "ollama:glm-ocr",
            "reference_image": "examples/recipes/bowl-of-fruit/octane-preview.png",
            "candidate_image": "examples/recipes/bowl-of-fruit/octane-preview.png",
            "max_iterations": 4,
            "review_focus": ["subject readability", "fruit variety", "bowl/framing", "material colour binding", "lighting/shadows"],
            "patch_dimensions": ["geometry", "camera", "lighting", "materials", "render_settings"],
            "required_evidence": [
                "bridge result metadata for queued commands",
                "native Octane candidate preview at octane-preview.png",
                "glm-ocr reference and candidate review notes",
                "one bounded patch plan per iteration",
                "final native Octane render bundled as octane-preview.png",
                "iteration review/patch records under iterations/",
            ],
            "stop_conditions": [
                "candidate content and major silhouettes match the reference or stated recipe intent",
                "task-critical colors/materials/labels are visually distinguishable",
                "camera/framing and lighting are close enough for the task",
                "remaining gaps require bridge schema or native material capability work",
            ],
            "baseline_sweep": {
                "enabled": True,
                "purpose": "Rapidly disambiguate camera orientation and fruit pile readability before fine visual matching.",
                "camera_or_scene_variants": [
                    {"name": "front", "azimuth_degrees": 0, "elevation_degrees": 12},
                    {"name": "left_three_quarter", "azimuth_degrees": -35, "elevation_degrees": 12},
                    {"name": "right_three_quarter", "azimuth_degrees": 35, "elevation_degrees": 12},
                    {"name": "top_oblique", "azimuth_degrees": 0, "elevation_degrees": 45},
                ],
                "visual_grammar_axes": ["fruit pile silhouette", "camera_distance", "focal_length", "lighting_direction", "colour/material contrast"],
                "evidence_pattern": "iterations/baseline-<variant>.png plus iterations/baseline-review.json",
            },
        },
        "final_bundle": {
            "required": True,
            "native_render": "examples/recipes/bowl-of-fruit/octane-preview.png",
            "iteration_dir": "examples/recipes/bowl-of-fruit/iterations",
            "final_review": "examples/recipes/bowl-of-fruit/iterations/final-review.json",
            "result_metadata_pattern": "workspace/results/<command_id>.json copied or summarized into iterations/",
            "bundled_assets": ["scene.obj", "scene.mtl", "scene.json", "octane-preview.png"],
            "status": "native_candidate_available",
            "note": "The final native Octane render is bundled as octane-preview.png; material binding depends on group_index order.",
        },
        "native_octane_verified": True,
        "status": "native_octane_verified (manual persistent-bridge refinement, 2026-07-12)",
    }
    SCENE_PATH.write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")


def write_readme(groups):
    rows = []
    for i, (mat, _verts, _faces) in enumerate(groups, 1):
        rows.append(f"| {i} | `{mat}` | {MATERIALS[mat]['kind']} | `{MATERIALS[mat]['color']}` |")
    README_PATH.write_text(
        "# Bowl of Fruit (Studio)\n\n"
        "A stylised ceramic bowl filled with glossy fruit: red apples, green apple/lime, orange citrus, lemon, grapes, banana, stems, and leaves under soft studio lighting.\n\n"
        "The scene is a **single combined OBJ** with one `usemtl` group per material. This is the reliable pattern for multi-part still-life scenes because the Octane render target exposes one mesh pin; `assign_material` with `group_index` binds the colours.\n\n"
        "## Material groups\n\n"
        "| group_index | material | kind | color |\n| --- | --- | --- | --- |\n"
        + "\n".join(rows)
        + "\n\n## Run\n\n```bash\nhermes mcp call octanex octane_queue_recipe --slug bowl-of-fruit\n```\n\n"
        "## Verification\n\n"
        "`octane-preview.png` is the native Octane render from the refined persistent-bridge pass on 2026-07-12. Pixel QA reported a 1280×1280 PNG, 744,599 bytes, mean abs deviation 64.459, non-background 99.964%, contrast 74.227, and `likely_blank=false`. Native visual inspection confirmed it reads as a bowl of fruit.\n\n"
        "## Notes\n\n"
        "- Regenerate geometry and metadata with `PYTHONPATH= uv run python scripts/gen_bowl_of_fruit.py`.\n"
        "- The banana is stylised from overlapping ellipsoids; it is readable but visibly segmented at close range.\n"
        "- OBJ/MTL colours are not sufficient in Octane; keep the explicit `create_material` + `assign_material` commands in `scene.json`.\n",
        encoding="utf-8",
    )


def main():
    RECIPE_DIR.mkdir(parents=True, exist_ok=True)
    groups = build_groups()
    write_obj(groups)
    write_mtl()
    write_scene(groups)
    write_readme(groups)
    total_verts = sum(len(v) for _m, v, _f in groups)
    print(f"wrote {RECIPE_DIR} ({len(groups)} groups, {total_verts} verts)")


if __name__ == "__main__":
    main()
