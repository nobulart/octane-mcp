#!/usr/bin/env python3
"""Standalone shared-engine dispatch driver for Octane X.

Two modes:

1. SERVER (default) — a long-lived loop that serves the shared render queue:
       python3 scripts/dispatch_loop.py --poll 15 --drain-timeout 240
   One DispatchLoop owns the engine via the filesystem render.lock. Safe to run
   on mac-studio as a launchd daemon. If a second instance starts, the lock
   makes it a no-op (and the gateway daemon is a separate, also-safe actor).

2. TICK — one unit of work, then exit (cron-friendly):
       python3 scripts/dispatch_loop.py --tick
   A live render.lock (from the server, the gateway daemon, or another tick)
   makes this return `busy` with no render started.

The point: multiple entry points can all call the same dispatch logic; the
filesystem lock is the single arbiter, so the single Octane engine is never
double-driven. Completion is written to jobs/<id>/done.json, so a killed
driver cannot strand a job — the next driver reclaims the stale lease.

Note: this script uses the repo's own venv (not the Hermes runtime PYTHONPATH),
so it must be run from the repo checkout or with the project venv active.
"""
from __future__ import annotations

import argparse
import json
import sys
import time

# Make the repo importable when run as `python3 scripts/dispatch_loop.py`.
if __name__ == "__main__":
    import pathlib

    _repo = pathlib.Path(__file__).resolve().parents[1]
    if str(_repo) not in sys.path:
        sys.path.insert(0, str(_repo))

from octanex_mcp.scheduler import DispatchLoop  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Octane X shared-engine dispatch driver")
    ap.add_argument("--tick", action="store_true", help="one unit of work, then exit")
    ap.add_argument("--poll", type=float, default=15.0, help="poll seconds (server mode)")
    ap.add_argument("--drain-timeout", type=int, default=240, help="per-job drain timeout")
    ap.add_argument("--max-retries", type=int, default=5)
    ap.add_argument("--once", action="store_true", help="server mode: run a single tick then exit")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON, not logs")
    args = ap.parse_args()

    loop = DispatchLoop(
        poll_seconds=args.poll,
        drain_timeout=args.drain_timeout,
        max_retries=args.max_retries,
    )

    if args.tick or args.once:
        res = loop.tick()
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            jid = res.get("promoted_job_id")
            note = res.get("note", "")
            print(f"[tick] promoted={jid} ok={res.get('ok')} {note}")
        return 0 if res.get("ok") or jid is None else 1

    # Server mode.
    if not args.json:
        print(f"[dispatch] serving shared queue (poll={args.poll}s, drain={args.drain_timeout}s)")
    try:
        while True:
            res = loop.tick()
            if args.json:
                print(json.dumps({"event": "tick", **res}, flush=True))
            else:
                jid = res.get("promoted_job_id")
                if jid is not None:
                    ok = (res.get("done") or {}).get("ok")
                    print(f"[dispatch] job={jid} done_ok={ok}")
                time.sleep(args.poll)
    except KeyboardInterrupt:
        if not args.json:
            print("\n[dispatch] stopped")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
