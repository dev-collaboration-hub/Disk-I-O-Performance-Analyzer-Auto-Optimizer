"""M7 safety-first automatic optimization engine."""

from __future__ import annotations

import uuid
from typing import Any

from config.settings import (
    AUTO_OPTIMIZATION_MAX_ACTIONS,
    AUTO_OPTIMIZATION_PRIORITY_STEP,
    OPTIMIZATION_JOURNAL_FILE,
)
from optimizer.process_priority import ProcessPriorityController
from optimizer.rollback_manager import OptimizationJournal, rollback_tokens
from optimizer.safety_guard import evaluate_automation_safety


def build_optimization_plan(
    snapshot: dict[str, Any],
    *,
    max_actions: int = AUTO_OPTIMIZATION_MAX_ACTIONS,
) -> dict[str, Any]:
    if max_actions < 0:
        raise ValueError("max_actions must be non-negative")

    recommendation_report = snapshot.get("recommendations", {})
    recommendations = (
        recommendation_report.get("recommendations", [])
        if isinstance(recommendation_report, dict)
        else []
    )
    actions: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    behavior = snapshot.get("process_behavior", {})
    runaways = behavior.get("runaways", []) if isinstance(behavior, dict) else []

    for recommendation in recommendations:
        if not isinstance(recommendation, dict):
            continue
        candidate = dict(recommendation)
        if candidate.get("target_create_time") in (None, ""):
            target_pid = int(candidate.get("target_pid", 0) or 0)
            target_name = str(candidate.get("target_process") or "").casefold()
            for runaway in runaways:
                if not isinstance(runaway, dict):
                    continue
                if (
                    int(runaway.get("pid", 0) or 0) == target_pid
                    and str(runaway.get("name") or "").casefold() == target_name
                ):
                    candidate["target_create_time"] = runaway.get("create_time")
                    break
        safety = evaluate_automation_safety(candidate)
        if safety["allowed"] and len(actions) < max_actions:
            actions.append(
                {
                    "action_type": safety["action_type"],
                    "recommendation_id": recommendation.get("id"),
                    "target_pid": safety["target_pid"],
                    "target_process": safety["target_process"],
                    "target_create_time": safety["target_create_time"],
                    "priority": recommendation.get("priority"),
                    "impact": recommendation.get("impact", {}),
                    "safety_reasons": safety["reasons"],
                }
            )
        else:
            blocked.append(
                {
                    "recommendation_id": recommendation.get("id"),
                    "reasons": safety["reasons"]
                    if not safety["allowed"]
                    else ["M7 maximum action count reached."],
                }
            )

    return {
        "analysis_version": 1,
        "timestamp": snapshot.get("timestamp"),
        "status": "PLAN_READY" if actions else "NO_SAFE_ACTIONS",
        "actions": actions,
        "action_count": len(actions),
        "blocked": blocked,
        "blocked_count": len(blocked),
        "destructive_actions_allowed": False,
    }


def execute_optimization_plan(
    plan: dict[str, Any],
    *,
    apply: bool = False,
    controller: Any | None = None,
    journal: OptimizationJournal | None = None,
) -> dict[str, Any]:
    actions = list(plan.get("actions", []))
    if not actions:
        return {
            **plan,
            "execution_status": "NO_SAFE_ACTIONS",
            "dry_run": not apply,
            "applied_count": 0,
            "rollback_tokens": [],
            "errors": [],
        }
    if not apply:
        return {
            **plan,
            "execution_status": "DRY_RUN",
            "dry_run": True,
            "applied_count": 0,
            "rollback_tokens": [],
            "errors": [],
        }

    controller = controller or ProcessPriorityController()
    journal = journal or OptimizationJournal(OPTIMIZATION_JOURNAL_FILE)
    session_id = uuid.uuid4().hex
    tokens: list[dict[str, Any]] = []
    applied: list[dict[str, Any]] = []

    journal.append(
        "SESSION_STARTED",
        session_id=session_id,
        payload={"action_count": len(actions)},
    )

    try:
        for action in actions:
            if action.get("action_type") != "LOWER_PROCESS_PRIORITY":
                raise RuntimeError(
                    f"Unsupported M7 action: {action.get('action_type')}"
                )
            token = controller.lower_priority(
                pid=int(action["target_pid"]),
                expected_name=str(action["target_process"]),
                expected_create_time=float(action["target_create_time"]),
                step=AUTO_OPTIMIZATION_PRIORITY_STEP,
            )
            tokens.append(token)
            applied.append(
                {
                    "recommendation_id": action.get("recommendation_id"),
                    "action_type": action.get("action_type"),
                    "target_pid": action.get("target_pid"),
                    "target_process": action.get("target_process"),
                    "changed": token.get("changed", False),
                }
            )
            journal.append(
                "ACTION_APPLIED",
                session_id=session_id,
                payload={
                    "action": action,
                    "rollback_token": token,
                },
            )
    except Exception as error:
        rollback = rollback_tokens(
            tokens,
            controller=controller,
            journal=journal,
            session_id=session_id,
        )
        return {
            **plan,
            "execution_status": "ROLLED_BACK_AFTER_FAILURE",
            "dry_run": False,
            "session_id": session_id,
            "applied_count": len(applied),
            "applied": applied,
            "rollback": rollback,
            "rollback_tokens": [],
            "errors": [f"{type(error).__name__}: {error}"],
        }

    return {
        **plan,
        "execution_status": "APPLIED",
        "dry_run": False,
        "session_id": session_id,
        "applied_count": len(applied),
        "applied": applied,
        "rollback_tokens": tokens,
        "errors": [],
        "rollback_available": bool(tokens),
    }


def run_optimization_cycle(
    snapshot: dict[str, Any],
    *,
    apply: bool = False,
    max_actions: int = AUTO_OPTIMIZATION_MAX_ACTIONS,
    controller: Any | None = None,
    journal: OptimizationJournal | None = None,
) -> dict[str, Any]:
    plan = build_optimization_plan(snapshot, max_actions=max_actions)
    report = execute_optimization_plan(
        plan,
        apply=apply,
        controller=controller,
        journal=journal,
    )
    snapshot["auto_optimization"] = report
    return report
