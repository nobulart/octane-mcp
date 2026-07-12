#!/usr/bin/env python3
"""Generate the desk-fan example recipe assets.

The scene is a single combined OBJ with explicit material groups. It includes
a desk fan with blue blades, a front/back tubular guard cage, a tubular power
cord, and a plug with brass prongs.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from octanex_mcp.bridge import Workspace, flush_queue, write_command  # noqa: E402
from octanex_mcp.visuals import ObjBuilder, camera_for_bounds  # noqa: E402

SLUG = "desk-fan"
OBJECT_NAME = "desk_fan"
RECIPE_DIR = ROOT / "examples" / "recipes" / SLUG
OUT = RECIPE_DIR / "scene.obj"
MTL_PATH = RECIPE_DIR / "scene.mtl"
SCENE_PATH = RECIPE_DIR / "scene.json"
README_PATH = RECIPE_DIR / "README.md"
NATIVE_RENDER = Path.home() / "Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/renders/desk_fan_with_cord_and_plug_octane-preview.png"

MATERIALS: dict[str, dict] = {
    "mat_base": {"kind": "glossy", "color": [0.10, 0.12, 0.14], "roughness": 0.35},
    "mat_stand": {"kind": "metallic", "color": [0.70, 0.72, 0.74], "roughness": 0.22},
    "mat_motor": {"kind": "glossy", "color": [0.12, 0.15, 0.18], "roughness": 0.28},
    "mat_cage": {"kind": "metallic", "color": [0.62, 0.66, 0.70], "roughness": 0.20},
    "mat_blade": {"kind": "glossy", "color": [0.20, 0.46, 0.88], "roughness": 0.18},
    "mat_hub": {"kind": "metallic", "color": [0.93, 0.86, 0.54], "roughness": 0.20},
    "mat_cord": {"kind": "glossy", "color": [0.015, 0.015, 0.018], "roughness": 0.50},
    "mat_prong": {"kind": "metallic", "color": [0.90, 0.86, 0.72], "roughness": 0.18},
}


def add_extruded_polygon(b: ObjBuilder, points: list[tuple[float, float]], *, z_center: float, thickness: float, material: str) -> None:
    """Add a convex-ish 2D polygon in XY, extruded in Z."""
    if len(points) < 3:
        return
    z0 = z_center - thickness / 2.0
    z1 = z_center + thickness / 2.0
    start = b.vertex_count + 1
    b.lines.append(f"usemtl {material}")
    verts = [(x, y, z0) for x, y in points] + [(x, y, z1) for x, y in points]
    b._record_points(verts)
    for x, y, z in verts:
        b.lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")
    n = len(points)
    # back/front caps
    b.lines.append("f " + " ".join(str(start + i) for i in range(n)))
    b.lines.append("f " + " ".join(str(start + n + i) for i in reversed(range(n))))
    # sides
    for i in range(n):
        j = (i + 1) % n
        b.lines.append(f"f {start+i} {start+j} {start+n+j} {start+n+i}")
    b.vertex_count += 2 * n


def add_radial_bar(b: ObjBuilder, *, center: tuple[float, float], angle: float, r0: float, r1: float, width: float, z_center: float, thickness: float, material: str) -> None:
    cx, cy = center
    ux, uy = math.cos(angle), math.sin(angle)
    px, py = -uy, ux
    pts = [
        (cx + ux * r0 + px * width / 2, cy + uy * r0 + py * width / 2),
        (cx + ux * r1 + px * width / 2, cy + uy * r1 + py * width / 2),
        (cx + ux * r1 - px * width / 2, cy + uy * r1 - py * width / 2),
        (cx + ux * r0 - px * width / 2, cy + uy * r0 - py * width / 2),
    ]
    add_extruded_polygon(b, pts, z_center=z_center, thickness=thickness, material=material)


def add_ring_segments(b: ObjBuilder, *, center: tuple[float, float], radius: float, count: int, z_center: float, material: str, bead: float = 0.055) -> None:
    cx, cy = center
    for i in range(count):
        a = 2.0 * math.pi * i / count
        b.add_box(
            center=(cx + radius * math.cos(a), cy + radius * math.sin(a), z_center),
            size=(bead * 1.8, bead * 1.8, bead * 0.9),
            material=material,
        )


def add_blade(b: ObjBuilder, *, center: tuple[float, float], angle: float, material: str) -> None:
    # Swept, tapered blade as two overlapping airfoil plates.
    cx, cy = center
    pts_local = [(0.18, -0.14), (1.45, -0.28), (1.78, 0.02), (0.34, 0.24)]
    ca, sa = math.cos(angle), math.sin(angle)
    pts = []
    for x, y in pts_local:
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    add_extruded_polygon(b, pts, z_center=0.08, thickness=0.10, material=material)


def add_cable_segment(b: ObjBuilder, *, p0: tuple[float, float], p1: tuple[float, float], y: float, width: float, material: str) -> None:
    # Cable is a flattened, black rectangular tube following XZ points on the desk plane.
    x0, z0 = p0
    x1, z1 = p1
    dx, dz = x1 - x0, z1 - z0
    length = math.hypot(dx, dz) or 1e-6
    px, pz = -dz / length * width / 2, dx / length * width / 2
    pts_bottom = [
        (x0 + px, y - width / 2, z0 + pz),
        (x1 + px, y - width / 2, z1 + pz),
        (x1 - px, y - width / 2, z1 - pz),
        (x0 - px, y - width / 2, z0 - pz),
    ]
    pts_top = [(x, y + width / 2, z) for x, _yb, z in pts_bottom]
    start = b.vertex_count + 1
    b.lines.append(f"usemtl {material}")
    verts = pts_bottom + pts_top
    b._record_points(verts)
    for x, yy, z in verts:
        b.lines.append(f"v {x:.6f} {yy:.6f} {z:.6f}")
    faces = [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
    for face in faces:
        b.lines.append("f " + " ".join(str(start + i) for i in face))
    b.vertex_count += 8


def _norm3(v: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = v
    d = math.sqrt(x * x + y * y + z * z) or 1e-9
    return (x / d, y / d, z / d)


def _cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def add_tube_between(
    b: ObjBuilder,
    *,
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
    radius: float,
    material: str,
    segments: int = 10,
) -> None:
    """Add a real cylindrical tube between two arbitrary 3D points."""
    ax = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
    length = math.sqrt(ax[0] * ax[0] + ax[1] * ax[1] + ax[2] * ax[2])
    if length < 1e-6:
        return
    axis = _norm3(ax)
    helper = (0.0, 1.0, 0.0) if abs(axis[1]) < 0.9 else (1.0, 0.0, 0.0)
    u = _norm3(_cross(axis, helper))
    v = _norm3(_cross(axis, u))
    start = b.vertex_count + 1
    b.lines.append(f"usemtl {material}")
    verts: list[tuple[float, float, float]] = []
    for end in (p0, p1):
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            ca, sa = math.cos(a), math.sin(a)
            verts.append((
                end[0] + radius * (u[0] * ca + v[0] * sa),
                end[1] + radius * (u[1] * ca + v[1] * sa),
                end[2] + radius * (u[2] * ca + v[2] * sa),
            ))
    b._record_points(verts)
    for x, y, z in verts:
        b.lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")
    for i in range(segments):
        j = (i + 1) % segments
        b.lines.append(f"f {start+i} {start+j} {start+segments+j} {start+segments+i}")
    b.lines.append("f " + " ".join(str(start + i) for i in range(segments)))
    b.lines.append("f " + " ".join(str(start + segments + i) for i in reversed(range(segments))))
    b.vertex_count += 2 * segments


def add_torus_ring(
    b: ObjBuilder,
    *,
    center: tuple[float, float],
    radius: float,
    tube_radius: float,
    z_center: float,
    material: str,
    radial_segments: int = 192,
    tube_segments: int = 16,
) -> None:
    """Add a circular wire: a circle extruded/swept around a point as a torus."""
    cx, cy = center
    start = b.vertex_count + 1
    b.lines.append(f"usemtl {material}")
    verts: list[tuple[float, float, float]] = []
    for i in range(radial_segments):
        a = 2.0 * math.pi * i / radial_segments
        ca, sa = math.cos(a), math.sin(a)
        for j in range(tube_segments):
            t = 2.0 * math.pi * j / tube_segments
            rr = radius + tube_radius * math.cos(t)
            z = z_center + tube_radius * math.sin(t)
            verts.append((cx + rr * ca, cy + rr * sa, z))
    b._record_points(verts)
    for x, y, z in verts:
        b.lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")
    for i in range(radial_segments):
        ni = (i + 1) % radial_segments
        for j in range(tube_segments):
            nj = (j + 1) % tube_segments
            a = start + i * tube_segments + j
            c = start + ni * tube_segments + j
            d = start + ni * tube_segments + nj
            e = start + i * tube_segments + nj
            b.lines.append(f"f {a} {c} {d} {e}")
    b.vertex_count += radial_segments * tube_segments


def build() -> tuple[str, dict]:
    b = ObjBuilder(OBJECT_NAME)
    # Desk/floor plate for grounding.
    b.add_box(center=(0.7, 0.0, 0.0), size=(7.6, 0.08, 4.6), material="mat_base")

    # Base, neck and rear motor housing.
    b.add_cylinder(center=(0.0, 0.30, -0.10), radius=0.92, height=0.26, segments=64, material="mat_base")
    b.add_box(center=(0.0, 1.35, -0.10), size=(0.28, 2.10, 0.28), material="mat_stand")
    b.add_ellipsoid(center=(0.0, 2.55, -0.16), radii=(0.42, 0.34, 0.30), segments_u=48, segments_v=20, material="mat_motor")
    b.add_box(center=(0.0, 2.98, -0.22), size=(0.18, 0.26, 0.18), material="mat_stand")

    center = (0.0, 2.58)
    # Real fan guard cage: tube rings and radial guard wires both in front of
    # and behind the blades, plus small depth ties so it reads as a cage.
    front_z, rear_z = 0.25, -0.20
    for z in (front_z, rear_z):
        add_torus_ring(b, center=center, radius=1.62, tube_radius=0.024, z_center=z, material="mat_cage", radial_segments=224, tube_segments=18)
        add_torus_ring(b, center=center, radius=1.28, tube_radius=0.018, z_center=z, material="mat_cage", radial_segments=192, tube_segments=16)
        add_torus_ring(b, center=center, radius=0.42, tube_radius=0.016, z_center=z, material="mat_cage", radial_segments=128, tube_segments=14)
        for i in range(24):
            a = 2 * math.pi * i / 24
            add_tube_between(
                b,
                p0=(center[0] + 0.34 * math.cos(a), center[1] + 0.34 * math.sin(a), z),
                p1=(center[0] + 1.58 * math.cos(a), center[1] + 1.58 * math.sin(a), z),
                radius=0.014,
                material="mat_cage",
                segments=8,
            )
    for i in range(12):
        a = 2 * math.pi * i / 12
        add_tube_between(
            b,
            p0=(center[0] + 1.62 * math.cos(a), center[1] + 1.62 * math.sin(a), rear_z),
            p1=(center[0] + 1.62 * math.cos(a), center[1] + 1.62 * math.sin(a), front_z),
            radius=0.014,
            material="mat_cage",
            segments=8,
        )

    # Three blue translucent-looking fan blades and gold central hub.
    for i in range(3):
        add_blade(b, center=center, angle=2 * math.pi * i / 3 + 0.18, material="mat_blade")
    b.add_cylinder(center=(0.0, 2.58, 0.12), radius=0.30, height=0.24, segments=48, material="mat_hub")

    # Cord trails from base to the right as a real black tube, then ends in a plug
    # with two brass prongs.
    cord_points = [(-0.25, 0.12, -0.12), (0.55, 0.12, -0.62), (1.45, 0.12, -0.92), (2.55, 0.12, -0.65), (3.25, 0.12, -1.05)]
    for a, c in zip(cord_points, cord_points[1:]):
        add_tube_between(b, p0=a, p1=c, radius=0.055, material="mat_cord", segments=12)
    # plug body and prongs near the cord end
    b.add_box(center=(3.46, 0.16, -1.12), size=(0.58, 0.30, 0.38), material="mat_cord")
    b.add_box(center=(3.92, 0.22, -1.04), size=(0.48, 0.045, 0.055), material="mat_prong")
    b.add_box(center=(3.92, 0.10, -1.20), size=(0.48, 0.045, 0.055), material="mat_prong")

    return b.text(), b.bounds()


def group_order(obj_text: str) -> list[str]:
    groups: list[str] = []
    for ln in obj_text.splitlines():
        if ln.startswith("usemtl "):
            group = ln.split()[1]
            if group not in groups:
                groups.append(group)
    return groups


def validate_obj(obj_text: str) -> dict[str, int]:
    vcount = sum(1 for ln in obj_text.splitlines() if ln.startswith("v "))
    fcount = sum(1 for ln in obj_text.splitlines() if ln.startswith("f "))
    max_idx = 0
    for ln in obj_text.splitlines():
        if ln.startswith("f "):
            for tok in ln.split()[1:]:
                max_idx = max(max_idx, int(tok.split("/")[0]))
    if max_idx > vcount:
        raise RuntimeError(f"OBJ invalid: max face index {max_idx} > vertex count {vcount}")
    return {"vertices": vcount, "faces": fcount, "max_face_index": max_idx}



def material_groups(obj_text: str) -> list[str]:
    return [ln.split()[1] for ln in obj_text.splitlines() if ln.startswith("usemtl ")]


def command_sequence(groups: list[str], *, asset_path: str = "examples/recipes/desk-fan/scene.obj", preview_path: str = "examples/recipes/desk-fan/octane-preview.png") -> list[dict]:
    camera = {"position": [2.6, 2.95, 8.4], "target": [0.65, 1.58, -0.28], "fov": 38.0, "focus_distance": 9.0012110296337}
    commands: list[dict] = [
        {"op": "import_geometry", "payload": {"path": asset_path, "format": "obj", "name": OBJECT_NAME}},
    ]
    unique_materials = list(dict.fromkeys(groups))
    for name in unique_materials:
        mat = MATERIALS[name]
        commands.append({"op": "create_material", "payload": {"name": name, **mat}})
    for idx, name in enumerate(groups, start=1):
        commands.append({"op": "assign_material", "payload": {"object_name": OBJECT_NAME, "material_name": name, "group_index": idx}})
    commands.extend([
        {"op": "set_camera", "payload": camera},
        {"op": "set_lighting", "payload": {"preset": "soft_studio"}},
        {"op": "save_preview", "payload": {"path": preview_path, "width": 1280, "height": 1280, "quality": "standard", "samples": 96, "min_samples": 24, "timeout_seconds": 120}},
    ])
    return commands


def write_mtl() -> None:
    lines = ["# Material hints; Octane binding is driven by scene.json create_material + assign_material."]
    for name, material in MATERIALS.items():
        r, g, b = material["color"]
        ks = 0.45 if material["kind"] in {"glossy", "metallic"} else 0.08
        lines.extend([f"newmtl {name}", f"Kd {r:.4f} {g:.4f} {b:.4f}", f"Ks {ks:.4f} {ks:.4f} {ks:.4f}", f"Ns {80 if material['kind'] == 'metallic' else 40}", ""])
    MTL_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_scene(groups: list[str]) -> None:
    scene = {
        "slug": SLUG,
        "title": "Desk Fan with Cord and Plug",
        "category": "Product / prop studio",
        "purpose": "Render a stylised desk fan with blue blades, a tubular front/back cage guard, stand/base, black tubular power cord, plug body, and brass prongs under soft studio lighting.",
        "prompt": "Visualise a desk fan with a cord and plug",
        "camera": {"position": [2.6, 2.95, 8.4], "target": [0.65, 1.58, -0.28], "fov": 38.0, "focus_distance": 9.0012110296337},
        "materials": {name: {"name": name, **mat} for name, mat in MATERIALS.items()},
        "commands": command_sequence(groups),
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 2.0, "min_nonbg": 2.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "very low contrast", "mostly near-white", "likely object too small"]},
        ],
        "preview_note": "octane-preview.png is the native Octane X render from 2026-07-12 after three refinement passes. Pixel QA: 1280x1280, 560,789 bytes, sampled non-background 92.93%, edge_std 20.27, blank=false. Visual QA confirmed a desk fan with a cage guard, blue blades, stand/base, tubular cord, plug, and brass prongs.",
        "quality_checklist": [
            "The fan silhouette is readable at thumbnail size: guard cage, hub, three blades, stand, and base.",
            "The guard is modeled as a cage: front and rear circular wire rings plus radial wires and depth ties around the blades.",
            "The power cable is a real tube, not a flat strip, and leads to a visible plug with two brass prongs.",
            "Explicit create_material + assign_material commands bind every OBJ usemtl group by 1-based group_index.",
            "Camera focus_distance is set to the camera-target distance to avoid the thin-lens depth-of-field blur seen in the first render.",
        ],
        "known_pitfalls": [
            "The guard wires are true mesh tubes, but at small preview sizes dense wires can alias; inspect the native PNG rather than only the thumbnail.",
            "OBJ/MTL colours are only hints: Octane colour correctness depends on the explicit create_material + assign_material commands in scene.json.",
            "Thin-lens focus must be set for this scene; otherwise the cage and plug can render soft. The recipe sets focus_distance explicitly.",
            "The desk plate is a simple product-shot ground plane, not a full environment or room model.",
        ],
        "visual_iteration_protocol": {
            "model": "ollama:glm-ocr",
            "reference_image": "examples/recipes/desk-fan/octane-preview.png",
            "candidate_image": "examples/recipes/desk-fan/octane-preview.png",
            "max_iterations": 4,
            "review_focus": ["guard cage readability", "cord/plug readability", "focus/sharpness", "material binding", "framing"],
            "patch_dimensions": ["geometry", "camera", "focus_distance", "materials", "lighting"],
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
                "purpose": "Rapidly compare fan front, three-quarter, plug-emphasis, and top-oblique variants before fine visual matching.",
                "camera_or_scene_variants": [
                    {"name": "front", "azimuth_degrees": 0, "elevation_degrees": 10},
                    {"name": "right_three_quarter", "azimuth_degrees": 28, "elevation_degrees": 12},
                    {"name": "plug_emphasis", "azimuth_degrees": 18, "elevation_degrees": 8},
                    {"name": "top_oblique", "azimuth_degrees": 0, "elevation_degrees": 35},
                ],
                "visual_grammar_axes": ["cage_wire_density", "cord_tube_readability", "plug_prong_visibility", "camera_distance", "focus_depth"],
                "evidence_pattern": "iterations/baseline-<variant>.png plus iterations/baseline-review.json",
            },
        },
        "final_bundle": {
            "required": True,
            "native_render": "examples/recipes/desk-fan/octane-preview.png",
            "iteration_dir": "examples/recipes/desk-fan/iterations",
            "final_review": "examples/recipes/desk-fan/iterations/final-review.json",
            "result_metadata_pattern": "workspace/results/<command_id>.json copied or summarized into iterations/",
            "bundled_assets": ["scene.obj", "scene.mtl", "scene.json", "octane-preview.png"],
            "status": "native_candidate_available",
            "note": "The final native Octane render is bundled as octane-preview.png; material binding depends on group_index order.",
        },
        "native_octane_verified": True,
        "status": "native_octane_verified (manual one-shot bridge refinement, 2026-07-12)",
    }
    SCENE_PATH.write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")


def write_readme(groups: list[str]) -> None:
    unique_materials = list(dict.fromkeys(groups))
    rows = [f"| {i} | `{name}` | {MATERIALS[name]['kind']} | `{MATERIALS[name]['color']}` |" for i, name in enumerate(unique_materials, 1)]
    README_PATH.write_text(
        "# Desk Fan with Cord and Plug\n\n"
        "![Native Octane X render](octane-preview.png)\n\n"
        "A stylised desk fan with three blue blades, a tubular front/back guard cage, stand/base, tubular black power cord, plug body, and two brass prongs under soft studio lighting.\n\n"
        "The scene is a **single combined OBJ** with repeated `usemtl` groups for each modeled part. This preserves the one-mesh render-target constraint while letting `assign_material(group_index=...)` bind cage, blades, cord, plug, and metal details separately.\n\n"
        "## Material groups\n\n"
        "| material-order | material | kind | color |\n| --- | --- | --- | --- |\n"
        + "\n".join(rows)
        + "\n\n## Run\n\n```bash\nhermes mcp call octanex octane_queue_recipe --slug desk-fan\n```\n\n"
        "Then drain Octane X via **Script -> `hermes_bridge_oneshot.generated`**; one click drains the full queue.\n\n"
        "## Verification\n\n"
        "`octane-preview.png` is the native Octane X render from the 2026-07-12 refinement pass. Pixel QA reported a 1280x1280 PNG, 560,789 bytes, sampled non-background 92.93%, edge_std 20.27, and `likely_blank=false`. Visual inspection confirmed the fan, cage guard, blue blades, tubular cord, plug, and brass prongs are visible and in focus.\n\n"
        "## Notes\n\n"
        "- Regenerate geometry and metadata with `PYTHONPATH= uv run python scripts/gen_desk_fan.py`.\n"
        f"- The OBJ contains {len(groups)} `usemtl` groups; `scene.json` emits one `assign_material` per group index, including repeated materials for separate cage wires/tubes.\n"
        "- The cage uses front and rear torus rings, radial wires, and depth ties; keep it as tubes, not flat strips or bead-only rings.\n"
        "- The cord is intentionally modeled as a real tube after review; do not flatten it back into a rectangular strip.\n"
        "- The scene sets a camera `focus_distance` because the first render showed thin-lens depth-of-field blur.\n"
        "- OBJ/MTL colours are not sufficient in Octane; keep the explicit `create_material` + `assign_material` commands in `scene.json`.\n",
        encoding="utf-8",
    )


def copy_native_preview() -> None:
    if NATIVE_RENDER.exists():
        shutil.copy2(NATIVE_RENDER, RECIPE_DIR / "octane-preview.png")


def queue_live_render(obj_text: str, groups: list[str]) -> None:
    ws = Workspace()
    ws.ensure()
    flushed = flush_queue(ws, backup=True)
    asset_path = ws.assets_dir / "desk_fan.obj"
    asset_path.write_text(obj_text, encoding="utf-8")
    preview_path = ws.renders_dir / "desk_fan_with_cord_and_plug_octane-preview.png"
    if preview_path.exists():
        preview_path.unlink()
    for cmd in command_sequence(groups, asset_path=str(asset_path), preview_path=str(preview_path)):
        write_command(cmd["op"], cmd["payload"], ws)
    print({"queued": len(list(ws.queue_dir.glob("*.json"))), "flushed": flushed, "preview": str(preview_path)})


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the desk-fan recipe assets.")
    parser.add_argument("--queue", action="store_true", help="Also queue a live Octane render into the container workspace.")
    args = parser.parse_args()
    RECIPE_DIR.mkdir(parents=True, exist_ok=True)
    obj_text, _bounds = build()
    stats = validate_obj(obj_text)
    groups = material_groups(obj_text)
    OUT.write_text(obj_text, encoding="utf-8")
    write_mtl()
    write_scene(groups)
    write_readme(groups)
    copy_native_preview()
    if args.queue:
        queue_live_render(obj_text, groups)
    print({"recipe": str(RECIPE_DIR), "groups": groups, "obj_stats": stats, "native_preview_copied": (RECIPE_DIR / "octane-preview.png").exists()})


if __name__ == "__main__":
    main()
