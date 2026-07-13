"""Offline tests for the filesystem render scheduler.

These deliberately do NOT touch Octane X. They exercise the lock (lease +
heartbeat + stale reclaim), job submission/promotion/requeue, and the
killed-drain recovery path — the exact failure mode observed when a hand-rolled
osascript drain was SIGTERM'd mid-render, leaving the global queue drained and
no completion mark.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from octanex_mcp.scheduler import JobScheduler, RenderLock, SchedulerError


class Clock:
    """Controllable clock for deterministic lease/heartbeat tests."""

    def __init__(self, t: float = 1_000_000.0):
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


def sample_commands() -> list[dict]:
    return [
        {"op": "import_geometry", "payload": {"path": "/x/a.obj", "name": "a"}},
        {"op": "set_camera", "payload": {"position": [1, 2, 3], "target": [0, 0, 0]}},
        {"op": "save_preview", "payload": {"path": "/out/a.png"}},
    ]


class TestRenderLock(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.clock = Clock()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_acquire_and_own(self):
        lock = RenderLock(self.root, "agentA", now=self.clock)
        self.assertTrue(lock.acquire("job1"))
        self.assertTrue(lock.lock_path.exists())
        st = lock.state()
        self.assertTrue(st["locked"])
        self.assertFalse(st["stale"])
        self.assertEqual(st["owner_job_id"], "job1")

    def test_acquire_refresh_lease(self):
        lock = RenderLock(self.root, "agentA", lease_seconds=100, now=self.clock)
        lock.acquire("job1")
        self.clock.advance(80)
        self.assertFalse(lock.is_stale())
        self.assertTrue(lock.refresh())
        exp = lock.state().get("expires_at")
        self.assertEqual(exp, self.clock() + 100)

    def test_live_lock_blocks_other_agent(self):
        la = RenderLock(self.root, "agentA", lease_seconds=100, now=self.clock)
        lb = RenderLock(self.root, "agentB", lease_seconds=100, now=self.clock)
        self.assertTrue(la.acquire("job1"))
        self.assertFalse(lb.acquire("job2"))  # owned by A, not stale
        st = lb.state()
        self.assertTrue(st["locked"])
        self.assertFalse(st["stale"])
        self.assertEqual(st["owner_agent_id"], "agentA")

    def test_stale_lock_reclaimed(self):
        la = RenderLock(self.root, "agentA", lease_seconds=50, now=self.clock)
        lb = RenderLock(self.root, "agentB", lease_seconds=50, now=self.clock)
        la.acquire("job1")
        self.clock.advance(60)  # past A's lease
        self.assertTrue(lb.acquire("job2"))
        st = lb.state()
        self.assertTrue(st["stale"] is False)
        self.assertEqual(st["owner_agent_id"], "agentB")

    def test_release_only_own(self):
        la = RenderLock(self.root, "agentA", lease_seconds=100, now=self.clock)
        lb = RenderLock(self.root, "agentB", lease_seconds=100, now=self.clock)
        la.acquire("job1")
        self.assertFalse(lb.release())  # not owner
        self.assertTrue(la.release())
        self.assertFalse(la.lock_path.exists())

    def test_no_false_claim_on_race(self):
        la = RenderLock(self.root, "agentA", lease_seconds=1000, now=self.clock)
        lb = RenderLock(self.root, "agentB", lease_seconds=1000, now=self.clock)
        a = la.acquire("jobA")
        b = lb.acquire("jobB")
        data = json.loads((self.root / "render.lock").read_text())
        self.assertEqual(data["owner_agent_id"], (la.state()["owner_agent_id"]))
        self.assertTrue(a ^ b)  # exactly one True

    def test_corrupt_lock_treated_as_absent(self):
        (self.root / "render.lock").write_text("{not valid json", encoding="utf-8")
        lock = RenderLock(self.root, "agentA", now=self.clock)
        self.assertTrue(lock.is_stale())
        self.assertTrue(lock.acquire("job1"))


class TestJobScheduler(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.clock = Clock()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _sched(self, agent: str = "agentA") -> JobScheduler:
        return JobScheduler(self.root, agent, now=self.clock, lease_seconds=100)

    def _manifest(self, s: JobScheduler, job_id: str) -> dict:
        m = s.get_manifest(job_id)
        assert m is not None, "manifest missing for " + job_id
        return m

    def test_submit_stages_commands_not_in_global_queue(self):
        s = self._sched()
        jid = s.submit(sample_commands(), preview_path="/out/a.png")
        assert jid is not None
        cmds = list((self.root / "jobs" / jid / "commands").glob("*.json"))
        self.assertEqual(len(cmds), 3)
        self.assertEqual(s.pending_queue_files(), [])
        m = self._manifest(s, jid)
        self.assertEqual(m["status"], "queued")
        self.assertEqual(m["preview_path"], "/out/a.png")

    def test_dispatch_promotes_oldest_job_under_lock(self):
        s = self._sched()
        j1 = s.submit(sample_commands(), preview_path="/out/1.png")
        j2 = s.submit(sample_commands(), preview_path="/out/2.png")
        promoted = s.dispatch_cycle()
        self.assertEqual(promoted, j1)
        self.assertEqual(len(s.pending_queue_files()), 3)
        self.assertEqual(self._manifest(s, j1)["status"], "active")
        self.assertEqual(self._manifest(s, j2)["status"], "queued")
        self.assertEqual(s.lock.state()["owner_job_id"], j1)

    def test_dispatch_busy_when_live_lock_held_by_other(self):
        sa = self._sched("agentA")
        sb = self._sched("agentB")
        sa.submit(sample_commands())
        sa.dispatch_cycle()
        self.assertIsNone(sb.dispatch_cycle())
        self.assertEqual(sb.pending_queue_files(), sa.pending_queue_files())

    def test_mark_done_releases_lock(self):
        s = self._sched()
        jid = s.submit(sample_commands())
        assert jid is not None
        s.dispatch_cycle()
        self.assertTrue(s.lock.lock_path.exists())
        s.mark_done(jid, outputs=["/out/a.png"])
        self.assertTrue(s.is_done(jid))
        self.assertEqual(self._manifest(s, jid)["status"], "done")
        self.assertFalse(s.lock.lock_path.exists())

    def test_killed_drain_recovery(self):
        """Simulates the observed SIGTERM case: controller dies while the job
        is active (queue drained, no done.json), lock left to go stale.

        A later dispatcher must reclaim the stale lock, roll the job's commands
        back into its staging, and re-promote it (and complete it).
        """
        s = self._sched("agentA")
        jid = s.submit(sample_commands(), preview_path="/out/a.png")
        assert jid is not None
        s.dispatch_cycle()  # copies commands into queue/, marks active, takes lock
        # Commands are COPIED (job dir is source of truth), so the global queue
        # now holds the active job's 3 commands.
        self.assertEqual(len(s.pending_queue_files()), 3)
        self.assertEqual(self._manifest(s, jid)["status"], "active")
        self.assertFalse(s.is_done(jid))

        # Time passes; controller was SIGTERM'd -> lock goes stale, no done.
        self.clock.advance(200)

        s2 = self._sched("agentB")
        reclaimed = s2.dispatch_cycle()
        self.assertEqual(reclaimed, jid)  # same job re-promoted
        self.assertEqual(len(s2.pending_queue_files()), 3)  # rolled back + promoted
        self.assertEqual(self._manifest(s2, jid)["status"], "active")
        self.assertEqual(s2.lock.state()["owner_agent_id"], "agentB")

        s2.mark_done(jid, outputs=["/out/a.png"])
        self.assertTrue(s2.is_done(jid))
        self.assertEqual(self._manifest(s2, jid)["status"], "done")

    def test_pending_queue_adoption(self):
        """Tools still call write_command (global queue). submit_pending_queue
        must wrap those commands in a job and clear the global queue."""
        for i, c in enumerate(sample_commands()):
            p = self.root / "queue" / f"cmd_{i}.json"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps({**c, "id": f"c{i}"}, indent=2))
        s = self._sched()
        jid = s.submit_pending_queue(preview_path="/out/adopted.png")
        assert jid is not None
        self.assertEqual(s.pending_queue_files(), [])
        cmds = list((self.root / "jobs" / jid / "commands").glob("*.json"))
        self.assertEqual(len(cmds), 3)
        self.assertEqual(self._manifest(s, jid)["preview_path"], "/out/adopted.png")

    def test_command_envelope_from_flat_dict(self):
        s = self._sched()
        jid = s.submit([{"op": "ping", "message": "hi"}])
        assert jid is not None
        files = list((self.root / "jobs" / jid / "commands").glob("*.json"))
        self.assertEqual(len(files), 1)
        env = json.loads(files[0].read_text())
        self.assertEqual(env["op"], "ping")
        self.assertEqual(env["payload"]["message"], "hi")

    def test_missing_op_raises(self):
        s = self._sched()
        with self.assertRaises(SchedulerError):
            s.submit([{"payload": {"x": 1}}])  # no op anywhere


if __name__ == "__main__":
    unittest.main()
