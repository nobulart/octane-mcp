---
name: canvas-key-debug
description: Use when ⌘K / ⌘Enter / Ctrl+Enter / plain-Enter or any keyboard shortcut in the OctaneX Agentic Canvas (apps/octanex-canvas/web) stops working, or the canvas loads but handlers are dead with no JS error. Three stacked root causes — stale static cache, missing key fallback, and an ES-module import cycle — and how to fix + verify each.
version: 1.0.0
author: OctaneX MCP contributors
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [octanex, canvas, keyboard, es-modules, cache, debugging]
    related_skills: [octanex-mcp, octane-viz, octanex-coordinate]
---

# Canvas Key Debug — ⌘K / ⌘Enter dead, no JS error

## When to use

The user reports a keyboard regression in the OctaneX Agentic Canvas web bundle
(`apps/octanex-canvas/web/`): ⌘K palette won't open, ⌘Enter/Enter won't submit,
or shortcuts are dead in a **real browser** even though the page loads and there
is no obvious console error. Load this skill *before* guessing — the failure is
almost always one of the three layers below, and they stack.

> **The user tests in a REAL browser and reports regressions sharply.**
> A "passes in headless/synthetic" result is NOT evidence of success. Do not
> blame a real-browser failure on "the automation harness" once he says it fails
> in a proper browser. The two real, repeated root causes are (1) static-cache
> headers and (2) ES-module import cycles — check those FIRST.

## Mental model

Three independent layers can each kill the keyboard without throwing a visible
error:

1. **Static cache** — gateway serves `app.js`/`agent.js`/`state.js` with no
   `Cache-Control`, so the browser runs a STALE bundle where the combos were
   broken. Looks fine, listener attached (in the old file), combos dead.
2. **Key fallback** — handler checks only `e.metaKey` (no `ctrlKey`) and submit
   is gated behind ⌘Enter with no plain-Enter path. Fails on Ctrl setups, IME
   swallow, or headless.
3. **ES-module cycle** — `agent.js` importing from `app.js` (or vice-versa) fails
   at *link time* with `SyntaxError: does not provide an export named 'X'`. This
   wipes the ENTIRE module graph — no handlers attach at all. This was the actual
   killer in the 2026-07-14 incident.

The cycle is the silent one: a link-time `SyntaxError` can be masked if you only
look at runtime console errors after a partial load, or if JS silently allows
duplicate `function` declarations (shadowing) so it doesn't even throw — but the
code path is then wrong/dead.

## Diagnostic order

Check all three, in this order (cheapest + highest-yield first):

### 1. Static cache (gateway)
```bash
curl -s -D - -o /dev/null http://127.0.0.1:8799/app.js | grep -i cache-control
```
- **Expected:** `Cache-Control: no-store` on every static asset (`app.js`,
  `app.css`, `index.html`).
- **If missing:** the browser caches the bundle. Fix `_serve_static` in
  `src/octanex_mcp/gateway.py` to pass `extra_headers={"Cache-Control": "no-store"}`
  into `_send_bytes`. API routes must NOT get `no-store` (only static assets).
- **Verify after fix:** hard reload (Cmd+Shift+R) in the real browser.

### 2. Key fallback (handler hardening)
Open `apps/octanex-canvas/web/app.js`:
- Global shortcut handler: `const mod = e.metaKey || e.ctrlKey;` — NOT just
  `e.metaKey`. ⌘ on macOS, Ctrl on others/headless.
- Cmd-bar submit: `if (e.key === "Enter" && (e.metaKey || e.ctrlKey || !e.shiftKey))`
  — plain Enter submits (not just ⌘/Ctrl+Enter). Always leave a send path.

### 3. ES-module import cycle (the usual silent killer)
Rule: **`app.js`, `agent.js`, `state.js` must form a DAG, never a cycle.**
- Neutral/shared code (`dom`, `state`, `GW`, `getJSON`, `postJSON`, `callTool`,
  `escapeHtml`, `setViewMode`, `pollPreview`, `pollStatus`) lives in `state.js`.
- `agent.js` imports from `state.js` only.
- `app.js` (shell: renderer init, keydown listeners, boot) imports from `state.js`
  + `agent.js`.
- **Never** `import { X } from "./app.js"` inside `agent.js` (or the reverse).
  If a function is needed by both, move it to `state.js`.

```bash
# Cycle guard — must print 0
grep -c 'from "./app.js"' apps/octanex-canvas/web/agent.js
```

If `agent.js` imports from `app.js`:
- Move the shared function into `state.js` (it almost certainly only touches
  `dom`/`state`/`GW` — all already there).
- Update both `agent.js` and `app.js` to import it from `state.js`.
- Then check for **duplicate local definitions**: after moving `setViewMode` out
  of `app.js`, a second `function setViewMode(mode) {...}` may still exist further
  down (e.g. the viewmodes binding block). JS allows duplicate `function`
  declarations, so it won't throw — but it shadows the import and is dead/confusing.
  Remove the local one; the viewmodes click binding should call the imported fn.
  ```bash
  grep -c "function setViewMode" apps/octanex-canvas/web/app.js   # must be 0
  ```

## Verification (real browser required)

Headless/synthetic key-dispatch does NOT reach page listeners in this harness —
you cannot reproduce ⌘K by dispatching a `KeyboardEvent`. So:

1. `node --check` all three modules (syntax).
2. **Browser module-graph load** is the authoritative regression check:
   ```js
   const errs=[];
   window.addEventListener('error',e=>errs.push(e.message+' @ '+e.filename+':'+e.lineno));
   window.addEventListener('unhandledrejection',e=>errs.push('reject: '+(e.reason&&e.reason.message||e.reason)));
   setTimeout(()=>console.log(JSON.stringify({moduleErrors:errs, liveActive:document.querySelector('[data-mode="live"]')?.classList.contains('active')})),700);
   ```
   Require `moduleErrors: []` and `liveActive: true`. A non-empty `moduleErrors`
   with a `does not provide an export named` message = cycle not fixed.
3. Ask the user to confirm in a **real browser** (hard reload first). Do not claim
   fixed until he says so.

## Pitfalls

- **Stale managed gateway:** Hermes may run its own gateway on a different port
  (e.g. 8731) serving possibly-stale code. Verify against the manual gateway
  port (8799) that has the new code. `curl` the port you think is live; if 8731
  is down and 8799 is up, use 8799.
- **Duplicate `function` declarations don't throw** — they shadow. A cycle "fix"
  that leaves a redundant local def is incomplete; remove it (KISS).
- **Don't expand scope** to the 2 pre-existing unrelated Python failures (Lua
  bridge parity + recipe-library count 32 vs 31) when fixing keyboard bugs.
- After any gateway/`octane_lua/` change, restart the gateway so it picks up new
  code (and the `no-store` header means the browser won't re-cache stale JS).

## Fix checklist (commit-shaped)

- [ ] `Cache-Control: no-store` on static assets in `gateway.py` `_serve_static`
- [ ] `mod = e.metaKey || e.ctrlKey` in global shortcut handler
- [ ] plain-Enter submit path in cmd-bar keydown
- [ ] no `from "./app.js"` import in `agent.js` (move shared fns to `state.js`)
- [ ] no duplicate `function setViewMode` (or similar) left in `app.js`
- [ ] `node --check` clean ×3; browser `moduleErrors: []`; user confirms in real browser
