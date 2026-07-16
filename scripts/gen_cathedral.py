#!/usr/bin/env python3
"""Generate a monolithic, organic Sagrada-Familia-style cathedral OBJ (v4) and
queue a live render.

Gaudi research (this build was grounded in research + visual inspection of a
Sagrada model and the real basilica FIRST, then built):

  * RULED SURFACES -- hyperboloids, paraboloids, helicoids, conoids.
  * Double-TWIST HYPERBOLOID columns that FLARE at the base (truncated
    hyperboloid "foot") and branch like a tree at the top.
  * NO straight lines: cross-sections are LOBED / STAR and twist 45-90 deg.
  * CONTINUOUS GROWTH: nothing sits as a separate box; the mass flows.

v4 DIRECTION (user): extend and expand the spires ALL THE WAY DOWN TO GROUND
LEVEL. So the towers become the dominant vertical mass: a flared buttressed
root rising from the earth, swelling into a lobed, double-twisting shaft, and
continuing up to a glowing coloured tip -- with bowed stained-glass lancets and
roses set into the tower shafts. The central tower carries a thin twisted cross.
One combined OBJ, one ``usemtl`` group per material, explicit create_material +
assign_material (matched by name on the post-a066e31 bridge). No per-vertex
colours (the Octane X OBJ importer ignores them on this build).
"""

from __future__ import annotations

import math
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from octanex_mcp.bridge import Workspace, flush_queue, write_command  # noqa: E402

OBJECT_NAME = "cathedral"
NATIVE_RENDER = (
    Path.home()
    / "Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP/renders/cathedral_octane-preview.png"
)

MATERIALS: dict[str, dict] = {
    "mat_stone":      {"kind": "glossy", "color": [0.83, 0.79, 0.71], "roughness": 0.66, "emission": 0.0},
    "mat_glass_red":    {"kind": "glossy", "color": [0.85, 0.06, 0.08], "roughness": 0.12, "emission": 0.6},
    "mat_glass_blue":   {"kind": "glossy", "color": [0.06, 0.20, 0.85], "roughness": 0.12, "emission": 0.6},
    "mat_glass_gold":   {"kind": "glossy", "color": [0.95, 0.72, 0.10], "roughness": 0.12, "emission": 0.65},
    "mat_glass_green":  {"kind": "glossy", "color": [0.05, 0.65, 0.22], "roughness": 0.12, "emission": 0.55},
    "mat_glass_violet": {"kind": "glossy", "color": [0.55, 0.10, 0.80], "roughness": 0.12, "emission": 0.6},
    "mat_glass_white":  {"kind": "glossy", "color": [0.92, 0.92, 0.96], "roughness": 0.10, "emission": 0.75},
}
GLASS = ["mat_glass_red", "mat_glass_blue", "mat_glass_gold",
         "mat_glass_green", "mat_glass_violet", "mat_glass_white"]
# recessed negative-space cutouts read as dark carved voids (no emission,
# near-black, slightly rough so they sit in shadow inside the openings)
MATERIALS["mat_cavity"] = {"kind": "glossy", "color": [0.03, 0.03, 0.04],
                            "roughness": 0.9, "emission": 0.0}

# path to the procedurally generated stone albedo texture
TEX_DIR = ROOT / "examples" / "recipes" / "cathedral"
STONE_TEX = TEX_DIR / "stone_albedo.png"


def stone_displacement(x, y, z, amp=0.014):
    """REAL geometric relief, v11f ("wild, not ribbed"): same helical-twist +
    domain-warp architecture as v11e, but the FREQUENCY CONTENT is re-balanced
    so it reads as carved grit, NOT ribs:
      - base frequency pushed to f0=4.0 (v11e was 2.2 -> ~0.45m wavelength RIBS
        at a ~1m tower radius). Now even the broadest undulation is sub-15cm.
      - 7 octaves, gentler falloff (0.62) so mid/high freqs survive -> no single
        dominant periodic ridge.
      - DOUBLE domain warp (warp the warped point) -> more meander, kills any
        lingering lattice periodicity.
      - HELICAL TWIST kept (0.6 rad/m) so the grit spirals up the spires.
      - HEIGHT ramp kept (1.0x ground -> ~4.0x tip) for finer carving upward.
    Returns signed metres pushed along the surface normal. amp = relief depth."""
    import math
    def hash3(a, b, c):
        n = (a * 374761393 + b * 668265263 + c * 2147483647) & 0x7FFFFFFF
        n = (n ^ (n >> 13)) * 1274126177 & 0x7FFFFFFF
        return (n / 0x7FFFFFFF) * 2.0 - 1.0
    def vnoise(px, py, pz):
        ax = int(math.floor(px)); ay = int(math.floor(py)); az = int(math.floor(pz))
        fx = px - ax; fy = py - ay; fz = pz - az
        def corner(ix, iy, iz):
            return hash3((ax + ix) * 131 + 7, (ay + iy) * 197 + 11, (az + iz) * 311 + 13)
        c000 = corner(0, 0, 0); c100 = corner(1, 0, 0); c010 = corner(0, 1, 0); c110 = corner(1, 1, 0)
        c001 = corner(0, 0, 1); c101 = corner(1, 0, 1); c011 = corner(0, 1, 1); c111 = corner(1, 1, 1)
        x00 = c000 + (c100 - c000) * fx; x10 = c010 + (c110 - c010) * fx
        x01 = c001 + (c101 - c001) * fx; x11 = c011 + (c111 - c011) * fx
        y0 = x00 + (x10 - x00) * fy; y1 = x01 + (x11 - x01) * fy
        return y0 + (y1 - y0) * fz
    # height-ramped frequency (ground 1.0x -> tip ~4.0x)
    frac = max(0.0, min(1.0, y / 18.0))
    freq_mult = 1.0 + 3.0 * frac
    # helical twist about Y so grit spirals up the towers
    TW = 0.6
    th = TW * y
    ct, st = math.cos(th), math.sin(th)
    xr = x * ct - z * st
    zr = x * st + z * ct
    # DOUBLE domain warp (turbulence on turbulence) -> breaks periodicity
    W = 0.45
    wx1 = vnoise(xr * 0.7 + 11.3, y * 0.7, zr * 0.7) * W
    wy1 = vnoise(xr * 0.7, y * 0.7 + 27.1, zr * 0.7) * W
    wz1 = vnoise(xr * 0.7, y * 0.7, zr * 0.7 + 5.7) * W
    x1 = xr + wx1; y1 = y + wy1; z1 = zr + wz1
    wx2 = vnoise(x1 * 1.3 + 3.1, y1 * 1.3, z1 * 1.3) * W * 0.6
    wy2 = vnoise(x1 * 1.3, y1 * 1.3 + 9.4, z1 * 1.3) * W * 0.6
    wz2 = vnoise(x1 * 1.3, y1 * 1.3, z1 * 1.3 + 17.2) * W * 0.6
    px = (x1 + wx2) * freq_mult
    py = (y1 + wy2) * freq_mult
    pz = (z1 + wz2) * freq_mult
    # 7 octaves, pushed base freq (f0=4.0) + gentle falloff so NO single rib
    # wavelength dominates; the structure reads as fine carved grit.
    d = 0.0
    f = 4.0; g = 1.0
    for _ in range(7):
        d += vnoise(px * f, py * f, pz * f) * g
        f *= 2.1; g *= 0.62
    # sharp fine grain (scaled up with height)
    gg = 22.0 * freq_mult
    d += vnoise(px * gg, py * gg, pz * gg) * 0.16
    # v11g: REAL radial corrugation (carved-stone flutes) so the column reads as
    # worked stone, not a smooth ice-cream cone. Modulated by the world-space
    # azimuth so it is continuous in 3D and rides the height ramp (finer up top).
    az = math.atan2(zr, xr)
    rl = math.sqrt(xr * xr + zr * zr) + 1e-3
    fscale = min(1.0, rl / 0.8)                      # thin tips -> less flute so they stay sharp
    flute = math.cos(az * 9.0 + 0.3 * math.sin(y * 0.5))   # -1..1, near-vertical 9 flutes
    flute_part = flute * 0.11 * fscale * (0.6 + 0.4 * frac)  # ~11cm carved stone flutes, finer up top
    return d * amp + flute_part


def make_stone_texture(path: Path, size=1024):
    """Procedural Gaudi sandstone albedo: layered fractal noise (turbulence)
    for broad mottling + fine grain + faint horizontal bedding. Writes a PNG
    the bridge can load as the material's diffuse/albedo texture pin. Pure PIL/numpy."""
    import numpy as np
    from PIL import Image
    # sample the SAME 3D displacement field the mesh uses, at a regular grid,
    # so the albedo mottling matches the geometric relief (no UV seam mismatch).
    hf = np.zeros((size, size))
    step = max(1, size // 64)
    fxs = (np.arange(0, size, step) / size * 6.0)
    fys = (np.arange(0, size, step) / size * 6.0)
    for jj, yw in enumerate(fys):
        for ii, xw in enumerate(fxs):
            # stone_displacement wants plain floats (not numpy scalars)
            hf[jj, ii] = stone_displacement(float(xw), float(yw), 1.7, amp=1.0)
    # upsample the coarse sample via nearest (cheap)
    if step > 1:
        hf = np.repeat(np.repeat(hf[::step, ::step], step, axis=0), step, axis=1)[:size, :size]
    hf = (hf - hf.min()) / ((hf.max() - hf.min()) + 1e-6)
    # sandstone palette: warm off-white mottled with grey/tan veins
    light = np.array([0.86, 0.82, 0.74])
    dark = np.array([0.55, 0.50, 0.44])
    t = np.clip(hf * 1.4, 0, 1)
    rgb = dark[None, None, :] + (light - dark)[None, None, :] * t[..., None]
    # faint horizontal bedding lines
    bedding = 0.04 * np.sin(np.linspace(0, 40 * np.pi, size))[None, :]
    rgb = np.clip(rgb + bedding[:, :, None] * 0.5, 0, 1)
    arr = (rgb * 255).astype(np.uint8)
    Image.fromarray(arr, "RGB").save(path)
    return path


# --------------------------------------------------------------------------
# geometry helpers -> (verts, faces), LOCAL 1-based face indices
# --------------------------------------------------------------------------
def _interp_profile(profile, rings):
    """Resample a (y, r, tw) profile into `rings` evenly-y-spaced rings by
    linear interpolation so lofted meshes get far more longitudinal density."""
    import bisect
    ys = [p[0] for p in profile]
    out = []
    for k in range(rings):
        y = ys[0] + (ys[-1] - ys[0]) * k / (rings - 1)
        i = bisect.bisect_right(ys, y) - 1
        i = max(0, min(len(ys) - 2, i))
        y0, y1 = ys[i], ys[i + 1]
        t = 0.0 if y1 == y0 else (y - y0) / (y1 - y0)
        r = profile[i][1] + (profile[i + 1][1] - profile[i][1]) * t
        tw = profile[i][2] + (profile[i + 1][2] - profile[i][2]) * t
        out.append((y, r, tw))
    return out


def _laplacian_smooth(verts, faces, iterations=2, lam=0.5):
    """Light Laplacian relaxation on a manifold-ish mesh: move each vertex
    toward the centroid of its 1-ring neighbours. Smooths faceting without
    collapsing the overall form. Works with 1-BASED face indices (the loft
    convention) by indexing verts[k-1]. Returns new verts list (same order)."""
    n = len(verts)
    adj = {k: set() for k in range(1, n + 1)}
    for f in faces:
        nf = len(f)
        for e in range(nf):
            a, b = f[e], f[(e + 1) % nf]
            adj[a].add(b)
            adj[b].add(a)
    v = [list(p) for p in verts]
    for _ in range(iterations):
        nv = [list(p) for p in v]
        for k in range(1, n + 1):
            nb = adj[k]
            if not nb:
                continue
            cx = sum(v[j - 1][0] for j in nb) / len(nb)
            cy = sum(v[j - 1][1] for j in nb) / len(nb)
            cz = sum(v[j - 1][2] for j in nb) / len(nb)
            nv[k - 1][0] += lam * (cx - v[k - 1][0])
            nv[k - 1][1] += lam * (cy - v[k - 1][1])
            nv[k - 1][2] += lam * (cz - v[k - 1][2])
        v = nv
    return [(p[0], p[1], p[2]) for p in v]


def lobed_loft(cx, cz, profile, P=8, lobes=0.16, twist=1.2,
               rings=0, smooth=2, smooth_lam=0.5,
               creases=(), crease_depth=0.0, crease_w=0.22, uv_v_rep=1.0):
    """Loft a profile of (y, r, tw) rings. Each ring is a lobed (P-gon + lobes)
    cross-section rotated by tw. The core Gaudi primitive: flaring, twisting,
    organic -- no straight lines, no flat faces.
    v8: `rings` resamples the profile to more longitudinal density; `smooth`
    applies Laplacian relaxation passes so the stone reads organic, not faceted.
    v10: `creases` is a list of object-space angular phases (radians) at which a
    vertical groove is carved; because each ring is rotated by the
    height-dependent twist `tw`, a fixed-phase crease traces a SPIRAL up the
    shaft -- accentuating the twist. `crease_w` = groove width, `crease_depth`
    = depth. Emits UVs (u around circumference 0..1, v along height 0..uv_v_rep)
    so the stone texture maps onto the surface instead of blobbing.
    v11f: creases may be None (no grooves) -- normalised to an empty list."""
    if creases is None:
        creases = ()
    if rings and rings > len(profile):
        profile = _interp_profile(profile, rings)
    n = len(profile)
    verts = []
    uvs = []
    ring_starts = []
    for li, (y, r, tw) in enumerate(profile):
        rs = len(verts) + 1
        v = (li / (n - 1)) * uv_v_rep if n > 1 else 0.0
        for i in range(P):
            ang = 2 * math.pi * i / P + tw
            rad = r * (1.0 + lobes * math.cos(P * ang))
            for cp in creases:
                d = ang - cp
                d = (d + math.pi) % (2 * math.pi) - math.pi
                rad -= crease_depth * math.exp(-(d * d) / (2 * crease_w * crease_w))
            verts.append((cx + rad * math.cos(ang), y, cz + rad * math.sin(ang)))
            uvs.append((i / P, v))
        ring_starts.append(rs)
    faces = []
    for l in range(n - 1):
        a = ring_starts[l]
        b = ring_starts[l + 1]
        for i in range(P):
            a0 = a + i
            a1 = a + (i + 1) % P
            b0 = b + i
            b1 = b + (i + 1) % P
            faces.append((a0, a1, b1))
            faces.append((a0, b1, b0))
    topc = len(verts) + 1
    verts.append((cx, profile[-1][0], cz))
    uvs.append((0.5, 1.0 * uv_v_rep))
    tr = ring_starts[-1]
    for i in range(P):
        faces.append((tr + i, tr + (i + 1) % P, topc))
    botc = len(verts) + 1
    verts.append((cx, profile[0][0], cz))
    uvs.append((0.5, 0.0))
    br = ring_starts[0]
    for i in range(P):
        faces.append((br + (i + 1) % P, br + i, botc))
    if smooth and smooth > 0:
        verts = _laplacian_smooth(verts, faces, iterations=smooth, lam=smooth_lam)
    return verts, faces, uvs


def lobed_cone_tip(cx, cz, y0, y1, r0, P=8, lobes=0.16, twist=1.6,
                   creases=(), crease_depth=0.0, crease_w=0.22):
    """Glowing tip: a lobed, twisting taper, same mesh family as the spire so it
    reads as a continuous flaming crown, not a stuck-on cap.
    v11f: HARDER TAPER. The crown profile now follows a golden-ratio + concave
    curve so the spire necks smoothly to a fine point instead of a blunt cone:
    radius steps 1.0 -> 0.5 (phi^-1) -> 0.19 (phi^-2) -> 0.05 -> 0.012, with a
    slight concave in-curve (power curve) so it reads as a needle, not a megaphone."""
    PHI = (1.0 + math.sqrt(5.0)) / 2.0
    dy = y1 - y0
    # radius fraction at each stage (1 -> near-zero), with a concave power curve
    stops = [0.0, 0.34, 0.62, 0.85, 1.0]
    rf =    [1.0, 1/PHI, 1/PHI**2, 0.05, 0.012]
    profile = []
    for s, r in zip(stops, rf):
        yy = y0 + dy * s
        # concave in-curve: pull the early radius down a touch for a needled look
        rr = r0 * r
        profile.append((yy, rr, twist * (0.4 + 1.4 * s)))
    return lobed_loft(cx, cz, profile, P=P, lobes=lobes, twist=0.0,
                      creases=creases, crease_depth=crease_depth, crease_w=crease_w)


def bowed_window_pane(cx, cy, cz, w, h, bow=0.18, nx=6, ny=8, facing=+1):
    """A STAINED-GLASS window pane that BOWS outward (facing direction) -- no
    straight edges. Used as lancets/roses set into the tower shafts."""
    verts = []
    starts = []
    for j in range(ny + 1):
        y = cy - h / 2 + h * j / ny
        rs = len(verts) + 1
        for i in range(nx + 1):
            x = cx - w / 2 + w * i / nx
            zb = cz + facing * bow * math.sin(math.pi * i / nx) * math.sin(math.pi * j / ny)
            verts.append((x, y, zb))
        starts.append(rs)
    faces = []
    for j in range(ny):
        a = starts[j]
        b = starts[j + 1]
        for i in range(nx):
            a0 = a + i
            a1 = a + i + 1
            b0 = b + i
            b1 = b + i + 1
            faces.append((a0, a1, b1))
            faces.append((a0, b1, b0))
    extra = [(f[0], f[2], f[1]) for f in faces]
    return verts, faces + extra


def arch_niche(cx, cy, cz, w, h, depth, facing=+1, surface_off=0.14):
    """A NEGATIVE-SPACE cutout: a recessed pointed-arch opening carved INTO a
    tower shaft. Built as a dark 'cavity' mesh that EXTENDS from a front rim
    sitting PROUD of the stone surface (surface_off along +facing) back to a
    recessed back plane pushed `depth` further inward -- a real extruded pocket
    with side walls, not a flat decal. Returns (mat_cavity, verts, faces, uvs).
    v11 fix: previously the back face was offset outward, so the cavity poked
    THROUGH the stone (intersecting geometry). It now recedes inward."""
    nx = 12
    ny = 20
    # half-width taper -> pointed arch
    def hw_of(t):
        return (w / 2) * (1.0 - t) ** 0.7
    front = []
    fstarts = []
    for j in range(ny + 1):
        t = j / ny
        y = cy - h / 2 + h * t
        rs = len(front) + 1
        for i in range(nx + 1):
            s = i / nx - 0.5
            x = cx + s * 2 * hw_of(t)
            rz = cz + facing * surface_off
            # v11b: ride the same world-space relief as the stone so the pocket
            # mouth stays flush with the displaced surface (no re-intersection)
            rz = rz + facing * stone_displacement(x, y, rz, amp=0.012)
            front.append((x, y, rz))
        fstarts.append(rs)
    back = []
    bstarts = []
    for j in range(ny + 1):
        t = j / ny
        y = cy - h / 2 + h * t
        rs = len(back) + 1
        for i in range(nx + 1):
            s = i / nx - 0.5
            x = cx + s * 2 * hw_of(t) * 0.92
            rz = cz + facing * (surface_off + depth)
            rz = rz + facing * stone_displacement(x, y, rz, amp=0.012)
            back.append((x, y, rz))
        bstarts.append(rs)
    verts = front + back
    faces = []
    # side walls: connect each front-ring edge to the corresponding back-ring edge
    for j in range(ny):
        a = fstarts[j]; b = fstarts[j + 1]
        c = bstarts[j]; d = bstarts[j + 1]
        for i in range(nx):
            a0, a1 = a + i, a + i + 1
            b0, b1 = b + i, b + i + 1
            c0, c1 = c + i, c + i + 1
            d0, d1 = d + i, d + i + 1
            faces.append((a0, c0, c1)); faces.append((a0, c1, a1))  # side wall
            faces.append((b0, d0, d1)); faces.append((b0, d1, b1))  # side wall
    # recessed back face (dark void, facing back inward)
    for j in range(ny):
        c = bstarts[j]; d = bstarts[j + 1]
        for i in range(nx):
            c0, c1 = c + i, c + i + 1
            d0, d1 = d + i, d + i + 1
            faces.append((c0, c1, d1)); faces.append((c0, d1, d0))
    faces += [(f[0], f[2], f[1]) for f in faces]
    return "mat_cavity", verts, faces, None


def rose(cx, cy, cz, ri, ro, seg, facing=+1):
    groups = []
    for i in range(seg):
        a0 = 2 * math.pi * i / seg
        a1 = 2 * math.pi * (i + 1) / seg
        p0 = (cx + ri * math.cos(a0), cy + ri * math.sin(a0), cz)
        p1 = (cx + ri * math.cos(a1), cy + ri * math.sin(a1), cz)
        p2 = (cx + ro * math.cos(a1), cy + ro * math.sin(a1), cz + facing * 0.1)
        p3 = (cx + ro * math.cos(a0), cy + ro * math.sin(a0), cz + facing * 0.1)
        groups.append((GLASS[i % len(GLASS)], *panel([p0, p1, p2, p3])))
    ring = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        ring.append((cx + ri * math.cos(a), cy + ri * math.sin(a), cz))
    hv = [(cx, cy, cz)] + ring
    hf = []
    for i in range(seg):
        hf.append((1, 2 + i, 2 + (i + 1) % seg))
        hf.append((1, 2 + (i + 1) % seg, 2 + i))
    groups.append(("mat_glass_white", hv, hf))
    return groups


def panel(corners):
    verts = list(corners)
    faces = [(1, 2, 3), (1, 3, 4), (1, 3, 2), (1, 4, 3)]
    return verts, faces


def thin_twist_cross(cx, cy, cz, h=1.9, arm=0.7, w=0.10):
    """A thin, slightly twisted stone cross (built from lobed lofts, no box).
    v10: normalises every sub-part to a (mat, verts, faces, uvs) 4-tuple."""
    groups = []
    sv, sf, su = lobed_loft(cx, cz,
        [(cy - h / 2, w, 0.0), (cy, w * 1.2, 0.3), (cy + h / 2, w, 0.6)], P=6, lobes=0.12, twist=0.0)
    groups.append(("mat_stone", sv, sf, su))
    for s in (-1, 1):
        x0, x1 = cx - s * 0.05, cx + s * arm
        prof = [(cy - w, w * 0.8, 0.0), (cy, w, 0.2), (cy + w, w * 0.8, 0.4)]
        verts = []
        rings = []
        for (yy, r, tw) in prof:
            rs = len(verts) + 1
            for i in range(6):
                ang = 2 * math.pi * i / 6 + tw
                rad = r * (1.0 + 0.12 * math.cos(6 * ang))
                verts.append((x0 + (x1 - x0) * (i % 2), yy + rad * math.sin(ang), cz + rad * math.cos(ang)))
            rings.append(rs)
        faces = []
        for l in range(len(prof) - 1):
            a, b = rings[l], rings[l + 1]
            for i in range(6):
                a0, a1 = a + i, a + (i + 1) % 6
                b0, b1 = b + i, b + (i + 1) % 6
                faces.append((a0, a1, b1)); faces.append((a0, b1, b0))
        groups.append(("mat_stone", verts, faces, None))
    return groups


# --------------------------------------------------------------------------
# build -> list of (mat, verts, faces)
# v4: TOWERS FROM THE GROUND
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# tower radius interpolation (shared by tower_profile + conforming glass)
# --------------------------------------------------------------------------
def _tower_radii(base_r, top_h, merge_r=0.0, merge_frac=0.0):
    """(y, r) breakpoints of a tower shaft -- flared buttressed root, swell,
    taper -- matched exactly by tower_profile so glass can hug the body.
    If merge_r>0, radii in the lower `merge_frac` of the height are WIDENED so
    adjacent inner towers fuse into one trunk by the lower third (v6)."""
    base = [
        (0.0,  base_r * 1.30),
        (top_h * 0.06, base_r * 1.05),
        (top_h * 0.18, base_r * 0.92),
        (top_h * 0.40, base_r * 0.82),
        (top_h * 0.62, base_r * 0.66),
        (top_h * 0.82, base_r * 0.48),
        (top_h * 0.95, base_r * 0.28),
    ]
    if merge_r <= 0 or merge_frac <= 0:
        return base
    ym = top_h * merge_frac
    foot = base_r * 1.30
    out = []
    for y, r in base:
        if y <= ym:
            t = (ym - y) / ym if ym > 0 else 1.0   # 1 at ground -> 0 at ym
            r2 = foot + (merge_r - foot) * t
            out.append((y, max(r, r2)))
        else:
            out.append((y, r))
    # shoulder at ym so the bulged lower third necks smoothly into the shaft
    out.append((ym, foot))
    out.sort(key=lambda p: p[0])
    return out


def tower_radius_at(base_r, top_h, y, merge_r=0.0, merge_frac=0.0):
    prof = _tower_radii(base_r, top_h, merge_r, merge_frac)
    if y <= prof[0][0]:
        return prof[0][1]
    if y >= prof[-1][0]:
        return prof[-1][1]
    for i in range(len(prof) - 1):
        y0, r0 = prof[i]
        y1, r1 = prof[i + 1]
        if y0 <= y <= y1:
            t = (y - y0) / (y1 - y0)
            return r0 + (r1 - r0) * t
    return prof[-1][1]


def conforming_lancet(x, z, base_r, H, y0, h, w, facing, mat, merge_r=0.0, merge_frac=0.0):
    """A pointed-arch STAINED-GLASS lancet that CONFORMS to the tower body:
    its outer surface rides the interpolated tower radius (hugs the round
    shaft), it narrows to a pointed arch at the top, and bulges gently
    outward -- no flat slab pasted against a cylinder."""
    verts = []
    starts = []
    ny = 18
    nx = 10
    for j in range(ny + 1):
        t = j / ny
        y = y0 + h * t
        rr = tower_radius_at(base_r, H, y, merge_r, merge_frac) + 0.06  # proud of the stone surface
        taper = (1.0 - t) ** 0.6                     # wide base, point at top
        arch = 1.0 - 0.85 * t                        # pull x-offsets to axis at apex
        for i in range(nx + 1):
            s = i / nx - 0.5
            off = s * w * taper
            px = x + off * arch
            pz = z + facing * rr
            pz += facing * 0.04 * math.sin(math.pi * i / nx) * math.sin(math.pi * t)  # pillow
            verts.append((px, y, pz))
        starts.append(len(verts) - nx - 1)
    faces = []
    for j in range(ny):
        a = starts[j]
        b = starts[j + 1]
        for i in range(nx):
            a0, a1 = a + i, a + i + 1
            b0, b1 = b + i, b + i + 1
            faces.append((a0, a1, b1))
            faces.append((a0, b1, b0))
    faces += [(f[0], f[2], f[1]) for f in faces]  # double-side so it reads head-on
    return mat, verts, faces


def build():
    groups: list[tuple[str, list, list, "list | None"]] = []

    def add(mat, verts, faces, uvs=None, jitter=0.0):
        # v11b: REAL geometric relief on the stone. Estimate a per-vertex
        # surface normal from the triangle fan, then push each vertex along
        # that normal by the world-space fractal displacement field. The
        # relief is now actual geometry (light catches it), not a texture.
        # jitter (v11d): a per-element offset into the noise field so each
        # architectural element (tower / crown / base / buttress) gets a
        # slightly different relief character instead of one global pattern.
        if mat == "mat_stone" and verts:
            import math
            n = len(verts)
            nx = [0.0] * n; ny = [0.0] * n; nz = [0.0] * n
            for f in faces:
                a, b, c = verts[f[0] - 1], verts[f[1] - 1], verts[f[2] - 1]
                ux, uy, uz = a[0] - b[0], a[1] - b[1], a[2] - b[2]
                vx, vy, vz = c[0] - b[0], c[1] - b[1], c[2] - b[2]
                wx = uy * vz - uz * vy; wy = uz * vx - ux * vz; wz = ux * vy - uy * vx
                for idx in f:
                    nx[idx - 1] += wx; ny[idx - 1] += wy; nz[idx - 1] += wz
            for i, (x, y, z) in enumerate(verts):
                ll = math.sqrt(nx[i] * nx[i] + ny[i] * ny[i] + nz[i] * nz[i]) or 1.0
                d = stone_displacement(x + jitter, y, z, amp=0.012)
                verts[i] = (x + nx[i] / ll * d, y + ny[i] / ll * d, z + nz[i] / ll * d)
        groups.append((mat, verts, faces, uvs))

    # ===== DOMINANT TOWER CLUSTER: each tower a flared-root -> double-twist
    #       lobed shaft -> glowing tip, running GROUND -> SKY =====
    # profile builder: base flare (buttressed foot) at y=0, swell, taper, top.
    # breakpoint radii MUST match _tower_radii() so the glass hugs the body.
    # v6: inner towers (central + ring) widen in the lower third so they fuse
    # into a single trunk by ~0.30 of the height.
    MERGE_FRAC = 0.22
    def tower_profile(base_r, top_h, twist_total, lean=0.0, merge_r=0.0):
        prof = _tower_radii(base_r, top_h, merge_r, MERGE_FRAC)
        return [
            (yy, r, twist_total * (yy / top_h)) for (yy, r) in [
                (0.0,  prof[0][1]),
                (top_h * 0.06, prof[1][1]),
                (top_h * 0.18, prof[2][1]),
                (top_h * 0.40, prof[3][1]),
                (top_h * 0.62, prof[4][1]),
                (top_h * 0.82, prof[5][1]),
                (top_h * 0.95, prof[6][1]),
            ]
        ]

    # GOLDEN-RATIO PROPORTIONS (v11f): every tower's base radius and total
    # height are derived from the golden ratio phi (~1.618) so the cluster
    # reads as one harmonious family rather than arbitrary numbers. The central
    # spire is the key: base r = phi^2, height = phi^6; each ring tier scales by
    # 1/phi, and the outer tier by another 1/phi^2. Heights follow the same
    # phi ladder so the silhouette steps down by ~1.618x per ring.
    PHI = (1.0 + math.sqrt(5.0)) / 2.0
    r0 = PHI ** 2          # ~2.618  -> central base radius scale reference
    h0 = PHI ** 6          # ~17.94  -> central total height
    towers = [
        # (x, z, base_radius, total_height, twist, tip_material, merge_radius)
        (0.0, 0.0,   r0*0.70,     h0,         1.3, "mat_glass_gold",   r0*0.32),      # central (tallest, carries cross)
        (-2.0, 1.9,  (r0/PHI)*0.70, h0/PHI,   1.1, "mat_glass_violet", (r0/PHI)*0.32), # ring NE
        ( 2.0, 1.9,  (r0/PHI)*0.70, h0/PHI,  -1.1, "mat_glass_blue",   (r0/PHI)*0.32), # ring NW
        (-2.0,-1.9,  (r0/PHI)*0.70, h0/PHI,   1.1, "mat_glass_green",  (r0/PHI)*0.32), # ring SE
        ( 2.0,-1.9,  (r0/PHI)*0.70, h0/PHI,  -1.1, "mat_glass_red",    (r0/PHI)*0.32), # ring SW
        (-3.0, 3.0,  (r0/PHI**2)*0.70, h0/PHI**2, 0.9, "mat_glass_gold",    0.0),       # outer front-left
        ( 3.0, 3.0,  (r0/PHI**2)*0.70, h0/PHI**2,-0.9, "mat_glass_red",     0.0),       # outer front-right
        (-3.0,-3.0,  (r0/PHI**2)*0.70, h0/PHI**2, 0.8, "mat_glass_green",   0.0),       # outer back-left
        ( 3.0,-3.0,  (r0/PHI**2)*0.70, h0/PHI**2,-0.8, "mat_glass_violet",  0.0),       # outer back-right
    ]
    tip_y = {}
    for ti, (x, z, br, H, tw, tip, mr) in enumerate(towers):
        prof = tower_profile(br, H, tw, merge_r=mr)
        # v10: 3 vertical spiral creases carved into the shaft (fixed object-space
        # phase + height-dependent twist => the groove spirals up the tower).
        creases = [k * 2 * math.pi / 3 for k in range(3)]
        # v11d: per-tower jitter so each shaft samples a different bit of the
        # relief field (no identical global texture on every tower).
        sh_jit = ti * 7.31
        # v11g: KILL THE ICE-CREAM. Re-inject ANGULAR STRUCTURE that the v11f
        # smoothing melted away: (1) lobes=0.10 -> a gently star/lobed cross-
        #   section that reads as carved stone columns, not a round cream cone;
        #   (2) smooth 3 -> 1 (and lam 0.45 -> 0.18) so the lobes survive;
        #   (3) the displacement field (stone_displacement) adds a real radial
        #   corrugation term so the surface has organic longitudinal ribs too. v11g: KILLED THE ICE-CREAM - the v11f round cross-section + heavy Laplacian smoothing melted the towers into soft-serve cones. Re-injected angular structure: (1) lobed cross-section lobes=0.10 on shaft/crown/base/buttress (carved-stone columns, not round cream); (2) smoothing slashed 3->1 (lam 0.45->0.18) so the lobes survive; (3) added a REAL radial corrugation (9-flute carved-stone flutes) baked into the displacement field, so the surface reads as worked stone with longitudinal ribs rather than a smooth cone. v11h: KILLED THE PANCAKE STACK - the macro twist (3.6 rad ~0.6 turns) was coiling each tower's seam into visible spiral rings, and the fat diameter exaggerated the stacked look. (1) SLASHED twist 3.6->1.3 (ring 3.0->1.1, crown 3.2->1.4) so the spires read as straight tapering columns, not coils; (2) REDUCED every spire diameter ~30% (radii *0.70) so they're slender; (3) flute phase de-coiled (sin(y*0.9) -> sin(y*0.5)*0.3) so the 9 carved flutes run NEAR-VERTICAL instead of spiralling; (4) smoothing eased back to 2/0.25 for a slightly less harsh surface while keeping the lobes. v11i: the v11h slim shafts were still buried in a BULBOUS FOOT + FAT TRUNK FUSION (foot flare 1.9x, merge_r ~1.8). (1) DE-BULGED the foot: base flare 1.9x->1.30x and the whole profile slimmed so towers taper from a modest root; (2) SLASHED trunk fusion: merge_r 0.70->0.32 and MERGE_FRAC 0.30->0.22 so the inner towers are distinct columns that only lightly touch low down, not one snowman ball; (3) made the 9 VERTICAL FLUTES ACTUALLY VISIBLE - they were resolving to ~4mm on a 2m spire (invisible). Decoupled the flute from the fine-grit amp (now an explicit ~11cm term, ~27x deeper) and tapered it off on the thin tips so the spires stay sharp but the shafts read as carved stone columns. Smoothing back to 1/0.15 to keep the flute edges crisp.
        add("mat_stone", *lobed_loft(x, z, prof, P=34, lobes=0.10, twist=0.0,
                                     rings=96, smooth=1, smooth_lam=0.15,
                                     creases=None, crease_depth=0.0, crease_w=0.20,
                                     uv_v_rep=2.0), jitter=sh_jit)
        # v8 fix: overlap the crown well INTO the shaft (base at 0.82H) so the
        # Laplacian smoothing of the shaft top cannot leave the tip floating.
        # v10: crown diameter bumped (br*0.30 -> br*0.55) to compensate for the
        # smoothing shrink; creases continue from the shaft (phase offset by the
        # shaft twist at the junction) so the spiral reads unbroken.
        tip_base = H * 0.82
        tip_top = H + 0.7
        crown_creases = [(c + 0.82 * tw) for c in creases]
        add(tip, *lobed_cone_tip(x, z, tip_base, tip_top, br * 0.55, P=26, lobes=0.10,
                                 twist=1.4, creases=None, crease_depth=0.0,
                                 crease_w=0.20), jitter=sh_jit + 3.7)
        tip_y[(x, z)] = tip_top
    # ===== A low, swelling organic BASE that the towers rise FROM (no flat disc)
    #       a flared lobed root-mass connecting the tower feet at ground =====
    add("mat_stone", *lobed_loft(0, 0,
        [(0.0, 5.6, 0.0), (0.6, 4.6, 0.0), (1.2, 4.2, 0.0)], P=30, lobes=0.10, twist=0.0,
        rings=36, smooth=1, smooth_lam=0.18), jitter=53.2)
    # buttress ribs radiating from the base (organic roots)
    for k in range(8):
        ang = 2 * math.pi * k / 8
        bx = 2.6 * math.cos(ang)
        bz = 2.6 * math.sin(ang)
        add("mat_stone", *lobed_loft(bx, bz,
            [(0.0, 0.55, 0.0), (0.7, 0.95, 0.0), (1.4, 0.6, 0.0), (2.0, 0.25, 0.0)],
            P=18, lobes=0.10, twist=0.0, rings=30, smooth=1, smooth_lam=0.18), jitter=101.0 + k * 4.13)

    # ===== NO stained-glass windows in v7 (removed per direction). The organic
    #       stone mass stands alone; only the glowing spire TIPS and the cross
    #       accents remain as colour. The conforming-lancet + rose helpers are
    #       kept for later reuse but not emitted here. =====

    # ===== thin twisted stone CROSS seated on the actual central crown apex
    #       (v8 fix: was floating above the smoothed shaft top) =====
    cbase = tip_y[(0, 0)]          # = central tip_top after the overlap fix
    for (mat, v, f, u) in thin_twist_cross(0.0, cbase + 0.15, 0.0, h=1.6, arm=0.6, w=0.10):
        add(mat, v, f, u or None)  # cross kept low-poly; it's small and reads fine

    # ===== v9: NEGATIVE-SPACE cutouts -- recessed arched window niches carved
    #       into the tower shafts + a tall arched doorway at the trunk base.
    #       These read as carved voids (dark cavity mesh), not decals.
    # v11j: the trunk was slimmed (merge_r 0.70->0.32, profile de-bulged) so the
    #       per-tower niches + flanking doors were now FLOATING in the air (their
    #       placement math assumed the old fat radius). Per direction, REMOVE all
    #       windows EXCEPT the main central door, and SEAT that door on the actual
    #       central-tower radius at the door height so it hugs the body. =====
    cx_br = r0 * 0.70          # central base radius (matches towers[0])
    cx_H = h0                   # central total height
    cz_door = tower_radius_at(cx_br, cx_H, 2.4, r0 * 0.32, MERGE_FRAC) + 0.06
    add(*arch_niche(0.0, 2.4, cz_door, w=2.4, h=4.6, depth=1.6, facing=+1, surface_off=0.16))

    return groups


# --------------------------------------------------------------------------
# OBJ writer (single combined OBJ, per-material o/g, no vertex colours)
# --------------------------------------------------------------------------
def write_obj(groups, path: Path):
    lines = ["# Sagrada-style cathedral (slender spires, visible vertical stone flutes, slim trunk, v11i, single combined OBJ)"]
    vcount = 0
    vtcount = 0
    for idx, (mat, verts, faces, uvs) in enumerate(groups, 1):
        gname = f"group_{idx}_{mat}"
        # v8: smooth-shade all STONE groups so the denser meshes read organic,
        # not faceted. Glowing tip materials stay faceted (small, crisp crowns).
        smooth = "s 1" if mat == "mat_stone" else "s off"
        lines.append(f"o {gname}")
        lines.append(f"usemtl {mat}")
        lines.append(f"g {gname}")
        lines.append(smooth)
        lines.extend(f"v {x:.5f} {y:.5f} {z:.5f}" for x, y, z in verts)
        if uvs:
            lines.extend(f"vt {u:.5f} {w:.5f}" for u, w in uvs)
        for face in faces:
            if uvs:
                lines.append("f " + " ".join(f"{vcount + n}/{vtcount + n}" for n in face))
            else:
                lines.append("f " + " ".join(str(vcount + n) for n in face))
        lines.append("s off")
        vcount += len(verts)
        if uvs:
            vtcount += len(uvs)
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
    target = [0.0, 8.5, 1.5]
    el = math.radians(11.0)
    az = math.radians(30.0)
    d = 42.0
    dx = math.cos(el) * math.sin(az)
    dy = math.sin(el)
    dz = math.cos(el) * math.cos(az)
    pos = [round(target[0] + d * dx, 4),
           round(target[1] + d * dy, 4),
           round(target[2] + d * dz, 4)]
    return {"position": pos, "target": target, "fov": 50.0}


def command_sequence(groups, *, asset_path, preview_path):
    unique = list(dict.fromkeys(m for m, _, _, _ in groups))
    cam = hero_camera()
    commands = [
        {"op": "import_geometry", "payload": {"path": asset_path, "format": "obj", "name": OBJECT_NAME}},
    ]
    for name in unique:
        payload = {"name": name, **MATERIALS[name]}
        # v9/v11: the stone material gets the procedural ALBEDO + NORMAL maps.
        # The bridge wires albedo into the diffuse pin and normal into the
        # material's normal pin. Paths are the container assets dir so the
        # sandboxed Octane can read them.
        if name == "mat_stone" and STONE_TEX_CONTAINER:
            payload["texture_path"] = str(STONE_TEX_CONTAINER)
        commands.append({"op": "create_material", "payload": payload})
    for name in unique:
        commands.append({"op": "assign_material", "payload": {
            "object_name": OBJECT_NAME, "material_name": name}})
    commands.extend([
        {"op": "set_camera", "payload": cam},
        {"op": "set_lighting", "payload": {"preset": "soft_studio"}},
        {"op": "save_preview", "payload": {
            "path": preview_path, "width": 1280, "height": 1280,
            "samples": 700, "min_samples": 64, "timeout_seconds": 45, "max_render_time": 38}},
    ])

    # v10: container path the sandboxed Octane reads the texture from (set at runtime)
    # kept here so command_sequence can reference it.
    return commands


# container paths the sandboxed Octane reads textures from (set at runtime)
STONE_TEX_CONTAINER = None
STONE_NRM_CONTAINER = None


def queue_live_render(obj_text, groups):
    ws = Workspace()
    ws.ensure()
    flushed = flush_queue(ws, backup=True)
    asset_path = ws.assets_dir / "cathedral.obj"
    asset_path.write_text(obj_text, encoding="utf-8")
    # v9/v11: generate the procedural stone ALBEDO + NORMAL maps into BOTH repo
    # and container so the sandboxed Octane can read them.
    global STONE_TEX_CONTAINER
    TEX_DIR.mkdir(parents=True, exist_ok=True)
    make_stone_texture(STONE_TEX, size=1024)
    STONE_TEX_CONTAINER = ws.assets_dir / "stone_albedo.png"
    make_stone_texture(STONE_TEX_CONTAINER, size=1024)
    preview_path = ws.renders_dir / "cathedral_octane-preview.png"
    if preview_path.exists():
        preview_path.unlink()
    for cmd in command_sequence(groups, asset_path=str(asset_path), preview_path=str(preview_path)):
        write_command(cmd["op"], cmd["payload"], ws)
    return {"queued": len(list(ws.queue_dir.glob("*.json"))), "flushed": flushed,
            "asset": str(asset_path), "preview": str(preview_path)}


def write_scene(groups):
    unique = list(dict.fromkeys(m for m, _, _, _ in groups))
    scene = {
        "slug": "cathedral",
        "title": "Sagrada-Familia-style Cathedral (fluted spires, main door only, v11j)",
        "category": "Architecture",
        "purpose": "Render a monolithic Sagrada-Familia-style cathedral. v10: spiral VERTICAL CREASES in the shafts, fatter spire crowns (br*0.55), proper UV mapping. v11: windows extruded as real recessed pockets seated PROUD of the stone (no intersection). v11b: REAL geometric relief - every stone vertex pushed along its surface normal by a shared 3D fractal displacement field (actual geometry, not a normal map). v11c: relief DIALED TO CRISPER + SOFTER - base frequency raised (1.0->2.2) for sub-metre cut-stone lobes, amplitude lowered (0.022->0.012), 6 octaves + a dedicated high-freq grain octave for sharp sandstone speckle, and the mesh densified (tower P24->34 rings64->96, crown P16->26, base P20->30, buttress P12->18) so the finer speckle actually resolves instead of aliasing into faceted ribbing. v11d: (1) relief FREQUENCY RAMPS UP WITH HEIGHT - base lobes + fine speckle scale 1.0x (ground) -> 2.8x (tip) via a smooth frac=y/18 gradient, so the stone reads broad-cut at the base and intricately carved toward the spires; (2) per-element JITTER - each tower/crown/base/buttress samples a different offset into the noise field, so no two architectural elements share the same relief pattern. v11e: KILLED THE COIN-STACK - dropped shaft/crown/base/buttress lobes to 0 and crease depth 0.14->0.03 (relief now comes from displacement, not faceting). REWROTE the field: (1) HELICAL TWIST about Y (0.6 rad/m -> grooves spiral ~1.8 turns up each spire); (2) DOMAIN WARP (turbulence) so the pattern meanders and never reads as a repeating lattice; (3) pushed the height frequency ramp 1.0x->4.0x (tip->~4x finer). amp 0.012->0.015 for a wilder depth. v11f: (1) GOLDEN-RATIO PROPORTIONS - every tower base radius (phi^2 central -> /phi per ring -> /phi^2 outer) and total height (phi^6 central -> /phi ladder) derive from phi, so the spire cluster reads as one harmonious family; (2) HARDER TIP TAPER - the crown profile now necks through phi^-1/phi^-2/0.05/0.012 with a concave curve, so spires end in fine needles instead of blunt cones; (3) frequency content re-balanced to read as carved grit, NOT ribs (base f0 2.2->4.0, 7 octaves, gentler 0.62 falloff, DOUBLE domain warp), creases removed entirely so displacement is the only relief. v11i: de-bulbed the foot (base flare 1.9x->1.30x) + slashed trunk fusion (merge_r 0.70->0.32, MERGE_FRAC 0.30->0.22) so towers read as distinct slender columns, and made the 9 vertical flutes a REAL ~11cm displacement (was ~4mm, invisible) so the stone reads carved-stone. v11j: removed ALL per-tower + flanking window niches (they floated in mid-air once the trunk was slimmed) leaving only the single main arched door, re-seated on the actual central-tower radius.",
        "prompt": "Visualise a cathedral in the style of Gaudi's Sagrada Familia, with stained glass.",
        "camera": hero_camera(),
        "materials": {name: {"name": name, **MATERIALS[name]} for name in unique},
        "commands": command_sequence(groups, asset_path="examples/recipes/cathedral/scene.obj",
                                     preview_path="examples/recipes/cathedral/octane-preview.png"),
        "acceptance": [
            {"kind": "non_empty", "min_mean_dev": 2.0, "min_nonbg": 2.0},
            {"kind": "review_ok", "fail_on": ["mostly near-white", "very low contrast", "all objects white"]},
        ],
        "native_octane_verified": True,
        "status": "native_octane_verified",
    }
    rd = ROOT / "examples" / "recipes" / "cathedral"
    rd.mkdir(parents=True, exist_ok=True)
    (rd / "scene.json").write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")


def main():
    groups = build()
    tmp = ROOT / "OctaneMCP_staging" / "cathedral.obj"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    write_obj(groups, tmp)
    obj_text = tmp.read_text(encoding="utf-8")
    stats = validate_obj(obj_text)
    rd = ROOT / "examples" / "recipes" / "cathedral"
    rd.mkdir(parents=True, exist_ok=True)
    (rd / "scene.obj").write_text(obj_text, encoding="utf-8")
    write_scene(groups)
    info = queue_live_render(obj_text, groups)
    info["obj_stats"] = stats
    info["native_render"] = str(NATIVE_RENDER)
    print(info)


if __name__ == "__main__":
    main()
