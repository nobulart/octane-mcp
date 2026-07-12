# Gyroid — 3DXM Minimal-Surface Gallery (Surface #1)

A single blue gyroid minimal surface — the first surface in the 3DXM gallery pass.

- **Equation:** `sin x cos y + sin y cos z + sin z cos x = 0` (verified against Wikipedia / Wolfram)
- **Form:** single manifold (one fundamental domain / unit cell), 1 connected component
- **Mesh:** 84,354 verts / 166,368 faces (`gyroid.obj`, plain single-material OBJ)
- **Material:** blue `[0.12, 0.45, 0.92]` (one solid glossy colour)
- **Render:** 1280×1280, ~5000 SPP, dark-studio lighting, auto-framed camera
- **Status:** ✅ approved (2026-07-13)

## Regenerate

```bash
# mesh (single manifold, correct equation)
python3 scripts/gen_implicit_surface.py <out.obj> gyroid gyroid 132 2.5 1

# queue + render via OctaneX MCP one-shot bridge
python3 scripts/queue_implicit_surface.py <out.obj> gyroid
osascript scripts/octane_run_oneshot.applescript
# capture the 1280x1280 render box from the Octane window (display 2, upper-left)
```

## Notes (see docs/recipe-book.md → "Surface #1 — Gyroid")

- Wait for the ~5000 SPP render to CONVERGE and the view to be oriented before judging — an intermediate/rotated low-SPP frame can look like a wrong surface (flower/starfish). The converged frame is the correct twisting labyrinth.
- Per-surface equation research is a prerequisite for every surface (SearXNG → Wikipedia/Wolfram verify).
- Single manifold only: mesh `[-π,π]³` (periods=1) and keep the largest connected component.
- Material colour is per-surface (blue for gyroid) — never hardcode.
- Capture the Octane viewport (1280×1280 box, upper-left of the window on display 2), not the full display.
