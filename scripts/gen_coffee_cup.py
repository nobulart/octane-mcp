#!/usr/bin/env python3
"""Generate a designer coffee cup with frothy dark brew (single combined OBJ).

Y-up world (Octane native): the cup stands upright on +Y, the camera looks
slightly down at it. The cup is a *hollow* surface of revolution (outer wall +
inner wall + rim annulus), the handle is a swept tube, the brew is a dark
recessed disc, and the froth is a pale cap with scattered bubble spheres.

One combined OBJ with one ``usemtl`` group per material, so Octane can bind
colours by 1-based ``group_index`` -- exactly the verified pattern from
``gen_photoreal_vase_studio.py`` / ``gen_watch.py``.
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

SLUG = "coffee-cup"
OBJECT_NAME = "coffee_cup"
RECIPE_DIR = ROOT / "examples" / "recipes" / SLUG
OUT = RECIPE_DIR / "scene.obj"
MTL_PATH = RECIPE_DIR / "scene.mtl"
SCENE_PATH = RECIPE_DIR / "scene.json"
README_PATH = RECIPE_DIR / "README.md"
NATIVE_RENDER = (
    Path.home()
    / "Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/renders/coffee_cup_octane-preview.png"
)

SEG = 72  # radial resolution of the lathe / rings

# --- materials ---------------------------------------------------------------
# DESIGN: dark BLACK coffee (near-black glossy brew) with a few clear RAINBOW
# bubbles floating on the surface. No froth cap (it read as latte/cream and hid
# the black); the brew disc itself shows as the near-black surface. Bubbles are a
# single clear-glassy glossy material whose RAINBOW hue is carried per-vertex
# (the OBJ importer collapses distinct mat_bubble_N names into one pin, so the
# only way to get 7 different hues is per-vertex colour on one mat_bubble).
MATERIALS: dict[str, dict] = {
    # designer ceramic cup: warm off-white, lightly glazed
    "mat_cup":      {"kind": "glossy",   "color": [0.93, 0.90, 0.83], "roughness": 0.20},
    # the DARK BLACK brew: near-black, a touch of gloss for the meniscus sheen
    "mat_brew":     {"kind": "glossy",   "color": [0.020, 0.018, 0.015], "roughness": 0.16},
    # clear rainbow bubble: glossy glassy bead; hue comes from per-vertex colour
    "mat_bubble":   {"kind": "glossy",   "color": [0.9, 0.9, 0.9],
                     "roughness": 0.04, "specular": 1.0},
    # saucer: same ceramic family, slightly cooler
    "mat_saucer":   {"kind": "glossy",   "color": [0.88, 0.85, 0.80], "roughness": 0.24},
    # dark table / contact shadow pad
    "mat_table":    {"kind": "diffuse",  "color": [0.06, 0.05, 0.05], "roughness": 0.92},
}

# A handful of prismatic tints for the rainbow bubbles (linear 0..1 RGB).
# Each bubble gets one as its PER-VERTEX colour, layered over mat_bubble's
# glassy gloss so the beads read as bright rainbow specks on the black coffee.
RAINBOW = [
    [1.00, 0.25, 0.30],   # red
    [1.00, 0.55, 0.10],   # orange
    [0.95, 0.90, 0.20],   # yellow
    [0.25, 0.95, 0.40],   # green
    [0.20, 0.70, 1.00],   # blue
    [0.55, 0.35, 1.00],   # indigo
    [0.95, 0.35, 0.90],   # violet
]

# cup vertical profile (outer wall), bottom -> top: (radius, y)
RO = 0.86
RI = 0.72
YB = 0.0      # cup base (sits flat on the table)
YT = 1.55     # cup rim
FLOOR = YB + 0.07   # interior floor height (wall thickness at the base)
# Flat, stable base: outer wall is VERTICAL at full radius RO from the base up
# (no taper to a point), so the cup sits flat instead of on a convex cone.
OUTER_PROFILE = [
    (RO, YB), (RO, YB + 0.14),
    (RO, YB + 0.55), (RO * 0.985, YB + 1.10), (RO * 0.95, YT - 0.05), (RO * 0.93, YT),
]
INNER_PROFILE = [  # inner wall, top -> bottom (cavity floor flat at FLOOR)
    (RI * 0.93, YT), (RI * 0.95, YT - 0.05), (RI * 0.985, YB + 1.10),
    (RI, YB + 0.55), (RI, FLOOR),
]
BREW_Y = YB + 0.92   # top surface of the liquid (below the rim -> meniscus)
FROTH_Y = BREW_Y + 0.02


# --------------------------------------------------------------------------
# lathe helpers
# --------------------------------------------------------------------------
def lathe(profile, cx, cz, seg=SEG):
    """Surface of revolution about Y. profile: list[(radius, y)], bottom->top."""
    ys = [p[1] for p in profile]
    y0, y1 = min(ys), max(ys)
    steps = max(8, int((y1 - y0) / 0.025))
    samples = [y0 + (y1 - y0) * i / steps for i in range(steps + 1)]

    def radius_at(y):
        if y <= ys[0]:
            return profile[0][0]
        if y >= ys[-1]:
            return profile[-1][0]
        for (ra, ya), (rb, yb) in zip(profile, profile[1:]):
            if ya <= y <= yb:
                t = (y - ya) / (yb - ya) if yb != ya else 0.0
                return ra + (rb - ra) * t
        return profile[-1][0]

    rings = [(max(0.0, radius_at(y)), y) for y in samples]
    verts = []
    for r, y in rings:
        for j in range(seg):
            th = 2 * math.pi * j / seg
            verts.append((cx + r * math.cos(th), y, cz + r * math.sin(th)))
    faces = []
    for i in range(len(rings) - 1):
        for j in range(seg):
            j2 = (j + 1) % seg
            a = i * seg + j + 1
            b = i * seg + j2 + 1
            c = (i + 1) * seg + j2 + 1
            d = (i + 1) * seg + j + 1
            # two triangles only (Octane OBJ importer handles mixed-face OBJs poorly)
            faces.append((a, b, c))
            faces.append((a, c, d))
    return verts, faces


def puck(cx, cz, bottom_y, top_y, radius, seg=SEG):
    """A closed solid cylinder (top fan + bottom fan + side ring) -- used for
    brew / froth pucks so the top is guaranteed visible from above (Octane is
    single-sided, so an open fan disc can backface-cull)."""
    bottom_c = (cx, bottom_y, cz)
    top_c = (cx, top_y, cz)
    bottom_ring = []
    top_ring = []
    for j in range(seg):
        th = 2 * math.pi * j / seg
        c, s = math.cos(th), math.sin(th)
        bottom_ring.append((cx + radius * c, bottom_y, cz + radius * s))
        top_ring.append((cx + radius * c, top_y, cz + radius * s))
    # vertex layout (1-based): 1=bottom_c, 2=top_c,
    #   3..seg+2 = bottom_ring[j],  seg+3..2*seg+2 = top_ring[j]
    verts = [bottom_c, top_c] + bottom_ring + top_ring
    faces = []
    # bottom fan (normal -y): visible from below
    for j in range(seg):
        j2 = (j + 1) % seg
        faces.append((1, 3 + j, 3 + j2))
    # top fan (normal +y): visible from above (inside the cup)
    for j in range(seg):
        j2 = (j + 1) % seg
        faces.append((2, seg + 3 + j, seg + 3 + j2))
    # side ring (normals point outward)
    for j in range(seg):
        j2 = (j + 1) % seg
        a = 3 + j                       # bottom_ring[j]
        b = seg + 3 + j                 # top_ring[j]
        c = seg + 3 + j2                # top_ring[j2]
        d = 3 + j2                      # bottom_ring[j2]
        faces.append((a, b, c))
        faces.append((a, c, d))
    return verts, faces


def tube(points, radius, seg=20):
    """Swept circular tube through ``points`` (list of (x,y,z))."""
    n = len(points)
    # build local frames via parallel transport (good enough for a smooth handle)
    tangents = []
    for i in range(n):
        p = points[i]
        a = points[max(0, i - 1)]
        b = points[min(n - 1, i + 1)]
        t = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        tl = math.sqrt(t[0] * t[0] + t[1] * t[1] + t[2] * t[2]) or 1e-4
        tangents.append((t[0] / tl, t[1] / tl, t[2] / tl))
    # initial normal
    t0 = tangents[0]
    ref = (0.0, 1.0, 0.0)
    if abs(t0[1]) > 0.9:
        ref = (1.0, 0.0, 0.0)
    nx = t0[1] * ref[2] - t0[2] * ref[1]
    ny = t0[2] * ref[0] - t0[0] * ref[2]
    nz = t0[0] * ref[1] - t0[1] * ref[0]
    nl = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    normal = [nx / nl, ny / nl, nz / nl]
    verts = []
    for i in range(n):
        t = tangents[i]
        # re-orthogonalize normal against tangent
        dot = normal[0] * t[0] + normal[1] * t[1] + normal[2] * t[2]
        normal = [normal[0] - dot * t[0], normal[1] - dot * t[1], normal[2] - dot * t[2]]
        nl = math.sqrt(normal[0] ** 2 + normal[1] ** 2 + normal[2] ** 2) or 1.0
        normal = [normal[0] / nl, normal[1] / nl, normal[2] / nl]
        # binormal = t x normal
        bx = t[1] * normal[2] - t[2] * normal[1]
        by = t[2] * normal[0] - t[0] * normal[2]
        bz = t[0] * normal[1] - t[1] * normal[0]
        px, py, pz = points[i]
        for j in range(seg):
            th = 2 * math.pi * j / seg
            cx = normal[0] * math.cos(th) + bx * math.sin(th)
            cy = normal[1] * math.cos(th) + by * math.sin(th)
            cz = normal[2] * math.cos(th) + bz * math.sin(th)
            verts.append((px + radius * cx, py + radius * cy, pz + radius * cz))
    faces = []
    for i in range(n - 1):
        for j in range(seg):
            j2 = (j + 1) % seg
            a = i * seg + j + 1
            b = i * seg + j2 + 1
            c = (i + 1) * seg + j2 + 1
            d = (i + 1) * seg + j + 1
            faces.append((a, b, c))
            faces.append((a, c, d))
    return verts, faces


def sphere(center, radius, seg_u=16, seg_v=10):
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


def disc(cx, cy, cz, radius, axis="xz", seg=64):
    """Flat quad ring (filled) for saucer / table. axis 'xz' => normal +y."""
    center = (cx, cy, cz)
    ring = []
    for j in range(seg):
        th = 2 * math.pi * j / seg
        if axis == "xz":
            ring.append((cx + radius * math.cos(th), cy, cz + radius * math.sin(th)))
        else:
            ring.append((cx + radius * math.cos(th), cy + radius * math.sin(th), cz))
    return [center] + ring, [(1, j + 2, ((j + 1) % seg) + 2) for j in range(seg)]


def ring_with_hole(cx, cy, cz, r_inner, r_outer, seg=64):
    """Annulus (rim ring) at height cy, normal +y."""
    verts = []
    inner = []
    outer = []
    for j in range(seg):
        th = 2 * math.pi * j / seg
        c, s = math.cos(th), math.sin(th)
        inner.append((cx + r_inner * c, cy, cz + r_inner * s))
        outer.append((cx + r_outer * c, cy, cz + r_outer * s))
    verts = inner + outer
    faces = []
    for j in range(seg):
        j2 = (j + 1) % seg
        a = j + 1
        b = j2 + 1
        c = seg + j2 + 1
        d = seg + j + 1
        faces.append((a, b, c))
        faces.append((a, c, d))
    return verts, faces


# --------------------------------------------------------------------------
# deterministic bubble layout (seeded, stable across runs)
# --------------------------------------------------------------------------
def bubble_layout(n, brew_r, froth_y, seed=7):
    import random
    rng = random.Random(seed)
    bubbles = []
    for i in range(n):
        # pick a point in the disc via sqrt for uniform area
        r = brew_r * 0.88 * math.sqrt(rng.random())
        th = rng.uniform(0, 2 * math.pi)
        x = r * math.cos(th)
        z = r * math.sin(th)
        rad = rng.uniform(0.018, 0.045)
        # float just at/above the dark surface so they read as specks on black coffee
        y = froth_y + rng.uniform(-0.004, 0.012)
        bubbles.append((x, y, z, rad, i % len(RAINBOW)))
    return bubbles


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# build -- accumulate geometry per distinct material so each material maps to
# EXACTLY ONE contiguous usemtl group (the structure Octane X imports as a
# mesh with N distinct, correctly-parsed material pins).
# --------------------------------------------------------------------------
def build():
    from collections import OrderedDict
    acc = OrderedDict()  # material -> list of (verts, faces, tint_or_None)

    def add(mat, verts, faces, tint=None):
        acc.setdefault(mat, []).append((verts, faces, tint))

    # table (dark, large, top at y = -0.02)
    add("mat_table", *disc(0.0, -0.02, 0.0, 6.0, axis="xz", seg=72))
    # saucer (slightly below cup base, wide, thin disc)
    add("mat_saucer", *disc(0.0, -0.015, 0.0, 1.45, axis="xz", seg=72))
    add("mat_saucer", *ring_with_hole(0.0, 0.0, 0.0, 0.0, 1.45, seg=72))

    # cup outer wall
    add("mat_cup", *lathe(OUTER_PROFILE, 0.0, 0.0))
    # cup inner wall (reversed winding so normals face inward -> visible inside)
    inner_v, inner_f = lathe(INNER_PROFILE, 0.0, 0.0)
    inner_f = [(c, b, a) for (a, b, c) in inner_f]
    add("mat_cup", inner_v, inner_f)
    # solid flat base closes the bottom (so the cup sits, not balances on a cone)
    add("mat_cup", *puck(0.0, 0.0, YB, FLOOR, RO, seg=SEG))
    # rim annulus connecting outer top to inner top
    add("mat_cup", *ring_with_hole(0.0, YT, 0.0, RI * 0.93, RO * 0.93, seg=SEG))

    # brew: a flat dark liquid surface (disc, +Y normal) at the fill line.
    # No froth cap -- a pale disc read as latte/cream and hid the black brew.
    add("mat_brew", *disc(0.0, BREW_Y, 0.0, RI * 0.90, axis="xz", seg=SEG))

    # handle: swept tube on +x side
    hy0, hy1 = 0.45, 1.20
    hx = RO * 0.93
    arc = []
    steps = 26
    for i in range(steps + 1):
        t = i / steps
        # vertical rise then fall, bulging outward in x
        y = hy0 + (hy1 - hy0) * (0.5 - 0.5 * math.cos(math.pi * t))
        bulge = 0.42 * math.sin(math.pi * t)
        x = hx + bulge
        arc.append((x, y, 0.0))
    add("mat_cup", *tube(arc, 0.085, seg=18))

    # a few clear RAINBOW bubbles on the dark surface. They all share the single
    # `mat_bubble` pin (Octane collapses mat_bubble_N into one), so the 7 hues
    # are carried as PER-VERTEX colours -> bright rainbow beads on black coffee.
    for (x, y, z, r, tint) in bubble_layout(7, RI * 0.90, BREW_Y):
        add("mat_bubble", *sphere((x, y, z), r), tint)

    # flatten to ordered (material, verts, faces, tint) list
    groups = [(mat, verts, faces, tint)
              for mat, parts in acc.items() for (verts, faces, tint) in parts]
    return groups


def write_obj(groups):
    # PROVEN structure (matches gen_photoreal_vase_studio.py, which renders):
    # ONE `o <group_N_mat>` + `usemtl <mat>` + `g <group_N_mat>` PER GROUP,
    # each group its own object/group name. This is the OBJ shape Octane X
    # imports as visible geometry with per-material colour hints from scene.mtl.
    # (A single shared `o` across all groups rendered BLANK for an equivalent
    # cup mesh, so per-group o/g is required.)
    #
    # COLOUR: bake the material colour directly into the OBJ as PER-VERTEX COLOURS
    # (`v x y z r g b`), which Octane's OBJ importer reads and applies even when
    # the material binding fails. RAINBOW bubbles carry their hue per-vertex
    # (the single `mat_bubble` pin can't carry 7 distinct material names).
    lines = ["mtllib scene.mtl", "# designer coffee cup (Y-up, single combined OBJ)"]
    vertex_count = 0
    for idx, (mat, verts, faces, tint) in enumerate(groups, 1):
        gname = f"group_{idx}_{mat}"
        lines.append(f"o {gname}")
        lines.append(f"usemtl {mat}")
        lines.append(f"g {gname}")
        # rainbow bubbles use their per-vertex tint; everything else its material colour
        rgb = RAINBOW[tint] if (tint is not None) else MATERIALS[mat]["color"]
        r, g, b = rgb
        # Octane vertex colour is 0..1 linear RGB
        lines.extend(f"v {x:.5f} {y:.5f} {z:.5f} {r:.4f} {g:.4f} {b:.4f}" for x, y, z in verts)
        for face in faces:
            lines.append("f " + " ".join(str(vertex_count + n) for n in face))
        vertex_count += len(verts)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def material_groups(obj_text):
    """Ordered list of ``usemtl`` material names, WITH repeats -- one entry
    per group in OBJ order. Callers that need uniqueness dedupe locally.
    The bridge binds ``assign_material`` by 1-based position in this order."""
    groups = []
    for ln in obj_text.splitlines():
        if ln.startswith("usemtl "):
            groups.append(ln.split()[1])
    return groups


def validate_obj(obj_text):
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
    target = [0.0, 0.75, 0.0]
    el = math.radians(44.0)   # higher elevation so we look DOWN into the cup
    az = math.radians(28.0)
    d = 5.6
    dx = math.cos(el) * math.sin(az)
    dy = math.sin(el)
    dz = -math.cos(el) * math.cos(az)
    pos = [round(target[0] + d * dx, 4), round(target[1] + d * dy, 4), round(target[2] + d * dz, 4)]
    return {"position": pos, "target": [0.0, 0.75, 0], "fov": 40.0}


def command_sequence(groups_full, *, asset_path, preview_path):
    """``groups_full`` is the ORDERED material list (with repeats, one entry
    per ``usemtl`` group in the OBJ). The bridge binds ``assign_material`` by
    1-based ``group_index`` = position in ``usemtl`` order, so we emit one
    assign per group (not per unique name)."""
    cam = hero_camera()
    commands = [
        {"op": "import_geometry", "payload": {"path": asset_path, "format": "obj", "name": OBJECT_NAME}},
    ]
    unique = list(dict.fromkeys(groups_full))
    for name in unique:
        commands.append({"op": "create_material", "payload": {"name": name, **MATERIALS[name]}})
    # One assign_material per UNIQUE material: the mesh exposes one material pin
    # per unique usemtl name (mat_table, mat_brew, ...) — NOT per OBJ group. The
    # pin name equals the material name, so the bridge matches by name. (Queueing
    # one per group would send 32 calls; only 6 pins exist, and the per-call
    # render-restart also thrashed the engine before save_preview could write.)
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


def write_mtl():
    lines = ["# Material hints; Octane binding is driven by scene.json + assign_material."]
    for name, m in MATERIALS.items():
        r, g, b = m["color"]
        ks = 0.6 if m["kind"] == "metallic" else 0.2
        lines.extend([f"newmtl {name}", f"Kd {r:.4f} {g:.4f} {b:.4f}",
                     f"Ks {ks:.4f} {ks:.4f} {ks:.4f}", f"Ns {90 if m['kind']=='metallic' else 40}", ""])
    MTL_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_scene(groups_full):
    unique = list(dict.fromkeys(groups_full))
    scene = {
        "slug": SLUG,
        "title": "Designer Coffee Cup with Dark Black Brew and Rainbow Bubbles",
        "category": "Product / prop studio",
        "purpose": "Render an elegant designer coffee cup (warm off-white glazed ceramic, hollow lathed body, swept-tube handle, wide saucer) holding a near-black glossy coffee, studded with a few clear iridescent rainbow bubbles, on a dark table.",
        "prompt": "Visualise an elegant designer coffee cup with dark black coffee and a few rainbow clear bubbles floating on the surface.",
        "camera": hero_camera(),
        "materials": {name: {"name": name, **m} for name, m in MATERIALS.items()},
        "commands": command_sequence(
            groups_full,
            asset_path="examples/recipes/coffee-cup/scene.obj",
            preview_path="examples/recipes/coffee-cup/octane-preview.png",
        ),
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 2.0, "min_nonbg": 2.0},
            {"kind": "review_ok", "fail_on": [
                "mostly near-black", "very low contrast", "mostly near-white",
                "cup reads as solid (no hollow interior visible)", "no froth/brew visible",
            ]},
        ],
        "native_octane_verified": False,
        "status": "pending live render",
    }
    SCENE_PATH.write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")


def write_readme(groups):
    unique = list(dict.fromkeys(groups))
    rows = [f"| {i} | `{n}` | {MATERIALS[n]['kind']} | `{MATERIALS[n]['color']}` |"
            for i, n in enumerate(unique, 1)]
    README_PATH.write_text(
        "# Designer Coffee Cup with Dark Black Brew and Rainbow Bubbles\n\n"
        "![Native Octane X render](octane-preview.png)\n\n"
        "An elegant designer coffee cup in warm off-white glazed ceramic: a hollow surface-of-"
        "revolution body with a swept-tube handle, standing on a wide matching saucer on a dark "
        "table. Inside, a near-black glossy coffee is studded with a few clear iridescent "
        "rainbow bubbles. Rendered with soft-studio lighting.\n\n"
        "## Geometry convention\n\n"
        "Authored **Y-up** (Octane native). The cup body is a true hollow lathe (outer wall + "
        "reversed-winding inner wall + rim annulus) so the interior and brew are visible from the "
        "slightly-above camera angle.\n\n"
        "## Material groups\n\n"
        "| order | material | kind | color |\n| --- | --- | --- | --- |\n"
        + "\n".join(rows)
        + "\n\n## Run\n\n```bash\nhermes mcp call octanex octane_queue_recipe --slug coffee-cup\n```\n\n"
        "Then drain Octane X via **Script -> `hermes_bridge_oneshot.generated`**; one click drains the full queue.\n",
        encoding="utf-8",
    )


def copy_native_preview():
    if NATIVE_RENDER.exists():
        shutil.copy2(NATIVE_RENDER, RECIPE_DIR / "octane-preview.png")


def queue_live_render(obj_text, groups):
    ws = Workspace()
    ws.ensure()
    flushed = flush_queue(ws, backup=True)
    asset_path = ws.assets_dir / "coffee_cup.obj"
    asset_path.write_text(obj_text, encoding="utf-8")
    preview_path = ws.renders_dir / "coffee_cup_octane-preview.png"
    if preview_path.exists():
        preview_path.unlink()
    for cmd in command_sequence(groups, asset_path=str(asset_path), preview_path=str(preview_path)):
        write_command(cmd["op"], cmd["payload"], ws)
    print({"queued": len(list(ws.queue_dir.glob("*.json"))),
           "flushed": flushed, "preview": str(preview_path)})


def main():
    parser = argparse.ArgumentParser(description="Generate the coffee-cup recipe assets.")
    parser.add_argument("--queue", action="store_true",
                        help="Also queue a live Octane render into the container workspace.")
    args = parser.parse_args()
    RECIPE_DIR.mkdir(parents=True, exist_ok=True)
    groups = build()
    write_obj(groups)
    obj_text = OUT.read_text(encoding="utf-8")
    stats = validate_obj(obj_text)
    grps = material_groups(obj_text)
    write_mtl()
    write_scene(grps)
    write_readme(grps)
    copy_native_preview()
    if args.queue:
        queue_live_render(obj_text, grps)
    print({"recipe": str(RECIPE_DIR), "groups": grps, "obj_stats": stats,
           "native_preview_copied": (RECIPE_DIR / "octane-preview.png").exists()})


if __name__ == "__main__":
    main()
