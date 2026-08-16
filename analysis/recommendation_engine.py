"""M6 evidence-backed optimization recommendation engine."""

from __future__ import annotations

from typing import Any

from analysis.impact_estimator import estimate_recommendation_impact
from config.settings import (
    CRITICAL_DISK_USAGE_PERCENT,
    RECOMMENDATION_MAX_ITEMS,
    RECOMMENDATION_MIN_ROOT_CAUSE_CONFIDENCE,
    WARNING_DISK_USAGE_PERCENT,
)

_CAUSE_ACTIONS = {
    "Windows Search Indexing": (
        "BACKGROUND_TASK",
        "Reschedule or temporarily pause indexing during foreground disk-heavy work.",
    ),
    "Windows Defender Scan": (
        "BACKGROUND_TASK",
        "Move intensive scans to idle periods; review exclusions carefully before changing them.",
    ),
    "Antivirus Scan": (
        "BACKGROUND_TASK",
        "Move intensive scans to idle periods and review scan scope before changing it.",
    ),
    "Browser Activity": (
        "APPLICATION",
        "Reduce disk-heavy downloads, cache churn, tabs, or extensions and then re-measure.",
    ),
    "Development Environment Activity": (
        "DEVELOPMENT",
        "Reduce unnecessary build/index/watch activity and close unused projects before re-measuring.",
    ),
    "Python Runtime Activity": (
        "APPLICATION",
        "Inspect the active script's file-access pattern and batch small writes where appropriate.",
    ),
    "JavaScript Runtime or Build Activity": (
        "DEVELOPMENT",
        "Inspect build/watch tasks and dependency-cache writes; disable redundant watchers.",
    ),
    "Database Activity": (
        "DATABASE",
        "Inspect query load, checkpoints, compaction, and file growth before tuning the database.",
    ),
    "File Synchronization": (
        "BACKGROUND_TASK",
        "Pause or rate-limit large synchronization work during foreground activity after confirming it is safe.",
    ),
    "Backup Activity": (
        "BACKGROUND_TASK",
        "Move backup work to idle periods or lower its I/O concurrency.",
    ),
    "Windows Background Service": (
        "SYSTEM_SERVICE",
        "Identify the specific hosted service and its open files before changing service behavior.",
    ),
    "Unknown Process Activity": (
        "INVESTIGATION",
        "Inspect the process owner, command line, open files, and recent I/O before taking action.",
    ),
}


def _priority_label(score: float) -> str:
    if score >= 85:
        return "CRITICAL"
    if score >= 65:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"


def _maximum_disk_usage(snapshot: dict[str, Any]) -> float:
    return max(
        (
            float(item.get("usage_percent", 0.0))
            for item in snapshot.get("disks", [])
            if isinstance(item, dict)
        ),
        default=0.0,
    )


def _recommendation(
    *,
    recommendation_id: str,
    title: str,
    category: str,
    priority_score: float,
    action: str,
    reason: str,
    safety_level: str = "MANUAL_REVIEW",
    target_process: str | None = None,
    target_pid: int | None = None,
    source_signals: list[str] | None = None,
) -> dict[str, Any]:
    score = min(100.0, max(0.0, float(priority_score)))
    return {
        "id": recommendation_id,
        "title": title,
        "category": category,
        "priority_score": round(score, 2),
        "priority": _priority_label(score),
        "action": action,
        "reason": reason,
        "safety_level": safety_level,
        "requires_confirmation": True,
        "automation_eligible": False,
        "target_process": target_process,
        "target_pid": target_pid,
        "source_signals": list(source_signals or []),
    }


def generate_recommendations(
    snapshot: dict[str, Any],
    *,
    max_items: int = RECOMMENDATION_MAX_ITEMS,
) -> list[dict[str, Any]]:
    """Return ranked M6 recommendations from M1-M5 evidence."""

    if max_items < 0:
        raise ValueError("max_items must be non-negative")
    if max_items == 0:
        return []

    root = snapshot.get("root_cause", {})
    behavior = snapshot.get("process_behavior", {})
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(item: dict[str, Any]) -> None:
        if item["id"] not in seen:
            seen.add(item["id"])
            candidates.append(item)

    usage = _maximum_disk_usage(snapshot)
    if usage >= WARNING_DISK_USAGE_PERCENT or root.get("cause") == "Disk Capacity Pressure":
        score = 96.0 if usage >= CRITICAL_DISK_USAGE_PERCENT else 76.0
        add(
            _recommendation(
                recommendation_id="capacity:recover-space",
                title="Recover disk capacity safely",
                category="CAPACITY",
                priority_score=score,
                action=(
                    "Review the largest expendable files, caches, or applications; "
                    "move or remove only data you have confirmed is unnecessary."
                ),
                reason=f"Maximum observed disk utilization is {usage:.1f}%.",
                safety_level="MANUAL_REVIEW",
                source_signals=[
                    "CRITICAL_CAPACITY_PRESSURE"
                    if usage >= CRITICAL_DISK_USAGE_PERCENT
                    else "CAPACITY_PRESSURE"
                ],
            )
        )

    for runaway in behavior.get("runaways", []):
        name = str(runaway.get("name") or "<unknown>")
        pid = runaway.get("pid")
        add(
            _recommendation(
                recommendation_id=f"runaway:{name.casefold()}:{pid}",
                title=f"Investigate sustained disk I/O from {name}",
                category="PROCESS_BEHAVIOR",
                priority_score=98.0 if runaway.get("severity") == "CRITICAL" else 90.0,
                action=(
                    "Inspect the process command, owner, and open files. Pause, stop, "
                    "or throttle it only after confirming the process is non-critical."
                ),
                reason=(
                    "The same process instance remained above the configured I/O "
                    f"rate/share thresholds for {runaway.get('samples', 'multiple')} samples."
                ),
                safety_level="MANUAL_REVIEW",
                target_process=name,
                target_pid=pid,
                source_signals=["RUNAWAY_PROCESS"],
            )
        )

    for anomaly in behavior.get("anomalies", []):
        name = str(anomaly.get("name") or "<unknown>")
        pid = anomaly.get("pid")
        signals = list(anomaly.get("signals", []))
        add(
            _recommendation(
                recommendation_id=f"anomaly:{name.casefold()}:{pid}",
                title=f"Inspect unexpected I/O change from {name}",
                category="PROCESS_BEHAVIOR",
                priority_score=82.0 if anomaly.get("severity") == "CRITICAL" else 72.0,
                action=(
                    "Compare the process's current task with its recent baseline, "
                    "then inspect open files or workload changes before tuning it."
                ),
                reason=(
                    "Current process behavior departed materially from its own recent baseline."
                ),
                safety_level="OBSERVE_FIRST",
                target_process=name,
                target_pid=pid,
                source_signals=signals,
            )
        )

    root_confidence = float(root.get("confidence", 0.0))
    root_process = root.get("process")
    root_pid = root.get("pid")
    cause = root.get("cause")
    if (
        root.get("status") == "BOTTLENECK_DETECTED"
        and root_process
        and root_confidence >= RECOMMENDATION_MIN_ROOT_CAUSE_CONFIDENCE
    ):
        category, action = _CAUSE_ACTIONS.get(
            cause,
            (
                "INVESTIGATION",
                "Inspect the suspected process and recent disk activity before changing system behavior.",
            ),
        )
        severity_bonus = 12.0 if root.get("severity") == "CRITICAL" else 5.0
        score = min(90.0, 45.0 + root_confidence * 0.35 + severity_bonus)
        add(
            _recommendation(
                recommendation_id=(
                    f"cause:{str(cause).casefold()}:{str(root_process).casefold()}"
                ),
                title=f"Address likely cause: {cause}",
                category=category,
                priority_score=score,
                action=action,
                reason=(
                    f"M4 attributed the current disk pressure to {cause} with "
                    f"{root_confidence:.1f}% confidence."
                ),
                safety_level="MANUAL_REVIEW",
                target_process=str(root_process),
                target_pid=root_pid,
                source_signals=list(root.get("signals", [])),
            )
        )

    if (
        root.get("status") == "BOTTLENECK_DETECTED"
        and not root_process
        and root.get("cause") == "System Disk I/O Spike"
    ):
        add(
            _recommendation(
                recommendation_id="system:inspect-io-spike",
                title="Inspect the source of the system I/O spike",
                category="INVESTIGATION",
                priority_score=70.0,
                action=(
                    "Review recent top consumers and M3 timeline events; collect more "
                    "samples before changing services or storage settings."
                ),
                reason=(
                    "M4 found system-level spike evidence without a confident process attribution."
                ),
                safety_level="OBSERVE_FIRST",
                source_signals=list(root.get("signals", [])),
            )
        )

    for item in candidates:
        item["impact"] = estimate_recommendation_impact(snapshot, item)

    candidates.sort(
        key=lambda item: (
            float(item["priority_score"]),
            float(item["impact"]["impact_score"]),
            item["id"],
        ),
        reverse=True,
    )
    return candidates[:max_items]
