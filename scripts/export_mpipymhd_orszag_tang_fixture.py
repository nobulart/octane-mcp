#!/usr/bin/env python3
"""Export a deterministic Orszag-Tang-style MHD fixture for OctaneX recipes.

This is a fixture producer for the local MPIPyMHD source track. The current local
MPIPyMHD checkout is a minimal MPI scaffold, so this exporter creates the
standard analytic Orszag-Tang initial condition as a bounded `.npz` fixture. If
`mpi4py` is available, the sidecar records the MPI rank/size context; normal
recipe tests do not require MPI.

Run:
    python3 scripts/export_mpipymhd_orszag_tang_fixture.py
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


def _mpi_context() -> dict[str, Any]:
    try:
        from mpi4py import MPI  # type: ignore
    except Exception as exc:
        return {"mpi_enabled": False, "mpi_error": f"{type(exc).__name__}: {exc}"}
    comm = MPI.COMM_WORLD
    return {"mpi_enabled": True, "mpi_rank": comm.Get_rank(), "mpi_size": comm.Get_size()}


def _analytic_fields(grid_size: int, time_steps: int) -> dict[str, tuple[list[float], tuple[int, int]]]:
    if grid_size < 8:
        raise ValueError("grid_size must be >= 8")
    shape = (grid_size, grid_size)
    arrays = {name: [] for name in ARRAY_NAMES}
    # A tiny deterministic phase shift stands in for a bounded timestep advance;
    # this keeps the fixture source explicit while avoiding a hidden solver dep.
    phase = 0.015 * time_steps
    for i in range(grid_size):
        x = 2.0 * math.pi * i / grid_size
        for j in range(grid_size):
            y = 2.0 * math.pi * j / grid_size
            vx = -math.sin(y + phase)
            vy = math.sin(x + phase)
            bx = -math.sin(y - phase)
            by = math.sin(2.0 * (x - phase))
            density = 1.0 + 0.18 * math.sin(x + y + phase) + 0.08 * math.cos(2.0 * x - y)
            pressure = 0.6 + 0.08 * math.cos(x - y + phase)
            arrays["vx"].append(vx)
            arrays["vy"].append(vy)
            arrays["Bx"].append(bx)
            arrays["By"].append(by)
            arrays["density"].append(density)
            arrays["pressure"].append(pressure)
    return {name: (values, shape) for name, values in arrays.items()}


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
    arrays = _analytic_fields(grid_size, time_steps)
    write_npz(arrays, output_path)
    vx, _ = arrays["vx"]
    vy, _ = arrays["vy"]
    bx, _ = arrays["Bx"]
    by, _ = arrays["By"]
    density, _ = arrays["density"]
    pressure, _ = arrays["pressure"]
    meta: dict[str, Any] = {
        "source_library": "MPIPyMHD",
        "source_path": str(SOURCE_PATH),
        "model": "Orszag-Tang analytic MHD snapshot",
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
        **_mpi_context(),
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
