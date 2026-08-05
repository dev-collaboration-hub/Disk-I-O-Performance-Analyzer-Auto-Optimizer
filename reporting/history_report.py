"""Historical metrics, event timeline, and spike reporting for M3."""

from __future__ import annotations

import argparse
import json
from typing import Any

from analysis.timeline_builder import EventTimeline
from config.settings import EVENT_TIMELINE_FILE, HISTORY_FILE
from utils.formatter import format_size
from utils.history_manager import HistoryManager


def build_history_report(
    history: HistoryManager,
    timeline: EventTimeline,
    *,
    limit: int = 20,
) -> dict[str, Any]:
    if limit < 0:
        raise ValueError("limit must be non-negative")
    events = timeline.load_events(limit=limit, newest_first=True)
    snapshots = history.load_history(limit=limit, newest_first=True)
    return {
        "summary": history.summarize(),
        "recent_snapshots": snapshots,
        "recent_events": events,
        "recent_spikes": [
            item
            for item in events
            if "SPIKE" in str(item.get("event_type", ""))
        ],
    }


def render_history_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "M3 Historical Disk Activity Report",
        "=" * 96,
        f"Snapshots stored : {summary['record_count']}",
        f"First timestamp  : {summary['first_timestamp'] or '-'}",
        f"Latest timestamp : {summary['last_timestamp'] or '-'}",
        f"Peak disk usage  : {summary['maximum_disk_usage_percent']:.1f}%",
        (
            "Peak throughput  : "
            f"{format_size(summary['maximum_io_bytes_per_second'])}/s"
        ),
        "",
        "Recent Events",
        "-" * 96,
    ]
    events = report["recent_events"]
    if not events:
        lines.append("No events recorded.")
    else:
        for event in events:
            lines.append(
                f"{event.get('timestamp')} | "
                f"{event.get('severity', 'INFO'):<8} | "
                f"{event.get('event_type')} | {event.get('message')}"
            )
    lines.extend(["", f"Recent spikes: {len(report['recent_spikes'])}"])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect M3 metrics history and event timeline."
    )
    parser.add_argument("--history-file", default=HISTORY_FILE)
    parser.add_argument("--event-file", default=EVENT_TIMELINE_FILE)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    report = build_history_report(
        HistoryManager(args.history_file, max_records=None),
        EventTimeline(args.event_file, max_records=None),
        limit=args.limit,
    )
    if args.as_json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_history_report(report))


if __name__ == "__main__":
    main()
