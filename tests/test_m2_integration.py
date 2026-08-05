"""M2 process enumeration, sampling, ranking, and dashboard tests."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import psutil

from monitoring.metrics_snapshot import create_snapshot
from monitoring.process_detector import get_running_processes
from monitoring.process_io_monitor import calculate_process_io_rates, get_process_io_stats
from monitoring.top_disk_consumers import rank_process_io
from reporting.cli_dashboard import render_dashboard
from reporting.process_report import get_risk_level, render_process_report


def process_stats(
    pid: int,
    *,
    create_time: float,
    read_bytes: int,
    write_bytes: int,
    read_count: int = 0,
    write_count: int = 0,
    name: str = "worker",
) -> dict:
    return {
        "pid": pid,
        "name": name,
        "status": "running",
        "username": "user",
        "create_time": create_time,
        "read_count": read_count,
        "write_count": write_count,
        "read_bytes": read_bytes,
        "write_bytes": write_bytes,
        "total_io_bytes": read_bytes + write_bytes,
    }


class M2ProcessMonitoringTests(unittest.TestCase):
    def test_process_enumeration_is_sorted_and_serializable(self) -> None:
        process_two = SimpleNamespace(
            info={
                "pid": 2,
                "name": "second",
                "status": "running",
                "username": None,
                "create_time": 20.0,
            }
        )
        process_one = SimpleNamespace(
            info={
                "pid": 1,
                "name": None,
                "status": None,
                "username": "alice",
                "create_time": 10.0,
            }
        )
        with patch(
            "monitoring.process_detector.psutil.process_iter",
            return_value=[process_two, process_one],
        ):
            result = get_running_processes()
        self.assertEqual([item["pid"] for item in result], [1, 2])
        self.assertEqual(result[0]["name"], "<unknown>")
        self.assertEqual(result[0]["status"], "unknown")

    def test_process_io_collection_skips_access_denied(self) -> None:
        good = Mock()
        good.info = {
            "pid": 10,
            "name": "writer",
            "status": "running",
            "username": "alice",
            "create_time": 10.0,
        }
        good.io_counters.return_value = SimpleNamespace(
            read_count=2,
            write_count=3,
            read_bytes=100,
            write_bytes=400,
        )
        denied = Mock()
        denied.info = {
            "pid": 11,
            "name": "denied",
            "status": "running",
            "username": None,
            "create_time": 11.0,
        }
        denied.io_counters.side_effect = psutil.AccessDenied(pid=11)

        with patch(
            "monitoring.process_io_monitor.psutil.process_iter",
            return_value=[denied, good],
        ):
            result = get_process_io_stats()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["pid"], 10)
        self.assertEqual(result[0]["total_io_bytes"], 500)

    def test_rate_calculation_uses_pid_and_creation_time(self) -> None:
        before = [
            process_stats(7, create_time=1.0, read_bytes=100, write_bytes=100),
            process_stats(8, create_time=2.0, read_bytes=50, write_bytes=50),
        ]
        after = [
            process_stats(7, create_time=1.0, read_bytes=300, write_bytes=500),
            process_stats(8, create_time=3.0, read_bytes=999, write_bytes=999),
        ]

        rates = calculate_process_io_rates(before, after, 2.0)
        self.assertEqual(len(rates), 1)
        self.assertEqual(rates[0]["pid"], 7)
        self.assertEqual(rates[0]["read_bytes_delta"], 200)
        self.assertEqual(rates[0]["write_bytes_delta"], 400)
        self.assertEqual(rates[0]["total_bytes_per_second"], 300.0)

    def test_top_consumers_use_current_window_not_lifetime_totals(self) -> None:
        quiet_historic = {
            **process_stats(
                1,
                create_time=1.0,
                read_bytes=10_000_000,
                write_bytes=0,
                name="historic",
            ),
            "sample_seconds": 1.0,
            "read_count_delta": 0,
            "write_count_delta": 0,
            "read_bytes_delta": 1,
            "write_bytes_delta": 0,
            "total_io_bytes_delta": 1,
            "read_bytes_per_second": 1.0,
            "write_bytes_per_second": 0.0,
            "total_bytes_per_second": 1.0,
            "read_operations_per_second": 0.0,
            "write_operations_per_second": 0.0,
        }
        active_now = {
            **process_stats(
                2,
                create_time=2.0,
                read_bytes=100,
                write_bytes=100,
                name="active",
            ),
            "sample_seconds": 1.0,
            "read_count_delta": 2,
            "write_count_delta": 3,
            "read_bytes_delta": 300,
            "write_bytes_delta": 700,
            "total_io_bytes_delta": 1000,
            "read_bytes_per_second": 300.0,
            "write_bytes_per_second": 700.0,
            "total_bytes_per_second": 1000.0,
            "read_operations_per_second": 2.0,
            "write_operations_per_second": 3.0,
        }

        ranked = rank_process_io([quiet_historic, active_now], limit=2)
        self.assertEqual(ranked[0]["name"], "active")
        self.assertGreater(ranked[0]["io_share_percent"], 99.0)

    def test_snapshot_uses_one_shared_sampling_window(self) -> None:
        disk = {
            "path": "/",
            "total_bytes": 1000,
            "used_bytes": 500,
            "free_bytes": 500,
            "usage_percent": 50.0,
        }
        system_before = {
            "read_count": 1,
            "write_count": 2,
            "read_bytes": 100,
            "write_bytes": 200,
            "read_time_ms": 0,
            "write_time_ms": 0,
        }
        system_after = {
            "read_count": 3,
            "write_count": 5,
            "read_bytes": 300,
            "write_bytes": 700,
            "read_time_ms": 0,
            "write_time_ms": 0,
        }
        process_before = [
            process_stats(9, create_time=1.0, read_bytes=100, write_bytes=100)
        ]
        process_after = [
            process_stats(
                9,
                create_time=1.0,
                read_bytes=300,
                write_bytes=500,
                name="worker",
            )
        ]
        times = iter([10.0, 12.0])
        sleeper = Mock()

        with (
            patch("monitoring.metrics_snapshot.get_disk_usage", return_value=disk),
            patch(
                "monitoring.metrics_snapshot.get_disk_io_stats",
                side_effect=[system_before, system_after],
            ),
            patch(
                "monitoring.metrics_snapshot.get_process_io_stats",
                side_effect=[process_before, process_after],
            ),
        ):
            snapshot = create_snapshot(
                ["/"],
                io_sample_interval=2.0,
                process_limit=3,
                sleeper=sleeper,
                clock=lambda: next(times),
            )

        sleeper.assert_called_once_with(2.0)
        self.assertEqual(snapshot["io"]["write_bytes_per_second"], 250.0)
        self.assertEqual(snapshot["processes"]["top_consumers"][0]["name"], "worker")

    def test_dashboard_and_report_render_process_activity(self) -> None:
        consumer = {
            **process_stats(
                42,
                create_time=1.0,
                read_bytes=100,
                write_bytes=200,
                name="database",
            ),
            "sample_seconds": 1.0,
            "read_count_delta": 1,
            "write_count_delta": 2,
            "read_bytes_delta": 100,
            "write_bytes_delta": 200,
            "total_io_bytes_delta": 300,
            "read_bytes_per_second": 100.0,
            "write_bytes_per_second": 200.0,
            "total_bytes_per_second": 300.0,
            "read_operations_per_second": 1.0,
            "write_operations_per_second": 2.0,
            "io_share_percent": 100.0,
            "percentage": 100.0,
        }
        snapshot = {
            "timestamp": "now",
            "disks": [],
            "io": {
                "read_count": 0,
                "write_count": 0,
                "read_bytes": 0,
                "write_bytes": 0,
                "read_time_ms": 0,
                "write_time_ms": 0,
                "sample_seconds": 1.0,
                "read_bytes_per_second": 0.0,
                "write_bytes_per_second": 0.0,
                "read_operations_per_second": 0.0,
                "write_operations_per_second": 0.0,
            },
            "processes": {
                "enabled": True,
                "accessible_after": 1,
                "matched": 1,
                "active": 1,
                "top_consumers": [consumer],
            },
            "errors": [],
        }
        dashboard = render_dashboard(snapshot)
        report = render_process_report(
            [{**consumer, "risk_level": get_risk_level(100.0)}]
        )
        self.assertIn("database", dashboard)
        self.assertIn("100.00%", dashboard)
        self.assertIn("DOMINANT", report)


if __name__ == "__main__":
    unittest.main()
