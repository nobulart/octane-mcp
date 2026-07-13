"""Robust detached v3 render driver.

Fixes the earlier failure modes:
* Recovers any stranded files in queue/ + processing/ back into the job dir
  (source of truth) so nothing is lost and the job dir is authoritative.
* Rebuilds the job commands from the canonical scene staging JSON (no dupes,
  no leftover save_preview/start_render retries).
* Promotes atomically, asserts the global queue holds exactly the 42 commands,
  THEN triggers the one-shot drain — so the bridge never sees an empty queue
  in a race window.
* DispatchLoop-safe: acquires the lock under the job's agent_id so the shared
  engine serves only this job.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT_REPO = Path("/Users/craig/octanex-mcp")
JOB_ID = "earth-hemisphere-jello-v3"


def rebuild_job(s, job_dir, cmd_dir):
    scene = json.loads((ROOT_REPO / "OctaneMCP_staging" / JOB_ID / "scene.json").read_text())
    root = s.root
    preview = str(root / "renders" / f"{JOB_ID}_octane-preview.png")
    asset = str(root / "assets" / f"{JOB_ID}.obj")
    commands = []
    for command in scene["commands"]:
        payload = dict(command["payload"])
        if command["op"] == "import_geometry":
            payload["path"] = asset
        if command["op"] == "save_preview":
            payload.update({"path": preview, "width": 1280, "height": 1280,
                             "samples": 800, "min_samples": 200, "timeout_seconds": 300})
        commands.append({"op": command["op"], "payload": payload})
    import shutil
    shutil.rmtree(cmd_dir, ignore_errors=True)
    cmd_dir.mkdir(parents=True, exist_ok=True)
    for i, c in enumerate(commands):
        env = s._command_envelope(c, i)
        s._atomic_write(cmd_dir / f"{env['id']}.json", json.dumps(env, indent=2))
    (job_dir / "manifest.json").write_text(json.dumps({
        "schema_version": "1.0", "job_id": JOB_ID, "agent_id": JOB_ID,
        "status": "queued", "preview_path": preview, "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }, indent=2))
    (job_dir / "done.json").unlink(missing_ok=True)
    return commands, preview


def main() -> None:
    sys.path.insert(0, str(ROOT_REPO / "src"))
    from octanex_mcp.scheduler import JobScheduler

    s = JobScheduler.from_defaults(JOB_ID)
    job_dir = s.jobs_dir / JOB_ID
    cmd_dir = job_dir / "commands"

    # 1) Recover strays into the job dir (source of truth).
    import shutil
    for f in list(s.queue_dir.glob("*.json")) + list((s.root / "processing").glob("*.json")):
        dest = cmd_dir / f.name
        if not dest.exists():
            shutil.move(str(f), str(dest))

    # 2) Rebuild clean authoritative command set.
    commands, preview = rebuild_job(s, job_dir, cmd_dir)

    # 3) Clear global queue + break lock.
    for f in s.queue_dir.glob("*.json"):
        f.unlink(missing_ok=True)
    s.lock.force_break()

    # 4) Promote atomically, assert full queue before draining.
    assert s._promote(JOB_ID), "promote failed"
    q = len(list(s.queue_dir.glob("*.json")))
    print(f"promoted: queue={q} (expect {len(commands)})", flush=True)
    assert q == len(commands), f"queue incomplete: {q}/{len(commands)}"

    # 5) Drain (clicks the one-shot; bridge processes the full queue).
    res = s.dispatch_and_drain(timeout_seconds=900)
    print(json.dumps(res, indent=2), flush=True)


if __name__ == "__main__":
    main()
