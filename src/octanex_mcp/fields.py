"""Regular-grid field interpolation and surface extraction for OctaneX MCP.

This module intentionally handles bounded review assets only. It does not claim
to be a sparse-volume store or VDB exporter: large simulations must stay
source-backed and be sampled one frame/region at a time.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Iterable, cast

from .bridge import Workspace
from .visuals import _safe_name, bounds_from_points, camera_for_bounds

FIELD_EXTRA_HINT = "optional field dependencies missing: install with `uv sync --extra pointcloud --extra fields`"


class FieldFormatError(ValueError):
    """Raised when a field cannot be represented as a regular three-dimensional grid."""


class FieldDependencyError(RuntimeError):
    """Raised when optional interpolation or mesh-extraction dependencies are absent."""


def _dependencies(*, density: bool = False) -> tuple[Any, Any, Any, Any | None]:
    try:
        import numpy as np
        import xarray as xr  # type: ignore[import-not-found]
        from skimage import measure  # type: ignore[import-not-found]
        if density:
            from scipy import ndimage  # type: ignore[import-not-found]
        else:
            ndimage = None
    except Exception as exc:  # pragma: no cover - exercised in bare installs
        raise FieldDependencyError(FIELD_EXTRA_HINT) from exc
    return np, xr, measure, ndimage


def _axis_name(dim: str, position_from_end: int) -> str:
    lower = dim.lower()
    if lower.startswith(("x", "lon", "longitude", "easting")):
        return "x"
    if lower.startswith(("y", "lat", "latitude", "northing")):
        return "y"
    if lower.startswith(("z", "depth", "height", "lev", "level", "alt")):
        return "z"
    return ("x", "y", "z")[position_from_end]


def _validate_fraction(value: float, *, name: str = "iso_fraction") -> float:
    value = float(value)
    if not 0.0 < value < 1.0:
        raise ValueError(f"{name} must be strictly between 0 and 1")
    return value


def _regular_axes(data: Any, np: Any) -> tuple[Any, tuple[str, str, str], list[Any]]:
    """Return finite 3D values, unambiguous xyz axis labels, and ascending coordinates."""
    if data.ndim != 3:
        raise FieldFormatError(f"field must be three-dimensional; got dimensions {data.dims}")
    dims = tuple(str(dim) for dim in data.dims)
    axis_names = [_axis_name(dim, 2 - index) for index, dim in enumerate(dims)]
    if len(set(axis_names)) != 3:
        axis_names = ["z", "y", "x"]
    values = np.asarray(data.values, dtype=float)
    axes: list[Any] = []
    for index, dim in enumerate(dims):
        coord = data.coords.get(dim)
        values_for_axis = np.asarray(
            coord.values if coord is not None and coord.ndim == 1 else np.arange(data.sizes[dim]),
            dtype=float,
        )
        if values_for_axis.size < 2 or not np.all(np.isfinite(values_for_axis)):
            raise FieldFormatError(f"field coordinate {dim!r} must contain at least two finite values")
        differences = np.diff(values_for_axis)
        if np.all(differences < 0):
            values = np.flip(values, axis=index)
            values_for_axis = values_for_axis[::-1]
            differences = -differences[::-1]
        if not np.all(differences > 0):
            raise FieldFormatError(f"field coordinate {dim!r} must be monotonic")
        spacing = float(np.mean(differences))
        if not np.allclose(differences, spacing, rtol=1e-4, atol=max(abs(spacing) * 1e-6, 1e-9)):
            raise FieldFormatError(f"field coordinate {dim!r} is irregular; resample it before extracting an isosurface")
        axes.append(values_for_axis)
    return values, (axis_names[0], axis_names[1], axis_names[2]), axes


def _interpolate_axis(values: Any, axis: int, target_size: int, np: Any) -> Any:
    if target_size < 2 or target_size > 160:
        raise ValueError("target field dimensions must be between 2 and 160")
    old_size = values.shape[axis]
    if old_size == target_size:
        return values
    source = np.arange(old_size, dtype=float)
    target = np.linspace(0.0, old_size - 1.0, target_size)
    return np.apply_along_axis(lambda line: np.interp(target, source, line), axis, values)


def trilinear_resample(values: Any, target_shape: tuple[int, int, int]) -> Any:
    """Resample a finite regular scalar field linearly in index space.

    This is deliberately explicit rather than silently applying an interpolation
    method to irregular physical coordinates. Physical axes are checked by the
    calling NetCDF reader and are rescaled alongside the field.
    """
    np, _xr, _measure, _ndimage = _dependencies()
    if len(target_shape) != 3:
        raise ValueError("target_shape must contain exactly three dimensions")
    result = np.asarray(values, dtype=float)
    finite = np.isfinite(result)
    if not finite.any():
        raise FieldFormatError("field contains no finite scalar values")
    result = np.where(finite, result, float(np.min(result[finite])))
    for axis, size in enumerate(target_shape):
        result = _interpolate_axis(result, axis, int(size), np)
    return result


def _mesh_from_field(
    values: Any,
    *,
    axes: list[Any],
    axis_names: tuple[str, str, str],
    iso_fraction: float,
    max_faces: int,
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]], dict[str, Any]]:
    np, _xr, measure, _ndimage = _dependencies()
    if not 100 <= int(max_faces) <= 250_000:
        raise ValueError("max_faces must be between 100 and 250000")
    fraction = _validate_fraction(iso_fraction)
    finite = np.isfinite(values)
    if not finite.any():
        raise FieldFormatError("field contains no finite scalar values")
    lo = float(np.min(values[finite]))
    hi = float(np.max(values[finite]))
    if not hi > lo:
        raise FieldFormatError("field must have a non-zero scalar range for surface extraction")
    level = lo + (hi - lo) * fraction
    filled = np.where(finite, values, lo)
    spacing = tuple(float(np.mean(np.diff(axis))) for axis in axes)
    try:
        vertices, faces, _normals, _values = measure.marching_cubes(filled, level=level, spacing=spacing, allow_degenerate=False)
    except ValueError as exc:
        raise FieldFormatError(f"isosurface level {level:g} does not cross the scalar field") from exc
    if len(faces) > max_faces:
        raise FieldFormatError(f"isosurface has {len(faces)} faces, above max_faces={max_faces}; resample to a lower resolution or raise the cap")
    xyz: list[tuple[float, float, float]] = []
    starts = [float(axis[0]) for axis in axes]
    for vertex in vertices:
        coordinates = {axis: starts[index] + float(vertex[index]) for index, axis in enumerate(axis_names)}
        xyz.append((coordinates["x"], coordinates["y"], coordinates["z"]))
    triangles = [cast(tuple[int, int, int], tuple(int(value) for value in face)) for face in faces]
    return xyz, triangles, {"iso_fraction": fraction, "iso_value": level, "scalar_min": lo, "scalar_max": hi, "face_count": len(triangles)}


def _write_mesh_obj(
    vertices: Iterable[tuple[float, float, float]],
    faces: Iterable[tuple[int, int, int]],
    *,
    name: str,
    workspace: Workspace,
) -> dict[str, Any]:
    workspace.ensure()
    safe = _safe_name(name)
    points = list(vertices)
    triangles = list(faces)
    if not points or not triangles:
        raise FieldFormatError("surface mesh must contain vertices and triangles")
    lines = ["# Generated by octanex-mcp field visualizer", f"o {safe}", "usemtl surface"]
    lines.extend(f"v {x:.6f} {y:.6f} {z:.6f}" for x, y, z in points)
    lines.extend(f"f {a + 1} {b + 1} {c + 1}" for a, b, c in triangles)
    path = workspace.assets_dir / f"{safe}.obj"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"path": str(path), "name": safe, "kind": "field_isosurface", "vertex_count": len(points), "face_count": len(triangles), "bounds": bounds_from_points(points)}


def netcdf_isosurface_to_asset(
    source_path: str | Path,
    *,
    variable: str | None = None,
    time_index: int = 0,
    iso_fraction: float = 0.5,
    resolution: int = 64,
    max_faces: int = 100_000,
    name: str = "netcdf_isosurface",
    workspace: Workspace = Workspace(),
) -> dict[str, Any]:
    """Extract a bounded triangular isosurface from a regular 3D NetCDF scalar field.

    ``iso_fraction`` is a normalized skin-density control: 0 approaches the
    outer low-value envelope, 1 approaches the high-value core. The source is
    linearly resampled to ``resolution`` on each axis before marching cubes.
    """
    np, xr, _measure, _ndimage = _dependencies()
    path = Path(source_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"NetCDF source does not exist: {path}")
    if path.suffix.lower() not in {".nc", ".nc4", ".cdf"}:
        raise FieldFormatError("NetCDF isosurface input must have .nc, .nc4, or .cdf suffix")
    resolution = int(resolution)
    if not 16 <= resolution <= 128:
        raise ValueError("resolution must be between 16 and 128")
    with xr.open_dataset(path) as dataset:
        if variable is None:
            candidates = [key for key, value in dataset.data_vars.items() if value.ndim >= 3]
            if not candidates:
                raise FieldFormatError("NetCDF has no data variable with at least three dimensions")
            variable = candidates[0]
        if variable not in dataset.data_vars:
            raise FieldFormatError(f"NetCDF variable {variable!r} not found; available: {', '.join(dataset.data_vars)}")
        data = dataset[variable]
        if "time" in data.dims:
            if not 0 <= int(time_index) < data.sizes["time"]:
                raise ValueError(f"time_index must be between 0 and {data.sizes['time'] - 1}")
            data = data.isel(time=int(time_index))
        values, axis_names, axes = _regular_axes(data, np)
        target_shape = (resolution, resolution, resolution)
        resampled = trilinear_resample(values, target_shape)
        resampled_axes = [np.linspace(float(axis[0]), float(axis[-1]), resolution) for axis in axes]
        vertices, faces, metadata = _mesh_from_field(resampled, axes=resampled_axes, axis_names=axis_names, iso_fraction=iso_fraction, max_faces=max_faces)
    asset = _write_mesh_obj(vertices, faces, name=name, workspace=workspace)
    asset["source"] = {
        "format": "netcdf",
        "source_path": str(path),
        "variable": variable,
        "time_index": int(time_index) if "time" in data.dims else None,
        "source_shape": list(values.shape),
        "interpolation": "linear_regular_grid",
        "resampled_shape": list(target_shape),
        "axis_names": list(axis_names),
        **metadata,
    }
    return asset


def density_surface_to_asset(
    points: Iterable[Iterable[float]],
    *,
    resolution: int = 48,
    smoothing_sigma: float = 1.2,
    skin_fraction: float = 0.18,
    max_faces: int = 100_000,
    name: str = "point_density_surface",
    workspace: Workspace = Workspace(),
) -> dict[str, Any]:
    """Splat points to a regular grid, smooth density, then extract a skin mesh.

    This is an unsigned density envelope, appropriate for particle/simulation
    clouds. It is not a signed-distance reconstruction of a scanned solid; that
    needs point normals and a separate VTK/Open3D-style workflow.
    """
    np, _xr, _measure, ndimage = _dependencies(density=True)
    parsed: list[tuple[float, float, float]] = []
    for values in points:
        try:
            point = tuple(float(value) for value in values)
        except (TypeError, ValueError):
            continue
        if len(point) == 3 and all(math.isfinite(value) for value in point):
            parsed.append((point[0], point[1], point[2]))
    if len(parsed) < 4:
        raise FieldFormatError("density surface needs at least four finite points")
    resolution = int(resolution)
    if not 16 <= resolution <= 128:
        raise ValueError("resolution must be between 16 and 128")
    if not 0.25 <= float(smoothing_sigma) <= 8.0:
        raise ValueError("smoothing_sigma must be between 0.25 and 8.0 grid cells")
    skin_fraction = _validate_fraction(skin_fraction, name="skin_fraction")
    samples = np.asarray(parsed, dtype=float)
    minima = np.min(samples, axis=0)
    maxima = np.max(samples, axis=0)
    span = float(np.max(maxima - minima))
    padding = max(span * 0.08, 1e-4)
    ranges = [(float(minima[index] - padding), float(maxima[index] + padding)) for index in (2, 1, 0)]
    density, edges = np.histogramdd(samples[:, (2, 1, 0)], bins=(resolution, resolution, resolution), range=ranges)
    if ndimage is None:  # pragma: no cover - guarded by _dependencies(density=True)
        raise FieldDependencyError(FIELD_EXTRA_HINT)
    density = ndimage.gaussian_filter(density, sigma=float(smoothing_sigma), mode="constant")
    axes = [(edge[:-1] + edge[1:]) / 2.0 for edge in edges]
    vertices, faces, metadata = _mesh_from_field(density, axes=axes, axis_names=("z", "y", "x"), iso_fraction=skin_fraction, max_faces=max_faces)
    asset = _write_mesh_obj(vertices, faces, name=name, workspace=workspace)
    asset["source"] = {"format": "point_density", "point_count": len(parsed), "resolution": resolution, "smoothing_sigma": float(smoothing_sigma), "skin_fraction": skin_fraction, **metadata}
    return asset


def field_surface_scene_commands(asset: dict[str, Any], *, color: list[float], preview_path: str) -> list[dict[str, Any]]:
    """Compile a field-derived surface asset into an isolated render sequence."""
    material_name = f"{asset['name']}_surface_material"
    return [
        {"op": "import_geometry", "payload": {"path": asset["path"], "format": "obj", "name": asset["name"]}},
        {"op": "create_material", "payload": {"name": material_name, "kind": "glossy", "color": color, "roughness": 0.32, "metallic": 0.0}},
        {"op": "assign_material", "payload": {"object_name": asset["name"], "material_name": material_name, "group_index": 1}},
        {"op": "set_camera", "payload": camera_for_bounds(asset["bounds"], margin=1.3, fov=42)},
        {"op": "set_lighting", "payload": {"preset": "soft_studio"}},
        {"op": "save_preview", "payload": {"path": preview_path, "width": 1024, "height": 1024, "samples": 128, "min_samples": 16, "timeout_seconds": 300}},
    ]
