#!/usr/bin/env python3
"""Unit tests for scripts/physics_fixture_io.py (pure stdlib, offline)."""
from __future__ import annotations

import csv
import io
import math
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_path = __import__("sys").path
if str(ROOT / "src") not in _path:
    _path.insert(0, str(ROOT / "src"))
if str(ROOT / "scripts") not in _path:
    _path.insert(0, str(ROOT / "scripts"))

from physics_fixture_io import (  # noqa: E402
    Fixtures,
    FixtureProvenance,
    _read_npy,
    _write_npy,
    load_csv_particles,
    load_npz,
    npz_has_numpy,
)


class NpyStdlibRoundTripTests(unittest.TestCase):
    def test_write_then_read_2d(self):
        arr = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        buf = io.BytesIO(_write_npy(arr, (2, 3)))
        data, shape, dtype = _read_npy(buf)
        self.assertEqual(data, arr)
        self.assertEqual(shape, (2, 3))
        self.assertEqual(dtype, "float64")

    def test_write_then_read_3d(self):
        arr = [float(i) for i in range(24)]
        buf = io.BytesIO(_write_npy(arr, (2, 3, 4)))
        data, shape, dtype = _read_npy(buf)
        self.assertEqual(shape, (2, 3, 4))
        self.assertEqual(len(data), 24)

    def test_bad_magic_raises(self):
        with self.assertRaises(ValueError):
            _read_npy(io.BytesIO(b"not npy"))


class LoadCsvParticlesTests(unittest.TestCase):
    def _write_csv(self, tmp: str, with_v=True, with_phase=True) -> Path:
        p = Path(tmp) / "dam-break-small.csv"
        cols = ["x", "y", "z"]
        if with_v:
            cols += ["vx", "vy", "vz"]
        if with_phase:
            cols += ["phase"]
        with p.open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            for i in range(20):
                row = [i * 0.1, (i % 5) * 0.2, 0.0]
                if with_v:
                    row += [0.1 * i, 0.0, -0.05]
                if with_phase:
                    row += [i % 2]
                w.writerow(row)
            # a malformed row (missing z) must be skipped
            w.writerow(["1.0", "2.0"])
        return p

    def test_loads_positions_and_phase(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_csv(tmp)
            res = load_csv_particles(p, source="test")
            cloud = res["cloud"]
            self.assertEqual(cloud.count, 20)
            self.assertEqual(len(cloud.positions), 20)
            self.assertEqual(len(cloud.phases), 20)
            self.assertEqual(cloud.positions[0], (0.0, 0.0, 0.0))
            self.assertEqual(cloud.phases[1], 1)
            prov = res["provenance"]
            self.assertEqual(prov["source_library"], "test")
            self.assertEqual(prov["fixture_shape"], [20, 3])
            self.assertEqual(prov["fixture_loader"], "stdlib-csv")

    def test_missing_required_column_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.csv"
            p.write_text("x,y\n1,2\n")
            with self.assertRaises(ValueError):
                load_csv_particles(p)

    def test_missing_velocity_defaults_to_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_csv(tmp, with_v=False)
            cloud = load_csv_particles(p)["cloud"]
            self.assertEqual(cloud.velocities[0], (0.0, 0.0, 0.0))


class LoadNpzTests(unittest.TestCase):
    def test_numpy_path_if_available(self):
        if not npz_has_numpy():
            self.skipTest("numpy not installed")
        import numpy as np

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "grid.npz"
            # Use numpy to CREATE the fixture (the real production path), then
            # load it back through our loader.
            np.savez(p, temperature=np.zeros((8, 8)), w=np.ones((8, 8)))
            res = load_npz(p, source="numpy-src")
            self.assertIn("temperature", res)
            self.assertIn("w", res)
            self.assertEqual(res["temperature"]["shape"], (8, 8))
            self.assertEqual(res["temperature"]["provenance"]["source_library"], "numpy-src")

    def test_stdlib_fallback_round_trip(self):
        # Force the pure-stdlib code path (no numpy) by monkeypatching the guard.
        import physics_fixture_io as m

        orig = m.npz_has_numpy
        m.npz_has_numpy = lambda: False  # type: ignore[assignment]
        try:
            # Build an .npz by zipping two stdlib-written .npy members.
            with tempfile.TemporaryDirectory() as tmp:
                import zipfile

                p = Path(tmp) / "grid.npz"
                a = io.BytesIO(_write_npy([float(i) for i in range(16)], (4, 4)))
                b = io.BytesIO(_write_npy([1.5] * 9, (3, 3)))
                with zipfile.ZipFile(p, "w") as zf:
                    zf.writestr("temperature.npy", a.getvalue())
                    zf.writestr("w_velocity.npy", b.getvalue())
                res = load_npz(p, source="stdlib-src")
                self.assertEqual(res["temperature"]["shape"], (4, 4))
                self.assertEqual(res["w_velocity"]["shape"], (3, 3))
                self.assertEqual(res["temperature"]["data"][0], 0.0)
                self.assertEqual(res["temperature"]["provenance"]["fixture_loader"], "stdlib-npy")
        finally:
            m.npz_has_numpy = orig


class FixturesRegistryTests(unittest.TestCase):
    def test_path_construction(self):
        p = Fixtures.path("oceananigans", "convection-column", "t0008.npz")
        self.assertTrue(str(p).endswith("examples/fixtures/oceananigans/convection-column/t0008.npz"))

    def test_load_missing_raises(self):
        with self.assertRaises(FileNotFoundError):
            Fixtures.load("oceananigans", "convection-column", "does-not-exist.npz")


if __name__ == "__main__":
    unittest.main()
