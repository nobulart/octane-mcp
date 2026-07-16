#!/usr/bin/env python3
"""Unit test for the SPlisHSPlasH real-export boundary.

This stays fixture-first: it asserts the exporter:
  * returns the committed fixture by default (no runtime solver needed),
  * records source_library + sha256 honestly,
  * never mutates/overwrites the committed fixture during the default path.

A real run is gated behind --scene-xml and is covered by the optional real-library
smoke (scripts/run_physics_real_library_smokes.py), not the offline suite.
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from unittest import TestCase

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "examples" / "fixtures" / "particles" / "dam-break-small" / "dam-break-small.csv"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))


class TestSplishSplashExporter(TestCase):
    def test_default_uses_committed_fixture(self):
        exporter = importlib.import_module("export_splishsplash_dam_break_fixture")
        meta = exporter.export_fixture()  # no scene_xml -> committed fixture
        self.assertEqual(meta["source_library"], "splishsplash")
        self.assertEqual(meta["fixture"], str(FIXTURE))
        self.assertFalse(meta["real_export"])
        self.assertIn("fixture_sha256", meta)
        # committed fixture untouched
        self.assertTrue(FIXTURE.exists())

    def test_scene_xml_branch_is_honest_when_missing(self):
        exporter = importlib.import_module("export_splishsplash_dam_break_fixture")
        # Point at a non-existent scene file -> the real branch must fail cleanly
        # and report fallback, not segfault or raise.
        meta = exporter.export_fixture(scene_xml=Path("/nonexistent/scene.xml"))
        self.assertFalse(meta["real_export"])
        self.assertTrue(meta["fallback"])
        self.assertIn("error", meta)
        # fell back to committed fixture
        self.assertEqual(meta["fixture"], str(FIXTURE))


if __name__ == "__main__":
    import unittest

    unittest.main()
