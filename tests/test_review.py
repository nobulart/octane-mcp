from __future__ import annotations

import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from octanex_mcp.review import review_preview, suggest_camera_fix, suggest_lighting_fix
from octanex_mcp.bridge import compare_previews


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


class ReviewTests(unittest.TestCase):
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
        self.assertEqual(result["severity"], "error")
        self.assertIn("diagnosis", result)
        self.assertIn("recommended_actions", result)
        self.assertTrue(any(action["action"] == "increase_lighting" for action in result["recommended_actions"]))

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
        self.assertTrue(any(action["action"] == "reduce_exposure" for action in result["recommended_actions"]))

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
        self.assertEqual(result["severity"], "ok")
        self.assertEqual(result["recommended_actions"], [])

    def test_low_detail_preview_suggests_tighter_camera(self) -> None:
        rows = [[(40, 40, 40)] * 12 for _ in range(12)]
        rows[5][5] = (140, 140, 140)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tiny.png"
            write_rgb_png(path, rows)
            result = review_preview(path)
        self.assertFalse(result["ok"])
        self.assertIn("likely object too small", result["issues"])
        self.assertTrue(any(action["action"] == "tighten_camera" for action in result["recommended_actions"]))

    def test_large_smooth_subject_is_not_mistaken_for_tiny_object(self) -> None:
        rows = [[(14, 18, 34)] * 24 for _ in range(16)]
        for y in range(4, 12):
            for x in range(5, 19):
                rows[y][x] = (42 + x * 4, 120, 180)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "large-smooth-subject.png"
            write_rgb_png(path, rows)
            result = review_preview(path)
        self.assertTrue(result["ok"], result["issues"])
        self.assertNotIn("likely object too small", result["issues"])
        self.assertGreater(result["foreground_bbox_area_percent"], 20.0)

    def test_camera_and_lighting_fix_helpers_return_actionable_patches(self) -> None:
        review = {
            "issues": ["likely object too small", "mostly near-black"],
            "mean_brightness": 2.0,
            "edge_density": 0.2,
        }
        bounds = {"center": [0, 0, 0], "radius": 2.0}
        camera = suggest_camera_fix(review, bounds)
        lighting = suggest_lighting_fix(review)
        self.assertEqual(camera["patch"]["camera"]["target"], [0, 0, 0])
        self.assertLess(camera["patch"]["camera"]["fov"], 45)
        self.assertEqual(lighting["patch"]["lighting"]["preset"], "brighter_studio")


class PreviewComparisonTests(unittest.TestCase):
    def test_compare_previews_returns_comparison_dict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path_a = Path(tmp) / "a.png"
            path_b = Path(tmp) / "b.png"
            # Dark preview
            write_rgb_png(path_a, [[(10, 10, 10)] * 8 for _ in range(8)])
            # Bright preview
            write_rgb_png(path_b, [[(240, 240, 240)] * 8 for _ in range(8)])
            result = compare_previews(path_a, path_b)
        self.assertEqual(result["a"]["mean_brightness"], result["a"].get("mean_brightness"))
        self.assertGreater(result["comparison"]["mean_brightness_diff"], 0)
        self.assertTrue(result["a"]["ok"])
        self.assertTrue(result["b"]["ok"])

    def test_compare_previews_identifies_clipping_differences(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path_a = Path(tmp) / "dark.png"
            path_b = Path(tmp) / "white.png"
            write_rgb_png(path_a, [[(0, 0, 0)] * 4 for _ in range(4)])
            write_rgb_png(path_b, [[(255, 255, 255)] * 4 for _ in range(4)])
            result = compare_previews(path_a, path_b)
        self.assertTrue(result["comparison"]["a_blank"])
        self.assertTrue(result["comparison"]["b_clipped"])

    def test_compare_previews_has_all_comparisons(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path_a = Path(tmp) / "a.png"
            path_b = Path(tmp) / "b.png"
            write_rgb_png(path_a, [[(20, 20, 20)] * 4 for _ in range(4)])
            write_rgb_png(path_b, [[(50, 50, 50)] * 4 for _ in range(4)])
            result = compare_previews(path_a, path_b)
        comparison = result["comparison"]
        self.assertIn("mean_brightness_diff", comparison)
        self.assertIn("contrast_diff", comparison)
        self.assertIn("near_black_diff", comparison)
        self.assertIn("near_white_diff", comparison)
        self.assertIn("edge_density_diff", comparison)
        self.assertIn("both_ok", comparison)
        self.assertIn("a_clipped", comparison)
        self.assertIn("b_clipped", comparison)
        self.assertIn("a_blank", comparison)
        self.assertIn("b_blank", comparison)


if __name__ == "__main__":
    unittest.main()
