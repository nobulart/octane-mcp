from __future__ import annotations

import importlib.util
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "spike_luisa_scene.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("spike_luisa_scene", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_rgb_png(path: Path) -> None:
    width, height = 4, 3
    pixels = [
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (255, 255, 0),
        (255, 0, 255),
        (0, 255, 255),
        (255, 255, 255),
        (0, 0, 0),
        (128, 64, 32),
        (32, 64, 128),
        (200, 100, 50),
        (50, 100, 200),
    ]
    rows = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            row.extend(pixels[y * width + x])
        rows.append(bytes(row))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    idat = zlib.compress(b"".join(rows))

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b""))


class LuisaSmokeScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_scene_text_contains_renderable_luisa_primitives(self) -> None:
        text = self.module.build_scene_text(resolution=64, spp=4, exr_name="out.exr")
        for needle in [
            "Surface mat_subject : Matte",
            "Shape subject : InlineMesh",
            "Camera camera : Pinhole",
            "resolution { 64, 64 }",
            "spp { 4 }",
            'file { "out.exr" }',
            "integrator : MegaPath",
            "environment : Null",
        ]:
            self.assertIn(needle, text)

    def test_stdlib_png_stats_detect_nonblank_image(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "fixture.png"
            _write_rgb_png(png)
            stats = self.module.read_png_stats(png)
        self.assertEqual((stats.width, stats.height), (4, 3))
        self.assertGreater(stats.stddev, 3.0)
        self.assertEqual(stats.min_value, 0)
        self.assertEqual(stats.max_value, 255)
        self.assertTrue(stats.nonblank)


if __name__ == "__main__":
    unittest.main()
