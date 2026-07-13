"""Point-cloud ingestion and particle-cloud geometry for OctaneX MCP.

The core readers use only the standard library so CSV/TSV, XYZ/PTS, ASCII PLY,
JSON, and GeoJSON Point datasets work in a minimal server install. NetCDF is an
optional path backed by ``xarray`` + ``netCDF4`` because those packages are too
heavy for the core bridge.

A loaded dataset is normalized into a compact, bounds-aware particle scene. This
is deliberately an *instanced-geometry approximation* of a volume, not a claim
that it is a physical VDB/participating medium.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any, Iterable, Iterator

from .bridge import Workspace
from .visuals import ObjBuilder, _safe_name, bounds_from_points, camera_for_bounds

POINTCLOUD_EXTRA_HINT = "optional NetCDF dependency missing: install with `uv sync --extra pointcloud` (adds numpy, xarray, netCDF4)"
_SUPPORTED_SUFFIXES = {".csv", ".tsv", ".xyz", ".pts", ".txt", ".ply", ".json", ".geojson", ".nc", ".nc4", ".cdf"}
_SUPPORTED_PRIMITIVES = {"sphere", "cube"}


class PointCloudFormatError(ValueError):
    """Raised when a point-cloud dataset cannot be read as xyz coordinates."""


class PointCloudDependencyError(RuntimeError):
    """Raised when an optional point-cloud reader dependency is unavailable."""


def supported_point_cloud_formats() -> dict[str, list[str]]:
    """Return supported suffixes split by core and optional-reader support."""
    return {
        "core": [".csv", ".tsv", ".xyz", ".pts", ".txt", ".ply (ASCII)", ".json", ".geojson"],
        "optional": [".nc", ".nc4", ".cdf (NetCDF via xarray + netCDF4)"],
    }


def _finite_triplet(values: Iterable[Any]) -> tuple[float, float, float] | None:
    try:
        point = tuple(float(value) for value in values)
    except (TypeError, ValueError):
        return None
    if len(point) != 3 or not all(math.isfinite(value) for value in point):
        return None
    return point  # type: ignore[return-value]


def _limit(points: Iterable[tuple[float, float, float]], max_points: int) -> list[tuple[float, float, float]]:
    if max_points < 1 or max_points > 4096:
        raise ValueError("max_points must be between 1 and 4096")
    parsed = list(points)
    if not parsed:
        raise PointCloudFormatError("dataset contains no finite xyz points")
    if len(parsed) <= max_points:
        return parsed
    # Deterministic even sampling preserves the overall extent without a random seed.
    step = len(parsed) / max_points
    return [parsed[min(int(index * step), len(parsed) - 1)] for index in range(max_points)]


def _read_delimited(path: Path, *, delimiter: str, columns: tuple[str, str, str]) -> list[tuple[float, float, float]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        has_header = csv.Sniffer().has_header(sample) if sample.strip() else False
        if has_header:
            reader = csv.DictReader(handle, delimiter=delimiter)
            points = []
            for row in reader:
                if row is None:
                    continue
                point = _finite_triplet(row.get(column) for column in columns)
                if point is not None:
                    points.append(point)
            return points
        reader = csv.reader(handle, delimiter=delimiter)
        points = []
        for row in reader:
            if not row or row[0].lstrip().startswith("#"):
                continue
            point = _finite_triplet(row[:3])
            if point is not None:
                points.append(point)
        return points


def _read_whitespace(path: Path) -> list[tuple[float, float, float]]:
    points = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        point = _finite_triplet(stripped.replace(",", " ").split()[:3])
        if point is not None:
            points.append(point)
    return points


def _read_ascii_ply(path: Path) -> list[tuple[float, float, float]]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if not lines or lines[0].strip() != "ply":
        raise PointCloudFormatError("PLY input must start with 'ply'")
    if "format ascii" not in "\n".join(lines[:20]).lower():
        raise PointCloudFormatError("only ASCII PLY is supported; convert binary PLY to ASCII first")
    vertex_count = None
    properties: list[str] = []
    in_vertex = False
    data_start = None
    for index, line in enumerate(lines[1:], start=1):
        fields = line.split()
        if fields[:2] == ["element", "vertex"] and len(fields) >= 3:
            vertex_count = int(fields[2])
            in_vertex = True
        elif fields[:1] == ["element"]:
            in_vertex = False
        elif in_vertex and fields[:1] == ["property"] and len(fields) >= 3:
            properties.append(fields[-1])
        elif line.strip() == "end_header":
            data_start = index + 1
            break
    if vertex_count is None or data_start is None:
        raise PointCloudFormatError("PLY header must declare an element vertex block")
    try:
        indices = [properties.index(axis) for axis in ("x", "y", "z")]
    except ValueError as exc:
        raise PointCloudFormatError("PLY vertex properties must include x, y, z") from exc
    points = []
    for line in lines[data_start : data_start + vertex_count]:
        values = line.split()
        point = _finite_triplet(values[index] for index in indices if index < len(values))
        if point is not None:
            points.append(point)
    return points


def _iter_geojson_points(value: Any) -> Iterator[tuple[float, float, float]]:
    if isinstance(value, dict):
        kind = value.get("type")
        if kind == "FeatureCollection":
            for feature in value.get("features", []):
                yield from _iter_geojson_points(feature)
        elif kind == "Feature":
            yield from _iter_geojson_points(value.get("geometry"))
        elif kind == "Point":
            coordinates = value.get("coordinates", [])
            if isinstance(coordinates, (list, tuple)) and len(coordinates) == 2:
                coordinates = [coordinates[0], coordinates[1], 0.0]
            point = _finite_triplet(coordinates)
            if point is not None:
                yield point
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, (list, tuple)):
                point = _finite_triplet(item)
                if point is not None:
                    yield point


def _read_json(path: Path) -> list[tuple[float, float, float]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, dict) and isinstance(value.get("points"), list):
        value = value["points"]
    return list(_iter_geojson_points(value))


def _netcdf_axis_name(dim: str, position_from_end: int) -> str:
    lower = dim.lower()
    if lower.startswith(("x", "lon", "longitude", "easting")):
        return "x"
    if lower.startswith(("y", "lat", "latitude", "northing")):
        return "y"
    if lower.startswith(("z", "depth", "height", "lev", "level", "alt")):
        return "z"
    return ("x", "y", "z")[position_from_end]


def _read_netcdf(path: Path, *, variable: str | None, time_index: int, max_points: int) -> tuple[list[tuple[float, float, float]], dict[str, Any]]:
    try:
        import numpy as np
        import xarray as xr  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - exercised in bare installs
        raise PointCloudDependencyError(POINTCLOUD_EXTRA_HINT) from exc

    with xr.open_dataset(path) as dataset:
        if variable is None:
            candidates = [name for name, data in dataset.data_vars.items() if data.ndim >= 3]
            if not candidates:
                raise PointCloudFormatError("NetCDF needs a variable with at least three spatial dimensions; pass variable explicitly")
            variable = candidates[0]
        if variable not in dataset.data_vars:
            raise PointCloudFormatError(f"NetCDF variable {variable!r} not found; available: {', '.join(dataset.data_vars)}")
        data = dataset[variable]
        if "time" in data.dims:
            if not 0 <= time_index < data.sizes["time"]:
                raise ValueError(f"time_index must be between 0 and {data.sizes['time'] - 1}")
            data = data.isel(time=time_index)
        if data.ndim != 3:
            raise PointCloudFormatError(f"NetCDF variable {variable!r} must be 3D after time selection; got dimensions {data.dims}")
        dims = tuple(str(dim) for dim in data.dims)
        axis_names = [_netcdf_axis_name(dim, 2 - index) for index, dim in enumerate(dims)]
        if len(set(axis_names)) != 3:
            axis_names = ["z", "y", "x"]
        arrays: dict[str, Any] = {}
        for dim, axis in zip(dims, axis_names):
            coord = data.coords.get(dim)
            arrays[axis] = np.asarray(coord.values if coord is not None and coord.ndim == 1 else np.arange(data.sizes[dim]), dtype=float)
        values = np.asarray(data.values, dtype=float)
        finite = np.isfinite(values)
        if not finite.any():
            raise PointCloudFormatError(f"NetCDF variable {variable!r} contains no finite values")
        # Prefer the strongest magnitude samples: appropriate for scalar fields such as
        # plume buoyancy/velocity, while retaining a strict cap for OBJ complexity.
        candidates = np.flatnonzero(finite.ravel())
        magnitudes = np.abs(values.ravel()[candidates])
        keep = candidates[np.argsort(magnitudes)[-min(max_points, len(candidates)) :]]
        points: list[tuple[float, float, float]] = []
        for flat in keep:
            indices = np.unravel_index(int(flat), values.shape)
            coords = {axis: arrays[axis][index] for axis, index in zip(axis_names, indices)}
            point = _finite_triplet((coords["x"], coords["y"], coords["z"]))
            if point is not None:
                points.append((float(point[0]), float(point[1]), float(point[2])))
        metadata = {
            "format": "netcdf",
            "variable": variable,
            "time_index": time_index if "time" in dataset[variable].dims else None,
            "dimensions": list(dims),
            "source_shape": list(values.shape),
        }
        return points, metadata


def load_point_cloud(
    source_path: str | Path,
    *,
    columns: tuple[str, str, str] = ("x", "y", "z"),
    variable: str | None = None,
    time_index: int = 0,
    max_points: int = 512,
) -> dict[str, Any]:
    """Load xyz points from a common point-cloud source without rendering it."""
    path = Path(source_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"point-cloud source does not exist: {path}")
    suffix = path.suffix.lower()
    if suffix not in _SUPPORTED_SUFFIXES:
        raise PointCloudFormatError(f"unsupported point-cloud format {suffix or '<none>'}; supported: {', '.join(sorted(_SUPPORTED_SUFFIXES))}")
    metadata: dict[str, Any] = {"format": suffix.lstrip("."), "source_path": str(path)}
    if suffix in {".csv", ".tsv"}:
        points = _read_delimited(path, delimiter="," if suffix == ".csv" else "\t", columns=columns)
    elif suffix in {".xyz", ".pts", ".txt"}:
        points = _read_whitespace(path)
    elif suffix == ".ply":
        points = _read_ascii_ply(path)
    elif suffix in {".json", ".geojson"}:
        points = _read_json(path)
    else:
        points, netcdf_metadata = _read_netcdf(path, variable=variable, time_index=time_index, max_points=max_points)
        metadata.update(netcdf_metadata)
    points = _limit(points, max_points)
    metadata.update({"point_count": len(points), "source_bounds": bounds_from_points(points)})
    return {"points": [list(point) for point in points], "metadata": metadata}


def normalize_points(points: Iterable[Iterable[float]], *, target_extent: float = 6.0) -> tuple[list[tuple[float, float, float]], dict[str, Any]]:
    """Centre and uniformly scale points so a data source renders predictably."""
    parsed = [point for point in (_finite_triplet(values) for values in points) if point is not None]
    if not parsed:
        raise PointCloudFormatError("point cloud contains no finite xyz points")
    source_bounds = bounds_from_points(parsed)
    center = tuple(float(value) for value in source_bounds["center"])
    spans = [float(source_bounds["max"][index]) - float(source_bounds["min"][index]) for index in range(3)]
    scale = float(target_extent) / max(max(spans), 1e-9)
    normalized = [tuple((point[index] - center[index]) * scale for index in range(3)) for point in parsed]
    return normalized, {"source_bounds": source_bounds, "normalization_scale": scale, "target_extent": float(target_extent)}


def create_particle_cloud_obj(
    points: Iterable[Iterable[float]],
    *,
    name: str = "visual_particle_cloud",
    point_size: float = 0.12,
    primitive: str = "sphere",
    workspace: Workspace = Workspace(),
) -> dict[str, Any]:
    """Create a single-mesh particle cloud from already-normalized xyz points.

    ``sphere`` has a volumetric reading; ``cube`` produces a lighter voxel-field
    diagnostic. Both preserve the same data coordinates and camera framing.
    """
    workspace.ensure()
    parsed = [point for point in (_finite_triplet(values) for values in points) if point is not None]
    if not parsed:
        raise ValueError("particle cloud must contain finite xyz points")
    if len(parsed) > 4096:
        raise ValueError("particle cloud supports up to 4096 points")
    safe = _safe_name(name)
    radius = max(float(point_size) / 2.0, 0.01)
    primitive = str(primitive).lower()
    if primitive not in _SUPPORTED_PRIMITIVES:
        raise ValueError(f"unsupported particle primitive {primitive!r}; expected one of {sorted(_SUPPORTED_PRIMITIVES)}")
    builder = ObjBuilder(safe)
    for point in parsed:
        if primitive == "sphere":
            builder.add_ellipsoid(center=point, radii=(radius, radius, radius), segments_u=8, segments_v=4, material="particle")
        else:
            builder.add_box(center=point, size=(radius * 2.0, radius * 2.0, radius * 2.0), material="particle")
    path = workspace.assets_dir / f"{safe}.obj"
    path.write_text(builder.text(), encoding="utf-8")
    return {"path": str(path), "name": safe, "kind": "particle_cloud", "primitive": primitive, "point_count": len(parsed), "bounds": builder.bounds()}


def point_cloud_to_asset(
    source_path: str | Path,
    *,
    name: str = "visual_particle_cloud",
    columns: tuple[str, str, str] = ("x", "y", "z"),
    variable: str | None = None,
    time_index: int = 0,
    max_points: int = 512,
    point_size: float = 0.12,
    primitive: str = "sphere",
    target_extent: float = 6.0,
    workspace: Workspace = Workspace(),
) -> dict[str, Any]:
    """Load a data source, normalize it, and write a renderable particle-cloud OBJ."""
    loaded = load_point_cloud(source_path, columns=columns, variable=variable, time_index=time_index, max_points=max_points)
    normalized, normalization = normalize_points(loaded["points"], target_extent=target_extent)
    asset = create_particle_cloud_obj(normalized, name=name, point_size=point_size, primitive=primitive, workspace=workspace)
    asset["source"] = {**loaded["metadata"], **normalization}
    return asset


def particle_cloud_scene_commands(asset: dict[str, Any], *, color: list[float], preview_path: str) -> list[dict[str, Any]]:
    """Compile a particle asset to a safe, self-contained render command sequence."""
    material_name = f"{asset['name']}_particle_material"
    return [
        {"op": "import_geometry", "payload": {"path": asset["path"], "format": "obj", "name": asset["name"]}},
        {"op": "create_material", "payload": {"name": material_name, "kind": "glossy", "color": color, "roughness": 0.22, "emission": 0.12}},
        {"op": "assign_material", "payload": {"object_name": asset["name"], "material_name": material_name, "group_index": 1}},
        {"op": "set_camera", "payload": camera_for_bounds(asset["bounds"], margin=1.3, fov=42)},
        {"op": "set_lighting", "payload": {"preset": "dark_studio"}},
        {"op": "save_preview", "payload": {"path": preview_path, "width": 1024, "height": 1024, "samples": 128, "min_samples": 16, "timeout_seconds": 300}},
    ]
