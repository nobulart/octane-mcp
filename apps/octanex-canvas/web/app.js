// OctaneX Agentic Canvas — shell entry point (ES module).
//
// Pipeline (post WebGL phase):
//   POST /canvas/build {intent|scene} -> WebGLBackend emits canvas.scene.v1
//   GET  /canvas/scene                -> current canvas.scene.v1
//   POST /mcp/call {tool, args}       -> tool dispatch (same functions the MCP server wraps)
//   GET  /status                      -> bridge status.json
//   GET  /preview[?progressive=1]     -> latest Octane render PNG
//   POST /intent {text}               -> record a free-text intent for the agent loop
//
// Everything funnels through submitIntent() (in agent.js) so voice / drag-drop
// can later drop payloads into the identical path.
import { CanvasRenderer } from "./canvas/renderer.js";
import { dom, state } from "./state.js";
import {
  submitIntent, showSelection,
  openPalette, openInspector, snapAndSend,
  loadModels, onModelChange, loadVox, onVoxToggle,
  loadTranscript, toggleLog,
} from "./agent.js";

// Live WebGL scene (Phase 2)
function initRenderer() {
  state.renderer = new CanvasRenderer(dom.webgl);
  state.renderer.onPick = (id, meta) => {
    state.selectedId = id;
    showSelection(id, meta);
  };
  state.renderer.start();
}

// ---------------------------------------------------------------------------
// Preview polling (Octane quality tier)
// ---------------------------------------------------------------------------
async function pollPreview() {
  if (state.viewMode === "live") {
    dom.preview.classList.remove("visible");
    dom.placeholder.style.display = "";
    return;
  }
  const url = `${""}/preview?ts=${Date.now()}`;
  try {
    const r = await fetch(url, { cache: "no-store" });
    if (r.ok) {
      dom.preview.src = url;
      dom.preview.classList.add("visible");
      dom.preview.classList.toggle("final-mode", state.viewMode === "final");
      dom.placeholder.style.display = "none";
    } else {
      dom.preview.classList.remove("visible");
      dom.placeholder.style.display = "";
      dom.placeholder.textContent = "no Octane frame yet — build or queue a recipe, or switch to Live";
    }
  } catch (_) {
    /* gateway down — leave last frame */
  }
}

// ---------------------------------------------------------------------------
// Status pill + truthful stage mapping
// ---------------------------------------------------------------------------
const STAGE_LABEL = {
  queued: ["queued", "state-queued"],
  processing: ["processing", "state-queued"],
  rendering: ["rendering", "state-render"],
  review: ["reviewing", "state-render"],
  ready: ["ready", "state-ready"],
  error: ["error", "state-error"],
};

async function pollStatus() {
  try {
    const s = await (await fetch(`${""}/status`, { cache: "no-store" })).json();
    state.lastStatusAt = Date.now();
    const stage = s.render_stage || (s.status === "failed" ? "error" : (s.status || "idle"));
    const [label, cls] = STAGE_LABEL[stage] || ["idle", "state-idle"];
    let text = label;
    if (stage === "rendering" && s.samples_done && s.samples_target) {
      const pct = Math.round((s.samples_done / s.samples_target) * 100);
      text = `rendering ${pct}%`;
    } else if (s.last_event) {
      text = `${label} · ${s.last_event}`.slice(0, 80);
    }
    // Once a live WebGL scene exists, the canvas owns the status text (it shows
    // the interpreted intent). Only let Octane status through when it is actively
    // doing something (rendering / queued / error).
    const octaneActive = ["queued", "processing", "rendering", "review", "error"].includes(stage);
    if (state.currentScene && !octaneActive) return;
    dom.status.className = cls;
    dom.statusText.textContent = text;
  } catch (_) {
    if (state.lastStatusAt && Date.now() - state.lastStatusAt > 15000 && !state.currentScene) {
      dom.status.className = "state-error";
      dom.statusText.textContent = "stalled";
    }
  }
}

// ---------------------------------------------------------------------------
// Continuity
// ---------------------------------------------------------------------------
function restoreContinuity() {
  if (state.continuityLoaded) return;
  const raw = localStorage.getItem("octanex.lastIntent");
  if (raw) {
    try {
      const { text } = JSON.parse(raw);
      dom.cmd.value = text;
      dom.cmd.placeholder = `last: "${text}" — ⌘↵ to resend, or type a new intent`;
    } catch (_) {}
  }
  state.continuityLoaded = true;
}

// View modes: live (WebGL) / final (Octane PNG) / split
function setViewMode(mode) {
  state.viewMode = mode;
  document.body.classList.remove("mode-live", "mode-final", "mode-split");
  document.body.classList.add(`mode-${mode}`);
  dom.viewmodes.querySelectorAll("button").forEach((b) => b.classList.toggle("active", b.dataset.mode === mode));
  pollPreview();
}

if (dom.viewmodes) {
  dom.viewmodes.querySelectorAll("button").forEach((b) =>
    b.addEventListener("click", () => setViewMode(b.dataset.mode))
  );
}

// ---------------------------------------------------------------------------
// Cmd-bar submit (⌘/Ctrl+Enter OR plain Enter)
// ---------------------------------------------------------------------------
dom.cmd.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.metaKey || e.ctrlKey || !e.shiftKey)) {
    e.preventDefault();
    submitIntent(dom.cmd.value);
  }
});

// ---------------------------------------------------------------------------
// Global shortcuts (⌘K, ⌘I, ~)
// ---------------------------------------------------------------------------
document.addEventListener("keydown", (e) => {
  const k = e.key.toLowerCase();
  const mod = e.metaKey || e.ctrlKey; // ⌘ on macOS, Ctrl on others / headless
  if (mod && k === "k") {
    e.preventDefault();
    dom.palette.classList.contains("hidden") ? openPalette() : dom.palette.classList.add("hidden");
  } else if (mod && k === "i") {
    e.preventDefault();
    dom.inspector.classList.contains("hidden") ? openInspector() : dom.inspector.classList.add("hidden");
  } else if (k === "~" || (e.key === "`" && !mod)) {
    e.preventDefault();
    document.body.classList.toggle("focus");
  } else if (e.key === "Escape") {
    dom.palette.classList.add("hidden");
    dom.inspector.classList.add("hidden");
  }
});

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
initRenderer();
restoreContinuity();
setViewMode("live");
setInterval(pollPreview, 750);
setInterval(pollStatus, 750);
pollPreview();
pollStatus();
loadModels();
if (dom.modelSelect) dom.modelSelect.addEventListener("change", onModelChange);
loadVox();
if (dom.voxToggle) dom.voxToggle.addEventListener("click", onVoxToggle);
loadTranscript();
if (dom.logToggle) dom.logToggle.addEventListener("click", toggleLog);
if (dom.transcriptClose) dom.transcriptClose.addEventListener("click", () => {
  dom.transcript.classList.add("hidden");
  dom.logToggle.setAttribute("aria-pressed", "false");
});
if (dom.snapToggle) dom.snapToggle.addEventListener("click", snapAndSend);
