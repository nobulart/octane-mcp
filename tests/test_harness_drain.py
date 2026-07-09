"""Regression tests for benchmarks.harness.drain_oneshot.

These cover the failure/retry path that the offline suite did NOT exercise —
the path where the recursion bug (now fixed) lived. Keep this file focused on
drain_oneshot so a future regression in the retry/termination logic is caught.

The function signature under test:
    drain_oneshot(ws, *, timeout_seconds: float = 60.0) -> dict

It clicks the one-shot bridge via octanex_mcp.bridge_control.run_bridge_script
(which spawns osascript -> needs macOS Accessibility/TCC in a live session) and
then polls ws.queue_dir for the queue to drain.
"""
from __future__ import annotations

import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import benchmarks.harness as H
import octanex_mcp.bridge_control as BC


class _FakeQueue:
    """Mimics the Workspace.queue_dir glob used by drain_oneshot."""

    def __init__(self, root: Path) -> None:
        self.queue_dir = root / "queue"
        self.queue_dir.mkdir(parents=True, exist_ok=True)


class DrainOneshotTests(unittest.TestCase):
    def setUp(self) -> None:
        # Neutralize real sleeps so retries/polls don't actually wait.
        self._sleep = mock.patch.object(time, "sleep", lambda *a, **k: None)
        self._sleep.start()
        import tempfile

        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        self._sleep.stop()
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def _ws(self) -> SimpleNamespace:
        qd = self.tmp / "queue"
        qd.mkdir(parents=True, exist_ok=True)
        return SimpleNamespace(queue_dir=qd)

    def test_all_clicks_fail_is_bounded_no_recursion(self) -> None:
        """Repeated bridge-click failure must retry at most 3 times and return
        ok=False with an error — NOT recurse into RecursionError."""
        calls = {"n": 0}

        def fail(mode, *, config=None, dry_run=False, timeout_seconds=15):
            calls["n"] += 1
            return {"ok": False, "error": "assistive access denied (-1719)"}

        with mock.patch.object(BC, "run_bridge_script", fail):
            res = H.drain_oneshot(self._ws(), timeout_seconds=5)

        self.assertLessEqual(calls["n"], 3, "retry must be bounded to <=3 clicks")
        self.assertFalse(res["ok"])
        self.assertIn("error", res)

    def test_success_on_first_click(self) -> None:
        calls = {"n": 0}

        def ok(mode, *, config=None, dry_run=False, timeout_seconds=15):
            calls["n"] += 1
            return {"ok": True, "status": {"octane_available": True}}

        with mock.patch.object(BC, "run_bridge_script", ok):
            res = H.drain_oneshot(self._ws(), timeout_seconds=5)

        self.assertTrue(res["ok"])
        self.assertEqual(calls["n"], 1)

    def test_recovers_on_second_click(self) -> None:
        calls = {"n": 0}

        def flip(mode, *, config=None, dry_run=False, timeout_seconds=15):
            calls["n"] += 1
            return {"ok": calls["n"] >= 2, "status": {}}

        with mock.patch.object(BC, "run_bridge_script", flip):
            res = H.drain_oneshot(self._ws(), timeout_seconds=5)

        self.assertTrue(res["ok"])
        self.assertEqual(calls["n"], 2)

    def test_polls_until_queue_empty(self) -> None:
        """After a successful click, drain_oneshot should report ok=True only
        once the queue dir is empty (it is empty in the fake ws)."""
        ws = self._ws()
        (ws.queue_dir / "stale.json").write_text("{}")

        def ok(mode, *, config=None, dry_run=False, timeout_seconds=15):
            # First click "drains" the queue by removing the file.
            for f in list(ws.queue_dir.glob("*.json")):
                f.unlink()
            return {"ok": True, "status": {"octane_available": True}}

        with mock.patch.object(BC, "run_bridge_script", ok):
            res = H.drain_oneshot(ws, timeout_seconds=5)

        self.assertTrue(res["ok"])
        self.assertEqual(res["queue_remaining"], 0)


if __name__ == "__main__":
    unittest.main()
