#!/usr/bin/env python3
"""Shared cloth-on-rigid drape math for the Genesis B5 fixture + recipe.

Single source of truth so the committed fixture (export_genesis_cloth_on_rigid_fixture.py)
and the recipe renderer (gen_genesis_cloth_on_rigid_recipe.py) cannot drift. The
drape is a deterministic analytic model: a flat cloth sheet at height `cloth_z0`
sinks onto the rigid sphere (final transform) wherever a vertex falls inside the
sphere's shell band, and otherwise keeps a gentle pre-sag toward the center.
"""
from __future__ import annotations

import math
from typing import Any


def drape_vertex(x: float, y: float, z0: float, n: int, sphere_center: list[float], sphere_r: float) -> tuple[float, float, float]:
    half = 3.0  # CLOTH_HALF, kept here as the canonical extent
    # gentle pre-sag toward center (same formula as the recipe's _cloth_surface)
    sag = 0.15 * (math.cos(math.pi * (x + half) / (2 * half)) * 0.5 + 0.5) * (
        math.cos(math.pi * (y + half) / (2 * half)) * 0.5 + 0.5
    )
    z = z0 - sag
    cx, cy, cz = sphere_center
    d = math.dist((x, y, z), (cx, cy, cz))
    if d < sphere_r + 0.4:
        k = sphere_r / max(d, 1e-6)
        x2 = x * k
        y2 = y * k
        z2 = z * k + 0.02 * (z * k - cz)
        return (x2, y2, z2)
    return (x, y, z)


def build_draped_vertices(n: int, cloth_half: float, cloth_z0: float, sphere_center: list[float], sphere_r: float) -> list[list[float]]:
    verts: list[list[float]] = []
    for iy in range(n):
        y = -cloth_half + (2 * cloth_half) * iy / (n - 1)
        for ix in range(n):
            x = -cloth_half + (2 * cloth_half) * ix / (n - 1)
            verts.append(list(drape_vertex(x, y, cloth_z0, n, sphere_center, sphere_r)))
    return verts


def contact_indices(verts: list[list[float]], sphere_center: list[float], sphere_r: float, band: float = 0.35) -> list[int]:
    out: list[int] = []
    for idx, (x, y, z) in enumerate(verts):
        d = math.dist((x, y, z), sphere_center)
        if abs(d - sphere_r) < band:
            out.append(idx)
    return out


def drape_grid_as_surface(verts: list[list[float]], n: int) -> list[list[tuple[float, float, float]]]:
    """Reshape the flat vertex list into an n×n grid of tuples for ObjBuilder.add_surface."""
    return [[(float(verts[i * n + j][0]), float(verts[i * n + j][1]), float(verts[i * n + j][2])) for j in range(n)] for i in range(n)]
