#!/usr/bin/env python3
"""Unit tests for the Phase C simulation-frame-strip recipe (C1).

Fixture-first + repo-native: exercises deterministic generator output and the
offline recipe contract without any external simulator. Asserts the frame-strip
grammar invariants that downstream per-frame export adapters must match:
  * one `usemtl` group per frame (+ base slab);
  * every group bound by a distinct create_material + assign_material;
  * OBJ face indices stay within the vertex count;
  * the scene declares the frame count and left-to-right time layout.
"""
from __future__ import annotations

import importlib
import json
import tempfile
from pathlib import Path
from unittest import TestCase

REPO = Path(__file__).resolve().parents[1]
sys_path_mod = None
import sys as _sys  # noqa: E402

for _p in (REPO / "src", REPO / "scripts"):
    if str(_p) not in _sys.path:
        _sys.path.insert(0, str(_p))

import benchmarks.verify_recipes as vr  # noqa: E402


class TestFrameStripRecipe(TestCase):
    def test_generated_recipe_passes_contract(self):
        gen = importlib.import_module("gen_simulation_frame_strip_recipe")

        with tempfile.TemporaryDirectory() as td:
            recipe_root = Path(td) / "recipes"
            stats = gen.main(output_root=recipe_root)
            recipe = recipe_root / "simulation-frame-strip"
            self.assertTrue(recipe.exists())
            self.assertTrue((recipe / "scene.obj").exists())
            self.assertTrue((recipe / "scene.mtl").exists())
            self.assertTrue((recipe / "preview.png").exists())
            self.assertTrue((recipe / "README.md").exists())

            data = json.loads((recipe / "scene.json").read_text())
            ok, errors, warnings, obj_path = vr._check_contract(
                "simulation-frame-strip", recipe, data)

        self.assertTrue(ok, f"contract errors: {errors}")
        self.assertIsNotNone(obj_path)
        # committed recipe dir also passes (regenerated above is a temp copy)
        self.assertEqual(stats["frames"], 8)
        self.assertEqual(stats["max_face_index"], stats["vertices"])

    def test_committed_recipe_dir_passes_contract(self):
        """The checked-in recipe directory must satisfy the offline contract."""
        recipe = REPO / "examples" / "recipes" / "simulation-frame-strip"
        if not recipe.exists():
            self.skipTest("recipe not generated yet")
        data = json.loads((recipe / "scene.json").read_text())
        ok, errors, warnings, obj_path = vr._check_contract(
            "simulation-frame-strip", recipe, data)
        self.assertTrue(ok, f"contract errors: {errors}")
        self.assertIsNotNone(obj_path)

    def test_obj_indices_in_range(self):
        recipe = REPO / "examples" / "recipes" / "simulation-frame-strip"
        obj_text = (recipe / "scene.obj").read_text()
        vcount = sum(1 for ln in obj_text.splitlines() if ln.startswith("v "))
        max_idx = 0
        for ln in obj_text.splitlines():
            if ln.startswith("f "):
                for tok in ln.split()[1:]:
                    max_idx = max(max_idx, int(tok.split("/")[0]))
        self.assertGreater(vcount, 0)
        self.assertLessEqual(max_idx, vcount)

    def test_frame_grammar_invariants(self):
        recipe = REPO / "examples" / "recipes" / "simulation-frame-strip"
        data = json.loads((recipe / "scene.json").read_text())

        commands = data["commands"]
        assigns = [c for c in commands if c.get("op") == "assign_material"]
        mats = {c["payload"]["material_name"] for c in assigns}
        # 8 frame groups + base slab
        frames = {f"frame_{i:02d}" for i in range(8)}
        self.assertTrue(frames.issubset(mats), f"missing frame groups: {frames - mats}")
        self.assertIn("strip_base", mats)

        # every assigned group also has a create_material
        creates = {c["payload"]["name"] for c in commands
                   if c.get("op") == "create_material"}
        self.assertTrue(mats.issubset(creates), "an assigned material lacks create_material")

        # simulation block declares the strip grammar
        sim = data["simulation"]
        self.assertEqual(sim["scale_mapping"]["frame_count"], 8)
        self.assertEqual(sim["frame_grammar"]["orientation"],
                         "left_to_right_increasing_time")
        self.assertTrue(sim["frame_grammar"]["per_frame_group"])
        # The recipe is now native-promoted (live render passed pixel acceptance
        # and copied back a fresh octane-preview.png), so the flag is True.
        self.assertIsInstance(data["native_octane_verified"], bool)
        self.assertTrue(data["native_octane_verified"],
                        "recipe should be native-promoted after live verification")

    def test_committed_preview_is_valid_png_with_frame_colours(self):
        """The reference preview must be a *decodable* PNG carrying 8 distinct
        frame colours. This catches the corrupt-PNG class the existence-only
        contract check used to let through."""
        import struct
        import zlib

        recipe = REPO / "examples" / "recipes" / "simulation-frame-strip"
        png = (recipe / "preview.png").read_bytes()
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n", "not a PNG signature")
        w, h, bitdepth, colour_type = struct.unpack(">IIBB", png[16:26])
        self.assertEqual(colour_type, 2, "expected 8-bit RGB")
        self.assertEqual(bitdepth, 8)

        # decode IDAT and strip per-scanline filter bytes (type 0 = None)
        idat = b""
        pos = 8
        while pos < len(png):
            ln = struct.unpack(">I", png[pos:pos + 4])[0]
            tag = png[pos + 4:pos + 8]
            if tag == b"IDAT":
                idat += png[pos + 8:pos + 8 + ln]
            elif tag == b"IEND":
                break
            pos += 12 + ln
        raw = zlib.decompress(idat)
        stride = w * 3
        self.assertEqual(len(raw), h * (1 + stride), "row count/filter bytes mismatch")
        rows = [raw[y * (1 + stride) + 1:(y + 1) * (1 + stride)]
                for y in range(h)]

        # sample one central pixel per of 8 horizontal panels; expect 8 distinct colours
        panels = 8
        pw = w // panels
        seen = []
        for pi in range(panels):
            cx = pi * pw + pw // 2
            cy = h // 2
            row = rows[cy]
            seen.append(tuple(row[cx * 3:cx * 3 + 3]))
        distinct = len(set(seen))
        self.assertGreaterEqual(distinct, 6,
                                f"preview does not encode distinct frames (got {distinct}/8)")
        # monotonic-ish cool->warm ramp: red increases and blue decreases along time
        reds = [c[0] for c in seen]
        blues = [c[2] for c in seen]
        self.assertGreater(blues[0], blues[-1], "blue should decrease left->right (cool->warm)")
        self.assertLess(reds[0], reds[-1], "red should increase left->right (cool->warm)")


if __name__ == "__main__":
    import unittest
    unittest.main()
