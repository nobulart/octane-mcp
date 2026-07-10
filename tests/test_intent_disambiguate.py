"""Tests for the scope -> domain intent resolver.

These encode the design rule from project review (2026-07-10): an object-scoped
property word resolves to the *object* domain without confirmation; a render-scoped
word resolves to *render*; only an unscoped word is ambiguous (default + confirm).
"""

import unittest

from octanex_mcp.intent.disambiguate import resolve


class TestScopeDomainResolver(unittest.TestCase):
    def test_object_resolution_unscoped_word(self):
        # "resolution of #1 and #3" -> object (mesh), high confidence, no confirm.
        r = resolve("increase the resolution of #1 and #3")
        self.assertEqual(r.domain, "object")
        self.assertEqual(r.ambiguity, "none")
        self.assertGreaterEqual(r.confidence, 0.9)
        self.assertFalse(r.needs_confirm)

    def test_render_resolution_explicit(self):
        r = resolve("set the output resolution to 4k")
        self.assertEqual(r.domain, "render")
        self.assertFalse(r.needs_confirm)

    def test_render_canvas_size(self):
        r = resolve("increase canvas size to 2048x2048")
        self.assertEqual(r.domain, "render")

    def test_unscoped_resolution_is_ambiguous(self):
        # No scope at all -> default render (statistically common) BUT needs confirm.
        r = resolve("increase resolution")
        self.assertTrue(r.needs_confirm)
        self.assertLess(r.confidence, 0.8)

    def test_object_refs_override_text_scan(self):
        # Even if the text also contains a render token, explicit object_refs win.
        r = resolve("resolution on output", object_refs=["#43"])
        self.assertEqual(r.domain, "object")
        self.assertFalse(r.needs_confirm)

    def test_smoothing_object_scope(self):
        r = resolve("apply mesh smoothing to #54")
        self.assertEqual(r.domain, "object")
        self.assertIn("modifier", r.note.lower())

    def test_smoothing_render_scope(self):
        r = resolve("add more smoothing to the render")
        self.assertEqual(r.domain, "render")

    def test_size_object_default(self):
        r = resolve("increase the size of #2")
        self.assertEqual(r.domain, "object")

    def test_size_canvas(self):
        r = resolve("increase the canvas size to 2048x2048")
        self.assertEqual(r.domain, "render")

    def test_unknown_property(self):
        r = resolve("frobnicate the widget")
        self.assertEqual(r.ambiguity, "unknown_property")
        self.assertTrue(r.needs_confirm)
        self.assertEqual(r.confidence, 0.0)

    def test_both_scopes_present_defers(self):
        r = resolve("resolution of #1 in the output")
        self.assertTrue(r.needs_confirm)
        self.assertLess(r.confidence, 0.7)


if __name__ == "__main__":
    unittest.main()
