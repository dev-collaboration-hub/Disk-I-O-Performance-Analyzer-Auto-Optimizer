"""M9 analytics for M8 alert lifecycles and M7 optimization journal outcomes."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from statistics import mean, median
from typing import Any


def _timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


def analyze_alert_events(events: list[dict[str, Any]] | None) -> dict[str, Any]:
    records = [item for item in (events or []) if isinstance(item, dict)]
    by_type = Counter(str(item.get("event_type") or "UNKNOWN") for item in records)
    by_severity = Counter(str(item.get("severity") or "UNKNOWN") for item in records)
    by_group = Counter(str(item.get("group") or "unknown") for item in records)
    by_source = Counter(str(item.get("source") or "unknown") for item in records)

    active: dict[str, dict[str, Any]] = {}
    started: dict[str, datetime] = {}
    recovery_seconds: list[float] = []
    for item in records:
        key = str(item.get("alert_key") or "")
        if not key:
            continue
        event_type = str(item.get("event_type") or "")
        stamp = _timestamp(item.get("emitted_at"))
        if event_type == "TRIGGERED" and stamp is not None and key not in started:
            started[key] = stamp
        if bool(item.get("active", False)):
            active[key] = item
        else:
            active.pop(key, None)
        if event_type == "RECOVERED":
            begin = started.pop(key, None)
            if begin is not None and stamp is not None and stamp >= begin:
                recovery_seconds.append((stamp - begin).total_seconds())

    return {
        "event_count": len(records),
        "events_by_type": dict(sorted(by_type.items())),
        "events_by_severity": dict(sorted(by_severity.items())),
        "events_by_group": dict(sorted(by_group.items())),
        "events_by_source": dict(sorted(by_source.items())),
        "active_alert_count": len(active),
        "active_alerts": [
            {
                "alert_key": key,
                "severity": item.get("severity"),
                "group": item.get("group"),
                "title": item.get("title"),
                "emitted_at": item.get("emitted_at"),
            }
            for key, item in sorted(active.items())
        ],
        "recovered_condition_count": len(recovery_seconds),
        "average_recovery_seconds": round(mean(recovery_seconds), 2)
        if recovery_seconds
        else None,
        "median_recovery_seconds": round(median(recovery_seconds), 2)
        if recovery_seconds
        else None,
    }


def analyze_optimization_events(events: list[dict[str, Any]] | None) -> dict[str, Any]:
    records = [item for item in (events or []) if isinstance(item, dict)]
    by_type = Counter(str(item.get("event_type") or "UNKNOWN") for item in records)
    sessions: dict[str, set[str]] = {}
    for item in records:
        session = str(item.get("session_id") or "")
        if not session:
            continue
        sessions.setdefault(session, set()).add(str(item.get("event_type") or "UNKNOWN"))

    rolled_back = sum("SESSION_ROLLED_BACK" in event_types for event_types in sessions.values())
    committed = sum("SESSION_COMMITTED" in event_types for event_types in sessions.values())
    active = sum(
        bool({"ACTION_APPLIED"} & event_types)
        and not bool({"SESSION_ROLLED_BACK", "SESSION_COMMITTED"} & event_types)
        for event_types in sessions.values()
    )
    return {
        "event_count": len(records),
        "session_count": len(sessions),
        "events_by_type": dict(sorted(by_type.items())),
        "actions_applied": int(by_type.get("ACTION_APPLIED", 0)),
        "actions_rolled_back": int(by_type.get("ACTION_ROLLED_BACK", 0)),
        "rolled_back_sessions": rolled_back,
        "committed_sessions": committed,
        "rollback_available_sessions": active,
    }
