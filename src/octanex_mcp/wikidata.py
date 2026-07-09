"""WP9 enrichment — canonical subject resolution + semantic match check.

The Commons image search returns the first file whose title matches the query
string, not a verified single-subject photo of that object. For ``yellow
banana`` it returned a *butterfly* ("Common yellow glider"); for ``green leaf``
a political flag. The pixel-QA filter cannot catch this (no vision model, by
design), so we add a cheap, fully-offline-testable text check:

  1. Resolve the query's canonical subject via Wikidata entity search (label +
     description tokens) — the "what we actually asked for".
  2. Collect the resolved Commons file's title + categories (the "what the file
     is actually about").
  3. Require at least one token overlap between the two. A file about a banana
     will sit in ``Category:...banana...`` or have "banana" in its title; a
     butterfly file will not, so it is rejected *before* it enters the corpus.

Network access is isolated behind two injectable callables (``search``,
``file_meta``) so the matcher is unit-testable without hitting Wikidata.

No SPARQL dependency: the Commons ``categories`` list is rich and
query-relevant enough for v1. A later step could tighten this with SDC
``depicts`` (P180) claims, which are currently sparse.
"""

from __future__ import annotations

import re
import urllib.parse
from typing import Any, Callable, Iterable

# Stopwords dropped from token sets so trivial words don't create false matches.
_STOPWORDS = frozenset({
    "the", "a", "an", "of", "on", "in", "at", "by", "for", "to", "and", "or",
    "with", "from", "as", "is", "are", "photograph", "photographs", "photo",
    "image", "image", "file", "jpg", "png", "svg", "und", "der", "die", "the",
    "looking", "right", "left", "top", "bottom", "view", "views", "white",
    "background", "black", "colored", "colour", "colored", "horizontal",
    "vertical", "x", "y", "z",
})


def _tokenize(text: str) -> set[str]:
    """Lowercase word tokens, dropping stopwords and pure numbers."""
    if not text:
        return set()
    toks = re.findall(r"[a-z0-9][a-z0-9']*", text.lower())
    return {t for t in toks if t not in _STOPWORDS and not t.isdigit()}


# Descriptor words stripped to find the query's HEAD NOUN (the subject we
# actually want a photo of). Commons image search already matched the descriptors
# in the title, so the semantic check must validate the *noun*, not "red" or
# "wooden" (those match incidentally everywhere).
_DESCRIPTORS = frozenset({
    "red", "green", "blue", "yellow", "orange", "purple", "pink", "black",
    "white", "brown", "grey", "gray", "cyan", "magenta", "gold", "golden",
    "silver", "wooden", "ceramic", "metal", "metallic", "glass", "plastic",
    "small", "large", "big", "tiny", "huge", "little", "old", "new", "ancient",
    "modern", "realistic", "stylized", "cartoon", "flat", "round", "square",
    "wood", "metalic", "wooden", "single", "double", "simple", "complex",
})


def _head_noun(query: str) -> set[str]:
    """The subject noun(s) of a query after stripping color/material/size words.

    'red apple' -> {'apple'}; 'blue ceramic vase' -> {'vase'}; 'wooden chair'
    -> {'chair'}. This is a far more reliable anchor than Wikidata entity search,
    which mis-resolves descriptive queries ('red apple' -> a settlement).
    """
    toks = _tokenize(query)
    head = {t for t in toks if t not in _DESCRIPTORS}
    return head or toks  # if only descriptors remain, fall back to all tokens


def _subject_tokens(query: str, entity: dict[str, Any] | None) -> set[str]:
    """Tokens describing what the query (canonically) asked for.

    Anchored on the query HEAD NOUN (see ``_head_noun``); Wikidata entity data,
    when present, is folded in as *enrichment* (broadens recall) but never
    overrides the head noun as the anchor of record.
    """
    toks = _head_noun(query)
    if entity:
        toks |= _tokenize(entity.get("label", ""))
        toks |= _tokenize(entity.get("description", ""))
        for alias in entity.get("aliases", []) or []:
            toks |= _tokenize(alias if isinstance(alias, str) else alias.get("value", ""))
    return toks


def _file_tokens(title: str, categories: Iterable[str]) -> set[str]:
    """Tokens describing what the resolved file is actually about."""
    toks = _tokenize(title.replace("File:", "").replace("_", " "))
    for cat in categories or []:
        # Drop the "Category:" prefix and keep the descriptive remainder.
        cat_name = cat.split(":", 1)[-1] if ":" in cat else cat
        toks |= _tokenize(cat_name)
    return toks


def _category_tokens(categories: Iterable[str]) -> set[str]:
    """Tokens drawn ONLY from Commons categories (the strong subject signal).

    The file title is weak (a file named 'Mystery.jpg' tells us nothing), so the
    semantic REJECT gate keys on category tokens, not the title.
    """
    toks: set[str] = set()
    for cat in categories or []:
        cat_name = cat.split(":", 1)[-1] if ":" in cat else cat
        toks |= _tokenize(cat_name)
    return toks


def _substring_overlap(anchor: set[str], cats: set[str]) -> set[str]:
    """Anchor tokens that occur (as substring) in any category token.

    Handles Commons pluralization/hyphenation ('apple' in 'apples'/'red-apple',
    'vase' in 'vases') without requiring exact equality. Short tokens (<3 chars)
    are ignored as overlap candidates to avoid noise (e.g. 'cat' in 'category').
    """
    out: set[str] = set()
    for a in anchor:
        if len(a) < 3:
            continue
        for c in cats:
            if a in c or c in a:
                out.add(a)
                break
    return out


def _live_get_json(url: str, *, user_agent: str, retries: int = 3) -> dict[str, Any] | None:
    """GET JSON with a small backoff; return None on any network/HTTP failure.

    A failed lookup (rate-limit 429, timeout, DNS) is treated as "could not
    verify", NOT as a hard rejection — the caller then skips the semantic gate
    and lets the pixel filter decide. This keeps the harvest resumable against
    flaky Wikimedia APIs instead of crashing the whole batch.
    """
    import json
    import time
    import urllib.error
    import urllib.request

    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": user_agent})
            with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < retries - 1:
                time.sleep(2.0 * (attempt + 1))  # back off on rate-limit
                continue
            return None
        except Exception:  # noqa: BLE001 - any network failure -> unverifiable
            return None
    return None


def search_entity(query: str, *,
                  search: Callable[[str], dict[str, Any]] | None = None,
                  user_agent: str = "octanex-mcp/0.1 (research)") -> dict[str, Any] | None:
    """Resolve a query to its top Wikidata entity.

    Returns ``{"id", "label", "description", "aliases"}`` or ``None`` if no
    entity is found / the lookup fails. ``search`` is injectable for offline
    tests; when omitted a live ``wbsearchentities`` call is made (fail-soft:
    network/429 errors return ``None`` rather than raising).
    """
    if search is None:
        url = (
            "https://www.wikidata.org/w/api.php?action=wbsearchentities"
            f"&search={urllib.parse.quote(query)}&language=en&format=json&limit=1"
        )
        data = _live_get_json(url, user_agent=user_agent)
        results = (data or {}).get("search", [])
    else:
        results = search(query).get("search", [])

    if not results:
        return None
    s = results[0]
    return {
        "id": s.get("id"),
        "label": s.get("label", ""),
        "description": s.get("description", ""),
        "aliases": s.get("aliases", []) or [],
    }


def file_metadata(title: str, *,
                  file_meta: Callable[[str], dict[str, Any]] | None = None,
                  user_agent: str = "octanex-mcp/0.1 (research)") -> dict[str, Any]:
    """Return ``{"title", "categories", "description"}`` for a Commons file.

    ``file_meta`` is injectable for offline tests; when omitted a live Commons
    ``prop=categories`` call is made (fail-soft: returns empty categories on any
    error so the semantic gate degrades to "unverifiable" rather than crashing).
    """
    if file_meta is None:
        t = urllib.parse.quote(title)
        url = (
            "https://commons.wikimedia.org/w/api.php?action=query"
            f"&titles={t}&prop=categories&cllimit=50&format=json"
        )
        data = _live_get_json(url, user_agent=user_agent)
        cats: list[str] = []
        if data:
            for pg in data.get("query", {}).get("pages", {}).values():
                cats.extend(c.get("title", "") for c in pg.get("categories", []))
        return {"title": title, "categories": cats, "description": ""}
    injected = file_meta(title)
    if not injected:
        # An injected callable may return None (e.g. a mock for an
        # unresolvable file) -> treat as empty/unverifiable, never crash.
        return {"title": title, "categories": [], "description": ""}
    return injected


def subject_matches_query(query: str, title: str, *,
                          categories: Iterable[str] | None = None,
                          search: Callable[[str], dict[str, Any]] | None = None,
                          file_meta: Callable[[str], dict[str, Any]] | None = None,
                          min_overlap: int = 1) -> dict[str, Any]:
    """Decide whether a resolved Commons file is actually about ``query``.

    Returns ``{"ok": bool, "reasons": [...], "subject_tokens": [...],
    "file_tokens": [...], "entity": {...}}``.

    The match requires at least ``min_overlap`` token shared between the
    canonical subject (query + Wikidata label/aliases/description) and the file
    (title + categories). A zero-overlap file is semantically off-topic and is
    rejected (e.g. ``yellow banana`` -> a butterfly file with only lepidoptera
    categories).
    """
    # Wikidata entity resolution is OPTIONAL enrichment (it mis-resolves
    # descriptive queries, so it is never the anchor). Only call it when an
    # injectable `search` is supplied, to avoid a wasted/unreliable live call
    # during real harvests. The head noun is always the anchor of record.
    entity = search_entity(query, search=search) if search is not None else None
    if categories is None:
        meta = file_metadata(title, file_meta=file_meta)
        categories = meta.get("categories", [])

    # Anchor on the QUERY HEAD NOUN (e.g. 'apple' from 'red apple'), NOT the
    # Wikidata label — live Wikidata mis-resolves descriptive queries
    # ('red apple' -> a settlement). Wikidata, when it resolves, only *broadens*
    # the subject token set; it never becomes the anchor of record.
    subj = _subject_tokens(query, entity)
    anchor = _head_noun(query)
    file_t = _file_tokens(title, categories or [])
    cat_t = _category_tokens(categories or [])
    # Gate the REJECT on category tokens (the strong signal). The title is weak
    # (a file named 'Mystery.jpg' says nothing), so it never alone rejects.
    # Use SUBSTRING overlap, not exact-token equality, so 'apple' matches
    # 'apples' / 'red-apple' and 'vase' matches 'vases' (Commons categories
    # are heavily pluralized / hyphenated).
    overlap = _substring_overlap(anchor, cat_t)
    reasons: list[str] = []
    # Fail-CLOSED on uncertainty: this gate guards a *curated* reference corpus
    # that feeds the RAGS warm-start, so silently accepting an unverifiable file
    # (e.g. a 429'd category lookup) would let a mislabeled image through.
    #  - categories resolved + noun present  -> accept
    #  - categories resolved + noun absent   -> REJECT (semantic mismatch)
    #  - categories NOT resolved (lookup failed/uncategorized) -> REJECT with an
    #    'unverified' reason so the harvest skips the subject rather than accepts.
    if cat_t and not overlap:
        bits = [f"subject noun '{sorted(anchor)}'"]
        bits.append(f"file categories {sorted(cat_t)[:8]}")
        reasons.append("semantic mismatch: subject noun not found in file categories (" + "; ".join(bits) + ")")
    elif not cat_t:
        reasons.append("unverified: category lookup failed or file is uncategorized; skipping to avoid accepting a mislabeled reference")
    return {
        "ok": bool(overlap),
        "verified": bool(cat_t),
        "reasons": reasons,
        "subject_tokens": sorted(subj),
        "anchor_tokens": sorted(anchor),
        "file_tokens": sorted(file_t),
        "overlap": sorted(overlap),
        "entity": entity,
    }
