"""WP9 — Harvest labeled, licensed reference imagery from Wikimedia Commons.

This script is the *network* layer of the corpus expansion (RAGS). It is the
only place that talks to Wikimedia; ``src/octanex_mcp/corpus.py`` stays
pure-Python and offline. The network calls are injected (``fetch_image_bytes`` /
``fetch_labels``), so the harvest + pixel-filter + corpus-write pipeline is
fully unit-testable without touching the network:

    PYTHONPATH= uv run python scripts/harvest_commons.py --dry-run
    PYTHONPATH= uv run python -m unittest tests.test_corpus

What it does per subject query:
  1. resolve a Commons file/page for ``<query>`` (via Commons API or Wikidata
     SPARQL) and pull structured labels (subject, material, era, domain);
  2. download the (downsampled) image bytes;
  3. hand the bytes + provenance to ``corpus.register_reference``, which runs
     the pixel harvest-filter and derives the acceptance spec;
  4. report accept/reject. Rejected references are never written.

Provenance (source URL + license) is always captured in the manifest — WP9's
"licensed, labeled, provenance" requirement. The default live fetchers use the
``commons``/``www.wikidata.org`` APIs over urllib (stdlib only); swap them for
a cached/mocked version in tests or for offline batch harvests.

WARNING: the live fetchers are intentionally conservative. They resolve a
single best candidate per query and refuse anything without a clear license /
without a downloadable image. Bulk harvesting should set a descriptive
User-Agent and respect the Wikimedia rate limit (max ~1 req/s).
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from octanex_mcp.corpus import register_reference  # noqa: E402

DEFAULT_USER_AGENT = "octanex-mcp/0.1 (WP9 corpus harvest; contact: hermes@nobulart.com)"


# ---------------------------------------------------------------------------
# Network layer (injectable)
# ---------------------------------------------------------------------------

def _http_get_json(url: str, *, user_agent: str = DEFAULT_USER_AGENT) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 - https only by caller
        return json.loads(resp.read().decode("utf-8"))


def _http_get_bytes(url: str, *, user_agent: str = DEFAULT_USER_AGENT) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
        return resp.read()


def commons_image_fetcher(query: str, *, width: int = 512,
                          user_agent: str = DEFAULT_USER_AGENT,
                          _get: Callable[[str], Any] = _http_get_json,
                          _get_bytes: Callable[[str], bytes] = _http_get_bytes,
                          ) -> dict[str, Any]:
    """Resolve one Commons image + labels for ``query``.

    Returns ``{"ok": bool, "image_bytes": bytes|None, "title": str,
    "source_url": str, "license": str, "labels": {...}, "error": ...}``.

    Strategy: Commons search API -> top file -> imageinfo (url + license) +
    a best-effort label set from the file's structured data / categories.
    """
    api = "https://commons.wikimedia.org/w/api.php"
    search = (
        f"{api}?action=query&format=json&generator=search&gsrsearch="
        f"{urllib.parse.quote(query)}&gsrnamespace=6&gsrlimit=5"
        "&prop=imageinfo&iiprop=url|extmetadata|size|mime&iiurlwidth="
        f"{width}"
    )
    try:
        data = _get(search)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "image_bytes": None, "error": f"commons search failed: {exc}"}

    pages = (data.get("query") or {}).get("pages") or {}
    candidates = []
    for page in pages.values():
        ii = (page.get("imageinfo") or [{}])[0]
        if not ii:
            continue
        mime = ii.get("mime", "")
        if not mime.startswith("image/"):
            continue
        thumb = ii.get("thumburl") or ii.get("url")
        if not thumb:
            continue
        meta = ii.get("extmetadata") or {}
        license_short = (meta.get("LicenseShortName") or {}).get("value") or "unknown"
        candidates.append({
            "title": page.get("title", ""),
            "url": thumb,
            "source_url": ii.get("descriptionurl") or thumb,
            "license": license_short,
            "categories": meta.get("Categories", {}).get("value", ""),
        })
    if not candidates:
        return {"ok": False, "image_bytes": None, "error": "no image candidates on Commons"}

    # Prefer the first candidate (search-ranked); refuse unknown license.
    best = candidates[0]
    if best["license"].lower() in ("", "unknown"):
        return {"ok": False, "image_bytes": None,
                "error": f"no license for {best['title']!r}"}
    try:
        image_bytes = _get_bytes(best["url"])
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "image_bytes": None, "error": f"image download failed: {exc}"}
    if not image_bytes:
        return {"ok": False, "image_bytes": None, "error": "empty image"}

    labels = _derive_labels(query, best)
    return {
        "ok": True,
        "image_bytes": image_bytes,
        "title": best["title"].replace("File:", "").rsplit(".", 1)[0],
        "source_url": best["source_url"],
        "license": best["license"],
        "labels": labels,
    }


def _derive_labels(query: str, best: dict[str, Any]) -> dict[str, Any]:
    """Best-effort structured labels from query + Commons metadata.

    Commons categories are a weak proxy for domain/era; we surface them verbatim
    and let the corpus manifest carry them. Domain/era are left to the caller /
    a later Wikidata SPARQL enrichment step (WP9 task 2 leaves SPARQL as an
    optional enrichment, not a hard dependency here).
    """
    cats = best.get("categories", "") or ""
    cat_list = [c.strip() for c in cats.split("|") if c.strip()] if "|" in cats else [
        c.strip() for c in cats.replace("[", "").replace("]", "").split("\n") if c.strip()
    ]
    return {
        "subject": query,
        "commons_title": best["title"],
        "categories": cat_list[:8],
    }


# ---------------------------------------------------------------------------
# Harvest orchestration
# ---------------------------------------------------------------------------

def harvest_subject(query: str, *,
                    fetch: Callable[[str], dict[str, Any]] = commons_image_fetcher,
                    domain: str = "uncategorized",
                    corpus_root: Path | None = None,
                    **fetch_kwargs: Any) -> dict[str, Any]:
    """Harvest one subject: fetch -> register (pixel-filter + derive).

    Returns the ``register_reference`` result (``{"ok", "entry", "reasons"}``)
    plus ``harvest`` metadata (source_url, license, labels, fetch_error).
    """
    fetched = fetch(query, **fetch_kwargs)
    if not fetched.get("ok"):
        return {"ok": False, "entry": None, "reasons": [fetched.get("error", "fetch failed")],
                "harvest": fetched}
    reg = register_reference(
        slug=query,
        title=fetched["title"],
        source_url=fetched["source_url"],
        license=fetched["license"],
        reference_png=fetched["image_bytes"],
        domain=domain,
        subject=query,
        labels=fetched.get("labels", {}),
        corpus_root=corpus_root or _default_corpus_root(),
    )
    reg["harvest"] = {k: fetched[k] for k in ("source_url", "license", "labels") if k in fetched}
    return reg


def _default_corpus_root() -> Path:
    from octanex_mcp.corpus import CORPUS_ROOT
    return CORPUS_ROOT


def harvest_batch(queries: list[str], *,
                  fetch: Callable[[str], dict[str, Any]] = commons_image_fetcher,
                  domain: str = "uncategorized",
                  **fetch_kwargs: Any) -> dict[str, Any]:
    """Harvest many subjects; never aborts on one failure."""
    results = []
    accepted = 0
    for q in queries:
        r = harvest_subject(q, fetch=fetch, domain=domain, **fetch_kwargs)
        results.append({"query": q, "ok": r["ok"], "reasons": r.get("reasons", [])})
        accepted += 1 if r["ok"] else 0
    return {"total": len(queries), "accepted": accepted, "rejected": len(queries) - accepted,
            "results": results}


def _main() -> None:
    ap = argparse.ArgumentParser(description="WP9 — harvest Wikimedia Commons references into the corpus")
    ap.add_argument("queries", nargs="*", help="subject queries to harvest")
    ap.add_argument("--domain", default="uncategorized")
    ap.add_argument("--dry-run", action="store_true",
                    help="run the pipeline with a mock fetcher (no network); writes a temp corpus entry")
    args = ap.parse_args()

    if args.dry_run:
        # Deterministic mock: a red subject on dark background (passes filter).
        def mock_fetch(q: str) -> dict[str, Any]:
            import struct, zlib
            from pathlib import Path as _P

            def _png(path, rows):
                h = len(rows); w = len(rows[0])
                raw = b"".join(b"\x00" + b"".join(bytes(p) for p in row) for row in rows)
                def _chunk(k, d):
                    return struct.pack(">I", len(d)) + k + d + struct.pack(">I", zlib.crc32(k + d) & 0xFFFFFFFF)
                path.write_bytes(b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                                 + _chunk(b"IDAT", zlib.compress(raw)) + _chunk(b"IEND", b""))
            rows = [[(10, 10, 12)] * 64 for _ in range(48)]
            for y in range(12, 36):
                for x in range(24, 40):
                    rows[y][x] = (200, 30, 30)
            import tempfile
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            _png(_P(tmp.name), rows); tmp.close()
            return {"ok": True, "image_bytes": _P(tmp.name).read_bytes(),
                    "title": q, "source_url": f"mock://commons/{q}",
                    "license": "CC-BY-mock", "labels": {"subject": q}}
        report = harvest_batch(args.queries or ["mock-red-subject"], fetch=mock_fetch, domain=args.domain)
    else:
        if not args.queries:
            ap.error("provide at least one query, or --dry-run")
        report = harvest_batch(args.queries, domain=args.domain)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    _main()
