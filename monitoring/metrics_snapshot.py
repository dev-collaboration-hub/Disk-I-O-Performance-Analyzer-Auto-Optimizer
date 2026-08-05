"""Unified M1, M2, and M3-ready monitoring snapshot collection."""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from config.settings import MINIMUM_PROCESS_IO_BYTES, TOP_PROCESS_LIMIT
from monitoring.disk_detector import get_mounted_disks
from monitoring.disk_monitor import calculate_disk_io_rates, get_disk_io_stats
from monitoring.disk_stats import get_disk_usage
from monitoring.process_io_monitor import (
    calculate_process_io_rates,
    get_process_io_stats,
)
from monitoring.top_disk_consumers import rank_process_io


def create_snapshot(
    paths: list[str] | None = None,
    *,
    io_sample_interval: float = 1.0,
    include_processes: bool = True,
    process_limit: int = TOP_PROCESS_LIMIT,
    minimum_process_io_bytes: int = MINIMUM_PROCESS_IO_BYTES,
    sleeper: Callable[[float], None] | None = None,
    clock: Callable[[], float] | None = None,
) -> dict[str, Any]:
    """Collect a versioned disk and process snapshot in one sample window."""

    if io_sample_interval < 0:
        raise ValueError("io_sample_interval must be non-negative")

    sleeper = sleeper or time.sleep
    clock = clock or time.monotonic
    selected_paths = paths or get_mounted_disks()
    disks: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for path in selected_paths:
        try:
            disks.append(get_disk_usage(path))
        except (FileNotFoundError, PermissionError, OSError) as error:
            errors.append(
                {
                    "path": str(path),
                    "error": type(error).__name__,
                    "message": str(error),
                }
            )

    system_before = get_disk_io_stats()
    process_before = get_process_io_stats() if include_processes else []
    started_at = clock()
    if io_sample_interval:
        sleeper(io_sample_interval)
    system_after = get_disk_io_stats()
    process_after = get_process_io_stats() if include_processes else []
    elapsed = max(clock() - started_at, 1e-9)

    io_stats = calculate_disk_io_rates(system_before, system_after, elapsed)
    process_rates = (
        calculate_process_io_rates(process_before, process_after, elapsed)
        if include_processes
        else []
    )
    top_consumers = rank_process_io(
        process_rates,
        limit=process_limit,
        minimum_io_bytes=minimum_process_io_bytes,
    )

    return {
        "schema_version": 3,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "disks": disks,
        "io": io_stats,
        "processes": {
            "enabled": include_processes,
            "sample_seconds": elapsed,
            "accessible_before": len(process_before),
            "accessible_after": len(process_after),
            "matched": len(process_rates),
            "active": sum(
                item["total_io_bytes_delta"] >= minimum_process_io_bytes
                for item in process_rates
            ),
            "top_consumers": top_consumers,
        },
        "errors": errors,
    }
