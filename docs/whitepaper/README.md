# OctaneX MCP Whitepaper

This directory contains a draft LaTeX/PDF whitepaper for the OctaneX MCP project.

- Source: `whitepaper.tex`
- Built PDF: `whitepaper.pdf`

Build from this directory:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error whitepaper.tex
latexmk -c whitepaper.tex
```

The LaTeX source references recipe preview images from `../../examples/recipes/...` rather than duplicating them into this folder.
