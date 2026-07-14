// OctaneX Agentic Canvas — shared state + gateway helpers.
// Loaded first (imported by app.js and agent.js). ES module scope is deferred,
// so the DOM is ready when `dom` resolves its elements.

export const GW = ""; // same origin (served from the gateway itself)

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

function escapeHtml(s) {
  return String(s).replace(/[&<>\"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

export { callTool, postJSON, getJSON, escapeHtml };
