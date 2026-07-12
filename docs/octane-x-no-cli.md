# Octane X has NO command-line Lua entry point (evidence)

**Date established:** 2026-07-12
**Scope:** Octane X (the macOS GUI app) on this machine — `/Applications/Octane X.app`.
**Bottom line:** You cannot launch Octane X with a Lua script via the command line. There is no `octane --no-gui -s script.lua` equivalent on macOS. The only programmatic Lua surface is Octane X's in-app **Scripts menu** (driven here via `osascript` UI-scripting). This is a *documented product boundary*, not a workaround for a bug.

## Why (binary evidence, inspected 2026-07-12)

| Check | Command | Result |
|---|---|---|
| App bundle declares a URL scheme or file association? | `plutil -p Info.plist` | **No** `CFBundleURLTypes`, **no** `CFBundleDocumentTypes` → no `octane://` URL, no `.lua`/`.orbx` double-click handler |
| Main app binary parses args / runs scripts? | `strings MacOS/Octane\ X` | **Zero** hits for `runScript`, `argv`, `no-gui`, `--script`, `NSAppleEventManager` URL events, `NSProcessInfo` arg use → pure Cocoa/Metal GUI; it does **not** forward `argv` to the engine |
| Engine lib has scripting? | `strings …/octanesdk.framework/Versions/A/octanesdk` | **Yes** — contains `LuaScriptingComponent::runScript(const char*)` and command-line arg parsing (`There was an error parsing the command-line arguments`) |
| Bundled benchmark Lua references no-gui? | `strings …/Resources/octane.dat` | References "no-gui mode" + a command-line result-file param — the *engine internally* supports headless, but the **app** only triggers it from its own GUI benchmark button, not from `argv` |
| Separate `octane` CLI on this Mac? | `mdfind` / `ls /usr/local/bin/octane` | **None** found |

Conclusion: the Lua scripting engine lives inside the `octanesdk` framework, but the **Octane X app shell never exposes it as a CLI entry point**. The app's `main()` does not call `runScript` from argv.

## Critical distinction: Octane X vs OctaneRender Standalone

The `--no-gui -s script.lua` invocation seen in OTOY docs/forums is for **OctaneRender Standalone** (`octane` / `octane.exe`), a *different product*:

```
# OctaneRender Standalone (Linux/Windows) — NOT available on macOS as a CLI
octane --no-gui -s script.lua
```

- OTOY ships **Octane X** (GUI app) for macOS. There is **no Mac command-line standalone**.
- The shared `octanesdk` engine is the same, but only the standalone product's `main()` wires `argv` → `runScript`.
- macOS network-render **daemon nodes** are still launched/controlled from the Octane X GUI — they are not a CLI script surface either.

## Consequences for this project

This is *why* `src/octanex_mcp/bridge_control.py` launches via AppleScript + the Scripts menu (`open -a "Octane X"` then UI-click the bridge), and why the following constraints exist:

- **macOS Accessibility (TCC)** must be granted to the agent-runtime python (the `osascript` caller), not `Hermes.app`.
- Launch is via the **Script** menu (singular), NOT `run script file` (which `-2741`s because AppleScript tries to compile Lua).
- A single one-shot click drains the **entire** queue; the Queue is shared + persistent.
- There is no supported headless/CI path on this Mac — a real GUI session is mandatory for a real render.

## If a CLI path is genuinely needed

Realistic options (none run Octane X itself headless on macOS):

1. **OctaneRender Standalone** on Linux/Windows (or a headless render node / Render Network job) — the `-s script.lua` path.
2. **Render Network / network rendering** — dispatch jobs to a daemon node; the node is still managed from the GUI on Mac.
3. **Stay on the Scripts-menu path** (current design) — it is the supported automation surface for Octane X.
4. *Not available:* `open -a "Octane X" --args <script>` (app ignores argv), `octane://` URL scheme (none registered), double-click-to-run `.lua` (no doc-type handler).
