"""Tests for the label-overlay projection + layout (std-lib only paths).

Pillow is NOT in the default venv (only the ``harvest`` extra), so the
raster ``draw_label_overlay`` is exercised only for its missing-dependency
message. The projection/layout logic is pure stdlib and fully tested here.
"""

import math
import unittest

from octanex_mcp.annotation import (
    CameraView,
    LabelPlacement,
    compute_label_layout,
    draw_label_overlay,
    project_world_to_screen,
)


class TestProjection(unittest.TestCase):
    def test_centered_axes(self):
        # Camera at origin looking down -Z (default up Y). A point straight
        # ahead at (0,0,-10) with 90deg fov, square frame, should land
        # dead-center.
        cam = CameraView(position=(0, 0, 0), target=(0, 0, -1), fov_deg=90.0)
        p = project_world_to_screen((0, 0, -10), cam, 100, 100)
        assert p is not None
        self.assertAlmostEqual(p[0], 50.0, places=3)
        self.assertAlmostEqual(p[1], 50.0, places=3)
        self.assertAlmostEqual(p[2], 10.0, places=3)

    def test_positive_x_is_right(self):
        # Point to the +X side of view should map right of center.
        cam = CameraView(position=(0, 0, 0), target=(0, 0, -1), fov_deg=90.0)
        p = project_world_to_screen((5, 0, -10), cam, 100, 100)
        assert p is not None
        self.assertGreater(p[0], 50.0)

    def test_positive_y_is_up(self):
        cam = CameraView(position=(0, 0, 0), target=(0, 0, -1), fov_deg=90.0)
        p = project_world_to_screen((0, 5, -10), cam, 100, 100)
        assert p is not None
        self.assertLess(p[1], 50.0)  # up -> smaller pixel y

    def test_behind_camera_is_none(self):
        cam = CameraView(position=(0, 0, 0), target=(0, 0, -1), fov_deg=90.0)
        self.assertIsNone(project_world_to_screen((0, 0, 10), cam, 100, 100))

    def test_bad_dimensions(self):
        cam = CameraView(position=(0, 0, 0), target=(0, 0, -1))
        with self.assertRaises(ValueError):
            project_world_to_screen((0, 0, -1), cam, 0, 100)


class TestLayout(unittest.TestCase):
    def _scene(self):
        return {
            "camera": {"position": [0, 0, 10], "target": [0, 0, 0], "fov": 45.0},
            "labels": {"#1": "o0001", "#2": "o0002"},
            "objects": [
                {"uid": "o0001", "bounds": {"center": [0, 0, 0]}},
                {"uid": "o0002", "bounds": {"center": [3, 0, 0]}},
            ],
        }

    def test_placements_projected(self):
        pls = compute_label_layout(self._scene(), width=1280, height=720)
        badges = {p.badge for p in pls if p.visible}
        self.assertEqual(badges, {"#1", "#2"})
        # #1 at origin (centered) should be near horizontal middle; #2 (+x) right.
        p1 = next(p for p in pls if p.badge == "#1")
        p2 = next(p for p in pls if p.badge == "#2")
        self.assertAlmostEqual(p1.screen[0], 640.0, delta=2.0)
        self.assertGreater(p2.screen[0], p1.screen[0])

    def test_missing_camera_raises(self):
        scene = self._scene()
        scene.pop("camera")
        with self.assertRaises(ValueError):
            compute_label_layout(scene)

    def test_object_without_bounds_skipped_invisible(self):
        scene = self._scene()
        scene["objects"][1].pop("bounds")
        pls = compute_label_layout(scene)
        p2 = next(p for p in pls if p.badge == "#2")
        self.assertFalse(p2.visible)

    def test_behind_camera_culled(self):
        scene = self._scene()
        scene["camera"] = {"position": [0, 0, 0], "target": [0, 0, -1], "fov": 45.0}
        # both objects now behind the camera (z=0 > camera z=0 looking -z)
        pls = compute_label_layout(scene, cull_behind=True)
        self.assertEqual([p for p in pls if p.visible], [])


class TestRasterMissingDep(unittest.TestCase):
    def test_missing_pillow_hint(self):
        # In the default venv Pillow is absent -> precise install hint.
        with self.assertRaises(RuntimeError) as ctx:
            draw_label_overlay("nope.png", [], "out.png")
        self.assertIn("harvest", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
