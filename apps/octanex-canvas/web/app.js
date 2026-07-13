// OctaneX Agentic Canvas — thin-client web bundle (ES module).
//
// Pipeline (post WebGL phase):
//   POST /canvas/build {intent|scene} -> WebGLBackend emits canvas.scene.v1
//   GET  /canvas/scene                -> current canvas.scene.v1
//   POST /mcp/call {tool, args}       -> tool dispatch (same functions the MCP server wraps)
//   GET  /status                      -> bridge status.json
//   GET  /preview[?progressive=1]     -> latest Octane render PNG (quality tier)
//   POST /intent {text}               -> record a free-text intent for the agent loop
//
// Everything funnels through submitIntent() so voice / drag-drop can later drop
// payloads into the identical path.

import { CanvasRenderer } from "./canvas/renderer.js";

const GW = ""; // same origin (served from the gateway itself)

const dom = {
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
  inspectorFixes: document.getElementById("inspector-fixes"),
  camDist: document.getElementById("cam-dist"),
};

const state = {
  previewETag: null,
  lastStatusAt: 0,
  paletteItems: [],
  paletteActive: 0,
  continuityLoaded: false,
  currentScene: null,
  viewMode: "live",
  renderer: null,
};

// ---------------------------------------------------------------------------
// Gateway helpers
// ---------------------------------------------------------------------------
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

// ---------------------------------------------------------------------------
// Live WebGL scene (Phase 2)
// ---------------------------------------------------------------------------
function initRenderer() {
  state.renderer = new CanvasRenderer(dom.webgl);
  state.renderer.onPick = (id, meta) => {
    // Expose selection to the inspector path (Phase 5 will bind edits).
    state.selectedId = id;
    console.debug("picked", id, meta);
  };
  state.renderer.start();
}

async function buildScene(intent, plan) {
  dom.status.className = "state-queued";
  dom.statusText.textContent = "building…";
  try {
    const res = await postJSON("/canvas/build", plan ? { scene: plan } : { intent });
    if (!res.ok) {
      dom.status.className = "state-error";
      dom.statusText.textContent = "build failed";
      console.error(res.error);
      return;
    }
    const scene = res.scene;
    state.currentScene = scene;
    if (state.renderer) state.renderer.setScene(scene);
    dom.placeholder.style.display = "none";
    // Honest status: show the interpreted intent the planner heard.
    const heard = scene.intent ? `live · ${scene.intent}`.slice(0, 80) : "live preview";
    dom.status.className = "state-ready";
    dom.statusText.textContent = heard;
    if (scene.scene_id) localStorage.setItem("octanex.lastSceneId", scene.scene_id);
  } catch (e) {
    dom.status.className = "state-error";
    dom.statusText.textContent = "gateway unreachable";
  }
}

// ---------------------------------------------------------------------------
// Preview polling (Octane quality tier)
// ---------------------------------------------------------------------------
async function pollPreview() {
  if (state.viewMode === "live") {
    // In live-only mode the WebGL canvas owns the screen; don't cover it.
    dom.preview.classList.remove("visible");
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
    const s = await getJSON("/status");
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
    // doing something (rendering / queued / error) — never when idle/ready, which
    // would clobber the useful "live · <intent>" label with Octane's own state.
    const octaneActive = ["queued", "processing", "rendering", "review", "error"].includes(stage);
    if (state.currentScene && !octaneActive) {
      return;
    }
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
// Intent boundary — single entry point for all input
// ---------------------------------------------------------------------------
async function submitIntent(text) {
  const t = (text || "").trim();
  if (!t) return;
  // The canvas build is synchronous-ish: show a live WebGL scene immediately,
  // independent of Octane. The intent is still logged for the agent loop.
  await buildScene(t);
  try {
    await fetch(`${GW}/intent`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: t }),
    });
    localStorage.setItem("octanex.lastIntent", JSON.stringify({ text: t, ts: Date.now() }));
  } catch (_) {
    dom.status.className = "state-error";
    dom.statusText.textContent = "dispatch failed";
  }
}

dom.cmd.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
    e.preventDefault();
    submitIntent(dom.cmd.value);
    dom.cmd.value = "";
  }
});

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

// ---------------------------------------------------------------------------
// ⌘K command palette
// ---------------------------------------------------------------------------
async function openPalette() {
  dom.palette.classList.remove("hidden");
  dom.paletteInput.value = "";
  await refreshPalette("");
  dom.paletteInput.focus();
}

async function refreshPalette(filter) {
  if (state.paletteItems.length === 0) {
    try {
      const book = await callTool("octane_recipe_book");
      const idx = await callTool("octane_recipe_index");
      const recipes = (idx.result && idx.result.recipes) || (book.result && book.result.recipes) || [];
      state.paletteItems = Array.isArray(recipes)
        ? recipes.map((r) => ({ slug: r.slug || r.name, label: r.title || r.slug || r.name, meta: r.tier || r.group || "recipe" }))
        : [];
      if (state.paletteItems.length === 0) {
        state.paletteItems = [{ slug: "t1_glossy_cube", label: "Glossy cube (tier 1)", meta: "recipe" }];
      }
    } catch (_) {
      state.paletteItems = [{ slug: "t1_glossy_cube", label: "Glossy cube (fallback)", meta: "recipe" }];
    }
  }
  const f = (filter || "").toLowerCase();
  const items = state.paletteItems.filter(
    (i) => !f || i.label.toLowerCase().includes(f) || i.slug.toLowerCase().includes(f)
  );
  state.paletteActive = 0;
  dom.paletteList.innerHTML = items
    .map((i, n) => `<li data-slug="${i.slug}" class="${n === 0 ? "active" : ""}"><span>${i.label}</span><span class="meta">${i.meta}</span></li>`)
    .join("");
  dom.paletteList.querySelectorAll("li").forEach((li) => {
    li.addEventListener("click", () => queueRecipe(li.dataset.slug));
  });
}

async function queueRecipe(slug) {
  dom.palette.classList.add("hidden");
  dom.status.className = "state-queued";
  dom.statusText.textContent = `queued ${slug}`;
  const res = await callTool("octane_queue_recipe", { slug });
  if (res.ok) {
    await callTool("octane_save_preview", { samples: 64, timeout_seconds: 12 });
    setViewMode("final");
  }
}

dom.paletteInput.addEventListener("input", (e) => refreshPalette(e.target.value));
dom.paletteInput.addEventListener("keydown", (e) => {
  const items = dom.paletteList.querySelectorAll("li");
  if (e.key === "ArrowDown") {
    e.preventDefault();
    state.paletteActive = Math.min(state.paletteActive + 1, items.length - 1);
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    state.paletteActive = Math.max(state.paletteActive - 1, 0);
  } else if (e.key === "Enter") {
    e.preventDefault();
    const sel = items[state.paletteActive];
    if (sel) queueRecipe(sel.dataset.slug);
    return;
  } else if (e.key === "Escape") {
    dom.palette.classList.add("hidden");
    return;
  }
  items.forEach((li, n) => li.classList.toggle("active", n === state.paletteActive));
});

// ---------------------------------------------------------------------------
// ⌘I inspector (preview review; live-object editing lands in Phase 5)
// ---------------------------------------------------------------------------
async function openInspector() {
  dom.inspector.classList.remove("hidden");
  await refreshReview();
}

async function refreshReview() {
  try {
    const r = await callTool("octane_review_preview");
    const review = r.result || {};
    dom.inspectorReview.textContent = JSON.stringify(review, null, 2).slice(0, 2000);

    const bounds = review.asset_bounds || { center: [0, 0, 0.5], radius: 3.0 };
    const fixes = await callTool("octane_suggest_camera_fix", { preview_review: review, asset_bounds: bounds });
    const actions = (fixes.result && fixes.result.recommended_actions) || [];
    dom.inspectorFixes.innerHTML = actions
      .map((a, n) => `<button data-i="${n}">${a.action}</button>`)
      .join("");
    dom.inspectorFixes.querySelectorAll("button").forEach((b) =>
      b.addEventListener("click", () => applyFix(actions[b.dataset.i]))
    );
  } catch (_) {
    dom.inspectorReview.textContent = "review unavailable";
  }
}

async function applyFix(action) {
  if (!action) return;
  const dist = parseFloat(dom.camDist.value);
  const pos = [0, 0, dist];
  await callTool("octane_set_camera", { position: pos, target: [0, 0, 0.5], fov: 45 });
  await callTool("octane_start_render", { samples: 64, width: 1280, height: 1280 });
  await callTool("octane_save_preview", { samples: 64, timeout_seconds: 12 });
  await refreshReview();
}

dom.camDist.addEventListener("change", () => applyFix());
dom.inspectorClose.addEventListener("click", () => dom.inspector.classList.add("hidden"));

// ---------------------------------------------------------------------------
// View modes: live (WebGL) / final (Octane PNG) / split
// ---------------------------------------------------------------------------
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
// Global shortcuts (⌘K, ⌘I, ~)
// ---------------------------------------------------------------------------
document.addEventListener("keydown", (e) => {
  const k = e.key.toLowerCase();
  if (e.metaKey && k === "k") {
    e.preventDefault();
    dom.palette.classList.contains("hidden") ? openPalette() : dom.palette.classList.add("hidden");
  } else if (e.metaKey && k === "i") {
    e.preventDefault();
    dom.inspector.classList.contains("hidden") ? openInspector() : dom.inspector.classList.add("hidden");
  } else if (k === "~" || (e.key === "`" && !e.metaKey)) {
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
