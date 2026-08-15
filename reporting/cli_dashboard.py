"""Real-time command-line dashboard for M1-M5 disk monitoring."""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import Any

from analysis.timeline_builder import EventTimeline, build_timeline_events
from config.settings import (
    CRITICAL_DISK_USAGE_PERCENT,
    EVENT_RETENTION_RECORDS,
    EVENT_TIMELINE_FILE,
    HISTORY_FILE,
    HISTORY_RETENTION_RECORDS,
    IO_SAMPLE_INTERVAL_SECONDS,
    MINIMUM_PROCESS_IO_BYTES,
    PROCESS_PROFILE_HISTORY_SAMPLES,
    REFRESH_INTERVAL_SECONDS,
    ROOT_CAUSE_SUSTAINED_SAMPLES,
    SPIKE_IO_MIN_BYTES_PER_SECOND,
    SPIKE_IO_MULTIPLIER,
    SPIKE_USAGE_DELTA_PERCENT,
    TOP_PROCESS_LIMIT,
    WARNING_DISK_USAGE_PERCENT,
)
from monitoring.metrics_snapshot import create_snapshot
from reporting.process_behavior_report import attach_process_behavior_analysis
from reporting.root_cause_report import attach_root_cause_analysis
from utils.formatter import format_size
from utils.history_manager import HistoryManager
from utils.logger import MonitoringLogger


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def usage_status(usage_percent: float) -> str:
    if usage_percent >= CRITICAL_DISK_USAGE_PERCENT:
        return "CRITICAL"
    if usage_percent >= WARNING_DISK_USAGE_PERCENT:
        return "WARNING"
    return "NORMAL"


def persist_snapshot_history(
    snapshot: dict[str, Any],
    history: HistoryManager,
    timeline: EventTimeline,
    *,
    usage_delta_threshold: float = SPIKE_USAGE_DELTA_PERCENT,
    io_multiplier: float = SPIKE_IO_MULTIPLIER,
    io_minimum_bytes_per_second: float = SPIKE_IO_MIN_BYTES_PER_SECOND,
) -> list[dict[str, Any]]:
    """Persist one snapshot with M3 events and M4-M5 analysis."""

    previous = history.latest_snapshot()
    events = build_timeline_events(
        previous,
        snapshot,
        usage_delta_threshold=usage_delta_threshold,
        io_multiplier=io_multiplier,
        io_minimum_bytes_per_second=io_minimum_bytes_per_second,
    )
    record_number = history.count() + 1
    snapshot["history"] = {
        "enabled": True,
        "record_number": record_number,
        "events_recorded": len(events),
        "spikes_detected": sum(
            "SPIKE" in event["event_type"] for event in events
        ),
        "recent_events": events[-3:],
        "history_file": str(history.history_file),
        "event_file": str(timeline.event_file),
    }

    history_window = max(
        ROOT_CAUSE_SUSTAINED_SAMPLES,
        PROCESS_PROFILE_HISTORY_SAMPLES,
    )
    recent_history = history.load_history(
        limit=max(0, history_window - 1)
    )
    recent_history.append(snapshot)

    attach_root_cause_analysis(
        snapshot,
        recent_history=recent_history,
    )
    attach_process_behavior_analysis(
        snapshot,
        recent_history=recent_history,
    )

    history.save_snapshot(snapshot)
    timeline.record_events(events)
    return events


def _render_processes(snapshot: dict[str, Any]) -> list[str]:
    process_data = snapshot.get("processes", {})
    if not process_data.get("enabled", False):
        return ["", "Process-level monitoring: disabled"]

    lines = [
        "",
        "Top Process Disk I/O Consumers",
        "-" * 94,
        f"{'PID':>7}  {'PROCESS':<28} {'READ/s':>13} {'WRITE/s':>13} "
        f"{'TOTAL/s':>13} {'SHARE':>8}",
    ]
    consumers = process_data.get("top_consumers", [])
    if not consumers:
        lines.append("No process disk I/O activity observed during this sample.")
    else:
        for process in consumers:
            lines.append(
                f"{process['pid']:>7}  {process['name'][:28]:<28} "
                f"{format_size(process['read_bytes_per_second']):>13} "
                f"{format_size(process['write_bytes_per_second']):>13} "
                f"{format_size(process['total_bytes_per_second']):>13} "
                f"{process['io_share_percent']:>7.2f}%"
            )
    lines.append(
        "Accessible processes: "
        f"{process_data.get('accessible_after', 0)} | "
        f"Matched: {process_data.get('matched', 0)} | "
        f"Active: {process_data.get('active', 0)}"
    )
    return lines


def _render_history(snapshot: dict[str, Any]) -> list[str]:
    history = snapshot.get("history", {})
    if not history.get("enabled", False):
        return ["", "Historical data collection: disabled"]

    lines = [
        "",
        "M3 Historical Data & Event Timeline",
        "-" * 94,
        f"History record : {history.get('record_number', 0)}",
        f"Events recorded: {history.get('events_recorded', 0)} | "
        f"Spikes detected: {history.get('spikes_detected', 0)}",
    ]
    for event in history.get("recent_events", []):
        lines.append(
            f"{event.get('severity', 'INFO'):<8} | "
            f"{event.get('event_type')} | {event.get('message')}"
        )
    return lines


def _render_root_cause(snapshot: dict[str, Any]) -> list[str]:
    report = snapshot.get("root_cause", {})
    if not report:
        return ["", "M4 Root Cause Detection: unavailable"]

    lines = [
        "",
        "M4 Root Cause Detection",
        "-" * 94,
    ]
    if report.get("status") != "BOTTLENECK_DETECTED":
        lines.append(report.get("message", "No bottleneck detected."))
        return lines

    lines.extend(
        [
            f"Severity   : {report.get('severity', 'UNKNOWN')}",
            f"Cause      : {report.get('cause', 'Unknown')}",
            f"Process    : {report.get('process') or 'n/a'}",
            f"Confidence : {float(report.get('confidence', 0.0)):.2f}%",
            "Signals    : "
            + ", ".join(report.get("signals", [])),
        ]
    )
    for item in report.get("evidence", []):
        lines.append(f"Evidence   : {item}")
    lines.append(
        f"Action     : {report.get('recommendation', 'Continue monitoring.')}"
    )
    return lines


def _render_process_behavior(snapshot: dict[str, Any]) -> list[str]:
    report = snapshot.get("process_behavior", {})
    if not report:
        return ["", "M5 Process Behavior Analysis: unavailable"]

    lines = [
        "",
        "M5 Process Behavior Analysis",
        "-" * 94,
        f"Status     : {report.get('status', 'UNKNOWN')}",
        (
            f"Profiles   : {report.get('profile_count', 0)} | "
            f"Anomalies: {report.get('anomaly_count', 0)} | "
            f"Runaways: {report.get('runaway_count', 0)}"
        ),
    ]

    for runaway in report.get("runaways", []):
        lines.append(
            "RUNAWAY    : "
            f"{runaway.get('name')} (PID {runaway.get('pid')}) | "
            f"{format_size(runaway.get('latest_rate_bytes_per_second', 0.0))}/s | "
            f"{float(runaway.get('latest_share_percent', 0.0)):.1f}% share | "
            f"{runaway.get('severity', 'WARNING')}"
        )

    for anomaly in report.get("anomalies", []):
        lines.append(
            "ANOMALY    : "
            f"{anomaly.get('name')} (PID {anomaly.get('pid')}) | "
            + ", ".join(anomaly.get("signals", []))
            + f" | {anomaly.get('severity', 'WARNING')}"
        )

    if not report.get("runaways") and not report.get("anomalies"):
        profiles = report.get("profiles", [])
        if profiles:
            top = profiles[0]
            lines.append(
                "Top profile: "
                f"{top.get('name')} | "
                f"{format_size(top.get('latest_rate_bytes_per_second', 0.0))}/s | "
                f"trend={top.get('trend', 'UNKNOWN')}"
            )
        else:
            lines.append(report.get("message", "No process activity."))
    return lines


def render_dashboard(snapshot: dict[str, Any]) -> str:
    lines = [
        "=" * 94,
        "DISK I/O PERFORMANCE ANALYZER — M5 PROCESS-BEHAVIOR MONITORING DASHBOARD",
        "=" * 94,
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
                "-" * 94,
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
            "-" * 94,
            f"Read Operations  : {io_stats['read_count']:,}",
            f"Write Operations : {io_stats['write_count']:,}",
            f"Bytes Read       : {format_size(io_stats['read_bytes'])}",
            f"Bytes Written    : {format_size(io_stats['write_bytes'])}",
            (
                "Read Rate        : "
                f"{format_size(io_stats['read_bytes_per_second'])}/s"
            ),
            (
                "Write Rate       : "
                f"{format_size(io_stats['write_bytes_per_second'])}/s"
            ),
            f"Read IOPS        : {io_stats['read_operations_per_second']:.2f}",
            f"Write IOPS       : {io_stats['write_operations_per_second']:.2f}",
        ]
    )
    lines.extend(_render_processes(snapshot))
    lines.extend(_render_history(snapshot))
    lines.extend(_render_root_cause(snapshot))
    lines.extend(_render_process_behavior(snapshot))

    errors = snapshot.get("errors", [])
    if errors:
        lines.extend(["", "Collection Warnings", "-" * 94])
        for error in errors:
            lines.append(
                f"{error['path']}: {error['error']} — {error['message']}"
            )
    lines.append("=" * 94)
    return "\n".join(lines)


def run_dashboard(
    *,
    paths: list[str] | None = None,
    refresh_interval: float = REFRESH_INTERVAL_SECONDS,
    io_sample_interval: float = IO_SAMPLE_INTERVAL_SECONDS,
    process_limit: int = TOP_PROCESS_LIMIT,
    minimum_process_io_bytes: int = MINIMUM_PROCESS_IO_BYTES,
    include_processes: bool = True,
    log_file: str | None = None,
    enable_logging: bool = True,
    history_file: str = HISTORY_FILE,
    event_file: str = EVENT_TIMELINE_FILE,
    enable_history: bool = True,
    history_retention: int = HISTORY_RETENTION_RECORDS,
    event_retention: int = EVENT_RETENTION_RECORDS,
    spike_usage_delta: float = SPIKE_USAGE_DELTA_PERCENT,
    spike_io_multiplier: float = SPIKE_IO_MULTIPLIER,
    spike_io_minimum_rate: float = SPIKE_IO_MIN_BYTES_PER_SECOND,
    clear_between_updates: bool = True,
    once: bool = False,
    output: Callable[[str], None] = print,
) -> None:
    if refresh_interval < 0 or io_sample_interval < 0:
        raise ValueError("refresh and sample intervals must be non-negative")
    if process_limit < 0 or history_retention < 0 or event_retention < 0:
        raise ValueError("limits and retention values must be non-negative")

    logger = MonitoringLogger(log_file) if log_file else MonitoringLogger()
    history = HistoryManager(history_file, max_records=history_retention)
    timeline = EventTimeline(event_file, max_records=event_retention)
    if enable_logging:
        logger.log_event("M5 process-behavior disk monitoring started")
    if enable_history:
        timeline.record_event(
            {
                "event_type": "MONITORING_STARTED",
                "severity": "INFO",
                "source": "cli_dashboard",
                "message": "M5 process-behavior disk monitoring started.",
            }
        )

    try:
        while True:
            cycle_started = time.monotonic()
            snapshot = create_snapshot(
                paths,
                io_sample_interval=io_sample_interval,
                include_processes=include_processes,
                process_limit=process_limit,
                minimum_process_io_bytes=minimum_process_io_bytes,
            )
            if enable_history:
                try:
                    persist_snapshot_history(
                        snapshot,
                        history,
                        timeline,
                        usage_delta_threshold=spike_usage_delta,
                        io_multiplier=spike_io_multiplier,
                        io_minimum_bytes_per_second=spike_io_minimum_rate,
                    )
                except (OSError, TypeError, ValueError) as error:
                    snapshot.setdefault("errors", []).append(
                        {
                            "path": str(history.history_file),
                            "error": type(error).__name__,
                            "message": f"History persistence failed: {error}",
                        }
                    )
                    snapshot["history"] = {
                        "enabled": False,
                        "error": str(error),
                    }
                    attach_root_cause_analysis(
                        snapshot,
                        recent_history=[snapshot],
                    )
                    attach_process_behavior_analysis(
                        snapshot,
                        recent_history=[snapshot],
                    )
            else:
                snapshot["history"] = {"enabled": False}
                attach_root_cause_analysis(
                    snapshot,
                    recent_history=[snapshot],
                )
                attach_process_behavior_analysis(
                    snapshot,
                    recent_history=[snapshot],
                )

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
            logger.log_event("M5 monitoring stopped by user")
        if enable_history:
            timeline.record_event(
                {
                    "event_type": "MONITORING_STOPPED",
                    "severity": "INFO",
                    "source": "cli_dashboard",
                    "message": "M5 monitoring stopped by user.",
                }
            )
        output("\nMonitoring stopped.")
