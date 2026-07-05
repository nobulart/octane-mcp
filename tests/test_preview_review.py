from __future__ import annotations

import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from octanex_mcp.review import review_preview


def _chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def write_rgb_png(path: Path, rows: list[list[tuple[int, int, int]]]) -> None:
    height = len(rows)
    width = len(rows[0])
    raw = b"".join(b"\x00" + b"".join(bytes(pixel) for pixel in row) for row in rows)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(raw))
        + _chunk(b"IEND", b"")
    )


class PreviewReviewTests(unittest.TestCase):
    def test_missing_preview_reports_not_exists(self) -> None:
        result = review_preview("/tmp/octanex-missing-preview.png")

        self.assertFalse(result["exists"])
        self.assertFalse(result["ok"])
        self.assertIn("file does not exist", result["issues"])

    def test_dark_blank_png_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dark.png"
            write_rgb_png(path, [[(0, 0, 0)] * 4 for _ in range(4)])

            result = review_preview(path)

        self.assertTrue(result["exists"])
        self.assertEqual(result["dimensions"], [4, 4])
        self.assertGreater(result["near_black_percent"], 99.0)
        self.assertTrue(result["likely_blank"])
        self.assertFalse(result["ok"])
        self.assertIn("mostly near-black", result["issues"])

    def test_white_clipped_png_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "white.png"
            write_rgb_png(path, [[(255, 255, 255)] * 5 for _ in range(3)])

            result = review_preview(path)

        self.assertEqual(result["dimensions"], [5, 3])
        self.assertGreater(result["near_white_percent"], 99.0)
        self.assertTrue(result["likely_clipped"])
        self.assertFalse(result["ok"])
        self.assertIn("mostly near-white", result["issues"])

    def test_normal_contrast_png_passes_basic_qa(self) -> None:
        rows = [
            [(0, 0, 0), (80, 80, 80), (160, 160, 160), (255, 255, 255)],
            [(255, 0, 0), (0, 255, 0), (0, 0, 255), (120, 100, 80)],
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "contrast.png"
            write_rgb_png(path, rows)

            result = review_preview(path)

        self.assertTrue(result["ok"], result["issues"])
        self.assertEqual(result["dimensions"], [4, 2])
        self.assertGreater(result["contrast"], 50.0)
        self.assertGreater(result["edge_density"], 0.0)
        self.assertFalse(result["likely_blank"])
        self.assertFalse(result["likely_clipped"])


if __name__ == "__main__":
    unittest.main()
