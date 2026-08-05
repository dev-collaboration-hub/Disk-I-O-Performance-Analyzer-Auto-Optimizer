"""M3 history, event timeline, spike detection, and reporting tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from analysis.spike_detector import detect_snapshot_spikes, detect_spikes
from analysis.timeline_builder import (
    EventTimeline,
    build_timeline,
    build_timeline_events,
)
from reporting.cli_dashboard import persist_snapshot_history, render_dashboard
from reporting.history_report import build_history_report, render_history_report
from utils.history_manager import HistoryManager, JsonlStore


def snapshot(
    timestamp: str,
    usage: float = 40.0,
    io_rate: float = 100.0,
    top: tuple[int, str] | None = None,
    errors: list[dict[str, str]] | None = None,
) -> dict:
    consumers = []
    if top is not None:
        consumers.append(
            {
                "pid": top[0],
                "name": top[1],
                "create_time": float(top[0]),
                "read_bytes_per_second": 0.0,
                "write_bytes_per_second": io_rate,
                "total_bytes_per_second": io_rate,
                "io_share_percent": 100.0,
            }
        )
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
            "read_count": 0,
            "write_count": 0,
            "read_bytes": 0,
            "write_bytes": 0,
            "read_bytes_per_second": io_rate / 2,
            "write_bytes_per_second": io_rate / 2,
            "read_operations_per_second": 0.0,
            "write_operations_per_second": 0.0,
        },
        "processes": {
            "enabled": True,
            "accessible_after": 1,
            "matched": 1,
            "active": len(consumers),
            "top_consumers": consumers,
        },
        "errors": errors or [],
    }


class M3HistoricalMonitoringTests(unittest.TestCase):
    def test_jsonl_retention_keeps_recent_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = JsonlStore(Path(directory) / "history.jsonl", max_records=3)
            for index in range(5):
                store.append({"timestamp": str(index)})
            self.assertEqual(
                [item["timestamp"] for item in store.load()],
                ["2", "3", "4"],
            )

    def test_corrupt_jsonl_line_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.jsonl"
            path.write_text('{"a":1}\n{broken\n{"a":2}\n', encoding="utf-8")
            self.assertEqual(
                [item["a"] for item in JsonlStore(path).load()],
                [1, 2],
            )

    def test_legacy_json_array_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"
            path.write_text(
                json.dumps([{"timestamp": "a"}, {"timestamp": "b"}]),
                encoding="utf-8",
            )
            manager = HistoryManager(path, max_records=None)
            self.assertEqual(manager.latest_snapshot()["timestamp"], "b")

    def test_usage_and_critical_spikes(self) -> None:
        events = detect_snapshot_spikes(
            snapshot("1", 70),
            snapshot("2", 96),
            usage_delta_threshold=20,
            io_minimum_bytes_per_second=999_999,
        )
        event_types = {item["event_type"] for item in events}
        self.assertIn("DISK_USAGE_SPIKE", event_types)
        self.assertIn("CRITICAL_DISK_USAGE_ENTERED", event_types)

    def test_io_throughput_spike(self) -> None:
        events = detect_snapshot_spikes(
            snapshot("1", 40, 100),
            snapshot("2", 40, 1000),
            io_multiplier=3,
            io_minimum_bytes_per_second=500,
        )
        self.assertEqual(
            [item["event_type"] for item in events],
            ["DISK_IO_SPIKE"],
        )

    def test_legacy_detect_spikes_api(self) -> None:
        history = [
            {"timestamp": "1", "disk_usage_percent": 10},
            {"timestamp": "2", "disk_usage_percent": 40},
        ]
        events = detect_spikes(
            history,
            usage_delta_threshold=20,
            io_minimum_bytes_per_second=999_999,
        )
        self.assertEqual(events[0]["event_type"], "DISK_USAGE_SPIKE")

    def test_timeline_persistence_and_filtering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            timeline = EventTimeline(
                Path(directory) / "events.jsonl",
                max_records=10,
            )
            timeline.record_event({"event_type": "A", "severity": "INFO"})
            timeline.record_event(
                {"event_type": "B", "severity": "WARNING"}
            )
            self.assertEqual(
                timeline.load_events(severity="warning")[0]["event_type"],
                "B",
            )
            self.assertEqual(timeline.count(), 2)

    def test_transition_warning_and_consumer_events(self) -> None:
        previous = snapshot("1", 79, 100, top=(1, "old"))
        current = snapshot(
            "2",
            85,
            100,
            top=(2, "new"),
            errors=[
                {"path": "/x", "error": "OSError", "message": "bad"}
            ],
        )
        event_types = {
            item["event_type"]
            for item in build_timeline_events(
                previous,
                current,
                io_minimum_bytes_per_second=999_999,
            )
        }
        self.assertIn("DISK_STATUS_CHANGED", event_types)
        self.assertIn("TOP_DISK_CONSUMER_CHANGED", event_types)
        self.assertIn("COLLECTION_WARNING", event_types)

    def test_snapshot_history_integration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            history = HistoryManager(
                Path(directory) / "history.jsonl",
                max_records=10,
            )
            timeline = EventTimeline(
                Path(directory) / "events.jsonl",
                max_records=10,
            )
            history.save_snapshot(snapshot("1", 70, 100))
            current = snapshot("2", 96, 100)
            events = persist_snapshot_history(
                current,
                history,
                timeline,
                usage_delta_threshold=20,
                io_minimum_bytes_per_second=999_999,
            )
            self.assertEqual(history.count(), 2)
            self.assertEqual(current["history"]["record_number"], 2)
            self.assertEqual(timeline.count(), len(events))

    def test_dashboard_and_history_report_render_m3(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            history = HistoryManager(
                Path(directory) / "history.jsonl",
                max_records=10,
            )
            timeline = EventTimeline(
                Path(directory) / "events.jsonl",
                max_records=10,
            )
            current = snapshot("2", 50, 2048)
            persist_snapshot_history(
                current,
                history,
                timeline,
                io_minimum_bytes_per_second=999_999,
            )
            dashboard = render_dashboard(current)
            report = render_history_report(
                build_history_report(history, timeline, limit=10)
            )
            self.assertIn("M3 Historical Data", dashboard)
            self.assertIn("Snapshots stored : 1", report)

    def test_build_timeline_returns_structured_events(self) -> None:
        result = build_timeline(
            [snapshot("2")],
            [
                {
                    "timestamp": "1",
                    "event_type": "START",
                    "severity": "INFO",
                }
            ],
        )
        self.assertEqual(
            [item["event_type"] for item in result],
            ["START", "METRICS_SNAPSHOT"],
        )


if __name__ == "__main__":
    unittest.main()
