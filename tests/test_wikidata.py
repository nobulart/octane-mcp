"""Offline tests for WP9 Wikidata subject-match enrichment (no network)."""

import unittest

from octanex_mcp.wikidata import (
    search_entity,
    file_metadata,
    subject_matches_query,
    _tokenize,
    _head_noun,
)


def _apple_file_meta(title):
    return {"title": title, "categories": [
        "Category:Apples on white background",
        "Category:Featured pictures of fruit",
        "Category:CC-BY-2.0",
    ]}


def _butterfly_file_meta(title):
    return {"title": title, "categories": [
        "Category:Cymothoe egesta",
        "Category:Nymphalidae",
        "Category:Animals looking right",
        "Category:2021 photographs of Ghana",
    ]}


class TokenizerTests(unittest.TestCase):
    def test_stopwords_dropped(self):
        toks = _tokenize("red apple on white background")
        self.assertNotIn("on", toks)
        self.assertNotIn("white", toks)
        self.assertIn("apple", toks)
        self.assertIn("red", toks)

    def test_numeric_dropped(self):
        self.assertEqual(_tokenize("photo 2021"), set())


class HeadNounTests(unittest.TestCase):
    def test_strips_descriptors(self):
        self.assertEqual(_head_noun("red apple"), {"apple"})
        self.assertEqual(_head_noun("blue ceramic vase"), {"vase"})
        self.assertEqual(_head_noun("wooden chair"), {"chair"})

    def test_falls_back_when_only_descriptors(self):
        # No noun left -> returns the descriptors so we don't silently accept.
        self.assertTrue(_head_noun("big red"))


class EntitySearchTests(unittest.TestCase):
    def test_injected_search_returns_entity(self):
        ent = search_entity("yellow banana", search=lambda q: {"search": [{
            "id": "Q503", "label": "banana",
            "description": "elongated edible fruit", "aliases": [{"value": "bananas"}],
        }]})
        self.assertEqual(ent["id"], "Q503")
        self.assertEqual(ent["label"], "banana")

    def test_no_results_returns_none(self):
        self.assertIsNone(search_entity("x", search=lambda q: {"search": []}))


class MatchTests(unittest.TestCase):
    # NOTE: the anchor is the QUERY HEAD NOUN (e.g. 'apple'), not Wikidata.
    # The match cases below deliberately pass NO `search` callable so the live
    # Wikidata call is skipped (it is only optional enrichment).

    def test_apple_query_matches_apple_file(self):
        res = subject_matches_query("red apple", "File:Red Apple.jpg",
                                   file_meta=_apple_file_meta)
        self.assertTrue(res["ok"], res["reasons"])
        self.assertIn("apple", res["overlap"])
        self.assertTrue(res["verified"])

    def test_banana_query_rejects_butterfly_file(self):
        # The real failure case: Commons returned a butterfly for 'yellow banana'.
        res = subject_matches_query(
            "yellow banana", "File:Common yellow glider underside 2.jpg",
            file_meta=_butterfly_file_meta,
        )
        self.assertFalse(res["ok"])
        self.assertTrue(res["verified"])
        self.assertTrue(any("semantic mismatch" in r for r in res["reasons"]))
        self.assertEqual(res["overlap"], [])

    def test_vase_query_matches_vase_file(self):
        res = subject_matches_query(
            "blue ceramic vase", "File:Blue Punjabi Vase.JPG",
            file_meta=lambda t: {"title": t, "categories": [
                "Category:Blue vases", "Category:Ceramic vases"]},
        )
        self.assertTrue(res["ok"], res["reasons"])
        self.assertIn("vase", res["overlap"])

    def test_unverifiable_empty_categories_rejects(self):
        # If the categories lookup failed (network/429) or the file is
        # uncategorized, we must FAIL CLOSED (reject) rather than silently accept
        # a possibly-mislabeled reference into the curated corpus.
        res = subject_matches_query(
            "yellow banana", "File:Mystery.jpg",
            file_meta=lambda t: {"title": t, "categories": []},
        )
        self.assertFalse(res["ok"])
        self.assertFalse(res["verified"])
        self.assertTrue(any("unverified" in r for r in res["reasons"]))


class NetworkFailSoftTests(unittest.TestCase):
    def test_live_get_json_returns_none_on_failure(self):
        from octanex_mcp.wikidata import _live_get_json
        # A guaranteed-dead host must return None (not raise).
        self.assertIsNone(_live_get_json("http://127.0.0.1:1/nope", user_agent="x", retries=1))

    def test_file_metadata_fail_soft(self):
        from octanex_mcp.wikidata import file_metadata
        self.assertEqual(
            file_metadata("File:X.jpg", file_meta=lambda t: {"title": t, "categories": []})["categories"],
            [],
        )


if __name__ == "__main__":
    unittest.main()
