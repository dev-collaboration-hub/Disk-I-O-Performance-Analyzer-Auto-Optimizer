"""Persistent event timeline and event derivation for M3."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from analysis.spike_detector import detect_snapshot_spikes
from config.settings import (
    CRITICAL_DISK_USAGE_PERCENT,
    EVENT_RETENTION_RECORDS,
    EVENT_TIMELINE_FILE,
    WARNING_DISK_USAGE_PERCENT,
)
from utils.history_manager import JsonlStore


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    event_type = str(
        event.get("event_type") or event.get("event") or "UNKNOWN_EVENT"
    )
    return {
        "timestamp": str(event.get("timestamp") or _now()),
        "event_type": event_type,
        "event": event_type,
        "severity": str(event.get("severity") or "INFO").upper(),
        "source": str(event.get("source") or "monitoring"),
        "message": str(
            event.get("message") or event_type.replace("_", " ").title()
        ),
        "details": (
            event.get("details")
            if isinstance(event.get("details"), dict)
            else {}
        ),
    }


class EventTimeline:
    """Append, filter, and retain structured monitoring events."""

    def __init__(
        self,
        event_file: str | Path = EVENT_TIMELINE_FILE,
        *,
        max_records: int | None = EVENT_RETENTION_RECORDS,
        durable: bool = False,
    ) -> None:
        self.event_file = Path(event_file)
        self.store = JsonlStore(
            self.event_file,
            max_records=max_records,
            durable=durable,
        )

    def record_event(self, event: dict[str, Any]) -> dict[str, Any]:
        normalized = normalize_event(event)
        self.store.append(normalized)
        return normalized

    def record_events(
        self, events: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        return [self.record_event(event) for event in events]

    def load_events(
        self,
        limit: int | None = None,
        *,
        event_type: str | None = None,
        severity: str | None = None,
        newest_first: bool = False,
    ) -> list[dict[str, Any]]:
        records = self.store.load(newest_first=False)
        if event_type is not None:
            records = [
                item for item in records if item.get("event_type") == event_type
            ]
        if severity is not None:
            severity_upper = severity.upper()
            records = [
                item
                for item in records
                if item.get("severity") == severity_upper
            ]
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be non-negative or None")
            records = records[-limit:] if limit else []
        if newest_first:
            records.reverse()
        return records

    def count(self) -> int:
        return self.store.count()

    def clear(self) -> None:
        self.store.clear()


def _usage_status(value: float) -> str:
    if value >= CRITICAL_DISK_USAGE_PERCENT:
        return "CRITICAL"
    if value >= WARNING_DISK_USAGE_PERCENT:
        return "WARNING"
    return "NORMAL"


def _disk_map(snapshot: dict[str, Any]) -> dict[str, float]:
    return {
        str(item.get("path", "<unknown>")): float(
            item.get("usage_percent", 0.0)
        )
        for item in snapshot.get("disks", [])
        if isinstance(item, dict)
    }


def _top_process_identity(
    snapshot: dict[str, Any],
) -> tuple[int, float | None, str] | None:
    consumers = snapshot.get("processes", {}).get("top_consumers", [])
    if not consumers:
        return None
    process = consumers[0]
    return (
        int(process.get("pid", -1)),
        (
            float(process["create_time"])
            if process.get("create_time") is not None
            else None
        ),
        str(process.get("name") or "<unknown>"),
    )


def build_timeline_events(
    previous: dict[str, Any] | None,
    current: dict[str, Any],
    **spike_options: Any,
) -> list[dict[str, Any]]:
    """Build meaningful transition, warning, and spike events for one cycle."""

    timestamp = current.get("timestamp")
    events = detect_snapshot_spikes(previous, current, **spike_options)

    for error in current.get("errors", []):
        if not isinstance(error, dict):
            continue
        events.append(
            {
                "timestamp": timestamp,
                "event_type": "COLLECTION_WARNING",
                "severity": "WARNING",
                "source": "metrics_snapshot",
                "message": (
                    "Metric collection warning for "
                    f"{error.get('path', '<unknown>')}."
                ),
                "details": dict(error),
            }
        )

    if previous is not None:
        previous_disks = _disk_map(previous)
        for path, current_usage in _disk_map(current).items():
            if path not in previous_disks:
                continue
            previous_status = _usage_status(previous_disks[path])
            current_status = _usage_status(current_usage)
            if previous_status != current_status:
                events.append(
                    {
                        "timestamp": timestamp,
                        "event_type": "DISK_STATUS_CHANGED",
                        "severity": (
                            current_status
                            if current_status != "NORMAL"
                            else "INFO"
                        ),
                        "source": "timeline_builder",
                        "message": (
                            f"Disk {path} status changed from {previous_status} "
                            f"to {current_status}."
                        ),
                        "details": {
                            "path": path,
                            "previous_status": previous_status,
                            "current_status": current_status,
                            "usage_percent": current_usage,
                        },
                    }
                )

        before_top = _top_process_identity(previous)
        after_top = _top_process_identity(current)
        if after_top is not None and before_top != after_top:
            events.append(
                {
                    "timestamp": timestamp,
                    "event_type": "TOP_DISK_CONSUMER_CHANGED",
                    "severity": "INFO",
                    "source": "timeline_builder",
                    "message": (
                        f"Top disk consumer changed to {after_top[2]} "
                        f"(PID {after_top[0]})."
                    ),
                    "details": {
                        "previous": before_top,
                        "current": after_top,
                    },
                }
            )

    return [normalize_event(event) for event in events]


def build_timeline(
    history: list[dict[str, Any]],
    events: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return a chronological structured timeline from snapshots and events."""

    timeline = [normalize_event(event) for event in (events or [])]
    for snapshot in history:
        maximum_usage = max(
            (
                float(item.get("usage_percent", 0.0))
                for item in snapshot.get("disks", [])
                if isinstance(item, dict)
            ),
            default=float(snapshot.get("disk_usage_percent", 0.0)),
        )
        timeline.append(
            normalize_event(
                {
                    "timestamp": snapshot.get("timestamp"),
                    "event_type": "METRICS_SNAPSHOT",
                    "severity": "INFO",
                    "source": "history",
                    "message": (
                        "Metrics snapshot recorded; maximum disk usage "
                        f"{maximum_usage:.1f}%."
                    ),
                    "details": {
                        "maximum_disk_usage_percent": maximum_usage
                    },
                }
            )
        )
    timeline.sort(key=lambda item: item.get("timestamp", ""))
    return timeline


def print_timeline(history: list[dict[str, Any]]) -> None:
    print("System Activity Timeline")
    print("=" * 80)
    for event in build_timeline(history):
        print(
            f"{event['timestamp']} | {event['severity']} | "
            f"{event['message']}"
        )
