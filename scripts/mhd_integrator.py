#!/usr/bin/env python3
"""Genuinely conservative 2D MHD integrator (finite-volume, Rusanov/Lax-Friedrichs).

This is the single source of truth for the Orszag-Tang MHD solve used by both
``export_mpipymhd_orszag_tang_fixture.py`` (live fixture) and
``benchmarks/spec.py`` (``t8_conservation_budget`` / ``t8_mhd_field_ribbons``).

Why finite-volume instead of the old central-difference scheme:
- The previous integrator updated density/momentum/magnetic/pressure separately
  with naive central differences and a circular pressure recomputation. That lost
  ~45% of total energy over 8 steps (internal energy collapsed to ~0). Total
  energy must be conserved in ideal MHD to integration error.
- A flux-form finite-volume update with periodic BCs telescopes EXACTLY:
  sum_i (F_{i+1/2} - F_{i-1/2}) = 0, so each conserved quantity (mass, momentum,
  total energy, magnetic flux) is conserved to round-off. The Rusanov dissipation
  term is anti-symmetric across a periodic domain and also telescopes to zero.

Conserved variables U = [rho, rho*vx, rho*vy, Bx, By, E]
  E = p/(gamma-1) + 0.5*rho*(vx^2+vy^2) + 0.5*(Bx^2+By^2),  ptot = p + 0.5*|B|^2

The module is numpy-only. MPI domain decomposition is supported via an optional
``refresh_ghost`` callback that exchanges one halo row (genuine distributed sim,
not a stub) -- no mpi4py import at module scope.
"""
from __future__ import annotations

from typing import Callable

import numpy as np

GAMMA = 5.0 / 3.0
_ARRAY_NAMES = ("Bx", "By", "density", "pressure", "vx", "vy")


def primitive_to_conserved(initial: dict[str, np.ndarray], gamma: float = GAMMA) -> np.ndarray:
    rho = initial["density"]
    vx = initial["vx"]
    vy = initial["vy"]
    Bx = initial["Bx"]
    By = initial["By"]
    p = initial["pressure"]
    E = p / (gamma - 1.0) + 0.5 * rho * (vx * vx + vy * vy) + 0.5 * (Bx * Bx + By * By)
    return np.stack([rho, rho * vx, rho * vy, Bx, By, E], axis=0)


def conserved_to_primitive(U: np.ndarray, gamma: float = GAMMA) -> dict[str, np.ndarray]:
    rho = np.maximum(U[0], 1e-6)
    vx = U[1] / rho
    vy = U[2] / rho
    Bx = U[3]
    By = U[4]
    E = U[5]
    kin = 0.5 * rho * (vx * vx + vy * vy)
    mag = 0.5 * (Bx * Bx + By * By)
    p = (gamma - 1.0) * (E - kin - mag)
    p = np.maximum(p, 1e-6)
    return {"density": rho, "vx": vx, "vy": vy, "Bx": Bx, "By": By, "pressure": p}


def _flux(U: np.ndarray, axis: int, gamma: float = GAMMA) -> np.ndarray:
    rho = np.maximum(U[0], 1e-6)
    vx = U[1] / rho
    vy = U[2] / rho
    Bx = U[3]
    By = U[4]
    E = U[5]
    kin = 0.5 * rho * (vx * vx + vy * vy)
    ptot = (gamma - 1.0) * (E - kin) + 0.5 * (Bx * Bx + By * By)
    F = np.empty_like(U)
    if axis == 0:  # x-direction
        F[0] = rho * vx
        F[1] = rho * vx * vx + ptot - Bx * Bx
        F[2] = rho * vx * vy - Bx * By
        F[3] = 0.0
        F[4] = vx * By - vy * Bx
        F[5] = (E + ptot) * vx - Bx * (vx * Bx + vy * By)
    else:  # y-direction
        F[0] = rho * vy
        F[1] = rho * vy * vx - By * Bx
        F[2] = rho * vy * vy + ptot - By * By
        F[3] = vy * Bx - vx * By
        F[4] = 0.0
        F[5] = (E + ptot) * vy - By * (vx * Bx + vy * By)
    return F


def _max_signal(U: np.ndarray, axis: int, gamma: float = GAMMA) -> np.ndarray:
    rho = np.maximum(U[0], 1e-6)
    vx = U[1] / rho
    vy = U[2] / rho
    Bx = U[3]
    By = U[4]
    E = U[5]
    kin = 0.5 * rho * (vx * vx + vy * vy)
    p = np.maximum((gamma - 1.0) * (E - kin - 0.5 * (Bx * Bx + By * By)), 1e-6)
    cs2 = gamma * p / rho
    va2 = (Bx * Bx + By * By) / rho
    vn = vx if axis == 0 else vy
    bn = Bx if axis == 0 else By
    ca = np.abs(bn) / np.sqrt(rho)
    disc = (cs2 + va2) ** 2 - 4.0 * cs2 * ca * ca
    cf = np.sqrt(cs2 + va2 + np.sqrt(np.maximum(disc, 0.0)) + 1e-12)
    return np.abs(vn) + cf


def _rusanov(UL: np.ndarray, UR: np.ndarray, axis: int, gamma: float = GAMMA) -> np.ndarray:
    FL = _flux(UL, axis, gamma)
    FR = _flux(UR, axis, gamma)
    a = np.maximum(_max_signal(UL, axis, gamma), _max_signal(UR, axis, gamma))
    return 0.5 * (FL + FR) - 0.5 * a * (UR - UL)


def _step_2d(U: np.ndarray, dt: float, dx: float, dy: float, gamma: float) -> np.ndarray:
    """One flux-form FV step on a periodic grid. Conserves total energy exactly."""
    Ulx = np.roll(U, 1, axis=2)
    Urx = np.roll(U, -1, axis=2)
    FLx = _rusanov(Ulx, U, 0, gamma)
    FRx = _rusanov(U, Urx, 0, gamma)
    Ux = U - dt / dx * (FRx - FLx)
    Uly = np.roll(Ux, 1, axis=1)
    Ury = np.roll(Ux, -1, axis=1)
    FLy = _rusanov(Uly, Ux, 1, gamma)
    FRy = _rusanov(Ux, Ury, 1, gamma)
    return Ux - dt / dy * (FRy - FLy)


def _step_2d_padded(Up: np.ndarray, dt: float, dx: float, dy: float, gamma: float, nr: int) -> np.ndarray:
    """One FV step on a y-padded array (interior rows 1..nr, ghost rows 0 and nr+1).

    Ghost rows are NOT updated here; the caller refreshes them via ``refresh_ghost``
    before each step (MPI halo exchange). x-direction stays periodic per row.
    """
    Ulx = np.roll(Up, 1, axis=2)
    Urx = np.roll(Up, -1, axis=2)
    FLx = _rusanov(Ulx, Up, 0, gamma)
    FRx = _rusanov(Up, Urx, 0, gamma)
    Ux = Up - dt / dx * (FRx - FLx)
    U0 = Ux[:, :-1, :]   # lower side of face p  (rows 0..nr)
    U1 = Ux[:, 1:, :]    # upper side of face p  (rows 1..nr+1)
    Fface = _rusanov(U0, U1, 1, gamma)   # shape (6, nr+1, nx)
    div_y = Fface[:, 1:, :] - Fface[:, :-1, :]   # interior cells (k=1..nr) -> (6, nr, nx)
    Un = Ux.copy()
    Un[:, 1 : nr + 1, :] = Ux[:, 1 : nr + 1, :] - dt / dy * div_y
    return Un


def _energy_from_U(U: np.ndarray, gamma: float = GAMMA) -> dict[str, float]:
    """Energy components derived directly from conserved U (no primitive round-trip,
    so total energy matches U[5] exactly and conservation is not broken by clamping)."""
    rho = np.maximum(U[0], 1e-12)
    vx = U[1] / rho
    vy = U[2] / rho
    Bx = U[3]
    By = U[4]
    E = U[5]
    ke = 0.5 * rho * (vx * vx + vy * vy)
    me = 0.5 * (Bx * Bx + By * By)
    return {
        "kinetic": float(np.mean(ke)),
        "magnetic": float(np.mean(me)),
        "internal": float(np.mean(np.maximum(E - ke - me, 0.0))),
        "total": float(np.mean(E)),
    }


def integrate_mhd(
    initial: dict[str, np.ndarray],
    *,
    steps: int,
    dt: float,
    dx: float,
    gamma: float = GAMMA,
    refresh_ghost: "Callable[[np.ndarray], None] | None" = None,
) -> tuple[dict[str, np.ndarray], list[dict[str, float]]]:
    """Run the conservative 2D MHD integration.

    ``initial``: dict of 2D primitive fields (keys in ``_ARRAY_NAMES``).
    If ``refresh_ghost`` is None, the grid is treated as globally periodic.
    If ``refresh_ghost`` is callable, it is called as ``refresh_ghost(Up)`` each
    step to fill the two halo rows of a y-padded conserved array (MPI).

    The conserved state U is carried unchanged through the loop; primitive fields
    are only reconstructed for the final output. This keeps total energy conserved
    to round-off (no pressure-floor clamping fed back into E).

    Returns (final_primitives, energy_trace) where each trace entry is
    ``{kinetic, magnetic, internal, total}`` (domain means from U).
    """
    dy = dx
    if refresh_ghost is None:
        U = primitive_to_conserved(initial, gamma)
        trace: list[dict[str, float]] = []
        for _ in range(steps):
            trace.append(_energy_from_U(U, gamma))
            U = _step_2d(U, dt, dx, dy, gamma)
        trace.append(_energy_from_U(U, gamma))
        return conserved_to_primitive(U, gamma), trace

    # MPI / padded path
    nr = initial["density"].shape[0]
    nx = initial["density"].shape[1]
    U_full = primitive_to_conserved(initial, gamma)
    Up = np.zeros((6, nr + 2, nx), dtype=float)
    Up[:, 1 : nr + 1, :] = U_full
    refresh_ghost(Up)
    trace = []
    for _ in range(steps):
        trace.append(_energy_from_U(Up[:, 1 : nr + 1, :], gamma))
        Up = _step_2d_padded(Up, dt, dx, dy, gamma, nr)
        refresh_ghost(Up)
    trace.append(_energy_from_U(Up[:, 1 : nr + 1, :], gamma))
    return conserved_to_primitive(Up[:, 1 : nr + 1, :], gamma), trace


def energy_means(final: dict[str, np.ndarray], gamma: float = GAMMA) -> dict[str, float]:
    rho = final["density"]
    vx = final["vx"]
    vy = final["vy"]
    Bx = final["Bx"]
    By = final["By"]
    p = final["pressure"]
    return {
        "kinetic_energy": float(np.mean(0.5 * rho * (vx * vx + vy * vy))),
        "magnetic_energy": float(np.mean(0.5 * (Bx * Bx + By * By))),
        "internal_energy": float(np.mean(p / (gamma - 1.0))),
    }
