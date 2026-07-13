# Render scheduler — shared Octane X across agents

The Octane X engine is physically single-tenant: one scene graph, one render
target, one drain at a time. The MCP server, the HTTP gateway, hand-rolled
`osascript` drains, and multiple Hermes agents all converge on the same
container `ROOT`
(`~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP`).

This module (`src/octanex_mcp/scheduler.py`) turns that shared filesystem into a
fair, crash-safe arbiter so several agents can *share* the engine instead of
clobbering each other's queued commands (the old `octane_flush_queue`
behaviour destroyed other agents' pending work).

## Design principles
- **No new network / no new process model.** Every participant already reads and
  writes `ROOT`, so the lock + job state live there.
- **Lease + heartbeat, never a bare create-lock.** A dead agent (SIGTERM of the
  controlling drain, Hermes restart, network drop) must not wedge the engine
  forever. A lock is `stale` once `expires_at` passes with no heartbeat; the
  next contender reclaims it. The killed-drain recovery path is exercised in
  `tests/test_scheduler.py`.
- **Completion is filesystem-observable, not process-alive.** Job completion is
  signalled by `jobs/<id>/done.json` (written by the dispatcher / the
  lock-aware `octane_drain.applescript` on a successful drain). The submitter
  polls that file, never the controlling process — which we know dies
  mid-render (the recurring `osascript octane_drain.applescript` SIGTERM case).
- **Global `queue/` is strictly the "currently draining" staging.** The
  dispatcher is the *only* thing that moves a job's commands into `queue/` and
  triggers a drain. Each job is a complete scene build (build + save), namespaced
  by `preview_path` so outputs don't clobber each other.

## On-disk layout (under `ROOT`)
```
render.lock                     # {owner_job_id, owner_agent_id, pid, heartbeat, expires_at}
jobs/<job_id>/
    manifest.json              # {job_id, agent_id, status, commands_path, preview_path, created_at, completed_at?}
    commands/<n>_<op>.json   # source of truth (copied into queue/, never moved)
    done.json                 # completion marker (ok / failed + error)
    notify.json               # (optional) how to alert the submitter
queue/*.json                 # GLOBAL drain staging — at most ONE job's commands at a time
```

## API (Python)
- `RenderLock(root)` — `acquire/release/refresh/force_break/state/is_stale`.
- `JobScheduler(root, agent_id)` — `submit / dispatch_cycle / dispatch_and_drain
  / mark_done / job_status / queued_jobs / active_job_without_done / reclaim`.
- `agent_id()` — `HOSTNAME:PID`, override via `OCTANEX_AGENT_ID`.
- `run_drain(root, *, timeout_seconds, preview_path, dry_run)` — shells out to
  `scripts/octane_drain.applescript`, parses its JSON, surfaces hard failures.

## MCP tools (server.py)
- `octane_submit_job(commands, preview_path, agent_id?)` — enqueue a complete
  scene build. **Never flushes other agents' work.**
- `octane_job_status(job_id)` — `{status, manifest, lock}`.
- `octane_job_queue()` — `{queued, active, lock}` (the lock is the cross-agent
  signal; `octane_render_job` refuses if a live lease is held).
- `octane_dispatch_jobs(max_retries?)` — one-shot promote under the lock.
- `octane_render_job(timeout_seconds?, max_retries?)` — **the SINGLE render
  path**: promote oldest queued job → lock-aware drain → write `done.json`.
  Marks failed + releases the lock on hard drain failure so the next agent retries.

## Drain contract (`scripts/octane_drain.applescript`)
- **Lock-aware**: reads `ROOT/render.lock`; refuses to drive Octane if another
  agent holds a live lease (returns `busy:true`). Without this guard a
  hand-rolled drain could double-drive the engine behind another agent.
- On success writes `jobs/<job_id>/done.json` so completion survives a
  SIGTERM'd controlling process.

## Status / next steps
- **Done (verified offline):** lock + lease + heartbeat + stale reclaim;
  job submit/promote/requeue; `done.json` completion; lock-aware drain;
  `dispatch_and_drain` composer; 15 unit tests + ad-hoc verification.
- **Not yet wired:** a gateway/cron loop driving `dispatch_and_drain` so the
  engine auto-serves the shared queue; live `done.json` emission by the Lua
  bridge (currently only the dispatcher + the lock-aware AppleScript write it).
- **Untested live:** actual `osascript` click + render against running Octane X
  (no live engine in CI); the AppleScript *compiles* and the Python that calls
  it is fully covered.
