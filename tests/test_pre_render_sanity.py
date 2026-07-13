"""Tests for pre-render sanity adoption (J).

Verifies that `analyze_scene_plan` and `analyze_scene_graph` produce
sane reports and that the report structure matches expectations for
pre-render guards.
"""

import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from octanex_mcp.sanity import (
    PLAN_CHECKS,
    GRAPH_CHECKS,
    SanityIssue,
    SanityReport,
    analyze_scene_graph,
    analyze_scene_plan,
)


class SanityReportTests(unittest.TestCase):
    """Tests for the SanityReport / SanityIssue dataclasses."""

    def test_sanity_issue_dict(self):
        """A SanityIssue serializes to a dict with all fields."""
        issue = SanityIssue(
            severity="warning",
            code="orphan_material",
            message="Material X is not connected to any mesh",
            node="mat_X",
            detail={"connections": []},
        )
        d = issue.as_dict()
        self.assertEqual(d["severity"], "warning")
        self.assertEqual(d["code"], "orphan_material")
        self.assertEqual(d["message"], "Material X is not connected to any mesh")
        self.assertEqual(d["node"], "mat_X")
        self.assertIn("detail", d)
        self.assertEqual(d["detail"]["connections"], [])

    def test_sanity_issue_minimal(self):
        """An issue without optional fields still serialises."""
        issue = SanityIssue(severity="error", code="no_camera", message="No camera")
        d = issue.as_dict()
        self.assertEqual(d["severity"], "error")
        self.assertNotIn("node", d)
        self.assertNotIn("detail", d)

    def test_sanity_report_ok_when_empty(self):
        """A report with no issues is .ok=True."""
        report = SanityReport(checks=["camera", "lights"])
        self.assertTrue(report.ok)
        self.assertEqual(len(report.errors), 0)
        self.assertEqual(len(report.warnings), 0)

    def test_sanity_report_errors_matter(self):
        """A report with one error returns .ok=False."""
        report = SanityReport(
            checks=["camera"],
            issues=[SanityIssue("error", "no_camera", "No camera")],
        )
        self.assertFalse(report.ok)
        self.assertEqual(len(report.errors), 1)
        self.assertEqual(len(report.warnings), 0)

    def test_report_as_dict_structure(self):
        """Report.as_dict() includes all required keys."""
        report = SanityReport(
            checks=["camera", "lights", "framing"],
        )
        d = report.as_dict()
        self.assertIn("ok", d)
        self.assertIn("passed_checks", d)
        self.assertIn("error_count", d)
        self.assertIn("warning_count", d)
        self.assertIn("issues", d)
        self.assertIn("summary", d)
        self.assertEqual(d["passed_checks"], ["camera", "lights", "framing"])

    def test_report_summary(self):
        """Report.summary() counts issues by code and mirrors ok/error count."""
        report = SanityReport(
            issues=[
                SanityIssue("error", "no_camera", "no cam"),
                SanityIssue("warning", "orphan_material", "orphaned A"),
                SanityIssue("warning", "orphan_material", "orphaned B"),
            ],
        )
        s = report.summary()
        # 1 error means ok=False
        self.assertFalse(s["ok"])
        self.assertEqual(s["errors"], 1)
        self.assertEqual(s["warnings"], 2)
        self.assertEqual(s["by_code"]["orphan_material"], 2)


class SanityEngineTests(unittest.TestCase):
    """Tests for the helper functions in sanityEngine."""

    def test_norm(self):
        """_norm normalizes values deterministically."""
        from octanex_mcp.sanity import _norm
        self.assertEqual(_norm("MY_TYPE"), "my type")
        self.assertEqual(_norm("render_target"), "render target")
        self.assertEqual(_norm(""), "")

    def test_is_render_target(self):
        """_is_render_target identifies render targets."""
        from octanex_mcp.sanity import _is_render_target
        self.assertTrue(_is_render_target("render target"))
        self.assertTrue(_is_render_target("rendertarget"))
        self.assertTrue(_is_render_target("render_target"))
        self.assertFalse(_is_render_target("light"))

    def test_is_light(self):
        """_is_light catches common light type names."""
        from octanex_mcp.sanity import _is_light
        self.assertTrue(_is_light("light"))
        self.assertTrue(_is_light("daylight"))
        self.assertTrue(_is_light("sun"))
        self.assertTrue(_is_light("spot"))
        self.assertTrue(_is_light("point light"))
        self.assertFalse(_is_light("camera"))

    def test_is_material(self):
        """_is_material identifies materials."""
        from octanex_mcp.sanity import _is_material
        self.assertTrue(_is_material("material"))
        self.assertTrue(_is_material("pbr_material"))
        self.assertFalse(_is_material("mesh"))


class LiveGraphAnalysisTests(unittest.TestCase):
    """Tests for analyze_scene_graph against live harvest data."""

    def test_graph_ok_for_sane_harvest(self):
        """A harvest with all required nodes returns ok=True."""
        harvest = {
            "nodes": [
                {"type": "render target", "name": "rt1"},
                {"type": "camera", "name": "cam1", "connected": ["rt1"]},
                {"type": "light", "name": "lb1"},
                {"type": "mesh", "name": "mesh1", "has_geometry": True, "has_material": True},
            ]
        }
        report = analyze_scene_graph(harvest)
        self.assertTrue(report.ok)

    def test_graph_no_render_target(self):
        """If there is no render target, it reports an error."""
        harvest = {"nodes": [{"type": "camera", "name": "cam1", "connected": []}]}
        report = analyze_scene_graph(harvest)
        errors = report.errors
        self.assertTrue(len(errors) >= 1)
        codes = {e.code for e in errors}
        self.assertIn("no_render_target", codes)

    def test_graph_malformed_harvest(self):
        """If 'nodes' is not a list, harvest_malformed is recorded."""
        report = analyze_scene_graph({"nodes": "not a list"})
        self.assertFalse(report.ok)
        codes = {e.code for e in report.issues}
        self.assertIn("harvest_malformed", codes)

    def test_graph_camera_not_wired(self):
        """Camera not connected to render target is a warning (non-strict)."""
        harvest = {
            "nodes": [
                {"type": "render target", "name": "rt1"},
                {"type": "camera", "name": "cam1", "connected": ["other"]},
            ]
        }
        report = analyze_scene_graph(harvest)
        codes = {e.code for e in report.issues}
        self.assertIn("camera_not_connected_to_rt", codes)


class ManifestAnalysisTests(unittest.TestCase):
    """Tests for analyze_scene_plan against manifest data."""

    def test_plan_ok_for_sane_plan(self):
        """A plan with camera + objects + lighting is ok."""
        plan = {
            "objects": [{"id": "obj1", "type": "sphere", "path": "/path/to.obj", "material": "mat1", "bounds": {"center": [0, 0, 0], "radius": 1.0}}],
            "materials": [{"name": "mat1"}],
            "camera": {"position": [0, 2, 4], "target": [0, 0, 0], "fov": 45},
            "lighting": {"type": "area_light"},
            "render": {"samples": 100},
        }
        report = analyze_scene_plan(plan)
        self.assertTrue(report.ok)

    def test_plan_missing_camera(self):
        """A plan with no camera reports an error."""
        plan = {
            "objects": [{"id": "obj1", "type": "sphere", "bounds": {"center": [0, 0, 0], "radius": 1.0}}],
            "camera": None,
            "lighting": {"type": "area_light"},
        }
        report = analyze_scene_plan(plan)
        self.assertFalse(report.ok)
        codes = {e.code for e in report.errors}
        self.assertIn("no_camera", codes)

    def test_plan_malformed(self):
        """A non-mapping plan carries plan_malformed."""
        # A list is not a Mapping for our purposes
        report1 = analyze_scene_plan([  # type: ignore
            "not", "a", "mapping",
        ])
        self.assertFalse(report1.ok)
        codes = {e.code for e in report1.issues}
        self.assertIn("plan_malformed", codes)

        # A complete mapping passes without errors
        report2 = analyze_scene_plan({
            "objects": [{"id": "obj1", "type": "sphere", "bounds": {"center": [0, 0, 0], "radius": 1.0}}],
            "camera": {"position": [0, 2, 4], "target": [0, 0, 0], "fov": 45},
            "lighting": {"type": "area_light"},
        })
        self.assertTrue(report2.ok)

    def test_plan_missing_render(self):
        """A plan without render block, objects, or camera is no_render_target."""
        plan = {"objects": [], "camera": None, "render": None}
        report = analyze_scene_plan(plan)
        codes = {e.code for e in report.issues}
        self.assertIn("no_render_target", codes)

    def test_plan_uses_plan_checks_by_default(self):
        """Default checks include framing."""
        plan = {"camera": {"position": [0, 5, 10], "target": [0, 0, 0], "fov": 45}}
        report = analyze_scene_plan(plan)
        self.assertIn("framing", report.checks)
        self.assertIn("render_target", report.checks)
        self.assertIn("materials", report.checks)

    def test_plan_material_unused_warning(self):
        """A defined material not referenced by objects emits a warning."""
        plan = {
            "objects": [{"id": "obj1", "type": "sphere", "material": "other_mat", "bounds": {"center": [0, 0, 0], "radius": 1.0}}],
            "materials": [{"name": "mat1"}],
            "camera": {"position": [0, 2, 4], "target": [0, 0, 0], "fov": 45},
            "lighting": {"type": "area_light"},
        }
        report = analyze_scene_plan(plan)
        self.assertTrue(report.ok)
        # Two warnings: material_unused + no_light_environment (if lighting empty)
        self.assertGreaterEqual(len(report.warnings), 1)
        self.assertIn("material_unused", {w.code for w in report.warnings})

    def test_graph_checks_tuple(self):
        """GRAPH_CHECKS and PLAN_CHECKS contain expected entries."""
        self.assertIn("camera", GRAPH_CHECKS)
        self.assertIn("render_target", GRAPH_CHECKS)
        self.assertIn("framing", PLAN_CHECKS)
        self.assertIn("materials", PLAN_CHECKS)


class SanityReportIntegrationTests(unittest.TestCase):
    """Integration-style tests verifying report → dict → JSON round-trip."""

    def test_full_report_roundtrip(self):
        """Report.as_dict → json → parsed matches original structure."""
        report = SanityReport(
            checks=["camera", "framing"],
            issues=[
                SanityIssue("error", "no_camera", "No camera node", node="cam1", detail={"connected": 0}),
                SanityIssue("warning", "camera_not_connected_to_rt", "Camera unconnected", node="cam1"),
            ],
        )
        payload = json.dumps(report.as_dict())
        parsed = json.loads(payload)
        # ok should reflect presence of errors (1 error here)
        self.assertFalse(parsed["ok"])
        self.assertEqual(len(parsed["issues"]), 2)
        self.assertEqual(parsed["issues"][0]["code"], "no_camera")
        self.assertEqual(parsed["error_count"], 1)
        self.assertEqual(parsed["warning_count"], 1)

    def test_report_with_many_issues_sorted(self):
        """Issues are sorted severity-first in as_dict."""
        report = SanityReport(
            issues=[
                SanityIssue("warning", "z_code", "warning"),
                SanityIssue("error", "a_code", "error1"),
                SanityIssue("error", "b_code", "error2"),
            ],
        )
        d = report.as_dict()
        codes = [iss["code"] for iss in d["issues"]]
        self.assertTrue(codes.index("a_code") < codes.index("z_code"))

    def test_check_sets_are_non_empty(self):
        """Both GRAPH_CHECKS and PLAN_CHECKS have entries."""
        self.assertGreater(len(GRAPH_CHECKS), 0)
        self.assertGreater(len(PLAN_CHECKS), 0)


if __name__ == "__main__":
    unittest.main()
