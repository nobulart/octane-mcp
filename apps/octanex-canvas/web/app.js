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

const state = {
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
    state.selectedId = id;
    showSelection(id, meta);
  };
  state.renderer.start();
}

// Selection -> inspector (Phase 5 first cut: editable live object).
function showSelection(id, meta) {
  state.selectedId = id;
  const o = (state.currentScene && state.currentScene.objects || []).find((x) => x.id === id);
  if (!o) return;
  // Selection chip in the cmd bar: click to reference @id in the next message.
  if (dom.selChip) {
    dom.selChip.textContent = `▣ ${o.label || id}`;
    dom.selChip.dataset.ref = id;
    dom.selChip.classList.remove("hidden");
    dom.selChip.onclick = () => {
      const cur = dom.cmd.value;
      dom.cmd.value = cur.includes(`@${id}`) ? cur : `${cur} @${id} `.trimStart();
      dom.cmd.focus();
    };
  }
  const mat = (state.currentScene && state.currentScene.materials || []).find((m) => m.id === o.material);
  const panel = dom.inspectorSelection;
  if (!panel) return;
  panel.innerHTML = `
    <div class="sel-row"><span>id</span><code>${o.id}</code></div>
    <div class="sel-row"><span>type</span><code>${o.type}</code></div>
    <label class="sel-color">color
      <input type="color" id="sel-color" value="${(mat && mat.color) || "#ffffff"}" />
    </label>
    <label class="sel-range">scale x
      <input type="range" id="sel-scale" min="0.1" max="4" step="0.05" value="${(o.scale && o.scale[0]) || 1}" />
    </label>
    <label class="sel-range">opacity
      <input type="range" id="sel-opacity" min="0.1" max="1" step="0.05" value="${(mat && mat.opacity != null) ? mat.opacity : 1}" />
    </label>
    <button id="sel-to-octane" class="sel-action">Send to Octane (quality)</button>
  `;
  panel.querySelector("#sel-color").addEventListener("input", (e) => {
    patchSelection({ material: { color: e.target.value } });
  });
  panel.querySelector("#sel-scale").addEventListener("input", (e) => {
    const s = parseFloat(e.target.value);
    patchSelection({ scale: [s, s, s] });
  });
  panel.querySelector("#sel-opacity").addEventListener("input", (e) => {
    patchSelection({ material: { opacity: parseFloat(e.target.value) } });
  });
  panel.querySelector("#sel-to-octane").addEventListener("click", async () => {
    // Phase 6 handoff: push the live scene to the Octane quality pipeline.
    dom.status.className = "state-queued";
    dom.statusText.textContent = `sending ${o.id} to Octane…`;
    try {
      const res = await postJSON("/canvas/to-octane", {});
      if (!res.ok) {
        console.error("to-octane failed", res.error);
        dom.status.className = "state-error";
        dom.statusText.textContent = `Octane handoff failed: ${(res.error || "").slice(0, 60)}`;
        return;
      }
      dom.status.className = "state-render";
      dom.statusText.textContent = `Octane rendering · ${res.queued_commands} cmds`;
      // Flip to Final so the quality frame shows when it lands.
      setViewMode("final");
    } catch (e) {
      console.error("to-octane error", e);
      dom.status.className = "state-error";
      dom.statusText.textContent = "handoff error";
    }
  });
}

async function patchSelection(changes) {
  if (!state.selectedId) return;
  try {
    const res = await postJSON("/canvas/patch", { object_id: state.selectedId, changes });
    if (!res.ok) {
      console.error("patch failed", res.error);
      return;
    }
    state.currentScene = res.scene;
    if (state.renderer) state.renderer.setScene(res.scene);
  } catch (e) {
    console.error("patch error", e);
  }
}

async function buildScene(intent, plan) {
  dom.status.className = "state-queued";
  dom.statusText.textContent = "building…";
  if (dom.selChip) dom.selChip.classList.add("hidden");
  state.selectedId = null;
  const { promise: buildP } = trackTask(plan ? "load scene" : `build ${intent || ""}`, "build", (signal) =>
    fetch(`${GW}/canvas/build`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(plan ? { scene: plan } : { intent }),
      signal,
    }).then((r) => r.json())
  );
  try {
    const res = await buildP;
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
    if (e && e.name !== "AbortError") {
      dom.status.className = "state-error";
      dom.statusText.textContent = "gateway unreachable";
    }
  }
}

// ---------------------------------------------------------------------------
// Preview polling (Octane quality tier)
// ---------------------------------------------------------------------------
async function pollPreview() {
  if (state.viewMode === "live") {
    // In live-only mode the WebGL canvas owns the screen; don't cover it.
    dom.preview.classList.remove("visible");
    dom.placeholder.style.display = "";
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
      // No Octane frame yet — don't leave a blank/dark block; surface the hint.
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
// ---------------------------------------------------------------------------
// Active task tray + status dots (frontend / backend activity)
// ---------------------------------------------------------------------------
let _frontActive = 0;
let _backActive = 0;

function setFront(active) {
  _frontActive += active ? 1 : -1;
  if (dom.dotFront) dom.dotFront.classList.toggle("active", _frontActive > 0);
}
function setBack(active) {
  _backActive += active ? 1 : -1;
  if (dom.dotBack) dom.dotBack.classList.toggle("active", _backActive > 0);
}

// Wrap a fetch in a cancellable task item with a glowing dot + cancel button.
function trackTask(label, kind, makeFetch) {
  const el = document.createElement("div");
  el.className = `task task-${kind}`;
  el.innerHTML = `<span class="task-dot"></span><span class="task-label">${escapeHtml(label)}</span><button class="task-cancel" title="cancel">✕</button>`;
  if (dom.tasks) dom.tasks.appendChild(el);
  const controller = new AbortController();
  el.querySelector(".task-cancel").addEventListener("click", () => controller.abort());
  const task = { controller, el, label, kind };
  state.activeTask = task;
  const p = makeFetch(controller.signal);
  setFront(kind === "build");
  setBack(true);
  const done = () => {
    el.classList.add("done");
    setTimeout(() => el.remove(), 600);
    if (state.activeTask === task) state.activeTask = null;
    setFront(kind === "build" ? false : false);
    setBack(false);
  };
  p.then(done, (e) => {
    if (e && e.name === "AbortError") {
      el.classList.add("cancelled");
      el.querySelector(".task-label").textContent = `${label} · cancelled`;
    }
    done();
  });
  return { controller, promise: p };
}

// ---------------------------------------------------------------------------
// Scene context summary (what the agent can see/control right now)
// ---------------------------------------------------------------------------
function sceneContext() {
  const sc = state.currentScene;
  if (!sc) return null;
  return {
    scene_id: sc.scene_id || null,
    objects: (sc.objects || []).map((o) => ({
      id: o.id,
      type: o.type,
      label: o.label || null,
      material: o.material || null,
    })),
  };
}

async function submitIntent(text) {
  const raw = (text || "").trim();
  if (!raw) return;
  // Conversation-first contract: the canvas is a natural-language modelling
  // interface. Plain text is design discussion with the agent (no scene
  // change); only an explicit Visualise/Build/Render prefix commits to a build.
  // Recipes (⌘K) are a separate, deliberate instant-load path.
  const buildMatch = raw.match(/^(visuali[sz]e|viz|build|render)\b[:\-\s]*/i);
  const isBuild = !!buildMatch;
  const intent = (buildMatch ? raw.slice(buildMatch[0].length) : raw).trim() || raw;
  const model = (dom.modelSelect && dom.modelSelect.value) || "";
  // Notify the harness of the interpreted intent (for continuity), but only
  // commit a build when the user explicitly asked for one.
  try {
    await fetch(`${GW}/intent`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: raw, voice: !!state.vox }),
    });
    localStorage.setItem("octanex.lastIntent", JSON.stringify({ text: raw, ts: Date.now() }));
  } catch (_) {
    dom.status.className = "state-error";
    dom.statusText.textContent = "dispatch failed";
  }
  if (isBuild) {
    await buildScene(intent);
    appendTranscript("build", `build "${intent}" → ${state.currentScene ? state.currentScene.objects.length : 0} object(s)${state.currentScene && state.currentScene.scene_id ? ` [${state.currentScene.scene_id}]` : ""}`, "octanex-mcp");
  const model = (dom.modelSelect && dom.modelSelect.value) || "";
  // Agentic model query (routed through the Hermes API / proxy). The reply
  // renders in the response line; the turn is logged to the transcript. The
  // agent is prewarmed with the live scene + selected object id (scene-aware),
  // and the whole turn is cancellable via the task tray.
  const scene = sceneContext();
  const selection = state.selectedId || null;
  showResponse("…", model);
  const { promise: chatP } = trackTask(`agent · ${model || "default"}`, "chat", (signal) =>
    fetch(`${GW}/canvas/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: raw, model, voice: !!state.vox, scene, selection }),
      signal,
    }).then((r) => r.json())
  );
  try {
    const res = await chatP;
    if (!res.ok) {
      showResponse(`model offline — ${res.error || "proxy down"}`, model, true);
      return;
    }
    showResponse(res.reply || "(empty)", res.model);
    appendTranscript("user", raw, null);
    appendTranscript("model", res.reply || "(empty)", res.model);
  } catch (e) {
    if (e && e.name === "AbortError") return;
    showResponse("model error — is `hermes proxy` running?", model, true);
  }
}

function showResponse(text, model, isError) {
  if (!dom.response) return;
  dom.response.className = isError ? "" : "";
  dom.response.innerHTML = model
    ? `<span class="resp-model">${model}</span>${escapeHtml(text)}`
    : escapeHtml(text);
  dom.response.classList.remove("hidden");
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
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
    // Pull the recipe catalog from the gateway directly (no MCP server needed).
    try {
      const res = await getJSON("/canvas/recipes");
      const recipes = (res && res.recipes) || [];
      state.paletteItems = Array.isArray(recipes)
        ? recipes.map((r) => ({ slug: r.slug || r.name, label: r.title || r.slug || r.name, meta: r.tier || r.group || "recipe" }))
        : [];
    } catch (_) {
      state.paletteItems = [];
    }
    if (state.paletteItems.length === 0) {
      state.paletteItems = [{ slug: "t1_glossy_cube", label: "Glossy cube (fallback)", meta: "recipe" }];
    }
  }
  const f = (filter || "").toLowerCase();
  const items = state.paletteItems.filter(
    (i) => !f || i.label.toLowerCase().includes(f) || i.slug.toLowerCase().includes(f)
  );
  state.paletteActive = 0;
  dom.paletteList.innerHTML = items
    .map((i, n) => `<li data-slug="${i.slug}" data-label="${i.label}" class="${n === 0 ? "active" : ""}"><span>${i.label}</span><span class="meta">${i.meta}</span></li>`)
    .join("");
  dom.paletteList.querySelectorAll("li").forEach((li) => {
    li.addEventListener("click", () => queueRecipe(li.dataset.slug));
  });
}

async function queueRecipe(slug, label) {
  dom.palette.classList.add("hidden");
  // Recipes are pre-existing scenes: instantiate the recipe's bundled
  // scene.obj as a canvas.scene.v1 and build it into the live WebGL canvas
  // as real, pickable, editable meshes — a starting point for interactive
  // development — rather than a flat preview raster. Quality re-render stays
  // on "Send to Octane".
  dom.status.className = "state-live";
  dom.statusText.textContent = `loading ${slug}…`;
  try {
    const res = await getJSON(`/canvas/recipe/${encodeURIComponent(slug)}`);
    if (!res.ok || !res.scene) {
      dom.status.className = "state-error";
      dom.statusText.textContent = `recipe "${slug}" not found`;
      return;
    }
    await buildScene(null, res.scene);
    setViewMode("live");
    appendTranscript("user", `(recipe) ${label || slug}`, null);
    appendTranscript("model", `Loaded pre-built scene "${res.title || slug}" into the canvas (${res.scene.objects.length} object(s), ready to edit).`, "recipe");
  } catch (e) {
    dom.status.className = "state-error";
    dom.statusText.textContent = "recipe load failed";
  }
}

dom.paletteList.querySelectorAll("li").forEach((li) => {
  li.addEventListener("click", () => queueRecipe(li.dataset.slug, li.dataset.label));
});
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
    if (sel) queueRecipe(sel.dataset.slug, sel.dataset.label);
    return;
  } else if (e.key === "Escape") {
    dom.palette.classList.add("hidden");
    return;
  }
  items.forEach((li, n) => li.classList.toggle("active", n === state.paletteActive));
});

// ---------------------------------------------------------------------------
// ⌘I inspector (preview review + live-object editing, Phase 5)
// ---------------------------------------------------------------------------
async function openInspector() {
  dom.inspector.classList.remove("hidden");
  if (state.selectedId) {
    const meta = state.renderer && state.renderer.objectNodes.get(state.selectedId);
    showSelection(state.selectedId, meta ? meta.meta : null);
  }
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
// Agent model selector (lower-right) — routes the Hermes harness model that
// powers the agentic intent -> scene interaction. Reads the live model list
// from the gateway (sourced from ~/.hermes/config.yaml) and writes the choice
// back so the harness uses it on the next interpretation.
// ---------------------------------------------------------------------------
async function loadModels() {
  try {
    const res = await getJSON("/config/models");
    const sel = dom.modelSelect;
    if (!sel) return;
    sel.innerHTML = "";
    // Group options by provider via <optgroup> so the harness choices read clearly.
    const byProvider = new Map();
    (res.options || []).forEach((m) => {
      const key = m.provider || "default";
      byProvider.set(key, (byProvider.get(key) || []).concat(m));
    });
    for (const [provider, models] of byProvider) {
      const group = document.createElement("optgroup");
      group.label = provider;
      models.forEach((m) => {
        const opt = document.createElement("option");
        opt.value = m.id;
        const caps = m.capabilities || {};
        const tags = [
          m.context_length ? `${(m.context_length / 1024) | 0}k` : null,
          caps.vision ? "vision" : null,
          caps.thinking ? "think" : null,
        ].filter(Boolean).join(" · ");
        // Cloud models the harness can't currently route to (no key) are shown
        // but disabled, so the full Hermes catalog is visible without implying
        // they're usable right now.
        const label = m.id + (m.cloud ? "  ☁" : "") + (tags ? `  (${tags})` : "");
        opt.textContent = label;
        if (m.selectable === false) opt.disabled = true;
        group.appendChild(opt);
      });
      sel.appendChild(group);
    }
    // Selection priority: user's persisted choice (across sessions) > Hermes
    // default from the server. A UI reset clears the persisted choice.
    const saved = localStorage.getItem("octanex.model");
    if (saved && res.options.some((o) => o.id === saved)) {
      sel.value = saved;
    } else if (res.current) {
      sel.value = res.current;
    }
  } catch (e) {
    console.error("loadModels failed", e);
  }
}

async function onModelChange() {
  const id = dom.modelSelect && dom.modelSelect.value;
  if (!id) return;
  // Persist the user's choice so it survives reloads (honored over the server
  // default on next load) until a UI reset clears it.
  localStorage.setItem("octanex.model", id);
  try {
    const res = await postJSON("/config/models", { model: id });
    if (!res.ok) {
      console.error("set model failed", res.error);
      dom.status.className = "state-error";
      dom.statusText.textContent = `model set failed`;
    }
  } catch (e) {
    console.error("set model failed", e);
  }
}

// Reset the model selection to the Hermes default (clears the persisted choice
// so loadModels falls back to the server's current model on next load).
function resetModelSelection() {
  localStorage.removeItem("octanex.model");
  loadModels();
}

// ---------------------------------------------------------------------------
// VOX voice-mode toggle (lower-right). Enables a terser, speech-shaped
// conversation contract for the harness. The flag is persisted locally and
// written into ~/.hermes/config.yaml (vox.enabled) so the harness adopts the
// contract on the next interpretation. Speech I/O itself is wired later.
// ---------------------------------------------------------------------------
async function loadVox() {
  try {
    const res = await getJSON("/config/vox");
    state.contract = res.contract || "";
    // User's persisted choice wins across sessions; else the server default.
    const saved = localStorage.getItem("octanex.vox");
    state.vox = saved !== null ? saved === "1" : !!res.enabled;
    applyVox();
  } catch (e) {
    console.error("loadVox failed", e);
  }
}

function applyVox() {
  if (!dom.voxToggle) return;
  dom.voxToggle.setAttribute("aria-pressed", state.vox ? "true" : "false");
  dom.voxToggle.title = state.vox
    ? "VOX on — terse voice contract. Click to disable."
    : "VOX off — click to enable terse voice mode.";
  // Hint the conversation register in the command bar.
  dom.cmd.placeholder = state.vox
    ? "speak… or type (VOX: terse mode)"
    : "discuss the design, or 'visualise …' / ⌘K to build…";
}

async function onVoxToggle() {
  state.vox = !state.vox;
  localStorage.setItem("octanex.vox", state.vox ? "1" : "0");
  applyVox();
  try {
    const res = await postJSON("/config/vox", { enabled: state.vox });
    if (!res.ok) {
      console.error("set vox failed", res.error);
      dom.status.className = "state-error";
      dom.statusText.textContent = "vox set failed";
    }
  } catch (e) {
    console.error("vox error", e);
  }
}

// ---------------------------------------------------------------------------
// Screenshot -> agent (viewport vision analysis)
// ---------------------------------------------------------------------------
async function snapAndSend() {
  if (!state.renderer) return;
  const image = state.renderer.snapshot(); // PNG data URL
  const model = (dom.modelSelect && dom.modelSelect.value) || "";
  const scene = sceneContext();
  const selection = state.selectedId || null;
  const prompt = dom.cmd.value.trim() || "Analyse this viewport. What geometry, colours, and framing do you see? Flag anything wrong (black faces, clipping, off-centre).";
  dom.cmd.value = "";
  showResponse("… analysing screenshot", model);
  const { promise: snapP } = trackTask("vision · screenshot", "chat", (signal) =>
    fetch(`${GW}/canvas/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: prompt, model, voice: !!state.vox, scene, selection, image }),
      signal,
    }).then((r) => r.json())
  );
  try {
    const res = await snapP;
    if (!res.ok) {
      showResponse(`vision failed — ${res.error || "proxy down"}`, model, true);
      return;
    }
    showResponse(res.reply || "(empty)", res.model);
    appendTranscript("user", `(screenshot) ${prompt}`, null);
    appendTranscript("model", res.reply || "(empty)", res.model);
  } catch (e) {
    if (e && e.name !== "AbortError") showResponse("vision error — is `hermes proxy` running?", model, true);
  }
}


const TRANSCRIPT_KEY = "octanex.transcript";

function loadTranscript() {
  try {
    const raw = localStorage.getItem(TRANSCRIPT_KEY);
    state.transcript = raw ? JSON.parse(raw) : [];
  } catch (_) {
    state.transcript = [];
  }
  renderTranscript();
}

function renderTranscript() {
  if (!dom.transcriptBody) return;
  dom.transcriptBody.innerHTML = (state.transcript || [])
    .map((t) => {
      const who = t.role === "model" ? `model · ${t.model || ""}` : t.role === "build" ? `build · ${t.model || "octanex-mcp"}` : "you";
      return `<div class="turn ${t.role}"><div class="who">${who}</div><div class="body">${escapeHtml(t.text)}</div></div>`;
    })
    .join("");
  dom.transcriptBody.scrollTop = dom.transcriptBody.scrollHeight;
}

function appendTranscript(role, text, model) {
  if (!state.transcript) state.transcript = [];
  state.transcript.push({ role, text, model: model || null });
  // Keep the log bounded but useful across a session.
  if (state.transcript.length > 200) state.transcript = state.transcript.slice(-200);
  localStorage.setItem(TRANSCRIPT_KEY, JSON.stringify(state.transcript));
  renderTranscript();
}

function toggleLog() {
  if (!dom.transcript || !dom.logToggle) return;
  const open = dom.transcript.classList.toggle("hidden") === false;
  dom.logToggle.setAttribute("aria-pressed", open ? "true" : "false");
}

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
