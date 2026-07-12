# Schwarz H — 3DXM Minimal-Surface Gallery (Surface #3)

A single green Schwarz H minimal surface — the hexagonal/3-fold-symmetry triply-periodic surface.

- **Equation:** `sin x cos y cos z + cos x sin y cos z + cos x cos y sin z = 0` (Wikipedia Schwarz H approximation; verified vs Wikipedia / Virtual Math Museum reference)
- **Form:** single manifold (one fundamental domain / unit cell), 1 connected component
- **Mesh:** 64,554 verts / 127,937 faces (`schwarz_h.obj`, plain single-material OBJ)
- **Material:** green `[0.20, 0.80, 0.40]` (one solid glossy colour)
- **Camera:** oblique — 60° rotation about X, 30° about Z (user-specified; TPMS read better from an oblique angle than head-on)
- **Render:** 1280×1280, ~5000 SPP, dark-studio lighting, auto-framed
- **Status:** ✅ approved (2026-07-13)

## Regenerate

```bash
# mesh (single manifold, correct H equation)
python3 scripts/gen_implicit_surface.py <out.obj> schwarz_h schwarz_h 132 2.5 1

# queue + render via OctaneX MCP one-shot bridge (oblique camera baked in)
python3 scripts/queue_implicit_surface.py <out.obj> schwarz_h
osascript scripts/octane_run_oneshot.applescript
# capture the 1280x1280 render box from the Octane window (display 2, upper-left)
```

## Notes (see docs/recipe-book.md)

- **Schwarz P vs H vs D are DIFFERENT surfaces.** `cos x + cos y + cos z = 0` is the **P** (primitive) surface; the **H** (hexagonal) surface is `sin x cos y cos z + cos x sin y cos z + cos x cos y sin z = 0`; the **D** (diamond) is `cos x cos y cos z − sin x sin y sin z = 0`. Don't conflate them — verify each equation against the source.
- Per-surface equation research is a prerequisite (SearXNG → Wikipedia/Wolfram verify).
- Single manifold only: mesh `[-π,π]³` (periods=1) and keep the largest connected component.
- Material colour is per-surface (green for Schwarz H) — never hardcode.
- **Oblique camera reads better for TPMS** — the queue driver now rotates 60° X / 30° Z by default.
- Capture the Octane viewport (1280×1280 box, upper-left of the window on display 2), not the full display.
