"""Benchmark suite tests.

Two layers:

  * Offline (always run): exercise the deterministic spec builders, the
    pixel-based acceptance logic on synthetic PNGs, and the harness's
    OBJ-index validation + queue-side effects (mirror + write_command) using
    an isolated fake container workspace.

  * Live (skipped unless OCTANEX_LIVE=1 and a container exists): end-to-end
    render + verify against the real Octane sandbox. These are the gate that
    promotes a benchmark into the native-Octane recipe book.

Run offline:
    uv run python -m unittest tests.test_benchmarks -v
Run live (Tier 1-2 only, bounded):
    OCTANEX_LIVE=1 uv run python -m unittest tests.test_benchmarks -v
"""

from __future__ import annotations

import json
import os
import struct
import unittest
import zlib
from pathlib import Path

import benchmarks.acceptance as acceptance
from benchmarks.spec import (
    ALL_TASKS,
    BenchmarkTask,
    CombinedObj,
    get_task,
    tasks_by_tier,
)
from benchmarks import harness
from octanex_mcp.visuals import ObjBuilder


# ---------------------------------------------------------------------------
# Helpers: minimal PNG writer (no PIL) so acceptance tests are dependency-free
# ---------------------------------------------------------------------------


def _write_png(path: Path, width: int, height: int, pixels: list[tuple[int, int, int]]) -> None:
    """Encode an RGB8 PNG from a flat pixel list using only zlib/struct."""
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter type 0
        for x in range(width):
            r, g, b = pixels[y * width + x]
            raw += bytes((r, g, b))
    compressed = zlib.compress(bytes(raw), 9)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    path.write_bytes(sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", compressed) + chunk(b"IEND", b""))


def _solid(width: int, height: int, color: tuple[int, int, int]) -> list[tuple[int, int, int]]:
    return [color] * (width * height)


def _blue_cube_ish(width: int, height: int) -> list[tuple[int, int, int]]:
    """A centered blue-ish square on a darker background — simulates a cube
    render so color_present / non_empty / shape_profile can be exercised."""
    px = []
    cx, cy = width // 2, height // 2
    for y in range(height):
        for x in range(width):
            d = max(abs(x - cx), abs(y - cy))
            if d < min(width, height) // 4:
                px.append((30, 115, 242))  # ~ (0.12,0.45,0.95)*255
            else:
                px.append((8, 8, 12))
    return px


# ---------------------------------------------------------------------------
# 1. Spec coverage / determinism
# ---------------------------------------------------------------------------


class SpecCoverageTests(unittest.TestCase):
    def test_all_tasks_have_unique_slugs(self):
        slugs = [t.slug for t in ALL_TASKS]
        self.assertEqual(len(slugs), len(set(slugs)), "duplicate task slugs")
        # 18 = 12 tiers 1-6 + 3 tier-7 physics + 2 tier-8 MHD diagnostics
        #      + 1 tier-9 simulation frame-strip grammar.
        # Bump this when adding/removing benchmark tasks, and keep spec.py ALL_TASKS in sync.
        self.assertEqual(len(slugs), 18)

    def test_task_build_is_deterministic_and_complete(self):
        for slug in (t.slug for t in ALL_TASKS):
            with self.subTest(slug=slug):
                task = get_task(slug)
                self.assertIsNotNone(task)
                spec1 = task.build_scene()
                spec2 = task.build_scene()
                self.assertEqual(spec1, spec2, "build() is not deterministic")

                for key in ("mesh_name", "obj", "bounds", "materials", "assignments",
                            "camera", "lighting", "save", "acceptance"):
                    self.assertIn(key, spec1, f"missing key {key} in {slug}")
                self.assertTrue(spec1["materials"], "no materials")
                self.assertTrue(spec1["assignments"], "no assignments")
                mat_names = {m["name"] for m in spec1["materials"]}
                for a in spec1["assignments"]:
                    self.assertIn(a["material_name"], mat_names, f"assignment to unknown material in {slug}")

    def test_task_obj_indices_in_range(self):
        for slug in (t.slug for t in ALL_TASKS):
            with self.subTest(slug=slug):
                task = get_task(slug)
                self.assertIsNotNone(task)
                spec = task.build_scene()
                obj_path = self._tmp / f"{slug}.obj"
                obj_path.write_text(spec["obj"], encoding="utf-8")
                harness._validate_obj_indices(obj_path)  # must not raise

    def setUp(self):
        self._tmp = Path(self._testMethodName + "_tmp")
        self._tmp.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        import shutil
        if self._tmp.exists():
            shutil.rmtree(self._tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# 2. Combined OBJ builder: the #1 empty-render cause
# ---------------------------------------------------------------------------


class CombinedObjTests(unittest.TestCase):
    def test_combined_obj_offsets_face_indices(self):
        a = ObjBuilder("a")
        a.add_box(center=(0, 0, 0), size=(1, 1, 1), material="ma")
        b = ObjBuilder("b")
        b.add_box(center=(3, 0, 0), size=(1, 1, 1), material="mb")
        obj = CombinedObj("ab")
        obj.add_group("a", "ma", a)
        obj.add_group("b", "mb", b)
        text = obj.text()
        lines = text.splitlines()
        vcount = sum(1 for l in lines if l.startswith("v "))
        max_idx = 0
        for l in lines:
            if l.startswith("f "):
                for tok in l.split()[1:]:
                    max_idx = max(max_idx, int(tok.split("/")[0]))
        self.assertLessEqual(max_idx, vcount, "face index exceeds vertex count (empty-render bug)")
        self.assertEqual(vcount, a.vertex_count + b.vertex_count)
        self.assertIn("usemtl ma", text)
        self.assertIn("usemtl mb", text)


# ---------------------------------------------------------------------------
# 3. Acceptance checks on synthetic PNGs
# ---------------------------------------------------------------------------


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_non_empty_passes_for_structure(self):
        p = self.tmp / "blue.png"
        _write_png(p, 64, 64, _blue_cube_ish(64, 64))
        rep = acceptance.evaluate_acceptance(p, [{"kind": "non_empty", "min_mean_dev": 1.0, "min_nonbg": 1.0}])
        self.assertTrue(rep["passed"])

    def test_non_empty_fails_for_black(self):
        p = self.tmp / "black.png"
        _write_png(p, 64, 64, _solid(64, 64, (0, 0, 0)))
        rep = acceptance.evaluate_acceptance(p, [{"kind": "non_empty", "min_mean_dev": 1.0, "min_nonbg": 1.0}])
        self.assertFalse(rep["passed"])

    def test_color_present(self):
        p = self.tmp / "blue.png"
        _write_png(p, 64, 64, _blue_cube_ish(64, 64))
        rep = acceptance.evaluate_acceptance(p, [
            {"kind": "color_present", "target": [0.12, 0.45, 0.95], "tol": 0.2, "min_fraction": 0.02},
        ])
        self.assertTrue(rep["passed"])

    def test_color_present_fails_wrong_color(self):
        p = self.tmp / "red.png"
        _write_png(p, 64, 64, _solid(64, 64, (255, 0, 0)))
        rep = acceptance.evaluate_acceptance(p, [
            {"kind": "color_present", "target": [0.12, 0.45, 0.95], "tol": 0.2, "min_fraction": 0.02},
        ])
        self.assertFalse(rep["passed"])

    def test_color_family(self):
        p = self.tmp / "blue.png"
        _write_png(p, 64, 64, _blue_cube_ish(64, 64))
        rep = acceptance.evaluate_acceptance(p, [
            {"kind": "color_family", "target": [0.12, 0.45, 0.95], "hue_tol": 40, "min_fraction": 0.02},
        ])
        self.assertTrue(rep["passed"])

    def test_shape_profile(self):
        p = self.tmp / "blue.png"
        _write_png(p, 64, 64, _blue_cube_ish(64, 64))
        rep = acceptance.evaluate_acceptance(p, [{"kind": "shape_profile", "min_rows": 6}])
        self.assertTrue(rep["passed"])

    def test_missing_png(self):
        rep = acceptance.evaluate_acceptance(self.tmp / "nope.png", [{"kind": "non_empty", "min_mean_dev": 1.0}])
        self.assertFalse(rep["passed"])
        self.assertTrue(rep["checks"][0]["error"])


# ---------------------------------------------------------------------------
# 4. Harness mirror + queue against a fake container
# ---------------------------------------------------------------------------


class _FakeWorkspace:
    """Minimal stand-in for octanex_mcp.bridge.Workspace for offline tests."""

    def __init__(self, root: Path):
        self.root = root
        self.assets_dir = root / "assets"
        self.queue_dir = root / "queue"
        self.processing_dir = root / "processing"
        self.renders_dir = root / "renders"
        self.state_dir = root / "state"
        self.status_path = root / "state" / "bridge_status.json"
        for d in (self.assets_dir, self.queue_dir, self.processing_dir, self.renders_dir, self.state_dir):
            d.mkdir(parents=True, exist_ok=True)

    def ensure(self):
        pass


class HarnessTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = Path(tempfile.mkdtemp())
        self.fake = _FakeWorkspace(self.tmp)

        # patch harness module references used inside run_task
        self._patches = []
        self._orig_ws = harness.Workspace
        self._orig_cfg = harness.resolve_config
        harness.Workspace = lambda *a, **k: self.fake

        class _Cfg:
            workspace = self.tmp
        harness.resolve_config = lambda: _Cfg()

    def tearDown(self):
        import shutil
        harness.Workspace = self._orig_ws
        harness.resolve_config = self._orig_cfg
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_harness_mirrors_obj_and_queues_commands(self):
        task = get_task("t1_glossy_cube")
        self.assertIsNotNone(task)
        run = harness.run_task(task, container=self.tmp, dry_run=True)
        self.assertTrue(run.obj_path and run.obj_path.exists(), "OBJ not mirrored")
        self.assertGreaterEqual(run.queued, 6, f"expected >=6 commands, got {run.queued}")
        queued = sorted(self.fake.queue_dir.glob("*.json"))
        self.assertTrue(queued, "no commands queued")
        last = json.loads(queued[-1].read_text())
        self.assertEqual(last["op"], "save_preview")

    def test_live_run_flushes_stale_queue_before_writing_task_commands(self):
        stale = self.fake.queue_dir / "000000_stale.json"
        stale.write_text(json.dumps({"op": "stale", "payload": {}}), encoding="utf-8")

        orig_drain = harness.drain_oneshot
        harness.drain_oneshot = lambda *a, **k: {"ok": True, "queue_remaining": 0}
        try:
            task = get_task("t1_glossy_cube")
            self.assertIsNotNone(task)
            assert task is not None
            run = harness.run_task(task, container=self.tmp, dry_run=False, drain=True)
        finally:
            harness.drain_oneshot = orig_drain

        self.assertFalse(stale.exists(), "stale queue file should be flushed before queueing")
        queued = sorted(self.fake.queue_dir.glob("*.json"))
        self.assertGreaterEqual(len(queued), run.queued, "freshly queued commands were flushed away")
        ops = [json.loads(p.read_text())["op"] for p in queued]
        self.assertIn("import_geometry", ops)
        self.assertEqual(ops[-1], "save_preview")

    def test_harness_obj_index_guard_raises(self):
        obj = CombinedObj("bad")
        b = ObjBuilder("bad")
        b.add_box(center=(0, 0, 0), size=(1, 1, 1), material="m")
        obj.add_group("bad", "m", b)
        lines = obj.text().splitlines()
        corrupted = []
        for l in lines:
            if l.startswith("f "):
                parts = l.split()
                parts[1] = str(9999)
                l = " ".join(parts)
            corrupted.append(l)
        bad_path = self.tmp / "bad.obj"
        bad_path.write_text("\n".join(corrupted))
        with self.assertRaises(ValueError):
            harness._validate_obj_indices(bad_path)


# ---------------------------------------------------------------------------
# 5. Live integration (gated)
# ---------------------------------------------------------------------------


LIVE = os.environ.get("OCTANEX_LIVE") == "1"
CONTAINER = harness.DEFAULT_CONTAINER


@unittest.skipUnless(LIVE, "set OCTANEX_LIVE=1 to run live renders")
@unittest.skipUnless(CONTAINER.exists(), "octane container workspace not found")
class LiveTaskRenderTests(unittest.TestCase):
    def test_live_tier1_tier2(self):
        for slug in (t.slug for t in tasks_by_tier(1) + tasks_by_tier(2)):
            with self.subTest(slug=slug):
                task = get_task(slug)
                self.assertIsNotNone(task)
                run = harness.run_task(task, container=CONTAINER, dry_run=False, drain=True, drain_timeout=120)
                self.assertIsNone(run.error, run.error)
                self.assertIsNotNone(run.acceptance, "no acceptance report")
                if not run.acceptance["passed"]:
                    summary = acceptance.summarize(run.acceptance)
                    self.fail(f"{slug} render failed acceptance:\n{summary}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
