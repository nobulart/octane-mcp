#!/usr/bin/env python3
"""Export the Oceananigans shallow-water fixture from a real Julia run.

The recipe adapter remains fixture-first: normal tests load the committed `.npz`
without importing Julia/Oceananigans. This script is the provenance bridge that
runs the real local Oceananigans source project, receives CSV arrays from the
Julia exporter, and packages them into the committed fixture format.

Run:
    python3 scripts/export_oceananigans_shallow_water_fixture.py
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "examples" / "fixtures" / "oceananigans" / "shallow-water-front"
FIXTURE_PATH = FIXTURE_DIR / "shallow-water-front.npz"
JULIA_EXPORTER = ROOT / "scripts" / "export_oceananigans_shallow_water_fixture.jl"
DEFAULT_JULIA_PROJECT = Path("/Users/craig/src/Oceananigans.jl")
ARRAY_NAMES = ("bathymetry", "eta", "u", "v")

sys.path.insert(0, str(ROOT / "scripts"))
from physics_fixture_io import load_npz  # noqa: E402


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_csv_grid(path: Path) -> tuple[list[float], tuple[int, int]]:
    rows: list[list[float]] = []
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.reader(fh):
            if not row:
                continue
            rows.append([float(x) for x in row])
    if not rows:
        raise ValueError(f"empty CSV grid: {path}")
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError(f"ragged CSV grid: {path}")
    return [x for row in rows for x in row], (len(rows), width)


def _read_metadata(path: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if key == "grid_shape" and "x" in value:
            out[key] = [int(x) for x in value.split("x", 1)]
        elif key in {"time_steps"}:
            out[key] = int(value)
        elif key in {"dt_seconds", "eta_min", "eta_max", "u_max", "v_max"}:
            out[key] = float(value)
        elif key == "field_names":
            out[key] = [x.strip() for x in value.split(",") if x.strip()]
        else:
            out[key] = value
    return out


def _write_npy_float64(data: list[float], shape: tuple[int, int]) -> bytes:
    total = shape[0] * shape[1]
    if len(data) != total:
        raise ValueError(f"array length {len(data)} != product(shape)={total}")
    header = f"{{'descr': '<f8', 'fortran_order': False, 'shape': {shape}, }}"
    padding = (64 - ((10 + len(header) + 1) % 64)) % 64
    header_bytes = (header + " " * padding + "\n").encode("latin-1")
    data_bytes = struct.pack("<" + "d" * total, *data)
    return b"\x93NUMPY\x01\x00" + struct.pack("<H", len(header_bytes)) + header_bytes + data_bytes


def write_npz_from_csv_bundle(csv_dir: Path, output_path: Path = FIXTURE_PATH) -> dict[str, Any]:
    """Package a Julia-exported CSV bundle as a NumPy-compatible `.npz` fixture."""
    csv_dir = Path(csv_dir)
    arrays: dict[str, tuple[list[float], tuple[int, int]]] = {}
    for name in ARRAY_NAMES:
        arrays[name] = _read_csv_grid(csv_dir / f"{name}.csv")

    shapes = {shape for _data, shape in arrays.values()}
    if len(shapes) != 1:
        raise ValueError(f"Oceananigans arrays must share one shape; got {sorted(shapes)}")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in ARRAY_NAMES:
            data, shape = arrays[name]
            info = zipfile.ZipInfo(f"{name}.npy", date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, _write_npy_float64(data, shape))

    metadata = _read_metadata(csv_dir / "metadata.txt")
    metadata.update({
        "fixture": str(output_path),
        "fixture_sha256": _sha256(output_path),
        "fixture_arrays": list(ARRAY_NAMES),
        "fixture_shape": list(next(iter(shapes))),
        "fixture_loader": "stdlib-npy",
        "fixture_dtype": "float64",
        "source_library": metadata.get("source_library", "Oceananigans.jl"),
    })
    output_path.with_suffix(".json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metadata


def load_npz_arrays(path: Path = FIXTURE_PATH) -> dict[str, Any]:
    """Load fixture arrays through the same adapter loader used by recipe generation."""
    return load_npz(path, source="Oceananigans.jl")


def run_julia_export(csv_dir: Path, *, julia: str | None = None, julia_project: Path = DEFAULT_JULIA_PROJECT, timeout: int = 180) -> dict[str, Any]:
    exe = julia or shutil.which("julia")
    if exe is None:
        raise RuntimeError("julia executable is not on PATH")
    if not julia_project.exists():
        raise RuntimeError(f"Oceananigans Julia project not found: {julia_project}")
    cmd = [exe, f"--project={julia_project}", str(JULIA_EXPORTER), str(csv_dir)]
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
    return {
        "command": cmd,
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def export_fixture(output_path: Path = FIXTURE_PATH, *, julia_project: Path = DEFAULT_JULIA_PROJECT, timeout: int = 180) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="octanex-oceananigans-export-") as td:
        csv_dir = Path(td) / "csv"
        csv_dir.mkdir()
        run = run_julia_export(csv_dir, julia_project=julia_project, timeout=timeout)
        if run["exit_code"] != 0:
            raise RuntimeError(f"Oceananigans exporter failed:\nSTDOUT:\n{run['stdout']}\nSTDERR:\n{run['stderr']}")
        meta = write_npz_from_csv_bundle(csv_dir, output_path)
    meta["julia_stdout"] = re.sub(r"output=\S+", "output=<temp-csv-dir>", run["stdout"].strip())
    meta["julia_stderr_tail"] = run["stderr"][-1000:]
    output_path.with_suffix(".json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return meta


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=FIXTURE_PATH)
    parser.add_argument("--julia-project", type=Path, default=DEFAULT_JULIA_PROJECT)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    meta = export_fixture(args.output, julia_project=args.julia_project, timeout=args.timeout)
    print(json.dumps(meta, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
