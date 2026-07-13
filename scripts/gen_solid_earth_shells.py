#!/usr/bin/env python3
"""Generate a mesh-equivalent Solid Earth concentric-shell cutaway.

This is the non-particle counterpart to the earth-hemisphere point-cloud recipe:
WGS84 oblate Earth, PREM-like interior radii, fluid outer core, atmospheric
shells, and a real 1:1 elevation/bathymetry displacement on the crust surface
when a global GeoTIFF is available.

Coordinate convention matches the existing earth-hemisphere recipe: the rendered
body is the lower half-space z <= 0, so the z=0 plane is the cut face and +z is
removed. y is the rotation/polar axis and is compressed by WGS84 flattening.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import OrderedDict
from pathlib import Path
from typing import Any

KM = 1000.0
A_EQ_KM = 6378.137
B_POLAR_KM = 6356.752
FLAT = B_POLAR_KM / A_EQ_KM
SURFACE_KM = 6371.0
CRUST_BASE_KM = 6346.0

# name, inner_km, outer_km, material colour, material extras
SOLID_LAYERS = [
    ("inner_core", 0.0, 1221.5, (1.00, 0.86, 0.32), {"kind": "glossy", "roughness": 0.30, "emission": 0.35, "opacity": 0.94, "transmission": 0.03}),
    ("outer_core", 1221.5, 3480.0, (1.00, 0.36, 0.08), {"kind": "glossy", "roughness": 0.24, "emission": 0.22, "opacity": 0.48, "transmission": 0.42}),
    ("lower_mantle", 3480.0, 5701.0, (0.58, 0.18, 0.08), {"kind": "glossy", "roughness": 0.55, "opacity": 0.52, "transmission": 0.35}),
    ("upper_mantle", 5701.0, 6346.0, (0.82, 0.35, 0.12), {"kind": "glossy", "roughness": 0.48, "opacity": 0.54, "transmission": 0.30}),
]
ATMOSPHERE = [
    ("troposphere", 0.0, 12.0, (0.60, 0.82, 1.00), {"kind": "specular", "roughness": 0.05, "transmission": 0.92, "ior": 1.0003, "opacity": 0.28}),
    ("stratosphere", 12.0, 50.0, (0.40, 0.62, 1.00), {"kind": "specular", "roughness": 0.05, "transmission": 0.93, "ior": 1.0003, "opacity": 0.20}),
    ("mesosphere", 50.0, 85.0, (0.63, 0.42, 1.00), {"kind": "specular", "roughness": 0.05, "transmission": 0.93, "ior": 1.0003, "opacity": 0.14}),
    ("thermosphere", 85.0, 600.0, (1.00, 0.42, 0.70), {"kind": "specular", "roughness": 0.05, "transmission": 0.95, "ior": 1.0003, "opacity": 0.08}),
]

MATERIALS: OrderedDict[str, dict[str, Any]] = OrderedDict([
    ("mat_inner_core", {"color": [1.00, 0.86, 0.32], "kind": "glossy", "roughness": 0.30, "emission": 0.35, "opacity": 0.94, "transmission": 0.03}),
    ("mat_outer_core", {"color": [1.00, 0.36, 0.08], "kind": "glossy", "roughness": 0.24, "emission": 0.22, "opacity": 0.48, "transmission": 0.42}),
    ("mat_lower_mantle", {"color": [0.58, 0.18, 0.08], "kind": "glossy", "roughness": 0.55, "opacity": 0.52, "transmission": 0.35}),
    ("mat_upper_mantle", {"color": [0.82, 0.35, 0.12], "kind": "glossy", "roughness": 0.48, "opacity": 0.54, "transmission": 0.30}),
    ("mat_continental_crust", {"color": [0.57, 0.49, 0.36], "kind": "glossy", "roughness": 0.82, "opacity": 0.90, "transmission": 0.02}),
    ("mat_oceanic_crust", {"color": [0.10, 0.13, 0.18], "kind": "glossy", "roughness": 0.62, "opacity": 0.86, "transmission": 0.04}),
    ("mat_polar_ice", {"color": [0.86, 0.92, 0.98], "kind": "glossy", "roughness": 0.38, "opacity": 0.94, "transmission": 0.03}),
    ("mat_llsvp", {"color": [0.78, 0.20, 0.52], "kind": "glossy", "roughness": 0.45, "emission": 0.12, "opacity": 0.58, "transmission": 0.25}),
    ("mat_plume", {"color": [1.00, 0.78, 0.38], "kind": "glossy", "roughness": 0.30, "emission": 0.40, "opacity": 0.90, "transmission": 0.05}),
    ("mat_troposphere", {"color": [0.60, 0.82, 1.00], "kind": "specular", "roughness": 0.05, "transmission": 0.92, "ior": 1.0003, "opacity": 0.28}),
    ("mat_stratosphere", {"color": [0.40, 0.62, 1.00], "kind": "specular", "roughness": 0.05, "transmission": 0.93, "ior": 1.0003, "opacity": 0.20}),
    ("mat_mesosphere", {"color": [0.63, 0.42, 1.00], "kind": "specular", "roughness": 0.05, "transmission": 0.93, "ior": 1.0003, "opacity": 0.14}),
    ("mat_thermosphere", {"color": [1.00, 0.42, 0.70], "kind": "specular", "roughness": 0.05, "transmission": 0.95, "ior": 1.0003, "opacity": 0.08}),
])


def crust_class(lon: float, lat: float, elev_m: float | None = None) -> str:
    if abs(math.degrees(lat)) > 70:
        return "mat_polar_ice"
    if elev_m is not None:
        return "mat_continental_crust" if elev_m >= 0.0 else "mat_oceanic_crust"
    # deterministic fallback continent mask used only if GDAL is unavailable
    v = (math.sin(2.7 * lon + 0.4) + 0.65 * math.sin(4.1 * lon - 1.7 * lat) + 0.45 * math.cos(3.0 * lat))
    return "mat_continental_crust" if v > 0.25 else "mat_oceanic_crust"


class DemSampler:
    def __init__(self, path: Path | None):
        self.path = path
        self.ds = None
        self.band = None
        self.gt = None
        if path and path.exists():
            try:
                from osgeo import gdal  # type: ignore
                self.ds = gdal.Open(str(path))
                if self.ds:
                    self.band = self.ds.GetRasterBand(1)
                    self.gt = self.ds.GetGeoTransform()
                    self.nodata = self.band.GetNoDataValue()
            except Exception:
                self.ds = None

    @property
    def available(self) -> bool:
        return self.ds is not None and self.band is not None and self.gt is not None

    def sample(self, lon_deg: float, lat_deg: float) -> float:
        if not self.available:
            return 0.0
        assert self.ds is not None and self.band is not None and self.gt is not None
        gt = self.gt
        # north-up lon/lat GeoTIFF: x = lon, y = lat
        px = int((lon_deg - gt[0]) / gt[1])
        py = int((lat_deg - gt[3]) / gt[5])
        px = max(0, min(self.ds.RasterXSize - 1, px))
        py = max(0, min(self.ds.RasterYSize - 1, py))
        val = float(self.band.ReadAsArray(px, py, 1, 1)[0, 0])
        if getattr(self, "nodata", None) is not None and val == self.nodata:
            return 0.0
        return val


def unit_from_params(i: int, j: int, meridians: int, parallels: int) -> tuple[float, float, float, float, float]:
    # t=0 is the cut rim (z=0); t=pi/2 is the centre of the retained hemisphere (z=-r)
    phi = (j / meridians) * math.tau
    t = (i / parallels) * (math.pi / 2.0)
    h = math.cos(t)
    x = h * math.cos(phi)
    y = h * math.sin(phi)
    z = -math.sin(t)
    lat = math.asin(max(-1.0, min(1.0, y)))
    lon = math.atan2(z, x)
    return x, y, z, lon, lat


def oblate_point(unit: tuple[float, float, float], radius_km: float) -> tuple[float, float, float]:
    r = radius_km / KM
    x, y, z = unit
    return (x * r, y * r * FLAT, z * r)


class Mesh:
    def __init__(self):
        self.groups: OrderedDict[str, list[tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]]] = OrderedDict()

    def add(self, mat: str, verts: list[tuple[float, float, float]], faces: list[tuple[int, ...]]) -> None:
        if mat not in self.groups:
            self.groups[mat] = []
        self.groups[mat].append((verts, faces))

    def add_quad(self, mat: str, a, b, c, d) -> None:
        self.add(mat, [a, b, c, d], [(1, 2, 3), (1, 3, 4)])

    def add_tri(self, mat: str, a, b, c) -> None:
        self.add(mat, [a, b, c], [(1, 2, 3)])

    def write_obj(self, path: Path) -> list[str]:
        lines = ["# Solid Earth concentric shell mesh generated by gen_solid_earth_shells.py", "mtllib scene.mtl", "o solid_earth_shells"]
        order = []
        offset = 1
        for mat, chunks in self.groups.items():
            if not chunks:
                continue
            order.append(mat)
            lines.append(f"usemtl {mat}")
            for verts, faces in chunks:
                for x, y, z in verts:
                    lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")
                for face in faces:
                    lines.append("f " + " ".join(str(offset + idx - 1) for idx in face))
                offset += len(verts)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return order


def add_hemi_surface(mesh: Mesh, mat: str, radius_km: float, meridians: int, parallels: int,
                     dem: DemSampler | None = None, material_by_dem: bool = False) -> None:
    for i in range(parallels):
        for j in range(meridians):
            # The final latitude row collapses to one pole point. Emit a triangle
            # cap there; a quad would contain two coincident pole vertices and
            # trip the OBJ degenerate-face verifier.
            if i == parallels - 1:
                rim = []
                mats = []
                for ii, jj in [(i, j), (i, j + 1)]:
                    x, y, z, lon, lat = unit_from_params(ii, jj % meridians, meridians, parallels)
                    elev = dem.sample(math.degrees(lon), math.degrees(lat)) if dem and dem.available else 0.0
                    rr = radius_km + (elev / 1000.0 if dem and dem.available else 0.0)
                    rim.append(oblate_point((x, y, z), rr))
                    mats.append(crust_class(lon, lat, elev if dem and dem.available else None))
                x, y, z, lon, lat = unit_from_params(parallels, 0, meridians, parallels)
                elev = dem.sample(math.degrees(lon), math.degrees(lat)) if dem and dem.available else 0.0
                pole = oblate_point((x, y, z), radius_km + (elev / 1000.0 if dem and dem.available else 0.0))
                use_mat = max(set(mats), key=mats.count) if material_by_dem else mat
                mesh.add_tri(use_mat, rim[0], rim[1], pole)
                continue
            pts = []
            elevs = []
            mats = []
            for ii, jj in [(i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j)]:
                x, y, z, lon, lat = unit_from_params(ii, jj % meridians, meridians, parallels)
                elev = dem.sample(math.degrees(lon), math.degrees(lat)) if dem and dem.available else 0.0
                rr = radius_km + (elev / 1000.0 if dem and dem.available else 0.0)
                pts.append(oblate_point((x, y, z), rr))
                elevs.append(elev)
                mats.append(crust_class(lon, lat, elev if dem and dem.available else None))
            use_mat = max(set(mats), key=mats.count) if material_by_dem else mat
            mesh.add_quad(use_mat, pts[0], pts[1], pts[2], pts[3])


def add_section_annulus(mesh: Mesh, mat: str, inner_km: float, outer_km: float, segs: int,
                        rings: int = 1, material_by_angle: bool = False) -> None:
    zcut = 0.035  # slight camera-side offset avoids z-fighting with shell rims
    inner = inner_km / KM
    outer = outer_km / KM
    if inner <= 0.0001:
        center = (0.0, 0.0, zcut)
        for j in range(segs):
            a0 = j * math.tau / segs
            a1 = (j + 1) * math.tau / segs
            p0 = (outer * math.cos(a0), outer * math.sin(a0) * FLAT, zcut)
            p1 = (outer * math.cos(a1), outer * math.sin(a1) * FLAT, zcut)
            mesh.add_tri(mat, center, p0, p1)
        return
    for r_i in range(rings):
        r0 = inner + (outer - inner) * r_i / rings
        r1 = inner + (outer - inner) * (r_i + 1) / rings
        for j in range(segs):
            a0 = j * math.tau / segs
            a1 = (j + 1) * math.tau / segs
            p00 = (r0 * math.cos(a0), r0 * math.sin(a0) * FLAT, zcut)
            p01 = (r0 * math.cos(a1), r0 * math.sin(a1) * FLAT, zcut)
            p11 = (r1 * math.cos(a1), r1 * math.sin(a1) * FLAT, zcut)
            p10 = (r1 * math.cos(a0), r1 * math.sin(a0) * FLAT, zcut)
            if material_by_angle:
                mid = (a0 + a1) / 2.0
                lat = math.asin(max(-1.0, min(1.0, math.sin(mid))))
                use_mat = crust_class(0.0, lat, None) + "_face"
            else:
                use_mat = mat
            mesh.add_quad(use_mat, p00, p01, p11, p10)


def add_llsvp_and_plumes(mesh: Mesh, segs: int) -> None:
    # Cut-face, mesh-only representation of two CMB-rooted thermochemical piles and plume conduits.
    provinces = [(-0.80, -0.20, 0.0), (0.58, 0.46, 0.0)]
    for cx, cy, _ in provinces:
        for j in range(segs // 3):
            a0 = j * math.tau / (segs // 3)
            a1 = (j + 1) * math.tau / (segs // 3)
            r0 = CMB_KM = 3480.0 / KM
            r1 = (3480.0 + 1300.0) / KM
            # angular lens on the section face, broad at CMB and tapering upward
            w0, w1 = 0.62, 0.34
            p00 = (cx * r0 + w0 * math.cos(a0), (cy * r0 + w0 * math.sin(a0)) * FLAT, 0.012)
            p01 = (cx * r0 + w0 * math.cos(a1), (cy * r0 + w0 * math.sin(a1)) * FLAT, 0.012)
            p11 = (cx * r1 + w1 * math.cos(a1), (cy * r1 + w1 * math.sin(a1)) * FLAT, 0.012)
            p10 = (cx * r1 + w1 * math.cos(a0), (cy * r1 + w1 * math.sin(a0)) * FLAT, 0.012)
            mesh.add_quad("mat_llsvp", p00, p01, p11, p10)
        # three tapered plume ribbons per province
        for k in range(3):
            angle = (k - 1) * 0.32
            dx = math.cos(angle) * cx - math.sin(angle) * cy
            dy = math.sin(angle) * cx + math.cos(angle) * cy
            n = math.hypot(dx, dy) or 1.0
            dx, dy = dx / n, dy / n
            prev_left = prev_right = None
            steps = 18
            for s in range(steps + 1):
                t = s / steps
                r = (3480.0 + t * (6000.0 - 3480.0)) / KM
                wig = 0.15 * math.sin(t * math.tau * 2.0 + k)
                px = dx * r + (-dy) * wig
                py = (dy * r + dx * wig) * FLAT
                width = (0.070 * (1.0 - 0.6 * t))
                left = (px - dy * width, py + dx * width * FLAT, 0.018)
                right = (px + dy * width, py - dx * width * FLAT, 0.018)
                if prev_left is not None:
                    mesh.add_quad("mat_plume", prev_left, prev_right, right, left)
                prev_left, prev_right = left, right


def build(out: Path, dem_path: Path | None, meridians: int, parallels: int) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    dem = DemSampler(dem_path)
    mesh = Mesh()

    # Boundary surfaces for concentric shells, semi-transparent so the cut face remains readable.
    for name, lo, hi, _col, _extra in SOLID_LAYERS:
        add_hemi_surface(mesh, f"mat_{name}", hi, meridians, parallels)
        add_section_annulus(mesh, f"mat_{name}_face", lo, hi, meridians * 2, rings=max(1, int((hi - lo) / 700)))

    # Real crust topography/bathymetry: 1:1 radial displacement from the GeoTIFF.
    add_hemi_surface(mesh, "mat_continental_crust", SURFACE_KM, meridians, parallels, dem=dem, material_by_dem=True)
    add_section_annulus(mesh, "mat_continental_crust_face", CRUST_BASE_KM, SURFACE_KM, meridians * 2, rings=1, material_by_angle=True)

    # Mesh-only LLSVP/plumes drawn on the cut plane, not as particles/volumes.
    add_llsvp_and_plumes(mesh, meridians * 2)

    for name, lo, hi, _col, _extra in ATMOSPHERE:
        add_hemi_surface(mesh, f"mat_{name}", SURFACE_KM + hi, meridians, max(8, parallels // 2))
        add_section_annulus(mesh, f"mat_{name}_face", SURFACE_KM + lo, SURFACE_KM + hi, meridians * 2, rings=1)

    obj_path = out / "scene.obj"
    group_order = mesh.write_obj(obj_path)

    mtl = ["# Reference MTL; Octane material binding is explicit in scene.json"]
    def material_payload(mat: str) -> dict[str, Any]:
        base = mat[:-5] if mat.endswith("_face") else mat
        payload = dict(MATERIALS[base])
        if mat.endswith("_face"):
            payload.update({"opacity": 0.96, "transmission": 0.0, "emission": payload.get("emission", 0.0)})
        payload["name"] = mat
        return payload

    for mat in group_order:
        col = material_payload(mat)["color"]
        mtl += [f"newmtl {mat}", f"Kd {col[0]:.3f} {col[1]:.3f} {col[2]:.3f}"]
    (out / "scene.mtl").write_text("\n".join(mtl) + "\n", encoding="utf-8")

    materials = OrderedDict((m, material_payload(m)) for m in group_order)
    commands = [{"op": "import_geometry", "payload": {"path": str(obj_path), "format": "obj", "name": "solid_earth_shells"}}]
    for payload in materials.values():
        commands.append({"op": "create_material", "payload": payload})
    for idx, mat in enumerate(group_order, start=1):
        commands.append({"op": "assign_material", "payload": {"object_name": "solid_earth_shells", "material_name": mat, "group_index": idx}})
    camera = {"position": [-8.982154, -19.817986, 13.783353], "target": [-0.06247065, -0.09485492, -1.137385], "fov": 28.0, "focus_distance": 27.631866}
    commands += [
        {"op": "set_camera", "payload": camera},
        {"op": "set_lighting", "payload": {"preset": "soft_studio"}},
        {"op": "save_preview", "payload": {"path": str(out / "octane-preview.png"), "width": 1280, "height": 1280, "samples": 800, "min_samples": 200, "timeout_seconds": 420}},
    ]
    scene = {
        "slug": out.name,
        "title": "Solid Earth concentric shell cutaway — mesh equivalent, no volumetric particles",
        "category": "Geoscience / planet visualization",
        "purpose": "Hemispherical mesh-only, to-scale model of present Earth interior and fluid envelopes: WGS84 oblateness, PREM radial shells, fluid outer core, atmosphere, LLSVP/plume context, and 1:1 GeoTIFF elevation/bathymetry displacement on the crust surface.",
        "source_recipe": "earth-hemisphere / Volumetric Earth point-cloud recipe, converted to mesh shells",
        "scale": {"scene_unit": "1000 km", "elevation_displacement": "1:1 metres from GeoTIFF converted to km"},
        "dem": {"path": str(dem_path) if dem_path else None, "available": dem.available},
        "camera": camera,
        "materials": materials,
        "commands": commands,
        "native_octane_verified": False,
        "status": "ad-hoc render candidate",
    }
    (out / "scene.json").write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
    return {"obj": str(obj_path), "groups": len(group_order), "materials": group_order, "dem_available": dem.available, "scene": str(out / "scene.json")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("output_dir", type=Path)
    ap.add_argument("--dem", type=Path, default=Path("/Users/craig/ECDO/GIS/elevation.tif"))
    ap.add_argument("--meridians", type=int, default=96)
    ap.add_argument("--parallels", type=int, default=36)
    args = ap.parse_args()
    print(json.dumps(build(args.output_dir, args.dem, args.meridians, args.parallels), indent=2))


if __name__ == "__main__":
    main()
