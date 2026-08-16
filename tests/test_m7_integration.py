"""M7 auto-optimization safety, execution, and rollback tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from optimizer.auto_optimizer import (
    build_optimization_plan,
    execute_optimization_plan,
    run_optimization_cycle,
)
from optimizer.rollback_manager import OptimizationJournal, rollback_tokens
from optimizer.safety_guard import evaluate_automation_safety


def runaway_recommendation(
    *,
    pid: int = 222,
    name: str = "worker.exe",
    impact: float = 90.0,
) -> dict:
    return {
        "id": f"runaway:{name.casefold()}:{pid}",
        "title": f"Investigate sustained disk I/O from {name}",
        "category": "PROCESS_BEHAVIOR",
        "priority_score": 90.0,
        "priority": "HIGH",
        "action": "Inspect before changing process behavior.",
        "reason": "Sustained runaway evidence.",
        "safety_level": "MANUAL_REVIEW",
        "requires_confirmation": True,
        "automation_eligible": False,
        "target_process": name,
        "target_pid": pid,
        "source_signals": ["RUNAWAY_PROCESS"],
        "impact": {
            "impact_score": impact,
            "impact_level": "HIGH",
        },
    }


def snapshot() -> dict:
    recommendation = runaway_recommendation()
    return {
        "timestamp": "2026-08-16T00:00:00+00:00",
        "recommendations": {
            "status": "RECOMMENDATIONS_AVAILABLE",
            "recommendations": [recommendation],
            "recommendation_count": 1,
        },
        "process_behavior": {
            "status": "RUNAWAY_DETECTED",
            "runaways": [
                {
                    "name": "worker.exe",
                    "pid": 222,
                    "create_time": 1234.5,
                    "severity": "WARNING",
                    "samples": 3,
                    "latest_rate_bytes_per_second": 4_000_000.0,
                    "latest_share_percent": 80.0,
                }
            ],
        },
    }


class FakeController:
    def __init__(self, *, fail_on_call: int | None = None) -> None:
        self.fail_on_call = fail_on_call
        self.calls = 0
        self.rolled_back: list[int] = []

    def lower_priority(
        self,
        *,
        pid: int,
        expected_name: str,
        expected_create_time: float,
        step: int,
    ) -> dict:
        self.calls += 1
        if self.fail_on_call == self.calls:
            raise RuntimeError("synthetic mutation failure")
        return {
            "action_type": "LOWER_PROCESS_PRIORITY",
            "pid": pid,
            "process": expected_name,
            "create_time": expected_create_time,
            "previous_priority": 0,
            "applied_priority": step,
            "changed": True,
        }

    def rollback(self, token: dict) -> dict:
        self.rolled_back.append(int(token["pid"]))
        return {
            "pid": int(token["pid"]),
            "process": token["process"],
            "rolled_back": True,
            "restored_priority": token["previous_priority"],
        }


class M7AutoOptimizationTests(unittest.TestCase):
    def test_non_runaway_recommendation_is_blocked(self) -> None:
        item = runaway_recommendation()
        item["id"] = "capacity:recover-space"
        item["source_signals"] = ["CAPACITY_PRESSURE"]
        item["target_create_time"] = 1234.5
        result = evaluate_automation_safety(
            item,
            current_pid=999,
            parent_pid=998,
        )
        self.assertFalse(result["allowed"])
        self.assertTrue(result["reasons"])

    def test_low_impact_runaway_is_blocked(self) -> None:
        item = runaway_recommendation(impact=20)
        item["target_create_time"] = 1234.5
        result = evaluate_automation_safety(
            item,
            current_pid=999,
            parent_pid=998,
        )
        self.assertFalse(result["allowed"])

    def test_runaway_plan_infers_same_instance_creation_time(self) -> None:
        plan = build_optimization_plan(snapshot())
        self.assertEqual(plan["status"], "PLAN_READY")
        self.assertEqual(plan["action_count"], 1)
        self.assertEqual(plan["actions"][0]["target_create_time"], 1234.5)
        self.assertEqual(
            plan["actions"][0]["action_type"],
            "LOWER_PROCESS_PRIORITY",
        )

    def test_dry_run_never_calls_controller(self) -> None:
        plan = build_optimization_plan(snapshot())
        controller = FakeController()
        report = execute_optimization_plan(
            plan,
            apply=False,
            controller=controller,
        )
        self.assertEqual(report["execution_status"], "DRY_RUN")
        self.assertEqual(controller.calls, 0)
        self.assertEqual(report["applied_count"], 0)

    def test_apply_produces_durable_rollback_token(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            journal = OptimizationJournal(
                Path(directory) / "optimization.jsonl"
            )
            controller = FakeController()
            report = run_optimization_cycle(
                snapshot(),
                apply=True,
                controller=controller,
                journal=journal,
            )
            self.assertEqual(report["execution_status"], "APPLIED")
            self.assertEqual(report["applied_count"], 1)
            self.assertTrue(report["rollback_available"])
            self.assertTrue(report["rollback_tokens"])
            self.assertTrue(journal.load())

    def test_failure_rolls_back_prior_actions(self) -> None:
        current = snapshot()
        second = runaway_recommendation(pid=333, name="worker2.exe")
        current["recommendations"]["recommendations"].append(second)
        current["process_behavior"]["runaways"].append(
            {
                "name": "worker2.exe",
                "pid": 333,
                "create_time": 9999.0,
                "severity": "WARNING",
                "samples": 3,
                "latest_rate_bytes_per_second": 4_000_000.0,
                "latest_share_percent": 80.0,
            }
        )
        plan = build_optimization_plan(current, max_actions=2)
        controller = FakeController(fail_on_call=2)
        with tempfile.TemporaryDirectory() as directory:
            report = execute_optimization_plan(
                plan,
                apply=True,
                controller=controller,
                journal=OptimizationJournal(
                    Path(directory) / "optimization.jsonl"
                ),
            )
        self.assertEqual(
            report["execution_status"],
            "ROLLED_BACK_AFTER_FAILURE",
        )
        self.assertEqual(controller.rolled_back, [222])

    def test_manual_rollback_uses_reverse_order(self) -> None:
        controller = FakeController()
        tokens = [
            {"pid": 1, "process": "a", "create_time": 1.0, "previous_priority": 0},
            {"pid": 2, "process": "b", "create_time": 2.0, "previous_priority": 0},
        ]
        result = rollback_tokens(tokens, controller=controller)
        self.assertEqual(result["status"], "ROLLED_BACK")
        self.assertEqual(controller.rolled_back, [2, 1])

    def test_denylisted_system_process_is_blocked(self) -> None:
        item = runaway_recommendation(pid=444, name="systemd")
        item["target_create_time"] = 12.0
        result = evaluate_automation_safety(
            item,
            current_pid=999,
            parent_pid=998,
        )
        self.assertFalse(result["allowed"])


if __name__ == "__main__":
    unittest.main()
