"""Offline tests for WP9 iteration loop (render_fn injected; no Octane session).

Verifies:
  * build_candidate_scene derives an Octane spec from a corpus entry grammar.
  * iterate_entry converges when the injected render reproduces the reference
    grammar (first attempt) and stops, writing nothing if it never converges
    but tagging geometry failures as needs_human.
  * promote_entry persists preview + promotion.json + snippet and flips status.
"""

import tempfile
import unittest
from pathlib import Path

import octanex_mcp.iteration as it
from octanex_mcp.corpus import register_reference, load_entry
import tests.test_corpus as tc


def _seed_entry(corpus_root: Path, slug: str):
    """Register a synthetic CC reference so the loop has a real entry to drive."""
    import tempfile as _tf
    tmp = Path(_tf.mkdtemp()) / f"{slug}.png"
    tc.write_rgb_png(tmp, tc._red_on_dark())
    data = tmp.read_bytes()
    res = register_reference(
        slug=slug, title=slug.title(), source_url=f"mock://{slug}",
        license="CC-BY-mock", reference_png=data, domain="photoreal",
        corpus_root=corpus_root,
    )
    assert res["ok"], res.get("reasons")
    return load_entry(slug, corpus_root=corpus_root)


class BuildTests(unittest.TestCase):
    def test_build_candidate_scene_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            cr = Path(tmp) / "corpus"
            entry = _seed_entry(cr, "red-sphere")
            spec = it.build_candidate_scene(entry)
            self.assertEqual(spec["mesh_name"], "wp9_red-sphere")
            self.assertIn("subject_mat", spec["obj"])
            self.assertEqual(len(spec["materials"]), 1)
            self.assertGreaterEqual(len(spec["acceptance"]), 2)
            # acceptance is the entry's own derived spec (not a benchmark's)
            self.assertEqual(spec["acceptance"], entry.derived_acceptance)


class IterateTests(unittest.TestCase):
    def test_converges_first_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            cr = Path(tmp) / "corpus"
            entry = _seed_entry(cr, "red-sphere")

            def render_fn(spec):
                # Simulate a render that reproduces the reference grammar:
                # write the seeded reference PNG to the requested save path.
                out = Path(spec["save"].get("path")) if spec["save"].get("path") else \
                    Path(tmp) / "render.png"
                out.parent.mkdir(parents=True, exist_ok=True)
                # The derived acceptance came FROM the red-on-dark ref, so it
                # passes when we render the same pixels.
                tc.write_rgb_png(out, tc._red_on_dark())
                return out

            res = it.iterate_entry(entry, render_fn=render_fn)
            self.assertTrue(res["converged"], res.get("report"))
            self.assertEqual(res["iters"], 1)
            self.assertFalse(res["needs_human"])

    def test_near_black_escapes_via_tweak(self):
        with tempfile.TemporaryDirectory() as tmp:
            cr = Path(tmp) / "corpus"
            entry = _seed_entry(cr, "red-sphere")

            state = {"n": 0}
            def render_fn(spec):
                state["n"] += 1
                out = Path(tmp) / f"render_{state['n']}.png"
                if state["n"] == 1:
                    # near-black: fails non_empty / color_family
                    tc.write_rgb_png(out, [[(2, 2, 3)] * 64 for _ in range(48)])
                else:
                    tc.write_rgb_png(out, tc._red_on_dark())
                return out

            res = it.iterate_entry(entry, render_fn=render_fn, max_iters=4)
            self.assertTrue(res["converged"])
            self.assertGreaterEqual(res["iters"], 2)  # needed at least one tweak

    def test_geometry_failure_flagged_needs_human(self):
        with tempfile.TemporaryDirectory() as tmp:
            cr = Path(tmp) / "corpus"
            entry = _seed_entry(cr, "red-sphere")

            def render_fn(spec):
                # A render that is VISIBLE (passes non_empty) but lacks the
                # reference's structural rows -> a real geometry/composition
                # problem the material/lighting tweaks cannot fix.
                out = Path(tmp) / "render.png"
                rows = [[(120, 120, 122)] * 64 for _ in range(48)]
                # faint uniform band (low structure, but not black/empty)
                for y in range(20, 28):
                    for x in range(64):
                        rows[y][x] = (140, 140, 145)
                tc.write_rgb_png(out, rows)
                return out

            res = it.iterate_entry(entry, render_fn=render_fn, max_iters=4)
            self.assertFalse(res["converged"])
            self.assertTrue(res["needs_human"])

    def test_no_convergence_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            cr = Path(tmp) / "corpus"
            entry = _seed_entry(cr, "red-sphere")
            def render_fn(spec):
                out = Path(tmp) / "render.png"
                tc.write_rgb_png(out, [[(2, 2, 3)] * 64 for _ in range(48)])
                return out
            res = it.iterate_entry(entry, render_fn=render_fn, max_iters=2)
            self.assertFalse(res["converged"])
            self.assertIsNotNone(res["png_path"])


class PromoteTests(unittest.TestCase):
    def test_promote_persists_and_flips_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            cr = Path(tmp) / "corpus"
            entry = _seed_entry(cr, "red-sphere")
            spec = it.build_candidate_scene(entry)
            render_out = Path(tmp) / "converged.png"
            tc.write_rgb_png(render_out, tc._red_on_dark())
            report = {"passed": True, "checks": []}

            promo = it.promote_entry(entry, spec, render_out, report, tier=7)
            self.assertTrue(promo["ok"])
            self.assertEqual(promo["slug"], "red-sphere")
            entry_dir = entry.dir
            self.assertTrue((entry_dir / "octane-preview.png").exists())
            self.assertTrue((entry_dir / "promotion.json").exists())
            self.assertTrue((entry_dir / "promotion_snippet.py").exists())
            reloaded = load_entry("red-sphere", corpus_root=cr)
            self.assertEqual(reloaded.status, "converged")
            # runtime registry got the promoted task
            self.assertIn(promo["task_slug"], [t.slug for t in it.PROMOTED_TASKS])

    def test_snippet_is_paste_ready(self):
        from benchmarks.spec import BenchmarkTask
        task = it.make_promoted_task("x", "X", 7, {"mesh_name": "wp9_x"})
        self.assertIsInstance(task, BenchmarkTask)
        self.assertTrue(task.native_octane_verified)
        self.assertEqual(task.build()["mesh_name"], "wp9_x")


if __name__ == "__main__":
    unittest.main()
