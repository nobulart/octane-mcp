"""WP10 lexical-intent-graph tests — offline, no Octane, no network.

Mirrors the iteration.py test pattern: a render_fn is injected so the
scene_spec produced by lexicon.resolve() can be validated without draining
the bridge. We assert the two failures the lexicon retires:

  * A color word resolves to the correct material color (no photo-hue drift).
  * Materials are emitted with 1-based assignments (no silent white subject).
  * Composition connectors produce multiple groups.
  * Motion verbs surface as motion specs (WP8 hook).
  * Unknown nouns raise LexiconError (never a default-white fallback).
"""

from __future__ import annotations

import math
import unittest

from octanex_mcp import lexicon
from octanex_mcp.acceptance import evaluate_acceptance

# A tiny inline PNG writer (offline, no PIL, no Octane). Produces a two-tone
# image: a dark background with a bright "subject" blob in the center, which is
# the minimal shape that passes evaluate_acceptance's non_empty gate (a flat
# fill reads as empty, like a real blank render would).
import struct
import zlib


def _blob_png(path, subject_rgb: tuple[int, int, int], bg_rgb: tuple[int, int, int] = (20, 20, 22),
              size: int = 16) -> None:
    w = h = size
    raw = bytearray()
    for y in range(h):
        raw.append(0)  # filter type 0
        for x in range(w):
            in_blob = (size * 0.35 <= x < size * 0.65) and (size * 0.35 <= y < size * 0.65)
            raw.extend(subject_rgb if in_blob else bg_rgb)
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(
            ">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    idat = zlib.compress(bytes(raw))
    path.write_bytes(sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b""))


class _RenderRecorder:
    """Fake render_fn: writes a two-tone PNG (dark bg + primary material blob)."""

    def __init__(self):
        self.calls = 0
        self.last_spec = None

    def __call__(self, spec: dict) -> "str":
        from pathlib import Path
        self.calls += 1
        self.last_spec = spec
        p = Path(spec.get("__out", "/tmp/lexicon_test_render.png"))
        mat = spec["materials"][0]
        c = mat["color"]
        _blob_png(p, (int(c[0] * 255), int(c[1] * 255), int(c[2] * 255)))
        return str(p)


class LexiconResolveTests(unittest.TestCase):

    def test_red_vase_resolves_red_not_blue(self):
        # Retires B: photo-hue drift (red-sphere corpus entry resolved blue).
        spec = lexicon.resolve("a red vase")
        mat = spec["materials"][0]
        self.assertEqual(mat["name"], "mat_vase_1")
        # Red's hue ~0deg -> dominant channel is R, G/B both low.
        self.assertGreater(mat["color"][0], 0.5)
        self.assertLess(mat["color"][1], 0.3)
        self.assertLess(mat["color"][2], 0.4)
        # VA self-check: a solid red render must pass the red color_family gate.
        rec = _RenderRecorder()
        out = rec(spec)
        report = evaluate_acceptance(out, spec["acceptance"])
        self.assertTrue(report["passed"], f"red scene failed its own acceptance: {report}")

    def test_gold_material_word_binds_metallic(self):
        spec = lexicon.resolve("a gold sphere")
        mat = spec["materials"][0]
        # Material word overrides the noun default; kind normalizes to metallic.
        self.assertEqual(mat["kind"], "metallic")
        self.assertAlmostEqual(mat["metallic"], 1.0, places=2)
        self.assertGreater(mat["color"][0], mat["color"][2])  # gold is warm

    def test_assignments_are_1based_per_group(self):
        # Retires A: material-binding trap (bridge ignores usemtl).
        spec = lexicon.resolve("a blue cube")
        self.assertEqual(len(spec["materials"]), 1)
        self.assertEqual(len(spec["assignments"]), 1)
        self.assertEqual(spec["assignments"][0]["group_index"], 1)
        self.assertEqual(spec["assignments"][0]["material_name"], spec["materials"][0]["name"])

    def test_composition_connector_makes_multiple_groups(self):
        # C: multi-object scene graph.
        spec = lexicon.resolve("a red cube on a blue pedestal")
        self.assertEqual(len(spec["materials"]), 2)
        self.assertEqual(len(spec["assignments"]), 2)
        # "on" -> the first phrase is lifted onto the second phrase. The
        # combined mesh carries two groups (one 'g' per assignable group), so
        # the OBJ has 2 group markers.
        self.assertEqual(spec["obj"].count("\ng "), 2)
        # Assignment group indices are 1 and 2.
        idxs = [a["group_index"] for a in spec["assignments"]]
        self.assertEqual(idxs, [1, 2])
        self.assertAlmostEqual(spec["phrases"][0]["center"][1], 1.05, places=2)
        self.assertAlmostEqual(spec["phrases"][1]["center"][1], 0.0, places=2)
        self.assertAlmostEqual(spec["bounds"]["min"][1], -0.25, places=2)
        self.assertAlmostEqual(spec["bounds"]["max"][1], 1.85, places=2)

    def test_with_connector_side_by_side(self):
        spec = lexicon.resolve("a green sphere with a small red cube")
        self.assertEqual(len(spec["materials"]), 2)
        names = [m["name"] for m in spec["materials"]]
        self.assertIn("mat_sphere_1", names)
        self.assertIn("mat_cube_2", names)
        # 'small' adjective applied -> cube half-extent scaled down.
        # (cube default half = 0.8; small scale 0.6 -> 0.48)
        # We don't expose half directly; assert the unresolved list is empty.
        self.assertEqual(spec["unresolved"], [])

    def test_motion_verb_surfaces_wp8_spec(self):
        # D: animation / camera-movement vocabulary.
        spec = lexicon.resolve("a red sphere spinning")
        self.assertTrue(any(m["type"] == "object_rotate" for m in spec["motion"]))
        rot = next(m for m in spec["motion"] if m["type"] == "object_rotate")
        self.assertEqual(rot["motion"], "rotate")
        self.assertEqual(rot["axis"], "y")
        self.assertEqual(rot["refs"], "#1")

    def test_camera_orbit_verb(self):
        spec = lexicon.resolve("a planet orbiting")
        orbit = next((m for m in spec["motion"] if m["type"] == "camera_orbit"), None)
        self.assertIsNotNone(orbit)
        self.assertEqual(orbit["type"], "camera_orbit")

    def test_unknown_noun_raises_no_silent_white(self):
        with self.assertRaises(lexicon.LexiconError):
            lexicon.resolve("a florbnarg")

    def test_strict_mode_flags_unresolved_word(self):
        # "banana" is not in the lexicon -> strict mode must reject it.
        with self.assertRaises(lexicon.LexiconError):
            lexicon.resolve("a banana cube", strict=True)

    def test_non_strict_tolerates_unresolved(self):
        spec = lexicon.resolve("a blue cube zebra")
        # "zebra" is unresolved but tolerated in non-strict mode; the cube still
        # resolves with a blue material.
        self.assertEqual(spec["materials"][0]["kind"], "glossy")
        self.assertIn("zebra", spec["unresolved"])

    def test_kind_normalization_bridges_four_kinds(self):
        for word, expected in (("glass", "specular"), ("steel", "metallic"),
                                ("ceramic", "glossy"), ("stone", "diffuse")):
            spec = lexicon.resolve(f"a {word} cube")
            self.assertEqual(spec["materials"][0]["kind"], expected,
                             f"word={word} -> {spec['materials'][0]['kind']}")

    def test_large_adjective_scales_geometry(self):
        small = lexicon.resolve("a small red cube")
        big = lexicon.resolve("a huge red cube")
        # inner groups differ only by scale; assert both build without error and
        # produce distinct bounds radii.
        self.assertGreater(big["bounds"]["radius"], small["bounds"]["radius"])

    def test_warm_start_accepted_for_api_symmetry(self):
        ws = {"slug": "blue-ceramic-vase", "source_url": "x"}
        spec = lexicon.resolve("a blue vase", warm_start=ws)
        self.assertEqual(spec["warm_start"], ws)


if __name__ == "__main__":
    unittest.main()
