from __future__ import annotations

import struct
import tempfile
import time
import unittest
import zlib
from pathlib import Path

from octanex_mcp.bridge import Workspace, octane_render_review_loop


class RenderReviewLoopTests(unittest.TestCase):
    """Tests for octane_render_review_loop() orchestration tool."""

    def test_render_review_loop_instantly_ends_when_preview_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp) / "workspace")
            ws.ensure()
            # Create a normal preview PNG (not black, not white)
            import struct
            import zlib
            rows = [[(128, 128, 128)] * 16 for _ in range(16)]
            width, height = 16, 16
            raw = b"".join(b"\x00" + b"".join(bytes(p) for p in row) for row in rows)
            png_bytes = (b"\x89PNG\r\n\x1a\n"
                        + struct.pack(">I", 13) + b"IHDR" + struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
                        + struct.pack(">I", len(raw)) + zlib.compress(raw)
                        + struct.pack(">I", 0))
            preview = ws.renders_dir / "preview.png"
            preview.write_bytes(png_bytes)
            result = octane_render_review_loop(
                scene_id="loop_test",
                workspace=ws,
                max_iterations=3,
            )
            self.assertTrue(result["completed"])
            self.assertGreaterEqual(result["iterations"], 1)
            self.assertIn("final_review", result)
            self.assertIn("checkpoint", result)

    def test_render_review_loop_tracks_multiple_iterations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp) / "workspace")
            with tempfile.TemporaryDirectory() as tmp2:
                # Create a dark preview so loop continues
                rows = [[(0, 0, 0)] * 4 for _ in range(4)]
                width, height = 4, 4
                raw = b"".join(b"\x00" + b"".join(bytes(p) for p in row) for row in rows)
                png_bytes = (b"\x89PNG\r\n\x1a\n"
                            + struct.pack(">I", 13) + b"IHDR" + struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
                            + struct.pack(">I", len(raw)) + zlib.compress(raw)
                            + struct.pack(">I", 0))
                preview = Path(tmp2) / "preview.png"
                preview.write_bytes(png_bytes)

                result = octane_render_review_loop(
                    scene_id="loop_test",
                    workspace=ws,
                    preview_path=str(preview),
                    max_iterations=3,
                    iteration_delay=0.1,  # Fast iteration
                )
            self.assertTrue(result["completed"])
            self.assertGreaterEqual(result["iterations"], 1)
            self.assertIn("all_checks", result)
            self.assertTrue(isinstance(result["all_checks"], list))

    def test_render_review_loop_stops_at_max_iterations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Workspace(Path(tmp) / "workspace")
            ws.ensure()
            # Create a dark preview so loop continues
            import struct
            import zlib
            rows = [[(0, 0, 0)] * 4 for _ in range(4)]
            width, height = 4, 4
            raw = b"".join(b"\x00" + b"".join(bytes(p) for p in row) for row in rows)
            png_bytes = (b"\x89PNG\r\n\x1a\n"
                        + struct.pack(">I", 13) + b"IHDR" + struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
                        + struct.pack(">I", len(raw)) + zlib.compress(raw)
                        + struct.pack(">I", 0))
            preview = ws.renders_dir / "preview.png"
            preview.write_bytes(png_bytes)

            result = octane_render_review_loop(
                scene_id="loop_test",
                workspace=ws,
                preview_path=str(preview),
                max_iterations=5,
            )
            self.assertTrue(result["completed"])
            self.assertEqual(result["iterations"], 5)


if __name__ == "__main__":
    unittest.main()
