# 3DXM Virtual Math Museum — OctaneX MCP Grammar Knowledge Base

> Research notes harvested from the 3D-XplorMath Virtual Math Museum
> (`virtualmathmuseum.org`) and Collected ATO-style PDF/text extractions. This
> directory is a compact source pack for turning math-museum surfaces into
> OctaneX MCP recipes and mesh generators.

## Overview

| Category | Geometry Types | Approx. Exhibits | OctaneX use |
|---|---|---:|---|
| Minimal surfaces | Catenoid, Helicoid, Scherk, Enneper, Costa, Gyroid, Schwarz PD/H | 45+ | implicit/parametric meshes, TPMS galleries, morph studies |
| Surfaces of revolution | Torus, sphere, Kuen, Dini, unduloid, cyclide | 20+ | sweep/revolve generators and toroidal grammars |
| Space curves | Helix, torus knots, Lissajous 3D, Viviani | 30+ | tube paths, orbit guides, curve annotations |
| Plane curves | Conics, cycloids, spirals, lemniscates | 30+ | 2D-to-3D curve lifts, pattern/glyph grammars |
| Fractals | Mandelbrot, Julia, Koch, Sierpinski, Hilbert | 15+ | iterative heightfields, recursive mesh/detail tests |
| Polyhedra | Platonic, Archimedean, Catalan | 12+ | symmetry tests and discrete mesh recipes |
| Conformal maps | Möbius, elliptic, transcendental | 15+ | texture/domain warp and complex-analysis diagrams |
| Implicit surfaces | Cayley, Clebsch, Kummer, Barth, Bretzel | 12+ | algebraic level-set recipes |

## Directory layout

Current committed subset:

```text
docs/3DXM/
├── README.md
├── minimal-surfaces.md        # Core: parametric equations + OctaneX mappings
├── surfaces-geometry.md       # Revolution, toroidal, quadratic surfaces
└── mineru_text/               # PDF/text extraction notes used as raw reference
    ├── Collected_ATOs.txt
    ├── Surfaces.txt
    ├── Space_Curves.txt
    ├── Plane_Curves.txt
    ├── Conformal_Maps.txt
    ├── Platonics.txt
    ├── Mandelbrot_Set.txt
    ├── Helicoid-Catenoid.txt
    ├── Enneper_Surface.txt
    ├── Costa.txt
    └── ... additional extracted exhibit notes
```

Planned/derived files, when promoted from notes to structured references:

```text
space-curves.md
plane-curves.md
fractals-iteration.md
conformal-maps.md
polyhedra-symmetry.md
implicit-surfaces.md
grammar-recommendations.md
equations/*.md
```

## Quick reference: high-priority geometries for OctaneX MCP

These are selected for maximum impact on the OctaneX grammar pipeline.

### Tier 1 — Direct surface construction

| Geometry | Type | OctaneX use | Source |
|---|---|---|---|
| Torus | Surface of revolution | primary sweep/revolve grammar; torus-knot carrier | `surfaces-geometry.md` |
| Möbius strip | twist surface | cross-cap / topology morphing | `minimal-surfaces.md` / `mineru_text/` |
| Cyclide | inversion of torus | algebraic/tube-sphere construction | `surfaces-geometry.md` |
| Boy's surface | non-orientable immersion | 3-fold symmetric immersion benchmark | `mineru_text/` |
| Gyroid | TPMS | material-interface and periodic-cell gallery | `minimal-surfaces.md` |

### Tier 2 — Tube / space-curve enhancement

| Geometry | Type | OctaneX use | Source |
|---|---|---|---|
| Helix | constant-curvature curve | tube generation and screw-motion guides | `mineru_text/Space_Curves.txt` |
| Torus knot | `(p,q)` curve on torus | parametric tube path / knot gallery | `mineru_text/Torus_Knot.txt` |
| Viviani curve | sphere-surface intersection | lens/curve-on-surface grammar | `mineru_text/Space_Curves.txt` |
| Lissajous 3D | frequency-ratio curve | parametric curve surface / animation path | `mineru_text/Space_Curves.txt` |

### Tier 3 — Algebraic / symbolic surface building

| Geometry | Type | OctaneX use | Source |
|---|---|---|---|
| Ellipsoid | triaxial quadric | basis surface and bounds/camera test | `surfaces-geometry.md` |
| Paraboloid | bowl/saddle | implicit + parametric primitive | `surfaces-geometry.md` |
| Hyperboloid | one/two sheet | ruled-surface construction | `surfaces-geometry.md` |
| Conoid | ruled surface | sweep generation / line-family test | `surfaces-geometry.md` |

### Tier 4 — Fractal / iterative surface generation

| Geometry | Type | OctaneX use | Source |
|---|---|---|---|
| Mandelbrot set | complex iteration | fractal height map / domain coloring | `mineru_text/Mandelbrot_Set.txt` |
| Julia set | complex iteration boundary | fractal boundary mesh | `mineru_text/Fractals.txt` |
| Koch snowflake | recursive subdivision | edge geometry and recursive generator test | `mineru_text/Koch_Snowflake.txt` |
| Sierpinski triangle | fractal subdivision | recursive surface patch pattern | `mineru_text/Fractals_and_Chaos.txt` |

## How to use this pack

1. Treat these notes as **source material**, not verified recipe metadata.
2. Before rendering a surface, confirm the exact equation from a primary/source page
   or the extracted PDF text.
3. Prefer single-manifold/unit-cell outputs for gallery recipes; avoid rendering
   large multi-period lattices unless the recipe explicitly asks for them.
4. Promote a geometry into `examples/recipes/` only after pixel QA and local vision
   inspection of a real native Octane preview.
5. If the surface is not directly meshable from an implicit equation, record it as
   blocked and add it to the parametric/Weierstrass mesher backlog rather than
   faking an unrelated shape.

## Sources

- Primary website: <https://virtualmathmuseum.org>
- Collected ATOs: <https://3d-xplormath.org/Downloads/Collected_Atos.pdf>
- Local extraction notes: `docs/3DXM/mineru_text/`
- Existing project synthesis: `docs/recipe-book.md` §3DXM gallery pass and
  `docs/recipe-gap-fill.md`
