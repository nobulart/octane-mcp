"""WP9 corpus data model — labeled, licensed reference -> self-describing grammar.

Sibling to ``recipes.py``: a *corpus entry* is the harvested counterpart to a
*recipe*. Whereas a recipe ships a hand-authored command sequence, a corpus
entry is harvested from a labeled, licensed reference image and derives its own
acceptance spec from pixels (``octanex_mcp.acceptance.reference_to_acceptance``)
— no vision model, no hand-authoring.

Layout (per entry, ``corpus/<slug>/``):

    reference.png      the (pixel-filtered) harvested reference image
    manifest.json      provenance + domain/era tags + derived acceptance spec
    grammar_spec.yaml  parametric OBJ generator (WP9 task 7; written later)
    iterations/        per-iteration candidate.png + report (WP9 task 4)
    octane-preview.png native converged render (WP9 task 4)

This module is pure-Python and offline-testable: it depends only on stdlib and
``octanex_mcp.acceptance`` (which itself uses only ``octanex_mcp.review``).
Network access lives in ``scripts/harvest_commons.py`` and is injected at that
layer, never here.
"""

from __future__ import annotations

import json
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from octanex_mcp.acceptance import filter_reference, reference_to_acceptance

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS_ROOT = REPO_ROOT / "corpus"

# Manifest keys persisted for every entry.
_MANIFEST_VERSION = 1
_REQUIRED_PROVENANCE = ("source_url", "license")


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-")
    return slug or "entry"


@dataclass
class CorpusEntry:
    slug: str
    title: str
    domain: str
    source_url: str
    license: str
    labels: dict[str, Any] = field(default_factory=dict)
    era: str | None = None
    subject: str | None = None
    derived_acceptance: list[dict[str, Any]] = field(default_factory=list)
    derived: dict[str, Any] = field(default_factory=dict)
    harvested_filter: dict[str, Any] = field(default_factory=dict)
    status: str = "harvested"
    manifest_version: int = _MANIFEST_VERSION
    entry_dir: Path | None = None

    # --- files -----------------------------------------------------------
    @property
    def dir(self) -> Path:
        return self.entry_dir or (CORPUS_ROOT / self.slug)

    @property
    def reference_png(self) -> Path:
        return self.dir / "reference.png"

    @property
    def manifest_path(self) -> Path:
        return self.dir / "manifest.json"

    @property
    def preview_png(self) -> Path:
        return self.dir / "octane-preview.png"

    # --- (de)serialization ----------------------------------------------
    def to_manifest(self) -> dict[str, Any]:
        return {
            "manifest_version": self.manifest_version,
            "slug": self.slug,
            "title": self.title,
            "domain": self.domain,
            "subject": self.subject,
            "era": self.era,
            "labels": self.labels,
            "source_url": self.source_url,
            "license": self.license,
            "status": self.status,
            "harvest_filter": self.harvested_filter,
            "derived": self.derived,
            "derived_acceptance": self.derived_acceptance,
        }

    @classmethod
    def from_manifest(cls, data: Mapping[str, Any], entry_dir: Path | None = None) -> "CorpusEntry":
        entry = cls(
            slug=str(data["slug"]),
            title=str(data.get("title") or data["slug"]),
            domain=str(data.get("domain") or "uncategorized"),
            source_url=str(data.get("source_url") or ""),
            license=str(data.get("license") or ""),
            labels=dict(data.get("labels") or {}),
            era=data.get("era"),
            subject=data.get("subject"),
            derived_acceptance=list(data.get("derived_acceptance") or []),
            derived=dict(data.get("derived") or {}),
            harvested_filter=dict(data.get("harvest_filter") or {}),
            status=str(data.get("status") or "harvested"),
            manifest_version=int(data.get("manifest_version", _MANIFEST_VERSION)),
        )
        if entry_dir is not None:
            entry.entry_dir = Path(entry_dir)
        return entry


def register_reference(
    *,
    slug: str,
    title: str,
    source_url: str,
    license: str,
    reference_png: Path | bytes,
    domain: str = "uncategorized",
    subject: str | None = None,
    era: str | None = None,
    labels: Mapping[str, Any] | None = None,
    corpus_root: Path = CORPUS_ROOT,
) -> dict[str, Any]:
    """Harvest one reference into a corpus entry.

    Steps (pure-Python, no network, no vision model):
      1. pixel harvest-filter the reference (reject blank/blown-out/busy/tiny);
      2. derive a pixel-only acceptance spec from the reference;
      3. write ``reference.png`` + ``manifest.json``.

    Returns ``{"ok": bool, "entry": <CorpusEntry|None>, "reasons": [...]}``.
    On filter rejection, no files are written and ``entry`` is ``None``.
    """
    entry_dir = Path(corpus_root) / _slugify(slug)
    reasons: list[str] = []

    # Resolve the reference pixels to a temp path so the filter/deriver can
    # read it (they operate on PNG files via octanex_mcp.review).
    if isinstance(reference_png, (bytes, bytearray)):
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.write(bytes(reference_png))
        tmp.close()
        ref_path = Path(tmp.name)
        cleanup = True
    else:
        ref_path = Path(reference_png)
        cleanup = False

    try:
        filt = filter_reference(ref_path)
        if not filt["ok"]:
            reasons.extend(filt["reasons"])
            return {"ok": False, "entry": None, "reasons": reasons, "harvest_filter": filt}

        spec = reference_to_acceptance(ref_path)
        if spec.get("error"):
            reasons.append(f"acceptance derivation failed: {spec['error']}")
            return {"ok": False, "entry": None, "reasons": reasons, "harvest_filter": filt}
    finally:
        if cleanup:
            ref_path.unlink(missing_ok=True)

    if not reasons:
        entry_dir.mkdir(parents=True, exist_ok=True)
        # Persist the reference bytes (re-read from source if it was a path).
        if isinstance(reference_png, (bytes, bytearray)):
            (entry_dir / "reference.png").write_bytes(bytes(reference_png))
        else:
            (entry_dir / "reference.png").write_bytes(Path(reference_png).read_bytes())

        entry = CorpusEntry(
            slug=_slugify(slug),
            title=title,
            domain=domain,
            subject=subject,
            era=era,
            labels=dict(labels or {}),
            source_url=source_url,
            license=license,
            derived_acceptance=spec["acceptance"],
            derived=spec["derived"],
            harvested_filter=filt,
            status="harvested",
        )
        # Bind the entry to the (possibly temporary) corpus root so its file
        # paths resolve here, not the default CORPUS_ROOT.
        entry.entry_dir = entry_dir
        entry.manifest_path.write_text(json.dumps(entry.to_manifest(), indent=2) + "\n", encoding="utf-8")
        return {"ok": True, "entry": entry, "reasons": [], "harvest_filter": filt}

    return {"ok": False, "entry": None, "reasons": reasons}


def iter_corpus(corpus_root: Path = CORPUS_ROOT) -> list[CorpusEntry]:
    """Load every corpus entry that has a valid manifest.json."""
    root = Path(corpus_root)
    if not root.exists():
        return []
    out: list[CorpusEntry] = []
    for d in sorted(p for p in root.iterdir() if p.is_dir() and (p / "manifest.json").exists()):
        try:
            data = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
            out.append(CorpusEntry.from_manifest(data, entry_dir=d))
        except Exception:
            # A broken manifest must not crash the index; surface it separately.
            continue
    return out


def load_entry(slug: str, corpus_root: Path = CORPUS_ROOT) -> CorpusEntry:
    """Load one entry by slug (directory name or manifest slug)."""
    safe = _slugify(slug)
    path = Path(corpus_root) / safe / "manifest.json"
    if not path.exists():
        raise ValueError(f"unknown corpus slug {slug!r} (no manifest at {path})")
    data = json.loads(path.read_text(encoding="utf-8"))
    return CorpusEntry.from_manifest(data, entry_dir=path.parent)


def validate_entry(entry: CorpusEntry) -> dict[str, Any]:
    """Validate one entry's manifest + required assets (offline contract)."""
    errors: list[str] = []
    if not entry.manifest_path.exists():
        errors.append("missing manifest.json")
    if not entry.reference_png.exists() or entry.reference_png.stat().st_size == 0:
        errors.append("missing or empty reference.png")
    for key in _REQUIRED_PROVENANCE:
        if not getattr(entry, key):
            errors.append(f"missing provenance: {key}")
    if entry.slug != entry.dir.name:
        errors.append("slug must match entry directory name")
    if not isinstance(entry.derived_acceptance, list) or not entry.derived_acceptance:
        errors.append("derived_acceptance must be a non-empty list")
    else:
        for i, crit in enumerate(entry.derived_acceptance):
            if not isinstance(crit, dict) or "kind" not in crit:
                errors.append(f"derived_acceptance[{i}] missing 'kind'")
    return {"ok": not errors, "slug": entry.slug, "errors": errors}


def corpus_index(corpus_root: Path = CORPUS_ROOT) -> dict[str, Any]:
    """Index the corpus: one-line metadata per entry (mirrors recipes.recipe_index)."""
    entries = iter_corpus(corpus_root)
    return {
        "corpus_root": str(Path(corpus_root)),
        "count": len(entries),
        "entries": [
            {
                "slug": e.slug,
                "title": e.title,
                "domain": e.domain,
                "subject": e.subject,
                "era": e.era,
                "license": e.license,
                "source_url": e.source_url,
                "status": e.status,
                "reference_exists": e.reference_png.exists(),
                "acceptance_criteria": len(e.derived_acceptance),
                "converged": e.preview_png.exists(),
            }
            for e in entries
        ],
    }


# ---------------------------------------------------------------------------
# WP9 — retrieve the nearest existing grammar as a warm start for a new subject.
#
# Lightweight, offline, deterministic ranking over corpus entries. No embeddings,
# no network: matches are scored by keyword overlap (labels / domain / subject /
# title), color-family hue overlap (from the pixel-derived spec), and era. Returns
# ranked entries with their derived acceptance spec so a new render can be
# conditioned against the closest prior reference.
# ---------------------------------------------------------------------------
import math

# Weighting of the three match signals. Keyword hits dominate; hue overlap and
# era tie-break between otherwise-similar entries.
_W_KEYWORD = 3.0
_W_HUE = 1.5
_W_ERA = 1.0


def _hue_ring_dist(a: float, b: float) -> float:
    """Circular hue distance in degrees (0..180)."""
    d = abs(((a - b + 180.0) % 360.0) - 180.0)
    return d


def _entry_hues(entry: CorpusEntry) -> list[float]:
    out: list[float] = []
    for fam in entry.derived.get("color_families") or []:
        h = fam.get("target_hue")
        if isinstance(h, (int, float)):
            out.append(float(h))
    return out


def _keyword_tokens(entry: CorpusEntry) -> set[str]:
    toks: set[str] = set()
    for raw in (entry.subject, entry.title, entry.domain, entry.era):
        if raw:
            toks.update(t.strip().lower() for t in re.split(r"[\s_\-/]+", str(raw)) if t.strip())
    for k, v in entry.labels.items():
        toks.add(str(k).lower().strip())
        if isinstance(v, str):
            toks.update(t.strip().lower() for t in re.split(r"[\s_\-/]+", v) if t.strip())
        elif isinstance(v, (list, tuple)):
            for vi in v:
                toks.add(str(vi).lower().strip())
    return {t for t in toks if t}


def _score(entry: CorpusEntry, query: str) -> float:
    q_tokens = {t.strip().lower() for t in re.split(r"[\s_\-/]+", query) if t.strip()}
    if not q_tokens:
        return 0.0
    entry_tokens = _keyword_tokens(entry)
    overlap = q_tokens & entry_tokens
    keyword_score = _W_KEYWORD * (len(overlap) / max(1.0, len(q_tokens)))

    # Hue overlap: partial credit when the query names a color and the entry's
    # derived color families sit within tolerance of that hue.
    hue_score = 0.0
    entry_hues = _entry_hues(entry)
    if entry_hues:
        color_words = {
            "red": 0.0, "orange": 30.0, "yellow": 60.0, "green": 120.0,
            "cyan": 180.0, "blue": 240.0, "violet": 270.0, "magenta": 300.0,
            "purple": 280.0, "white": None, "black": None, "grey": None, "gray": None,
        }
        q_hues = [h for w, h in color_words.items() if w in q_tokens and h is not None]
        if q_hues:
            best = 0.0
            for qh in q_hues:
                for eh in entry_hues:
                    if _hue_ring_dist(qh, eh) <= 35.0:
                        best = max(best, 1.0 - _hue_ring_dist(qh, eh) / 35.0)
            hue_score = _W_HUE * best

    # Era only counts as a tie-breaker when the query explicitly names it.
    era_score = 0.0
    if entry.era and entry.era.strip().lower() in q_tokens:
        era_score = _W_ERA

    return keyword_score + hue_score + era_score


def find_grammar(query: str, *, top_k: int = 3,
                 domain: str | None = None,
                 only_converged: bool = False,
                 corpus_root: Path = CORPUS_ROOT) -> dict[str, Any]:
    """Retrieve the nearest existing grammar(s) for ``query`` as a warm start.

    Returns a ranked list of matches, each carrying enough to condition a new
    render: the derived acceptance spec, dominant colors, and provenance.
    """
    entries = iter_corpus(corpus_root)
    if domain:
        entries = [e for e in entries if e.domain == domain]
    if only_converged:
        entries = [e for e in entries if e.preview_png.exists()]

    scored = []
    for e in entries:
        s = _score(e, query)
        if s <= 0.0:
            continue
        scored.append((s, e))
    scored.sort(key=lambda se: se[0], reverse=True)

    matches = []
    for s, e in scored[:top_k]:
        matches.append({
            "slug": e.slug,
            "title": e.title,
            "domain": e.domain,
            "subject": e.subject,
            "era": e.era,
            "status": e.status,
            "converged": e.preview_png.exists(),
            "score": round(s, 3),
            "labels": e.labels,
            "derived_acceptance": e.derived_acceptance,
            "dominant_hues": e.derived.get("dominant_hues"),
            "color_families": e.derived.get("color_families"),
            "source_url": e.source_url,
            "license": e.license,
        })

    best = matches[0] if matches else None
    return {
        "query": query,
        "domain_filter": domain,
        "only_converged": only_converged,
        "corpus_count": len(iter_corpus(corpus_root)),
        "match_count": len(matches),
        "best": best,
        "matches": matches,
    }

