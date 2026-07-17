"""Backend protocol conformance + gated live render test for LuisaBackend."""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from octanex_mcp import canvas_scene as cs
from octanex_mcp.backends import Backend, LuisaBackend


class TestLuisaBackendProtocol(unittest.TestCase):
    def test_is_backend_instance(self):
        self.assertIsInstance(LuisaBackend(), Backend)
        self.assertEqual(LuisaBackend().name, "luisa")

    def test_build_emits_scene_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            b = LuisaBackend(workdir=Path(tmp), spp=4, resolution=(64, 64))
            manifest = b.build(cs.default_scene())
            self.assertTrue(manifest["ok"])
            self.assertEqual(manifest["backend"], "luisa")
            scene_file = Path(manifest["scene_file"])
            self.assertTrue(scene_file.exists())
            text = scene_file.read_text()
            self.assertIn("Camera camera : Pinhole", text)
            self.assertIn("spp { 4 }", text)
            self.assertEqual(manifest["spp"], 4)
            self.assertEqual(manifest["resolution"], [64, 64])

    def test_build_rejects_invalid_scene(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            b = LuisaBackend(workdir=Path(tmp))
            with self.assertRaises(ValueError):
                b.build({"objects": [{"id": "x", "type": "nope"}]})


@unittest.skipUnless(
    os.environ.get("LUISA_LIVE") == "1",
    "live render requires LUISA_LIVE=1 and a built luisa-render-cli",
)
class TestLuisaBackendLiveRender(unittest.TestCase):
    """End-to-end smoke: real luisa-render-cli run + EXR→PNG + pixel stats."""

    def test_bar_scene_renders_nonblank(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            b = LuisaBackend(
                workdir=Path(tmp), spp=8, resolution=(128, 128), timeout=180
            )
            scene = cs.plan_scene("bar chart")
            result = b.render_preview(scene)
            self.assertTrue(result["ok"], result.get("error"))
            self.assertTrue(result["supported"])
            png = Path(result["png"])
            self.assertTrue(png.exists())
            self.assertGreater(result["png_bytes"], 5000)
            stats = result["png_stats"]
            self.assertTrue(stats["nonblank"], stats)

    def test_save_png_persists(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            b = LuisaBackend(
                workdir=Path(tmp), spp=8, resolution=(128, 128), timeout=180
            )
            dest = Path(tmp) / "out" / "saved.png"
            result = b.save_png(cs.default_scene(), path=str(dest))
            self.assertTrue(result["ok"], result.get("error"))
            self.assertTrue(dest.exists())
            self.assertGreater(dest.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
