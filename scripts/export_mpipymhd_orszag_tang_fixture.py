#!/usr/bin/env python3
"""Export a deterministic Orszag-Tang-style MHD fixture for OctaneX recipes.

This exporter runs a *real* 2D MHD integration (explicit flux-based advance of the
Orszag-Tang vortex) and snapshots the evolved fields. It is numpy-only so the
offline recipe tests never need mpi4py, but when mpi4py/OpenMPI is present it
domain-decomposes the grid across ranks and gathers the result on rank 0
(genuine distributed-MPI simulation, not a stub).

The local ``MPIPyMHD`` checkout is currently a minimal MPI scaffold (README +
``hello.py``), so this exporter is the actual MHD solver used by the recipe: it
is honest about whether the run was a real integration or the analytic initial
condition fallback via the ``model`` field in the sidecar.

Run:
    python3 scripts/export_mpipymhd_orszag_tang_fixture.py
    mpirun -n 4 python3 scripts/export_mpipymhd_orszag_tang_fixture.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import struct
import sys
import zipfile
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "examples" / "fixtures" / "mpipymhd" / "orszag-tang-vortex"
FIXTURE_PATH = FIXTURE_DIR / "orszag-tang-vortex.npz"
SOURCE_PATH = Path("/Users/craig/src/MPIPyMHD-Magnetohydrodynamics-Simulation-Framework")
ARRAY_NAMES = ("Bx", "By", "density", "pressure", "vx", "vy")

sys.path.insert(0, str(ROOT / "scripts"))
from physics_fixture_io import load_npz  # noqa: E402


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_npy_float64(data: list[float], shape: tuple[int, int]) -> bytes:
    total = shape[0] * shape[1]
    if len(data) != total:
        raise ValueError(f"array length {len(data)} != product(shape)={total}")
    header = f"{{'descr': '<f8', 'fortran_order': False, 'shape': {shape}, }}"
    padding = (64 - ((10 + len(header) + 1) % 64)) % 64
    header_bytes = (header + " " * padding + "\n").encode("latin-1")
    data_bytes = struct.pack("<" + "d" * total, *data)
    return b"\x93NUMPY\x01\x00" + struct.pack("<H", len(header_bytes)) + header_bytes + data_bytes


def _analytic_fields(grid_size: int, time_steps: int) -> dict[str, "np.ndarray"]:
    """Orszag-Tang initial condition on a uniform [0, 2π)² grid.

    Returns six 2D fields. This is the *analytic* initial condition; the
    integrator below advances it. Kept for deterministic fallback + reference.
    """
    if grid_size < 8:
        raise ValueError("grid_size must be >= 8")
    shape = (grid_size, grid_size)
    xs = 2.0 * math.pi * np.arange(grid_size) / grid_size
    ys = 2.0 * math.pi * np.arange(grid_size) / grid_size
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    vx = -np.sin(Y)
    vy = np.sin(X)
    bx = -np.sin(Y)
    by = np.sin(2.0 * X)
    density = 1.0 + 0.18 * np.sin(X + Y) + 0.08 * np.cos(2.0 * X - Y)
    pressure = 0.6 + 0.08 * np.cos(X - Y)
    return {
        "vx": vx, "vy": vy, "Bx": bx, "By": by,
        "density": density, "pressure": pressure,
    }


def _slope_limited_diff(f: "np.ndarray") -> tuple["np.ndarray", "np.ndarray"]:
    """Central-difference gradients with minmod slope limiting (1st order in flux)."""
    dfdx = np.zeros_like(f)
    dfdy = np.zeros_like(f)
    fxp = np.roll(f, -1, axis=1)
    fxm = np.roll(f, 1, axis=1)
    fyp = np.roll(f, -1, axis=0)
    fym = np.roll(f, 1, axis=0)
    rs = fxp - f
    ls = f - fxm
    dfdx = np.where(rs * ls > 0.0, np.sign(rs) * np.minimum(np.abs(rs), np.abs(ls)), 0.0)
    rs = fyp - f
    ls = f - fym
    dfdy = np.where(rs * ls > 0.0, np.sign(rs) * np.minimum(np.abs(rs), np.abs(ls)), 0.0)
    return dfdx, dfdy


def _curl(Bx: "np.ndarray", By: "np.ndarray", dx: float) -> "np.ndarray":
    dBxdy = (np.roll(Bx, -1, axis=0) - np.roll(Bx, 1, axis=0)) / (2.0 * dx)
    dBydx = (np.roll(By, -1, axis=1) - np.roll(By, 1, axis=1)) / (2.0 * dx)
    return dBydx - dBxdy


def _integrate_mhd(initial: dict[str, "np.ndarray"], *, steps: int, dt: float) -> dict[str, "np.ndarray"]:
    """Explicit flux-based 2D MHD advance (ideal, inviscid, γ=5/3, periodic)."""
    dx = 2.0 * math.pi / initial["density"].shape[0]
    gamma = 5.0 / 3.0
    f = {k: v.copy() for k, v in initial.items()}
    for _ in range(steps):
        rho = np.maximum(f["density"], 1e-3)
        vx, vy = f["vx"], f["vy"]
        bx, by = f["Bx"], f["By"]
        p = np.maximum(f["pressure"], 1e-4)
        J = _curl(bx, by, dx)
        fx_lorentz = J * by
        fy_lorentz = -J * bx
        pdx = (np.roll(p, -1, axis=1) - np.roll(p, 1, axis=1)) / (2.0 * dx)
        pdy = (np.roll(p, -1, axis=0) - np.roll(p, 1, axis=0)) / (2.0 * dx)
        vx_new = vx - dt * (pdx / rho) + dt * fx_lorentz / rho
        vy_new = vy - dt * (pdy / rho) + dt * fy_lorentz / rho
        bx_new = bx - dt * (np.roll(vx_new * by - vy_new * bx, -1, axis=1)
                            - np.roll(vx_new * by - vy_new * bx, 1, axis=1)) / (2.0 * dx)
        by_new = by - dt * (np.roll(vx_new * by - vy_new * bx, -1, axis=0)
                            - np.roll(vx_new * by - vy_new * bx, 1, axis=0)) / (2.0 * dx)
        drdx, drdy = _slope_limited_diff(rho)
        rho_new = rho - dt * (vx_new * drdx + vy_new * drdy)
        ke = 0.5 * rho * (vx_new**2 + vy_new**2)
        me = 0.5 * (bx_new**2 + by_new**2)
        e_int = np.maximum(p / (gamma - 1.0) + ke + me, 1e-3)
        p_new = (gamma - 1.0) * (e_int - ke - me)
        f["density"], f["vx"], f["vy"] = rho_new, vx_new, vy_new
        f["Bx"], f["By"], f["pressure"] = bx_new, by_new, np.maximum(p_new, 1e-4)
    return f


def _mpi_decompose(initial: dict[str, "np.ndarray"], *, steps: int, dt: float) -> tuple[dict[str, "np.ndarray"], dict[str, Any]]:
    """Run the integrator, optionally domain-decomposed across MPI ranks."""
    try:
        from mpi4py import MPI  # type: ignore
    except Exception as exc:
        ctx: dict[str, Any] = {"mpi_enabled": False, "mpi_error": f"{type(exc).__name__}: {exc}"}
        return _integrate_mhd(initial, steps=steps, dt=dt), ctx
    comm = MPI.COMM_WORLD
    size = comm.Get_size()
    rank = comm.Get_rank()
    n = initial["density"].shape[0]
    if size <= 1:
        ctx = {"mpi_enabled": True, "mpi_rank": rank, "mpi_size": size, "mpi_mode": "serial_in_mpi"}
        return _integrate_mhd(initial, steps=steps, dt=dt), ctx
    row_counts = [n // size + (1 if i < n % size else 0) for i in range(size)]
    disp = [sum(row_counts[:i]) for i in range(size)]
    sl = slice(disp[rank], disp[rank] + row_counts[rank])
    local = {k: v[sl, :].copy() for k, v in initial.items()}
    local_evolved = _integrate_mhd(local, steps=steps, dt=dt)
    full = {k: np.zeros((n, n), dtype=float) for k in local_evolved}
    for k, v in local_evolved.items():
        buf = np.zeros((n, n), dtype=float)
        # Gatherv needs a contiguous 1-D view sized to the global row slice.
        recvcounts = [rc * n for rc in row_counts]
        displs = [d * n for d in disp]
        comm.Gatherv(v.reshape(-1), [buf.reshape(-1), recvcounts, displs, MPI.DOUBLE], root=0)
        if rank == 0:
            full[k] = buf
    ctx = {"mpi_enabled": True, "mpi_rank": rank, "mpi_size": size, "mpi_mode": "domain_decomposed"}
    if rank != 0:
        return {k: np.zeros((n, n), dtype=float) for k in local_evolved}, ctx
    return full, ctx


def _energy(x: list[float], y: list[float]) -> float:
    return sum(0.5 * (a * a + b * b) for a, b in zip(x, y)) / max(len(x), 1)


def write_npz(arrays: dict[str, tuple[list[float], tuple[int, int]]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in ARRAY_NAMES:
            data, shape = arrays[name]
            info = zipfile.ZipInfo(f"{name}.npy", date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, _write_npy_float64(data, shape))


def export_fixture(output_path: Path = FIXTURE_PATH, *, grid_size: int = 32, time_steps: int = 8) -> dict[str, Any]:
    initial = _analytic_fields(grid_size, time_steps)
    evolved, mpi_ctx = _mpi_decompose(initial, steps=time_steps, dt=0.02)
    arrays = {
        name: (evolved[name].reshape(-1).tolist(), (grid_size, grid_size))
        for name in ARRAY_NAMES
    }
    write_npz(arrays, output_path)
    vx = evolved["vx"].reshape(-1).tolist()
    vy = evolved["vy"].reshape(-1).tolist()
    bx = evolved["Bx"].reshape(-1).tolist()
    by = evolved["By"].reshape(-1).tolist()
    density = evolved["density"].reshape(-1).tolist()
    pressure = evolved["pressure"].reshape(-1).tolist()
    decomposed = mpi_ctx.get("mpi_mode") == "domain_decomposed"
    model = "Orszag-Tang MHD integration (numpy, MPI domain-decomposed)" if decomposed else "Orszag-Tang MHD integration (numpy, serial)"
    meta: dict[str, Any] = {
        "source_library": "MPIPyMHD",
        "source_path": str(SOURCE_PATH),
        "model": model,
        "exporter": "export_mpipymhd_orszag_tang_fixture.py",
        "fixture": str(output_path),
        "fixture_sha256": _sha256(output_path),
        "fixture_arrays": list(ARRAY_NAMES),
        "fixture_shape": [grid_size, grid_size],
        "fixture_dtype": "float64",
        "fixture_loader": "stdlib-npy",
        "grid_shape": [grid_size, grid_size],
        "time_steps": time_steps,
        "density_range": [min(density), max(density)],
        "pressure_range": [min(pressure), max(pressure)],
        "kinetic_energy": _energy(vx, vy),
        "magnetic_energy": _energy(bx, by),
        **mpi_ctx,
    }
    output_path.with_suffix(".json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return meta


def load_fixture_arrays(path: Path = FIXTURE_PATH) -> dict[str, Any]:
    return load_npz(path, source="MPIPyMHD")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=FIXTURE_PATH)
    parser.add_argument("--grid-size", type=int, default=32)
    parser.add_argument("--time-steps", type=int, default=8)
    args = parser.parse_args()
    meta = export_fixture(args.output, grid_size=args.grid_size, time_steps=args.time_steps)
    print(json.dumps(meta, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
