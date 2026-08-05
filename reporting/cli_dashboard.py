"""Real-time command-line dashboard for M1 disk metrics."""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import Any

from config.settings import (
    CRITICAL_DISK_USAGE_PERCENT,
    IO_SAMPLE_INTERVAL_SECONDS,
    REFRESH_INTERVAL_SECONDS,
    WARNING_DISK_USAGE_PERCENT,
)
from monitoring.metrics_snapshot import create_snapshot
from utils.formatter import format_size
from utils.logger import MonitoringLogger


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def usage_status(usage_percent: float) -> str:
    if usage_percent >= CRITICAL_DISK_USAGE_PERCENT:
        return "CRITICAL"
    if usage_percent >= WARNING_DISK_USAGE_PERCENT:
        return "WARNING"
    return "NORMAL"


def render_dashboard(snapshot: dict[str, Any]) -> str:
    """Render a monitoring snapshot as a readable console dashboard."""

    lines = [
        "=" * 72,
        "DISK I/O PERFORMANCE ANALYZER — M1 MONITORING DASHBOARD",
        "=" * 72,
        f"Timestamp: {snapshot['timestamp']}",
    ]

    disks = snapshot.get("disks", [])
    if not disks:
        lines.extend(["", "No accessible disks were detected."])

    for disk in disks:
        usage = float(disk["usage_percent"])
        lines.extend(
            [
                "",
                f"Disk: {disk['path']}",
                "-" * 72,
                f"Status      : {usage_status(usage)}",
                f"Usage       : {usage:.1f}%",
                f"Total Space : {format_size(disk['total_bytes'])}",
                f"Used Space  : {format_size(disk['used_bytes'])}",
                f"Free Space  : {format_size(disk['free_bytes'])}",
            ]
        )

    io_stats = snapshot["io"]
    lines.extend(
        [
            "",
            "System-wide Disk I/O",
            "-" * 72,
            f"Read Operations  : {io_stats['read_count']:,}",
            f"Write Operations : {io_stats['write_count']:,}",
            f"Bytes Read       : {format_size(io_stats['read_bytes'])}",
            f"Bytes Written    : {format_size(io_stats['write_bytes'])}",
            f"Read Rate        : {format_size(io_stats['read_bytes_per_second'])}/s",
            f"Write Rate       : {format_size(io_stats['write_bytes_per_second'])}/s",
            f"Read IOPS        : {io_stats['read_operations_per_second']:.2f}",
            f"Write IOPS       : {io_stats['write_operations_per_second']:.2f}",
        ]
    )

    errors = snapshot.get("errors", [])
    if errors:
        lines.extend(["", "Collection Warnings", "-" * 72])
        for error in errors:
            lines.append(f"{error['path']}: {error['error']} — {error['message']}")

    lines.append("=" * 72)
    return "\n".join(lines)


def run_dashboard(
    *,
    paths: list[str] | None = None,
    refresh_interval: float = REFRESH_INTERVAL_SECONDS,
    io_sample_interval: float = IO_SAMPLE_INTERVAL_SECONDS,
    log_file: str | None = None,
    enable_logging: bool = True,
    clear_between_updates: bool = True,
    once: bool = False,
    output: Callable[[str], None] = print,
) -> None:
    """Run the live dashboard until interrupted, or once when requested."""

    if refresh_interval < 0 or io_sample_interval < 0:
        raise ValueError("refresh and sample intervals must be non-negative")

    logger = MonitoringLogger(log_file) if log_file else MonitoringLogger()
    logger.log_event("M1 disk monitoring started") if enable_logging else None

    try:
        while True:
            cycle_started = time.monotonic()
            snapshot = create_snapshot(paths, io_sample_interval=io_sample_interval)
            if enable_logging:
                logger.log_snapshot(snapshot)

            if clear_between_updates:
                clear_screen()
            output(render_dashboard(snapshot))

            if once:
                break

            elapsed = time.monotonic() - cycle_started
            remaining = max(0.0, refresh_interval - elapsed)
            if remaining:
                time.sleep(remaining)
    except KeyboardInterrupt:
        if enable_logging:
            logger.log_event("M1 disk monitoring stopped by user")
        output("\nMonitoring stopped.")
