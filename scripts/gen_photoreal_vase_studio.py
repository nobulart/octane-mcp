#!/usr/bin/env python3
"""Generate the photoreal multi-vase studio recipe assets.

The recipe is a single combined OBJ with one ``usemtl`` group per material so
Octane can bind colours by 1-based ``group_index``.  Geometry is authored in
**Octane's native Y-up world** (matching the working ``bowl-of-fruit`` recipe),
which is the root fix over the previous Z-up OBJ that produced a broken native
render: vases rose in +Z so Octane (Y-up) laid them on their side and the
camera framing was off, yielding a dark/wrong frame.

Five vases with deliberately different silhouettes:
  1. smoky glass        - tall slender, faintly bulbous
  2. cobalt ceramic     - short stout, round
  3. terracotta ribbed  - medium, *real* sinusoidal ribbing in the lathe
  4. white porcelain    - tall bulbous flask
  5. dark brushed metal - tall cylindrical, flared rim

Plus a matte stone pedestal, a warm cyclorama back wall, a near-black contact
shadow pad, and bright softbox proxy panels.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RECIPE_DIR = REPO_ROOT / "examples" / "recipes" / "photoreal-vase-studio"
OBJ_PATH = RECIPE_DIR / "scene.obj"
MTL_PATH = RECIPE_DIR / "scene.mtl"
SCENE_PATH = RECIPE_DIR / "scene.json"
README_PATH = RECIPE_DIR / "README.md"

SEG = 56
WALL_SEG = 24


# --------------------------------------------------------------------------
# Primitive builders (Y-up: y is vertical)
# --------------------------------------------------------------------------
def lathe(profile, cx, cz, seg=SEG):
    """Surface of revolution about the Y axis.

    ``profile`` is a list of ``(radius, y)`` control points from bottom to top.
    A smooth sphere-cap closes the base (radius -> 0 at the start) so vessels
    read as solid from below.
    """
    # resample to an even vertical spacing for smooth shading
    ys = [p[1] for p in profile]
    y0, y1 = min(ys), max(ys)
    steps = max(8, int((y1 - y0) / 0.04))
    samples = [y0 + (y1 - y0) * i / steps for i in range(steps + 1)]

    def radius_at(y):
        if y <= ys[0]:
            return profile[0][0]
        if y >= ys[-1]:
            return profile[-1][0]
        for (r_a, ya), (r_b, yb) in zip(profile, profile[1:]):
            if ya <= y <= yb:
                t = (y - ya) / (yb - ya) if yb != ya else 0.0
                return r_a + (r_b - r_a) * t
        return profile[-1][0]

    rings = []
    for y in samples:
        r = max(0.0, radius_at(y))
        rings.append((r, y))
    verts = []
    for r, y in rings:
        for j in range(seg):
            theta = 2 * math.pi * j / seg
            verts.append((cx + r * math.cos(theta), y, cz + r * math.sin(theta)))
    faces = []
    for i in range(len(rings) - 1):
        for j in range(seg):
            j2 = (j + 1) % seg
            a = i * seg + j + 1
            b = i * seg + j2 + 1
            c = (i + 1) * seg + j2 + 1
            d = (i + 1) * seg + j + 1
            faces.append((a, b, c))
            faces.append((a, c, d))
    return verts, faces


def ribbed_lathe(profile, cx, cz, *, amp=0.06, freq=22.0, seg=SEG):
    """Like ``lathe`` but radius is modulated by a sine rib pattern."""
    ys = [p[1] for p in profile]
    y0, y1 = min(ys), max(ys)
    steps = max(8, int((y1 - y0) / 0.04))
    samples = [y0 + (y1 - y0) * i / steps for i in range(steps + 1)]

    def radius_at(y):
        if y <= ys[0]:
            return profile[0][0]
        if y >= ys[-1]:
            return profile[-1][0]
        for (r_a, ya), (r_b, yb) in zip(profile, profile[1:]):
            if ya <= y <= yb:
                t = (y - ya) / (yb - ya) if yb != ya else 0.0
                return r_a + (r_b - r_a) * t
        return profile[-1][0]

    rings = []
    for y in samples:
        base = max(0.0, radius_at(y))
        # taper ribs toward the very top so the rim stays clean
        env = 0.5 + 0.5 * math.sin(min(1.0, (y - y0) / max(1e-3, y1 - y0)) * math.pi)
        r = base * (1.0 + amp * math.sin(y * freq) * env)
        rings.append((r, y))
    verts = []
    for r, y in rings:
        for j in range(seg):
            theta = 2 * math.pi * j / seg
            verts.append((cx + r * math.cos(theta), y, cz + r * math.sin(theta)))
    faces = []
    for i in range(len(rings) - 1):
        for j in range(seg):
            j2 = (j + 1) % seg
            a = i * seg + j + 1
            b = i * seg + j2 + 1
            c = (i + 1) * seg + j2 + 1
            d = (i + 1) * seg + j + 1
            faces.append((a, b, c))
            faces.append((a, c, d))
    return verts, faces


def box(x0, x1, y0, y1, z0, z1):
    verts = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ]
    faces = [
        (1, 2, 3), (1, 3, 4),       # -z
        (5, 7, 6), (5, 8, 7),       # +z
        (1, 5, 6), (1, 6, 2),       # -y
        (4, 3, 7), (4, 7, 8),       # +y
        (1, 4, 8), (1, 8, 5),       # -x
        (2, 6, 7), (2, 7, 3),       # +x
    ]
    return verts, faces


def panel(cx, cy, cz, sx, sy, sz, axis):
    """A flat quad. ``axis`` chooses orientation: 'xy' (faces +/-z), 'xz' (faces +/-y)."""
    if axis == "xy":
        verts = [
            (cx - sx, cy - sy, cz), (cx + sx, cy - sy, cz),
            (cx + sx, cy + sy, cz), (cx - sx, cy + sy, cz),
        ]
    else:  # xz
        verts = [
            (cx - sx, cy, cz - sz), (cx + sx, cy, cz - sz),
            (cx + sx, cy, cz + sz), (cx - sx, cy, cz + sz),
        ]
    faces = [(1, 2, 3), (1, 3, 4)]
    return verts, faces


# --------------------------------------------------------------------------
# Materials
# --------------------------------------------------------------------------
MATERIALS = {
    "mat_stone_pedestal": {"kind": "diffuse", "color": [0.52, 0.50, 0.46], "roughness": 0.82},
    "mat_warm_cyclorama": {"kind": "diffuse", "color": [0.70, 0.64, 0.56], "roughness": 0.92},
    "mat_shadow": {"kind": "diffuse", "color": [0.05, 0.05, 0.06], "roughness": 1.0},
    "mat_softbox": {"kind": "diffuse", "color": [1.0, 0.97, 0.90], "roughness": 1.0},
    "mat_smoky_glass": {"kind": "specular", "color": [0.22, 0.32, 0.36], "roughness": 0.02, "transmission": 0.62, "ior": 1.46},
    "mat_cobalt_ceramic": {"kind": "glossy", "color": [0.02, 0.12, 0.72], "roughness": 0.08},
    "mat_terracotta_ribbed": {"kind": "diffuse", "color": [0.74, 0.30, 0.14], "roughness": 0.72},
    "mat_white_porcelain": {"kind": "glossy", "color": [0.90, 0.86, 0.78], "roughness": 0.16},
    "mat_dark_brushed_metal": {"kind": "metallic", "color": [0.08, 0.08, 0.09], "roughness": 0.28, "metallic": 1.0},
}

# Vase profiles: (radius, y) bottom -> top. Placed at distinct X, centered z=0.
VASE_X = [-2.4, -1.2, 0.0, 1.2, 2.4]
GLASS_PROFILE = [(0.001, 0.0), (0.34, 0.02), (0.42, 0.30), (0.36, 0.70), (0.46, 1.20), (0.40, 1.55), (0.30, 1.82)]
CERAMIC_PROFILE = [(0.001, 0.0), (0.52, 0.04), (0.62, 0.30), (0.58, 0.70), (0.40, 1.05), (0.30, 1.18)]
TERRA_PROFILE = [(0.001, 0.0), (0.46, 0.03), (0.50, 0.40), (0.44, 0.90), (0.52, 1.30), (0.42, 1.62)]
PORCELAIN_PROFILE = [(0.001, 0.0), (0.40, 0.03), (0.70, 0.45), (0.74, 0.95), (0.52, 1.45), (0.30, 1.95)]
METAL_PROFILE = [(0.001, 0.0), (0.40, 0.03), (0.42, 0.50), (0.40, 1.05), (0.46, 1.40), (0.54, 1.48)]


def build_groups():
    groups = []

    # 1. stone pedestal (flat slab the vases stand on)
    groups.append(("mat_stone_pedestal", *box(-3.6, 3.6, -0.18, 0.0, -1.45, 1.45)))
    # 2. warm cyclorama back wall
    groups.append(("mat_warm_cyclorama", *panel(0.0, 1.925, 1.45, 3.7, 1.925, 0.0, "xy")))
    # 3. contact shadow pad (thin dark plane just above the pedestal top)
    groups.append(("mat_shadow", *panel(0.0, 0.012, 0.0, 3.3, 0.0, 1.25, "xz")))
    # 4. softbox proxy panels (bright, above + sides)
    groups.append(("mat_softbox", *panel(0.0, 3.4, -0.8, 3.2, 0.0, 1.4, "xz")))   # overhead
    groups.append(("mat_softbox", *panel(-3.6, 2.0, 0.0, 0.0, 1.6, 1.6, "xy")))   # left
    groups.append(("mat_softbox", *panel(3.6, 2.0, 0.0, 0.0, 1.6, 1.6, "xy")))    # right

    # 5-9. the five vases
    groups.append(("mat_smoky_glass", *lathe(GLASS_PROFILE, VASE_X[0], 0.0)))
    groups.append(("mat_cobalt_ceramic", *lathe(CERAMIC_PROFILE, VASE_X[1], 0.0)))
    groups.append(("mat_terracotta_ribbed", *ribbed_lathe(TERRA_PROFILE, VASE_X[2], 0.0)))
    groups.append(("mat_white_porcelain", *lathe(PORCELAIN_PROFILE, VASE_X[3], 0.0)))
    groups.append(("mat_dark_brushed_metal", *lathe(METAL_PROFILE, VASE_X[4], 0.0)))
    return groups


def write_obj(groups):
    lines = ["mtllib scene.mtl", "# photoreal multi-vase studio (Y-up, single combined OBJ)"]
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
        glossy = material["kind"] == "glossy"
        lines.extend([
            f"newmtl {name}",
            f"Kd {r:.4f} {g:.4f} {b:.4f}",
            f"Ks {0.35 if glossy else 0.05:.4f} {0.35 if glossy else 0.05:.4f} {0.35 if glossy else 0.05:.4f}",
            f"Ns {720 if glossy else 70}",
            "d 1.0",
            "illum 2",
            "",
        ])
    MTL_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_scene(groups):
    material_names = [mat for mat, _v, _f in groups]
    commands = [
        {"op": "import_geometry", "payload": {
            "path": "examples/recipes/photoreal-vase-studio/scene.obj",
            "format": "obj", "name": "photoreal-vase-studio"}},
    ]
    for name, material in MATERIALS.items():
        payload = {"name": name, **material}
        commands.append({"op": "create_material", "payload": payload})
    for group_index, name in enumerate(material_names, 1):
        commands.append({"op": "assign_material", "payload": {
            "object_name": "photoreal-vase-studio",
            "material_name": name, "group_index": group_index}})
    commands.extend([
        {"op": "set_camera", "payload": {
            "position": [0.0, 2.35, -10.5], "target": [0.0, 1.05, 0.25], "fov": 45}},
        {"op": "set_lighting", "payload": {"preset": "soft_studio"}},
        {"op": "save_preview", "payload": {
            "path": "examples/recipes/photoreal-vase-studio/octane-preview.png",
            "width": 1536, "height": 864, "samples": 128, "min_samples": 16, "timeout_seconds": 30, "max_render_time": 20}},
    ])
    scene = {
        "slug": "photoreal-vase-studio",
        "title": "Photoreal Multi-Vase Studio",
        "category": "Photoreal/PBR rendering",
        "purpose": "A studio product visualization recipe for five vases with deliberately different colour, texture, and material: smoky glass, cobalt ceramic, ribbed terracotta, white porcelain, and dark brushed metal.",
        "prompt": "Create a high-end catalog render of five distinct vases on a matte pedestal with softbox reflections and a warm neutral cyclorama backdrop.",
        "preview_note": "target-preview.png is an AI-generated TARGET/REFERENCE image, NOT a native Octane render. The legitimate native render is octane-preview.png, regenerated from this recipe's geometry. This recipe previously shipped a false native_octane_verified flag and presented the AI image as the hero; that is corrected here.",
        "target_preview": "target-preview.png",
        "native_octane_verified": False,
        "camera": {"position": [0.0, 2.35, -10.5], "target": [0.0, 1.05, 0.25], "fov": 45},
        "lighting": {"preset": "soft_studio", "intent": "large side softboxes, warm overhead strip, broad soft shadows, visible glossy/specular highlights"},
        "materials": {name: {"name": name, **mat} for name, mat in MATERIALS.items()},
        "quality_checklist": [
            "Scene contains five distinct vases with visibly different silhouettes.",
            "Materials read differently: transparent smoky glass, glossy cobalt ceramic, matte ribbed terracotta, smooth white porcelain, and dark brushed metal.",
            "Softbox reflections appear on glossy/glass/metal surfaces without clipping the whole image.",
            "Pedestal and cyclorama produce a credible studio-product photography composition.",
            "Native Octane output is saved as octane-preview.png before claiming native render success.",
        ],
        "known_pitfalls": [
            "OBJ/MTL material hints cannot express full Octane glass transmission, IOR, clearcoat, or anisotropic brushed metal; scene.json material intent + assign_material drives the native look.",
            "The previous release shipped photoreal-preview.png / target-preview.png (an AI image) as the hero and a false native_octane_verified flag; do not repeat that.",
            "If the smoky-glass vase imports opaque, the bridge material schema lacks transmission/IOR support for that build -- note it, do not claim glass.",
        ],
        "assets": ["scene.obj", "scene.mtl", "target-preview.png", "octane-preview.png"],
        "commands": commands,
        "visual_iteration_protocol": {
            "model": "ollama:glm-ocr",
            "reference_image": "examples/recipes/photoreal-vase-studio/target-preview.png",
            "candidate_image": "examples/recipes/photoreal-vase-studio/octane-preview.png",
            "max_iterations": 4,
            "review_focus": [
                "object count and semantic content (exactly five vases)",
                "composition, framing, and camera perspective",
                "material/color readability and contrast",
                "lighting, shadows, and background clarity",
            ],
            "patch_dimensions": ["geometry", "camera", "lighting", "materials", "render_settings"],
            "required_evidence": [
                "bridge result metadata for queued commands",
                "native Octane candidate preview at octane-preview.png",
                "one bounded patch plan per iteration",
                "final native Octane render bundled as octane-preview.png",
                "iteration review/patch records under iterations/",
            ],
            "stop_conditions": [
                "candidate shows five distinct vases with readable, distinct materials",
                "camera/framing and lighting are close enough for a catalog shot",
                "remaining gaps require bridge schema or native material capability work",
            ],
        },
        "final_bundle": {
            "required": True,
            "native_render": "examples/recipes/photoreal-vase-studio/octane-preview.png",
            "iteration_dir": "examples/recipes/photoreal-vase-studio/iterations",
            "final_review": "examples/recipes/photoreal-vase-studio/iterations/final-review.json",
            "result_metadata_pattern": "workspace/results/<command_id>.json copied or summarized into iterations/",
            "bundled_assets": ["scene.obj", "scene.mtl", "scene.json", "target-preview.png", "octane-preview.png", "iterations/*.json", "iterations/*.png"],
            "status": "native_candidate_saved_but_not_final",
            "note": "octane-preview.png must be a real native Octane render of this recipe's geometry, not the AI target image.",
        },
        "status": "native_candidate_saved_but_not_final",
    }
    SCENE_PATH.write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")


def write_readme(groups):
    rows = []
    for i, (mat, _v, _f) in enumerate(groups, 1):
        kind = MATERIALS[mat]["kind"]
        color = MATERIALS[mat]["color"]
        rows.append(f"| {i} | `{mat}` | {kind} | `{color}` |")
    README_PATH.write_text(
        "# Photoreal Multi-Vase Studio\n\n"
        "A product-studio recipe for five vases with intentionally varied silhouettes, colours, "
        "texture treatments, and material intent -- smoky glass, cobalt ceramic, ribbed terracotta, "
        "pearlescent white porcelain, and dark brushed metal.\n\n"
        "![Native Octane render of the five-vase studio](octane-preview.png)\n\n"
        "> **Note on the reference image.** `target-preview.png` (formerly `photoreal-preview.png`) "
        "is an **AI-generated target/reference** showing the intended look. It is **not** a native "
        "Octane render and must never be shown as the recipe's legitimate preview. The hero image "
        "above (`octane-preview.png`) is the real native render produced from this recipe's geometry.\n\n"
        "## Geometry convention\n\n"
        "The scene OBJ is authored **Y-up** (Octane's native world), so vases stand upright and the "
        "camera in `scene.json` uses true `[x, y, z]` coordinates. The previous release used a Z-up "
        "OBJ with a mismatched camera convention, which produced a broken native render.\n\n"
        "## Material groups\n\n"
        "| group_index | material | kind | color |\n| --- | --- | --- | --- |\n"
        + "\n".join(rows)
        + "\n\n## Run\n\n```bash\nhermes mcp call octanex octane_queue_recipe --slug photoreal-vase-studio\n```\n\n"
        "## Regenerate\n\n"
        "```bash\nPYTHONPATH= uv run python scripts/gen_photoreal_vase_studio.py\n```\n\n"
        "## Notes\n\n"
        "- The terracotta vase's ribbing is real geometry (sinusoidal radius modulation in the lathe), "
        "not a texture hint.\n"
        "- OBJ/MTL colours are only hints; Octane colour correctness depends on the explicit "
        "`create_material` + `assign_material` commands in `scene.json`.\n"
        "- Verify the native output via bridge result metadata plus an inspected `octane-preview.png`.\n",
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
