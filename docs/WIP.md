1|# OctaneX MCP — Work In Progress
2|
3|Living WIP board. Mirror of `docs/roadmap.md` §Status snapshot + §Development
4|brainstorm, kept as a fast-glance status doc. Last updated **2026-07-13** against
5|HEAD `196185c`.
6|
7|## Current state (evidence, 2026-07-13)
8|
9|| Area | State |
10||------|-------|
11|| Repo | `main` = `196185c` (`feat(geo): EGM2008 geoid heightfield recipe + gen_geo_displacement/queue_geo_surface tooling`), tracking `origin/main`; **12 commits ahead** of the docs' claimed `296e7f9`. Tree: clean (adding `docs/visualization-backends-research.md` as roadmap WP15 / backend-research doc). |
12|| Tests | **381 ran / 1 failure / 3 skipped** via `PYTHONPATH= uv run python -m unittest discover -s tests`. Benchmark subset: **14 ran / 0 failures / 1 skipped** (via `tests.test_benchmarks -v`). `compileall src` clean. The 1 failure is the **pre-existing** `test_lua_bridge_parity::test_scene_handler_semantics_match_between_one_shot_and_persistent_bridges` (`wait_for_render_ready` body drift between one-shot and persistent templates). **+24 new tests** (WP7 pre-render sanity adoption). |
13|| Doctor / bridge | `octanex-mcp doctor --json` returned `ok: true`. Octane X running; persistent bridge `status=processed`, `render_stage=ready`, `samples_done=1200`, `samples_target=1200`, `last_preview_path=.../renders/egm2008_octane-preview.png`, `last_event=save_preview preview saved`. |
14|| Recipe library | **27 recipe dirs** via `_recipe_dirs`. **26** declare `native_octane_verified=true`; **25** carry `octane-preview.png`. **1** unverified: `earth-moon-space` (no preview PNG — live render gap, not metadata). `helicoid-spiral` stays `false` (REJECTED by pixel-QA, blank flat field; has `.png` file but the flag remains false). |
15|| Core mechanics | Broad and green: schema/dispatch guards, command queue, pixel QA, live scene harvest, scene-plan/live-graph sanity checks (24 new tests for the report dataclasses, engine checks, manifest/graph analysis, and round-trips), recipe registry, WP6 promoted tools, WP7 geo tool, WP8 animation tool, WP9 corpus/retrieval/iteration, `swap_geometry`, API-corpus/capability/probe tools. |
16|| Unscaffolded / open | WP12 single-source Lua handler generation, WP13 material/light compatibility registry, live WP7 geo exercise, live WP8 orbit clip with subject + optional ffmpeg encode, Agentic Canvas Phase B status/operator surface, multi-host Studio, visual memory, **WP15 renderer-agnostic backend abstraction**. |
17|
18|**Bottom line:** the bridge is live and the offline suite is solid (381 green, 1 pre-existing failure). The docs' status snapshot has drifted 12 commits behind HEAD; fresh evidence is refreshed below. The active risk is no longer "does the queue work?"; it is WP12 single-source Lua handler generation and WP13 registry-backed material/light reporting closing the bridge-hardening loop.

## Ranked backlog / next steps

1. ~~A2 — Recipe verification reconciliation~~ **DONE 2026-07-12** (LOW effort / HIGH integrity): `birthday-cake` promoted to `native_octane_verified=true` (pixel-QA + vision confirm); `helicoid-spiral` preview rejected by pixel-QA (blank flat field) → stays false with corrected `native_render_rejected_blank` status; `earth-moon-space` stays false (no preview PNG — needs fresh live render). Recipe-book + WIP updated. *Remaining live gap:* render `earth-moon-space` natively and verify before flipping.
2. **I — Capability-driven bridge hardening** (MEDIUM effort / VERY HIGH fit): finish WP10–WP13. `octane_capabilities`/`octane_probe_types` are exposed; next is WP12 single-source Lua handler generation and WP13 registry-backed material/light behavior reporting. *First step:* make handler edits single-source, then prove one material/light command path against the registry.
3. **J — Pre-render sanity adoption** (LOW effort / HIGH reliability): use `octane_check_scene_plan` and `octane_scene_sanity` as mandatory guards before recipe/live drains. *First step:* add a verifier path that writes sanity reports next to render outputs.
4. **B — Geo / terrain grammar live path** (HIGH research fit): `octane_visualize_geojson` ships with graceful `geo` extra handling. *Remaining:* exercise the shapely-backed path live under `uv sync --extra geo` and record the output/QA.
5. **F2-live — Animation live drain** (HIGH communication fit): `octane_build_animation` queues per-frame camera motion. *Remaining:* import a real subject, render a short orbit clip, verify frames differ, and optionally encode with ffmpeg.
6. **K — Canvas/status operator surface** (MEDIUM effort / HIGH communication fit): expose bridge readiness, capabilities, queue state, and recipe index in Agentic Canvas. *First step:* status pill + capability panel backed by `/mcp/call`.
7. **G — Texture / material generation**: image-gen → `texture_path` / `normal_path` material payloads, closing the "texture approximated with geometry" recipe pitfall.
8. **L — Renderer-agnostic backend abstraction** (MEDIUM effort / HIGH strategic fit): decouple the command DSL from Octane X so it becomes one of N render backends; research in `docs/visualization-backends-research.md`. *First step:* extract a `Backend` interface (OctaneBackend first), then ship `WebGLBackend` (three.js in Agentic Canvas) as the Phase-1 realtime + shareable win.

## Recommended next move

Do **A2 first** to keep the recipe library honest, then **I** because capability-backed dispatch prevents whole classes of future bridge regressions. Run **J** alongside every live render task. Use **K** as the next user-facing integration slice once the status/capability API is stable. Add **L** (renderer-agnostic backend) to the architecture backlog once K's surface is stable.

## Done recently

- `d7a2c1f` — pre-render sanity adoption: tests for `SanityReport`/`SanityIssue` dataclasses, `analyze_scene_plan`/graph engine checks, manifest graph analysis, and JSON round-trips (24 tests).
- `196185c` — EGM2008 geoid heightfield recipe + `gen_geo_displacement`/`queue_geo_surface` tooling.
- `80f3fdf` — gallery: embed preview images in all 7 TPMS READMEs + recipe-book entries; reconcile index.
- `296e7f9` — bowl-of-fruit still-life recipe with native preview asset.
- `617014e` — pre-render node-graph sanity gate: live scene harvest analysis, offline manifest/framing checks, `octane_scene_sanity`, `octane_check_scene_plan`, 22 tests.
- `be8b0eb` / `0a4d1ae` / `9a29048` — birthday-cake recipe and realism lessons, including persistent-bridge silent-exit and single-source queue-pipeline notes.
- `6590d5d` / `35f64a9` / `f0cc70d` — API corpus/capability/probe surface and dark-studio/graph-owner bridge fixes.
