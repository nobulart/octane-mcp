// OctaneX Agentic Canvas — shared state + gateway helpers.
// Loaded first (imported by app.js and agent.js). ES module scope is deferred,
// so the DOM is ready when `dom` resolves its elements.

export const GW = ""; // same origin (served from the gateway itself)

// Dev-mode auto-detect: served from localhost/127.0.0.1 (the gateway runs
// locally), or forced with ?dev. In dev mode the forensic debug stream renders
// over the canvas so we can examine agent actions / model changes live.
export const DEV_MODE =
  /[?&]dev\b/.test(location.search) ||
  location.hostname === "localhost" ||
  location.hostname === "127.0.0.1";

export const dom = {
  preview: document.getElementById("preview"),
  placeholder: document.getElementById("placeholder"),
  webgl: document.getElementById("webgl-canvas"),
  viewmodes: document.getElementById("viewmodes"),
  cmd: document.getElementById("cmd"),
  cmdbar: document.getElementById("cmdbar"),
  status: document.getElementById("status"),
  statusText: document.getElementById("status-text"),
  palette: document.getElementById("palette"),
  paletteInput: document.getElementById("palette-input"),
  paletteList: document.getElementById("palette-list"),
  inspector: document.getElementById("inspector"),
  inspectorClose: document.getElementById("inspector-close"),
  inspectorReview: document.getElementById("inspector-review"),
  inspectorControls: document.getElementById("inspector-controls"),
  inspectorSelection: document.getElementById("inspector-selection"),
  inspectorFixes: document.getElementById("inspector-fixes"),
  camDist: document.getElementById("cam-dist"),
  modelSelect: document.getElementById("model-select"),
  voxToggle: document.getElementById("vox-toggle"),
  response: document.getElementById("response"),
  logToggle: document.getElementById("log-toggle"),
  transcript: document.getElementById("transcript"),
  transcriptBody: document.getElementById("transcript-body"),
  transcriptClose: document.getElementById("transcript-close"),
  selChip: document.getElementById("sel-chip"),
  snapToggle: document.getElementById("snap-toggle"),
  tasks: document.getElementById("tasks"),
  dotFront: document.getElementById("dot-front"),
  dotBack: document.getElementById("dot-back"),
  debugLog: document.getElementById("debug-log"),
};

export const state = {
  previewETag: null,
  lastStatusAt: 0,
  paletteItems: [],
  paletteActive: 0,
  continuityLoaded: false,
  currentScene: null,
  viewMode: "live",
  renderer: null,
  vox: false,
  contract: "",
  selectedId: null,
  activeTask: null, // { controller, el, label, kind }
};

async function callTool(tool, args = {}) {
  const r = await fetch(`${GW}/mcp/call`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tool, args }),
  });
  return r.json();
}

async function postJSON(path, body) {
  const r = await fetch(`${GW}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  return r.json();
}

async function getJSON(path) {
  const r = await fetch(`${GW}${path}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`${path} -> ${r.status}`);
  return r.json();
}

function debugLog(cat, msg, payload) {
  if (!DEV_MODE || !dom.debugLog) return;
  const t = new Date();
  const ts = `${String(t.getHours()).padStart(2, "0")}:${String(t.getMinutes()).padStart(2, "0")}:${String(t.getSeconds()).padStart(2, "0")}`;
  const line = document.createElement("div");
  line.className = `dbg dbg-${cat}`;
  const p = payload !== undefined && payload !== null
    ? ` ${typeof payload === "string" ? payload : JSON.stringify(payload)}`.slice(0, 400)
    : "";
  line.textContent = `${ts} ${cat.toUpperCase()} · ${msg}${p}`;
  dom.debugLog.appendChild(line);
  while (dom.debugLog.childElementCount > 400) dom.debugLog.removeChild(dom.debugLog.firstChild);
}

function escapeHtml(s) {
  return String(s).replace(/[&<>\"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// --- View modes + status polling (shared; imported by app.js + agent.js) ----
const STAGE_LABEL = {
  queued: ["queued", "state-queued"],
  processing: ["processing", "state-queued"],
  rendering: ["rendering", "state-render"],
  review: ["reviewing", "state-render"],
  ready: ["ready", "state-ready"],
  error: ["error", "state-error"],
};

async function pollPreview() {
  if (state.viewMode === "live") {
    dom.preview.classList.remove("visible");
    // A live WebGL scene owns the viewport — the "no frame yet" overlay only
    // makes sense when there is no scene at all. Hide it once a scene is loaded.
    if (state.currentScene) {
      dom.placeholder.style.display = "none";
      dom.placeholder.textContent = "";
    } else {
      dom.placeholder.style.display = "";
      dom.placeholder.textContent = "type an intent, or open ⌘K to load a recipe";
    }
    return;
  }
  const url = `${GW}/preview?ts=${Date.now()}`;
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

async function pollStatus() {
  try {
    const s = await (await fetch(`${GW}/status`, { cache: "no-store" })).json();
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
    // Once a live WebGL scene exists, the canvas owns the status text. Only let
    // Octane status through when it is actively doing something.
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

function setViewMode(mode) {
  state.viewMode = mode;
  document.body.classList.remove("mode-live", "mode-final", "mode-split");
  document.body.classList.add(`mode-${mode}`);
  dom.viewmodes.querySelectorAll("button").forEach((b) => b.classList.toggle("active", b.dataset.mode === mode));
  pollPreview();
}

export { callTool, postJSON, getJSON, escapeHtml, debugLog, pollPreview, pollStatus, setViewMode };

