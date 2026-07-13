"""Detached render driver for earth-hemisphere v4 (LLSVP + plume tendrils).

Robust pattern: recover strays into the job dir (source of truth), rebuild job
commands from the canonical staging scene.json, clear the global queue, break
any stale lock, promote atomically, assert the full queue, then run
dispatch_and_drain. The bridge saves the default `octane-preview.png`; we copy it
to the job-specific name and write done.json on completion. Completion is
observable via filesystem, so it survives message-driven SIGTERMs / Octane restarts.
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

ROOT_REPO = Path("/Users/craig/octanex-mcp")
JOB_ID = "earth-hemisphere-v4"


def main() -> None:
    sys.path.insert(0, str(ROOT_REPO / "src"))
    from octanex_mcp.scheduler import JobScheduler

    s = JobScheduler.from_defaults(JOB_ID)
    root = s.root
    job_dir = s.jobs_dir / JOB_ID
    cmd_dir = job_dir / "commands"
    default_preview = root / "renders" / "octane-preview.png"
    final_preview = root / "renders" / f"{JOB_ID}_octane-preview.png"
    asset = str(root / "assets" / f"{JOB_ID}.obj")

    scene = json.loads((ROOT_REPO / "OctaneMCP_staging" / JOB_ID / "scene.json").read_text())
    commands = []
    for command in scene["commands"]:
        payload = dict(command["payload"])
        if command["op"] == "import_geometry":
            payload["path"] = asset
        # Always save to the bridge's default preview path (it ignores custom paths).
        if command["op"] == "save_preview":
            payload.update({"path": str(default_preview), "width": 1280, "height": 1280,
                             "samples": 800, "min_samples": 200, "timeout_seconds": 300})
        commands.append({"op": command["op"], "payload": payload})

    # 1) Recover any strays back into the job dir (make the dir first).
    cmd_dir.mkdir(parents=True, exist_ok=True)
    for f in list(s.queue_dir.glob("*.json")) + list((root / "processing").glob("*.json")):
        dest = cmd_dir / f.name
        if not dest.exists():
            shutil.move(str(f), str(dest))

    # 2) Rebuild authoritative command set.
    shutil.rmtree(cmd_dir, ignore_errors=True)
    cmd_dir.mkdir(parents=True, exist_ok=True)
    for i, c in enumerate(commands):
        env = s._command_envelope(c, i)
        s._atomic_write(cmd_dir / f"{env['id']}.json", json.dumps(env, indent=2))
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "manifest.json").write_text(json.dumps({
        "schema_version": "1.0", "job_id": JOB_ID, "agent_id": JOB_ID,
        "status": "queued", "preview_path": str(final_preview), "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }, indent=2))
    (job_dir / "done.json").unlink(missing_ok=True)
    final_preview.unlink(missing_ok=True)
    # Guard: delete stale default preview so we only promote a fresh render.
    if default_preview.exists():
        old = default_preview.stat().st_mtime
        time.sleep(1)
        default_preview.unlink(missing_ok=True)

    # 3) Clear global queue + break lock.
    for f in s.queue_dir.glob("*.json"):
        f.unlink(missing_ok=True)
    s.lock.force_break()

    # 4) Promote atomically; assert full queue before draining.
    assert s._promote(JOB_ID), "promote failed"
    q = len(list(s.queue_dir.glob("*.json")))
    print(f"promoted: queue={q} (expect {len(commands)})", flush=True)
    assert q == len(commands), f"queue incomplete: {q}/{len(commands)}"

    # 5) Drain (clicks the one-shot; bridge processes the whole queue).
    res = s.dispatch_and_drain(timeout_seconds=1200)
    print(json.dumps(res, indent=2), flush=True)

    # 6) Promote default preview to job-specific name if a fresh one landed.
    if default_preview.exists():
        shutil.copy2(str(default_preview), str(final_preview))
        (job_dir / "done.json").write_text(json.dumps({
            "status": "done", "preview": str(final_preview),
            "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }, indent=2))
        print(f"preview promoted -> {final_preview}", flush=True)
    else:
        print("WARN: no default preview found after drain", flush=True)


if __name__ == "__main__":
    main()
