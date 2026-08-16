"""Real-time command-line dashboard for M1-M8 disk monitoring."""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import Any

from alerts.alert_engine import evaluate_alerts
from alerts.alert_store import AlertStore
from analysis.timeline_builder import EventTimeline, build_timeline_events
from config.settings import (
    ALERT_COOLDOWN_SECONDS, ALERT_FILE, ALERT_RETENTION_RECORDS,
    CRITICAL_DISK_USAGE_PERCENT, EVENT_RETENTION_RECORDS, EVENT_TIMELINE_FILE,
    HISTORY_FILE, HISTORY_RETENTION_RECORDS, IO_SAMPLE_INTERVAL_SECONDS,
    MINIMUM_PROCESS_IO_BYTES, PROCESS_PROFILE_HISTORY_SAMPLES,
    REFRESH_INTERVAL_SECONDS, ROOT_CAUSE_SUSTAINED_SAMPLES,
    SPIKE_IO_MIN_BYTES_PER_SECOND, SPIKE_IO_MULTIPLIER,
    SPIKE_USAGE_DELTA_PERCENT, TOP_PROCESS_LIMIT, WARNING_DISK_USAGE_PERCENT,
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


def _attach_m4_to_m8(
    snapshot: dict[str, Any], *, recent_history: list[dict[str, Any]],
    alert_store: AlertStore | None, alert_cooldown_seconds: float,
) -> None:
    attach_root_cause_analysis(snapshot, recent_history=recent_history)
    attach_process_behavior_analysis(snapshot, recent_history=recent_history)
    if alert_store is None:
        snapshot["alerts"] = {
            "analysis_version": 1, "timestamp": snapshot.get("timestamp"),
            "status": "DISABLED", "emitted": [], "emitted_count": 0,
            "suppressed_count": 0, "active_count": 0,
        }
        return
    try:
        evaluate_alerts(snapshot, store=alert_store, cooldown_seconds=alert_cooldown_seconds)
    except (OSError, TypeError, ValueError) as error:
        snapshot.setdefault("errors", []).append({
            "path": str(alert_store.alert_file),
            "error": type(error).__name__,
            "message": f"Alert processing failed: {error}",
        })
        snapshot["alerts"] = {
            "analysis_version": 1, "timestamp": snapshot.get("timestamp"),
            "status": "ERROR", "emitted": [], "emitted_count": 0,
            "suppressed_count": 0, "active_count": 0, "error": str(error),
        }


def persist_snapshot_history(
    snapshot: dict[str, Any], history: HistoryManager, timeline: EventTimeline, *,
    alert_store: AlertStore | None = None,
    alert_cooldown_seconds: float = ALERT_COOLDOWN_SECONDS,
    usage_delta_threshold: float = SPIKE_USAGE_DELTA_PERCENT,
    io_multiplier: float = SPIKE_IO_MULTIPLIER,
    io_minimum_bytes_per_second: float = SPIKE_IO_MIN_BYTES_PER_SECOND,
) -> list[dict[str, Any]]:
    previous = history.latest_snapshot()
    events = build_timeline_events(
        previous, snapshot, usage_delta_threshold=usage_delta_threshold,
        io_multiplier=io_multiplier,
        io_minimum_bytes_per_second=io_minimum_bytes_per_second,
    )
    snapshot["history"] = {
        "enabled": True, "record_number": history.count() + 1,
        "events_recorded": len(events),
        "spikes_detected": sum("SPIKE" in event["event_type"] for event in events),
        "recent_events": events[-3:],
        "history_file": str(history.history_file),
        "event_file": str(timeline.event_file),
    }
    window = max(ROOT_CAUSE_SUSTAINED_SAMPLES, PROCESS_PROFILE_HISTORY_SAMPLES)
    recent_history = history.load_history(limit=max(0, window - 1))
    recent_history.append(snapshot)
    _attach_m4_to_m8(
        snapshot, recent_history=recent_history, alert_store=alert_store,
        alert_cooldown_seconds=alert_cooldown_seconds,
    )
    history.save_snapshot(snapshot)
    timeline.record_events(events)
    return events


def _render_processes(snapshot: dict[str, Any]) -> list[str]:
    data = snapshot.get("processes", {})
    if not data.get("enabled", False):
        return ["", "Process-level monitoring: disabled"]
    lines = ["", "Top Process Disk I/O Consumers", "-" * 94]
    for process in data.get("top_consumers", []):
        lines.append(
            f"{process.get('pid'):>7}  {str(process.get('name', ''))[:28]:<28} "
            f"{format_size(process.get('total_bytes_per_second', 0.0)):>13}/s "
            f"{float(process.get('io_share_percent', 0.0)):>7.2f}%"
        )
    if not data.get("top_consumers"):
        lines.append("No process disk I/O activity observed during this sample.")
    return lines


def _render_history(snapshot: dict[str, Any]) -> list[str]:
    history = snapshot.get("history", {})
    if not history.get("enabled", False):
        return ["", "Historical data collection: disabled"]
    lines = [
        "", "M3 Historical Data & Event Timeline", "-" * 94,
        f"History record : {history.get('record_number', 0)}",
        f"Events recorded: {history.get('events_recorded', 0)} | "
        f"Spikes detected: {history.get('spikes_detected', 0)}",
    ]
    for event in history.get("recent_events", []):
        lines.append(f"{event.get('severity', 'INFO'):<8} | {event.get('event_type')} | {event.get('message')}")
    return lines


def _render_root_cause(snapshot: dict[str, Any]) -> list[str]:
    report = snapshot.get("root_cause", {})
    lines = ["", "M4 Root Cause Detection", "-" * 94]
    if not report:
        lines.append("Unavailable")
    elif report.get("status") != "BOTTLENECK_DETECTED":
        lines.append(report.get("message", "No bottleneck detected."))
    else:
        lines.extend([
            f"Severity   : {report.get('severity', 'UNKNOWN')}",
            f"Cause      : {report.get('cause', 'Unknown')}",
            f"Process    : {report.get('process') or 'n/a'}",
            f"Confidence : {float(report.get('confidence', 0.0)):.2f}%",
        ])
    return lines


def _render_process_behavior(snapshot: dict[str, Any]) -> list[str]:
    report = snapshot.get("process_behavior", {})
    lines = ["", "M5 Process Behavior Analysis", "-" * 94]
    if not report:
        lines.append("Unavailable")
        return lines
    lines.append(f"Status     : {report.get('status', 'UNKNOWN')}")
    lines.append(
        f"Profiles   : {report.get('profile_count', 0)} | "
        f"Anomalies: {report.get('anomaly_count', 0)} | "
        f"Runaways: {report.get('runaway_count', 0)}"
    )
    return lines


def _render_recommendations(snapshot: dict[str, Any]) -> list[str]:
    report = snapshot.get("recommendations", {})
    lines = ["", "M6 Optimization Recommendations", "-" * 94]
    if not report:
        lines.append("Unavailable")
        return lines
    lines.append(f"Status     : {report.get('status', 'UNKNOWN')}")
    for item in report.get("recommendations", [])[:3]:
        impact = item.get("impact", {})
        lines.append(
            f"{item.get('priority', 'LOW'):<8} | {item.get('title')} | "
            f"impact={impact.get('impact_level', 'LOW')} "
            f"({float(impact.get('impact_score', 0.0)):.1f}/100)"
        )
    return lines


def _render_alerts(snapshot: dict[str, Any]) -> list[str]:
    report = snapshot.get("alerts", {})
    lines = ["", "M8 Alerts & Notifications", "-" * 94]
    if not report:
        lines.append("Unavailable")
        return lines
    lines.append(f"Status     : {report.get('status', 'UNKNOWN')}")
    lines.append(
        f"Emitted    : {report.get('emitted_count', 0)} | "
        f"Suppressed: {report.get('suppressed_count', 0)} | "
        f"Active: {report.get('active_count', 0)}"
    )
    for event in report.get("emitted", []):
        lines.append(
            f"{event.get('severity', 'INFO'):<8} | "
            f"{event.get('event_type', 'EVENT'):<10} | {event.get('title')}"
        )
    return lines


def render_dashboard(snapshot: dict[str, Any]) -> str:
    lines = [
        "=" * 94, "DISK I/O PERFORMANCE ANALYZER — M8 ALERTING DASHBOARD",
        "=" * 94, f"Timestamp: {snapshot['timestamp']}",
    ]
    for disk in snapshot.get("disks", []):
        usage = float(disk["usage_percent"])
        lines.extend([
            "", f"Disk: {disk['path']}", "-" * 94,
            f"Status      : {usage_status(usage)}", f"Usage       : {usage:.1f}%",
            f"Total Space : {format_size(disk['total_bytes'])}",
            f"Used Space  : {format_size(disk['used_bytes'])}",
            f"Free Space  : {format_size(disk['free_bytes'])}",
        ])
    io = snapshot["io"]
    lines.extend([
        "", "System-wide Disk I/O", "-" * 94,
        f"Read Operations  : {io['read_count']:,}",
        f"Write Operations : {io['write_count']:,}",
        f"Bytes Read       : {format_size(io['read_bytes'])}",
        f"Bytes Written    : {format_size(io['write_bytes'])}",
        f"Read Rate        : {format_size(io['read_bytes_per_second'])}/s",
        f"Write Rate       : {format_size(io['write_bytes_per_second'])}/s",
        f"Read IOPS        : {io['read_operations_per_second']:.2f}",
        f"Write IOPS       : {io['write_operations_per_second']:.2f}",
    ])
    lines.extend(_render_processes(snapshot))
    lines.extend(_render_history(snapshot))
    lines.extend(_render_root_cause(snapshot))
    lines.extend(_render_process_behavior(snapshot))
    lines.extend(_render_recommendations(snapshot))
    lines.extend(_render_alerts(snapshot))
    if snapshot.get("errors"):
        lines.extend(["", "Collection Warnings", "-" * 94])
        for error in snapshot["errors"]:
            lines.append(f"{error['path']}: {error['error']} — {error['message']}")
    lines.append("=" * 94)
    return "\n".join(lines)


def run_dashboard(
    *, paths: list[str] | None = None,
    refresh_interval: float = REFRESH_INTERVAL_SECONDS,
    io_sample_interval: float = IO_SAMPLE_INTERVAL_SECONDS,
    process_limit: int = TOP_PROCESS_LIMIT,
    minimum_process_io_bytes: int = MINIMUM_PROCESS_IO_BYTES,
    include_processes: bool = True, log_file: str | None = None,
    enable_logging: bool = True, history_file: str = HISTORY_FILE,
    event_file: str = EVENT_TIMELINE_FILE, enable_history: bool = True,
    history_retention: int = HISTORY_RETENTION_RECORDS,
    event_retention: int = EVENT_RETENTION_RECORDS,
    spike_usage_delta: float = SPIKE_USAGE_DELTA_PERCENT,
    spike_io_multiplier: float = SPIKE_IO_MULTIPLIER,
    spike_io_minimum_rate: float = SPIKE_IO_MIN_BYTES_PER_SECOND,
    alert_file: str = ALERT_FILE, enable_alerts: bool = True,
    alert_retention: int = ALERT_RETENTION_RECORDS,
    alert_cooldown_seconds: float = ALERT_COOLDOWN_SECONDS,
    clear_between_updates: bool = True, once: bool = False,
    output: Callable[[str], None] = print,
) -> None:
    if refresh_interval < 0 or io_sample_interval < 0 or alert_cooldown_seconds < 0:
        raise ValueError("intervals must be non-negative")
    if min(process_limit, history_retention, event_retention, alert_retention) < 0:
        raise ValueError("limits and retention values must be non-negative")
    logger = MonitoringLogger(log_file) if log_file else MonitoringLogger()
    history = HistoryManager(history_file, max_records=history_retention)
    timeline = EventTimeline(event_file, max_records=event_retention)
    alert_store = AlertStore(alert_file, max_records=alert_retention) if enable_alerts else None
    if enable_logging:
        logger.log_event("M8 alerting disk monitoring started")
    try:
        while True:
            started = time.monotonic()
            snapshot = create_snapshot(
                paths, io_sample_interval=io_sample_interval,
                include_processes=include_processes, process_limit=process_limit,
                minimum_process_io_bytes=minimum_process_io_bytes,
            )
            if enable_history:
                try:
                    persist_snapshot_history(
                        snapshot, history, timeline, alert_store=alert_store,
                        alert_cooldown_seconds=alert_cooldown_seconds,
                        usage_delta_threshold=spike_usage_delta,
                        io_multiplier=spike_io_multiplier,
                        io_minimum_bytes_per_second=spike_io_minimum_rate,
                    )
                except (OSError, TypeError, ValueError) as error:
                    snapshot.setdefault("errors", []).append({
                        "path": str(history.history_file),
                        "error": type(error).__name__,
                        "message": f"History persistence failed: {error}",
                    })
                    snapshot["history"] = {"enabled": False, "error": str(error)}
                    _attach_m4_to_m8(
                        snapshot, recent_history=[snapshot], alert_store=alert_store,
                        alert_cooldown_seconds=alert_cooldown_seconds,
                    )
            else:
                snapshot["history"] = {"enabled": False}
                _attach_m4_to_m8(
                    snapshot, recent_history=[snapshot], alert_store=alert_store,
                    alert_cooldown_seconds=alert_cooldown_seconds,
                )
            if enable_logging:
                logger.log_snapshot(snapshot)
            if clear_between_updates:
                clear_screen()
            output(render_dashboard(snapshot))
            if once:
                break
            remaining = max(0.0, refresh_interval - (time.monotonic() - started))
            if remaining:
                time.sleep(remaining)
    except KeyboardInterrupt:
        if enable_logging:
            logger.log_event("M8 monitoring stopped by user")
        output("\nMonitoring stopped.")
