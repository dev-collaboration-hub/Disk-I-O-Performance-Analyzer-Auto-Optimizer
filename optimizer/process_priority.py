"""Reversible process-priority mitigation for M7."""

from __future__ import annotations

import os
from typing import Any

import psutil

from config.settings import AUTO_OPTIMIZATION_PRIORITY_STEP
from optimizer.safety_guard import verify_live_process_identity


class ProcessPriorityController:
    """Apply and reverse the single M7 mutation: lower process priority."""

    def __init__(self, process_factory: Any = psutil.Process) -> None:
        self.process_factory = process_factory

    @staticmethod
    def _lower_priority_value(current: Any, step: int) -> Any:
        if os.name == "nt":
            below_normal = getattr(psutil, "BELOW_NORMAL_PRIORITY_CLASS", None)
            idle = getattr(psutil, "IDLE_PRIORITY_CLASS", None)
            if below_normal is None:
                raise RuntimeError("Windows below-normal priority is unavailable.")
            if idle is not None and int(current) == int(idle):
                return current
            return below_normal

        numeric = int(current)
        return min(19, numeric + max(1, int(step)))

    def lower_priority(
        self,
        *,
        pid: int,
        expected_name: str,
        expected_create_time: float,
        step: int = AUTO_OPTIMIZATION_PRIORITY_STEP,
    ) -> dict[str, Any]:
        if os.name != "nt" and hasattr(os, "geteuid") and os.geteuid() != 0:
            raise PermissionError(
                "POSIX auto-apply requires privilege that can restore the original niceness."
            )

        identity = verify_live_process_identity(
            pid,
            expected_name,
            expected_create_time,
            process_factory=self.process_factory,
        )
        if not identity["verified"]:
            raise RuntimeError(
                "Process identity changed before optimization; refusing mutation."
            )

        process = identity["process"]
        previous = process.nice()
        desired = self._lower_priority_value(previous, step)
        changed = int(desired) != int(previous)
        if changed:
            process.nice(desired)

        return {
            "action_type": "LOWER_PROCESS_PRIORITY",
            "pid": int(pid),
            "process": identity["actual_name"],
            "create_time": identity["actual_create_time"],
            "previous_priority": int(previous),
            "applied_priority": int(desired),
            "changed": changed,
        }

    def rollback(self, token: dict[str, Any]) -> dict[str, Any]:
        identity = verify_live_process_identity(
            int(token["pid"]),
            str(token["process"]),
            float(token["create_time"]),
            process_factory=self.process_factory,
        )
        if not identity["verified"]:
            raise RuntimeError(
                "Process identity changed before rollback; refusing to touch reused PID."
            )
        process = identity["process"]
        process.nice(int(token["previous_priority"]))
        return {
            "action_type": token.get("action_type"),
            "pid": int(token["pid"]),
            "process": token.get("process"),
            "restored_priority": int(token["previous_priority"]),
            "rolled_back": True,
        }
