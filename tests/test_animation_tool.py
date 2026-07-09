"""Tests for the WP8 animation bake MCP tool (octane_build_animation) and its
HTTP gateway parity, plus the underlying ``build_animation_commands`` helper.

The WP8 animation DSL (``animation.py``) models a camera-orbit bake and turns it
into per-frame ``set_camera`` + ``save_preview`` command envelopes. This test
exercises the *tool* layer: calling the tool must (a) register on the MCP server,
(b) return exactly ``2 * frames`` queued command responses (each a real
``write_command`` result carrying ``op`` + a queue ``path``), in the alternating
``set_camera`` / ``save_preview`` order that drives a camera orbit, and (c) agree
with the gateway dispatch on the frame count. The returned ``path`` values are
real files in the OctaneMCP queue, so we confirm they exist on disk and parse back
to the asserted ops (proving the bridge would drain genuine commands). No Octane
session, no Lua edit, no heavy dependency required.

Run with: `PYTHONPATH= uv run python -m unittest tests.test_animation_tool`
"""

from __future__ import annotations

import asyncio
import json
import unittest
from pathlib import Path

from octanex_mcp.animation import orbit_manifest, build_animation_commands
from octanex_mcp.server import build_mcp


def _call_tool(name: str, args: dict) -> dict:
    raw = asyncio.run(build_mcp()._tool_manager.call_tool(name, args))
    text = raw[1]["content"][0]["text"] if isinstance(raw, tuple) else raw
    return json.loads(text)


class BuildAnimationCommandsTests(unittest.TestCase):
    def test_build_animation_commands_emits_two_per_frame(self) -> None:
        manifest = orbit_manifest(fps=4, duration=2.0, segments=8)
        cmds = build_animation_commands(manifest)
        # 4 fps * 2 s = 8 frames -> 8 set_camera + 8 save_preview.
        self.assertEqual(len(cmds), 16)
        ops = [c["op"] for c in cmds]
        self.assertEqual(ops[0::2], ["set_camera"] * 8)
        self.assertEqual(ops[1::2], ["save_preview"] * 8)

    def test_save_preview_paths_are_zero_padded(self) -> None:
        manifest = orbit_manifest(fps=4, duration=2.0, segments=8, output_dir="renders")
        cmds = build_animation_commands(manifest)
        previews = [c["payload"]["path"] for c in cmds[1::2]]
        self.assertEqual(previews[0], "renders/frame_0000.png")
        self.assertEqual(previews[-1], "renders/frame_0007.png")

    def test_camera_payload_uses_sampled_pose(self) -> None:
        manifest = orbit_manifest(radius=8.0, height=2.0, segments=4)
        cmds = build_animation_commands(manifest)
        cam = cmds[0]["payload"]
        # First keyframe sits at angle 0 -> (radius, height, 0)-ish.
        self.assertAlmostEqual(cam["position"][0], 8.0, places=4)
        self.assertAlmostEqual(cam["position"][1], 2.0, places=4)

    def test_quality_passthrough(self) -> None:
        manifest = orbit_manifest(fps=2, duration=1.0, segments=4)
        cmds = build_animation_commands(manifest, quality="high")
        payloads = [c["payload"] for c in cmds if c["op"] == "save_preview"]
        for p in payloads:
            self.assertEqual(p["quality"], "high")

    def test_output_dir_override_is_absolute(self) -> None:
        manifest = orbit_manifest(fps=2, duration=1.0, segments=4)
        cmds = build_animation_commands(manifest, output_dir="/abs/renders")
        previews = [c["payload"]["path"] for c in cmds if c["op"] == "save_preview"]
        for p in previews:
            self.assertTrue(p.startswith("/abs/renders/frame_"), p)
        # Default (no override) is the relative "renders" (caller must absolutize).
        cmds2 = build_animation_commands(manifest)
        self.assertTrue(cmds2[1]["payload"]["path"].startswith("renders/frame_"))


class AnimationToolTests(unittest.TestCase):
    def test_tool_registers_on_server(self) -> None:
        names = {t.name for t in build_mcp()._tool_manager.list_tools()}
        self.assertIn("octane_build_animation", names)

    def test_tool_returns_per_frame_command_responses(self) -> None:
        data = _call_tool(
            "octane_build_animation", {"fps": 5, "duration": 2.0, "segments": 10}
        )
        self.assertTrue(data.get("ok"), data)
        # 5 fps * 2 s = 10 frames; each frame = set_camera + save_preview.
        self.assertEqual(data["frames"], 10)
        cmds = data["queued_commands"]
        self.assertEqual(len(cmds), 20)
        ops = [c["op"] for c in cmds]
        self.assertEqual(ops[0::2], ["set_camera"] * 10)
        self.assertEqual(ops[1::2], ["save_preview"] * 10)
        # Each response is a real write_command result with a queue path.
        for c in cmds:
            self.assertIn("path", c)
            self.assertTrue(c["queued"])
        # Camera poses vary across frames (orbit, not a static shot).
        cam_positions = [
            tuple(json.loads(Path(c["path"]).read_text())["payload"]["position"])
            for c in cmds
            if c["op"] == "set_camera"
        ]
        self.assertEqual(len({p for p in cam_positions}), 10)

    def test_tool_accepts_quality_tier(self) -> None:
        data = _call_tool(
            "octane_build_animation", {"fps": 2, "duration": 1.0, "quality": "high"}
        )
        self.assertTrue(data.get("ok"), data)
        # The quality tier must propagate into the save_preview payloads on disk.
        previews = [
            json.loads(Path(c["path"]).read_text())["payload"].get("quality")
            for c in data["queued_commands"]
            if c["op"] == "save_preview"
        ]
        self.assertEqual(previews, ["high"] * 2)

    def test_tool_writes_real_queue_files(self) -> None:
        # End-to-end: the tool's returned command responses point at real files
        # in the OctaneMCP queue. Confirm those files exist and parse back to the
        # same op sequence (proves the bridge would drain genuine commands).
        data = _call_tool(
            "octane_build_animation", {"fps": 4, "duration": 1.0, "segments": 8}
        )
        self.assertTrue(data.get("ok"), data)
        # 4 fps * 1 s = 4 frames -> 8 commands (set_camera + save_preview each).
        self.assertEqual(data["frames"], 4)
        paths = [c["path"] for c in data["queued_commands"]]
        self.assertEqual(len(paths), 8)
        ops_on_disk = []
        for p in paths:
            self.assertTrue(Path(p).exists(), p)
            ops_on_disk.append(json.loads(Path(p).read_text())["op"])
        self.assertEqual(ops_on_disk, [c["op"] for c in data["queued_commands"]])


class AnimationGatewayParityTests(unittest.TestCase):
    def test_gateway_parity_returns_same_frame_count(self) -> None:
        from octanex_mcp import gateway

        result = gateway.call_tool(
            "octane_build_animation", {"fps": 6, "duration": 2.0, "segments": 12}
        )
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["result"]["frames"], 12)
        cmds = result["result"]["queued_commands"]
        self.assertEqual(len(cmds), 24)
        ops = [c["op"] for c in cmds]
        self.assertEqual(ops[0::2], ["set_camera"] * 12)
        self.assertEqual(ops[1::2], ["save_preview"] * 12)


if __name__ == "__main__":
    unittest.main()
