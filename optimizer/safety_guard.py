"""M7 safety policy for automatic disk-I/O mitigation."""

from __future__ import annotations

import os
from typing import Any

import psutil

from config.settings import (
    AUTO_OPTIMIZATION_DENYLIST,
    AUTO_OPTIMIZATION_MIN_IMPACT_SCORE,
)


def _normalized_name(value: object) -> str:
    return os.path.basename(str(value or "")).strip().casefold()


def _impact_score(recommendation: dict[str, Any]) -> float:
    impact = recommendation.get("impact", {})
    if not isinstance(impact, dict):
        return 0.0
    return max(0.0, float(impact.get("impact_score", 0.0)))


def evaluate_automation_safety(
    recommendation: dict[str, Any],
    *,
    current_pid: int | None = None,
    parent_pid: int | None = None,
    minimum_impact_score: float = AUTO_OPTIMIZATION_MIN_IMPACT_SCORE,
) -> dict[str, Any]:
    """Decide whether one M6 recommendation may become an M7 action."""

    current_pid = os.getpid() if current_pid is None else int(current_pid)
    if parent_pid is None:
        try:
            parent_pid = os.getppid()
        except OSError:
            parent_pid = -1

    reasons: list[str] = []
    recommendation_id = str(recommendation.get("id", ""))
    signals = {
        str(item).upper()
        for item in recommendation.get("source_signals", [])
    }
    pid = int(recommendation.get("target_pid", 0) or 0)
    name = _normalized_name(recommendation.get("target_process"))
    create_time_raw = recommendation.get("target_create_time")
    create_time = (
        float(create_time_raw)
        if create_time_raw not in (None, "")
        else None
    )

    if not recommendation_id.startswith("runaway:"):
        reasons.append("Only sustained runaway-process recommendations are auto-actionable.")
    if "RUNAWAY_PROCESS" not in signals:
        reasons.append("Sustained runaway-process evidence is required.")
    if recommendation.get("priority") not in {"HIGH", "CRITICAL"}:
        reasons.append("Recommendation priority must be HIGH or CRITICAL.")
    if _impact_score(recommendation) < minimum_impact_score:
        reasons.append(
            f"Impact score is below the {minimum_impact_score:.1f} safety threshold."
        )
    if pid <= 1:
        reasons.append("Target PID is missing or system-reserved.")
    if pid in {current_pid, int(parent_pid or -1)}:
        reasons.append("The analyzer process or its parent cannot be optimized.")
    if not name:
        reasons.append("Target process name is required.")
    denylist = {_normalized_name(item) for item in AUTO_OPTIMIZATION_DENYLIST}
    if name in denylist:
        reasons.append(f"{name} is protected by the system-process denylist.")
    if create_time is None or create_time <= 0:
        reasons.append("Process creation time is required to prevent PID-reuse errors.")

    if reasons:
        return {
            "allowed": False,
            "reasons": reasons,
            "action_type": None,
            "target_pid": pid or None,
            "target_process": recommendation.get("target_process"),
            "target_create_time": create_time,
        }

    return {
        "allowed": True,
        "reasons": [
            "Sustained same-instance runaway evidence passed M7 safety policy."
        ],
        "action_type": "LOWER_PROCESS_PRIORITY",
        "target_pid": pid,
        "target_process": recommendation.get("target_process"),
        "target_create_time": create_time,
    }


def verify_live_process_identity(
    pid: int,
    expected_name: str,
    expected_create_time: float,
    *,
    process_factory: Any = psutil.Process,
) -> dict[str, Any]:
    """Verify live PID/name/create-time identity immediately before mutation."""

    process = process_factory(int(pid))
    actual_name = process.name()
    actual_create_time = float(process.create_time())
    expected_normalized = _normalized_name(expected_name)
    actual_normalized = _normalized_name(actual_name)

    same_name = actual_normalized == expected_normalized
    same_instance = abs(actual_create_time - float(expected_create_time)) < 0.001
    return {
        "verified": bool(same_name and same_instance),
        "process": process,
        "actual_name": actual_name,
        "actual_create_time": actual_create_time,
        "same_name": same_name,
        "same_instance": same_instance,
    }
