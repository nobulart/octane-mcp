#!/usr/bin/env python3
"""Generate a dense, to-scale point-cloud cutaway of the solid Earth + atmosphere.

Science basis (current accepted reference-Earth model):
  * WGS84 ellipsoid: equatorial radius a = 6378.137 km, polar radius b = 6356.752 km.
    Centrifugal oblateness is modelled exactly by scaling the rotation axis (Y)
    by b/a = 0.996647 (1/298.257 flattening).
  * PREM radial layering (chemical/radial):
      inner core    0 - 1221.5 km   (solid Fe-Ni)
      outer core    1221.5 - 3480 km (liquid Fe-Ni)
      lower mantle  3480 - 5701 km
      upper mantle  5701 - 6346 km
      crust         6346 - 6371 km  (Moho at ~6346 km radius)
  * Crust is differentiated by a deterministic continent mask into:
      continental  (~35 km thick, granitic, lighter)  and
      oceanic      (~7 km thick, basaltic, darker).
  * Atmosphere (proportionally sparser point density):
      troposphere   0 - 12 km,   stratosphere 12 - 50 km,
      mesosphere    50 - 85 km,  thermosphere  85 - 600 km.
    Exosphere (no hard edge) is intentionally excluded.

Output: a single combined OBJ with per-layer `usemtl` groups (one group per
shell + one per section-face layer), a scene.mtl, and a scene.json recipe that
creates one Octane material per layer and assigns it by group index.

Render path (Octane X, sandboxed container): the committed scene.obj must be
mirrored into the container assets dir, then drained; see render_earth.py notes
or the desk-fan render workflow.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

KM = 1000.0  # 1 scene unit = 1000 km
A_EQ = 6378.137 / KM       # equatorial radius (scene units)
B_POLAR = 6356.752 / KM     # polar radius
FLAT = B_POLAR / A_EQ       # oblateness scale along rotation axis (Y)
SURFACE = 6371.0 / KM       # mean surface radius
CRUST_BASE = 6346.0 / KM    # Moho (radius)

GOLDEN_ANGLE = math.pi * (3.0 - math.sqrt(5.0))

# name, inner_km, outer_km, color(rgb 0..1), kind, roughness, extra
SOLID_LAYERS = [
    ("inner_core",   0.0,     1221.5, (1.00, 0.88, 0.40), "glossy", 0.35, {"emission": 0.40, "opacity": 0.92, "transmission": 0.06}),
    ("outer_core",   1221.5,  3480.0, (1.00, 0.42, 0.16), "glossy", 0.30, {"emission": 0.26, "opacity": 0.50, "transmission": 0.40}),
    ("lower_mantle", 3480.0,  5701.0, (0.62, 0.20, 0.10), "glossy", 0.55, {"opacity": 0.40, "transmission": 0.55}),
    ("upper_mantle", 5701.0,  6346.0, (0.78, 0.34, 0.14), "glossy", 0.48, {"opacity": 0.40, "transmission": 0.55}),
]
# crust handled separately (cont vs ocean)
CRUST_CONT_COLOR = (0.55, 0.48, 0.38)   # granitic tan
CRUST_OCEAN_COLOR = (0.16, 0.17, 0.22)  # basaltic dark

ATMOSPHERE = [
    ("troposphere",  0.0,   12.0,  (0.62, 0.80, 1.00), "specular", 0.10, {"transmission": 0.90, "ior": 1.0003, "opacity": 0.32}),
    ("stratosphere", 12.0,  50.0,  (0.42, 0.62, 1.00), "specular", 0.10, {"transmission": 0.91, "ior": 1.0003, "opacity": 0.24}),
    ("mesosphere",   50.0,  85.0,  (0.64, 0.42, 1.00), "specular", 0.10, {"transmission": 0.91, "ior": 1.0003, "opacity": 0.18}),
    ("thermosphere", 85.0,  600.0, (1.00, 0.42, 0.70), "specular", 0.10, {"transmission": 0.94, "ior": 1.0003, "opacity": 0.12}),
]

# Base point counts at DENSITY=1. The section face is deliberately denser than
# the shell (2x) so the layered cut reads clearly; the atmosphere is sparser.
SHELL_COUNTS = {
    "inner_core": 40000, "outer_core": 100000, "lower_mantle": 140000,
    "upper_mantle": 90000, "crust_cont": 800000, "crust_ocean": 800000,
    "troposphere": 22000, "stratosphere": 18000, "mesosphere": 14000, "thermosphere": 18000,
}
FACE_COUNTS = {
    "inner_core": 80000, "outer_core": 200000, "lower_mantle": 280000,
    "upper_mantle": 180000, "crust_cont": 1200000, "crust_ocean": 1200000,
    "troposphere": 40000, "stratosphere": 32000, "mesosphere": 26000, "thermosphere": 32000,
}
# Crust is emitted as a dense colour bitmap (per user): high surface density
# so the continental/oceanic tints resolve as a continuous surface rather than dots.
CRUST_SHELL_DENSITY = 2.0
CRUST_FACE_DENSITY = 2.0
ATMOSPHERE_DENSITY = 0.5  # atmosphere is proportionally less dense than solid
POINT_RADIUS_SOLID = 0.058
POINT_RADIUS_ATMO = 0.205  # soft fuzzy atmospheric shells (low opacity)
JITTER_INTERIOR = 0.018  # edge-localized particle jitter for a naturally perturbed interior
JITTER_FACE = 0.010      # smaller jitter on the flat cut face so the layering stays legible


# --------------------------------------------------------------------------
# Samplers
# --------------------------------------------------------------------------
def oblate(position: tuple[float, float, float], radius: float) -> tuple[float, float, float]:
    """Place a point at `position` (unit-ish direction) scaled to `radius`,
    with the rotation axis (Y) compressed by FLAT (centrifugal oblateness)."""
    x, y, z = position
    return (x * radius, y * radius * FLAT, z * radius)


def hemisphere_directions(count: int, phase: float = 0.0):
    """Equal-area directions on the lower hemisphere (z <= 0)."""
    for i in range(count):
        z = -(i + 0.5) / count
        horizontal = math.sqrt(max(0.0, 1.0 - z * z))
        angle = i * GOLDEN_ANGLE + phase
        yield (horizontal * math.cos(angle), horizontal * math.sin(angle), z)


def radial_point_cloud(lower_km: float, upper_km: float, radial_levels: int, directions: int, phase: float, jitter: float = 0.0) -> list:
    out = []
    inner3, outer3 = (lower_km / KM) ** 3, (upper_km / KM) ** 3
    for r_i in range(radial_levels):
        frac = (r_i + 0.5) / radial_levels
        radius = (inner3 + frac * (outer3 - inner3)) ** (1.0 / 3.0)
        for dx, dy, dz in hemisphere_directions(directions, phase=phase + r_i * 0.37):
            px, py, pz = oblate((dx, dy, dz), radius)
            if jitter > 0.0:
                # jitter scaled by the local layer thickness so particles stay inside the shell
                span = (outer3 ** (1.0 / 3.0) - inner3 ** (1.0 / 3.0)) * (KM / 1000.0) * 0.35
                j = jitter * span
                px += random.uniform(-j, j)
                py += random.uniform(-j, j)
                pz += random.uniform(-j, j)
            out.append((px, py, pz))
    return out


def shell_surface(radius_km: float, count: int, phase: float) -> list:
    radius = radius_km / KM
    return [oblate((dx, dy, dz), radius) for dx, dy, dz in hemisphere_directions(count, phase=phase)]


def section_annulus(lower_km: float, upper_km: float, count: int) -> list:
    """Dense oblate-ellipse cut face between two radii (the flat sectional disc)."""
    r0, r1 = lower_km / KM, upper_km / KM
    pts = []
    a_eq = (r0 + r1) / 2.0
    # grid over the bounding box, keep points in the annulus with oblate radii
    cells = max(8, int(math.ceil((r1 - r0) / 0.05)) + int(r1 * 60))
    step = (2.0 * r1) / cells
    for ix in range(cells + 1):
        for iy in range(cells + 1):
            x = -r1 + ix * step
            y = -r1 + iy * step
            r_eq = math.hypot(x, y)
            if r_eq < r0 or r_eq > r1:
                continue
            # oblate: a point (x,y) on the cut plane maps to surface radius r
            # where x is equatorial, y is polar -> effective radius check done above
            if (ix * cells + iy) % max(1, (cells * cells) // max(1, count)) != 0:
                continue
            pts.append((x, y * FLAT, 0.0))
            if len(pts) >= count:
                return pts
    return pts


# --------------------------------------------------------------------------
# Crust continent mask (deterministic, reproducible)
# --------------------------------------------------------------------------
def is_land(lon: float, lat: float) -> bool:
    """Coarse pseudo-continent mask from summed sinusoids (stable, no RNG)."""
    v = (
        0.50 * math.sin(1.7 * lon + 0.4) * math.cos(1.3 * lat)
        + 0.30 * math.sin(2.9 * lon - 1.1) * math.cos(2.1 * lat + 0.6)
        + 0.20 * math.sin(4.3 * lon + 2.0) * math.cos(3.7 * lat - 0.3)
    )
    return v > 0.12


def crust_class(lon: float, lat: float) -> str:
    return "crust_cont" if is_land(lon, lat) else "crust_ocean"


# --------------------------------------------------------------------------
# OBJ writing
# --------------------------------------------------------------------------
def write_sphere(lines: list[str], point: tuple[float, float, float], pr: float, base: list[int], segments: int = 4) -> None:
    x, y, z = point
    r = max(pr, 1e-4)
    # three perpendicular rings (XY, YZ, XZ) sampled at `segments` steps each
    ring: list[tuple[float, float, float]] = []
    for s in range(segments):
        a = math.tau * s / segments
        ca, sa = math.cos(a), math.sin(a)
        ring.append((x + r * ca, y + r * sa, z))
        ring.append((x, y + r * ca, z + r * sa))
        ring.append((x + r * ca, y, z + r * sa))
    start = base[0]
    for vx, vy, vz in ring:
        lines.append(f"v {vx:.5f} {vy:.5f} {vz:.5f}")
    base[0] += len(ring)
    n = segments * 3
    for s in range(segments):
        ns = (s + 1) % segments
        A, B, C = start + 3 * s, start + 3 * s + 1, start + 3 * s + 2
        D, E, F = start + 3 * ns, start + 3 * ns + 1, start + 3 * ns + 2
        tris = ((A, B, E), (A, E, D), (B, C, F), (B, F, E), (C, A, D), (C, D, F))
        for t in tris:
            lines.append(f"f {t[0]} {t[1]} {t[2]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("output_dir", type=Path)
    ap.add_argument(
        "--density",
        type=float,
        default=0.05,
        help="global point-density multiplier; 0.05 is a bounded live-render preset",
    )
    args = ap.parse_args()
    d = args.density
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    groups: dict[str, list[tuple[float, float, float]]] = defaultdict(list)

    # --- solid shell layers (jitter the interior so it reads like translucent
    #     jello rather than a rigid lattice) ---
    for name, lo, hi, _c, _k, _r, _e in SOLID_LAYERS:
        radial_levels = max(4, int(8 * d))
        directions = max(2000, int(SHELL_COUNTS[name] * d))
        groups[name].extend(radial_point_cloud(lo, hi, radial_levels, directions, phase=hash(name) % 100, jitter=JITTER_INTERIOR))

    # --- crust (surface shell, differentiated) — dense colour bitmap ---
    crust_shell = max(4000, int(SHELL_COUNTS["crust_cont"] * d * CRUST_SHELL_DENSITY))
    for dx, dy, dz in hemisphere_directions(crust_shell, phase=1.9):
        lon = math.atan2(dz, dx)
        lat = math.asin(max(-1.0, min(1.0, dy)))
        cls = crust_class(lon, lat)
        groups[cls].append(oblate((dx, dy, dz), SURFACE))

    # --- atmosphere: dense transparent instanced shells (continuous haze) ---
    # Each layer is a thin transparent surface shell at its mean altitude,
    # emitted as a dense point cloud with a large transparent specular particle
    # so it reads as a continuous sheath rather than scattered dots.
    for name, lo, hi, _c, _k, _r, _e in ATMOSPHERE:
        mid = (lo + hi) / 2.0
        cnt = max(2000, int(SHELL_COUNTS[name] * d * ATMOSPHERE_DENSITY * 4))
        groups[name].extend(shell_surface(mid, cnt, phase=hash(name) % 100))

    # --- section face (dense cut at z=0) ---
    # pre-compute crust cut classification by (x,y) using same mask via lon/lat
    def face_crust_class(x: float, y: float) -> str:
        r = math.hypot(x, y) or 1.0
        lon = math.atan2(0.0, x)  # z=0 -> seam at +/-X; acceptable on section
        lat = math.asin(max(-1.0, min(1.0, y / r)))
        return crust_class(lon, lat)

    for name, lo, hi, _c, _k, _r, _e in SOLID_LAYERS:
        cnt = max(4000, int(FACE_COUNTS[name] * d))
        for p in section_annulus(lo, hi, cnt):
            groups["face_" + name].append(p)
    # crust face band (Moho..surface), differentiated
    cnt = max(4000, int(FACE_COUNTS["crust_cont"] * d))
    for p in section_annulus(CRUST_BASE * KM, SURFACE * KM, cnt):
        x, y, z = p
        cls = face_crust_class(x, y)
        groups["face_" + cls].append(p)
    for name, lo, hi, _c, _k, _r, _e in ATMOSPHERE:
        mid = (lo + hi) / 2.0
        cnt = max(2000, int(FACE_COUNTS[name] * d * ATMOSPHERE_DENSITY))
        for p in section_annulus(mid, mid + 0.01, cnt):
            groups["face_" + name].append(p)

    # --- material + group ordering (shell then face) ---
    solid_names = [n for n, *_ in SOLID_LAYERS] + ["crust_cont", "crust_ocean"]
    atmo_names = [n for n, *_ in ATMOSPHERE]
    # Every OBJ material group has a unique label.  Reusing a label for both a
    # shell and a cut face makes the Octane importer's material-pin diagnostics
    # ambiguous and was the root cause of prior colour-collapse experiments.
    ordered = [(f"mat_{n}_shell", n) for n in solid_names] + [(f"mat_{n}_shell", n) for n in atmo_names]
    face_ordered = [(f"mat_{n}_face", "face_" + n) for n in solid_names] + [(f"mat_{n}_face", "face_" + n) for n in atmo_names]

    colors = {}
    for name, lo, hi, col, kind, rough, extra in SOLID_LAYERS:
        colors[name] = (col, kind, rough, extra)
    colors["crust_cont"] = (CRUST_CONT_COLOR, "glossy", 0.82, {})
    colors["crust_ocean"] = (CRUST_OCEAN_COLOR, "glossy", 0.60, {})
    for name, lo, hi, col, kind, rough, extra in ATMOSPHERE:
        colors[name] = (col, kind, rough, extra)

    group_specs = {
        material: colors[base]
        for material, group in ordered + face_ordered
        for base in [group.removeprefix("face_")]
        if groups.get(group)
    }

    # --- write OBJ ---
    lines = ["# Generated by octanex-mcp gen_earth_hemisphere.py", "mtllib scene.mtl", "o earth_section"]
    base = [1]
    mat_lines = []
    group_index = {}
    idx = 1
    for mat, gname in ordered + face_ordered:
        pts = groups.get(gname, [])
        if not pts:
            continue
        lines.append(f"usemtl {mat}")
        mat_lines.append(f"usemtl {mat}")
        group_index[mat] = idx
        pr = POINT_RADIUS_ATMO if mat.startswith("mat_trop") or mat.startswith("mat_strat") or mat.startswith("mat_meso") or mat.startswith("mat_therm") else POINT_RADIUS_SOLID
        for p in pts:
            write_sphere(lines, p, pr, base)
        idx += 1

    obj_path = out / "scene.obj"
    obj_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # --- scene.mtl (reference; Octane uses explicit create_material commands) ---
    mtl_lines = ["# reference materials (Octane assigns via scene.json commands)"]
    for mat, (col, _kind, _rough, _extra) in group_specs.items():
        mtl_lines.append(f"newmtl {mat}")
        mtl_lines.append(f"Kd {col[0]:.3f} {col[1]:.3f} {col[2]:.3f}")
    (out / "scene.mtl").write_text("\n".join(mtl_lines) + "\n", encoding="utf-8")

    # --- materials manifest for scene.json ---
    materials = {}
    for mat, (col, kind, rough, extra) in group_specs.items():
        payload = {"name": mat, "kind": kind, "color": list(col), "roughness": rough}
        payload.update(extra)
        materials[mat] = payload

    # --- scene.json (recipe commands) ---
    commands = [
        {"op": "import_geometry", "payload": {"path": str(out / "scene.obj"), "format": "obj", "name": "earth_section"}},
    ]
    for mat, payload in materials.items():
        commands.append({"op": "create_material", "payload": payload})
    # assign by group index (order = shell groups then face groups)
    assign_groups = []
    for mat, gname in ordered + face_ordered:
        if gname in groups and groups[gname]:
            assign_groups.append(mat)
    for gi, mat in enumerate(assign_groups, start=1):
        commands.append({"op": "assign_material", "payload": {"object_name": "earth_section", "material_name": mat, "group_index": gi}})
    commands.append({
        "op": "set_camera", "payload": {
            # Oblique ~50 deg off-axis view of the hemisphere (azimuth 50, elevation 18),
            # pulled back to frame the full cutaway including the atmospheric sheaths.
            "position": [16.0, 6.4, 20.6], "target": [0.0, 0.0, -1.0], "fov": 28.0, "focus_distance": 28.0,
        },
    })
    commands.append({"op": "set_lighting", "payload": {"preset": "soft_studio"}})
    commands.append({
        "op": "save_preview", "payload": {
            "path": str(out / "octane-preview.png"), "width": 1280, "height": 1280,
            "samples": 800, "min_samples": 200, "timeout_seconds": 240,
        },
    })

    scene = {
        "slug": out.name,
        "title": "Cutaway Earth: solid interior + atmospheric sheaths (point cloud)",
        "category": "Geoscience / planet visualization",
        "purpose": "Dense, to-scale point-cloud cutaway of the Earth's interior layers (PREM) and proportionally sparser atmospheric shells, with WGS84 centrifugal oblateness and differentiated continental/oceanic crust.",
        "camera": {"position": [16.0, 6.4, 20.6], "target": [0.0, 0.0, -1.0], "fov": 28.0, "focus_distance": 28.0},
        "materials": materials,
        "commands": commands,
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 2.0, "min_nonbg": 2.0},
            {"kind": "review_ok", "fail_on": ["mostly near-black", "very low contrast", "likely object too small", "crust not distinguishable", "atmosphere invisible"]},
        ],
        "native_octane_verified": False,
        "status": "pending live render",
    }
    (out / "scene.json").write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")

    total = sum(len(v) for v in groups.values())
    print(json.dumps({
        "obj": str(obj_path), "points": total, "vertices": base[0] - 1,
        "groups": len(assign_groups), "materials": len(materials),
    }, indent=2))


if __name__ == "__main__":
    main()
