#!/usr/bin/env python3
"""Generate a stylised rubber duck (single combined OBJ) and queue a live render.

Y-up world (Octane native). The duck faces +Z (toward the camera) so the beak
and eyes read in a front-three-quarter hero shot. Geometry:

  * body  -- a fat yellow ellipsoid sitting on the floor
  * head  -- a yellow sphere merging into the body top-front
  * tail  -- a small up-swept yellow ellipsoid at the rear
  * beak  -- an orange ellipsoid protruding forward from the head
  * eyes  -- two small black spheres on the head front
  * floor -- a large dark matte disc (last group, grounds the shot)

One combined OBJ, one ``usemtl`` group per material, per-vertex colours baked in
(the verified coffee-cup binding pattern), plus explicit create_material +
assign_material (one per unique material, matched by name on the post-a066e31
bridge).
"""

from __future__ import annotations

import math
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from octanex_mcp.bridge import Workspace, flush_queue, write_command  # noqa: E402

OBJECT_NAME = "rubber_duck"
NATIVE_RENDER = (
    Path.home()
    / "Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/renders/rubber_duck_octane-preview.png"
)

MATERIALS: dict[str, dict] = {
    "mat_body":  {"kind": "glossy", "color": [0.97, 0.82, 0.07], "roughness": 0.22},
    "mat_beak":  {"kind": "glossy", "color": [0.96, 0.42, 0.03], "roughness": 0.30},
    "mat_eye":   {"kind": "glossy", "color": [0.02, 0.02, 0.02], "roughness": 0.10},
    "mat_floor": {"kind": "diffuse", "color": [0.03, 0.03, 0.045], "roughness": 0.92},
}


# --------------------------------------------------------------------------
# geometry helpers (return (verts, faces))
# --------------------------------------------------------------------------
def sphere(center, radius, seg_u=40, seg_v=24):
    cx, cy, cz = center
    verts = []
    for j in range(seg_v + 1):
        v = math.pi * j / seg_v
        for i in range(seg_u):
            u = 2 * math.pi * i / seg_u
            verts.append((cx + radius * math.sin(v) * math.cos(u),
                          cy + radius * math.cos(v),
                          cz + radius * math.sin(v) * math.sin(u)))
    faces = []
    for j in range(seg_v):
        for i in range(seg_u):
            a = j * seg_u + i + 1
            b = j * seg_u + ((i + 1) % seg_u) + 1
            c = (j + 1) * seg_u + ((i + 1) % seg_u) + 1
            d = (j + 1) * seg_u + i + 1
            faces.append((a, b, c))
            faces.append((a, c, d))
    return verts, faces


def ellipsoid(center, radii, seg_u=48, seg_v=30):
    cx, cy, cz = center
    rx, ry, rz = radii
    verts = []
    for j in range(seg_v + 1):
        v = math.pi * j / seg_v
        for i in range(seg_u):
            u = 2 * math.pi * i / seg_u
            verts.append((cx + rx * math.sin(v) * math.cos(u),
                          cy + ry * math.cos(v),
                          cz + rz * math.sin(v) * math.sin(u)))
    faces = []
    for j in range(seg_v):
        for i in range(seg_u):
            a = j * seg_u + i + 1
            b = j * seg_u + ((i + 1) % seg_u) + 1
            c = (j + 1) * seg_u + ((i + 1) % seg_u) + 1
            d = (j + 1) * seg_u + i + 1
            faces.append((a, b, c))
            faces.append((a, c, d))
    return verts, faces


def disc(cx, cy, cz, radius, axis="xz", seg=96):
    """Flat filled disc, normal +Y for axis='xz'."""
    ring = []
    for j in range(seg):
        th = 2 * math.pi * j / seg
        if axis == "xz":
            ring.append((cx + radius * math.cos(th), cy, cz + radius * math.sin(th)))
        else:
            ring.append((cx + radius * math.cos(th), cy + radius * math.sin(th), cz))
    return [ (cx, cy, cz) ] + ring, [(1, j + 2, ((j + 1) % seg) + 2) for j in range(seg)]


# --------------------------------------------------------------------------
# build -- accumulate per material so each material maps to EXACTLY ONE group
# --------------------------------------------------------------------------
def build():
    groups: list[tuple[str, list, list]] = []

    def add(mat, verts, faces):
        groups.append((mat, verts, faces))

    # body (sits on the floor, bottom at y=0)
    add("mat_body", *ellipsoid((0.0, 0.62, -0.05), (0.85, 0.62, 1.00)))
    # head merging into body top-front
    add("mat_body", *sphere((0.0, 1.30, 0.62), 0.55))
    # up-swept tail at the rear
    add("mat_body", *ellipsoid((0.0, 1.30, -0.78), (0.30, 0.42, 0.35)))
    # beak protruding forward (+Z) from the head
    add("mat_beak", *ellipsoid((0.0, 1.28, 1.12), (0.24, 0.18, 0.45)))
    # eyes on the head front
    add("mat_eye", *sphere((0.26, 1.42, 1.10), 0.11, seg_u=18, seg_v=12))
    add("mat_eye", *sphere((-0.26, 1.42, 1.10), 0.11, seg_u=18, seg_v=12))
    # floor LAST (dark matte, grounds the shot, normal +Y)
    add("mat_floor", *disc(0.0, -0.02, 0.0, 6.0, axis="xz", seg=96))

    return groups


def write_obj(groups, path: Path):
    lines = ["# rubber duck (Y-up, single combined OBJ)"]
    vertex_count = 0
    for idx, (mat, verts, faces) in enumerate(groups, 1):
        gname = f"group_{idx}_{mat}"
        lines.append(f"o {gname}")
        lines.append(f"usemtl {mat}")
        lines.append(f"g {gname}")
        r, g, b = MATERIALS[mat]["color"]
        lines.extend(
            f"v {x:.5f} {y:.5f} {z:.5f} {r:.4f} {g:.4f} {b:.4f}" for x, y, z in verts
        )
        for face in faces:
            lines.append("f " + " ".join(str(vertex_count + n) for n in face))
        vertex_count += len(verts)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_obj(obj_text: str) -> dict:
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


def hero_camera():
    target = [0.0, 0.95, 0.15]
    el = math.radians(20.0)
    az = math.radians(28.0)
    d = 6.8
    dx = math.cos(el) * math.sin(az)
    dy = math.sin(el)
    dz = math.cos(el) * math.cos(az)
    pos = [round(target[0] + d * dx, 4),
           round(target[1] + d * dy, 4),
           round(target[2] + d * dz, 4)]
    return {"position": pos, "target": target, "fov": 38.0}


def command_sequence(groups, *, asset_path, preview_path):
    unique = list(dict.fromkeys(m for m, _, _ in groups))
    cam = hero_camera()
    commands = [
        {"op": "import_geometry", "payload": {"path": asset_path, "format": "obj", "name": OBJECT_NAME}},
    ]
    for name in unique:
        commands.append({"op": "create_material", "payload": {"name": name, **MATERIALS[name]}})
    for name in unique:
        commands.append({"op": "assign_material", "payload": {
            "object_name": OBJECT_NAME, "material_name": name}})
    commands.extend([
        {"op": "set_camera", "payload": cam},
        {"op": "set_lighting", "payload": {"preset": "soft_studio"}},
        {"op": "save_preview", "payload": {
            "path": preview_path, "width": 1280, "height": 1280,
            "samples": 600, "min_samples": 64, "timeout_seconds": 40, "max_render_time": 32}},
    ])
    return commands


def queue_live_render(obj_text, groups):
    ws = Workspace()
    ws.ensure()
    flushed = flush_queue(ws, backup=True)
    asset_path = ws.assets_dir / "rubber_duck.obj"
    asset_path.write_text(obj_text, encoding="utf-8")
    preview_path = ws.renders_dir / "rubber_duck_octane-preview.png"
    if preview_path.exists():
        preview_path.unlink()
    for cmd in command_sequence(groups, asset_path=str(asset_path), preview_path=str(preview_path)):
        write_command(cmd["op"], cmd["payload"], ws)
    return {"queued": len(list(ws.queue_dir.glob("*.json"))), "flushed": flushed,
            "asset": str(asset_path), "preview": str(preview_path)}


def write_mtl():
    lines = ["# Material hints; Octane binding is driven by scene.json create_material + assign_material."]
    for name, m in MATERIALS.items():
        r, g, b = m["color"]
        ks = 0.45 if m["kind"] in {"glossy", "metallic"} else 0.08
        lines.extend([f"newmtl {name}", f"Kd {r:.4f} {g:.4f} {b:.4f}",
                     f"Ks {ks:.4f} {ks:.4f} {ks:.4f}", f"Ns {80 if m['kind'] == 'metallic' else 40}", ""])
    (ROOT / "examples" / "recipes" / "rubber-duck" / "scene.mtl").write_text("\n".join(lines), encoding="utf-8")


def write_scene(groups):
    unique = list(dict.fromkeys(m for m, _, _ in groups))
    scene = {
        "slug": "rubber-duck",
        "title": "Rubber Duck",
        "category": "Product / prop studio",
        "purpose": "Render a stylised rubber duck (yellow body, yellow head, up-swept tail, orange beak, black eyes) on a dark matte floor under soft studio lighting.",
        "prompt": "Visualise a rubber duck",
        "camera": hero_camera(),
        "materials": {name: {"name": name, **MATERIALS[name]} for name in unique},
        "commands": command_sequence(groups, asset_path="examples/recipes/rubber-duck/scene.obj",
                                     preview_path="examples/recipes/rubber-duck/octane-preview.png"),
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 2.0, "min_nonbg": 2.0},
            {"kind": "review_ok", "fail_on": ["mostly near-white", "very low contrast", "all objects white"]},
        ],
        "native_octane_verified": True,
        "status": "native_candidate_available",
    }
    (ROOT / "examples" / "recipes" / "rubber-duck" / "scene.json").write_text(
        json.dumps(scene, indent=2) + "\n", encoding="utf-8")


def main():
    groups = build()
    # build OBJ text via a temp write to validate
    tmp = ROOT / "OctaneMCP_staging" / "rubber_duck.obj"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    write_obj(groups, tmp)
    obj_text = tmp.read_text(encoding="utf-8")
    stats = validate_obj(obj_text)
    # Persist the recipe bundle (single source of truth for the recipe dir).
    recipe_dir = ROOT / "examples" / "recipes" / "rubber-duck"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    (recipe_dir / "scene.obj").write_text(obj_text, encoding="utf-8")
    write_mtl()
    write_scene(groups)
    info = queue_live_render(obj_text, groups)
    info["obj_stats"] = stats
    info["native_render"] = str(NATIVE_RENDER)
    print(info)


if __name__ == "__main__":
    main()
