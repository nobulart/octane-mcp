#!/usr/bin/env python3
"""Schema tests for optional real-library physics smoke runner."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))


class TestPhysicsRealLibrarySmokes(TestCase):
    def test_run_all_report_schema(self):
        smokes = importlib.import_module("run_physics_real_library_smokes")

        def fake(name: str, status: str):
            return {
                "name": name,
                "source_path": f"/tmp/{name}",
                "source_exists": True,
                "status": status,
                "detail": f"{name} {status}",
                "evidence": {"exit_code": 0 if status == "passed" else 1},
            }

        with patch.object(smokes, "smoke_oceananigans", return_value=fake("Oceananigans.jl", "passed")), \
             patch.object(smokes, "smoke_splishsplash", return_value=fake("SPlisHSPlasH", "blocked")), \
             patch.object(smokes, "smoke_genesis", return_value=fake("Genesis", "blocked")), \
             patch.object(smokes, "smoke_mpipymhd", return_value=fake("MPIPyMHD", "skipped")):
            report = smokes.run_all(timeout=7)

        self.assertEqual(report["schema"], "octanex-physics-real-library-smokes/v1")
        self.assertEqual(report["timeout_seconds"], 7)
        self.assertEqual(report["summary"], {"passed": 1, "blocked": 2, "skipped": 1})
        self.assertEqual([c["name"] for c in report["checks"]], [
            "Oceananigans.jl",
            "SPlisHSPlasH",
            "Genesis",
            "MPIPyMHD",
        ])
        for check in report["checks"]:
            self.assertIn(check["status"], {"passed", "blocked", "skipped"})
            self.assertIn("detail", check)
            self.assertIn("evidence", check)
