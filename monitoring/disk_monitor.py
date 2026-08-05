"""System-wide cumulative disk I/O counters and rate sampling."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any, TypedDict

import psutil


class DiskIOStats(TypedDict):
    read_count: int
    write_count: int
    read_bytes: int
    write_bytes: int
    read_time_ms: int
    write_time_ms: int


class DiskIORates(DiskIOStats):
    sample_seconds: float
    read_bytes_per_second: float
    write_bytes_per_second: float
    read_operations_per_second: float
    write_operations_per_second: float


def _counter_value(counter: Any, name: str) -> int:
    return int(getattr(counter, name, 0) or 0)


def get_disk_io_stats() -> DiskIOStats:
    """Return cumulative system-wide disk read/write counters.

    A zero-filled result is returned when the operating system does not expose
    disk I/O counters, allowing the dashboard to remain operational.
    """

    counter = psutil.disk_io_counters()
    if counter is None:
        return {
            "read_count": 0,
            "write_count": 0,
            "read_bytes": 0,
            "write_bytes": 0,
            "read_time_ms": 0,
            "write_time_ms": 0,
        }

    return {
        "read_count": _counter_value(counter, "read_count"),
        "write_count": _counter_value(counter, "write_count"),
        "read_bytes": _counter_value(counter, "read_bytes"),
        "write_bytes": _counter_value(counter, "write_bytes"),
        "read_time_ms": _counter_value(counter, "read_time"),
        "write_time_ms": _counter_value(counter, "write_time"),
    }


def _non_negative_delta(current: int, previous: int) -> int:
    # Counters can reset after reboot or device changes. Negative rates are not
    # meaningful, so treat a reset as a fresh counter window.
    return max(0, current - previous)


def sample_disk_io_rates(
    interval_seconds: float = 1.0,
    *,
    sleeper: Callable[[float], None] | None = None,
    clock: Callable[[], float] | None = None,
) -> DiskIORates:
    """Sample disk I/O and calculate read/write throughput and operation rates."""

    if interval_seconds < 0:
        raise ValueError("interval_seconds must be non-negative")

    sleeper = sleeper or time.sleep
    clock = clock or time.monotonic

    before = get_disk_io_stats()
    started_at = clock()
    if interval_seconds:
        sleeper(interval_seconds)
    after = get_disk_io_stats()
    elapsed = max(clock() - started_at, 1e-9)

    read_bytes_delta = _non_negative_delta(after["read_bytes"], before["read_bytes"])
    write_bytes_delta = _non_negative_delta(after["write_bytes"], before["write_bytes"])
    read_count_delta = _non_negative_delta(after["read_count"], before["read_count"])
    write_count_delta = _non_negative_delta(after["write_count"], before["write_count"])

    return {
        **after,
        "sample_seconds": elapsed,
        "read_bytes_per_second": read_bytes_delta / elapsed,
        "write_bytes_per_second": write_bytes_delta / elapsed,
        "read_operations_per_second": read_count_delta / elapsed,
        "write_operations_per_second": write_count_delta / elapsed,
    }


if __name__ == "__main__":
    print(sample_disk_io_rates())
