# WP9 reference corpus

This directory holds **harvested reference imagery** for the Reference-Anchored
Grammar Synthesis (RAGS) work package. Each entry is a labeled, licensed
reference image that *anchors* a visual-grammar entry: it is processed
pixel-only (no vision model) into a self-describing acceptance spec.

## Layout (per entry: `corpus/<slug>/`)

| Path             | Purpose                                                        |
|------------------|----------------------------------------------------------------|
| `reference.png`  | the (pixel-filtered) harvested reference image                 |
| `manifest.json`  | provenance + domain/era tags + derived acceptance spec         |
| `grammar_spec.yaml` | parametric OBJ generator (WP9 task 7; written later)       |
| `iterations/`    | per-iteration candidate.png + report (WP9 task 4)             |
| `octane-preview.png` | native converged render (WP9 task 4)                      |

The `manifest.json` carries:

```json
{
  "manifest_version": 1,
  "slug": "red-sphere",
  "title": "Red Sphere",
  "domain": "photoreal",
  "subject": "sphere",
  "era": null,
  "labels": {"material": "metal", "categories": ["Mock"]},
  "source_url": "https://commons.wikimedia.org/...",
  "license": "CC-BY-SA-4.0",
  "status": "harvested",
  "harvest_filter": {"ok": true, "reasons": [], "stats": {}},
  "derived": {"hue_families": [...], "shape_rows": 12, "...": "..."},
  "derived_acceptance": [
    {"kind": "non_empty", ...},
    {"kind": "review_ok", "fail_on": [...]},
    {"kind": "color_family", "target": [1.0, 0.0, 0.0], "hue_tol": 35, "min_fraction": 0.05},
    {"kind": "bright_fraction", "min_near_white": 1.0, "max_near_white": 95.0},
    {"kind": "shape_profile", "min_rows": 6}
  ]
}
```

## Provenance is mandatory

Every entry records `source_url` + `license` in `manifest.json`. A reference
without a resolvable license is **rejected** by `filter_reference` and never
enters the corpus. This is the "licensed, labeled, provenance" requirement of
WP9 — nothing synthetic or unsourced is promoted into a benchmark.

## How entries are created

```bash
# offline / deterministic (mock fetcher — writes to a temp corpus)
PYTHONPATH= uv run python scripts/harvest_commons.py --dry-run "red sphere"

# live harvest from Wikimedia Commons (respects rate limits)
PYTHONPATH= uv run python scripts/harvest_commons.py "Mars" "Saturn" "terracotta vase" --domain photoreal
```

Programmatic registration (pure-Python, no network):

```python
from octanex_mcp.corpus import register_reference, load_entry, validate_entry

res = register_reference(
    slug="red-sphere", title="Red Sphere",
    source_url="https://commons.wikimedia.org/...", license="CC-BY-SA-4.0",
    reference_png=image_bytes, domain="photoreal", subject="sphere",
)
assert res["ok"], res["reasons"]
```

## Acceptance criteria (WP9)

- A harvested reference yields a self-describing acceptance spec with **no
  hand-authoring and no vision model** (`reference_to_acceptance`).
- Corpus entries carry provenance (source URL, license, Wikidata/Commons labels).
- The harvest filter rejects low-contrast / blown-out / watermarked / busy /
  tiny references via pixel stats.
- `reference_to_acceptance()` output is consumed by `evaluate_acceptance()`
  and covered by tests.

## Git hygiene

The `corpus/*/` dynamic directories are gitignored (only this README is
tracked). Harvested entries are local artifacts; they become benchmarks via
WP9 task 7, which registers converged entries into `benchmarks/spec.py`.
