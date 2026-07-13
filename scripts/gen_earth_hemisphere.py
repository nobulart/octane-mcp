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
POINT_RADIUS_SOLID = 0.0464  # -20% size vs v4 (0.058)
POINT_RADIUS_ATMO = 0.164    # soft fuzzy atmospheric shells (low opacity), -20% size
SPHERE_SEGMENTS = 8        # smooth spheres; 4 segments read as low-poly icosahedrons in closeup
INTERIOR_DENSITY_SCALE = 0.70 * 1.20  # -30% internal density, then +20% per request -> net -16% vs solid
JITTER_GLOBAL = 0.04       # -20% jitter vs v4 (0.05): break lattice, less smear
GLOBAL_DENSITY_SCALE = 1.20  # +20% overall particle density per request

# Reduce internal (solid-shell) density ~30% per request; crust + atmosphere unchanged.
for _n in ("inner_core", "outer_core", "lower_mantle", "upper_mantle"):
    SHELL_COUNTS[_n] = int(round(SHELL_COUNTS[_n] * INTERIOR_DENSITY_SCALE))
    FACE_COUNTS[_n] = int(round(FACE_COUNTS[_n] * INTERIOR_DENSITY_SCALE))

# --- LLSVP provinces + mantle plume tendrils (CMB-rooted thermochemical
#     upwellings; plumes initiate at LLSVP edges — see geodynamics literature) ---
LLSVP_COLOR = (0.78, 0.22, 0.52)   # magenta-plum thermochemical pile (distinct from orange core)
PLUME_COLOR = (1.00, 0.80, 0.45)   # hot gold buoyant upwelling
CMB_KM = 3480.0                     # core-mantle boundary (outer core / lower mantle)
LLSVP_HEIGHT_KM = 1300.0            # LLSVPs extend ~1000-1500 km above the CMB
PLUME_TOP_KM = 6000.0               # plumes rise to mid-upper mantle
LLSVP_BASE_COUNT = 100000           # per province (x density)
PLUME_BASE_COUNT = 35000            # per tendril (x density)


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


def _force_lower(d: tuple[float, float, float]) -> tuple[float, float, float]:
    """Force a direction into the rendered (lower) hemisphere by mirroring z<=0."""
    return (d[0], d[1], -abs(d[2]))


def _norm(v: tuple[float, float, float]) -> tuple[float, float, float]:
    n = math.hypot(*v) or 1.0
    return (v[0] / n, v[1] / n, v[2] / n)


def apply_flat(p: tuple[float, float, float]) -> tuple[float, float, float]:
    """Apply WGS84 oblateness (Y-axis compression) to an already-scaled point,
    and clamp to the rendered lower hemisphere (z <= 0) so no structure floats
    in the cut-away upper half."""
    z = min(0.0, p[2])
    return (p[0], p[1] * FLAT, z)


def _random_direction_around(center: tuple[float, float, float], max_angle: float) -> tuple[float, float, float]:
    """Rejection-sample a unit direction within `max_angle` of `center`."""
    while True:
        x, y, z = (random.uniform(-1, 1) for _ in range(3))
        n = math.hypot(x, y, z)
        if n < 1e-6:
            continue
        d = (x / n, y / n, z / n)
        dot = max(-1.0, min(1.0, d[0] * center[0] + d[1] * center[1] + d[2] * center[2]))
        if math.acos(dot) <= max_angle:
            return d


def blob_cloud(center_dir: tuple[float, float, float], angular_radius: float,
               r0_km: float, r1_km: float, count: int, phase: float = 0.0) -> list:
    """Broad, low thermochemical province: points scattered within an angular cap
    around `center_dir`, radius r0..r1 (scene units)."""
    center = tuple(center_dir)
    out = []
    r0, r1 = r0_km / KM, r1_km / KM
    while len(out) < count:
        d = _random_direction_around(center, angular_radius)
        if d[2] > 0.0:  # keep only the rendered (lower) hemisphere; else floats in cut-away space
            continue
        r = r0 + random.random() * (r1 - r0)
        out.append(apply_flat((d[0] * r, d[1] * r, d[2] * r)))
    return out


def plume_tendril(axis_dir: tuple[float, float, float], r0_km: float, r1_km: float,
                  count: int, width_km: float, freq: float, phase: float) -> list:
    """Thin, wavy conduit rising from the CMB (r0) toward the upper mantle (r1).
    Lateral meander (perpendicular to the rise axis) gives the tendril/organic
    look; a second out-of-phase offset adds curl."""
    axis = tuple(axis_dir)
    tmp = (0.0, 1.0, 0.0) if abs(axis[1]) < 0.9 else (1.0, 0.0, 0.0)
    cx = axis[1] * tmp[2] - axis[2] * tmp[1]
    cy = axis[2] * tmp[0] - axis[0] * tmp[2]
    cz = axis[0] * tmp[1] - axis[1] * tmp[0]
    nl = math.hypot(cx, cy, cz) or 1.0
    u = (cx / nl, cy / nl, cz / nl)
    vx = axis[1] * u[2] - axis[2] * u[1]
    vy = axis[2] * u[0] - axis[0] * u[2]
    vz = axis[0] * u[1] - axis[1] * u[0]
    nl2 = math.hypot(vx, vy, vz) or 1.0
    v = (vx / nl2, vy / nl2, vz / nl2)
    r0, r1 = r0_km / KM, r1_km / KM
    w, m = width_km / KM, width_km / KM
    out = []
    for i in range(count):
        t = i / max(1, count - 1)
        r = r0 + t * (r1 - r0)
        off = w * (0.4 + 0.6 * t) * math.sin(t * freq * math.tau + phase)
        off2 = m * 0.6 * math.cos(t * freq * 0.7 * math.tau + phase * 1.7)
        bx, by, bz = axis[0] * r, axis[1] * r, axis[2] * r
        px = bx + (u[0] * off + v[0] * off2)
        py = by + (u[1] * off + v[1] * off2)
        pz = bz + (u[2] * off + v[2] * off2)
        j = w * 0.25
        px += random.uniform(-j, j)
        py += random.uniform(-j, j)
        pz += random.uniform(-j, j)
        out.append(apply_flat((px, py, pz)))
    return out


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
def write_sphere(lines: list[str], point: tuple[float, float, float], pr: float, base: list[int], segments: int = SPHERE_SEGMENTS) -> None:
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
    d = args.density * GLOBAL_DENSITY_SCALE  # +20% overall particle density per request
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    groups: dict[str, list[tuple[float, float, float]]] = defaultdict(list)

    # --- solid shell layers (jitter the interior so it reads like translucent
    #     jello rather than a rigid lattice) ---
    for name, lo, hi, _c, _k, _r, _e in SOLID_LAYERS:
        radial_levels = max(4, int(8 * d))
        directions = max(2000, int(SHELL_COUNTS[name] * d))
        groups[name].extend(radial_point_cloud(lo, hi, radial_levels, directions, phase=hash(name) % 100, jitter=JITTER_GLOBAL))

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

    # --- LLSVP thermochemical provinces + mantle plume tendrils ---
    # Two broad CMB-rooted provinces (Africa / Pacific) at the base of the lower
    # mantle; thin wavy plumes rise from their edges toward the mid-upper mantle.
    llsvp_dirs = [
        _norm((0.4, -0.6, -0.7)),   # Africa-ish province (lower hemisphere, z<=0 so it's inside the cut body)
        _norm((-0.5, 0.5, -0.6)),   # Pacific-ish province (opposite side, lower hemisphere)
    ]
    # Keep both provinces inside the rendered (lower) hemisphere: if a center lands
    # in the cut-away upper half (z>0) its blob would float in empty space.
    llsvp_dirs = [_force_lower(d) for d in llsvp_dirs]
    llsvp_cnt = max(6000, int(LLSVP_BASE_COUNT * d))
    for d0 in llsvp_dirs:
        groups["llsvp"].extend(blob_cloud(d0, math.radians(42), CMB_KM, CMB_KM + LLSVP_HEIGHT_KM, llsvp_cnt, phase=hash(str(d0)) % 100))
    # 2-3 plumes per province edge, rising to mid-upper mantle with meander
    plume_cnt = max(2500, int(PLUME_BASE_COUNT * d))
    for d0 in llsvp_dirs:
        for k in range(3):
            edge = _norm(tuple(d0[i] + 0.55 * ((i + k) % 2 * 2 - 1) * 0.4 for i in range(3)))
            groups["plume"].extend(plume_tendril(edge, CMB_KM, PLUME_TOP_KM, plume_cnt, width_km=320.0, freq=2.2 + 0.3 * k, phase=k * 2.1))

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
    # LLSVP / plume on the cut face: project the 3D structures onto z=0 so the
    # cross-section also shows the thermochemical province + rising tendrils.
    face_llsvp_cnt = max(4000, int(LLSVP_BASE_COUNT * d))
    for d0 in llsvp_dirs:
        for _ in range(face_llsvp_cnt):
            dd = _random_direction_around(d0, math.radians(42))
            r = (CMB_KM + random.random() * LLSVP_HEIGHT_KM) / KM
            groups["face_llsvp"].append((dd[0] * r, (dd[1] * r) * FLAT, 0.0))
    face_plume_cnt = max(2500, int(PLUME_BASE_COUNT * d))
    for d0 in llsvp_dirs:
        for k in range(3):
            edge = _norm(tuple(d0[i] + 0.55 * ((i + k) % 2 * 2 - 1) * 0.4 for i in range(3)))
            for _ in range(face_plume_cnt):
                t = random.random()
                r = (CMB_KM + t * (PLUME_TOP_KM - CMB_KM)) / KM
                w = (320.0 / KM) * (0.4 + 0.6 * t)
                a = random.uniform(0, math.tau)
                ux, uy, uz = edge[1], -edge[0], 0.0  # crude perpendicular in-plane
                un = math.hypot(ux, uy) or 1.0
                off = w * 0.6 * random.uniform(-1, 1)
                x = edge[0] * r + (ux / un) * off
                y = edge[1] * r + (uy / un) * off
                groups["face_plume"].append((x, y * FLAT, 0.0))

    # --- material + group ordering (shell then face) ---
    # add LLSVP + plume materials/faces for ordering + colours
    solid_names = [n for n, *_ in SOLID_LAYERS] + ["crust_cont", "crust_ocean", "llsvp", "plume"]
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
    colors["llsvp"] = (LLSVP_COLOR, "glossy", 0.50, {"emission": 0.18, "opacity": 0.55, "transmission": 0.30})
    colors["plume"] = (PLUME_COLOR, "glossy", 0.35, {"emission": 0.45, "opacity": 0.92, "transmission": 0.05})
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
            # uniform positional jitter on every particle (shell/face/crust/atmo)
            # to break the golden-angle lattice and homogenize the volumes
            gx = p[0] + random.uniform(-JITTER_GLOBAL, JITTER_GLOBAL)
            gy = p[1] + random.uniform(-JITTER_GLOBAL, JITTER_GLOBAL)
            gz = p[2] + random.uniform(-JITTER_GLOBAL, JITTER_GLOBAL)
            write_sphere(lines, (gx, gy, gz), pr, base)
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
            # "Hermes Camera" off-axis framing (from the live Octane node inspector):
            # azimuth ~25deg, elevation ~35deg, pulled back ~24 units. Shows the
            # hemisphere bulge AND the layered cut face in perspective (not a head-on disc).
            "position": [-8.982154, -19.817986, 13.783353],
            "target": [-0.06247065, -0.09485492, -1.137385],
            "fov": 28.0, "focus_distance": 27.631866,
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
        "camera": {"position": [-8.982154, -19.817986, 13.783353], "target": [-0.06247065, -0.09485492, -1.137385], "fov": 28.0, "focus_distance": 27.631866},
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
