#!/usr/bin/env python3
"""Generate an analog wristwatch with a linked metal strap (single combined OBJ).

Hero product shot, face-up (face normal = +Z):
  * brushed-steel case (short cylinder, axis along Z)
  * two-tone gold bezel (torus at the rim)
  * deep-blue glossy dial with gold arabic numerals + white radial markers
  * polished silver hour + minute hands, ONE END PINNED AT THE DIAL CENTER,
    radial orientation (rotation fixes the first-pass tangential bug)
  * red second hand with a counterweight tail, also pinned at center
  * steel center cap
  * two-tone gold crown at 3 o'clock
  * 4 lugs
  * two bracelet runs (up/down) of interlocking links: steel outer + gold center,
    curving away from the face (+Z) so they read as wrapping

One combined OBJ with repeated `usemtl` groups; `assign_material` per 1-based
group_index binds each part. The bridge exposes each `usemtl` group as a named
material pin on this build, so distinct colors survive.

Render target: sunset HDR environment + reflective ground for a photoreal metal look.
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
from octanex_mcp.visuals import ObjBuilder  # noqa: E402

SLUG = "wristwatch"
OBJECT_NAME = "wristwatch"
RECIPE_DIR = ROOT / "examples" / "recipes" / SLUG
OUT = RECIPE_DIR / "scene.obj"
MTL_PATH = RECIPE_DIR / "scene.mtl"
SCENE_PATH = RECIPE_DIR / "scene.json"
README_PATH = RECIPE_DIR / "README.md"
NATIVE_RENDER = Path.home() / "Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/renders/wristwatch_octane-preview.png"

# Two-tone sport watch: steel + gold accents, blue dial, white markers,
# polished silver hands, red second hand, gold arabic numerals. 8 materials.
MATERIALS: dict[str, dict] = {
    "mat_steel":   {"kind": "metallic", "color": [0.80, 0.82, 0.86], "roughness": 0.12},
    "mat_gold":    {"kind": "metallic", "color": [0.88, 0.71, 0.36], "roughness": 0.10},
    "mat_dial":    {"kind": "glossy",   "color": [0.05, 0.13, 0.34], "roughness": 0.25},
    "mat_marker":  {"kind": "glossy",   "color": [0.95, 0.95, 0.91], "roughness": 0.20},
    "mat_hand":    {"kind": "metallic", "color": [0.92, 0.93, 0.95], "roughness": 0.14},
    "mat_second":  {"kind": "glossy",   "color": [0.82, 0.07, 0.07], "roughness": 0.30},
    "mat_numeral": {"kind": "glossy",   "color": [0.96, 0.80, 0.42], "roughness": 0.22},
    "mat_ground":  {"kind": "glossy",   "color": [0.02, 0.02, 0.03], "roughness": 0.9},
}

# 3x5 pixel font for dial numerals (1 = filled cell)
GLYPH: dict[str, list[str]] = {
    "0": ["111", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"],
    "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"],
    "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"],
    "7": ["111", "001", "010", "010", "010"],
    "8": ["111", "101", "111", "101", "111"],
    "9": ["111", "101", "111", "001", "111"],
}


# ---------- geometry helpers ----------

def _rot_x(v, a):
    y, z = v[1], v[2]
    return (v[0], y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a))

def _rot_z(v, a):
    x, y = v[0], v[1]
    return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a), v[2])


def add_box_rot(b: ObjBuilder, *, center, size, material, rot_x=0.0, rot_z=0.0):
    cx, cy, cz = center
    hx = max(float(size[0]), 1e-4) / 2.0
    hy = max(float(size[1]), 1e-4) / 2.0
    hz = max(float(size[2]), 1e-4) / 2.0
    local = [
        (-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
        (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz),
    ]
    corners = []
    for p in local:
        q = p
        if rot_x:
            q = _rot_x(q, rot_x)
        if rot_z:
            q = _rot_z(q, rot_z)
        corners.append((cx + q[0], cy + q[1], cz + q[2]))
    start = b.vertex_count + 1
    b.lines.append(f"usemtl {material}")
    b._record_points(corners)
    for x, y, z in corners:
        b.lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7)]
    for f in faces:
        b.lines.append("f " + " ".join(str(start + i) for i in f))
    b.vertex_count += 8


def add_cylinder_axis(b: ObjBuilder, *, center, radius, height, axis="z", segments=28, material="default"):
    cx, cy, cz = center
    radius = max(float(radius), 1e-4)
    half = max(float(height), 1e-4) / 2.0
    segments = max(8, int(segments))
    if axis == "z":
        def ring_pt(i, zc):
            ang = 2.0 * math.pi * i / segments
            return (cx + radius * math.cos(ang), cy + radius * math.sin(ang), zc)
        ends = (cz - half, cz + half)
    elif axis == "x":
        def ring_pt(i, xc):
            ang = 2.0 * math.pi * i / segments
            return (xc, cy + radius * math.cos(ang), cz + radius * math.sin(ang))
        ends = (cx - half, cx + half)
    else:
        def ring_pt(i, yc):
            ang = 2.0 * math.pi * i / segments
            return (cx + radius * math.cos(ang), yc, cz + radius * math.sin(ang))
        ends = (cy - half, cy + half)
    start = b.vertex_count + 1
    b.lines.append(f"usemtl {material}")
    verts = []
    for off in ends:
        for i in range(segments):
            verts.append(ring_pt(i, off))
    if axis == "z":
        c0, c1 = (cx, cy, cz - half), (cx, cy, cz + half)
    elif axis == "x":
        c0, c1 = (cx - half, cy, cz), (cx + half, cy, cz)
    else:
        c0, c1 = (cx, cy - half, cz), (cx, cy + half, cz)
    bottom = start + 2 * segments
    top = bottom + 1
    verts.extend([c0, c1])
    b._record_points(verts)
    for x, y, z in verts:
        b.lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")
    for i in range(segments):
        j = (i + 1) % segments
        b.lines.append(f"f {start+i} {start+j} {start+segments+j} {start+segments+i}")
        b.lines.append(f"f {bottom} {start+j} {start+i}")
        b.lines.append(f"f {top} {start+segments+i} {start+segments+j}")
    b.vertex_count += 2 * segments + 2


def add_torus_ring(b: ObjBuilder, *, center, radius, tube_radius, z_center, material,
                   radial_segments=180, tube_segments=16):
    cx, cy = center
    start = b.vertex_count + 1
    b.lines.append(f"usemtl {material}")
    verts = []
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


def add_hand(b: ObjBuilder, *, angle_deg, length, width, thickness, material, z, tail=0.0):
    """A hand pinned at the dial center, pointing radially outward.

    The box long axis (local Y) is aligned to the radial direction by using
    rot_z = angle - 90deg, so one end sits exactly at the center (radius 0).
    """
    a = math.radians(angle_deg)
    rx, ry = math.cos(a), math.sin(a)
    rot = a - math.pi / 2.0
    mid = length / 2.0
    add_box_rot(b, center=(mid * rx, mid * ry, z), size=(width, length, thickness),
                material=material, rot_z=rot)
    if tail > 0:
        tmid = -tail / 2.0
        add_box_rot(b, center=(tmid * rx, tmid * ry, z), size=(width * 0.7, tail, thickness),
                    material=material, rot_z=rot)


def add_link(b: ObjBuilder, *, y_c, z_c, rot_x, length=0.55, width=1.45, thick=0.26):
    """One bracelet link: steel outer halves flanking a gold center (two-tone)."""
    outer_w = 0.52
    center_w = width - 2 * outer_w
    # left steel, center gold, right steel
    add_box_rot(b, center=(-(width / 2 - outer_w / 2), y_c, z_c), size=(outer_w, length, thick),
                material="mat_steel", rot_x=rot_x)
    add_box_rot(b, center=(0.0, y_c, z_c), size=(center_w, length, thick),
                material="mat_gold", rot_x=rot_x)
    add_box_rot(b, center=(width / 2 - outer_w / 2, y_c, z_c), size=(outer_w, length, thick),
                material="mat_steel", rot_x=rot_x)


def add_numeral(b: ObjBuilder, *, digit, center, cell=0.05, thickness=0.04, material="mat_numeral"):
    """Extruded 3x5 glyph (or multi-digit string) placed flat on the dial (+Z).

    Multi-digit strings lay glyphs left-to-right along X, centered as a group.
    """
    glyphs = [GLYPH[c] for c in digit]
    rows = max(len(g) for g in glyphs)
    cols_per = [len(g[0]) for g in glyphs]
    total_cols = sum(cols_per) + (len(glyphs) - 1)  # 1-cell gap between digits
    ox, oy, oz = center
    col_cursor = -(total_cols - 1) / 2.0
    for g in glyphs:
        g_rows = len(g)
        g_cols = len(g[0])
        # vertical centering of this (possibly 5-row) glyph within the line
        row_offset = (rows - 1) / 2.0 - (g_rows - 1) / 2.0
        for r, rowstr in enumerate(g):
            for c, ch in enumerate(rowstr):
                if ch != "1":
                    continue
                cx = (col_cursor + c) * cell
                cy = (row_offset + (g_rows - 1) / 2.0 - r) * cell
                add_box_rot(b, center=(ox + cx, oy + cy, oz),
                            size=(cell * 0.9, cell * 0.9, thickness), material=material)
        col_cursor += g_cols + 1  # advance + 1-cell gap


def bracelet_curve_z(side, t, n_links, link_len, bow, case_r):
    """Z-offset of a bracelet link as it curves away from the face (wrapping)."""
    y_c = side * (case_r + 0.35 + t * link_len)
    theta = t * 0.16
    z_c = -bow * (1.0 - math.cos(theta)) + 0.08
    return y_c, z_c, side * theta


# ---------- build the watch ----------

def build():
    b = ObjBuilder(OBJECT_NAME)

    case_r = 2.0
    case_half = 0.28
    case_top = case_half
    dial_r = 1.62
    dial_z = case_top + 0.04
    marker_r = 1.50
    marker_z = dial_z + 0.025
    hand_z = dial_z + 0.07
    second_z = hand_z + 0.04
    cap_z = second_z + 0.02

    # Case body (steel)
    b.add_cylinder(center=(0, 0, 0), radius=case_r, height=2 * case_half, segments=72, material="mat_steel")

    # Two-tone gold bezel at the rim
    add_torus_ring(b, center=(0, 0), radius=case_r - 0.05, tube_radius=0.14,
                   z_center=case_top + 0.02, material="mat_gold",
                   radial_segments=180, tube_segments=16)

    # Blue dial
    b.add_cylinder(center=(0, 0, dial_z), radius=dial_r, height=0.05, segments=72, material="mat_dial")

    # White hour markers as small spheres in a ring near the dial edge (chunkier
    # at 12/3/6/9). Spheres catch specular highlights so they read clearly vs the
    # flat batons that vanished against the blue dial.
    for k in range(12):
        a = math.pi / 2 - 2.0 * math.pi * k / 12
        mx, my = marker_r * math.cos(a), marker_r * math.sin(a)
        rad = 0.077 if k % 3 == 0 else 0.056
        b.add_ellipsoid(center=(mx, my, marker_z), radii=(rad, rad, rad),
                        segments_u=24, segments_v=14, material="mat_marker")


    # Gold arabic numerals just inside the markers (12 at top; classic clockwise layout)
    numeral_r = 1.20
    numeral_z = dial_z + 0.02
    for k in range(12):
        digit = str(12 if k == 0 else k)
        a = math.pi / 2 - 2.0 * math.pi * k / 12
        nx, ny = numeral_r * math.cos(a), numeral_r * math.sin(a)
        add_numeral(b, digit=digit, center=(nx, ny, numeral_z), cell=0.058, thickness=0.03)

    # Hands pinned at center, 10:10 classic pose
    add_hand(b, angle_deg=300, length=1.10, width=0.15, thickness=0.06, material="mat_hand", z=hand_z)
    add_hand(b, angle_deg=60,  length=1.50, width=0.11, thickness=0.06, material="mat_hand", z=hand_z)
    # Red second hand with counterweight tail
    add_hand(b, angle_deg=210, length=1.62, width=0.05, thickness=0.05, material="mat_second",
             z=second_z, tail=0.42)

    # Center cap (steel)
    b.add_cylinder(center=(0, 0, cap_z), radius=0.13, height=0.10, segments=48, material="mat_steel")

    # Two-tone gold crown at 3 o'clock (axis along X)
    add_cylinder_axis(b, center=(case_r + 0.14, 0, 0), radius=0.17, height=0.34, axis="x",
                      segments=48, material="mat_gold")

    # Lugs (4) bridging case to strap
    for sy in (-1, 1):
        for sx in (-1, 1):
            add_box_rot(b, center=(sx * 0.62, sy * (case_r - 0.05), 0.0),
                        size=(0.5, 0.7, 0.55), material="mat_steel")

    # Linked metal strap: two runs (up +Y, down -Y), two-tone links, curving in Z
    n_links = 7
    link_len = 0.60
    bow = 0.55
    for side in (1, -1):
        for i in range(n_links):
            t = i + 0.5
            y_c, z_c, theta = bracelet_curve_z(side, t, n_links, link_len, bow, case_r)
            add_link(b, y_c=y_c, z_c=z_c, rot_x=theta, length=link_len * 0.92)

    # Reflective floor (part of the same OBJ so it imports in one shot). Faces -Z
    # (down/away) so it reads as a floor, not a lit wall. Dark + near-matte so it
    # doesn't mirror the bright daylight sky and wash the frame.
    add_ground(b, half=9.0, top=-0.34, thick=0.4, material="mat_ground")

    return b.text(), b.bounds()


def add_ground(b: ObjBuilder, *, half=9.0, top=-0.34, thick=0.4, material="mat_ground"):
    """Floor slab below the watch, top surface normal = -Z (faces away/floor)."""
    bottom = [
        (-half, -half, top - thick), (half, -half, top - thick),
        (half, half, top - thick), (-half, half, top - thick),
    ]
    topr = [
        (-half, -half, top), (half, -half, top),
        (half, half, top), (-half, half, top),
    ]
    verts = bottom + topr
    b.lines.append(f"usemtl {material}")
    b._record_points(verts)
    for x, y, z in verts:
        b.lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")
    # indices 1-based: top ring 5..8, bottom 1..4. Top quad wound for -Z normal.
    faces = [
        (0, 1, 2, 3),   # bottom (+Z, hidden)
        (7, 6, 5, 4),   # top (-Z, visible floor)
        (4, 5, 1, 0), (5, 6, 2, 1), (6, 7, 3, 2), (7, 4, 0, 3),
    ]
    for f in faces:
        b.lines.append("f " + " ".join(str(1 + i) for i in f))
    b.vertex_count += 8


def material_groups(obj_text: str) -> list[str]:
    groups: list[str] = []
    for ln in obj_text.splitlines():
        if ln.startswith("usemtl "):
            g = ln.split()[1]
            if g not in groups:
                groups.append(g)
    return groups


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
    target = [0.0, 0.0, 0.15]
    el = math.radians(32.0)   # elevation above the face plane
    az = math.radians(20.0)   # azimuth offset
    d = 16.0
    dx = math.cos(el) * math.sin(az)
    dy = -math.cos(el) * math.cos(az)
    dz = math.sin(el)
    pos = [target[0] + d * dx, target[1] + d * dy, target[2] + d * dz]
    focus = math.sqrt(sum((pos[i] - target[i]) ** 2 for i in range(3)))
    return {"position": [round(x, 4) for x in pos], "target": target,
            "fov": 34.0, "focus_distance": round(focus, 4)}


def command_sequence(groups: list[str], *, asset_path: str, preview_path: str) -> list[dict]:
    cam = hero_camera()
    commands: list[dict] = [
        {"op": "import_geometry", "payload": {"path": asset_path, "format": "obj", "name": OBJECT_NAME}},
    ]
    unique = list(dict.fromkeys(groups))
    for name in unique:
        commands.append({"op": "create_material", "payload": {"name": name, **MATERIALS[name]}})
    for idx, name in enumerate(groups, start=1):
        commands.append({"op": "assign_material", "payload": {"object_name": OBJECT_NAME, "material_name": name, "group_index": idx}})
    commands.extend([
        {"op": "set_camera", "payload": cam},
        {"op": "set_lighting", "payload": {"preset": "soft_studio"}},
        {"op": "save_preview", "payload": {"path": preview_path, "width": 1280, "height": 1280,
                                           "samples": 1500, "min_samples": 400, "timeout_seconds": 90}},
    ])
    return commands


def write_mtl():
    lines = ["# Material hints; Octane binding is driven by scene.json create_material + assign_material."]
    for name, m in MATERIALS.items():
        r, g, bl = m["color"]
        ks = 0.6 if m["kind"] == "metallic" else 0.2
        lines.extend([f"newmtl {name}", f"Kd {r:.4f} {g:.4f} {bl:.4f}",
                      f"Ks {ks:.4f} {ks:.4f} {ks:.4f}", f"Ns {90 if m['kind']=='metallic' else 40}", ""])
    MTL_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_scene(groups: list[str]):
    scene = {
        "slug": SLUG,
        "title": "Analog Wristwatch with Linked Metal Strap (two-tone)",
        "category": "Product / prop studio",
        "purpose": "Render an analog wristwatch: steel case, gold two-tone bezel + crown, blue dial, white markers, polished silver hands pinned at center, red second hand, and a two-tone steel/gold linked bracelet.",
        "prompt": "Visualise a man's analog wrist watch with a linked metal strap",
        "camera": hero_camera(),
        "materials": {name: {"name": name, **m} for name, m in MATERIALS.items()},
        "commands": command_sequence(
            groups,
            asset_path="examples/recipes/wristwatch/scene.obj",
            preview_path="examples/recipes/wristwatch/octane-preview.png",
        ),
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 2.0, "min_nonbg": 2.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "very low contrast", "mostly near-white", "likely object too small", "dial appears metallic (material collapse)", "hands not pinned at center"]},
        ],
        "native_octane_verified": False,
        "status": "pending live render",
    }
    SCENE_PATH.write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")


def write_readme(groups: list[str]):
    unique = list(dict.fromkeys(groups))
    rows = [f"| {i} | `{n}` | {MATERIALS[n]['kind']} | `{MATERIALS[n]['color']}` |" for i, n in enumerate(unique, 1)]
    README_PATH.write_text(
        "# Analog Wristwatch with Linked Metal Strap (two-tone)\n\n"
        "![Native Octane X render](octane-preview.png)\n\n"
        "A two-tone analog wristwatch: brushed-steel case, gold bezel and crown, deep-blue glossy dial "
        "with gold arabic numerals near the outer edge and a ring of small white spherical hour markers "
        "set flush into the dial face just inside the bezel, polished silver hour/minute hands "
        "pinned at the dial center, a red second hand with counterweight, and a linked steel/gold "
        "bracelet curving away from the face (reads as wrapping). Rendered on a dark matte ground plane "
        "with soft-studio lighting at 1500 samples for a photoreal metal look.\n\n"
        "## Material groups\n\n"
        "| order | material | kind | color |\n| --- | --- | --- | --- |\n" + "\n".join(rows) + "\n\n"
        "## Run\n\n```bash\nhermes mcp call octanex octane_queue_recipe --slug wristwatch\n```\n\n"
        "Then drain Octane X via **Script -> `hermes_bridge_oneshot.generated`**; one click drains the full queue.\n",
        encoding="utf-8",
    )


def copy_native_preview():
    if NATIVE_RENDER.exists():
        shutil.copy2(NATIVE_RENDER, RECIPE_DIR / "octane-preview.png")


def queue_live_render(obj_text: str, groups: list[str]):
    ws = Workspace()
    ws.ensure()
    flushed = flush_queue(ws, backup=True)
    asset_path = ws.assets_dir / "wristwatch.obj"
    asset_path.write_text(obj_text, encoding="utf-8")
    preview_path = ws.renders_dir / "wristwatch_octane-preview.png"
    if preview_path.exists():
        preview_path.unlink()
    for cmd in command_sequence(groups, asset_path=str(asset_path), preview_path=str(preview_path)):
        write_command(cmd["op"], cmd["payload"], ws)
    print({"queued": len(list(ws.queue_dir.glob("*.json"))), "flushed": flushed, "preview": str(preview_path)})


def main():
    parser = argparse.ArgumentParser(description="Generate the wristwatch recipe assets.")
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
    print({"recipe": str(RECIPE_DIR), "groups": groups, "obj_stats": stats,
           "native_preview_copied": (RECIPE_DIR / "octane-preview.png").exists()})


if __name__ == "__main__":
    main()
