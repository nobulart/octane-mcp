# OctaneRender® Standalone — Offline Manual Mirror

A local, greppable Markdown copy of the OT oy **Standalone Edition** user manual,
mirrored into this repo for offline reference and agent research.

## Provenance

- **Source:** `https://docs.otoy.com/standaloneSE/` (HelpNDoc build, `lastmod` 2025-06-02)
- **Sitemap:** `https://docs.otoy.com/standaloneSE/sitemap.xml` (431 HTML pages)
- **Copyright:** © OTOY Inc. 2014–2025. All rights reserved. This is a local
  research/reference copy only.
- **Authorship (per the manual cover):** Curvin Huber, with contributions from the
  OTOY Development and Support Teams; edited by Curvin Huber and Jay Roth.

## What's in here

- `index.md` — reading-order table of contents (page number → title → file link)
  for all **430** pages (the sitemap's 431st entry — `OCTANE STANDALONE.html` —
  is a duplicate alias of *Installation* and was omitted).
- `<PageName>.md` — one cleaned Markdown file per manual page. HelpNDoc nav/sidebar/
  search chrome is stripped; only the article body (`.main-content`) is converted.
  Internal `.html` cross-links are rewritten to `.md` so the mirror navigates offline.
- `<PageName>.json` — tiny sidecar per page: `{title, h1, source}` (used to build
  the index; safe to ignore or delete).
- `images/` — screenshots and figures referenced by the pages, downloaded alongside
  and rewritten to relative `images/...` paths.

## How it was built

1. Parsed `sitemap.xml` → 431 page URLs.
2. For each page: fetch → extract `.main-content` → strip presentation attributes →
   download images locally → rewrite links → `pandoc -f html -t markdown`
   → cleanup pass (drop HelpNDoc `.rvts*` spans and layout wrappers).
3. Generated `index.md` from each page's H1 title in sitemap order.

Reproduce with:

```bash
# urls.txt = one absolute page URL per line (from sitemap.xml)
python3 build_octane_manual.py <urls.txt> <out_dir>
```

## Notes / limitations

- Page **styling** (exact fonts, colors, multi-column layouts) is not preserved —
  this is a semantic text mirror, not a pixel-perfect render.
- A handful of sitemap entries may 404 (the sitemap can list pages that were removed
  upstream); the builder logs each fetch failure and skips them. Re-run after the
  manual is updated to refresh.
- This is a **reference snapshot** dated 2025-06-02. For the authoritative/current
  manual, use the live OT oy docs site.
- Nothing here should be treated as a license grant beyond personal/research use.
