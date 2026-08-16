"""M8 stateful alert detection, deduplication, cooldown, and recovery."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from alerts.alert_store import AlertStore
from config.settings import (
    ALERT_COOLDOWN_SECONDS,
    ALERT_MIN_RECOMMENDATION_PRIORITY_SCORE,
    ALERT_RECOVERY_ENABLED,
    CRITICAL_DISK_USAGE_PERCENT,
    WARNING_DISK_USAGE_PERCENT,
)

_SEVERITY_RANK = {"INFO": 0, "WARNING": 1, "CRITICAL": 2}


def _severity(value: Any) -> str:
    text = str(value or "WARNING").upper()
    return text if text in _SEVERITY_RANK else "WARNING"


def _now_iso(now: datetime | None = None) -> str:
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _candidate(
    *, key: str, group: str, source: str, severity: str, title: str, message: str,
    target_process: str | None = None, target_pid: int | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "alert_key": key,
        "group": group,
        "source": source,
        "severity": _severity(severity),
        "title": title,
        "message": message,
        "target_process": target_process,
        "target_pid": target_pid,
        "details": dict(details or {}),
    }


def collect_alert_candidates(
    snapshot: dict[str, Any],
    *,
    minimum_recommendation_priority_score: float = ALERT_MIN_RECOMMENDATION_PRIORITY_SCORE,
) -> tuple[list[dict[str, Any]], set[str]]:
    candidates: list[dict[str, Any]] = []
    evaluated: set[str] = set()

    disks = snapshot.get("disks")
    if isinstance(disks, list):
        evaluated.add("capacity")
        for disk in disks:
            if not isinstance(disk, dict):
                continue
            usage = float(disk.get("usage_percent", 0.0))
            if usage < WARNING_DISK_USAGE_PERCENT:
                continue
            path = str(disk.get("path", "<unknown>"))
            severity = "CRITICAL" if usage >= CRITICAL_DISK_USAGE_PERCENT else "WARNING"
            candidates.append(_candidate(
                key=f"capacity:{path}", group="capacity", source="M1", severity=severity,
                title=f"Disk capacity pressure on {path}",
                message=f"{path} is {usage:.1f}% utilized.",
                details={"path": path, "usage_percent": usage},
            ))

    history = snapshot.get("history")
    if isinstance(history, dict):
        evaluated.add("spike")
        recent_events = history.get("recent_events", [])
        if isinstance(recent_events, list):
            for event in recent_events:
                if not isinstance(event, dict):
                    continue
                event_type = str(event.get("event_type", ""))
                if "SPIKE" not in event_type:
                    continue
                candidates.append(_candidate(
                    key=f"spike:{event_type}", group="spike", source="M3",
                    severity=event.get("severity", "WARNING"),
                    title="Disk I/O spike detected",
                    message=str(event.get("message") or event_type),
                    details={"event_type": event_type},
                ))

    root = snapshot.get("root_cause")
    if isinstance(root, dict):
        evaluated.add("root_cause")
        if root.get("status") == "BOTTLENECK_DETECTED":
            cause = str(root.get("cause") or "Unknown")
            process = root.get("process")
            pid = root.get("pid")
            identity = f"{str(process).casefold()}:{pid}" if process else "system"
            candidates.append(_candidate(
                key=f"root_cause:{cause.casefold()}:{identity}",
                group="root_cause", source="M4",
                severity=root.get("severity", "WARNING"),
                title=f"Likely disk bottleneck: {cause}",
                message=f"{cause} detected with {float(root.get('confidence', 0.0)):.1f}% confidence.",
                target_process=str(process) if process else None,
                target_pid=int(pid) if pid is not None else None,
                details={
                    "cause": cause,
                    "confidence": float(root.get("confidence", 0.0)),
                    "signals": list(root.get("signals", [])),
                },
            ))

    behavior = snapshot.get("process_behavior")
    if isinstance(behavior, dict):
        evaluated.update({"anomaly", "runaway"})
        for anomaly in behavior.get("anomalies", []):
            if not isinstance(anomaly, dict):
                continue
            name = str(anomaly.get("name") or "<unknown>")
            pid = int(anomaly.get("pid", 0) or 0)
            candidates.append(_candidate(
                key=f"anomaly:{name.casefold()}:{pid}", group="anomaly", source="M5",
                severity=anomaly.get("severity", "WARNING"),
                title=f"Process I/O anomaly: {name}",
                message=f"{name} departed from its recent disk-I/O baseline.",
                target_process=name, target_pid=pid,
                details={"signals": list(anomaly.get("signals", []))},
            ))
        for runaway in behavior.get("runaways", []):
            if not isinstance(runaway, dict):
                continue
            name = str(runaway.get("name") or "<unknown>")
            pid = int(runaway.get("pid", 0) or 0)
            candidates.append(_candidate(
                key=f"runaway:{name.casefold()}:{pid}", group="runaway", source="M5",
                severity=runaway.get("severity", "WARNING"),
                title=f"Runaway disk I/O: {name}",
                message=(
                    f"{name} sustained {float(runaway.get('latest_share_percent', 0.0)):.1f}% "
                    "of observed process disk I/O."
                ),
                target_process=name, target_pid=pid,
                details={
                    "samples": runaway.get("samples"),
                    "latest_rate_bytes_per_second": runaway.get("latest_rate_bytes_per_second", 0.0),
                    "latest_share_percent": runaway.get("latest_share_percent", 0.0),
                },
            ))

    recommendations = snapshot.get("recommendations")
    if isinstance(recommendations, dict):
        evaluated.add("recommendation")
        for item in recommendations.get("recommendations", []):
            if not isinstance(item, dict):
                continue
            score = float(item.get("priority_score", 0.0))
            if score < minimum_recommendation_priority_score:
                continue
            priority = str(item.get("priority", "HIGH")).upper()
            severity = "CRITICAL" if priority == "CRITICAL" else "WARNING"
            recommendation_id = str(item.get("id") or "unknown")
            candidates.append(_candidate(
                key=f"recommendation:{recommendation_id}",
                group="recommendation", source="M6", severity=severity,
                title=f"High-priority optimization: {item.get('title', recommendation_id)}",
                message=str(item.get("reason") or item.get("action") or ""),
                target_process=item.get("target_process"),
                target_pid=item.get("target_pid"),
                details={
                    "recommendation_id": recommendation_id,
                    "priority_score": score,
                    "impact": item.get("impact", {}),
                },
            ))

    deduped: dict[str, dict[str, Any]] = {}
    for item in candidates:
        key = item["alert_key"]
        existing = deduped.get(key)
        if existing is None or _SEVERITY_RANK[item["severity"]] > _SEVERITY_RANK[existing["severity"]]:
            deduped[key] = item
    return list(deduped.values()), evaluated


def evaluate_alerts(
    snapshot: dict[str, Any],
    *,
    store: AlertStore,
    cooldown_seconds: float = ALERT_COOLDOWN_SECONDS,
    recovery_enabled: bool = ALERT_RECOVERY_ENABLED,
    now: datetime | None = None,
) -> dict[str, Any]:
    if cooldown_seconds < 0:
        raise ValueError("cooldown_seconds must be non-negative")

    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    emitted_at = _now_iso(current_time)
    candidates, evaluated_groups = collect_alert_candidates(snapshot)
    current = {item["alert_key"]: item for item in candidates}
    previous = store.latest_by_key()
    emitted: list[dict[str, Any]] = []
    suppressed = 0

    for key, candidate in current.items():
        old = previous.get(key)
        event_type = "TRIGGERED"
        should_emit = old is None or not bool(old.get("active", False))

        if old and bool(old.get("active", False)):
            old_rank = _SEVERITY_RANK.get(_severity(old.get("severity")), 1)
            new_rank = _SEVERITY_RANK[candidate["severity"]]
            if new_rank > old_rank:
                should_emit = True
                event_type = "ESCALATED"
            else:
                previous_time = _parse_time(old.get("emitted_at"))
                elapsed = (
                    (current_time.astimezone(timezone.utc) - previous_time).total_seconds()
                    if previous_time else cooldown_seconds
                )
                if elapsed >= cooldown_seconds:
                    should_emit = True
                    event_type = "REMINDER"
                else:
                    suppressed += 1

        if should_emit:
            event = {
                **candidate,
                "event_type": event_type,
                "active": True,
                "emitted_at": emitted_at,
                "snapshot_timestamp": snapshot.get("timestamp"),
            }
            store.append(event)
            emitted.append(event)

    if recovery_enabled:
        for key, old in previous.items():
            if not bool(old.get("active", False)):
                continue
            group = str(old.get("group") or "")
            if group not in evaluated_groups or key in current:
                continue
            event = {
                "alert_key": key, "group": group, "source": old.get("source", "M8"),
                "severity": "INFO",
                "title": f"Recovered: {old.get('title', key)}",
                "message": "The previously active condition is no longer present.",
                "target_process": old.get("target_process"),
                "target_pid": old.get("target_pid"),
                "details": {"previous_severity": old.get("severity")},
                "event_type": "RECOVERED", "active": False,
                "emitted_at": emitted_at,
                "snapshot_timestamp": snapshot.get("timestamp"),
            }
            store.append(event)
            emitted.append(event)

    report = {
        "analysis_version": 1,
        "timestamp": snapshot.get("timestamp"),
        "status": "ALERTS_EMITTED" if emitted else "NO_NEW_ALERTS",
        "emitted": emitted,
        "emitted_count": len(emitted),
        "suppressed_count": suppressed,
        "active_count": len(store.active_alerts()),
        "alert_file": str(store.alert_file),
    }
    snapshot["alerts"] = report
    return report


def record_optimization_event(
    report: dict[str, Any], *, store: AlertStore, now: datetime | None = None
) -> dict[str, Any] | None:
    execution = str(report.get("execution_status") or report.get("status") or "")
    status = str(report.get("status") or "")
    if execution in {"", "DRY_RUN", "NO_DATA"} and status not in {
        "ROLLED_BACK", "PARTIAL_ROLLBACK", "ROLLBACK_FAILED"
    }:
        return None

    if execution == "APPLIED":
        severity, title, kind = "INFO", "M7 optimization applied", "optimization_applied"
        message = f"Applied {int(report.get('applied_count', 0))} reversible optimization action(s)."
    elif execution == "ROLLED_BACK_AFTER_FAILURE":
        severity, title, kind = "CRITICAL", "M7 optimization failed and rolled back", "optimization_failure"
        message = "An optimization action failed; previously applied actions were rolled back."
    elif status in {"ROLLED_BACK", "PARTIAL_ROLLBACK", "ROLLBACK_FAILED"}:
        severity = "INFO" if status == "ROLLED_BACK" else "WARNING"
        title = "M7 rollback completed" if status == "ROLLED_BACK" else "M7 rollback requires attention"
        kind = "optimization_rollback"
        message = f"Rollback status: {status}; restored {int(report.get('rolled_back_count', 0))} action(s)."
    else:
        return None

    event = {
        "alert_key": f"m7:{kind}:{report.get('session_id') or 'latest'}",
        "group": "optimization", "source": "M7", "severity": severity,
        "title": title, "message": message,
        "target_process": None, "target_pid": None,
        "details": {
            "execution_status": execution,
            "status": status,
            "session_id": report.get("session_id"),
        },
        "event_type": "EVENT", "active": False,
        "emitted_at": _now_iso(now), "snapshot_timestamp": None,
    }
    store.append(event)
    return event
