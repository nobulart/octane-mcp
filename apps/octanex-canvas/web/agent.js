// OctaneX Agentic Canvas — agentic layer.
// Imports the shared dom/state + net helpers, and exposes the agent-facing
// functions (build, recipe load, scene-aware chat, selection, inspector,
// model/VOX selectors, transcript). app.js wires the shell to these.
import { GW, dom, state, callTool, postJSON, getJSON, escapeHtml, debugLog, setViewMode } from "./state.js";

// Selection -> inspector (Phase 5 first cut: editable live object).
export function showSelection(id, meta) {
  state.selectedId = id;
  debugLog("pick", id, meta);
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
      setViewMode("final");
    } catch (e) {
      console.error("to-octane error", e);
      dom.status.className = "state-error";
      dom.statusText.textContent = "handoff error";
    }
  });
}

export function clearSelection() {
  state.selectedId = null;
  if (dom.selChip) dom.selChip.classList.add("hidden");
  if (dom.inspector && !dom.inspector.classList.contains("hidden")) dom.inspector.classList.add("hidden");
  debugLog("pick", "cleared");
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

// --- NL -> scene edit interpreter ------------------------------------------
// The model SHOULD emit `canvas.patch(object_id="...", color="red")` calls in
// its reply (per CANVAS_SOUL). We parse + execute them so "make the roof red"
// actually recolors the WebGL mesh. Some models narrate the edit instead of
// emitting the call, so we also fall back to a lightweight NL parse: if the
// reply contains an action verb + a color + an object id but no explicit
// canvas.patch(...), we synthesize and apply the patch anyway.
const MAT_KEYS = new Set(["color", "opacity", "metalness", "roughness"]);
const ACTION_VERBS = /\b(applied|make|turn|set|change|paint|painted|recolor|recolour|colou?r)\b/i;

function _normalizeColor(v) {
  // The renderer (THREE.Color + EXTRA_COLORS) is the authoritative parser, so
  // we pass the model's color token through verbatim: "vermillion", "#e34234",
  // "rgb(227,66,52)", "hsv(12,0.85,0.89)" all resolve there. No client-side
  // name list to drift out of sync.
  return v;
}

function _parsePatchArgs(inner) {
  const out = {};
  const re = /(\w+)\s*=\s*("([^"]*)"|'([^']*)'|true|false|-?[\d.]+)/g;
  let m;
  while ((m = re.exec(inner))) {
    const k = m[1];
    let val = m[3] !== undefined ? m[3] : m[4] !== undefined ? m[4] : m[2];
    if (val === "true") val = true;
    else if (val === "false") val = false;
    else if (/^-?[\d.]+$/.test(val)) val = parseFloat(val);
    out[k] = val;
  }
  return out;
}

function _extractColor(text) {
  // Capture whatever color token the model wrote; the renderer parses it.
  // Precedence: hsv(...) / #hex / rgb(...) / a color-name word (letters,
  // optional internal hyphen — covers "vermillion", "sky-blue", etc.).
  let m = text.match(/hsv\(\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+\s*\)/i)
    || text.match(/#[0-9a-f]{6}/i)
    || text.match(/rgb\(\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+\s*\)/i)
    || text.match(/\b([a-z]+(?:-[a-z]+)*)\s+(?:colour|color)\b/i) // "sky blue color"
    || text.match(/\b([a-z]+(?:-[a-z]+)*)\b/i);
  if (!m) return null;
  // For the bare-word / "X color" match, return just the color word (strip a
  // trailing "color"/"colour" so we hand the renderer "vermillion", not
  // "vermillion color").
  let tok = m[0].trim().replace(/\s+(colour|color)$/i, "");
  if (/^(the|a|an|roof|columns|temple|mesh|object|it|that|this|model|building|wall|base|structure)$/i.test(tok)) return null;
  return tok;
}

function _extractObjectId(text) {
  let m = text.match(/object_id\s*=\s*["']([^"']+)["']/i)
    || text.match(/@([\w-]+)/)
    || text.match(/\bto\s+['"]([\w-]+)['"]/i)
    || text.match(/['"]([\w-]+_[\w-]+)['"]/);
  return m ? m[1] : null;
}

async function _runPatchCall(inner) {
  const args = _parsePatchArgs(inner);
  const objectId = args.object_id || args.id || state.selectedId;
  if (!objectId) return;
  const changes = {};
  const mat = {};
  for (const [k, v] of Object.entries(args)) {
    if (k === "object_id" || k === "id") continue;
    if (MAT_KEYS.has(k)) mat[k] = k === "color" ? _normalizeColor(v) : v;
    else if (k === "scale") changes.scale = Array.isArray(v) ? v : [v, v, v];
    else changes[k] = v;
  }
  if (Object.keys(mat).length) changes.material = mat;
  try {
    const res = await postJSON("/canvas/patch", { object_id: objectId, changes });
    if (res.ok && res.scene) {
      state.currentScene = res.scene;
      if (state.renderer) state.renderer.setScene(res.scene);
      if (objectId === state.selectedId) showSelection(objectId, null);
      appendTranscript("build", `patch ${objectId}: ${JSON.stringify(changes)}`, "canvas");
      debugLog("patch", objectId, changes);
    }
  } catch (e) {
    console.error("reply patch failed", e);
  }
}

async function applyReplyPatches(reply) {
  const calls = [];
  const re = /canvas\.patch\(\s*([^)]*)\)/g;
  let m;
  while ((m = re.exec(reply))) calls.push(m[1]);

  if (calls.length) {
    for (const inner of calls) await _runPatchCall(inner);
  } else if (state.currentScene && ACTION_VERBS.test(reply)) {
    // NL fallback: model narrated an edit (e.g. "Applied red color to
    // 'ancient-temple_4'") without emitting canvas.patch(...). Synthesize it.
    const color = _extractColor(reply);
    const oid = _extractObjectId(reply) || state.selectedId;
    if (color && oid) await _runPatchCall(`object_id="${oid}", color="${color}"`);
  }

  let cleaned = reply.replace(/canvas\.patch\(\s*[^)]*\)/g, "").trim();
  cleaned = cleaned.replace(/tool_code\s*/gi, "").replace(/print\(\s*f?['"`]|['"`]\s*\)/g, "").trim();
  return cleaned || "(applied scene edit)";
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
    const heard = scene.intent ? `live · ${scene.intent}`.slice(0, 80) : "live preview";
    dom.status.className = "state-ready";
    dom.statusText.textContent = heard;
    if (scene.scene_id) localStorage.setItem("octanex.lastSceneId", scene.scene_id);
    debugLog("scene", `${scene.objects ? scene.objects.length : 0} object(s)${scene.scene_id ? " · " + scene.scene_id : ""}`);
  } catch (e) {
    if (e && e.name !== "AbortError") {
      dom.status.className = "state-error";
      dom.statusText.textContent = "gateway unreachable";
    }
  }
}

// --- Active task tray + status dots (frontend / backend activity) ----------
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
export function trackTask(label, kind, makeFetch) {
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
  debugLog(kind, `start · ${label}`);
  const done = () => {
    el.classList.add("done");
    setTimeout(() => el.remove(), 600);
    if (state.activeTask === task) state.activeTask = null;
    setFront(false);
    setBack(false);
    debugLog(kind, `done · ${label}`);
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

// --- Scene context summary (what the agent can see/control right now) -------
export function sceneContext() {
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

export async function submitIntent(text) {
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
  debugLog("intent", raw, { isBuild });
  if (isBuild) debugLog("build", intent);
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
  // Clear the prompt immediately so the user can queue more prompts while the
  // agent works (the input is already captured in `raw` + logged to transcript).
  dom.cmd.value = "";
  if (isBuild) {
    await buildScene(intent);
    // Camera inheritance: the user's live Three.js viewport angle is the source
    // of truth. Push it to Octane so the render inherits the canvas viewpoint
    // rather than resetting to a recipe default. The bridge set_camera op reads
    // position/target/fov; getCameraState() returns exactly that shape.
    if (state.renderer && typeof state.renderer.getCameraState === "function") {
      const cam = state.renderer.getCameraState();
      if (cam && cam.position && cam.target) {
        try {
          await callTool("octane_set_camera", {
            position: cam.position,
            target: cam.target,
            fov: cam.fov || 45,
          });
          debugLog("camera-inherit", cam);
        } catch (_) {
          debugLog("camera-inherit", "skipped (octane_set_camera unavailable)");
        }
      }
    }
    appendTranscript("build", `build "${intent}" → ${state.currentScene ? state.currentScene.objects.length : 0} object(s)${state.currentScene && state.currentScene.scene_id ? ` [${state.currentScene.scene_id}]` : ""}`, "octanex-mcp");
  }
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
    const cleaned = await applyReplyPatches(res.reply || "(empty)");
    showResponse(cleaned, res.model);
    appendTranscript("user", raw, null);
    appendTranscript("model", cleaned, res.model);
    debugLog("reply", cleaned, res.model);
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

// --- Screenshot -> agent (viewport vision analysis) -------------------------
export async function snapAndSend() {
  if (!state.renderer) return;
  const image = state.renderer.snapshot(); // PNG data URL
  const model = (dom.modelSelect && dom.modelSelect.value) || "";
  const scene = sceneContext();
  const selection = state.selectedId || null;
  const prompt = dom.cmd.value.trim() || "Analyse this viewport. What geometry, colours, and framing do you see? Flag anything wrong (black faces, clipping, off-centre).";
  dom.cmd.value = "";
  debugLog("vision", prompt.slice(0, 80));
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

// --- Agent model selector ----------------------------------------------------
export async function loadModels() {
  try {
    const res = await getJSON("/config/models");
    const sel = dom.modelSelect;
    if (!sel) return;
    sel.innerHTML = "";
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
        const label = m.id + (m.cloud ? "  ☁" : "") + (tags ? `  (${tags})` : "");
        opt.textContent = label;
        if (m.selectable === false) opt.disabled = true;
        group.appendChild(opt);
      });
      sel.appendChild(group);
    }
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

export async function onModelChange() {
  const id = dom.modelSelect && dom.modelSelect.value;
  if (!id) return;
  localStorage.setItem("octanex.model", id);
  debugLog("model", id);
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

export function resetModelSelection() {
  localStorage.removeItem("octanex.model");
  loadModels();
}

// --- VOX voice-mode toggle ---------------------------------------------------
export async function loadVox() {
  try {
    const res = await getJSON("/config/vox");
    state.contract = res.contract || "";
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
  dom.cmd.placeholder = state.vox
    ? "speak… or type (VOX: terse mode)"
    : "discuss the design, or 'visualise …' / ⌘K to build…";
}

export async function onVoxToggle() {
  state.vox = !state.vox;
  localStorage.setItem("octanex.vox", state.vox ? "1" : "0");
  debugLog("vox", state.vox ? "on" : "off");
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

// --- Agent transcript (LOG toggle, right of the chat entry) ------------------
const TRANSCRIPT_KEY = "octanex.transcript";

export function loadTranscript() {
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
  // Newest first: the latest message sits at the top, older ones pushed down.
  const ordered = (state.transcript || []).slice().reverse();
  dom.transcriptBody.innerHTML = ordered
    .map((t) => {
      const who = t.role === "model" ? `model · ${t.model || ""}` : t.role === "build" ? `build · ${t.model || "octanex-mcp"}` : "you";
      const ts = t.ts ? `<span class="ts">${new Date(t.ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}</span>` : "";
      return `<div class="turn ${t.role}"><div class="who">${who}${ts}</div><div class="body">${escapeHtml(t.text)}</div></div>`;
    })
    .join("");
  dom.transcriptBody.scrollTop = 0;
}

export function appendTranscript(role, text, model) {
  if (!state.transcript) state.transcript = [];
  state.transcript.push({ role, text, model: model || null, ts: new Date().toISOString() });
  if (state.transcript.length > 200) state.transcript = state.transcript.slice(-200);
  localStorage.setItem(TRANSCRIPT_KEY, JSON.stringify(state.transcript));
  renderTranscript();
}

export function toggleLog() {
  if (!dom.transcript || !dom.logToggle) return;
  const open = dom.transcript.classList.toggle("hidden") === false;
  dom.logToggle.setAttribute("aria-pressed", open ? "true" : "false");
}

// --- ⌘I inspector (preview review + live-object editing, Phase 5) -----------
export async function openInspector() {
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

// --- ⌘K command palette ------------------------------------------------------
export async function openPalette() {
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

export async function queueRecipe(slug, label) {
  dom.palette.classList.add("hidden");
  dom.status.className = "state-live";
  dom.statusText.textContent = `loading ${slug}…`;
  debugLog("recipe", slug);
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

// Palette + inspector listener bindings (module-eval; DOM is ready).
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
dom.camDist.addEventListener("change", () => applyFix());
dom.inspectorClose.addEventListener("click", () => dom.inspector.classList.add("hidden"));
