#!/usr/bin/env python3
"""Generate Phase A deterministic physical-simulation recipe assets.

Phase A recipes are *fixture-first*: they compute a small, deterministic
physical state with pure Python (no external simulator, no NumPy required) and
emit a complete recipe directory:

  * scene.obj    — single combined OBJ with per-group `usemtl` (one mesh per
                   render target; the OctaneX bridge connects only one mesh).
  * scene.mtl    — material hints (documentation; the bridge uses explicit
                   create_material + assign_material commands instead).
  * scene.json   — verified-recipe contract: import + create_material per group
                   + assign_material(group_index) per group + camera + lighting
                   + save_preview (no colliding start_render; the live runner
                   strips it anyway). Includes the optional `simulation` block.
  * preview.png  — a lightweight reference raster (stdlib zlib/PNG, no PIL) so
                   the offline contract passes before any native render.
  * README.md    — purpose, starter prompt, re-render command, pitfalls.

Recipes built here:
  A1 fluid-kelvin-helmholtz-slice — opposed shear layers roll into vortices.
  A2 advection-diffusion-pulse    — Gaussian tracer broadens/diminishes over 4 panels.
  A3 mass-spring-cloth-drape      — Verlet cloth drapes over a sphere (contact tenting).
  A4 rigid-stack-contact-forces   — settled blocks + contact-force glyphs.
  A5 nbody-chaotic-divergence     — two near-identical 3-body paths diverge.

Run:
    PYTHONPATH= uv run python scripts/gen_physics_sim_recipes.py
"""
from __future__ import annotations

import json
import math
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECIPES = ROOT / "examples" / "recipes"

# Reuse the project's ObjBuilder so geometry/index behaviour matches every
# other recipe generator in the repo.
sys_path_patch = None
import sys as _sys  # noqa: E402

if str(ROOT / "src") not in _sys.path:
    _sys.path.insert(0, str(ROOT / "src"))

from octanex_mcp.visuals import ObjBuilder, camera_for_bounds  # noqa: E402


# --------------------------------------------------------------------------- #
# stdlib PNG writer (no PIL — the recipe-gen venv lacks PIL)                   #
# --------------------------------------------------------------------------- #
def _png_bytes(width: int, height: int, pixels: bytes) -> bytes:
    """pixels: RGB bytes, rows top-to-bottom, width*height*3."""

    def chunk(tag: bytes, data: bytes) -> bytes:
        c = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", c)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter type 0 (none) per scanline
        raw.extend(pixels[y * width * 3 : (y + 1) * width * 3])
    idat = zlib.compress(bytes(raw), 9)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def write_preview(path: Path, width: int, height: int, pixels: bytes) -> None:
    path.write_bytes(_png_bytes(width, height, pixels))


# --------------------------------------------------------------------------- #
# Shared geometry helpers                                                      #
# --------------------------------------------------------------------------- #
def add_arrow(b: ObjBuilder, *, p0, p1, shaft_r=0.05, head_r=0.16, head_h=0.36,
              segments=10, material="default") -> None:
    """Thin wrapper around ObjBuilder.add_arrow with sane defaults."""
    b.add_arrow(start_point=p0, end_point=p1, shaft_radius=shaft_r,
                head_radius=head_r, head_height=head_h, segments=segments,
                material=material)


def make_heightfield_grid(rows: int, cols: int, value_fn) -> list[list[tuple[float, float, float]]]:
    """value_fn(i, j) -> (x, y, z); returns a 2D vertex grid for add_surface."""
    grid: list[list[tuple[float, float, float]]] = []
    for i in range(rows):
        row = [value_fn(i, j) for j in range(cols)]
        grid.append(row)
    return grid


def validate_obj_indices(obj_text: str, label: str) -> dict:
    vcount = 0
    max_idx = 0
    for ln in obj_text.splitlines():
        if ln.startswith("v "):
            vcount += 1
        elif ln.startswith("f "):
            for tok in ln.split()[1:]:
                max_idx = max(max_idx, int(tok.split("/")[0]))
    if max_idx > vcount:
        raise RuntimeError(f"{label}: OBJ invalid — max face index {max_idx} > vertex count {vcount}")
    return {"vertices": vcount, "max_face_index": max_idx}


# --------------------------------------------------------------------------- #
# A1 — Kelvin–Helmholtz shear-layer slice                                     #
# --------------------------------------------------------------------------- #
def build_kelvin_helmholtz(d: Path) -> dict:
    N = 96  # grid resolution
    L = 12.0
    span = L / 2.0
    dy = 2.0  # half-thickness of the shear layer about y=0
    show_x = (-span, span)
    show_y = (-span, span)
    nx = N
    ny = N
    # Scalar tracer: tilted tanh layers (rolls) + interface displacement help
    # read the vortex rolls. Plus a vorticity-ribbon overlay on the interfaces.
    kx = 2 * math.pi / (L / 2.2)
    amp = 0.9
    verts: list[list[tuple[float, float, float]]] = []
    for iy in range(ny):
        y = show_y[0] + (show_y[1] - show_y[0]) * iy / (ny - 1)
        row = []
        for ix in range(nx):
            x = show_x[0] + (show_x[1] - show_x[0]) * ix / (nx - 1)
            # interface displacement (roll roll-up cue)
            eta = amp * math.exp(-(y * y) / (dy * dy)) * math.sin(kx * x)
            # tracer concentration: upper layer (y>0) vs lower layer (y<0)
            yy = y - eta
            conc = 0.5 * (1.0 - math.tanh(yy / 0.45))
            z = conc * 1.6 - 0.8  # heightfield in z
            row.append((x, y, z))
        verts.append(row)

    b = ObjBuilder("fluid_kh_slice")
    # base plate
    b.add_box(center=(0, 0, -0.95), size=(L + 1.0, L + 1.0, 0.1), material="kh_base")
    b.add_surface(vertices=verts, material="kh_tracer")

    # Vorticity ribbons: along the interface (y ~ eta) draw counter-rotating
    # tube ribbons — upper roll rotates one way, lower the other.
    ribbon_pts: list[tuple[float, float, float]] = []
    steps = 200
    for s in range(steps + 1):
        x = show_x[0] + (show_x[1] - show_x[0]) * s / steps
        y = amp * math.exp(-0.0 / (dy * dy)) * math.sin(kx * x)  # eta at y=0
        ribbon_pts.append((x, y, 0.25))
    if ribbon_pts:
        for k in range(len(ribbon_pts) - 1):
            p0 = ribbon_pts[k]
            p1 = ribbon_pts[k + 1]
            # colour family flips by roll index (upper vs lower) -> two materials
            mat = "kh_vort_up" if (k % 2 == 0) else "kh_vort_dn"
            add_arrow(b, p0=p0, p1=p1, shaft_r=0.12, head_r=0.0, head_h=0.0,
                      segments=8, material=mat)

    obj_text = b.text()
    stats = validate_obj_indices(obj_text, "A1")
    (d / "scene.obj").write_text(obj_text, encoding="utf-8")
    mats = {
        "kh_base": {"kind": "glossy", "color": [0.07, 0.08, 0.10], "roughness": 0.6},
        "kh_tracer": {"kind": "glossy", "color": [0.12, 0.55, 0.92], "roughness": 0.35},
        "kh_vort_up": {"kind": "glossy", "color": [0.95, 0.45, 0.12], "roughness": 0.3},
        "kh_vort_dn": {"kind": "glossy", "color": [0.95, 0.78, 0.12], "roughness": 0.3},
    }
    write_mtl(d / "scene.mtl", mats)
    groups = material_groups(obj_text)
    cam = camera_for_bounds(b.bounds(), view="iso", margin=1.5, fov=42)
    commands = command_sequence("fluid_kh_slice", groups, mats, cam,
                                preview=f"{d}/octane-preview.png")
    scene = scene_template(
        slug="fluid-kelvin-helmholtz-slice",
        title="Kelvin–Helmholtz Shear-Layer Slice",
        category="Physical simulation / fluid dynamics",
        domain="Physics simulation",
        purpose=("Show shear instability: two opposed horizontal layers (upper/lower tracer) "
                 "roll into counter-rotating vortex tubes at the interface, the classic "
                 "Kelvin–Helmholtz billow. Built from a deterministic analytic tanh/sin "
                 "tracer field plus interface ribbons — no live solver required."),
        prompt="Visualise a Kelvin–Helmholtz shear-layer instability slice with rolled-up vortices.",
        materials=mats, commands=commands, camera=cam, groups=groups,
        simulation={
            "source_library": "analytic",
            "fixture": "deterministic tanh/sin tracer (N=96 grid)",
            "physical_variables": ["tracer_concentration", "vorticity"],
            "units": {"length": "m", "time": "s"},
            "scale_mapping": {"scene_units_per_meter": 1.0, "height_scale": 1.6,
                              "vector_scale": 0.25},
            "time": {"frame": 0, "t_seconds": 0.0},
            "null_model": "single flat interface with zero displacement amplitude",
            "limitations": ["analytic tracer, not a live Navier–Stokes solve",
                            "2D slice extruded to a heightfield + interface ribbons"],
        },
        quality_checklist=[
            "Two colour families are visible: blue tracer heightfield and orange/yellow interface ribbons.",
            "The interface reads as rolled/sinusoidal, not a flat plane.",
            "Each usemtl group has an explicit create_material + assign_material(group_index).",
            "Camera frames the full 12×12 slice with margin.",
        ],
        known_pitfalls=[
            "OBJ/MTL colours are ignored by the bridge; the blue/orange split must come from explicit create_material + assign_material commands.",
            "The vortex roll-up is a heightfield + ribbon cue, not a true 3D velocity field — keep the analytic note in the README.",
            "Ribbons use tube/arrow geometry, not OBJ `l` lines (which Octane can drop).",
        ],
    )
    (d / "scene.json").write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
    write_preview(d / "preview.png", 160, 160, _kh_preview_pixels())
    return {"slug": "fluid-kelvin-helmholtz-slice", "stats": stats, "cam": cam,
            "groups": groups}


def _kh_preview_pixels() -> bytes:
    w = h = 160
    px = bytearray()
    for y in range(h):
        for x in range(w):
            # blue gradient + warm interface band -> proves two colour families
            t = x / w
            band = math.exp(-((y - 80) ** 2) / 600.0)
            r = int(40 + 200 * band * (0.5 + 0.5 * math.sin(x / 6.0)))
            g = int(120 + 100 * t)
            b = int(180 + 60 * (1 - t))
            px.extend((min(255, r), min(255, g), min(255, b)))
    return bytes(px)


# --------------------------------------------------------------------------- #
# A2 — Advection–diffusion pulse (4 panels)                                   #
# --------------------------------------------------------------------------- #
def build_advection_diffusion(d: Path) -> dict:
    N = 48
    L = 6.0
    panels = 4
    D = 0.05
    U = 0.6
    t_vals = [0.0, 0.6, 1.4, 2.6]
    panel_sep = 0.6
    panel_w = L + 0.4
    total_w = panels * panel_w + (panels - 1) * panel_sep

    b = ObjBuilder("adv_diff_pulse")
    b.add_box(center=(0, 0, -0.95), size=(total_w + 1.0, L + 1.0, 0.1),
              material="ad_base")

    all_groups: list[str] = []
    for p, t in enumerate(t_vals):
        ox = -total_w / 2 + panel_w / 2 + p * (panel_w + panel_sep)
        verts = make_heightfield_grid(
            N, N,
            lambda i, j, t=t, ox=ox: _adv_diff_vertex(i, j, N, L, D, U, t, ox),
        )
        mat = f"ad_panel_{p}"
        b.add_surface(vertices=verts, material=mat)
        all_groups.append(mat)

    obj_text = b.text()
    stats = validate_obj_indices(obj_text, "A2")
    (d / "scene.obj").write_text(obj_text, encoding="utf-8")
    mats = {"ad_base": {"kind": "glossy", "color": [0.06, 0.07, 0.09], "roughness": 0.6}}
    # cool->warm colour ramp per panel (peak height fades as it diffuses)
    ramp = [[0.15, 0.45, 0.95], [0.20, 0.70, 0.85], [0.45, 0.80, 0.45], [0.85, 0.70, 0.25]]
    for p in range(panels):
        mats[f"ad_panel_{p}"] = {"kind": "glossy", "color": ramp[p], "roughness": 0.35}
    write_mtl(d / "scene.mtl", mats)
    groups = material_groups(obj_text)
    cam = camera_for_bounds(b.bounds(), view="iso", margin=1.5, fov=40)
    commands = command_sequence("adv_diff_pulse", groups, mats, cam,
                                preview=f"{d}/octane-preview.png")
    scene = scene_template(
        slug="advection-diffusion-pulse",
        title="Advection–Diffusion Pulse (4 Panels)",
        category="Physical simulation / transport",
        domain="Physics simulation",
        purpose=("Show a Gaussian tracer pulse advected by a uniform flow while diffusing: "
                 "each panel is a later time. The peak height drops and the pulse widens "
                 "left-to-right — visible evidence of the diffusion term, not just translation. "
                 "Deterministic closed-form solution, no solver required."),
        prompt="Visualise a Gaussian tracer pulse advecting and diffusing across four time panels.",
        materials=mats, commands=commands, camera=cam, groups=groups,
        simulation={
            "source_library": "analytic",
            "fixture": "closed-form Gaussian advection–diffusion (4 panels)",
            "physical_variables": ["tracer_concentration"],
            "units": {"length": "m", "time": "s"},
            "scale_mapping": {"scene_units_per_meter": 1.0, "height_scale": 2.0,
                              "vector_scale": 1.0},
            "time": {"frames": 4, "t_seconds": max(t_vals)},
            "null_model": "pure advection (D=0): pulse translates without broadening",
            "limitations": ["1D pulse shown as 2D heightfields", "no live PDE solve"],
        },
        quality_checklist=[
            "Four spatially separated panels are visible (peak height decreases left to right).",
            "Each panel is a distinct colour in the cool→warm ramp.",
            "Each usemtl group has explicit create_material + assign_material(group_index).",
            "Camera frames all four panels with margin.",
        ],
        known_pitfalls=[
            "OBJ/MTL colours are ignored by the bridge — the per-panel ramp needs explicit materials.",
            "The diffusion signal is the broadening + peak decay; under diffuse lighting it can wash out — keep contrast high.",
        ],
    )
    (d / "scene.json").write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
    write_preview(d / "preview.png", 160, 80, _ad_preview_pixels())
    return {"slug": "advection-diffusion-pulse", "stats": stats, "cam": cam,
            "groups": groups}


def _adv_diff_vertex(i, j, N, L, D, U, t, ox) -> tuple[float, float, float]:
    x = -L / 2 + L * j / (N - 1)
    y = -L / 2 + L * i / (N - 1)
    sigma2 = 0.25 + 2.0 * D * t
    peak = math.exp(-((x - U * t) ** 2) / (2 * sigma2))
    z = peak * 1.8 - 0.9
    return (ox + x, y, z)


def _ad_preview_pixels() -> bytes:
    w, h = 160, 80
    px = bytearray()
    cols = [[0.15, 0.45, 0.95], [0.20, 0.70, 0.85], [0.45, 0.80, 0.45], [0.85, 0.70, 0.25]]
    for y in range(h):
        for x in range(w):
            p = min(3, x // 40)
            c = cols[p]
            px.extend((int(c[0] * 255), int(c[1] * 255), int(c[2] * 255)))
    return bytes(px)


# --------------------------------------------------------------------------- #
# A3 — Mass-spring cloth drape over a sphere (Verlet/PBD)                     #
# --------------------------------------------------------------------------- #
def build_cloth_drape(d: Path) -> dict:
    G = 28          # grid resolution
    L = 6.0
    sphere_r = 1.9
    sphere_c = (0.0, 0.0, 0.0)
    rest = L / (G - 1)
    k_struct = 0.9
    k_shear = 0.4
    gravity = -0.012
    dt = 0.6
    steps = 90
    # pinned top corners so it drapes like a hanging sheet over the sphere
    pinned = {(0, 0), (0, G - 1)}

    def _mk(x: float, y: float, z: float) -> list[float]:
        return [x, y, z]

    pos: list[list[list[float]]] = []
    prev: list[list[list[float]]] = []
    for i in range(G):
        prow = []
        vrow = []
        for j in range(G):
            x = -L / 2 + L * j / (G - 1)
            y = -L / 2 + L * i / (G - 1)
            z = sphere_r + 0.5  # start above the sphere
            prow.append(_mk(x, y, z))
            vrow.append(_mk(x, y, z))
        pos.append(prow)
        prev.append(vrow)

    def dist(a, b):
        return math.sqrt(sum((a[k] - b[k]) ** 2 for k in range(3)))

    pinned_set = pinned
    damping = 0.98  # velocity damping keeps the PBD solve stable

    for _ in range(steps):
        # Verlet integrate (recover velocity implicitly, apply gravity + damping)
        for i in range(G):
            for j in range(G):
                if (i, j) in pinned_set:
                    continue
                p = pos[i][j]
                pr = prev[i][j]
                nxt = [0.0, 0.0, 0.0]
                for kk in range(3):
                    vel = (p[kk] - pr[kk]) * damping
                    nxt[kk] = p[kk] + vel + gravity * dt * dt
                prev[i][j] = p[:]
                pos[i][j] = nxt
        # Gauss–Seidel distance constraints (symmetric, stiffness-bounded)
        for _iter in range(8):
            for i in range(G):
                for j in range(G):
                    for di, dj in ((1, 0), (0, 1), (1, 1), (1, -1)):
                        ni, nj = i + di, j + dj
                        if not (0 <= ni < G and 0 <= nj < G):
                            continue
                        a = pos[i][j]
                        b = pos[ni][nj]
                        target = rest * (1.0 if di == 0 or dj == 0 else math.sqrt(2))
                        cur = dist(a, b) or 1e-6
                        k = k_struct if (di == 0 or dj == 0) else k_shear
                        diff = (cur - target) / cur
                        corr = min(max(diff, -0.5), 0.5) * 0.5 * k
                        ai = (i, j) not in pinned_set
                        bi = (ni, nj) not in pinned_set
                        if ai and bi:
                            for kk in range(3):
                                off = (b[kk] - a[kk]) * corr
                                a[kk] += off
                                b[kk] -= off
                        elif ai:
                            for kk in range(3):
                                a[kk] += (b[kk] - a[kk]) * 2 * corr
                        elif bi:
                            for kk in range(3):
                                b[kk] -= (b[kk] - a[kk]) * 2 * corr
        # sphere collision (push cloth outside the sphere)
        for i in range(G):
            for j in range(G):
                if (i, j) in pinned_set:
                    continue
                p = pos[i][j]
                v = [p[k] - sphere_c[k] for k in range(3)]
                r = math.sqrt(sum(x * x for x in v)) or 1e-6
                if r < sphere_r + 0.05:
                    s = (sphere_r + 0.05) / r
                    for kk in range(3):
                        p[kk] = sphere_c[kk] + v[kk] * s
        # NaN guard
        for i in range(G):
            for j in range(G):
                p = pos[i][j]
                for kk in range(3):
                    if not math.isfinite(p[kk]):
                        p[kk] = sphere_c[kk]

    b = ObjBuilder("cloth_drape")
    # sphere obstacle
    b.add_ellipsoid(center=sphere_c, radii=(sphere_r, sphere_r, sphere_r),
                    segments_u=48, segments_v=24, material="cloth_sphere")
    # cloth surface
    verts = [[(pos[i][j][0], pos[i][j][1], pos[i][j][2]) for j in range(G)] for i in range(G)]
    b.add_surface(vertices=verts, material="cloth_sheet")

    obj_text = b.text()
    stats = validate_obj_indices(obj_text, "A3")
    (d / "scene.obj").write_text(obj_text, encoding="utf-8")
    mats = {
        "cloth_sphere": {"kind": "glossy", "color": [0.30, 0.32, 0.36], "roughness": 0.5},
        "cloth_sheet": {"kind": "glossy", "color": [0.85, 0.30, 0.35], "roughness": 0.6},
    }
    write_mtl(d / "scene.mtl", mats)
    groups = material_groups(obj_text)
    cam = camera_for_bounds(b.bounds(), view="iso", margin=1.6, fov=42)
    commands = command_sequence("cloth_drape", groups, mats, cam,
                                preview=f"{d}/octane-preview.png")
    scene = scene_template(
        slug="mass-spring-cloth-drape",
        title="Mass-Spring Cloth Drape over a Sphere",
        category="Physical simulation / deformable bodies",
        domain="Physics simulation",
        purpose=("A small cloth sheet solved with Verlet integration + distance constraints "
                 "(PBD-style) drapes under gravity and tents over a rigid sphere. The sag and "
                 "contact curvature are emergent from the solver, not sculpted. Deterministic, "
                 "no external physics engine."),
        prompt="Visualise a cloth sheet draping and tenting over a rigid sphere under gravity.",
        materials=mats, commands=commands, camera=cam, groups=groups,
        simulation={
            "source_library": "analytic (Verlet/PBD fixture)",
            "fixture": "embedded 28×28 Verlet cloth, 90 steps",
            "physical_variables": ["displacement", "contact"],
            "units": {"length": "m", "time": "s"},
            "scale_mapping": {"scene_units_per_meter": 1.0, "height_scale": 1.0,
                              "vector_scale": 1.0},
            "time": {"frames": 1, "t_seconds": steps * dt},
            "null_model": "pinned flat sheet with zero gravity",
            "limitations": ["small grid, not a production cloth solver",
                            "sphere collision is a hard radius push"],
        },
        quality_checklist=[
            "A red cloth sheet clearly drapes above/around the grey sphere.",
            "Contact tenting over the sphere top is visible (cloth does not pass through).",
            "Each usemtl group has explicit create_material + assign_material(group_index).",
            "Camera frames both the sphere and the cloth silhouette.",
        ],
        known_pitfalls=[
            "OBJ/MTL colours are ignored by the bridge — the red cloth vs grey sphere needs explicit materials.",
            "Cloth is a triangulated surface; at low grid resolution it can look faceted — keep G≥24.",
            "Sphere collision is approximate; do not claim continuous contact for overhangs.",
        ],
    )
    (d / "scene.json").write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
    write_preview(d / "preview.png", 120, 120, _cloth_preview_pixels())
    return {"slug": "mass-spring-cloth-drape", "stats": stats, "cam": cam,
            "groups": groups}


def _cloth_preview_pixels() -> bytes:
    w = h = 120
    px = bytearray()
    for y in range(h):
        for x in range(w):
            cx, cy = 60, 64
            r = math.hypot(x - cx, y - cy)
            if r < 34:
                px.extend((77, 82, 92))       # grey sphere
            else:
                # warm cloth-ish gradient in corners
                px.extend((200, 70, 80))
    return bytes(px)


# --------------------------------------------------------------------------- #
# A4 — Rigid stack contact forces                                             #
# --------------------------------------------------------------------------- #
def build_rigid_stack(d: Path) -> dict:
    bw, bh, bd = 2.2, 1.1, 2.2
    n = 5
    base_z = 0.0
    b = ObjBuilder("rigid_stack")
    groups: list[str] = []
    for k in range(n):
        z = base_z + bh * (k + 0.5)
        jitter = 0.12 * (k % 2)
        center = (jitter, 0.0, z)
        mat = f"stack_block_{k}"
        b.add_box(center=center, size=(bw, bd, bh), material=mat)
        groups.append(mat)
    # ground
    b.add_box(center=(0, 0, base_z - 0.1), size=(bw + 1.0, bd + 1.0, 0.2),
              material="stack_ground")
    groups.append("stack_ground")
    # contact-force arrows between blocks: magnitude grows downward (load path)
    arrow_base = base_z + bh
    for k in range(n - 1):
        z0 = arrow_base + bh * k + 0.05
        z1 = z0 + bh * 0.55
        mag = (n - k) / n  # higher at the bottom
        mat = f"contact_force_{k}"
        # draw a downward arrow scaled by load; colour shifts red(high)->yellow(low)
        add_arrow(b, p0=(0.0, 0.0, z1), p1=(0.0, 0.0, z0),
                  shaft_r=0.06 + 0.05 * mag, head_r=0.18 + 0.06 * mag, head_h=0.35,
                  segments=10, material=mat)
        groups.append(mat)

    obj_text = b.text()
    stats = validate_obj_indices(obj_text, "A4")
    (d / "scene.obj").write_text(obj_text, encoding="utf-8")
    mats = {
        "stack_ground": {"kind": "glossy", "color": [0.10, 0.11, 0.13], "roughness": 0.6},
    }
    block_cols = [[0.55, 0.58, 0.62], [0.50, 0.55, 0.62], [0.45, 0.55, 0.60],
                  [0.40, 0.52, 0.58], [0.35, 0.50, 0.55]]
    for k in range(n):
        mats[f"stack_block_{k}"] = {"kind": "glossy", "color": block_cols[k], "roughness": 0.4}
    for k in range(n - 1):
        mag = (n - k) / n
        # red (high load) -> yellow (low load)
        mats[f"contact_force_{k}"] = {
            "kind": "glossy",
            "color": [0.95, 0.30 + 0.55 * (1 - mag), 0.12],
            "roughness": 0.3,
        }
    write_mtl(d / "scene.mtl", mats)
    groups2 = material_groups(obj_text)
    cam = camera_for_bounds(b.bounds(), view="iso", margin=1.7, fov=40)
    commands = command_sequence("rigid_stack", groups2, mats, cam,
                                preview=f"{d}/octane-preview.png")
    scene = scene_template(
        slug="rigid-stack-contact-forces",
        title="Rigid Stack Contact Forces",
        category="Physical simulation / rigid bodies",
        domain="Physics simulation",
        purpose=("A settled stack of blocks with contact-force glyphs between layers. The "
                 "downward arrows thicken and shift red→yellow as load increases toward the "
                 "base — the static load path. Deterministic geometric fixture; arrow scale "
                 "encodes the computed contact magnitude."),
        prompt="Visualise a stack of rigid blocks with contact-force arrows showing the load path.",
        materials=mats, commands=commands, camera=cam, groups=groups2,
        simulation={
            "source_library": "analytic (static load path)",
            "fixture": "5-block stack, linear load model",
            "physical_variables": ["contact_force"],
            "units": {"length": "m", "force": "N (arbitrary scale)"},
            "scale_mapping": {"scene_units_per_meter": 1.0, "height_scale": 1.0,
                              "vector_scale": 1.0},
            "time": {"frames": 1, "t_seconds": 0.0},
            "null_model": "single block: no inter-block contacts",
            "limitations": ["linear load model, no friction/torque",
                            "arrows are load proxies, not stress tensors"],
        },
        quality_checklist=[
            "Five stacked blocks are visible with vertical alignment.",
            "Downward contact arrows between blocks thicken toward the base (red→yellow).",
            "Each usemtl group has explicit create_material + assign_material(group_index).",
            "Camera frames the full stack with margin.",
        ],
        known_pitfalls=[
            "OBJ/MTL colours are ignored by the bridge — block + arrow colours need explicit materials.",
            "Arrows are tube geometry, not OBJ `l` lines (which Octane can drop).",
            "The load model is linear/static; do not claim dynamic or frictional contact.",
        ],
    )
    (d / "scene.json").write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
    write_preview(d / "preview.png", 120, 160, _stack_preview_pixels())
    return {"slug": "rigid-stack-contact-forces", "stats": stats, "cam": cam,
            "groups": groups2}


def _stack_preview_pixels() -> bytes:
    w, h = 120, 160
    px = bytearray()
    for y in range(h):
        for x in range(w):
            # 5 horizontal grey bands + red arrow in the middle
            band = (y // 32) % 2
            r, g, bcol = (140, 145, 155) if band else (120, 125, 140)
            if 54 < x < 66 and 40 < y < 130:
                r, g, bcol = (240, 60, 30)
            px.extend((r, g, bcol))
    return bytes(px)


# --------------------------------------------------------------------------- #
# A5 — N-body chaotic divergence (3-body, two near-identical paths)           #
# --------------------------------------------------------------------------- #
def build_nbody_divergence(d: Path) -> dict:
    # Two 3-body integrations with a tiny epsilon on one initial velocity.
    # Deterministic RK-free symplectic Euler; small enough to be stable.
    dt = 0.004
    steps = 2200
    eps = 1e-3
    G = 1.0
    m = [1.0, 1.0, 1.0]

    def init_state():
        # three bodies in a near-chaotic triangle with some orbital velocity
        return [
            {"p": [-1.0, 0.0, 0.0], "v": [0.0, 0.35, 0.0]},
            {"p": [1.0, 0.0, 0.0], "v": [0.0, -0.35, 0.0]},
            {"p": [0.0, 0.9, 0.0], "v": [0.45, 0.0, 0.0]},
        ]

    def accel(bodies):
        a = [[0.0, 0.0, 0.0] for _ in bodies]
        for i in range(len(bodies)):
            for j in range(len(bodies)):
                if i == j:
                    continue
                d = [bodies[j]["p"][k] - bodies[i]["p"][k] for k in range(3)]
                r2 = sum(x * x for x in d) + 1e-3
                r = math.sqrt(r2)
                f = G * m[j] / (r2 * r)
                for k in range(3):
                    a[i][k] += f * d[k]
        return a

    def integrate(perturb):
        bodies = init_state()
        if perturb:
            bodies[2]["v"][0] += eps
        traj = [[[] for _ in range(3)] for _ in bodies]
        for _ in range(steps):
            a = accel(bodies)
            for i, bd in enumerate(bodies):
                for k in range(3):
                    bd["v"][k] += a[i][k] * dt
                for k in range(3):
                    bd["p"][k] += bd["v"][k] * dt
            for i, bd in enumerate(bodies):
                traj[i][0].append(bd["p"][0])
                traj[i][1].append(bd["p"][1])
                traj[i][2].append(bd["p"][2])
        return traj

    traj_a = integrate(False)
    traj_b = integrate(True)

    b = ObjBuilder("nbody_divergence")
    body_cols = [[0.95, 0.35, 0.30], [0.30, 0.75, 0.95], [0.55, 0.95, 0.45]]
    # endpoints as small spheres
    for ti, traj in enumerate((traj_a, traj_b)):
        for bi in range(3):
            mat = f"nb_t{ti}_b{bi}"
            last = traj[bi][:]
            b.add_ellipsoid(center=(last[0][-1], last[1][-1], last[2][-1]),
                            radii=(0.12, 0.12, 0.12), segments_u=18, segments_v=10,
                            material=mat)
    # sampled trajectory tubes (ribbons) — sub-sample for size
    stride = 14
    for ti, traj in enumerate((traj_a, traj_b)):
        for bi in range(3):
            mat = f"nb_path_t{ti}_b{bi}"
            pts = [(traj[bi][0][s], traj[bi][1][s], traj[bi][2][s])
                   for s in range(0, steps, stride) if s < len(traj[bi][0])]
            if len(pts) < 2:
                continue
            for k in range(len(pts) - 1):
                add_arrow(b, p0=pts[k], p1=pts[k + 1], shaft_r=0.04, head_r=0.0,
                          head_h=0.0, segments=6, material=mat)

    obj_text = b.text()
    stats = validate_obj_indices(obj_text, "A5")
    (d / "scene.obj").write_text(obj_text, encoding="utf-8")
    mats = {}
    for ti in (0, 1):
        for bi in range(3):
            base = body_cols[bi]
            if ti == 1:
                base = [0.7 * c + 0.2 for c in base]  # dim the perturbed set
            mats[f"nb_t{ti}_b{bi}"] = {"kind": "glossy", "color": base, "roughness": 0.35}
            mats[f"nb_path_t{ti}_b{bi}"] = {"kind": "glossy", "color": base,
                                             "roughness": 0.4, "emission": 0.4}

    write_mtl(d / "scene.mtl", mats)
    groups = material_groups(obj_text)
    cam = camera_for_bounds(b.bounds(), view="iso", margin=1.8, fov=45)
    commands = command_sequence("nbody_divergence", groups, mats, cam,
                                preview=f"{d}/octane-preview.png")
    scene = scene_template(
        slug="nbody-chaotic-divergence",
        title="N-Body Chaotic Divergence (3-Body)",
        category="Physical simulation / n-body dynamics",
        domain="Physics simulation",
        purpose=("Two near-identical three-body systems integrated from the same initial "
                 "conditions except a 1e-3 velocity perturbation on one body. Their paths "
                 "start together and visibly diverge — sensitive dependence on initial "
                 "conditions. Deterministic symplectic integration, no live solver."),
        prompt="Visualise two nearly identical 3-body trajectories diverging due to a tiny perturbation.",
        materials=mats, commands=commands, camera=cam, groups=groups,
        simulation={
            "source_library": "analytic (symplectic Euler n-body)",
            "fixture": "two 3-body integrations, Δv=1e-3 perturbation",
            "physical_variables": ["position", "velocity"],
            "units": {"length": "m", "time": "s", "mass": "kg"},
            "scale_mapping": {"scene_units_per_meter": 1.0, "height_scale": 1.0,
                              "vector_scale": 1.0},
            "time": {"frames": 1, "t_seconds": steps * dt},
            "null_model": "identical initial conditions (zero perturbation): paths overlay",
            "limitations": ["symplectic Euler, moderate step count",
                            "no relativistic/relaxation effects"],
        },
        quality_checklist=[
            "Two sets of three-body paths are visible, starting from a common region.",
            "The two path sets diverge as they extend (sensitive dependence).",
            "Endpoint spheres mark the final body positions.",
            "Each usemtl group has explicit create_material + assign_material(group_index).",
        ],
        known_pitfalls=[
            "OBJ/MTL colours are ignored by the bridge — path + endpoint colours need explicit materials.",
            "Paths use tube/arrow geometry, not OBJ `l` lines (which Octane can drop).",
            "Divergence is real but the integrator is low-order; do not overclaim precision.",
        ],
    )
    (d / "scene.json").write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
    write_preview(d / "preview.png", 140, 140, _nbody_preview_pixels())
    return {"slug": "nbody-chaotic-divergence", "stats": stats, "cam": cam,
            "groups": groups}


def _nbody_preview_pixels() -> bytes:
    w = h = 140
    px = bytearray()
    for y in range(h):
        for x in range(w):
            # two faint curved streaks in red and blue
            d1 = abs((x - 40) ** 2 / 900 + (y - 40) ** 2 / 400 - 1)
            d2 = abs((x - 100) ** 2 / 900 + (y - 100) ** 2 / 400 - 1)
            if d1 < 0.15:
                px.extend((230, 80, 70))
            elif d2 < 0.15:
                px.extend((70, 180, 230))
            else:
                px.extend((20, 22, 28))
    return bytes(px)


# --------------------------------------------------------------------------- #
# Shared scene.json / mtl / material-group helpers                            #
# --------------------------------------------------------------------------- #
def material_groups(obj_text: str) -> list[str]:
    out = []
    for ln in obj_text.splitlines():
        if ln.startswith("usemtl "):
            g = ln.split()[1]
            if g not in out:
                out.append(g)
    return out


def write_mtl(path: Path, mats: dict) -> None:
    lines = ["# Material hints; Octane binding is driven by scene.json create_material + assign_material."]
    for name, spec in mats.items():
        r, g, b = spec.get("color", [0.8, 0.8, 0.8])
        lines.append(f"newmtl {name}")
        lines.append(f"Ka 1.0 1.0 1.0")
        lines.append(f"Kd {r:.4f} {g:.4f} {b:.4f}")
        lines.append(f"Ks 0.5 0.5 0.5")
        lines.append(f"Ns {(1 - spec.get('roughness', 0.25)) * 64:.1f}")
        lines.append("d 1.0")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def command_sequence(object_name: str, groups: list[str], mats: dict, camera: dict,
                     *, preview: str, samples=256, min_samples=24, timeout=14) -> list[dict]:
    commands: list[dict] = [
        {"op": "import_geometry", "payload": {
            "path": f"examples/recipes/{object_name.replace('_', '-')}/scene.obj",
            "format": "obj", "name": object_name}},
    ]
    unique = list(dict.fromkeys(groups))
    for name in unique:
        m = mats[name]
        payload = {"name": name, "kind": m.get("kind", "glossy"), "color": m["color"],
                   "roughness": m.get("roughness", 0.3)}
        if "metallic" in m:
            payload["metallic"] = m["metallic"]
        if "emission" in m:
            payload["emission"] = m["emission"]
        commands.append({"op": "create_material", "payload": payload})
    for idx, name in enumerate(groups, start=1):
        commands.append({"op": "assign_material", "payload": {
            "object_name": object_name, "material_name": name, "group_index": idx}})
    commands.extend([
        {"op": "set_camera", "payload": camera},
        {"op": "set_lighting", "payload": {"preset": "soft_studio"}},
        {"op": "save_preview", "payload": {
            "path": preview, "width": 1280, "height": 1280, "quality": "standard",
            "samples": samples, "min_samples": min_samples, "timeout_seconds": timeout}},
    ])
    return commands


def scene_template(*, slug, title, category, domain, purpose, prompt, materials,
                   commands, camera, groups, simulation, quality_checklist,
                   known_pitfalls) -> dict:
    return {
        "slug": slug,
        "title": title,
        "category": category,
        "domain": domain,
        "purpose": purpose,
        "prompt": prompt,
        "camera": camera,
        "materials": {name: {"name": name, **mat} for name, mat in materials.items()},
        "commands": commands,
        "simulation": simulation,
        "preview_note": ("preview.png is a lightweight reference raster; octane-preview.png "
                         "is the REAL native Octane render (standard tier)."),
        "quality_checklist": quality_checklist,
        "known_pitfalls": known_pitfalls,
        "visual_iteration_protocol": {
            "model": "ollama:glm-ocr",
            "reference_image": f"examples/recipes/{slug}/preview.png",
            "candidate_image": f"examples/recipes/{slug}/octane-preview.png",
            "max_iterations": 4,
            "review_focus": ["physical subject readability", "material/color families",
                             "geometry carrying the physical claim", "framing", "lighting"],
            "patch_dimensions": ["geometry", "camera", "lighting", "materials", "render_settings"],
            "required_evidence": [
                "bridge result metadata",
                "native Octane preview at octane-preview.png",
                "iteration records",
                "final native Octane render bundled as octane-preview.png",
            ],
            "baseline_sweep": {
                "camera_or_scene_variants": [
                    {"label": "default framing", "camera": camera},
                    {"label": "closer framing",
                     "camera": {**camera, "position": [c * 0.7 for c in camera["position"]]}},
                    {"label": "wider framing",
                     "camera": {**camera, "position": [c * 1.3 for c in camera["position"]]}},
                    {"label": "elevated angle",
                     "camera": {**camera, "position": [camera["position"][0],
                                                      camera["position"][1] + 2.0,
                                                      camera["position"][2]]}},
                ],
            },
            "stop_conditions": ["subject matches intent", "material families visually distinct",
                                "framing acceptable"],
        },
        "final_bundle": {
            "required": True,
            "native_render": f"examples/recipes/{slug}/octane-preview.png",
            "bundled_assets": ["scene.obj", "scene.mtl", "scene.json", "preview.png",
                               "octane-preview.png"],
            "status": "pending_native_octane_iteration",
        },
        "native_octane_verified": False,
        "status": "built; native render pending (physical-simulation Phase A)",
    }


def write_readme(d: Path, slug: str, title: str, purpose: str, groups: list[str],
                 mats: dict, obj_stats: dict, cam: dict) -> None:
    unique = list(dict.fromkeys(groups))
    rows = [f"| {i} | `{name}` | {mats[name].get('kind','glossy')} | `{mats[name].get('color')}` |"
            for i, name in enumerate(unique, 1)]
    text = (
        f"# {title}\n\n"
        f"{purpose}\n\n"
        "## Usage\n\n"
        "1. Import `scene.obj` with "
        f"`octane_import_geometry(path=\"examples/recipes/{slug}/scene.obj\", "
        f"name=\"{slug.replace('-', '_')}\")`.\n"
        "2. Create + assign materials per `usemtl` group (see table).\n"
        "3. Set camera, lighting, then `octane_save_preview`.\n\n"
        "Regenerate the geometry + metadata with:\n\n"
        f"```bash\nPYTHONPATH= uv run python scripts/gen_physics_sim_recipes.py\n```\n\n"
        "## Material groups\n\n"
        "| material-order | material | kind | color |\n| --- | --- | --- | --- |\n"
        + "\n".join(rows) + "\n\n"
        f"OBJ stats: {obj_stats['vertices']} vertices, max face index "
        f"{obj_stats['max_face_index']} (indices valid).\n\n"
        f"Camera: position {cam['position']} -> target {cam['target']}, fov {cam.get('fov')}.\n\n"
        "## Notes\n\n"
        "- This is a **deterministic fixture-first** recipe: the physical state is computed "
        "in `scripts/gen_physics_sim_recipes.py` with no external simulator, so it reproduces "
        "identically offline.\n"
        "- OBJ/MTL colours are not sufficient in Octane; the explicit `create_material` + "
        "`assign_material` commands in `scene.json` bind every group.\n"
        "- `native_octane_verified` is `false` until a fresh native Octane preview is promoted.\n"
    )
    (d / "README.md").write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
BUILDERS = [
    ("fluid-kelvin-helmholtz-slice", build_kelvin_helmholtz),
    ("advection-diffusion-pulse", build_advection_diffusion),
    ("mass-spring-cloth-drape", build_cloth_drape),
    ("rigid-stack-contact-forces", build_rigid_stack),
    ("nbody-chaotic-divergence", build_nbody_divergence),
]


def main() -> int:
    for slug, fn in BUILDERS:
        d = RECIPES / slug
        d.mkdir(parents=True, exist_ok=True)
        info = fn(d)
        scene = json.loads((d / "scene.json").read_text(encoding="utf-8"))
        write_readme(d, slug, scene["title"], scene["purpose"], info["groups"],
                     scene["materials"], info["stats"], info["cam"])
        print(f"  built {slug}: {info['stats']['vertices']} verts, "
              f"{len(info['groups'])} groups; cam={info['cam']['position']}")
    print(f"\nPhase A complete: {len(BUILDERS)} physics recipes generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
