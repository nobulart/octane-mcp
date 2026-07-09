"""Offline tests for the WP8 animation manifest grammar (no live Octane)."""

import os
import tempfile
import unittest

from octanex_mcp.animation import (
    AnimationEncodeError,
    AnimationManifest,
    CameraKeyframe,
    build_bake_plan,
    camera_command,
    encode_frames,
    frame_paths,
    orbit_manifest,
    sample_camera,
)


class TestSampleCamera(unittest.TestCase):
    def _manifest(self):
        return AnimationManifest(
            fps=24,
            duration=4.0,
            keyframes=(
                CameraKeyframe(t=0.0, position=(0, 0, 8), target=(0, 0, 0)),
                CameraKeyframe(t=4.0, position=(8, 0, 0), target=(0, 0, 0)),
            ),
        )

    def test_holds_first_before_start(self):
        kf = sample_camera(self._manifest(), -1.0)
        self.assertEqual(kf.position, (0, 0, 8))

    def test_holds_last_after_end(self):
        kf = sample_camera(self._manifest(), 99.0)
        self.assertEqual(kf.position, (8, 0, 0))

    def test_linear_midpoint(self):
        kf = sample_camera(self._manifest(), 2.0)
        self.assertAlmostEqual(kf.position[0], 4.0)
        self.assertAlmostEqual(kf.position[2], 4.0)

    def test_empty_keyframes_rejected(self):
        m = AnimationManifest(fps=24, duration=1.0, keyframes=())
        with self.assertRaises(ValueError):
            sample_camera(m, 0.0)


class TestCameraCommand(unittest.TestCase):
    def test_envelope_shape(self):
        cmd = camera_command(CameraKeyframe(t=1.0, position=(1, 2, 3), target=(0, 0, 0), fov=30.0))
        self.assertEqual(cmd["op"], "set_camera")
        self.assertEqual(cmd["position"], [1, 2, 3])
        self.assertEqual(cmd["target"], [0, 0, 0])
        self.assertEqual(cmd["fov"], 30.0)


class TestBakePlan(unittest.TestCase):
    def test_frame_count_and_zero_start(self):
        m = AnimationManifest(
            fps=24,
            duration=1.0,  # 24 frames
            keyframes=(CameraKeyframe(t=0.0, position=(8, 0, 0), target=(0, 0, 0)),),
        )
        plan = build_bake_plan(m)
        self.assertEqual(len(plan), 24)
        self.assertEqual(plan[0][0], 0)
        self.assertEqual(plan[0][1], 0.0)
        # every entry carries a valid set_camera command
        for _idx, _t, cmd in plan:
            self.assertEqual(cmd["op"], "set_camera")

    def test_zero_fps_degenerate(self):
        m = AnimationManifest(
            fps=0,
            duration=1.0,
            keyframes=(CameraKeyframe(t=0.0, position=(1, 1, 1), target=(0, 0, 0)),),
        )
        plan = build_bake_plan(m)
        self.assertEqual(len(plan), 1)


class TestOrbitManifest(unittest.TestCase):
    def test_segments_plus_one_keyframes(self):
        m = orbit_manifest(radius=8.0, duration=6.0, segments=24)
        self.assertEqual(len(m.keyframes), 25)
        self.assertEqual(m.keyframes[0].t, 0.0)
        self.assertAlmostEqual(m.keyframes[-1].t, 6.0)

    def test_arc_not_chord(self):
        # Full 360 deg: start and end keyframes coincide at (radius,0). A naive
        # 2-point chord would interpolate a CONSTANT (radius,0); our 24-segment
        # arc must pass through the opposite side (-radius,0) at the midpoint.
        m = orbit_manifest(radius=8.0, duration=6.0, segments=24)
        mid = m.keyframes[12]
        self.assertAlmostEqual(mid.position[0], -8.0, places=5)
        self.assertAlmostEqual(mid.position[2], 0.0, places=5)
        self.assertEqual(tuple(mid.target), (0.0, 0.0, 0.0))

    def test_segments_lt_2_rejected(self):
        with self.assertRaises(ValueError):
            orbit_manifest(segments=1)


class TestEncodeAndPaths(unittest.TestCase):
    def test_frame_paths_zero_padded(self):
        m = AnimationManifest(
            fps=24, duration=1.0, basename="anim",
            output_dir="/tmp/r", keyframes=(CameraKeyframe(t=0.0, position=(0, 0, 8), target=(0, 0, 0)),),
        )
        paths = frame_paths(m, 3)
        self.assertEqual(paths[0], "/tmp/r/anim_0000.png")
        self.assertEqual(paths[-1], "/tmp/r/anim_0002.png")

    def test_encode_requires_injected_encoder(self):
        m = AnimationManifest(
            fps=24, duration=1.0, keyframes=(CameraKeyframe(t=0.0, position=(0, 0, 8), target=(0, 0, 0)),),
        )
        with self.assertRaises(AnimationEncodeError):
            encode_frames(m, ["a.png"], "out.mp4")

    def test_encode_injected_encoder_called(self):
        calls = {}

        def _enc(paths, out):
            calls["paths"] = list(paths)
            calls["out"] = out

        m = AnimationManifest(
            fps=24, duration=1.0, keyframes=(CameraKeyframe(t=0.0, position=(0, 0, 8), target=(0, 0, 0)),),
            encoder=_enc,
        )
        out = encode_frames(m, ["a.png", "b.png"], "out.mp4")
        self.assertEqual(out, "out.mp4")
        self.assertEqual(calls["paths"], ["a.png", "b.png"])
        self.assertEqual(calls["out"], "out.mp4")


if __name__ == "__main__":
    unittest.main()
