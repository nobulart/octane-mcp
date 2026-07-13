# Octane X osascript control toolkit

A set of small, composable, **verifiable** AppleScript primitives for fully
automated agentic control of Octane X on macOS. Octane X has **no CLI Lua
entry point** (`docs/octane-x-no-cli.md`): the only programmatic surface is
UI-scripting its **Script** menu via `System Events`. These scripts drive that
surface.

> **TCC:** macOS Accessibility must be granted to the process that runs
> `osascript` — the Hermes agent-runtime python (or its shell/terminal
> ancestor), **not** `Hermes.app`. After granting or a Hermes update, restart
> Hermes (and the spawning terminal). A live `-1719` means the cached TCC
> token was not refreshed — re-add the grant, then restart.

## The six required on-demand controls

| # | Operation | Script | Notes |
|---|---|---|---|
| 1 | Launch Octane X | `octane_launch.applescript [wait_s]` | Idempotent; waits for menu bar UI-ready. |
| 2 | `File ▸ New` (warm reset) | `octane_reset_scene.applescript` | Clears in-memory scene graph; keeps engine hot. |
| 3 | `Script ▸ hermes_bridge_oneshot.generated` | `octane_run_oneshot.applescript` | Fires the click; one click drains the whole queue. |
| 4 | `Script ▸ hermes_bridge_persistent.generated` | `octane_run_persistent.applescript` | Opens the persistent bridge window (no auto-drain). |
| 5 | Cancel a running script/render | `octane_cancel.applescript` | Sends `Escape` (best-effort). See "Cancellation". |
| 6 | Shutdown Octane X | `octane_shutdown.applescript [--force]` | Graceful `Quit`; `--force` hard-kills. |

## Supporting / composable toolkit

| Script | Purpose |
|---|---|
| `octane_status.applescript` | Print JSON health + live `bridge_status.json`. No side effects. |
| `octane_click_script.applescript <NAME>` | Click any **Script**-menu item by (sub)string. Generalizes #3/#4. |
| `octane_flush_queue.applescript` | Move (never delete) stale `queue/*.json` to a dated backup. |
| `octane_drain.applescript [timeout_s] [preview_path]` | Click one-shot + poll until queue empty + PNG fresh. |
| `relaunch_octane_oneshot.applescript [timeout_s] [preview_path]` | **Cold cycle:** quit → relaunch → click one-shot → poll. |

## Cancellation (important)

Octane X exposes **no "Cancel script" / "Stop" / "Abort" menu item** (verified
by enumerating the full menu bar). The available cancel gestures are:

1. `octane_cancel.applescript` — sends `Escape`, the standard Octane gesture
   for an in-progress render / current operation. **Best-effort**: if a Lua
   script is fully synchronous and blocking the Lua thread, Escape may not
   take effect until the script yields.
2. `octane_shutdown.applescript --force` — hard-kills Octane X when a render
   or script will not yield to Escape. Use as the escalation path, not the
   default (it loses the in-memory scene).

## Drain rule (do not loop)

A single one-shot click drains the **entire** queue. After clicking, poll
`queue/` to 0 — **never re-click on a timer**. A second click while
`save_preview` is mid-render is ignored and kills that render.

## Render-target note (stale claim retired)

The Lua bridge **programmatically activates the render target** before each
render (verified live in `bridge.log`:
`activated render target Hermes Render Target` → `render start requested` →
PNG saved). The old note claiming a *manual* "Hermes Render Target" re-select
is required is **obsolete** — do not reintroduce it.

## Composable workflows

### Warm reset between recipes (preferred — keeps engine hot)
```bash
osascript scripts/octane_launch.applescript
osascript scripts/octane_reset_scene.applescript        # #2 File > New
# ...queue commands via octanex-mcp tools / write_command...
osascript scripts/octane_flush_queue.applescript        # optional: clear stragglers
osascript scripts/octane_drain.applescript              # #3 + wait
```

### Fire a specific bridge on demand
```bash
osascript scripts/octane_launch.applescript
osascript scripts/octane_run_oneshot.applescript        # #3
osascript scripts/octane_run_persistent.applescript     # #4
```

### Cancel / shutdown
```bash
osascript scripts/octane_cancel.applescript             # #5 (best-effort Escape)
osascript scripts/octane_shutdown.applescript --force   # #6 (hard kill, escalation)
osascript scripts/octane_shutdown.applescript           # #6 (graceful)
```

### Cold cycle (bridge patch reload, or wedged session ONLY)
```bash
osascript scripts/relaunch_octane_oneshot.applescript   # quit+relaunch+click+poll
```
Never relaunch between `import_geometry` and `save_preview` — the in-memory
scene is purged and you get a uniform gray (243,243,243) frame.

## Exit-code / output contract
- `octane_launch`, `octane_reset_scene`, `octane_run_oneshot`,
  `octane_run_persistent`, `octane_click_script`: exit 0 on success; non-zero
  (with a classified message) on TCC `-1719`, app-down `-600`, `-2741`, or
  "not found".
- `octane_drain` / `relaunch_octane_oneshot`: **always print a JSON summary to
  stdout and exit 0**; inspect the `"ok"` field for drain success (a timeout is
  reported as `ok:false`, not as a non-zero exit, so it stays machine-parseable).
  They only exit non-zero on a *hard* control failure (click not found / TCC /
  app down).
- `octane_flush_queue` / `octane_status` / `octane_cancel` / `octane_shutdown`:
  exit 0 on a normal outcome; non-zero only on a genuine failure (e.g. graceful
  quit timed out).
