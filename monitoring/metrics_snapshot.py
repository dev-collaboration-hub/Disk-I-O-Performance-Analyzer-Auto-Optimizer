"""Unified M1 monitoring snapshot collection."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from monitoring.disk_detector import get_mounted_disks
from monitoring.disk_monitor import sample_disk_io_rates
from monitoring.disk_stats import get_disk_usage


def create_snapshot(
    paths: list[str] | None = None,
    *,
    io_sample_interval: float = 1.0,
) -> dict[str, Any]:
    """Collect mounted-disk utilization and system-wide disk I/O metrics.

    Permission or transient filesystem errors are recorded in ``errors`` and do
    not stop the remaining disks from being monitored.
    """

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

    io_stats = sample_disk_io_rates(io_sample_interval)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "disks": disks,
        "io": io_stats,
        "errors": errors,
    }


if __name__ == "__main__":
    print(create_snapshot())
