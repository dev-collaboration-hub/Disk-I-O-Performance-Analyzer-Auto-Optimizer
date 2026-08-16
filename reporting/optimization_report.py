"""M7 optimization planning, execution, rollback, and CLI reporting."""

from __future__ import annotations

import argparse
import json
from typing import Any

from config.settings import (
    AUTO_OPTIMIZATION_MAX_ACTIONS,
    HISTORY_FILE,
    OPTIMIZATION_JOURNAL_FILE,
)
from optimizer.auto_optimizer import run_optimization_cycle
from optimizer.process_priority import ProcessPriorityController
from optimizer.rollback_manager import OptimizationJournal, rollback_tokens
from utils.history_manager import HistoryManager


def render_optimization_report(report: dict[str, Any]) -> str:
    lines = ["AUTO OPTIMIZATION ENGINE", "=" * 72]
    lines.append(f"Plan status      : {report.get('status', 'UNKNOWN')}")
    lines.append(f"Execution status : {report.get('execution_status', 'UNKNOWN')}")
    lines.append(f"Safe actions     : {report.get('action_count', 0)}")
    lines.append(f"Blocked          : {report.get('blocked_count', 0)}")

    for item in report.get("actions", []):
        lines.append(
            "ACTION           : "
            f"{item.get('action_type')} -> {item.get('target_process')} "
            f"(PID {item.get('target_pid')})"
        )
    for item in report.get("blocked", [])[:5]:
        lines.append(
            "BLOCKED          : "
            f"{item.get('recommendation_id')} | "
            + "; ".join(item.get("reasons", []))
        )

    if report.get("execution_status") == "DRY_RUN":
        lines.append(
            "No system change applied. Re-run with --apply to execute safe actions."
        )
    elif report.get("execution_status") == "APPLIED":
        lines.append(
            f"Applied {report.get('applied_count', 0)} reversible action(s); rollback is available."
        )
    elif report.get("execution_status") == "ROLLED_BACK_AFTER_FAILURE":
        lines.append("Execution failed and previously applied actions were rolled back.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan/apply M7 safe auto-optimization for the latest snapshot."
    )
    parser.add_argument("--history-file", default=HISTORY_FILE)
    parser.add_argument("--journal-file", default=OPTIMIZATION_JOURNAL_FILE)
    parser.add_argument(
        "--max-actions",
        type=int,
        default=AUTO_OPTIMIZATION_MAX_ACTIONS,
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply only M7 safety-approved reversible actions.",
    )
    parser.add_argument(
        "--rollback-last",
        action="store_true",
        help="Rollback the most recent applied M7 session if still active.",
    )
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    journal = OptimizationJournal(args.journal_file)

    if args.rollback_last:
        session_id, tokens = journal.latest_active_session()
        if not session_id or not tokens:
            report = {
                "status": "NO_ACTIVE_SESSION",
                "rolled_back_count": 0,
                "errors": [],
            }
        else:
            report = rollback_tokens(
                tokens,
                controller=ProcessPriorityController(),
                journal=journal,
                session_id=session_id,
            )
    else:
        snapshot = HistoryManager(args.history_file).latest_snapshot()
        if snapshot is None:
            report = {
                "status": "NO_DATA",
                "execution_status": "NO_DATA",
                "action_count": 0,
                "blocked_count": 0,
            }
        else:
            report = run_optimization_cycle(
                snapshot,
                apply=args.apply,
                max_actions=args.max_actions,
                journal=journal,
            )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        if args.rollback_last:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(render_optimization_report(report))


if __name__ == "__main__":
    main()
