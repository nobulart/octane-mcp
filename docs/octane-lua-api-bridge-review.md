# Octane X Lua API bridge review

Recorded: 2026-07-12T09:30:32Z
Scope: public Octane/Octane X Lua/API documentation, public Lua examples, and the current `octanex-mcp` bridge architecture.

## Executive summary

The current design — **Hermes/Python emits an allowlisted JSON command DSL, Octane X executes it through Lua inside the GUI** — is still the right primary bridge for this project. It matches the official Octane scripting model: the Lua API is explicitly intended to automate workflows, create nodes, render them, and manipulate root graphs from scripts run through Octane's Script menu/API browser. It also respects the project's safety requirement: no arbitrary Lua execution from agents.

However, the project would benefit substantially from a **comprehensive, versioned Octane Lua API inclusion layer**. The weak point is not the high-level bridge idea; it is that our Lua implementation is currently based on empirical pin/name probing, copied handler bodies, and scattered lessons. A better next architecture is:

1. **Keep the JSON queue + allowlisted command DSL.**
2. **Generate and commit a local Octane API corpus from the running Octane X build** using `octane.help` / API browser export scripts.
3. **Build a Python-side capability registry from that corpus**: available modules, node types, pin constants, attributes, render functions, image-save signatures, supported material/light families.
4. **Generate Lua compatibility shims and tests from the registry**, rather than growing more one-off fallback lists in bridge handlers.
5. **Move the bridge toward a single shared Lua runtime/handler source**, with entrypoint wrappers generated for one-shot and persistent modes.
6. Treat a native C++ Octane module as a **later fast/reliable transport option**, not as the next default replacement. It can remove AppleScript/TCC friction, but it has higher crash risk, SDK/ABI burden, startup-only loading, and currently exists as a scaffold rather than a working dispatcher.

In short: **do not replace the bridge yet; formalize it around Octane's Lua API.**

---

## Sources reviewed

### Official/public documentation

| Source | Relevant facts |
| --- | --- |
| OTOY Standalone docs: `Lua Scripting In OctaneRender` (`https://docs.otoy.com/StandaloneH_STA/StandaloneSTA/LUAScriptinginOctane.htm`) | Lua scripting is for workflow automation; scripts can create nodes and render them; Octane exposes one global table named `octane`; modules such as `octane.gui` live under it; constants are available both under module-specific constant tables and directly under `octane`; the API browser is the detailed reference. |
| OTOY Standalone docs: `The Script Menu` (`https://docs.otoy.com/StandaloneH_DEV/StandaloneDEV/TheScriptMenuandLua.htm`) | Scripts are run from Octane's Script menu/editor; Lua can manipulate tables of node types/pin types, disconnect nodes, create root graphs, render nodes without changing the current project, and create GUI windows. |
| OTOY Standalone docs: `OctaneRender Modules` (`https://docs.otoy.com/StandaloneH_STA/StandaloneSTA/OctaneModules.htm`) | Native modules are C++ shared libraries loaded once at startup from a configured modules directory; macOS modules require `-undefined dynamic_lookup`; API calls generally occur on Octane's main/message thread; a bad module can crash Octane; examples include command modules and work-pane modules. |
| OTOY forum result: `Introducing the Octane Lua API` (`https://render.otoy.com/forum/viewtopic.php?t=37257`) | Search result confirms the API browser has an overview, function docs, and item/node/pin/attribute listings — exactly the information we should export locally from the running build. |
| Public Lua examples: `rndr-man/OctaneLuaSurvivalKit` (`https://github.com/rndr-man/OctaneLuaSurvivalKit`) | Confirms real-world Lua scripts use `octane.project.getSceneGraph()`, `graph:getOwnedItems()`, `node:getAttribute(octane.A_FILENAME)`, `node:setAnimator(...)`, `octane.file.*`, `octane.json.encode`, `octane.gui.*`, and headless `octane.exe --no-gui --script` patterns where supported. |

> Note: `web_extract` was unavailable in this Hermes session due Firecrawl billing/configuration. I fetched official pages directly with Python `urllib.request` and inspected the plain text that came back.

### Repo files inspected

- `README.md`
- `pyproject.toml`
- `docs/octane-bridge.md`
- `docs/roadmap.md`
- `docs/command-schema.md`
- `src/octanex_mcp/bridge.py`
- `src/octanex_mcp/bridge_control.py`
- `src/octanex_mcp/config.py`
- `src/octanex_mcp/server.py`
- `src/octanex_mcp/schema.py`
- `src/octanex_mcp/models.py`
- `octane_lua/hermes_bridge_oneshot_v2.lua`
- `octane_lua/hermes_bridge_persistent_v1.lua`
- `octane_lua/lib/runtime.lua`
- `octane_lua/lib/handlers.lua`
- `octane_lua/export_api_docs.lua`
- `octane_lua/export_api_docs_v2.lua`
- `tests/test_lua_bridge_parity.py`

---

## Current bridge architecture

```text
Hermes MCP tool
  -> Python FastMCP server (`src/octanex_mcp/server.py`)
  -> typed JSON command envelope (`models.py` / `schema.py`)
  -> atomic queue file under Octane container workspace (`bridge.py`)
  -> generated Lua bridge script run inside Octane X (`octane_lua/*.generated.lua`)
  -> Octane Lua API (`octane.project`, `octane.node`, `octane.render`, `octane.gui`)
  -> result JSON + PNG preview + local QA
```

### Strong parts

| Area | Evidence | Why it matters |
| --- | --- | --- |
| Safety boundary | `README.md` states arbitrary Lua is intentionally avoided; `models.py` defines `ALLOWED_OPS`; `write_command()` rejects unsupported ops. | Keeps agent access constrained to an inspectable command DSL. |
| Queue lifecycle | `bridge.py` writes atomic queue files and keeps `queue/`, `processing/`, `processed/`, `failed/`, `results/`. | Good auditability and crash recovery. |
| Result metadata | `docs/command-schema.md` documents per-command result files. | Lets agents verify behavior rather than trusting a tool call. |
| One-shot batch model | `docs/octane-bridge.md` documents one click drains the whole queue. | Avoids click-per-command races and UI dead time. |
| Defensive render handling | Lua bridge defers actual `octane.render.start{}` to preview/save paths and uses readiness polling. | Matches observed Octane behavior where render start can block. |
| Pixel/vision verification culture | AGENTS.md and skills require non-blank pixel checks plus vision. | Prevents false render success claims. |
| Existing API export seed | `octane_lua/export_api_docs_v2.lua` already uses `octane.help.modules()`, `octane.help.functions()`, `octane.help.properties()`, `octane.help.constants()`. | This is the right starting point for a local API corpus. |

### Weak parts

| Weakness | Evidence | Impact |
| --- | --- | --- |
| Lua API knowledge is not yet first-class | No committed `octane_lua_api.txt` / JSON corpus exists; only exporter scripts are present. | Bridge code must guess constants/pins/functions instead of validating against the active Octane X build. |
| Handler source-of-truth is confused | `octane_lua/lib/handlers.lua` says generated entrypoints `dofile` shared handlers, but AGENTS.md and current bridge templates state `lib/*.lua` are reference-only and handlers are inline. | Future agents may edit the wrong file and produce no runtime change. |
| One-shot and persistent bridge duplicate large handler bodies | Parity test compares function bodies byte-for-byte across templates. | Better than drift, but still makes edits expensive and error-prone. |
| Schema includes ops not in Python `ALLOWED_OPS` | Lua has `scene_harvest`; `bridge.py::scene_harvest()` queues it, but `models.ALLOWED_OPS` shown in the inspected file does not include `scene_harvest`. | This class of mismatch causes runtime failures or forces direct queue bypasses. It should be contract-tested automatically. |
| Material/light support is empirical | `handle_create_light()` comments say native light constants are nil on this Octane build and falls back to environment/emissive proxies. | Acceptable fallback, but should be captured as a build capability record, not a hardcoded anecdote. |
| Render/image-save API signatures are probed ad hoc | `handle_save_preview()` tries `saveImage`, `saveImage2`, `saveImage3`, `saveRenderPass` variants. | Practical, but opaque. A capability registry could select known-good calls for the current build and warn on drift. |
| Web/offline documentation drift | Skills contain some stale contradictory statements; `docs/roadmap.md` carries both current status and older roadmap sections. | Agents can reintroduce already-fixed bugs. This repo already recognizes this as a functional regression risk. |

---

## What the official Lua API implies for us

The official documentation and public examples point to a bridge built around **Octane's own runtime introspection**, not hand-maintained folklore.

### 1. The `octane` global is the root contract

Official docs state that Octane exposes a single global table named `octane`, with modules such as `octane.gui`. Constants can appear both in constant tables and directly under `octane`.

Current code already uses this pattern:

- `octane.project.getSceneGraph()` / `octane.nodegraph.getRootGraph()`
- `octane.node.create{ type=..., name=..., position=... }`
- `octane.render.start{ renderTargetNode = rt }`
- `octane.render.saveImage(...)`
- `octane.gui.*` in persistent bridge/window helpers
- direct constants such as `octane.NT_GEO_MESH`, `octane.P_CAMERA`, `octane.A_FILENAME`

**Recommendation:** make `octane` API introspection a build artifact:

```text
octane_lua/export_api_docs_v3.lua
  -> OctaneMCP/api/octane_lua_api.<octane-version>.json
  -> repo docs/reference/octane-lua-api/<version>.json
  -> generated Python capability registry
  -> generated Lua compat shims / tests
```

### 2. The API browser is likely the authoritative fine-grained reference

Official docs repeatedly point to the Lua API browser / HTML documentation script for exact modules, functions, properties, node types, dynamic pins, and constants.

The project should stop treating online docs as sufficient. They explain how the API is organized, but not necessarily the exact current Octane X build's constants and available calls.

**Recommendation:** run `export_api_docs_v2.lua` inside the user's Octane X and replace it with a structured exporter that captures:

- Octane app/version/build if exposed.
- `octane.help.modules()` output.
- `octane.help.functions(module)` and function docs.
- `octane.help.properties(module)`.
- `octane.help.constants(module)`.
- Direct constants on `octane` grouped by prefixes: `NT_`, `P_`, `A_`, `PT_`, image save constants, GUI constants.
- Probe results for runtime calls we depend on: `project.getSceneGraph`, `node.create`, `render.start`, `render.restart`, `render.saveImage`, `render.getRenderResultStatistics`, `file.exists`, `json.encode`.
- Optional node factory probes in a scratch graph, behind a safe flag: create/delete candidate nodes and record which node types actually exist.

### 3. Lua is already capable of more than we expose

Public examples use APIs we are barely using or not using systematically:

- `octane.file.*` for portable path/file handling.
- `octane.json.encode` for result/corpus writing.
- `node:getAnimator()` / `node:setAnimator(...)` for animated attributes.
- `node:isAnimated(attribute)`.
- `project.getProjectSettings()` and `A_FRAMES_PER_SECOND`.
- GUI components beyond simple bridge buttons.
- Scene scanning via `getOwnedItems()` and `getAttribute(A_FILENAME)`.

**Recommendation:** broaden the command DSL using these supported API areas, but only through typed, allowlisted operations:

- Native animation/attribute animator commands.
- Asset manifest/scanning commands.
- Project settings/query commands.
- Capability query command.
- Scene graph harvest command formally added to schema.
- Pin/attribute-safe material builders generated from known node definitions.

---

## Is there a better bridge architecture?

### Option A — Keep current JSON queue + Lua Script-menu execution, but formalize API capabilities

**Verdict: best immediate path.**

Pros:

- Works with Octane X's documented script model.
- Preserves a safe agent-facing DSL.
- Keeps Python dependencies light.
- Allows local, version-specific API discovery.
- Minimizes crash risk compared with native modules.
- Compatible with current recipe/QA/test infrastructure.

Cons:

- Still depends on Octane X GUI and Script-menu launch.
- macOS TCC/Accessibility remains a practical issue for autonomous launch.
- Lua scripts run on the UI/message thread; long/blocking work must be paced.
- Requires careful generated-script strategy if Octane cannot reliably `require` repo-local modules.

Best use:

- Current project default.
- Scene creation, material/light work, previews, visual DSLs, recipes, agentic canvas.

### Option B — Persistent Lua bridge as a true daemon/channel

**Verdict: useful after hardening, not enough by itself.**

Pros:

- Could reduce AppleScript clicks after one manual/autonomous startup.
- More natural for scene harvest, live status, and interactive tools.

Cons:

- Current skill notes say timer auto-poll has been unreliable.
- Long-running GUI windows can block viewport refresh.
- Still runs on Octane's UI thread.

Better design:

- Keep persistent bridge minimal: heartbeat, explicit `Drain queue`, capability export, scene harvest.
- Avoid timer loops unless verified on the target build.
- Use one-shot for render-producing batches until persistent is proven.

### Option C — Octane no-GUI/headless script execution

**Verdict: investigate, but do not assume Octane X supports it cleanly.**

Public examples mention `octane.exe --no-gui --script` on Windows/Standalone-style deployments. If Octane X on macOS exposes an equivalent binary/script mode, it could be valuable for API export, offline validation, or batch rendering.

Risks:

- Mac App Store Octane X sandboxing may differ from standalone docs/examples.
- The app bundle binary may not support the same CLI flags.
- GPU/render licensing and sandbox file access may differ.

Next test:

```bash
"/Applications/Octane X.app/Contents/MacOS/Octane X" --help
"/Applications/Octane X.app/Contents/MacOS/Octane X" --no-gui --script /path/to/export_api_docs_v3.lua
```

Do this as a spike with no assumptions. If it works, use it for API export and maybe batch tests; still keep GUI bridge for interactive canvas workflows.

### Option D — Native C++ Octane module

**Verdict: strategic later path, not the next replacement.**

Official module docs show this is a legitimate integration route: modules are C++ shared libraries, loaded at startup, registered as command or work-pane modules, and run on Octane's main/message thread. On macOS, modules use dynamic lookup. This could eventually eliminate Script-menu AppleScript and provide deeper API access.

But it carries clear costs:

- Loaded only at startup; cannot hot-load into running Octane.
- A module crash can crash Octane.
- Requires correct C++ ABI, SDK headers/wrappers, module registration, install paths, and code-sign/sandbox realities.
- Current `octanex-module` skill says the native fork is a scaffold: ABI mismatch, command dispatch stub, and Python FFI not actually driving Octane yet.

Best role:

- Later transport/backend behind the same JSON command DSL.
- Shared queue interop point remains valuable.
- Do not expose arbitrary native commands to agents.

### Option E — Direct AppleScript/UI automation only

**Verdict: keep as launcher/fallback only.**

AppleScript is useful for selecting the Script menu and File → New. It is not a good scene-control layer. The bridge should continue to use Octane Lua for scene graph operations and AppleScript only for app lifecycle/menu launch.

---

## Recommended target architecture

```text
                       ┌──────────────────────────────┐
                       │ docs/reference/octane-api     │
                       │ versioned API/capability JSON │
                       └──────────────┬───────────────┘
                                      │ generated from Octane X
                                      ▼
Hermes tool ──► Python command model / schema ──► queue/*.json
                                      │
                                      │ validates against capability registry
                                      ▼
                          generated Lua compat layer
                                      │
                                      ▼
                         one-shot / persistent wrappers
                                      │
                                      ▼
                         Octane Lua API (`octane.*`)
                                      │
                                      ▼
                         results + PNG + pixel/vision QA
```

### Core design principles

1. **DSL over arbitrary code.** Agents emit typed scene/render/material commands, never raw Lua.
2. **Capability-driven bridge.** The active Octane build determines supported node types/pins/functions.
3. **One source of truth for handlers.** Inline generated wrappers are acceptable, but handler source should not be manually duplicated.
4. **Probe, don't guess.** Unknown pin/function behavior should be measured once and recorded.
5. **Result files are contracts.** Every command returns structured success/failure/result metadata.
6. **Render verification remains external.** Octane success is not visual success; keep pixel QA + vision.

---

## Concrete implementation plan

### Phase 1 — Build an Octane Lua API corpus

Files:

- `octane_lua/export_api_docs_v3.lua`
- `src/octanex_mcp/api_corpus.py`
- `docs/reference/octane-lua-api/README.md`
- `docs/reference/octane-lua-api/<build>.json` after live export
- `tests/test_api_corpus.py`

Tasks:

1. Replace the text-only exporter with structured JSON.
2. Capture `octane.help` module/function/property/constant output.
3. Capture direct `octane` constants by prefix.
4. Capture feature probes for critical bridge calls.
5. Add a CLI command: `octanex-mcp api-corpus inspect/export/validate`.
6. Validate corpus shape offline in Python.

Acceptance criteria:

- A live Octane run writes a JSON API corpus into the container workspace.
- The repo can ingest the corpus and report capabilities.
- Tests fail clearly if required bridge capabilities are absent.

### Phase 2 — Make command schema and Lua dispatch mechanically consistent

Files:

- `src/octanex_mcp/models.py`
- `src/octanex_mcp/schema.py`
- `src/octanex_mcp/server.py`
- `octane_lua/*_v*.lua`
- `tests/test_schema.py`
- `tests/test_lua_bridge_parity.py`

Tasks:

1. Add a test that compares:
   - Python `ALLOWED_OPS`
   - `PAYLOAD_VALIDATORS`
   - `command_schema()["operations"]`
   - MCP tool queueing ops
   - Lua `handle_command` dispatch branches
2. Add missing ops intentionally or remove unsupported ones. Immediate candidate: formalize `scene_harvest` if it is meant to be supported.
3. Add capability-aware warnings when a command is valid but unsupported on the active Octane build.

Acceptance criteria:

- No operation can exist in only Python or only Lua without a failing test.
- `octane_schema()` distinguishes command-contract support from active-Octane capability support.

### Phase 3 — Collapse handler duplication into generated entrypoints

Files:

- `octane_lua/lib/runtime.lua`
- `octane_lua/lib/handlers.lua`
- `octane_lua/hermes_bridge_oneshot_v2.lua`
- `octane_lua/hermes_bridge_persistent_v1.lua`
- `src/octanex_mcp/config.py`
- `tests/test_lua_bridge_parity.py`

Tasks:

1. Decide honestly whether `lib/runtime.lua` / `lib/handlers.lua` are source-of-truth or reference-only.
2. If source-of-truth: make `octanex-mcp init` generate entrypoints by inlining lib chunks, not by maintaining duplicate handler bodies.
3. If reference-only remains necessary: update docs/comments to stop claiming generated entrypoints `dofile` handlers.
4. Keep generated `.generated.lua` self-contained enough for Octane X's sandbox/script path.

Acceptance criteria:

- A handler edit happens in one source file.
- Generated one-shot/persistent scripts preserve behavior.
- Parity test compares generated-from-same-source markers or source hashes rather than requiring humans to manually patch two large bodies.

### Phase 4 — Material/light/node compatibility registry

Files:

- `src/octanex_mcp/capabilities.py`
- `src/octanex_mcp/materials.py`
- `octane_lua/lib/compat.lua`
- tests under `tests/`

Tasks:

1. Build a registry of material node families and supported pins from the API corpus.
2. Replace large fallback pin lists with registry-backed helpers.
3. Keep graceful fallbacks when the build lacks real light nodes; but record the reason in capability metadata.
4. Add `octane_capabilities()` MCP tool.

Acceptance criteria:

- `create_material` can say which requested fields were applied, skipped, or approximated.
- `create_light` reports whether it created a native node, environment node, or emissive proxy.
- Tests cover at least one “missing native light constants” capability case.

### Phase 5 — Evaluate no-GUI and module transports as optional backends

Files:

- `docs/octane-transport-options.md`
- spike scripts under `scripts/spikes/`

Tasks:

1. Test whether Octane X's app binary supports `--help`, `--no-gui`, and `--script` on this install.
2. If yes, use it for API export and offline bridge smoke tests.
3. Audit `octanex-module` separately and decide whether to build a native command transport behind the existing queue DSL.

Acceptance criteria:

- The project has a measured transport matrix: Script-menu, persistent Lua, no-GUI script, native module.
- No transport is promoted without a real live proof and documented failure modes.

---

## Immediate high-value fixes discovered during this review

1. **Resolve `scene_harvest` contract mismatch.** The Lua bridge dispatches `scene_harvest`, and `bridge.py::scene_harvest()` queues it, but inspected `models.ALLOWED_OPS` did not include it. Add it with a payload validator, or change `scene_harvest()` to use a supported path. This should be covered by a dispatch/schema parity test.

2. **Correct `octane_lua/lib/handlers.lua` comments or generation behavior.** The file claims it is the source of truth and that generated entrypoints `dofile` it. Current project rules say handler copies are inline and `lib/*.lua` are reference-only. This is exactly the kind of stale bridge documentation that causes agents to patch the wrong file.

3. **Promote `export_api_docs_v2.lua` to a real artifact pipeline.** It already knows about `octane.help`; it just needs structured output, versioning, and ingestion.

4. **Add an `octane_capabilities()` MCP tool.** This should report active corpus version, bridge capability probes, known-good save-preview signature, material/light support, and transport readiness.

5. **Document public Lua examples as design evidence.** The Survival Kit examples validate that scene graph scans, file APIs, JSON encoding, animators, project settings, and GUI tools are normal Octane Lua workflows.

---

## Answer to the user's core question

> Is there a better way for us to implement this bridge?

Yes, but it is an **evolution of the Lua bridge**, not a wholesale replacement.

The better implementation is a **capability-driven Lua bridge**:

- Keep the queue and allowlisted JSON command DSL.
- Include Octane X's actual Lua API by exporting a structured local API corpus from the running build.
- Generate or validate bridge compatibility from that corpus.
- Collapse duplicated Lua handlers into one generated source path.
- Add schema/dispatch parity tests so unsupported ops cannot drift silently.
- Explore no-GUI and native module transports only as optional later backends.

This would make the bridge more reliable, less anecdotal, more portable across Octane X builds, and easier for future agents to extend without reintroducing known failures.
