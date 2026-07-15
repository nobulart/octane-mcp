#!/usr/bin/env python3
"""Fixture IO for physical-simulation recipe adapters.

This module is the *adapter* boundary between external simulators
(Oceananigans, SPlisHSPlasH, Genesis, MPIPyMHD, ...) and the OctaneX recipe
pipeline. It deliberately takes **no runtime dependency** on those libraries:
recipes load small exported fixtures (.npz grids, .csv particles) that were
generated once from the source simulator and committed under
``examples/fixtures/<source>/<slug>/``.

Design:
  * ``.npz`` is NumPy's zip-of-``.npy`` container. We prefer NumPy when it is
    available (fully correct). When it is NOT available we fall back to a
    stdlib loader that handles the common ``.npy`` v1/v2 layout for 1-D/2-D
    float arrays (the shapes recipe adapters actually consume). This keeps the
    offline recipe contract runnable on a bare checkout.
  * ``.csv`` particle files are read with the stdlib ``csv`` module. Expected
    columns for particle fixtures: ``x,y,z`` plus optional ``phase`` and
    ``vx,vy,vz`` (velocity). Rows with missing coordinates are skipped.
  * Every loader attaches *provenance* metadata (source file, sha256, shape,
    dtype) so adapters can embed it into the recipe ``simulation`` block
    honestly.

Run the unit tests with:
    PYTHONPATH= uv run python -m unittest tests.test_physics_fixture_io -v
"""
from __future__ import annotations

import csv
import hashlib
import io
import math
import re
import struct
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

__all__ = [
    "FixtureProvenance",
    "load_npz",
    "load_csv_particles",
    "npz_has_numpy",
    "Fixtures",
]


# --------------------------------------------------------------------------- #
# Provenance                                                                   #
# --------------------------------------------------------------------------- #
@dataclass
class FixtureProvenance:
    source: str
    path: str
    sha256: str
    shape: tuple[int, ...] = ()
    dtype: str = ""
    loader: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_library": self.source,
            "fixture": self.path,
            "fixture_sha256": self.sha256,
            "fixture_shape": list(self.shape),
            "fixture_dtype": self.dtype,
            "fixture_loader": self.loader,
        }


def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# .npy (stdlib, minimal) — supports float32/float64 1-D/2-D/3-D arrays         #
# --------------------------------------------------------------------------- #
def _read_npy(stream: io.BytesIO) -> tuple[list[float], tuple[int, ...], str]:
    """Parse a minimal .npy (v1/v2) float array from a binary stream.

    Returns (flat_data, shape, dtype_name). Supports little-endian float32 and
    float64 with C-order, 1-D/2-D/3-D. Raises ValueError on unsupported layout.
    """
    magic = stream.read(6)
    if magic[:6] != b"\x93NUMPY":
        raise ValueError("not a .npy file (bad magic)")
    major = stream.read(1)
    minor = stream.read(1)
    if major == b"\x01":
        header_len = struct.unpack("<H", stream.read(2))[0]
    elif major == b"\x02":
        header_len = struct.unpack("<I", stream.read(4))[0]
    else:
        raise ValueError(f"unsupported .npy major version {major!r}")
    header = stream.read(header_len).decode("latin-1")
    # Header example: {'descr': '<f8', 'fortran_order': False, 'shape': (2, 2), }
    # Parse with regex (robust against commas inside the shape tuple).
    descr_m = re.search(r"['\"]descr['\"]\s*:\s*['\"]([^'\"]+)['\"]", header)
    shape_m = re.search(r"['\"]shape['\"]\s*:\s*\(([^)]*)\)", header)
    if not descr_m or not shape_m:
        raise ValueError(f"could not parse npy header: {header!r}")
    descr = descr_m.group(1)
    nums = [int(x) for x in re.findall(r"-?\d+", shape_m.group(1))]
    shape: tuple[int, ...] = tuple(nums)
    if descr not in ("<f4", "<f8", "|f4", "|f8", "f4", "f8"):
        raise ValueError(f"unsupported npy dtype {descr!r} (only float32/64 supported)")
    itemsize = 4 if descr.endswith("f4") else 8
    total = 1
    for s in shape:
        total *= int(s)
    raw = stream.read(total * itemsize)
    if len(raw) < total * itemsize:
        raise ValueError("truncated .npy data")
    fmt = "<" + ("f" if itemsize == 4 else "d") * total
    data = list(struct.unpack(fmt, raw))
    return data, tuple(int(s) for s in shape), ("float32" if itemsize == 4 else "float64")


def _write_npy(arr: Sequence[float], shape: tuple[int, ...]) -> bytes:
    """Serialize a 1-D/2-D/3-D float list to .npy (float64, little-endian)."""
    total = 1
    for s in shape:
        total *= s
    if len(arr) != total:
        raise ValueError(f"array length {len(arr)} != product(shape)={total}")
    data_bytes = struct.pack("<" + "d" * total, *arr)
    header = f"{{'descr': '<f8', 'fortran_order': False, 'shape': {shape}, }}\n"
    header = header.encode("latin-1")
    # Pad so the data section begins at a 64-byte boundary from the file start
    # (10-byte prefix + header_len must be a multiple of 64). The trailing
    # newline is part of the header length, matching the numpy convention.
    while (10 + len(header)) % 64 != 0:
        header += b" "
    return b"\x93NUMPY\x01\x00" + struct.pack("<H", len(header)) + header + data_bytes


# --------------------------------------------------------------------------- #
# .npz loader                                                                  #
# --------------------------------------------------------------------------- #
def npz_has_numpy() -> bool:
    try:
        import numpy  # noqa: F401

        return True
    except Exception:
        return False


def load_npz(path: str | Path, *, source: str = "unknown") -> dict[str, Any]:
    """Load a ``.npz`` archive into {array_name: {"data": [...], "shape": (...),
    "dtype": str, "provenance": FixtureProvenance}}.

    Uses NumPy when available; otherwise a stdlib fallback parses each ``.npy``
    member (float arrays only). Raises FileNotFoundError / ValueError on bad
    input.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    sha = _sha256_of(path)

    if npz_has_numpy():
        import numpy as np

        out: dict[str, Any] = {}
        with np.load(path) as data:
            names = list(data.files)
            for name in names:
                arr = data[name]
                arr = np.ascontiguousarray(arr)
                if arr.dtype not in (np.float32, np.float64):
                    # cast other numeric dtypes to float64 for adapters
                    arr = arr.astype(np.float64)
                out[name] = {
                    "data": arr.ravel().tolist(),
                    "shape": tuple(int(s) for s in arr.shape),
                    "dtype": str(arr.dtype),
                }
        prov = FixtureProvenance(source, str(path), sha, tuple(), "mixed", "numpy")
        return _wrap(out, prov)

    # stdlib fallback: read each .npy member from the zip
    if not zipfile.is_zipfile(path):
        raise ValueError(f"{path} is not a zip/.npz archive")
    out = {}
    shapes: dict[str, tuple[int, ...]] = {}
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if not name.endswith(".npy"):
                continue
            key = name.rsplit(".", 1)[0]
            raw = zf.read(name)
            data, shape, dtype = _read_npy(io.BytesIO(raw))
            out[key] = {"data": data, "shape": shape, "dtype": dtype}
            shapes[key] = shape
    if not out:
        raise ValueError(f"{path} contained no .npy members")
    # use the largest array's shape as the representative fixture shape
    rep = max(shapes.items(), key=lambda kv: (len(kv[1]), kv[1]))[1] if shapes else ()
    prov = FixtureProvenance(source, str(path), sha, rep, "float32/64", "stdlib-npy")
    return _wrap(out, prov)


def _wrap(arrays: dict[str, Any], prov: FixtureProvenance) -> dict[str, Any]:
    for v in arrays.values():
        v["provenance"] = prov.as_dict()
    return arrays


# --------------------------------------------------------------------------- #
# .csv particle loader                                                        #
# --------------------------------------------------------------------------- #
@dataclass
class ParticleCloud:
    positions: list[tuple[float, float, float]] = field(default_factory=list)
    velocities: list[tuple[float, float, float]] = field(default_factory=list)
    phases: list[int] = field(default_factory=list)
    count: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "positions": self.positions,
            "velocities": self.velocities,
            "phases": self.phases,
            "count": self.count,
        }


def load_csv_particles(path: str | Path, *, source: str = "unknown") -> dict[str, Any]:
    """Load a particle fixture CSV.

    Required columns: ``x,y,z``. Optional: ``phase`` (int), ``vx,vy,vz``
    (float velocity). Rows missing any coordinate are skipped. Returns
    ``{"cloud": ParticleCloud, "provenance": {...}}``.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    sha = _sha256_of(path)
    positions: list[tuple[float, float, float]] = []
    velocities: list[tuple[float, float, float]] = []
    phases: list[int] = []
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        cols = {c.lower(): c for c in (reader.fieldnames or [])}
        need = ["x", "y", "z"]
        if not all(n in cols for n in need):
            missing = [n for n in need if n not in cols]
            raise ValueError(f"CSV missing required columns {missing}; got {reader.fieldnames}")
        has_v = all(v in cols for v in ("vx", "vy", "vz"))
        has_phase = "phase" in cols
        for row in reader:
            try:
                x = float(row[cols["x"]])
                y = float(row[cols["y"]])
                z = float(row[cols["z"]])
            except (TypeError, ValueError):
                continue
            positions.append((x, y, z))
            if has_v:
                try:
                    velocities.append((float(row[cols["vx"]]), float(row[cols["vy"]]),
                                      float(row[cols["vz"]])))
                except (TypeError, ValueError):
                    velocities.append((0.0, 0.0, 0.0))
            else:
                velocities.append((0.0, 0.0, 0.0))
            if has_phase:
                try:
                    phases.append(int(float(row[cols["phase"]])))
                except (TypeError, ValueError):
                    phases.append(0)
            else:
                phases.append(0)
    cloud = ParticleCloud(positions=positions, velocities=velocities,
                          phases=phases, count=len(positions))
    prov = FixtureProvenance(source, str(path), sha, (cloud.count, 3),
                             "csv-particles", "stdlib-csv")
    return {"cloud": cloud, "provenance": prov.as_dict()}


# --------------------------------------------------------------------------- #
# Convenience aggregate                                                       #
# --------------------------------------------------------------------------- #
class Fixtures:
    """Tiny registry so adapters can discover committed fixtures by source."""

    ROOT = Path(__file__).resolve().parents[1] / "examples" / "fixtures"

    @classmethod
    def path(cls, source: str, slug: str, filename: str) -> Path:
        return cls.ROOT / source / slug / filename

    @classmethod
    def load(cls, source: str, slug: str, filename: str) -> dict[str, Any]:
        p = cls.path(source, slug, filename)
        if p.suffix == ".npz":
            return load_npz(p, source=source)
        if p.suffix == ".csv":
            return load_csv_particles(p, source=source)
        raise ValueError(f"unsupported fixture extension {p.suffix}")


if __name__ == "__main__":
    # Smoke: round-trip a tiny .npy via the stdlib writer/reader.
    buf = io.BytesIO(_write_npy([1.0, 2.0, 3.0, 4.0], (2, 2)))
    data, shape, dtype = _read_npy(buf)
    assert data == [1.0, 2.0, 3.0, 4.0] and shape == (2, 2), (data, shape)
    print("physics_fixture_io stdlib npy round-trip OK; numpy available:", npz_has_numpy())
