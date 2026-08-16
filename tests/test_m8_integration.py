"""M8 alerting and notification tests."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from alerts.alert_engine import (
    collect_alert_candidates,
    evaluate_alerts,
    record_optimization_event,
)
from alerts.alert_store import AlertStore


def snapshot(usage: float = 40.0) -> dict:
    return {
        "timestamp": "2026-08-16T00:00:00+00:00",
        "disks": [{"path": "/", "usage_percent": usage}],
        "history": {"enabled": True, "recent_events": []},
        "root_cause": {"status": "NO_BOTTLENECK"},
        "process_behavior": {
            "status": "NORMAL", "anomalies": [], "runaways": []
        },
        "recommendations": {
            "status": "NO_ACTION_NEEDED", "recommendations": []
        },
    }


class M8AlertingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = AlertStore(Path(self.temp.name) / "alerts.jsonl", max_records=100)
        self.t0 = datetime(2026, 8, 16, tzinfo=timezone.utc)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_capacity_alert_triggers(self) -> None:
        report = evaluate_alerts(snapshot(90), store=self.store, now=self.t0)
        self.assertEqual(report["emitted_count"], 1)
        self.assertEqual(report["emitted"][0]["event_type"], "TRIGGERED")
        self.assertEqual(report["active_count"], 1)

    def test_duplicate_is_suppressed_during_cooldown(self) -> None:
        evaluate_alerts(snapshot(90), store=self.store, now=self.t0)
        report = evaluate_alerts(
            snapshot(90), store=self.store, now=self.t0 + timedelta(seconds=30)
        )
        self.assertEqual(report["emitted_count"], 0)
        self.assertEqual(report["suppressed_count"], 1)

    def test_reminder_after_cooldown(self) -> None:
        evaluate_alerts(snapshot(90), store=self.store, now=self.t0)
        report = evaluate_alerts(
            snapshot(90), store=self.store, cooldown_seconds=60,
            now=self.t0 + timedelta(seconds=61),
        )
        self.assertEqual(report["emitted"][0]["event_type"], "REMINDER")

    def test_escalation_bypasses_cooldown(self) -> None:
        evaluate_alerts(snapshot(90), store=self.store, now=self.t0)
        report = evaluate_alerts(
            snapshot(97), store=self.store, now=self.t0 + timedelta(seconds=1)
        )
        self.assertEqual(report["emitted"][0]["event_type"], "ESCALATED")
        self.assertEqual(report["emitted"][0]["severity"], "CRITICAL")

    def test_recovery_closes_active_alert(self) -> None:
        evaluate_alerts(snapshot(90), store=self.store, now=self.t0)
        report = evaluate_alerts(
            snapshot(40), store=self.store, now=self.t0 + timedelta(seconds=2)
        )
        self.assertEqual(report["emitted"][0]["event_type"], "RECOVERED")
        self.assertEqual(report["active_count"], 0)

    def test_missing_group_does_not_create_false_recovery(self) -> None:
        s = snapshot(40)
        s["process_behavior"]["runaways"] = [{
            "name": "python", "pid": 7, "severity": "WARNING",
            "latest_share_percent": 80, "latest_rate_bytes_per_second": 2_000_000,
        }]
        evaluate_alerts(s, store=self.store, now=self.t0)
        next_snapshot = snapshot(40)
        next_snapshot.pop("process_behavior")
        report = evaluate_alerts(
            next_snapshot, store=self.store, now=self.t0 + timedelta(seconds=2)
        )
        self.assertEqual(report["emitted_count"], 0)
        self.assertEqual(report["active_count"], 1)

    def test_high_priority_recommendation_is_candidate(self) -> None:
        s = snapshot()
        s["recommendations"]["recommendations"] = [{
            "id": "runaway:python:7", "title": "Inspect python",
            "priority": "HIGH", "priority_score": 90,
            "reason": "sustained activity", "impact": {"impact_score": 80},
            "target_process": "python", "target_pid": 7,
        }]
        candidates, _ = collect_alert_candidates(s)
        self.assertTrue(any(item["group"] == "recommendation" for item in candidates))

    def test_m7_apply_event_is_recorded_but_dry_run_is_not(self) -> None:
        self.assertIsNone(record_optimization_event(
            {"execution_status": "DRY_RUN"}, store=self.store, now=self.t0
        ))
        event = record_optimization_event(
            {"execution_status": "APPLIED", "applied_count": 1, "session_id": "abc"},
            store=self.store, now=self.t0,
        )
        self.assertIsNotNone(event)
        self.assertEqual(event["source"], "M7")
        self.assertEqual(len(self.store.load()), 1)

    def test_malformed_jsonl_line_is_skipped(self) -> None:
        self.store.alert_file.parent.mkdir(parents=True, exist_ok=True)
        self.store.alert_file.write_text("{bad json}\n", encoding="utf-8")
        self.assertEqual(self.store.load(), [])
        evaluate_alerts(snapshot(90), store=self.store, now=self.t0)
        self.assertEqual(len(self.store.load()), 1)


if __name__ == "__main__":
    unittest.main()
