---
name: octanex-coordinate
description: Use when two Hermes instances (MacBook Pro / Mac Studio) are working the octanex-mcp repo and need to stay in sync — autonomous push-notify + pull-rebase coordination loop, conflict prevention, and fast merge resolution.
version: 1.0.0
author: OctaneX MCP contributors
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [octanex, coordination, git, tcc, multi-agent, blackboard]
    related_skills: [octanex-mcp, octanex-mcp-overview]
---

# octanex-coordinate — autonomous inter-instance sync

Two Hermes instances (MacBook Pro `macbook-pro` / Mac Studio `mac-studio`) keep
each other informed in near-real-time so merges and conflict resolutions are fast
and need no manual handoff. Built on `~/hermes-bridge` file channel + keyless SSH.

## When to use
- Both instances editing `octanex-mcp` (or any shared repo with this loop installed).
- At the START of a session, and on every push.

## Components (`scripts/coord/`, deployed on both machines)
| Script | Role |
|---|---|
| `common.sh` | Identity auto-detect, peer resolution, SSH fast-path append, watermark. Sourced. |
| `notify.sh` | Build structured `done`/`intent` message from a pushed range (commits + files + verified) → peer inbox over SSH (sub-second) + local outbox. |
| `watch.sh` | Every 2 min (launchd). Pulls peer outbox→inbox, reacts to unseen peer `done`/`intent`: `git fetch`; if tree **clean**, `rebase origin/main` + `ack`; if **dirty**, `blocked` (never rebases, never loses work); on conflict, `--abort` + `blocked`. |
| `intent.sh` | Declare files you'll touch this session (`intent` message) → peer avoids same files. |
| `gitp.sh` | **Canonical push**: `git push && notify`. Use THIS instead of `git push`. |

## Session-start checklist
1. `bash scripts/coord/intent.sh "path1;path2;..."` — declare your scope (conflict prevention).
2. Do your work.
3. `bash scripts/coord/gitp.sh "commit message"` — commits (tracked changes only), pushes, notifies peer.

## Why `gitp.sh` and not `git push`
git's `post-receive` hook (`.git/hooks/post-receive`) fires reliably in an
interactive shell but **does NOT fire through some agent git paths**. `gitp.sh`
does the push + notify explicitly, so notification is deterministic. The hook
remains as a bonus for normal terminals.

## Message schema (one JSON/line in `~/hermes-bridge/{in,out}box.jsonl`)
```json
{"from":"macbook-pro|mac-studio","ts":"…Z","type":"intent|done|note|ack|blocked",
 "repo":"octanex-mcp","branch":"main","commits":["…"],"files":["…"],
 "summary":"…","verified":true,"action":"rebase"}
```
`ack`/`blocked` are non-reactive (watcher ignores them for rebase) — no ack loops.

## Latency budget
- Notify: push → peer inbox ≤1 s (SSH fast-path).
- Absorb: peer `done` → fetch+rebase+ack ≤2 min (watch interval).
- Legacy 15-min `sync.sh` is a fallback for the outbox→inbox path.

## Resolving a conflict
If both edited the same file, the peer's watcher sends `blocked` (its tree is
dirty / rebase conflicted) — **do NOT force-rebase the peer**. Either:
- Coordinate via an `intent` message to split the file, or
- The peer resolves its own tree, then `gitp.sh` re-notifies and the loop converges.

## Gotchas (learned 2026-07-10)
- `coord_append_peer` writes directly to the peer's inbox over SSH; the watcher
  reacts to ALL unseen inbox lines (`.coord_seen`), NOT the outbox-pull count —
  the pull dedup sees fast-path-delivered lines as "already there".
- `coord_is_dirty` treats untracked files as dirty → watcher `blocked`. Keep the
  working tree clean (commit coord scripts) so auto-rebase can run.
- Hook uses `$0` (not `BASH_SOURCE`) — git runs hooks via `sh` where `BASH_SOURCE`
  is unset.
