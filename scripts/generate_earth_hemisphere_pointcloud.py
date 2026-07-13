#!/usr/bin/env python3
"""Generate a physically proportioned cutaway Earth as colour-grouped point clouds.

The planet uses a 6.371-unit radius (one unit = 1,000 km). The solid layers
are true radial proportions; atmospheric shells use nominal layer boundaries.
The exosphere is intentionally excluded because it has no finite hard edge.

A local equirectangular true-colour Earth bitmap is sampled for crust particles.
The palette is quantized so Octane can assign one material per colour group
without relying on the unavailable vertex-colour/texture-node path.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

from PIL import Image

EARTH_RADIUS_KM = 6371.0
SCALE = 1_000.0
EARTH_RADIUS = EARTH_RADIUS_KM / SCALE
GOLDEN_ANGLE = math.pi * (3.0 - math.sqrt(5.0))

# Boundaries are radii from the centre, in kilometres. Interior values follow
# conventional global discontinuities; the atmosphere uses nominal heights.
SOLID_LAYERS = [
    ("inner_core", 0.0, 1221.0, (1.00, 0.86, 0.34), 12, 55),
    ("outer_core", 1221.0, 3480.0, (1.00, 0.31, 0.08), 16, 70),
    ("lower_mantle", 3480.0, 5711.0, (0.72, 0.18, 0.08), 18, 75),
    ("upper_mantle", 5711.0, 6336.0, (0.40, 0.12, 0.08), 8, 80),
]
ATMOSPHERE = [
    ("troposphere", 6371.0, 6383.0, (0.20, 0.78, 1.00), 360),
    ("stratosphere", 6383.0, 6421.0, (0.20, 0.45, 1.00), 390),
    ("mesosphere", 6421.0, 6456.0, (0.67, 0.27, 1.00), 420),
    ("thermosphere", 6456.0, 6971.0, (1.00, 0.24, 0.63), 500),
]


def octahedron(lines: list[str], center: tuple[float, float, float], radius: float, vertex_index: list[int]) -> None:
    """Write one faceted point primitive; efficient and visibly granular."""
    x, y, z = center
    base = vertex_index[0]
    points = [(x + radius, y, z), (x - radius, y, z), (x, y + radius, z), (x, y - radius, z), (x, y, z + radius), (x, y, z - radius)]
    lines.extend(f"v {px:.6f} {py:.6f} {pz:.6f}" for px, py, pz in points)
    faces = ((0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5))
    lines.extend("f " + " ".join(str(base + index) for index in face) for face in faces)
    vertex_index[0] += 6


def hemisphere_directions(count: int, phase: float = 0.0):
    """Equal-area directions on the back half (z <= 0) of the sphere."""
    for index in range(count):
        z = -(index + 0.5) / count
        horizontal = math.sqrt(max(0.0, 1.0 - z * z))
        angle = index * GOLDEN_ANGLE + phase
        yield horizontal * math.cos(angle), horizontal * math.sin(angle), z


def radial_point_cloud(lower_km: float, upper_km: float, radial_levels: int, directions: int) -> list[tuple[float, float, float]]:
    """Uniform-in-volume samples of a hemispherical radial layer."""
    output = []
    inner3, outer3 = lower_km**3, upper_km**3
    for radial_index in range(radial_levels):
        fraction = (radial_index + 0.5) / radial_levels
        radius = (inner3 + fraction * (outer3 - inner3)) ** (1.0 / 3.0) / SCALE
        for x, y, z in hemisphere_directions(directions, phase=radial_index * 0.37):
            output.append((radius * x, radius * y, radius * z))
    return output


def shell_point_cloud(radius_km: float, count: int) -> list[tuple[float, float, float]]:
    radius = radius_km / SCALE
    return [(radius * x, radius * y, radius * z) for x, y, z in hemisphere_directions(count)]


def cross_section_points(spacing: float = 0.20) -> list[tuple[float, float, float]]:
    """Planar z=0 cut face; supplies the legible nested layer discs."""
    points = []
    cells = math.ceil(EARTH_RADIUS / spacing)
    for ix in range(-cells, cells + 1):
        for iy in range(-cells, cells + 1):
            x, y = ix * spacing, iy * spacing
            if x * x + y * y <= EARTH_RADIUS * EARTH_RADIUS:
                points.append((x, y, 0.0))
    return points


def layer_for_radius(radius_km: float) -> str | None:
    for name, lower, upper, *_rest in SOLID_LAYERS:
        if lower <= radius_km < upper:
            return name
    return None


def texture_palette(path: Path, colors: int) -> tuple[Image.Image, list[tuple[float, float, float]]]:
    source = Image.open(path).convert("RGB")
    indexed = source.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
    raw = indexed.getpalette() or []
    palette = []
    for index in range(colors):
        offset = index * 3
        palette.append(tuple(component / 255.0 for component in raw[offset : offset + 3]))
    return indexed, palette


def colour_for_surface_point(indexed: Image.Image, point: tuple[float, float, float]) -> int:
    x, y, z = point
    radius = math.sqrt(x * x + y * y + z * z) or 1.0
    longitude = math.atan2(z, x)
    latitude = math.asin(max(-1.0, min(1.0, y / radius)))
    u = (longitude + math.pi) / (2.0 * math.pi)
    v = (math.pi / 2.0 - latitude) / math.pi
    px = min(indexed.width - 1, max(0, int(u * indexed.width)))
    py = min(indexed.height - 1, max(0, int(v * indexed.height)))
    return int(indexed.getpixel((px, py)))


def write_asset(path: Path, name: str, points: list[tuple[float, float, float]], point_radius: float) -> None:
    # Material-pin names must be unique per imported OBJ. Reusing `particle`
    # caused this Octane build to resolve every layer through one shared pin.
    lines = ["# Generated by octanex-mcp Earth hemisphere point-cloud prototype", f"o {name}", f"usemtl {name}"]
    vertex_index = [1]
    for point in points:
        octahedron(lines, point, point_radius, vertex_index)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--surface-bitmap", type=Path, required=True)
    parser.add_argument("--palette-colors", type=int, default=12)
    args = parser.parse_args()
    if not args.surface_bitmap.is_file():
        raise SystemExit(f"surface bitmap does not exist: {args.surface_bitmap}")
    if not 4 <= args.palette_colors <= 32:
        raise SystemExit("--palette-colors must be between 4 and 32")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    assets: list[dict] = []
    groups: dict[str, list[tuple[float, float, float]]] = defaultdict(list)
    colours: dict[str, tuple[float, float, float]] = {}

    for name, lower, upper, colour, radial_levels, directions in SOLID_LAYERS:
        groups[name].extend(radial_point_cloud(lower, upper, radial_levels, directions))
        colours[name] = colour

    # The actual cut plane is classed by the physically correct radial boundary.
    for point in cross_section_points():
        layer = layer_for_radius(math.hypot(point[0], point[1]) * SCALE)
        if layer:
            groups[layer].append(point)

    indexed, palette = texture_palette(args.surface_bitmap, args.palette_colors)
    crust_points = shell_point_cloud(EARTH_RADIUS_KM, 1250)
    # Add extra crust points exactly in the cut plane, producing a thin true-colour rim.
    for point in cross_section_points(0.16):
        radius = math.hypot(point[0], point[1])
        if EARTH_RADIUS - 0.09 <= radius <= EARTH_RADIUS:
            crust_points.append(point)
    for point in crust_points:
        palette_index = colour_for_surface_point(indexed, point)
        key = f"crust_palette_{palette_index:02d}"
        groups[key].append(point)
        colours[key] = palette[palette_index]

    for name, lower, upper, colour, count in ATMOSPHERE:
        # A thin shell uses its midpoint; this preserves the actual radial altitude.
        groups[name].extend(shell_point_cloud((lower + upper) / 2.0, count))
        colours[name] = colour

    for name, points in sorted(groups.items()):
        if not points:
            continue
        file_name = f"earth_hemisphere_{name}.obj"
        point_radius = 0.040 if name.startswith(("crust", "troposphere", "stratosphere", "mesosphere", "thermosphere")) else 0.055
        write_asset(args.output_dir / file_name, name, points, point_radius)
        assets.append({"name": name, "path": str(args.output_dir / file_name), "point_count": len(points), "color": list(colours[name]), "point_radius": point_radius})

    manifest = {
        "name": "earth_hemisphere_pointcloud",
        "representation": "cutaway hemisphere point cloud with actual radial proportions",
        "units": {"scene_unit_km": SCALE, "earth_mean_radius_km": EARTH_RADIUS_KM},
        "surface_bitmap": str(args.surface_bitmap.resolve()),
        "surface_mapping": "equirectangular longitude/latitude lookup, median-cut palette quantized for material groups",
        "limitations": ["crust bitmap is colour/topography imagery sampled onto point positions; no displacement is applied", "atmosphere stops at 600 km nominal thermosphere extent; exosphere has no finite hard boundary"],
        "solid_layers_km": [{"name": name, "inner_radius": lower, "outer_radius": upper} for name, lower, upper, *_ in SOLID_LAYERS],
        "atmosphere_layers_km": [{"name": name, "inner_radius": lower, "outer_radius": upper} for name, lower, upper, *_ in ATMOSPHERE],
        "assets": assets,
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"assets": len(assets), "points": sum(item["point_count"] for item in assets), "manifest": str(args.output_dir / "manifest.json")}, indent=2))


if __name__ == "__main__":
    main()
