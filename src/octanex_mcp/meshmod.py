"""Grouping + mesh modifiers for human-numbered scene objects (Phase 3).

This module turns the Phase-2 label/ref language (``#N`` / ``#Gk``) into real
mesh edits:

* **resolution** of ``#1`` and ``#3`` -> subdivide those OBJs (more triangles).
* **group** ``#6 through #10`` and ``#54`` -> merged OBJ under one node name.
* **mesh smoothing** on a group -> Laplacian / subdivision smoothing pass.

It is intentionally gated on the optional ``science`` extra (``trimesh``),
mirroring how ``geo.py`` gates ``shapely``. The core server stays light; the
mesh ops fail loudly with a precise install hint, not an import traceback at
module load. Every op writes a new OBJ into the workspace ``assets/`` dir and
returns ``(path, bounds)`` so the caller can re-point the node via
``swap_geometry`` / grouped import and frame a bounds camera.

The ops are asset-level (replaceable-asset-files primitive): they do not touch
Octane directly. The bridge swap / import is the caller's job, exactly like
``swap_geometry``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Sequence

from .bridge import Workspace

MESH_EXTRA_HINT = "optional 'science' dependency missing: install with `uv sync --extra science` (adds trimesh)"


class MeshDependencyError(Exception):
    """Raised when a mesh op needs the optional ``science`` extra not installed."""


def is_mesh_available() -> bool:
    """Return True if the optional ``science`` extra (trimesh) is importable."""
    try:
        import trimesh  # noqa: F401

        return True
    except Exception:
        return False


def require_mesh() -> None:
    """Raise ``MeshDependencyError`` unless the ``science`` extra is installed."""
    if not is_mesh_available():
        raise MeshDependencyError(MESH_EXTRA_HINT)


def _bounds_of(vertices: Iterable[Sequence[float]]) -> dict[str, Any]:
    xs, ys, zs = [], [], []
    for v in vertices:
        xs.append(float(v[0]))
        ys.append(float(v[1]))
        zs.append(float(v[2]))
    if not xs:
        return {"center": [0.0, 0.0, 0.0], "radius": 0.0, "min": [0, 0, 0], "max": [0, 0, 0]}
    center = [(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2]
    # bounding-sphere radius over the 8 box corners
    radius = 0.0
    for cx, cy, cz in (
        (min(xs), min(ys), min(zs)),
        (max(xs), max(ys), max(zs)),
    ):
        d = ((cx - center[0]) ** 2 + (cy - center[1]) ** 2 + (cz - center[2]) ** 2) ** 0.5
        radius = max(radius, d)
    return {
        "center": center,
        "radius": radius,
        "min": [min(xs), min(ys), min(zs)],
        "max": [max(xs), max(ys), max(zs)],
    }


def subdivide_obj(
    path: str,
    *,
    iterations: int = 1,
    max_faces: int | None = None,
    out_path: str | None = None,
    workspace: Workspace = Workspace(),
) -> dict[str, Any]:
    """Increase mesh resolution by subdividing ``path`` (Catmull-Clark for quads,
    simple for tris). Writes a new OBJ; returns ``{path, bounds, face_count}``.

    ``iterations`` controls tessellation depth; ``max_faces`` is a safety cap so a
    stray "infinite resolution" never explodes the asset (default 200k tris).
    """
    require_mesh()
    import trimesh

    src = Path(path)
    if not src.exists():
        raise FileNotFoundError(f"subdivide target not found: {path}")
    mesh = trimesh.load(str(src), force="mesh")
    if not isinstance(mesh, trimesh.Trimesh):
        # a Scene/PointCloud -> take the first mesh
        mesh = next(iter(mesh.geometry.values())) if hasattr(mesh, "geometry") else mesh
    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError(f"cannot subdivide non-mesh asset: {path}")

    cap = max_faces if max_faces is not None else 200_000
    for _ in range(max(0, int(iterations))):
        if mesh.faces.shape[0] >= cap:
            break
        try:
            mesh = mesh.subdivide()
        except Exception:
            # non-manifold / mixed topology: stop rather than risk scipy-backed
            # ops we don't guarantee. The current level is the result.
            break

    out = Path(out_path) if out_path else workspace.assets_dir / f"{src.stem}_subdiv.obj"
    workspace.ensure()
    out.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(str(out))
    return {
        "path": str(out),
        "bounds": _bounds_of(mesh.vertices),
        "face_count": int(mesh.faces.shape[0]),
        "vertex_count": int(mesh.vertices.shape[0]),
    }


def smooth_obj(
    path: str,
    *,
    iterations: int = 1,
    laplacian: float = 0.5,
    out_path: str | None = None,
    workspace: Workspace = Workspace(),
) -> dict[str, Any]:
    """Apply a mesh-smoothing modifier to ``path`` (Laplacian smoothing pass).

    ``laplacian`` is the per-iteration blend factor (0..1). Writes a new OBJ and
    returns ``{path, bounds, vertex_count}``.
    """
    require_mesh()
    import numpy as np
    import trimesh

    src = Path(path)
    if not src.exists():
        raise FileNotFoundError(f"smooth target not found: {path}")
    mesh = trimesh.load(str(src), force="mesh")
    if not isinstance(mesh, trimesh.Trimesh):
        mesh = next(iter(mesh.geometry.values())) if hasattr(mesh, "geometry") else mesh
    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError(f"cannot smooth non-mesh asset: {path}")

    verts = np.array(mesh.vertices, dtype=float)
    faces = np.array(mesh.faces, dtype=int)
    for _ in range(max(0, int(iterations))):
        # Pure-numpy umbrella Laplacian: move each vertex toward the mean of its
        # one-ring neighbors (cotangent weights skipped for simplicity; uniform
        # weights are adequate for a dev "smoothing" modifier and need no scipy).
        neighbors: dict[int, list[int]] = {i: [] for i in range(len(verts))}
        for a, b, c in faces:
            neighbors[a].append(b); neighbors[a].append(c)
            neighbors[b].append(a); neighbors[b].append(c)
            neighbors[c].append(a); neighbors[c].append(b)
        new_verts = verts.copy()
        for i, nbrs in neighbors.items():
            if not nbrs:
                continue
            mean = verts[nbrs].mean(axis=0)
            new_verts[i] = (1.0 - laplacian) * verts[i] + laplacian * mean
        verts = new_verts
        mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)

    out = Path(out_path) if out_path else workspace.assets_dir / f"{src.stem}_smooth.obj"
    workspace.ensure()
    out.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(str(out))
    return {
        "path": str(out),
        "bounds": _bounds_of(mesh.vertices),
        "vertex_count": int(mesh.vertices.shape[0]),
    }


def merge_objs(
    paths: Sequence[str],
    *,
    out_name: str = "merged",
    out_path: str | None = None,
    workspace: Workspace = Workspace(),
) -> dict[str, Any]:
    """Merge several OBJs into one asset (the geometry meaning of "group these
    objects together"). Each source keeps its transform offset if present in the
    manifest, but at the asset level we concatenate vertices/faces un-transformed
    (callers apply the group transform via the node). Returns ``{path, bounds,
    part_count, vertex_count}``.
    """
    require_mesh()
    import trimesh

    meshes = []
    for p in paths:
        pp = Path(p)
        if not pp.exists():
            raise FileNotFoundError(f"merge target not found: {p}")
        m = trimesh.load(str(pp), force="mesh")
        if not isinstance(m, trimesh.Trimesh):
            m = next(iter(m.geometry.values())) if hasattr(m, "geometry") else m
        if isinstance(m, trimesh.Trimesh):
            meshes.append(m)
    if not meshes:
        raise ValueError("no mergeable meshes found in inputs")
    merged = trimesh.util.concatenate(meshes)

    out = Path(out_path) if out_path else workspace.assets_dir / f"{out_name}.obj"
    workspace.ensure()
    out.parent.mkdir(parents=True, exist_ok=True)
    merged.export(str(out))
    return {
        "path": str(out),
        "bounds": _bounds_of(merged.vertices),
        "part_count": len(meshes),
        "vertex_count": int(merged.vertices.shape[0]),
        "face_count": int(merged.faces.shape[0]),
    }
