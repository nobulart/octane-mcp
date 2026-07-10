# Autonomous Coordination Protocol (inter-instance)

Two Hermes instances (MacBook Pro / Mac Studio) keep each other informed in
near-real-time so repository merges and conflict resolutions happen fast and
without manual handoff. Built on the existing `~/hermes-bridge` file channel +
keyless SSH; no external services.

## Components (`scripts/coord/`)

| Script | Role |
|---|---|
| `common.sh` | Identity auto-detect, peer resolution, SSH-fast-path append, watermark. Sourced by the others. |
| `notify.sh` | Builds a structured `done`/`intent` message from a pushed commit range (commits + touched files + verified flag) and delivers it **directly to the peer's inbox over SSH** (sub-second) + our local outbox (redundancy). |
| `watch.sh` | Runs every 2 min (launchd). Pulls peer outbox → inbox, then for each peer `done`/`intent`: `git fetch`; if tree **clean**, `rebase origin/main` and `ack` back; if **dirty**, sends `blocked` (never rebases, never loses work); on rebase conflict, `--abort` + `blocked`. |
| `intent.sh` | Declares files we plan to touch this session (`intent` message) so the peer can avoid the same files (conflict prevention). |

## Git hook

`.git/hooks/post-receive` parses `<old> <new> <ref>` from stdin and calls
`notify.sh --from <old> --to <new> --verified`. Non-fatal: a notify failure
never breaks the push.

## Message schema (one JSON object per line)

```json
{"from":"macbook-pro|mac-studio","ts":"…Z","type":"intent|done|note|ack|blocked",
 "repo":"octanex-mcp","branch":"main","commits":["…"],"files":["…"],
 "summary":"…","verified":true,"action":"rebase"}
```

`ack` / `blocked` are non-reactive (watcher ignores them for rebase) — prevents
ack loops.

## Latency budget

- Notify: push → peer inbox: **≤1 s** (SSH fast-path).
- Absorb: peer `done` → `fetch`+`rebase`+`ack`: **≤2 min** (watch interval).
- (The legacy 15-min `sync.sh` remains as a fallback for the outbox→inbox path.)

## Loop

1. At session start: `bash scripts/coord/intent.sh "path1;path2"` to declare scope.
2. Commit + push normally. `post-receive` auto-notifies the peer.
3. Peer's `watch.sh` auto-rebases if clean and acks. If their tree is dirty,
   they get a `blocked` and resolve manually (no race).
4. Both sides stay within seconds-to-2-min of each other; conflicts are rare
   (declared upfront) and cheap (rebase + ack).

## Setup (per machine)

```sh
# copy scripts + hook (already deployed on both MacBook Pro and mac-studio.local)
chmod +x scripts/coord/*.sh .git/hooks/post-receive
cp scripts/coord/com.nobulart.octanex.coord-watch.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.nobulart.octanex.coord-watch.plist
```

<!-- loop verified 15:02:23Z -->
