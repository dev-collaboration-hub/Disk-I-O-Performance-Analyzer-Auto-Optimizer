"""M6 recommendation-engine and impact-estimation tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from analysis.recommendation_engine import generate_recommendations
from analysis.timeline_builder import EventTimeline
from reporting.cli_dashboard import persist_snapshot_history
from reporting.process_behavior_report import attach_process_behavior_analysis
from reporting.recommendation_report import (
    analyze_recommendations,
    render_recommendation_report,
)
from utils.history_manager import HistoryManager


def snapshot(
    timestamp: str,
    *,
    usage: float = 50.0,
    share: float = 75.0,
    rate: float = 3_000_000.0,
) -> dict:
    return {
        "schema_version": 3,
        "timestamp": timestamp,
        "disks": [
            {
                "path": "/",
                "total_bytes": 1000,
                "used_bytes": int(usage * 10),
                "free_bytes": 1000 - int(usage * 10),
                "usage_percent": usage,
            }
        ],
        "io": {
            "read_count": 1,
            "write_count": 1,
            "read_bytes": 1,
            "write_bytes": 1,
            "read_bytes_per_second": rate / 2,
            "write_bytes_per_second": rate / 2,
            "read_operations_per_second": 1.0,
            "write_operations_per_second": 1.0,
        },
        "processes": {
            "enabled": True,
            "accessible_before": 1,
            "accessible_after": 1,
            "matched": 1,
            "active": 1,
            "top_consumers": [
                {
                    "pid": 11,
                    "name": "chrome.exe",
                    "create_time": 1.0,
                    "read_bytes_delta": int(rate / 2),
                    "write_bytes_delta": int(rate / 2),
                    "total_io_bytes_delta": int(rate),
                    "read_count_delta": 1,
                    "write_count_delta": 1,
                    "read_bytes_per_second": rate / 2,
                    "write_bytes_per_second": rate / 2,
                    "total_bytes_per_second": rate,
                    "read_operations_per_second": 1.0,
                    "write_operations_per_second": 1.0,
                    "io_share_percent": share,
                    "percentage": share,
                }
            ],
        },
        "history": {"enabled": True, "recent_events": []},
        "errors": [],
    }


class M6RecommendationTests(unittest.TestCase):
    def test_no_evidence_produces_no_recommendation(self) -> None:
        current = snapshot("1", usage=40, share=10, rate=100)
        current["root_cause"] = {"status": "NO_BOTTLENECK", "confidence": 0}
        current["process_behavior"] = {
            "status": "NORMAL",
            "anomalies": [],
            "runaways": [],
        }
        self.assertEqual(generate_recommendations(current), [])

    def test_capacity_pressure_recommendation(self) -> None:
        current = snapshot("1", usage=97, share=10, rate=100)
        current["root_cause"] = {
            "status": "BOTTLENECK_DETECTED",
            "cause": "Disk Capacity Pressure",
            "confidence": 97,
        }
        current["process_behavior"] = {
            "status": "NORMAL",
            "anomalies": [],
            "runaways": [],
        }
        result = generate_recommendations(current)
        self.assertEqual(result[0]["category"], "CAPACITY")
        self.assertEqual(result[0]["priority"], "CRITICAL")

    def test_runaway_is_ranked_first_and_high_impact(self) -> None:
        current = snapshot("1", share=85, rate=8_000_000)
        current["root_cause"] = {
            "status": "BOTTLENECK_DETECTED",
            "severity": "CRITICAL",
            "confidence": 90,
            "cause": "Browser Activity",
            "process": "chrome.exe",
            "pid": 11,
            "signals": ["PROCESS_IO_DOMINANCE"],
        }
        current["process_behavior"] = {
            "status": "RUNAWAY_DETECTED",
            "anomalies": [],
            "runaways": [
                {
                    "name": "chrome.exe",
                    "pid": 11,
                    "severity": "CRITICAL",
                    "samples": 3,
                }
            ],
        }
        result = generate_recommendations(current)
        self.assertTrue(result[0]["id"].startswith("runaway:"))
        self.assertEqual(result[0]["impact"]["impact_level"], "HIGH")
        self.assertFalse(result[0]["automation_eligible"])

    def test_known_root_cause_gets_specific_action(self) -> None:
        current = snapshot("1")
        current["root_cause"] = {
            "status": "BOTTLENECK_DETECTED",
            "severity": "WARNING",
            "confidence": 80,
            "cause": "Browser Activity",
            "process": "chrome.exe",
            "pid": 11,
            "signals": ["PROCESS_IO_DOMINANCE"],
        }
        current["process_behavior"] = {
            "status": "NORMAL",
            "anomalies": [],
            "runaways": [],
        }
        result = generate_recommendations(current)
        self.assertIn("downloads", result[0]["action"])

    def test_low_confidence_root_cause_is_gated(self) -> None:
        current = snapshot("1", usage=40)
        current["root_cause"] = {
            "status": "BOTTLENECK_DETECTED",
            "severity": "WARNING",
            "confidence": 20,
            "cause": "Unknown Process Activity",
            "process": "chrome.exe",
            "pid": 11,
            "signals": [],
        }
        current["process_behavior"] = {
            "status": "NORMAL",
            "anomalies": [],
            "runaways": [],
        }
        self.assertEqual(generate_recommendations(current), [])

    def test_report_is_explicitly_advisory(self) -> None:
        current = snapshot("1")
        current["root_cause"] = {
            "status": "BOTTLENECK_DETECTED",
            "severity": "WARNING",
            "confidence": 80,
            "cause": "Browser Activity",
            "process": "chrome.exe",
            "pid": 11,
            "signals": ["PROCESS_IO_DOMINANCE"],
        }
        current["process_behavior"] = {
            "status": "NORMAL",
            "anomalies": [],
            "runaways": [],
        }
        report = analyze_recommendations(current)
        self.assertFalse(report["automatic_changes_applied"])
        self.assertIn("advisory only", render_recommendation_report(report).lower())

    def test_m5_attachment_also_attaches_m6(self) -> None:
        current = snapshot("1")
        current["root_cause"] = {
            "status": "BOTTLENECK_DETECTED",
            "severity": "WARNING",
            "confidence": 80,
            "cause": "Browser Activity",
            "process": "chrome.exe",
            "pid": 11,
            "signals": ["PROCESS_IO_DOMINANCE"],
        }
        attach_process_behavior_analysis(current, recent_history=[current])
        self.assertIn("recommendations", current)

    def test_persistence_stores_m6_analysis(self) -> None:
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
            persist_snapshot_history(
                current,
                history,
                timeline,
                io_minimum_bytes_per_second=999_999_999,
            )
            stored = history.latest_snapshot()
            self.assertIsNotNone(stored)
            self.assertIn("recommendations", stored)


if __name__ == "__main__":
    unittest.main()
