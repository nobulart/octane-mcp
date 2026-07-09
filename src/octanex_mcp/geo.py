"""Optional geo / terrain visual grammar (WP7, first slice).

This module is the start of the science/geo visual grammar work package. It is
deliberately additive and safe:

* ``elevation_grid_to_obj`` works with pure Python (no optional dependency) and
  turns a 2D elevation grid (e.g. a DEM sample) into a height-field OBJ.
* ``geojson_to_obj`` is the *shapely-backed* GeoJSON → mesh op. Shapely is an
  **optional** dependency (declared in ``pyproject.toml`` under the ``geo``
  extra). If the extra is not installed the op fails loudly with
  ``GeoDependencyError`` and a clear install hint, rather than importing
  shapely at module load time. This keeps the core install lightweight and the
  render server bootable without the extra.

Both ops follow the same contract as ``octanex_mcp.visuals``: write an OBJ into
the workspace ``assets/`` dir, return an asset dict with ``bounds`` so the
caller can frame a bounds camera via ``camera_for_bounds``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .bridge import Workspace
from .visuals import ObjBuilder, _safe_name, bounds_from_points, camera_for_bounds

GEO_EXTRA_HINT = "optional 'geo' dependency missing: install with `uv sync --extra geo` (adds shapely)"


class GeoDependencyError(Exception):
    """Raised when a geo op needs the optional ``geo`` extra that is not installed."""


def is_geo_available() -> bool:
    """Return True if the optional ``geo`` extra (shapely) is importable."""
    try:
        import shapely  # noqa: F401

        return True
    except Exception:
        return False


def require_geo() -> None:
    """Raise ``GeoDependencyError`` if the ``geo`` extra is not installed."""
    if not is_geo_available():
        raise GeoDependencyError(GEO_EXTRA_HINT)


def _extrude_ring_wall(
    b: ObjBuilder,
    ring: Iterable[tuple[float, float]],
    *,
    z_bottom: float,
    z_top: float,
    material: str = "geo",
) -> None:
    """Extrude a closed 2D ring into a vertical wall (two stacked vertex rows)."""
    pts = [(float(x), float(y)) for x, y in ring]
    if len(pts) < 3:
        return
    bottom = [(x, y, z_bottom) for x, y in pts]
    top = [(x, y, z_top) for x, y in pts]
    # add_surface connects row0 (bottom ring) to row1 (top ring) -> the wall.
    b.add_surface(vertices=[bottom, top], material=material)


def elevation_grid_to_obj(
    grid: list[list[float]],
    *,
    name: str = "geo_elevation",
    workspace: Workspace = Workspace(),
    x_range: tuple[float, float] = (-1.0, 1.0),
    y_range: tuple[float, float] = (-1.0, 1.0),
    z_scale: float = 1.0,
    material: str = "terrain",
    base_thickness: float = 0.05,
) -> dict[str, Any]:
    """Turn a 2D elevation grid into a height-field OBJ (pure Python, no extra).

    Args:
        grid: rows x cols matrix of z values (row index -> y, col index -> x).
        x_range / y_range: world-space extents the grid spans.
        z_scale: multiplier applied to grid values for vertical exaggeration.
        base_thickness: solid slab under the surface so it reads as terrain.

    Returns an asset dict compatible with ``scene_commands_for_asset`` /
    ``camera_for_bounds`` (has ``path``, ``name``, ``bounds``, ``kind``).
    """
    workspace.ensure()
    if not grid or not grid[0]:
        raise ValueError("elevation grid must be non-empty 2D")
    rows = len(grid)
    cols = len(grid[0])
    xmin, xmax = float(x_range[0]), float(x_range[1])
    ymin, ymax = float(y_range[0]), float(y_range[1])
    z_values: list[float] = []
    vertices: list[list[tuple[float, float, float]]] = []
    for iy in range(rows):
        row: list[tuple[float, float, float]] = []
        y = ymin + (ymax - ymin) * iy / max(rows - 1, 1)
        src_row = grid[iy]
        for ix in range(cols):
            x = xmin + (xmax - xmin) * ix / max(cols - 1, 1)
            try:
                z = float(src_row[ix]) * z_scale
            except (TypeError, ValueError):
                z = 0.0
            if z != z:  # NaN -> flatten
                z = 0.0
            z_values.append(z)
            row.append((x, y, z))
        vertices.append(row)
    min_z = min(z_values)
    safe = _safe_name(name)
    b = ObjBuilder(safe)
    # Solid base slab under the lowest point so the tile is not paper-thin.
    span_x = abs(xmax - xmin) + 0.4
    span_y = abs(ymax - ymin) + 0.4
    b.add_box(
        center=(0.0, 0.0, min_z - base_thickness / 2.0),
        size=(span_x, span_y, base_thickness),
        material="base",
    )
    b.add_surface(vertices=vertices, material=material)
    path = workspace.assets_dir / f"{safe}.obj"
    path.write_text(b.text(), encoding="utf-8")
    return {
        "path": str(path),
        "name": safe,
        "kind": "elevation_grid",
        "bounds": b.bounds(),
        "rows": rows,
        "cols": cols,
        "x_range": [xmin, xmax],
        "y_range": [ymin, ymax],
        "z_scale": z_scale,
    }


def _geometry_to_geojson(geom: Any) -> dict[str, Any]:
    """Normalize a shapely geometry to a GeoJSON-like dict via its __geo_interface__."""
    if hasattr(geom, "__geo_interface__"):
        return dict(geom.__geo_interface__)
    raise GeoDependencyError("unsupported geometry object (expected shapely geometry)")


def _add_shapely_geometry(b: ObjBuilder, geom: Any, *, z_extrude: float, material: str) -> None:
    from shapely.geometry import (  # local import; guarded by require_geo()
        LineString,
        MultiLineString,
        MultiPoint,
        MultiPolygon,
        Point,
        Polygon,
    )

    gtype = geom.geom_type
    if gtype == "Point":
        x, y = geom.coords[0][0], geom.coords[0][1]
        b.add_box(center=(float(x), float(y), z_extrude / 2.0), size=(0.06, 0.06, max(z_extrude, 0.06)), material=material)
        return
    if gtype == "MultiPoint":
        for p in geom.geoms:
            x, y = p.coords[0][0], p.coords[0][1]
            b.add_box(center=(float(x), float(y), z_extrude / 2.0), size=(0.06, 0.06, max(z_extrude, 0.06)), material=material)
        return
    if gtype in ("LineString", "LinearRing"):
        _extrude_ring_wall(b, list(geom.coords), z_bottom=0.0, z_top=max(z_extrude, 0.02), material=material)
        return
    if gtype == "MultiLineString":
        for line in geom.geoms:
            _extrude_ring_wall(b, list(line.coords), z_bottom=0.0, z_top=max(z_extrude, 0.02), material=material)
        return
    if gtype == "Polygon":
        _extrude_ring_wall(b, list(geom.exterior.coords), z_bottom=0.0, z_top=max(z_extrude, 0.05), material=material)
        for interior in geom.interiors:
            _extrude_ring_wall(b, list(interior.coords), z_bottom=0.0, z_top=max(z_extrude, 0.05), material=material)
        return
    if gtype == "MultiPolygon":
        for poly in geom.geoms:
            _extrude_ring_wall(b, list(poly.exterior.coords), z_bottom=0.0, z_top=max(z_extrude, 0.05), material=material)
            for interior in poly.interiors:
                _extrude_ring_wall(b, list(interior.coords), z_bottom=0.0, z_top=max(z_extrude, 0.05), material=material)
        return
    # Fallback: try geometry collection-like iteration.
    if hasattr(geom, "geoms"):
        for sub in geom.geoms:
            _add_shapely_geometry(b, sub, z_extrude=z_extrude, material=material)
        return
    raise GeoDependencyError(f"unsupported shapely geometry type: {gtype}")


def geojson_to_obj(
    geojson: dict[str, Any],
    *,
    name: str = "geo_scene",
    workspace: Workspace = Workspace(),
    z_extrude: float = 0.5,
    material: str = "geo",
) -> dict[str, Any]:
    """Convert GeoJSON (or a shapely geometry) into an extruded OBJ scene.

    Requires the optional ``geo`` extra (shapely). Raises ``GeoDependencyError``
    with an install hint if shapely is missing. Accepts:

    * a GeoJSON ``FeatureCollection`` / ``Feature`` / bare geometry dict, or
    * any object exposing ``__geo_interface__`` (e.g. a shapely geometry).

    Polygons/multipolygons and lines are extruded into vertical walls; points
    become marker boxes. Returns an asset dict with ``bounds``.
    """
    require_geo()
    from shapely.geometry import shape

    workspace.ensure()
    safe = _safe_name(name)

    # Resolve to a list of shapely geometries.
    geometries: list[Any] = []
    gj = geojson
    if isinstance(gj, dict):
        gtype = gj.get("type")
        if gtype == "FeatureCollection":
            for feat in gj.get("features", []):
                geometries.append(shape(feat["geometry"]))
        elif gtype == "Feature":
            geometries.append(shape(gj.get("geometry", {})))
        elif gtype in ("Point", "MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon", "GeometryCollection"):
            geometries.append(shape(gj))
        else:
            raise GeoDependencyError(f"unsupported GeoJSON type: {gtype!r}")
    elif hasattr(gj, "__geo_interface__"):
        geoms = _geometry_to_geojson(gj)
        return geojson_to_obj(geoms, name=name, workspace=workspace, z_extrude=z_extrude, material=material)
    else:
        raise GeoDependencyError("geojson must be a dict or support __geo_interface__")

    if not geometries:
        raise ValueError("no geometries found in GeoJSON input")

    b = ObjBuilder(safe)
    for geom in geometries:
        _add_shapely_geometry(b, geom, z_extrude=z_extrude, material=material)
    path = workspace.assets_dir / f"{safe}.obj"
    path.write_text(b.text(), encoding="utf-8")
    return {
        "path": str(path),
        "name": safe,
        "kind": "geojson",
        "bounds": b.bounds(),
        "geometry_count": len(geometries),
        "z_extrude": z_extrude,
    }


def geo_asset_to_scene_commands(asset: dict[str, Any], *, material_name: str = "geo_mat", color: list[float] | None = None) -> list[dict[str, Any]]:
    """Build a render command list for a geo/elevation asset (bounds camera).

    Mirrors ``octanex_mcp.visuals.scene_commands_for_asset`` so geo assets drop
    into the same render-review pipeline.
    """
    cam_color = color or [0.55, 0.7, 0.85]
    camera = camera_for_bounds(asset.get("bounds", {"center": [0.0, 0.0, 0.5], "radius": 3.0}))
    return [
        {"op": "import_geometry", "payload": {"path": asset["path"], "format": "obj", "name": asset["name"]}},
        {"op": "create_material", "payload": {"name": material_name, "kind": "glossy", "color": cam_color, "roughness": 0.35}},
        {"op": "assign_material", "payload": {"object_name": asset["name"], "material_name": material_name}},
        {"op": "set_camera", "payload": camera},
        {"op": "set_lighting", "payload": {"preset": "soft_studio"}},
        {"op": "start_render", "payload": {"samples": 128, "width": 1280, "height": 1280}},
    ]
