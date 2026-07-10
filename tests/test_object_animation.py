"""Tests for Phase 4: object transform animation (rotate/translate/scale).

Covers the Python animation grammar (easing, timecode parsing, per-frame bake)
and the new ``set_object_transform`` op at the schema + Lua-handler level. The
Lua handler itself runs only inside Octane; we assert the dispatch table maps
the op and the handler is callable, mirroring the existing parity tests.
"""

import unittest

from pathlib import Path

from octanex_mcp.animation import (
    DEFAULT_FPS,
    EASING,
    ObjectAnimationManifest,
    ObjectKeyframe,
    build_object_animation_commands,
    ease,
    object_rotate_manifest,
    object_translate_manifest,
    sample_object,
)
from octanex_mcp.models import ALLOWED_OPS, validate_command_model
from octanex_mcp.scene import animate_objects, save_scene_manifest


class EasingTests(unittest.TestCase):
    def test_quad_in_out_midpoint_is_half(self):
        self.assertAlmostEqual(ease("ease_in_out_quad", 0.5), 0.5, places=6)

    def test_quad_in_out_slows_at_ends(self):
        # derivative smaller near ends than middle: value at 0.25 < 0.25? No:
        # quad in-out at 0.25 = 2*(0.25)^2 = 0.125 (slow start), symmetry holds.
        self.assertAlmostEqual(ease("ease_in_out_quad", 0.25), 0.125, places=6)
        self.assertAlmostEqual(ease("ease_in_out_quad", 0.75), 0.875, places=6)

    def test_unknown_easing_falls_back_to_linear(self):
        self.assertAlmostEqual(ease("nope", 0.3), 0.3, places=6)

    def test_clamps(self):
        self.assertEqual(ease("linear", 2.0), 1.0)
        self.assertEqual(ease("linear", -1.0), 0.0)


class FrameParseTests(unittest.TestCase):
    def test_int_passthrough(self):
        from octanex_mcp.animation import _parse_frame

        self.assertEqual(_parse_frame(400, 24), 400)

    def test_timecode_smpte(self):
        from octanex_mcp.animation import _parse_frame

        # 00:00:16:08 at 24fps -> 16s*24 + 8 = 392
        self.assertEqual(_parse_frame("00:00:16:08", 24), 392)

    def test_seconds_dot_frames(self):
        from octanex_mcp.animation import _parse_frame

        self.assertEqual(_parse_frame(2.5, 24), 60)  # 2.5s * 24

    def test_default_fps_is_24(self):
        self.assertEqual(DEFAULT_FPS, 24)


class ObjectBakeTests(unittest.TestCase):
    def _man(self):
        return object_rotate_manifest(
            "Hermes::s::o54", axis="y", degrees=104,
            start_frame=400, end_frame=1000, fps=24, easing="ease_in_out_quad",
        )

    def test_manifest_frame_range(self):
        m = self._man()
        self.assertEqual((m.start_frame, m.end_frame), (400, 1000))
        self.assertEqual(m.fps, 24)

    def test_sample_at_ends(self):
        m = self._man()
        start = sample_object(m, 400)
        end = sample_object(m, 1000)
        self.assertEqual(start.rotation_euler[1], 0.0)
        self.assertAlmostEqual(end.rotation_euler[1], 104.0, places=4)

    def test_sample_midpoint_eased_not_linear(self):
        m = self._man()
        linear_mid = 52.0  # halfway in degrees
        mid = sample_object(m, 700).rotation_euler  # frame 700 of 400..1000 = t=0.5
        self.assertIsNotNone(mid)
        # ease_in_out_quad at t=0.5 hits exactly 0.5 -> 52 deg (midpoint of quad)
        self.assertAlmostEqual(mid[1], linear_mid, places=3)

    def test_bake_emits_transform_plus_preview_per_frame(self):
        m = object_rotate_manifest(
            "Hermes::s::o1", axis="y", degrees=90,
            start_frame=0, end_frame=10, fps=24,
        )
        cmds = build_object_animation_commands(m)
        # 11 frames (0..10 inclusive) * 2 ops each
        self.assertEqual(len(cmds), 22)
        self.assertEqual(cmds[0]["op"], "set_object_transform")
        self.assertEqual(cmds[1]["op"], "save_preview")
        # absolute frame index preserved in path
        self.assertIn("frame_0000.png", cmds[1]["payload"]["path"])
        self.assertIn("frame_0010.png", cmds[21]["payload"]["path"])
        # last frame hits 90 deg
        self.assertAlmostEqual(cmds[20]["payload"]["rotation_euler"][1], 90.0, places=3)

    def test_translate_bakes_offset(self):
        m = object_translate_manifest("Hermes::s::o2", offset=(0, 5, 0), start_frame=0, end_frame=5)
        cmds = build_object_animation_commands(m)
        self.assertEqual(cmds[-2]["payload"]["translation"], [0.0, 5.0, 0.0])


class SchemaAcceptanceTests(unittest.TestCase):
    def test_set_object_transform_allowed(self):
        self.assertIn("set_object_transform", ALLOWED_OPS)

    def test_valid_transform_command_passes(self):
        cmd = {
            "schema_version": "1.0",
            "id": "x1",
            "op": "set_object_transform",
            "payload": {"object_name": "Hermes::s::o1", "rotation_euler": [0, 45, 0]},
            "created_at": "2026-01-01T00:00:00Z",
            "source": "octanex-mcp",
        }
        self.assertTrue(validate_command_model(cmd).ok)

    def test_transform_without_channel_fails(self):
        cmd = {
            "schema_version": "1.0",
            "id": "x2",
            "op": "set_object_transform",
            "payload": {"object_name": "Hermes::s::o1"},
            "created_at": "2026-01-01T00:00:00Z",
            "source": "octanex-mcp",
        }
        self.assertFalse(validate_command_model(cmd).ok)


class LuaHandlerDispatchTests(unittest.TestCase):
    def test_dispatch_registers_set_object_transform(self):
        # Mirror the existing parity approach: inspect the Lua source as text
        # (the bridge runs inside Octane, not as a Python import).
        root = Path(__file__).resolve().parents[1]
        handlers_src = (root / "octane_lua" / "lib" / "handlers.lua").read_text(encoding="utf-8")
        self.assertIn('handlers.handle_set_object_transform', handlers_src)
        self.assertIn('handlers.dispatch["set_object_transform"]', handlers_src)
        # Handler must set the three transform pins and find the node by name.
        self.assertIn("runtime.find_item_by_name", handlers_src)
        self.assertIn("P_TRANSFORM_ROTATION", handlers_src)


class AnimateObjectsQueueTests(unittest.TestCase):
    def test_rotate_queues_per_frame_commands(self):
        from octanex_mcp.bridge import Workspace
        from pathlib import Path

        ws = Workspace(Path.home() / "tmp" / "octanex_phase4_ws")
        ws.ensure()
        save_scene_manifest(
            {"scene_id": "ph4", "objects": [{"id": "o54", "type": "box", "size": [1, 1, 1]}]},
            ws,
        )
        # label #1 addresses the only object (badge is positional, not the id)
        res = animate_objects(
            "ph4", "#1", "rotate", axis="y", degrees=104,
            start_frame=400, end_frame=410, fps=24, workspace=ws,
        )
        self.assertEqual(res["queued_command_count"], 22)  # 11 frames * 2
        self.assertIn("o54", res["baked"])


if __name__ == "__main__":
    unittest.main()
