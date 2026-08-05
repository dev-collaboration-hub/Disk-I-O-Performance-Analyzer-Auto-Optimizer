"""Per-process cumulative disk I/O counters and sampled rates."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any, TypedDict

import psutil


class ProcessIOStats(TypedDict):
    pid: int
    name: str
    status: str
    username: str | None
    create_time: float | None
    read_count: int
    write_count: int
    read_bytes: int
    write_bytes: int
    total_io_bytes: int


class ProcessIORates(ProcessIOStats):
    sample_seconds: float
    read_count_delta: int
    write_count_delta: int
    read_bytes_delta: int
    write_bytes_delta: int
    total_io_bytes_delta: int
    read_bytes_per_second: float
    write_bytes_per_second: float
    total_bytes_per_second: float
    read_operations_per_second: float
    write_operations_per_second: float


_PROCESS_EXCEPTIONS = (
    psutil.NoSuchProcess,
    psutil.AccessDenied,
    psutil.ZombieProcess,
)


def _counter_value(counter: Any, name: str) -> int:
    return int(getattr(counter, name, 0) or 0)


def _process_identity(process: ProcessIOStats) -> tuple[int, float | None]:
    return process["pid"], process["create_time"]


def get_process_io_stats() -> list[ProcessIOStats]:
    """Return cumulative I/O counters for all accessible processes."""

    results: list[ProcessIOStats] = []
    attributes = ["pid", "name", "status", "username", "create_time"]

    for process in psutil.process_iter(attributes, ad_value=None):
        try:
            info = process.info
            counters = process.io_counters()
            read_bytes = _counter_value(counters, "read_bytes")
            write_bytes = _counter_value(counters, "write_bytes")
            results.append(
                {
                    "pid": int(info["pid"]),
                    "name": str(info.get("name") or "<unknown>"),
                    "status": str(info.get("status") or "unknown"),
                    "username": (
                        str(info["username"]) if info.get("username") is not None else None
                    ),
                    "create_time": (
                        float(info["create_time"])
                        if info.get("create_time") is not None
                        else None
                    ),
                    "read_count": _counter_value(counters, "read_count"),
                    "write_count": _counter_value(counters, "write_count"),
                    "read_bytes": read_bytes,
                    "write_bytes": write_bytes,
                    "total_io_bytes": read_bytes + write_bytes,
                }
            )
        except (*_PROCESS_EXCEPTIONS, AttributeError, NotImplementedError):
            continue

    results.sort(key=lambda item: item["pid"])
    return results


def _non_negative_delta(current: int, previous: int) -> int:
    return max(0, current - previous)


def calculate_process_io_rates(
    before: list[ProcessIOStats],
    after: list[ProcessIOStats],
    elapsed_seconds: float,
) -> list[ProcessIORates]:
    """Calculate per-process I/O activity over one sampling window.

    A process is matched by both PID and creation time, preventing a reused PID
    from inheriting counters from a process that exited during the sample.
    """

    elapsed = max(float(elapsed_seconds), 1e-9)
    previous_by_identity = {_process_identity(item): item for item in before}
    rates: list[ProcessIORates] = []

    for current in after:
        previous = previous_by_identity.get(_process_identity(current))
        if previous is None:
            continue

        read_count_delta = _non_negative_delta(
            current["read_count"], previous["read_count"]
        )
        write_count_delta = _non_negative_delta(
            current["write_count"], previous["write_count"]
        )
        read_bytes_delta = _non_negative_delta(
            current["read_bytes"], previous["read_bytes"]
        )
        write_bytes_delta = _non_negative_delta(
            current["write_bytes"], previous["write_bytes"]
        )
        total_delta = read_bytes_delta + write_bytes_delta

        rates.append(
            {
                **current,
                "sample_seconds": elapsed,
                "read_count_delta": read_count_delta,
                "write_count_delta": write_count_delta,
                "read_bytes_delta": read_bytes_delta,
                "write_bytes_delta": write_bytes_delta,
                "total_io_bytes_delta": total_delta,
                "read_bytes_per_second": read_bytes_delta / elapsed,
                "write_bytes_per_second": write_bytes_delta / elapsed,
                "total_bytes_per_second": total_delta / elapsed,
                "read_operations_per_second": read_count_delta / elapsed,
                "write_operations_per_second": write_count_delta / elapsed,
            }
        )

    return rates


def sample_process_io_rates(
    interval_seconds: float = 1.0,
    *,
    sleeper: Callable[[float], None] | None = None,
    clock: Callable[[], float] | None = None,
    collector: Callable[[], list[ProcessIOStats]] | None = None,
) -> list[ProcessIORates]:
    """Sample accessible processes and calculate their current I/O rates."""

    if interval_seconds < 0:
        raise ValueError("interval_seconds must be non-negative")

    sleeper = sleeper or time.sleep
    clock = clock or time.monotonic
    collector = collector or get_process_io_stats

    before = collector()
    started_at = clock()
    if interval_seconds:
        sleeper(interval_seconds)
    after = collector()
    return calculate_process_io_rates(before, after, clock() - started_at)


if __name__ == "__main__":
    for item in sample_process_io_rates():
        print(item)
