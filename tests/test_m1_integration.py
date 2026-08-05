"""M1 unit and integration tests using only Python's standard library."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from monitoring.disk_capacity import get_disk_capacity
from monitoring.disk_detector import get_mounted_disks
from monitoring.disk_monitor import get_disk_io_stats, sample_disk_io_rates
from monitoring.disk_stats import get_disk_usage, get_disk_usage_percentage
from monitoring.metrics_snapshot import create_snapshot
from reporting.cli_dashboard import render_dashboard
from utils.logger import MonitoringLogger


class M1MonitoringTests(unittest.TestCase):
    def test_detects_unique_mountpoints(self) -> None:
        partitions = [
            SimpleNamespace(mountpoint="/"),
            SimpleNamespace(mountpoint="/"),
            SimpleNamespace(mountpoint="/data"),
        ]
        with patch("monitoring.disk_detector.psutil.disk_partitions", return_value=partitions):
            self.assertEqual(get_mounted_disks(), ["/", "/data"])

    def test_capacity_has_consistent_byte_keys(self) -> None:
        usage = SimpleNamespace(total=1000, used=600, free=400)
        with patch("monitoring.disk_capacity.shutil.disk_usage", return_value=usage):
            result = get_disk_capacity("/")
        self.assertEqual(result["total_bytes"], 1000)
        self.assertEqual(result["used_bytes"], 600)
        self.assertEqual(result["free_bytes"], 400)

    def test_usage_percentage_interface(self) -> None:
        usage = SimpleNamespace(total=1000, used=750, free=250, percent=75.0)
        with patch("monitoring.disk_stats.psutil.disk_usage", return_value=usage):
            self.assertEqual(get_disk_usage("/")["usage_percent"], 75.0)
            self.assertEqual(get_disk_usage_percentage("/"), 75.0)

    def test_io_counters_and_rates(self) -> None:
        before = SimpleNamespace(
            read_count=10,
            write_count=20,
            read_bytes=1000,
            write_bytes=2000,
            read_time=30,
            write_time=40,
        )
        after = SimpleNamespace(
            read_count=14,
            write_count=26,
            read_bytes=3000,
            write_bytes=5000,
            read_time=35,
            write_time=48,
        )
        with (
            patch("monitoring.disk_monitor.psutil.disk_io_counters", side_effect=[before, after]),
            patch("monitoring.disk_monitor.time.monotonic", side_effect=[10.0, 12.0]),
            patch("monitoring.disk_monitor.time.sleep") as sleep_mock,
        ):
            result = sample_disk_io_rates(2.0)
        sleep_mock.assert_called_once_with(2.0)
        self.assertEqual(result["read_bytes_per_second"], 1000.0)
        self.assertEqual(result["write_bytes_per_second"], 1500.0)
        self.assertEqual(result["read_operations_per_second"], 2.0)
        self.assertEqual(result["write_operations_per_second"], 3.0)

    def test_missing_io_counters_returns_zeroes(self) -> None:
        with patch("monitoring.disk_monitor.psutil.disk_io_counters", return_value=None):
            result = get_disk_io_stats()
        self.assertEqual(result["read_bytes"], 0)
        self.assertEqual(result["write_count"], 0)

    def test_structured_logger_writes_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "logs" / "metrics.jsonl"
            logger = MonitoringLogger(path)
            logger.log_snapshot({"timestamp": "now", "disks": [], "io": {}, "errors": []})
            record = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(record["record_type"], "metrics")
        self.assertEqual(record["timestamp"], "now")

    def test_end_to_end_snapshot_and_dashboard(self) -> None:
        disk = {
            "path": "/",
            "total_bytes": 1000,
            "used_bytes": 500,
            "free_bytes": 500,
            "usage_percent": 50.0,
        }
        io = {
            "read_count": 10,
            "write_count": 20,
            "read_bytes": 100,
            "write_bytes": 200,
            "read_time_ms": 1,
            "write_time_ms": 2,
            "sample_seconds": 1.0,
            "read_bytes_per_second": 10.0,
            "write_bytes_per_second": 20.0,
            "read_operations_per_second": 1.0,
            "write_operations_per_second": 2.0,
        }
        with (
            patch("monitoring.metrics_snapshot.get_disk_usage", return_value=disk),
            patch("monitoring.metrics_snapshot.sample_disk_io_rates", return_value=io),
        ):
            snapshot = create_snapshot(["/"], io_sample_interval=0)
        dashboard = render_dashboard(snapshot)
        self.assertIn("Usage       : 50.0%", dashboard)
        self.assertIn("Read Operations", dashboard)
        self.assertIn("Write Rate", dashboard)


if __name__ == "__main__":
    unittest.main()
