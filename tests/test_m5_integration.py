"""M5 process profiling, anomaly detection, runaway detection, and integration tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from analysis.anomaly_detector import detect_process_anomalies
from analysis.process_profiler import build_process_profiles
from analysis.runaway_detector import detect_runaway_processes
from analysis.timeline_builder import EventTimeline
from reporting.cli_dashboard import persist_snapshot_history, render_dashboard
from reporting.process_behavior_report import analyze_process_behavior
from utils.history_manager import HistoryManager


def snapshot(
    timestamp: str,
    *,
    process_name: str = "python.exe",
    pid: int = 101,
    create_time: float = 1.0,
    process_share: float = 40.0,
    process_rate: float = 500_000.0,
) -> dict:
    consumer = {
        "pid": pid,
        "name": process_name,
        "create_time": create_time,
        "read_bytes_delta": int(process_rate / 2),
        "write_bytes_delta": int(process_rate / 2),
        "total_io_bytes_delta": int(process_rate),
        "read_count_delta": 1,
        "write_count_delta": 1,
        "read_bytes_per_second": process_rate / 2,
        "write_bytes_per_second": process_rate / 2,
        "total_bytes_per_second": process_rate,
        "read_operations_per_second": 1.0,
        "write_operations_per_second": 1.0,
        "io_share_percent": process_share,
        "percentage": process_share,
    }
    return {
        "schema_version": 3,
        "timestamp": timestamp,
        "disks": [
            {
                "path": "/",
                "total_bytes": 1_000,
                "used_bytes": 400,
                "free_bytes": 600,
                "usage_percent": 40.0,
            }
        ],
        "io": {
            "read_count": 10,
            "write_count": 10,
            "read_bytes": 1_000,
            "write_bytes": 1_000,
            "read_bytes_per_second": process_rate / 2,
            "write_bytes_per_second": process_rate / 2,
            "read_operations_per_second": 1.0,
            "write_operations_per_second": 1.0,
        },
        "processes": {
            "enabled": True,
            "accessible_before": 1,
            "accessible_after": 1,
            "matched": 1,
            "active": 1,
            "top_consumers": [consumer],
        },
        "history": {
            "enabled": True,
            "recent_events": [],
        },
        "errors": [],
    }


class M5ProcessBehaviorTests(unittest.TestCase):
    def test_profile_builds_history_and_trend(self) -> None:
        history = [
            snapshot("1", process_rate=500_000),
            snapshot("2", process_rate=750_000),
            snapshot("3", process_rate=1_500_000),
        ]
        profiles = build_process_profiles(history, max_samples=10)
        self.assertEqual(len(profiles), 1)
        profile = profiles[0]
        self.assertEqual(profile["samples_observed"], 3)
        self.assertEqual(profile["trend"], "INCREASING")
        self.assertEqual(profile["latest_rate_bytes_per_second"], 1_500_000)

    def test_anomaly_detects_rate_and_share_departure(self) -> None:
        history = [
            snapshot("1", process_share=20, process_rate=500_000),
            snapshot("2", process_share=22, process_rate=500_000),
            snapshot("3", process_share=21, process_rate=500_000),
        ]
        current = snapshot(
            "4",
            process_share=70,
            process_rate=2_000_000,
        )
        anomalies = detect_process_anomalies(
            current,
            history + [current],
        )
        self.assertEqual(len(anomalies), 1)
        self.assertIn("RATE_SPIKE", anomalies[0]["signals"])
        self.assertIn("SHARE_JUMP", anomalies[0]["signals"])

    def test_anomaly_requires_baseline_samples(self) -> None:
        current = snapshot("2", process_share=90, process_rate=5_000_000)
        anomalies = detect_process_anomalies(
            current,
            [snapshot("1"), current],
        )
        self.assertEqual(anomalies, [])

    def test_runaway_requires_sustained_same_process_instance(self) -> None:
        history = [
            snapshot("1", process_share=70, process_rate=2_000_000),
            snapshot("2", process_share=72, process_rate=2_200_000),
            snapshot("3", process_share=75, process_rate=2_500_000),
        ]
        runaways = detect_runaway_processes(history[-1], history)
        self.assertEqual(len(runaways), 1)
        self.assertEqual(runaways[0]["name"], "python.exe")
        self.assertEqual(runaways[0]["samples"], 3)

    def test_pid_change_breaks_runaway_identity(self) -> None:
        history = [
            snapshot("1", pid=101, process_share=70, process_rate=2_000_000),
            snapshot("2", pid=101, process_share=70, process_rate=2_000_000),
            snapshot("3", pid=202, process_share=90, process_rate=5_000_000),
        ]
        self.assertEqual(
            detect_runaway_processes(history[-1], history),
            [],
        )

    def test_behavior_report_prioritizes_runaway_status(self) -> None:
        history = [
            snapshot("1", process_share=70, process_rate=2_000_000),
            snapshot("2", process_share=70, process_rate=2_000_000),
            snapshot("3", process_share=70, process_rate=2_000_000),
        ]
        report = analyze_process_behavior(
            history[-1],
            recent_history=history,
        )
        self.assertEqual(report["status"], "RUNAWAY_DETECTED")
        self.assertEqual(report["runaway_count"], 1)

    def test_persistence_attaches_m5_analysis_before_storing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            history = HistoryManager(
                Path(directory) / "history.jsonl",
                max_records=10,
            )
            timeline = EventTimeline(
                Path(directory) / "events.jsonl",
                max_records=10,
            )
            for index in range(1, 4):
                history.save_snapshot(
                    snapshot(
                        str(index),
                        process_share=20,
                        process_rate=500_000,
                    )
                )
            current = snapshot(
                "4",
                process_share=70,
                process_rate=2_000_000,
            )
            persist_snapshot_history(
                current,
                history,
                timeline,
                io_minimum_bytes_per_second=999_999_999,
            )
            self.assertIn("process_behavior", current)
            self.assertEqual(
                current["process_behavior"]["status"],
                "ANOMALY_DETECTED",
            )
            stored = history.latest_snapshot()
            self.assertIsNotNone(stored)
            self.assertIn("process_behavior", stored)

    def test_dashboard_renders_m5_section(self) -> None:
        history = [
            snapshot("1"),
            snapshot("2"),
            snapshot("3"),
        ]
        current = history[-1]
        current["process_behavior"] = analyze_process_behavior(
            current,
            recent_history=history,
        )
        rendered = render_dashboard(current)
        self.assertIn("M5 Process Behavior Analysis", rendered)
        self.assertIn("Profiles", rendered)


if __name__ == "__main__":
    unittest.main()
