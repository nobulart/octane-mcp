# OctaneX MCP — Work In Progress

Living WIP board. Mirror of `docs/roadmap.md` §Status snapshot + §Development
brainstorm, kept as a fast-glance status doc. Last updated **2026-07-14** against
HEAD `4de64d1`.

## Current state (evidence, 2026-07-13)

| Area | State |
|------|-------|
| Repo | `main` = `4de64d1` (`fix(canvas): remove duplicate setViewMode def in app.js`), tracking `origin/main`; tree contains this sweep's two regression fixes (recipe-count drift + oneshot/persistent `handle_assign_material` divergent body). |
| Tests | **492 ran / 0 failures / 10 skipped** via `PYTHONPATH= uv run python -m unittest discover -s tests`. `compileall src` clean. Fixed two regressions: recipe contract total (31→32) and oneshot↔persistent `handle_assign_material` parity drift (now unified with `request_render_restart` + group-index suffix). |
| Doctor / bridge | `octanex-mcp doctor --json` returned `ok: true`. Octane X bridge status seen as `status=processed`, `render_stage=ready`, `samples_done=64`, `samples_target=64`, `last_event=save_preview preview saved .../renders/octane-preview.png`. Bridge module `hermes_bridge_oneshot_v2.lua` in one-shot mode. |
| Recipe library | **32 recipe dirs**. **31** pass offline contract; **1** fails (`earth-moon-space`). `native_octane_verified` counts pending live sweep. Offline contract: **31/32 OK**; `earth-moon-space` is the remaining contract failure. |
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

- Today — fix(test): recipe count drift 31→32 in dry_run parity check (`test_verify_recipes.py`).
- Today — fix(lua): oneshot↔persistent `handle_assign_material` parity (added `request_render_restart` + group-index suffix in oneshot).
- `4de64d1` — canvas: remove duplicate setViewMode def in app.js.
- `642fa21` — canvas: break app.js<->agent.js import cycle (setViewMode).
- `310b2e4` — canvas: split app.js into state.js + agent.js + app.js (shell).
- `f476ba2` — canvas: inline JS bundle into index.html (removes separate app.js fetch).
- `b04b495` — canvas: HTTP/1.1 + Connection: close to defeat fetch-hooking extension truncation.
- `4f9b9ab` — earth-hemisphere v4.1 smooth spheres + LLSVP/plume + off-axis Hermes Camera.
- `3db043e` — README points vase preview at native render.
- `6fcd43a` / `737e8e3` — earth-hemisphere v3 jello cutaway recipe + drain/queue recovery docs.
- `e4c8b3a` — shared-engine dispatch loop (gateway daemon + CLI + cron tick).
- `4ae0e65` — pointcloud merge pipeline and native vase render.
- `c325609` — shared-engine render lock + per-agent job queue.
