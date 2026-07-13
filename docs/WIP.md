# OctaneX MCP — Work In Progress

Living WIP board. Mirror of `docs/roadmap.md` §Status snapshot + §Development
brainstorm, kept as a fast-glance status doc. Last updated **2026-07-13** against
HEAD `4f9b9ab`.

## Current state (evidence, 2026-07-13)

| Area | State |
|------|-------|
| Repo | `main` = `4f9b9ab` (`feat(earth-hemisphere): v4.1 smooth spheres + LLSVP/plume + off-axis Hermes Camera`), tracking `origin/main`; tree contains this sweep's code/docs fixes plus new `docs/3DXM/` math-grammar reference material. |
| Tests | **408 ran / 0 failures / 10 skipped** via `PYTHONPATH= uv run python -m unittest discover -s tests`. Benchmark subset: **14 ran / 0 failures / 1 skipped**. `compileall src` clean. This sweep fixed the Pillow-missing source check, stale recipe-contract counts, and one-shot/persistent `wait_for_render_ready` parity drift. |
| Doctor / bridge | `octanex-mcp doctor --json` returned `ok: true`. Octane X bridge status seen as `status=processed`, `render_stage=ready`, `samples_done=800`, `samples_target=800`, `last_event=save_preview preview saved .../renders/octane-preview.png`. Stdio MCP boot probe returned **64 tools** and found `octane_find_grammar`. |
| Recipe library | **30 recipe dirs** via `_recipe_dirs`. **25** declare `native_octane_verified=true`; **29** carry `octane-preview.png`. **5** currently have `native_octane_verified=false`: `earth-moon-space`, `headphones-studio`, `helicoid-spiral`, `photoreal-vase-studio`, `wristwatch`. Only `earth-moon-space` is missing a preview PNG. Offline recipe contract is **29/30 OK**; `earth-moon-space` is the remaining contract failure. |
| Core mechanics | Broad coverage across schema/dispatch guards, command queue, pixel QA, live scene harvest, scene-plan/live-graph sanity checks, recipe registry, WP6 promoted tools, WP7 geo tool, WP8 animation tool, WP9 corpus/retrieval/iteration, `swap_geometry`, API-corpus/capability/probe tools. This sweep also removes a library-layering trap by lazy-importing `benchmarks.spec` inside `iteration.py` instead of importing repo-root benchmark code at package import time. |
| Documentation corpus | Added/curated `docs/3DXM/` as a 3D-XplorMath / Collected ATOs math-surface grammar reference for the gallery pipeline. Existing `docs/recipe-gap-fill.md` remains the proposal for filling blocked 3DXM surfaces with parametric/Weierstrass meshers. |
| Unscaffolded / open | WP12 single-source Lua handler generation, WP13 material/light compatibility registry, live WP7 geo exercise, live WP8 orbit clip with subject + optional ffmpeg encode, Agentic Canvas Phase B status/operator surface, multi-host Studio, visual memory, WP15 renderer-agnostic backend abstraction, and a 3DXM parametric/Weierstrass mesher for non-implicit gallery surfaces. |

**Bottom line:** the repo has grown into a working visual workbench with 30 recipe dirs and a live bridge, but the current closure risk is documentation/test drift after rapid recipe additions. This sweep consolidates that drift and keeps the remaining gaps explicit instead of silently promoting unverified renders.

## Ranked backlog / next steps

1. **I — Capability-driven bridge hardening** (MEDIUM effort / VERY HIGH fit): finish WP12 single-source Lua handler generation and WP13 registry-backed material/light behavior reporting. *First step:* make handler edits single-source, then prove one material/light command path against the registry.
2. **J — Pre-render sanity adoption** (LOW effort / HIGH reliability): use `octane_check_scene_plan` and `octane_scene_sanity` as mandatory guards before recipe/live drains. *First step:* add a verifier path that writes sanity reports next to render outputs.
3. **M — 3DXM parametric/Weierstrass mesher** (MEDIUM-HIGH effort / HIGH research fit): turn `docs/3DXM/` and `docs/recipe-gap-fill.md` into reusable mesh generators for non-implicit math-museum surfaces. *First step:* implement one parametric surface recipe from `docs/3DXM/minimal-surfaces.md` and gate it with pixel QA + local vision.
4. **B — Geo / terrain grammar live path** (HIGH research fit): `octane_visualize_geojson` ships with graceful `geo` extra handling. *Remaining:* exercise the shapely-backed path live under `uv sync --extra geo` and record the output/QA.
5. **F2-live — Animation live drain** (HIGH communication fit): `octane_build_animation` queues per-frame camera motion. *Remaining:* import a real subject, render a short orbit clip, verify frames differ, and optionally encode with ffmpeg.
6. **K — Canvas/status operator surface** (MEDIUM effort / HIGH communication fit): expose bridge readiness, capabilities, queue state, and recipe index in Agentic Canvas. *First step:* status pill + capability panel backed by `/mcp/call`.
7. **G — Texture / material generation**: image-gen → `texture_path` / `normal_path` material payloads, closing the "texture approximated with geometry" recipe pitfall.
8. **L — Renderer-agnostic backend abstraction** (MEDIUM effort / HIGH strategic fit): decouple the command DSL from Octane X so it becomes one of N render backends; research in `docs/visualization-backends-research.md`. *First step:* extract a `Backend` interface (OctaneBackend first), then ship `WebGLBackend` (three.js in Agentic Canvas) as the Phase-1 realtime + shareable win.

## Recommended next move

Do **I** first because handler-generation and registry-backed reporting prevent whole classes of future bridge regressions. Run **J** alongside every live render task. Start **M** as the math-gallery unblocker once one clean implicit recipe pass has been reviewed, then use **K/L** for the user-facing multi-backend surface.

## PDF Consolidation (docs/3DXM/ — 3DXM Virtual Math Museum)

**Completed 2026-07-13** — Harvested the entire virtualmathmuseum.org geometry museum for the
OctaneX MCP grammar pipeline. 22 PDFs downloaded; 13 redundant PDFs moved to staging, 9 kept
as the core collection. Collected_ATOs.pdf (7 MB) serves as the master index for all exhibits.

| Decision | PDFs | Action |
|---|---|---|
| **Keep (9)** | Collected_ATOs, Surfaces, Space_Curves, Plane_Curves, Conformal_Maps, Fractals, Platonics, Helicoid-Catenoid, Enneper_Surface | Core geometry for OctaneX MCP — unique equation sets, distinct math, direct grammar mapping |
| **Stage (13)** | CatalanHennebergScherk, ConstKSurfofRev, Costa, Fractals_and_Chaos, Helix, Koch_Snowflake, Mandelbrot_Set, MonkeyTorusCyclide, RuledSurfaces, Saddle_Tower, Scherk_w_Handle, Schwarz_H_Family, Torus_Knot | Content covered by Collected_ATOS, Surfaces, or Fractals (verified via MinerU pdftotext extractions) |

MinerU text extractions saved at `docs/3DXM/mineru_text/*.txt` (total 610 KB) for full-text search.

---

## Done recently

- `4f9b9ab` — earth-hemisphere v4.1 smooth spheres + LLSVP/plume + off-axis Hermes Camera.
- `3db043e` — README points vase preview at native render.
- `6fcd43a` / `737e8e3` — earth-hemisphere v3 jello cutaway recipe + drain/queue recovery docs.
- `e4c8b3a` — shared-engine dispatch loop (gateway daemon + CLI + cron tick).
- `4ae0e65` — pointcloud merge pipeline and native vase render.
- `c325609` — shared-engine render lock + per-agent job queue.
