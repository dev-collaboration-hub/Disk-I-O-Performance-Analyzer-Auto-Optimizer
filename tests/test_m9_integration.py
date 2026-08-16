from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from analytics.history_analytics import analyze_history
from analytics.outcome_analytics import analyze_alert_events, analyze_optimization_events
from analytics.process_analytics import analyze_processes
from reporting.analytics_report import _load_jsonl, build_analytics_report, render_analytics_report


def snapshot(timestamp: str, usage: float, rate: float, share: float = 60.0) -> dict:
    process = {
        "pid": 101,
        "name": "worker.exe",
        "total_bytes_per_second": rate,
        "io_share_percent": share,
    }
    return {
        "timestamp": timestamp,
        "disks": [{"path": "/", "usage_percent": usage}],
        "io": {
            "read_bytes_per_second": rate * 0.4,
            "write_bytes_per_second": rate * 0.6,
        },
        "processes": {"top_consumers": [process]},
        "root_cause": {"status": "NO_BOTTLENECK"},
        "process_behavior": {"anomaly_count": 0, "runaway_count": 0, "anomalies": [], "runaways": []},
        "recommendations": {"recommendation_count": 0},
        "alerts": {"emitted_count": 0},
    }


class M9AnalyticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.records = [
            snapshot("2026-08-16T00:00:00+00:00", 50, 1000),
            snapshot("2026-08-16T01:00:00+00:00", 60, 2000),
            snapshot("2026-08-16T02:00:00+00:00", 70, 4000),
        ]

    def test_disk_usage_trend_and_change(self) -> None:
        report = analyze_history(self.records)
        disk = report["disks"][0]
        self.assertEqual(disk["trend"]["direction"], "INCREASING")
        self.assertEqual(disk["change_percentage_points"], 20.0)
        self.assertAlmostEqual(disk["trend"]["slope_per_hour"], 10.0)

    def test_system_io_percentile_and_peak(self) -> None:
        report = analyze_history(self.records)
        io = report["system_io"]
        self.assertGreater(io["p95_total_bytes_per_second"], io["average_total_bytes_per_second"])
        self.assertEqual(io["maximum_total_bytes_per_second"], 4000.0)
        self.assertEqual(io["peak_timestamp"], "2026-08-16T02:00:00+00:00")

    def test_process_analytics_aggregate_retained_top_consumers(self) -> None:
        report = analyze_processes(self.records, top_n=5)
        worker = report["processes"][0]
        self.assertEqual(worker["samples_seen"], 3)
        self.assertEqual(worker["dominant_samples"], 3)
        self.assertEqual(worker["maximum_rate_bytes_per_second"], 4000.0)

    def test_process_anomaly_and_runaway_counts(self) -> None:
        self.records[-1]["process_behavior"] = {
            "anomaly_count": 1,
            "runaway_count": 1,
            "anomalies": [{"name": "worker.exe", "pid": 101}],
            "runaways": [{"name": "worker.exe", "pid": 101}],
        }
        worker = analyze_processes(self.records)["processes"][0]
        self.assertEqual(worker["anomaly_events"], 1)
        self.assertEqual(worker["runaway_events"], 1)

    def test_alert_lifecycle_recovery_duration(self) -> None:
        events = [
            {
                "alert_key": "capacity:/",
                "group": "capacity",
                "source": "M1",
                "severity": "WARNING",
                "event_type": "TRIGGERED",
                "active": True,
                "emitted_at": "2026-08-16T00:00:00+00:00",
                "title": "pressure",
            },
            {
                "alert_key": "capacity:/",
                "group": "capacity",
                "source": "M1",
                "severity": "INFO",
                "event_type": "RECOVERED",
                "active": False,
                "emitted_at": "2026-08-16T00:05:00+00:00",
                "title": "recovered",
            },
        ]
        report = analyze_alert_events(events)
        self.assertEqual(report["active_alert_count"], 0)
        self.assertEqual(report["recovered_condition_count"], 1)
        self.assertEqual(report["average_recovery_seconds"], 300.0)

    def test_active_alert_reconstruction(self) -> None:
        events = [{
            "alert_key": "runaway:x",
            "group": "runaway",
            "source": "M5",
            "severity": "CRITICAL",
            "event_type": "TRIGGERED",
            "active": True,
            "emitted_at": "2026-08-16T00:00:00+00:00",
            "title": "runaway",
        }]
        self.assertEqual(analyze_alert_events(events)["active_alert_count"], 1)

    def test_optimization_outcomes(self) -> None:
        events = [
            {"event_type": "SESSION_STARTED", "session_id": "a"},
            {"event_type": "ACTION_APPLIED", "session_id": "a"},
            {"event_type": "ACTION_ROLLED_BACK", "session_id": "a"},
            {"event_type": "SESSION_ROLLED_BACK", "session_id": "a"},
        ]
        report = analyze_optimization_events(events)
        self.assertEqual(report["session_count"], 1)
        self.assertEqual(report["actions_applied"], 1)
        self.assertEqual(report["actions_rolled_back"], 1)
        self.assertEqual(report["rolled_back_sessions"], 1)

    def test_combined_report_and_render(self) -> None:
        report = build_analytics_report(self.records)
        text = render_analytics_report(report)
        self.assertEqual(report["status"], "OK")
        self.assertIn("Disk usage trends", text)
        self.assertIn("worker.exe", text)

    def test_jsonl_loader_skips_corrupt_tail_and_limits(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.jsonl"
            path.write_text('{"timestamp":"1"}\nnot-json\n{"timestamp":"2"}\n', encoding="utf-8")
            records = _load_jsonl(path, limit=1)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["timestamp"], "2")

    def test_no_data_is_explicit(self) -> None:
        report = build_analytics_report([])
        self.assertEqual(report["status"], "NO_DATA")
        self.assertEqual(report["history"]["record_count"], 0)


if __name__ == "__main__":
    unittest.main()
