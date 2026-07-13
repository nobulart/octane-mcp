"""Filesystem render scheduler for shared Octane X access.

The Octane X engine is physically single-tenant: one scene graph, one render
target, one drain at a time. The MCP server, the HTTP gateway, hand-rolled
``osascript`` drains, and multiple Hermes agents all converge on the same
container ``ROOT`` (``~/Library/Containers/com.otoy.rndrviewer/Data/OctaneMCP``).
This module turns that shared filesystem into a fair, crash-safe arbiter so
several agents can *share* the engine instead of clobbering each other's
queued commands (the historical ``octane_flush_queue`` behaviour destroyed
other agents' pending work).

Design principles
----------------
* **No new network / no new process model.** Every participant already reads
  and writes ``ROOT``, so the lock and job state live there.
* **Lease + heartbeat, never a bare create-lock.** A dead agent (SIGTERM of the
  controlling drain, Hermes restart, network drop) must not wedge the engine
  forever. A lock is ``stale`` once ``expires_at`` passes with no heartbeat;
  the next contender reclaims it. The killed-drain recovery path is exercised
  in ``tests/test_scheduler.py``.
* **Completion is filesystem-observable, not process-alive.** Job completion is
  signalled by ``jobs/<id>/done.json`` (written by the bridge at the end of a
  pass, or by the dispatcher). The submitter polls that file, never the
  controlling process — which we now know dies mid-render (see the
  ``octane_drain.applescript`` SIGTERM case).
* **Global ``queue/`` is strictly the "currently draining" staging.** The
  dispatcher is the *only* thing that moves a job's commands into ``queue/``
  and triggers a drain. Each job is a complete scene build (build + save),
  namespaced by ``preview_path`` so outputs don't clobber each other.

This module is deliberately Octane-free: all logic is pure filesystem + JSON,
so it can be unit-tested without a running Octane X.
"""

from __future__ import annotations

import datetime
import json
import os
import shutil
import socket
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_LEASE_SECONDS = 300
DEFAULT_HEARTBEAT_SECONDS = 30
LOCK_FILENAME = "render.lock"
JOBS_DIRNAME = "jobs"
QUEUE_DIRNAME = "queue"

__all__ = [
    "SchedulerError",
    "RenderLock",
    "JobScheduler",
    "agent_id",
    "run_drain",
]


class SchedulerError(Exception):
    """Base error for scheduler operations."""


def _iso(t: float) -> str:
    return datetime.datetime.fromtimestamp(t, tz=datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _now_ns() -> int:
    return time.time_ns()


def agent_id() -> str:
    """Stable per-agent identity for the scheduler.

    Each Hermes agent process has its own PID; combine with hostname so the
    render lock can attribute ownership across the mac-studio / macbook-pro
    pair. Override via OCTANEX_AGENT_ID for deterministic multi-agent tests.
    """
    env = os.environ.get("OCTANEX_AGENT_ID")
    if env:
        return env
    host = "unknown"
    try:
        host = socket.gethostname()
    except Exception:
        pass
    return f"{host}:{os.getpid()}"


def run_drain(
    root: Path,
    *,
    timeout_seconds: int = 240,
    preview_path: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Trigger the one-shot Lua bridge drain via AppleScript and poll until the
    global ``queue/`` is empty AND the preview is freshly written (or the
    timeout elapses).

    This is the single shell command the dispatcher uses to drive Octane. It is
    deliberately thin: it shells out to ``scripts/octane_drain.applescript``,
    which performs the Scripts-menu click (never ``run script file``) and the
    fresh-save poll. ``root`` must match the container workspace the bridge
    reads, otherwise the drain acts on the wrong queue.

    Returns the parsed drain result plus ``ok``. On a hard control failure
    (TCC denied, script not found, app down) the AppleScript itself returns a
    non-zero exit; we surface that as ``ok: False`` with the captured error.
    """
    root = Path(root)
    ws = str(root)
    preview = preview_path or (str(root / "renders" / "preview.png"))
    script = Path(__file__).resolve().parents[2] / "scripts" / "octane_drain.applescript"
    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "would_run": [
                "osascript",
                str(script),
                str(timeout_seconds),
                preview,
            ],
            "workspace": ws,
        }
    if not script.exists():
        return {"ok": False, "error": f"drain script missing: {script}"}
    try:
        proc = subprocess.run(
            ["osascript", str(script), str(timeout_seconds), preview],
            capture_output=True,
            text=True,
            timeout=timeout_seconds + 30,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "timed_out": True,
            "error": f"osascript hung after {timeout_seconds + 30}s (Octane busy/modal); the drain was NOT re-clicked.",
        }
    if proc.returncode != 0:
        return {
            "ok": False,
            "returncode": proc.returncode,
            "stderr": (proc.stderr or proc.stdout or "").strip(),
            "error": "hard drain control failure (TCC / script not found / app down).",
        }
    try:
        parsed = json.loads(proc.stdout.strip())
        result: Dict[str, Any] = parsed if isinstance(parsed, dict) else {"raw": proc.stdout.strip()}
    except Exception:
        result: Dict[str, Any] = {"raw": proc.stdout.strip()}
    result["ok"] = bool(result.get("ok", False)) and (proc.returncode == 0)
    return result


# --------------------------------------------------------------------------- #
# Render lock (filesystem lease + heartbeat)
# --------------------------------------------------------------------------- #
class RenderLock:
    """A crash-safe single-owner lock in ``ROOT/render.lock``.

    Acquire is a best-effort compare-and-swap: read the current lock, and only
    claim it if it is absent or stale. The claim is written to a temp file in
    ``ROOT`` then ``os.replace``'d onto the lock path (atomic on the same
    filesystem). We then re-read to confirm we actually own it, because another
    process may have claimed it in the gap.
    """

    def __init__(
        self,
        root: Path,
        agent_id: str,
        *,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
        heartbeat_seconds: int = DEFAULT_HEARTBEAT_SECONDS,
        now=None,
    ) -> None:
        self.root = Path(root)
        self.agent_id = agent_id
        self.lease_seconds = lease_seconds
        self.heartbeat_seconds = heartbeat_seconds
        self._now = now or time.time
        self.lock_path = self.root / LOCK_FILENAME
        self._host = _hostname()

    def _read(self) -> Optional[Dict[str, Any]]:
        if not self.lock_path.exists():
            return None
        try:
            return json.loads(self.lock_path.read_text(encoding="utf-8"))
        except Exception:
            # Corrupt lock file: treat as absent so it gets overwritten.
            return None

    def is_stale(self, lock: Optional[Dict[str, Any]] = None) -> bool:
        lock = self._read() if lock is None else lock
        if lock is None:
            return True
        exp = lock.get("expires_at")
        if exp is None:
            return True
        return self._now() >= float(exp)

    def state(self) -> Dict[str, Any]:
        lock = self._read()
        if lock is None:
            return {"locked": False, "stale": True, "owner": None}
        return {
            "locked": True,
            "stale": self.is_stale(lock),
            "owner_agent_id": lock.get("owner_agent_id"),
            "owner_job_id": lock.get("owner_job_id"),
            "owner_pid": lock.get("owner_pid"),
            "owner_host": lock.get("owner_host"),
            "acquired_at": lock.get("acquired_at"),
            "heartbeat_at": lock.get("heartbeat_at"),
            "expires_at": lock.get("expires_at"),
        }

    def _write_lock(self, job_id: str) -> bool:
        now = self._now()
        payload = {
            "owner_agent_id": self.agent_id,
            "owner_job_id": job_id,
            "owner_pid": os.getpid(),
            "owner_host": self._host,
            "acquired_at": _iso(now),
            "heartbeat_at": _iso(now),
            "expires_at": now + self.lease_seconds,
        }
        tmp = self.lock_path.with_name(f".{self.lock_path.name}.{uuid.uuid4().hex[:8]}.tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        try:
            os.replace(tmp, self.lock_path)
        except Exception:
            if tmp.exists():
                tmp.unlink(missing_ok=True)
            raise
        # Confirm ownership (another process may have claimed in the gap).
        cur = self._read()
        if cur is None:
            return False
        return (
            cur.get("owner_job_id") == job_id
            and cur.get("owner_agent_id") == self.agent_id
        )

    def acquire(
        self,
        job_id: str,
        *,
        max_retries: int = 5,
        retry_pause: float = 0.02,
    ) -> bool:
        """Claim the lock for ``job_id``. Returns True only if we own it.

        A live lock held by someone else (not stale) is a no-go. A lock we
        already hold is simply refreshed.
        """
        for _ in range(max_retries):
            lock = self._read()
            if lock is not None and not self.is_stale(lock):
                if (
                    lock.get("owner_job_id") == job_id
                    and lock.get("owner_agent_id") == self.agent_id
                ):
                    return self.refresh()
                return False
            if self._write_lock(job_id):
                return True
            time.sleep(retry_pause)
        return False

    def refresh(self) -> bool:
        """Extend our own lease (heartbeat). No-op if we don't own it."""
        lock = self._read()
        if lock is None or lock.get("owner_agent_id") != self.agent_id:
            return False
        now = self._now()
        lock["heartbeat_at"] = _iso(now)
        lock["expires_at"] = now + self.lease_seconds
        tmp = self.lock_path.with_name(f".{self.lock_path.name}.{uuid.uuid4().hex[:8]}.tmp")
        tmp.write_text(json.dumps(lock, indent=2), encoding="utf-8")
        try:
            os.replace(tmp, self.lock_path)
        except Exception:
            if tmp.exists():
                tmp.unlink(missing_ok=True)
            raise
        return True

    def release(self) -> bool:
        """Release only if we own the lock. Returns True if now free."""
        lock = self._read()
        if lock is None:
            return True
        if lock.get("owner_agent_id") != self.agent_id:
            return False
        self.lock_path.unlink(missing_ok=True)
        return True

    def force_break(self) -> bool:
        """Break the lock unconditionally (used during stale reclaim)."""
        self.lock_path.unlink(missing_ok=True)
        return True


# --------------------------------------------------------------------------- #
# Job scheduler
# --------------------------------------------------------------------------- #
class JobScheduler:
    """Manages per-agent jobs under ``ROOT/jobs/<job_id>/`` and promotes them
    onto the single global ``queue/`` under lock protection.
    """

    def __init__(
        self,
        root: Path,
        agent_id: str,
        *,
        lock: Optional[RenderLock] = None,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
        now=None,
    ) -> None:
        self.root = Path(root)
        self.agent_id = agent_id
        self._now = now or time.time
        self.jobs_dir = self.root / JOBS_DIRNAME
        self.queue_dir = self.root / QUEUE_DIRNAME
        self.lock = lock or RenderLock(
            self.root, agent_id, lease_seconds=lease_seconds, now=self._now
        )
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.queue_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_defaults(
        cls,
        agent_id: str,
        *,
        now=None,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
    ) -> "JobScheduler":
        from .config import resolve_config

        return cls(resolve_config().workspace, agent_id, now=now, lease_seconds=lease_seconds)

    # -- job submission ----------------------------------------------------- #
    def submit(
        self,
        commands: List[Dict[str, Any]],
        *,
        agent_id: Optional[str] = None,
        preview_path: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> str:
        """Stage a job (a complete scene build) and return its job_id.

        ``commands`` is a list of command envelopes, each either a full object
        with ``op``/``payload`` or a dict that already carries ``op`` at the top
        level. The staged files live under ``jobs/<id>/commands/`` — never in
        the global ``queue/`` until dispatched.
        """
        agent_id = agent_id or self.agent_id
        job_id = job_id or f"{_now_ns()}-{uuid.uuid4().hex[:8]}"
        job_dir = self.jobs_dir / job_id
        cmd_dir = job_dir / "commands"
        job_dir.mkdir(parents=True, exist_ok=True)
        cmd_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "schema_version": "1.0",
            "job_id": job_id,
            "agent_id": agent_id,
            "submitted_at": _iso(self._now()),
            "status": "queued",
            "preview_path": preview_path,
            "done_path": None,
            "error": None,
        }
        for i, cmd in enumerate(commands):
            env = self._command_envelope(cmd, i)
            self._atomic_write(cmd_dir / f"{env['id']}.json", json.dumps(env, indent=2))
        self._atomic_write(job_dir / "manifest.json", json.dumps(manifest, indent=2))
        return job_id

    def submit_pending_queue(
        self,
        *,
        agent_id: Optional[str] = None,
        preview_path: Optional[str] = None,
    ) -> Optional[str]:
        """Adopt whatever is currently in the global ``queue/`` into a new job.

        Migration bridge for the existing pipeline: tools still call
        ``write_command`` (which writes into global ``queue/``), so a controller
        can stage normally, then ``submit_pending_queue`` to wrap those commands
        in a job and clear the global queue. Returns the new job_id, or None if
        the queue was empty.
        """
        files = self.pending_queue_files()
        if not files:
            return None
        commands: List[Dict[str, Any]] = []
        for f in files:
            try:
                commands.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                pass
        if not commands:
            return None
        job_id = self.submit(commands, agent_id=agent_id, preview_path=preview_path)
        for f in files:
            f.unlink(missing_ok=True)
        return job_id

    # -- inspection --------------------------------------------------------- #
    def list_jobs(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        if not self.jobs_dir.exists():
            return out
        for d in sorted(self.jobs_dir.iterdir()):
            if not d.is_dir():
                continue
            m = d / "manifest.json"
            if m.exists():
                try:
                    out.append(json.loads(m.read_text(encoding="utf-8")))
                except Exception:
                    out.append({"job_id": d.name, "status": "unknown"})
        return out

    def get_manifest(self, job_id: str) -> Optional[Dict[str, Any]]:
        p = self.jobs_dir / job_id / "manifest.json"
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def queued_jobs(self) -> List[Dict[str, Any]]:
        jobs = [j for j in self.list_jobs() if j.get("status") == "queued"]
        jobs.sort(key=lambda j: j.get("submitted_at", ""))
        return jobs

    def pending_queue_files(self) -> List[Path]:
        if not self.queue_dir.exists():
            return []
        return sorted(self.queue_dir.glob("*.json"))

    def is_done(self, job_id: str) -> bool:
        return (self.jobs_dir / job_id / "done.json").exists()

    def active_job_without_done(self) -> Optional[str]:
        for j in self.list_jobs():
            if j.get("status") == "active" and not self.is_done(j["job_id"]):
                return j["job_id"]
        return None

    # -- dispatch (the only path that owns the global queue + lock) --------- #
    def dispatch_cycle(
        self,
        *,
        max_retries: int = 5,
        retry_pause: float = 0.02,
    ) -> Optional[str]:
        """Reclaim a stale lock, repair any orphaned job, and promote the oldest
        queued job onto the global ``queue/`` (acquiring the lock).

        Invariant: the global ``queue/`` holds copies of exactly ONE job's
        commands at a time (the active one). Commands are COPIED into ``queue/``
        so the job dir remains the source of truth if the controller dies.

        Returns the promoted job_id (now draining) or None if the engine is busy
        (live lock held by someone else), or there is nothing queued.
        """
        # 1) Engine busy if a live lock is held by someone else.
        if not self.lock.is_stale():
            return None

        # 2) Stale/absent lock -> reclaim and repair any orphaned job.
        self.lock.force_break()
        orphan = self.active_job_without_done()
        if orphan:
            self._requeue_orphan(orphan)

        # 3) Any stragglers left in queue/ belong to a (now requeued) orphan or
        #    a partial drain; sweep them back into their owning job dir so we
        #    never promote on top of someone else's commands.
        for f in self.pending_queue_files():
            owner = self._job_for_queue_file(f)
            dest = (self.jobs_dir / owner / "commands" / f.name) if owner else (self.jobs_dir / "unclaimed" / "commands" / f.name)
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.replace(f, dest)
            except Exception:
                pass

        queued = self.queued_jobs()
        if not queued:
            return None

        next_job = queued[0]["job_id"]
        if not self._promote(next_job):
            return None
        if not self.lock.acquire(next_job, max_retries=max_retries, retry_pause=retry_pause):
            # Lost the race for the lock; roll the job back to queued.
            self._requeue_orphan(next_job)
            return None
        return next_job

    def dispatch_and_drain(
        self,
        *,
        timeout_seconds: int = 240,
        max_retries: int = 5,
        retry_pause: float = 0.02,
    ) -> Dict[str, Any]:
        """The single end-to-end render path for the shared engine.

        Promotes the oldest queued job under the lock, triggers the one-shot
        Lua drain (via ``run_drain``), then writes ``jobs/<id>/done.json`` so
        completion is filesystem-observable even if THIS process is SIGTERM'd
        mid-render. On a hard drain-control failure the job is marked failed
        and the lock released so the next agent can retry.

        Returns a dict: {promoted_job_id, drain, done, lock}.
        """
        job_id = self.dispatch_cycle(max_retries=max_retries, retry_pause=retry_pause)
        if job_id is None:
            return {
                "promoted_job_id": None,
                "drain": None,
                "done": None,
                "lock": self.lock.state(),
                "note": "engine busy or nothing queued",
            }
        manifest = self.get_manifest(job_id) or {}
        preview_path = manifest.get("preview_path")
        drain = run_drain(self.root, timeout_seconds=timeout_seconds, preview_path=preview_path)
        outputs: List[str] = []
        if drain.get("ok"):
            if preview_path:
                outputs.append(preview_path)
            done = self.mark_done(job_id, outputs=outputs)
        else:
            err = drain.get("error") or "drain failed"
            done = self.mark_done(job_id, error=err)
        return {
            "promoted_job_id": job_id,
            "drain": drain,
            "done": done,
            "lock": self.lock.state(),
        }

    def _job_for_queue_file(self, f: Path) -> Optional[str]:
        """Best-effort: identify which job a stray queue file belongs to by
        matching its filename against staged command filenames."""
        name = f.name
        if not self.jobs_dir.exists():
            return None
        for d in self.jobs_dir.iterdir():
            if not d.is_dir():
                continue
            cmd_dir = d / "commands"
            if cmd_dir.exists() and (cmd_dir / name).exists():
                return d.name
        return None

    def mark_done(
        self,
        job_id: str,
        *,
        outputs: Optional[List[str]] = None,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record job completion (filesystem-observable). Releases the lock if
        we own it for this job."""
        job_dir = self.jobs_dir / job_id
        done = {
            "schema_version": "1.0",
            "job_id": job_id,
            "completed_at": _iso(self._now()),
            "outputs": outputs or [],
            "error": error,
            "ok": error is None,
        }
        self._atomic_write(job_dir / "done.json", json.dumps(done, indent=2))

        manifest = self.get_manifest(job_id) or {"job_id": job_id, "agent_id": self.agent_id}
        manifest["status"] = "failed" if error else "done"
        manifest["done_path"] = str(job_dir / "done.json")
        if error:
            manifest["error"] = error
        self._atomic_write(job_dir / "manifest.json", json.dumps(manifest, indent=2))

        st = self.lock.state()
        if st.get("owner_job_id") == job_id and st.get("owner_agent_id") == self.agent_id:
            self.lock.release()
        return done

    # -- internals ---------------------------------------------------------- #
    def _command_envelope(self, cmd: Dict[str, Any], index: int) -> Dict[str, Any]:
        payload = cmd.get("payload")
        if payload is None:
            # Allow a flat {"op": ..., "x": ...} dict to become the payload.
            payload = {k: v for k, v in cmd.items() if k not in ("id", "op", "schema_version", "created_at", "source")}
        op = cmd.get("op") or (payload or {}).get("op")
        if not op:
            raise SchedulerError(f"command missing op: {cmd!r}")
        return {
            "schema_version": "1.0",
            "id": cmd.get("id") or f"{_now_ns()}-{index:04d}-{uuid.uuid4().hex[:6]}",
            "op": op,
            "payload": payload or {},
            "created_at": _iso(self._now()),
            "source": "octanex-scheduler",
        }

    def _atomic_write(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex[:8]}.tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)

    def _promote(self, job_id: str) -> bool:
        """Copy a queued job's commands into the global ``queue/`` and mark it
        active. We COPY (not move) because once the Lua bridge drains
        ``queue/`` the files decouple from the job: if the controller then dies
        mid-render with no ``done.json``, the job dir is the only source of
        truth to re-promote from. Returns False if the job has no commands."""
        cmd_dir = self.jobs_dir / job_id / "commands"
        files = sorted(cmd_dir.glob("*.json")) if cmd_dir.exists() else []
        if not files:
            return False
        for f in files:
            shutil.copyfile(f, self.queue_dir / f.name)
        m = self.get_manifest(job_id) or {"job_id": job_id, "agent_id": self.agent_id}
        m["status"] = "active"
        m["activated_at"] = _iso(self._now())
        m["active_by"] = self.agent_id
        self._atomic_write(self.jobs_dir / job_id / "manifest.json", json.dumps(m, indent=2))
        return True

    def _requeue_orphan(self, job_id: str) -> None:
        """Roll a job whose commands are no longer in ``queue/`` (drained by the
        bridge, controller died) back to queued.

        The job dir's ``commands/`` is the source of truth — but if any
        stragglers remain in the global ``queue/`` (e.g. a partial drain) we
        sweep them back into the job dir first, then re-copy into ``queue/``.
        Status is set back to ``queued`` so ``dispatch_cycle`` will re-promote.
        """
        cmd_dir = self.jobs_dir / job_id / "commands"
        cmd_dir.mkdir(parents=True, exist_ok=True)
        # Sweep global-queue stragglers (partial drain) back into the job dir.
        for f in self.pending_queue_files():
            try:
                os.replace(f, cmd_dir / f.name)
            except Exception:
                pass
        m = self.get_manifest(job_id) or {"job_id": job_id, "agent_id": self.agent_id}
        m["status"] = "queued"
        m["error"] = None
        m.pop("activated_at", None)
        m.pop("active_by", None)
        self._atomic_write(self.jobs_dir / job_id / "manifest.json", json.dumps(m, indent=2))
        # Re-promote from the job dir (source of truth) — re-copy into queue/.
        files = sorted(cmd_dir.glob("*.json"))
        for f in files:
            shutil.copyfile(f, self.queue_dir / f.name)


def _hostname() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return "unknown"


class DispatchLoop:
    """Crash-safe background driver that serves the shared Octane queue.

    A single long-lived loop (or a cron invocation of ``tick``) repeatedly calls
    ``JobScheduler.dispatch_and_drain`` so the engine auto-serves every queued
    job in FIFO order. All arbitrage lives in the filesystem lock, so:

    * running the gateway daemon AND a cron ``tick`` can't double-drive Octane —
      the second call finds a live lease and returns ``busy``;
    * a killed loop can't strand a job — the next tick reclaims the stale lease
      and re-promotes from the job's ``commands/`` dir;
    * a job that ends in a hard drain failure is marked ``failed`` and its lock
      released so the next tick retries the following job.

    The loop is intentionally dumb: it holds no in-memory queue, just polls the
    filesystem and sleeps. ``agent_id`` defaults to ``gateway-dispatch`` so its
    lock is attributable to the dispatcher rather than a submitter.
    """

    def __init__(
        self,
        root: Optional[Path] = None,
        *,
        agent_id: Optional[str] = None,
        poll_seconds: float = 15.0,
        drain_timeout: int = 240,
        max_retries: int = 5,
        now=None,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
    ):
        if root is not None:
            self.root = Path(root)
        else:
            from .config import resolve_config

            self.root = resolve_config().workspace
        self.agent_id = agent_id or f"gateway-dispatch@{_hostname()}"
        self.poll_seconds = poll_seconds
        self.drain_timeout = drain_timeout
        self.max_retries = max_retries
        self._now = now
        self.lease_seconds = lease_seconds
        self._stop = False
        self.last_result: Optional[Dict[str, Any]] = None
        self.cycles = 0
        self.errors = 0

    def _sched(self) -> JobScheduler:
        return JobScheduler(
            self.root, self.agent_id, now=self._now, lease_seconds=self.lease_seconds
        )

    def tick(self) -> Dict[str, Any]:
        """One unit of work: dispatch + drain the oldest job (or no-op if busy /
        nothing queued). Returns the scheduler result dict."""
        sched = self._sched()
        try:
            res = sched.dispatch_and_drain(
                timeout_seconds=self.drain_timeout, max_retries=self.max_retries
            )
        except Exception as exc:  # never let one bad job wedge the loop
            self.errors += 1
            res = {"promoted_job_id": None, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
        self.last_result = res
        self.cycles += 1
        return res

    def run(self) -> None:
        """Blocking loop until ``stop()``. Safe to run in a daemon thread."""
        self._stop = False
        while not self._stop:
            self.tick()
            # If the engine is busy or idle, don't spin hot — sleep before retrying.
            if not self._stop:
                time.sleep(self.poll_seconds)

    def stop(self) -> None:
        self._stop = True

    def status(self) -> Dict[str, Any]:
        sched = self._sched()
        return {
            "agent_id": self.agent_id,
            "running": not self._stop,
            "cycles": self.cycles,
            "errors": self.errors,
            "last_result": self.last_result,
            "queue": sched.queued_jobs(),
            "active_without_done": sched.active_job_without_done(),
            "lock": sched.lock.state(),
        }
