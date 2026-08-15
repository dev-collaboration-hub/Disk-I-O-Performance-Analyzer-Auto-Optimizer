"""M4 bottleneck detection, root-cause analysis, and integration tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from analysis.bottleneck_detector import (
    detect_bottleneck,
    detect_snapshot_bottleneck,
)
from analysis.cause_classifier import classify_process
from analysis.timeline_builder import EventTimeline
from reporting.cli_dashboard import persist_snapshot_history, render_dashboard
from reporting.root_cause_report import (
    analyze_snapshot_root_cause,
    generate_root_cause_report,
)
from utils.history_manager import HistoryManager


def snapshot(
    timestamp: str,
    *,
    usage: float = 40.0,
    process_name: str = "chrome.exe",
    process_share: float = 70.0,
    process_rate: float = 2_000_000.0,
    recent_events: list[dict] | None = None,
) -> dict:
    consumer = {
        "pid": 101,
        "name": process_name,
        "create_time": 1.0,
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
                "used_bytes": int(usage * 10),
                "free_bytes": 1_000 - int(usage * 10),
                "usage_percent": usage,
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
            "recent_events": recent_events or [],
        },
        "errors": [],
    }


class M4RootCauseTests(unittest.TestCase):
    def test_no_bottleneck_when_signals_are_below_thresholds(self) -> None:
        result = detect_bottleneck(
            40,
            [
                {
                    "pid": 1,
                    "name": "quiet.exe",
                    "percentage": 20,
                    "total_bytes_per_second": 100,
                }
            ],
        )
        self.assertFalse(result["bottleneck_detected"])
        self.assertEqual(result["severity"], "NORMAL")

    def test_capacity_pressure_is_detected_without_process_data(self) -> None:
        result = detect_bottleneck(96, [])
        self.assertTrue(result["bottleneck_detected"])
        self.assertEqual(result["severity"], "CRITICAL")
        self.assertIn("CRITICAL_CAPACITY_PRESSURE", result["signals"])

    def test_dominant_process_is_identified(self) -> None:
        result = detect_bottleneck(
            50,
            [
                {
                    "pid": 7,
                    "name": "python.exe",
                    "io_share_percent": 72,
                    "total_bytes_per_second": 2_000_000,
                }
            ],
        )
        self.assertTrue(result["bottleneck_detected"])
        self.assertEqual(result["likely_process"], "python.exe")
        self.assertIn("PROCESS_IO_DOMINANCE", result["signals"])

    def test_snapshot_detector_uses_m3_spike_events(self) -> None:
        current = snapshot(
            "2026-08-16T00:00:00+00:00",
            process_share=20,
            recent_events=[
                {
                    "event_type": "DISK_IO_SPIKE",
                    "severity": "WARNING",
                }
            ],
        )
        result = detect_snapshot_bottleneck(current)
        self.assertIn("RECENT_IO_SPIKE", result["signals"])

    def test_classifier_is_case_insensitive_and_cross_platform(self) -> None:
        self.assertEqual(
            classify_process("SearchIndexer.EXE")["cause"],
            "Windows Search Indexing",
        )
        self.assertEqual(
            classify_process("/usr/bin/python3")["cause"],
            "Python Runtime Activity",
        )

    def test_root_cause_report_contains_evidence_and_recommendation(self) -> None:
        report = generate_root_cause_report(
            50,
            snapshot("x")["processes"]["top_consumers"],
            spike_detected=True,
        )
        self.assertEqual(report["status"], "BOTTLENECK_DETECTED")
        self.assertEqual(report["cause"], "Browser Activity")
        self.assertTrue(report["evidence"])
        self.assertTrue(report["recommendation"])

    def test_sustained_activity_uses_recent_history(self) -> None:
        history = [
            snapshot("1"),
            snapshot("2"),
            snapshot("3"),
        ]
        report = analyze_snapshot_root_cause(
            history[-1],
            recent_history=history,
        )
        self.assertTrue(report["sustained_activity"])
        self.assertGreater(report["confidence"], 0)

    def test_persistence_attaches_m4_analysis_before_storing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            history = HistoryManager(
                Path(directory) / "history.jsonl",
                max_records=10,
            )
            timeline = EventTimeline(
                Path(directory) / "events.jsonl",
                max_records=10,
            )
            current = snapshot("2")
            current.pop("root_cause", None)
            persist_snapshot_history(
                current,
                history,
                timeline,
                io_minimum_bytes_per_second=999_999_999,
            )
            self.assertIn("root_cause", current)
            stored = history.latest_snapshot()
            self.assertIsNotNone(stored)
            self.assertIn("root_cause", stored)

    def test_dashboard_renders_m4_section(self) -> None:
        current = snapshot("3")
        current["root_cause"] = analyze_snapshot_root_cause(
            current,
            recent_history=[snapshot("1"), snapshot("2"), current],
        )
        rendered = render_dashboard(current)
        self.assertIn("M4 Root Cause Detection", rendered)
        self.assertIn("Browser Activity", rendered)


if __name__ == "__main__":
    unittest.main()
