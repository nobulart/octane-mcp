# OctaneX Agentic Canvas — Implementation Roadmap

**Status:** Draft for build. Supersedes the high-level "Phase A–D" bullets in
`reports/dashboard-proposal/octanex-agentic-canvas.html §6` with ticket-ready
detail. Carries forward the four recommendations decided in that proposal's
follow-up (host surface, multi-surface, voice timing, sharing).

**Source of truth:** the proposal at
`reports/dashboard-proposal/octanex-agentic-canvas.html` and its captured mockup
states in `reports/dashboard-proposal/assets/` (`mockup-default.png`,
`mockup-palette.png`, `mockup-inspector.png`).

---

## 0. Architecture recap (unchanged layers)

```
┌────────────────────────┐   WKWebView (Swift)   ┌─────────────────────────┐
│  Agentic Canvas (app)  │ ──── HTTP/stdio ────▶ │  Hermes MCP server      │
│  apps/octanex-canvas   │                        │  src/octanex_mcp/       │
│  - command bar         │ ◀── status.json ───── │  octane_status()        │
│  - ⌘K / ⌘I / ~        │      preview.png       │  octane_save_preview()  │
└────────────────────────┘                        └───────────┬─────────────┘
                                                              │ AppleScript / SSH
                                                              ▼
                                                   ┌─────────────────────────┐
                                                   │  Octane bridge (Lua)    │
                                                   │  octane_lua/hermes_*    │
                                                   │  write_status() → JSON  │
                                                   └───────────┬─────────────┘
                                                               ▼
                                                        Octane X (render)
```

The dashboard is a **thin client by construction**. What changes between a
laptop render and a Studio render is only *where the bridge executes and where
`preview.png` lands* — not the UI, not the agent, not the MCP protocol.

---

## 1. Decision log (the four recommendations, resolved)

| # | Question | Decision | Consequence / build target |
|---|----------|----------|----------------------------|
| 1 | Host: inject WKWebView into Octane, or separate app? | **Separate native Swift+WKWebView app** (`apps/octanex-canvas`). | Octane X is a closed Otoy binary with no extension API, so in-Window injection is not currently buildable. A native app also avoids a ~150 MB Electron/Chromium bundle and matches the local-first privacy posture. Revisit only if Otoy ships a plugin surface. |
| 2 | Multi-surface: drive Mac Studio (M3 Ultra, 512 GB) as heavy renderer? | **Yes — build the target-select as a config flag in Phase A**, not Phase D. | `OCTANEX_RENDER_HOST` (`localhost` \| `mac-studio.local`). Studio reached over the existing SSH shared key; previews pulled back via `scp`/lazy backup sync. Laptop stays responsive; Studio holds scenes the M3 Max cannot. |
| 3 | Voice: day-1 or stretch? | **Stretch (Phase D), but make intent ingestion modality-agnostic from day 1.** | The command bar calls one `submitIntent(text)` boundary. Voice is a later adapter (local Whisper) feeding the same string. Avoids the mis-transcription → wrong-render failure mode during core build. |
| 4 | Sharing: one-click export to X, or local-first? | **Local-first by default; explicit opt-in export, never auto-upload.** | Default actions: clipboard copy PNG, save to folder, copy scene-manifest JSON. "Share to X" copies `preview.png` + a draft caption to the clipboard; the human posts. Honors privacy; serves the real workflow (you share real tool output to X). |

---

## 2. Phase timeline

```
Wk1    ── Phase A: Canvas shell + Studio config flag ─────┐
Wk1–2  ── Phase B: ⌘K palette, ⌘I inspector, ~ focus ────┤
Wk2–3  ── Phase C: progressive save + live stage polling ─┤  (Studio target live from Phase A)
Wk4    ── Phase D: voice adapter (stub→impl), share ──────┘
```

**Recommended first slice (highest thesis-per-effort):** Phase A shell **+ the
Studio flag (A5) + the progressive save hook stub (C1/C2 foundations)**. That
demonstrates end-to-end: type intent on the laptop → watch it build on the
Studio → honest progress → real preview, in roughly one week.

---

## 3. Phase A — Canvas shell (1–2 days)

**Goal:** a borderless/translucent native window that shows Octane's output
full-bleed, takes an intent via a command bar, and shows live status — matching
`mockup-default.png`.

**Scope in:** viewport binding, command bar, status pill, render-host flag.
**Scope out:** palette, inspector, voice, sharing (later phases).

### Tasks

- **A1 — Scaffold Swift+WKWebView app**
  - *Files:* new `apps/octanex-canvas/` (Xcode/macOS target, single window).
  - *Steps:* single `NSWindow` with `WKWebView`; transparent/titlebar-less
    option for clutter-free overlay; loads a local `index.html` bundle.
  - *Acceptance:* app builds and launches; web view renders a placeholder.

- **A2 — Full-bleed viewport binding**
  - *Files:* `apps/octanex-canvas/` web bundle; consumes
    `Workspace().renders_dir/preview.png`.
  - *Steps:* watch the preview path (fswatch / `DispatchSource`) and reload the
    `<img>` on change; handle missing/partial file gracefully.
  - *Acceptance:* after `octane_save_preview()` writes a frame, the canvas
    updates within ~1 s, no white flash on partial writes.

- **A3 — Intent command bar (⌘↵)**
  - *Files:* web bundle + a thin local bridge that calls the agent loop.
  - *Steps:* text field → `submitIntent(text)` → agent `octane_queue_recipe` /
    `octane_import_geometry` / `octane_start_render` as the agent decides.
  - *Acceptance:* typing an intent + enter drives a render that appears in the
    viewport; matches `mockup-default.png`.

- **A4 — Live status pill**
  - *Files:* `octane_status()` (`src/octanex_mcp/server.py:44`), bridge
    `status.json`.
  - *Steps:* poll `octane_status()` (or read `ROOT/status.json` directly) and
    surface `status` + `last_event` as corner HUD text.
  - *Acceptance:* pill shows `queued` / `processing` / `ready` transitions.

- **A5 — Render-host config flag (the Studio target, built early)**
  - *Files:* `src/octanex_mcp/server.py` (`octane_run_bridge`), new
    `OCTANEX_RENDER_HOST` setting; bridge `ROOT` already points at the container
    FS workspace.
  - *Steps:* when host = `mac-studio.local`, `octane_run_bridge` executes via
    `ssh craig@mac-studio.local` and previews are pulled back with `scp`
    (or the existing lazy backup sync). `localhost` path unchanged.
  - *Acceptance:* flipping the flag renders on the Studio; laptop UI is
    unchanged; preview appears in the local viewport.

- **A6 — Modality-agnostic intent boundary (voice-ready stub)**
  - *Files:* `apps/octanex-canvas/` `submitIntent(text)` entry point.
  - *Steps:* all intent input funnels through one function; no keyboard-specific
    coupling.
  - *Acceptance:* voice not required, but the only edit needed later is to call
    `submitIntent` from a Whisper callback.

**Phase A risks:** Octane must already be running (cold-engine re-wedge — use
File>New on a warm engine, per bridge notes). Preview path must be the container
FS `OctaneMCP/` workspace, not the repo checkout.

---

## 4. Phase B — Reveal surfaces (2–3 days)

**Goal:** the clutter-free default stays minimal; ⌘K and ⌘I reveal depth on
demand. Matches `mockup-palette.png` and `mockup-inspector.png`.

- **B1 — ⌘K command palette**
  - *Files:* web bundle; `octane_recipe_book()`, `octane_queue_recipe(slug)`,
    `octane_validate_command()`.
  - *Steps:* grouped tool/recipe suggestions; accept a reference-image attachment
    (path intent).
  - *Acceptance:* opening palette shows grouped suggestions; selecting a recipe
    queues it via `octane_queue_recipe`.

- **B2 — ⌘I inspector drawer**
  - *Files:* web bundle; `octane_review_preview()`, `octane_suggest_camera_fix()`,
    camera/`octane_start_render()` ops in the bridge.
  - *Steps:* reveal-on-demand side drawer; live controls (e.g. camera-distance
    slider → re-render); suggested-patch chips from QA output that apply + re-queue.
  - *Acceptance:* dragging the slider re-renders; a patch chip applies and
    re-queues the scene.

- **B3 — `~` focus / clutter-free toggle**
  - *Files:* web bundle + window config.
  - *Steps:* toggle hides command bar + HUD pills; optional translucent overlay
    sitting over the Octane window.
  - *Acceptance:* toggle produces the minimal present state from the proposal.

**Phase B risks:** key-handling conflicts when the window overlays Octane
(reason #1 for not injecting into Octane's own window).

---

## 5. Phase C — Latency honesty & continuity (3–4 days)

**Goal:** every progress claim is true, and a session survives restart. This is
the proposal's §3.2 honesty promise made real.

- **C1 — Progressive preview hook**
  - *Files:* `octane_save_preview()` (`server.py:246`) + `handle_save_preview`
    in `octane_lua/hermes_bridge_oneshot_v2.lua:763` /
    `hermes_bridge_persistent_v1.lua`.
  - *Steps:* add `progressive: bool`; when set, bridge does a low-spp quick
    save then the final pass (reuse the existing `quality` tier machinery).
  - *Acceptance:* a single `save_preview(progressive=True)` yields an early
    low-quality frame and a final frame.

- **C2 — Enrich `status.json` with render progress**
  - *Files:* `write_status()` (`oneshot_v2.lua:202`).
  - *Steps:* add `render_stage` (`queued`→`processing`→`rendering`→`review`→
    `ready`), `samples_done`, `samples_target`, `last_preview_path`. Bridge
    updates these during the render poll.
  - *Acceptance:* `status.json` exposes a truthful percentage mid-render.

- **C3 — Live stage polling in the UI**
  - *Files:* web bundle; reads `status.json` (or `octane_status()`).
  - *Steps:* show `Rendering 38%` from `samples_done/samples_target`; honest
    timeouts — surface a wedge/error state instead of a frozen spinner.
  - *Acceptance:* during a ~20 s render the UI shows real stage transitions;
    a stalled render is reported, not hidden.

- **C4 — Continuity**
  - *Files:* local app state file (intent + scene manifest).
  - *Steps:* persist last intent + resolved command sequence; restore on launch.
  - *Acceptance:* closing and reopening restores the last scene + intent.

**Phase C risks:** `status.json` is written by the bridge under Octane's
container FS — the UI must read the *resolved* path (localhost `OctaneMCP/`, or
the `scp`-pulled copy when on Studio).

---

## 6. Phase D — Voice & multimodal (stretch)

- **D1 — Voice adapter**
  - *Files:* local Whisper (Nous STT is in subscription); feeds `submitIntent`.
  - *Acceptance:* spoken intent builds a scene through the identical path as text.

- **D2 — Drag-reference-image intent**
  - *Files:* web bundle; attaches a path to the command bar intent.
  - *Acceptance:* dropping an image yields "like this, but…" intent with the
    reference path included.

- **D3 — Share actions (local-first)**
  - *Files:* web bundle; clipboard / file-save / manifest-JSON copy.
  - *Steps:* "Share to X" copies `preview.png` + a draft caption to the
    clipboard only. No network upload without an explicit user click.
  - *Acceptance:* each action works; no auto-upload occurs.

---

## 7. Definition of Done (whole initiative)

- [ ] Type an intent on the laptop → Octane builds the scene → preview appears
      full-bleed, with live status (A).
- [ ] ⌘K / ⌘I / `~` reveal depth without cluttering the default (B).
- [ ] During a render the UI shows *truthful* stage/progress; sessions survive
      restart (C).
- [ ] Same intent surface drives the Mac Studio as a heavy renderer, laptop as
      thin client (A5 + C).
- [ ] Voice + reference-image intent are possible via the same `submitIntent`
      path; outputs share local-first (D).
- [ ] Every acceptance state is reproducible from the captured mockups
      (`mockup-default/palette/inspector.png`).

## 8. Non-goals (explicitly NOT doing)

- No Electron/Chromium bundle.
- No injecting UI into Octane X's own window (no plugin API available).
- No automatic upload of any render to any network destination.
- No voice as a day-1 hard requirement.

---

## 9. Open build questions to close before A1

1. App packaging: Xcode project vs. a lightweight `swift` CLI + WKWebView
   harness? (Affects repo CI.)
2. Preview delivery on Studio: `scp` pull vs. rely on the existing lazy backup
   sync — which is lower-latency for a 1280² PNG?
3. Should `OCTANEX_RENDER_HOST` live in `config.yaml` (MCP) or an env var the
   app sets at launch?
