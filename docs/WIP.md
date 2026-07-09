# OctaneX MCP — Work In Progress

Living WIP board. Mirror of `docs/roadmap.md` §Status snapshot + §Development
brainstorm, kept as a fast-glance status doc. Last updated **2026-07-09**.

## Current state (evidence, 2026-07-09)

| Area | State |
|------|-------|
| Repo | `main` = `5d928ac`, clean, up to date with `origin/main` |
| Tests | 116 passed / 1 skipped (offline `python -m unittest discover -s tests`) — green |
| Octane X | running; persistent bridge; 135 processed / 0 failed; no wedge |
| Benchmarks | 18/18 native-Octane verified (Tiers 1–6) |
| Recipe library | 18 recipes; 2 verified, 16 target/reference only |
| Core mechanics | solid: bridge, schema, pixel-QA, render-review loop, scene v2, PBR mats/lights, bounds-camera, recipe registry |
| Unscaffolded | WP6 promoted tools, WP7 geo grammar, WP8 animation, `apps/octanex-canvas/` (not built), Studio multi-host, visual memory |

**Bottom line:** reliability + core mechanics are proven. The gap is
*surface area + closure* — high-level ergonomics (promoted tools, domain
grammars, canvas UI, autonomous loop) and recipe-library verification are
unfinished.

## Backlog (from brainstorm 2026-07-09)

Ranked by effort × strategic fit (reviewer's call — none committed yet):

1. **A — Recipe verification** (LOW effort / HIGH integrity): live-verify the 16
   unverified recipes, flip `native_octane_verified`, append `docs/recipe-book.md`.
   *First step:* a `verify-recipe-library` loop reusing `benchmarks/harness.run_task`
   over `examples/recipes/*`.
2. **B — Geo / terrain grammar** (HIGH strategic fit): GeoJSON / DEM /
   elevation-grid → combined OBJ with bounds + camera, behind `uv sync --extra geo`.
   *First step:* one `shapely`-backed GeoJSON→mesh op with graceful extra-missing
   failure (per WP7 dependency policy).
3. **C — Agentic Canvas app** (biggest unbuilt): Phase A slice — shell + full-bleed
   viewport + intent command bar + `OCTANEX_RENDER_HOST` Studio flag
   (from `docs/canvas-implementation-roadmap.md`).
4. **D — Autonomous loop**: bounded 2-iteration `octane_render_review_loop` over one
   recipe, driven end-to-end.
5. **E — Recipe promotion** (WP6): wrap the 3 strongest recipes as first-class tools
   (`octane_build_product_studio`, `octane_build_planet_scene`, `octane_visualize_network`).
6. **F — Animation DSL** (WP8): camera-orbit keyframe manifest + optional ffmpeg encode.
7. **G — Texture gen**: image-gen → `texture_path` / `normal_path` on materials,
   closing the "texture approximated with geometry" recipe pitfall.

## Recommended next move

**A → then B and/or C.** A is cheap and restores full honesty; B is the
highest-leverage fit for ECDO / TPW / impact-structure research; C is the biggest
step toward the shared visual communication medium. A + B are Python-only and
offline-testable; C is a separate Swift workstream.

## In progress / this session

_No committed build yet — status review + brainstorm only._

## Done recently

- `5d928ac` fix(bridge): render-restart retry loop unblocks Tier 3–6 renders; 18/18 benchmarks live.
- `760e34b` docs(canvas): ticket-ready implementation roadmap + proposal cross-link.
- `fc566cf` feat(benchmarks): progressive visualisation suite + Tier 1–2 live verification.
