# OctaneX MCP Whitepaper

This directory contains the LaTeX source and checked-in PDF for the OctaneX MCP
whitepaper. It documents the current two-tier collaboration model: an editable
Agentic Canvas live scene plus an explicit, verified Octane Final render path.
It also records the stewardship boundary between the protected Canvas product
surface and the project's CC BY-SA knowledge commons.

- Source: `whitepaper.tex`
- Built PDF: `whitepaper.pdf`

Build from this directory:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error whitepaper.tex
latexmk -c whitepaper.tex
```

The LaTeX source references recipe preview images from `../../examples/recipes/...` rather than duplicating them into this folder.
