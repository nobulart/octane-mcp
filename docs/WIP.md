# OctaneX MCP — Work In Progress

Living WIP board. Mirror of `docs/roadmap.md` §Status snapshot + §Development
brainstorm, kept as a fast-glance status doc. Last updated **2026-07-12** against
HEAD `296e7f9`.

## Current state (evidence, 2026-07-12)

| Area | State |
|------|-------|
| Repo | `main` = `296e7f9` (`feat(recipes): add bowl-of-fruit still-life recipe`), tracking `origin/main`; tree clean before this docs review. |
| Tests | **357 ran / 0 failures / 3 skipped** via `PYTHONPATH= uv run python -m unittest discover -s tests`. Benchmark subset: **14 ran / 0 failures / 1 skipped** via `tests.test_benchmarks -v`. `compileall src` clean. |
| Doctor / bridge | `octanex-mcp doctor --json` returned `ok: true`. Octane X running (`pid 78834`); persistent bridge `status=processed`, `render_stage=ready`, `processed_count=1`, `failed_count=0`, last event `set_camera camera connected`. |
| Recipe library | **26 recipe dirs** via `_recipe_dirs` (post-`ancient-temple` merge). **24** declare `native_octane_verified=true`; **25** have `octane-preview.png`; **1** lacks a preview (`earth-moon-space`). A2 closed 2026-07-12: `birthday-cake` promoted (pixel-QA `filter_reference.ok` + `evaluate_acceptance.passed` + vision confirm → `native_octane_verified=true`); `helicoid-spiral` preview REJECTED by pixel-QA (blank flat field, no visible subject) → stays `false`, status corrected to `native_render_rejected_blank`; `earth-moon-space` stays `false` (no preview PNG — live-render gap). Honest remaining flag gap: **1** (`earth-moon-space`). |
| Core mechanics | Broad and green: schema/dispatch guards, command queue, pixel QA, live scene harvest, scene-plan/live-graph sanity checks, recipe registry, WP6 promoted tools, WP7 geo tool, WP8 animation tool, WP9 corpus/retrieval/iteration, `swap_geometry`, API-corpus/capability/probe tools. |
| Unscaffolded / open | Recipe verification reconciliation, WP12 single-source Lua handler generation, WP13 material/light compatibility registry, live WP7 geo exercise, live WP8 orbit clip with subject + optional ffmpeg encode, Agentic Canvas Phase B status/operator surface, multi-host Studio, visual memory. |

**Bottom line:** the bridge is live and the offline suite is solid. The active risk is no longer "does the queue work?"; it is stale verification metadata, duplicated Lua handler knowledge, and not yet making bridge capabilities/status visible enough for smaller agents to operate safely.

## Ranked backlog / next steps

1. ~~A2 — Recipe verification reconciliation~~ **DONE 2026-07-12** (LOW effort / HIGH integrity): `birthday-cake` promoted to `native_octane_verified=true` (pixel-QA + vision confirm); `helicoid-spiral` preview rejected by pixel-QA (blank flat field) → stays false with corrected `native_render_rejected_blank` status; `earth-moon-space` stays false (no preview PNG — needs fresh live render). Recipe-book + WIP updated. *Remaining live gap:* render `earth-moon-space` natively and verify before flipping.
2. **I — Capability-driven bridge hardening** (MEDIUM effort / VERY HIGH fit): finish WP10–WP13. `octane_capabilities`/`octane_probe_types` are exposed; next is WP12 single-source Lua handler generation and WP13 registry-backed material/light behavior reporting. *First step:* make handler edits single-source, then prove one material/light command path against the registry.
3. **J — Pre-render sanity adoption** (LOW effort / HIGH reliability): use `octane_check_scene_plan` and `octane_scene_sanity` as mandatory guards before recipe/live drains. *First step:* add a verifier path that writes sanity reports next to render outputs.
4. **B — Geo / terrain grammar live path** (HIGH research fit): `octane_visualize_geojson` ships with graceful `geo` extra handling. *Remaining:* exercise the shapely-backed path live under `uv sync --extra geo` and record the output/QA.
5. **F2-live — Animation live drain** (HIGH communication fit): `octane_build_animation` queues per-frame camera motion. *Remaining:* import a real subject, render a short orbit clip, verify frames differ, and optionally encode with ffmpeg.
6. **K — Canvas/status operator surface** (MEDIUM effort / HIGH communication fit): expose bridge readiness, capabilities, queue state, and recipe index in Agentic Canvas. *First step:* status pill + capability panel backed by `/mcp/call`.
7. **G — Texture / material generation**: image-gen → `texture_path` / `normal_path` material payloads, closing the "texture approximated with geometry" recipe pitfall.

## Recommended next move

Do **A2 first** to keep the recipe library honest, then **I** because capability-backed dispatch prevents whole classes of future bridge regressions. Run **J** alongside every live render task. Use **K** as the next user-facing integration slice once the status/capability API is stable.

## Done recently

- `296e7f9` — bowl-of-fruit still-life recipe with native preview asset.
- `617014e` — pre-render node-graph sanity gate: live scene harvest analysis, offline manifest/framing checks, `octane_scene_sanity`, `octane_check_scene_plan`, 22 tests.
- `be8b0eb` / `0a4d1ae` / `9a29048` — birthday-cake recipe and realism lessons, including persistent-bridge silent-exit and single-source queue-pipeline notes.
- `6590d5d` / `35f64a9` / `f0cc70d` — API corpus/capability/probe surface and dark-studio/graph-owner bridge fixes.
