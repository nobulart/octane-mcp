"""WP9 corpus expansion — offline tests (no network, no Octane, no vision model).

Mirror the PNG fixture helper from tests/test_review.py so we can build
deterministic references and candidates for the pixel-only deriver + filter.
"""

from __future__ import annotations

import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from octanex_mcp.corpus import (
    CORPUS_ROOT,
    CorpusEntry,
    corpus_index,
    find_grammar,
    iter_corpus,
    load_entry,
    register_reference,
    validate_entry,
)
from benchmarks.acceptance import (
    evaluate_acceptance,
    filter_reference,
    reference_to_acceptance,
)

import scripts.harvest_commons as harvest


def write_rgb_png(path: Path, rows: list[list[tuple[int, int, int]]]) -> None:
    height = len(rows)
    width = len(rows[0])
    raw = b"".join(b"\x00" + b"".join(bytes(pixel) for pixel in row) for row in rows)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(raw))
        + _chunk(b"IEND", b"")
    )


def _chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def _red_on_dark() -> list[list[tuple[int, int, int]]]:
    rows = [[(10, 10, 12)] * 64 for _ in range(48)]
    for y in range(12, 36):
        for x in range(24, 40):
            rows[y][x] = (200, 30, 30)
    return rows


def _blue_green_split() -> list[list[tuple[int, int, int]]]:
    rows = []
    bg = (10, 10, 12)
    for y in range(40):
        row = []
        for x in range(64):
            if x == 0:
                row.append(bg)                  # neutral background pixel at origin
            elif x < 32:
                row.append((20, 40, 220))       # saturated blue (left)
            else:
                row.append((20, 210, 40))       # saturated green (right)
        rows.append(row)
    return rows


class ReferenceToAcceptanceTests(unittest.TestCase):
    def test_derives_color_family_and_shape_and_bright_band(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "ref.png"
            write_rgb_png(p, _red_on_dark())
            spec = reference_to_acceptance(p)
        self.assertNotIn("error", spec)
        kinds = [c["kind"] for c in spec["acceptance"]]
        self.assertIn("non_empty", kinds)
        self.assertIn("review_ok", kinds)
        self.assertIn("color_family", kinds)
        self.assertIn("bright_fraction", kinds)
        self.assertIn("shape_profile", kinds)
        # The single dominant hue must be the red sphere.
        color = [c for c in spec["acceptance"] if c["kind"] == "color_family"][0]
        self.assertGreater(color["min_fraction"], 0.0)

    def test_two_hue_families_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "ref.png"
            write_rgb_png(p, _blue_green_split())
            spec = reference_to_acceptance(p)
        families = [c for c in spec["acceptance"] if c["kind"] == "color_family"]
        # blue + green occupy roughly equal halves -> >= 2 families above threshold
        self.assertGreaterEqual(len(families), 2)

    def test_bright_fraction_has_max_guard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "ref.png"
            write_rgb_png(p, _red_on_dark())
            spec = reference_to_acceptance(p)
            # The derived spec must actually evaluate as PASS on the reference itself.
            report = evaluate_acceptance(p, spec["acceptance"])
        bright = [c for c in spec["acceptance"] if c["kind"] == "bright_fraction"][0]
        self.assertIn("max_near_white", bright)
        self.assertTrue(report["passed"], report)


class FilterReferenceTests(unittest.TestCase):
    def test_rejects_near_black_blank(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "dark.png"
            write_rgb_png(p, [[(2, 2, 2)] * 8 for _ in range(8)])
            res = filter_reference(p)
        self.assertFalse(res["ok"])
        self.assertTrue(any("near-black" in r for r in res["reasons"]))

    def test_rejects_blown_out_white(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "white.png"
            write_rgb_png(p, [[(255, 255, 255)] * 8 for _ in range(8)])
            res = filter_reference(p)
        self.assertFalse(res["ok"])
        self.assertTrue(any("blown out" in r for r in res["reasons"]))

    def test_accepts_clean_single_subject(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "ref.png"
            write_rgb_png(p, _red_on_dark())
            res = filter_reference(p)
        self.assertTrue(res["ok"], res["reasons"])

    def test_rejects_flat_full_frame_fill(self) -> None:
        # A uniformly mid-grey frame has near-100% foreground bbox -> not a subject.
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "fill.png"
            write_rgb_png(p, [[(120, 120, 120)] * 40 for _ in range(40)])
            res = filter_reference(p)
        self.assertFalse(res["ok"])
        # Either the "subject too small" (0% real foreground) or "flat full-frame
        # fill" guard must fire on a uniform frame.
        self.assertTrue(
            any("flat full-frame" in r or "subject too small" in r for r in res["reasons"]),
            res["reasons"],
        )


class CorpusRegisterTests(unittest.TestCase):
    def _tmp_corpus(self) -> Path:
        d = Path(tempfile.mkdtemp()) / "corpus"
        return d

    def test_register_accepts_and_writes_manifest(self) -> None:
        corpus_root = self._tmp_corpus()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "ref.png"
            write_rgb_png(p, _red_on_dark())
            res = register_reference(
                slug="red-sphere", title="Red Sphere", source_url="https://example.com/x",
                license="CC-BY", reference_png=p, corpus_root=corpus_root,
                domain="photoreal", subject="sphere",
            )
        self.assertTrue(res["ok"], res.get("reasons"))
        entry = res["entry"]
        self.assertTrue(entry.manifest_path.exists())
        self.assertTrue(entry.reference_png.exists())
        # Round-trip: manifest reload yields the same acceptance spec.
        reloaded = load_entry("red-sphere", corpus_root=corpus_root)
        self.assertEqual(len(reloaded.derived_acceptance), len(entry.derived_acceptance))
        self.assertEqual(reloaded.status, "harvested")
        self.assertEqual(reloaded.license, "CC-BY")
        self.assertEqual(reloaded.source_url, "https://example.com/x")
        # Validation passes on a freshly written entry.
        self.assertTrue(validate_entry(reloaded)["ok"])
        # Index sees exactly one entry.
        self.assertEqual(corpus_index(corpus_root)["count"], 1)

    def test_register_rejects_filtered_reference_and_writes_nothing(self) -> None:
        corpus_root = self._tmp_corpus()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "dark.png"
            write_rgb_png(p, [[(1, 1, 1)] * 8 for _ in range(8)])
            res = register_reference(
                slug="blank-thing", title="Blank", source_url="https://example.com/y",
                license="CC-BY", reference_png=p, corpus_root=corpus_root,
            )
        self.assertFalse(res["ok"])
        self.assertIsNone(res["entry"])
        self.assertFalse((corpus_root / "blank-thing").exists())

    def test_register_accepts_bytes_payload(self) -> None:
        corpus_root = self._tmp_corpus()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "ref.png"
            write_rgb_png(p, _red_on_dark())
            data = p.read_bytes()
            res = register_reference(
                slug="bytes-ref", title="Bytes", source_url="https://example.com/z",
                license="CC-BY", reference_png=data, corpus_root=corpus_root,
            )
        self.assertTrue(res["ok"], res.get("reasons"))
        self.assertTrue((corpus_root / "bytes-ref" / "reference.png").exists())

    def test_iter_corpus_skips_dirs_without_manifest(self) -> None:
        corpus_root = self._tmp_corpus()
        (corpus_root / "no-manifest").mkdir(parents=True)
        self.assertEqual(iter_corpus(corpus_root), [])


class HarvestOfflineTests(unittest.TestCase):
    """harvest_commons with an injected mock fetcher (no network)."""

    def _mock_fetch(self, q: str) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "ref.png"
            write_rgb_png(p, _red_on_dark())
            return {
                "ok": True,
                "image_bytes": p.read_bytes(),
                "title": q,
                "source_url": f"mock://commons/{q}",
                "license": "CC-BY-mock",
                "labels": {"subject": q, "categories": ["Mock"]},
            }

    def _mock_fetch_blank(self, q: str) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "dark.png"
            write_rgb_png(p, [[(1, 1, 1)] * 8 for _ in range(8)])
            return {
                "ok": True,
                "image_bytes": p.read_bytes(),
                "title": q,
                "source_url": f"mock://commons/{q}",
                "license": "CC-BY-mock",
                "labels": {"subject": q},
            }

    def test_harvest_subject_accepts(self) -> None:
        corpus_root = Path(tempfile.mkdtemp()) / "corpus"
        res = harvest.harvest_subject("red sphere", fetch=self._mock_fetch, corpus_root=corpus_root)
        self.assertTrue(res["ok"], res.get("reasons"))
        self.assertEqual(res["harvest"]["license"], "CC-BY-mock")
        self.assertEqual(res["harvest"]["source_url"], "mock://commons/red sphere")

    def test_harvest_subject_rejects_filtered(self) -> None:
        corpus_root = Path(tempfile.mkdtemp()) / "corpus"
        res = harvest.harvest_subject("void", fetch=self._mock_fetch_blank, corpus_root=corpus_root)
        self.assertFalse(res["ok"])
        self.assertIsNone(res["entry"])
        self.assertFalse((corpus_root / "void").exists())

    def test_harvest_batch_counts_accept_reject(self) -> None:
        corpus_root = Path(tempfile.mkdtemp()) / "corpus"
        report = harvest.harvest_batch(
            ["good", "bad"], fetch=lambda q: self._mock_fetch(q) if q == "good" else self._mock_fetch_blank(q),
            corpus_root=corpus_root,
        )
        self.assertEqual(report["total"], 2)
        self.assertEqual(report["accepted"], 1)
        self.assertEqual(report["rejected"], 1)


def _blue_on_dark() -> list[list[tuple[int, int, int]]]:
    rows = [[(10, 10, 12)] * 64 for _ in range(48)]
    for y in range(12, 36):
        for x in range(24, 40):
            rows[y][x] = (30, 60, 210)
    return rows


class FindGrammarTests(unittest.TestCase):
    def _seed(self, tmp: Path) -> Path:
        corpus_root = tmp / "corpus"
        # red sphere: label "red" + subject "sphere"
        p_red = tmp / "red.png"
        write_rgb_png(p_red, _red_on_dark())
        register_reference(slug="red-sphere", title="Red Sphere", source_url="https://e/r",
                           license="CC-BY", reference_png=p_red, corpus_root=corpus_root,
                           domain="photoreal", subject="sphere", labels={"subject": "sphere", "color": "red"})
        # blue vase: label "blue" + subject "vase"
        p_blue = tmp / "blue.png"
        write_rgb_png(p_blue, _blue_on_dark())
        register_reference(slug="blue-vase", title="Blue Vase", source_url="https://e/b",
                           license="CC-BY", reference_png=p_blue, corpus_root=corpus_root,
                           domain="photoreal", subject="vase", labels={"subject": "vase", "color": "blue"})
        return corpus_root

    def test_finds_nearest_by_subject(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cr = self._seed(Path(tmp))
            res = find_grammar("sphere", corpus_root=cr)
            self.assertEqual(res["match_count"], 1)
            self.assertEqual(res["best"]["slug"], "red-sphere")

    def test_hue_overlap_promotes_color_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cr = self._seed(Path(tmp))
            res = find_grammar("red ball", corpus_root=cr)
            self.assertEqual(res["best"]["slug"], "red-sphere")
            # the red-sphere entry should outrank the blue one
            slugs = [m["slug"] for m in res["matches"]]
            self.assertIn("red-sphere", slugs)

    def test_domain_filter_narrows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cr = self._seed(Path(tmp))
            res = find_grammar("sphere", domain="stylized", corpus_root=cr)
            self.assertEqual(res["match_count"], 0)
            res2 = find_grammar("sphere", domain="photoreal", corpus_root=cr)
            self.assertGreaterEqual(res2["match_count"], 1)

    def test_no_match_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cr = self._seed(Path(tmp))
            res = find_grammar("nonexistent-xyz", corpus_root=cr)
            self.assertEqual(res["match_count"], 0)
            self.assertIsNone(res["best"])


if __name__ == "__main__":
    unittest.main()
