"""M9 combined historical reporting and analytics CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from analytics.history_analytics import analyze_history
from analytics.outcome_analytics import analyze_alert_events, analyze_optimization_events
from analytics.process_analytics import analyze_processes
from config.settings import (
    ALERT_FILE,
    ANALYTICS_DEFAULT_HISTORY_RECORDS,
    ANALYTICS_TOP_PROCESSES,
    HISTORY_FILE,
    OPTIMIZATION_JOURNAL_FILE,
)


def _load_jsonl(path: str | Path, *, limit: int | None = None) -> list[dict[str, Any]]:
    selected = Path(path)
    if limit is not None and limit < 0:
        raise ValueError("limit must be non-negative or None")
    if not selected.exists():
        return []
    records: list[dict[str, Any]] = []
    try:
        text = selected.read_text(encoding="utf-8")
    except OSError:
        return []
    stripped = text.lstrip()
    if stripped.startswith("["):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = []
        if isinstance(payload, list):
            records = [item for item in payload if isinstance(item, dict)]
    else:
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                records.append(item)
    if limit is not None:
        return records[-limit:] if limit else []
    return records


def build_analytics_report(
    snapshots: list[dict[str, Any]] | None,
    *,
    alert_events: list[dict[str, Any]] | None = None,
    optimization_events: list[dict[str, Any]] | None = None,
    top_processes: int = ANALYTICS_TOP_PROCESSES,
) -> dict[str, Any]:
    history = analyze_history(snapshots)
    processes = analyze_processes(snapshots, top_n=top_processes)
    alerts = analyze_alert_events(alert_events)
    optimization = analyze_optimization_events(optimization_events)
    return {
        "analysis_version": 1,
        "status": "OK" if history.get("record_count", 0) else "NO_DATA",
        "history": history,
        "processes": processes,
        "alerts": alerts,
        "optimization": optimization,
        "data_scope": {
            "snapshot_records": history.get("record_count", 0),
            "alert_events": alerts.get("event_count", 0),
            "optimization_events": optimization.get("event_count", 0),
            "retention_aware": True,
        },
    }


def render_analytics_report(report: dict[str, Any]) -> str:
    lines = ["DISK I/O REPORTING & ANALYTICS", "=" * 78]
    history = report.get("history", {})
    if report.get("status") == "NO_DATA":
        lines.append("No retained monitoring snapshots are available.")
        return "\n".join(lines)

    lines.extend(
        [
            f"Snapshots : {history.get('record_count', 0)}",
            f"Range     : {history.get('first_timestamp')} -> {history.get('last_timestamp')}",
            "",
            "Disk usage trends",
            "-" * 78,
        ]
    )
    for disk in history.get("disks", []):
        trend = disk.get("trend", {})
        slope = trend.get("slope_per_hour")
        slope_text = "n/a" if slope is None else f"{float(slope):+.3f} pp/hour"
        lines.append(
            f"{disk.get('path')}: latest={float(disk.get('latest_usage_percent',0)):.1f}% "
            f"max={float(disk.get('maximum_usage_percent',0)):.1f}% "
            f"change={float(disk.get('change_percentage_points',0)):+.1f} pp "
            f"trend={trend.get('direction')} ({slope_text})"
        )

    io = history.get("system_io", {})
    lines.extend(
        [
            "",
            "System I/O",
            "-" * 78,
            f"Average total : {float(io.get('average_total_bytes_per_second', 0.0)):.0f} bytes/s",
            f"P95 total     : {float(io.get('p95_total_bytes_per_second', 0.0)):.0f} bytes/s",
            f"Maximum total : {float(io.get('maximum_total_bytes_per_second', 0.0)):.0f} bytes/s",
            f"Trend         : {io.get('trend', {}).get('direction', 'UNKNOWN')}",
            "",
            "Top observed process consumers",
            "-" * 78,
        ]
    )
    for item in report.get("processes", {}).get("processes", []):
        lines.append(
            f"{item.get('name')}: samples={item.get('samples_seen',0)} "
            f"max={float(item.get('maximum_rate_bytes_per_second',0)):.0f} bytes/s "
            f"avg-share={float(item.get('average_share_percent',0)):.1f}% "
            f"anomalies={item.get('anomaly_events',0)} "
            f"runaways={item.get('runaway_events',0)}"
        )

    alerts = report.get("alerts", {})
    optimization = report.get("optimization", {})
    lines.extend(
        [
            "",
            "Alerts & optimization outcomes",
            "-" * 78,
            f"Alert events   : {alerts.get('event_count', 0)} | active={alerts.get('active_alert_count', 0)}",
            f"Recoveries     : {alerts.get('recovered_condition_count', 0)}",
            f"M7 sessions    : {optimization.get('session_count', 0)}",
            f"Actions applied: {optimization.get('actions_applied', 0)} | rolled back={optimization.get('actions_rolled_back', 0)}",
            "",
            "Note: analytics reflect retained JSONL history and retained top-consumer samples.",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate M9 trend, usage, process, alert, and optimization analytics."
    )
    parser.add_argument("--history-file", default=HISTORY_FILE)
    parser.add_argument("--alert-file", default=ALERT_FILE)
    parser.add_argument("--journal-file", default=OPTIMIZATION_JOURNAL_FILE)
    parser.add_argument("--limit", type=int, default=ANALYTICS_DEFAULT_HISTORY_RECORDS)
    parser.add_argument("--top-processes", type=int, default=ANALYTICS_TOP_PROCESSES)
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.limit < 0 or args.top_processes < 0:
        raise SystemExit("--limit and --top-processes must be non-negative")
    snapshots = _load_jsonl(args.history_file, limit=args.limit)
    alerts = _load_jsonl(args.alert_file)
    optimization = _load_jsonl(args.journal_file)
    report = build_analytics_report(
        snapshots,
        alert_events=alerts,
        optimization_events=optimization,
        top_processes=args.top_processes,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_analytics_report(report))


if __name__ == "__main__":
    main()
