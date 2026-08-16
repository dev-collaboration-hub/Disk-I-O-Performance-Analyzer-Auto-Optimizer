"""M6 recommendation analysis, ranking, persistence, and CLI reporting."""

from __future__ import annotations

import argparse
import json
from typing import Any

from analysis.recommendation_engine import generate_recommendations
from config.settings import HISTORY_FILE, RECOMMENDATION_MAX_ITEMS
from utils.history_manager import HistoryManager


def analyze_recommendations(
    snapshot: dict[str, Any],
    *,
    max_items: int = RECOMMENDATION_MAX_ITEMS,
) -> dict[str, Any]:
    recommendations = generate_recommendations(snapshot, max_items=max_items)
    if recommendations:
        status = "RECOMMENDATIONS_AVAILABLE"
        message = "Evidence-backed manual optimization recommendations are available."
        highest_priority = recommendations[0]["priority"]
        highest_impact = max(
            recommendations,
            key=lambda item: float(
                item.get("impact", {}).get("impact_score", 0.0)
            ),
        )["impact"]["impact_level"]
    else:
        status = "NO_ACTION_NEEDED"
        message = "No optimization action is justified by the current evidence."
        highest_priority = "LOW"
        highest_impact = "LOW"

    return {
        "analysis_version": 1,
        "timestamp": snapshot.get("timestamp"),
        "status": status,
        "message": message,
        "recommendations": recommendations,
        "recommendation_count": len(recommendations),
        "highest_priority": highest_priority,
        "highest_impact": highest_impact,
        "automatic_changes_applied": False,
    }


def attach_recommendation_analysis(
    snapshot: dict[str, Any],
    *,
    max_items: int = RECOMMENDATION_MAX_ITEMS,
) -> dict[str, Any]:
    report = analyze_recommendations(snapshot, max_items=max_items)
    snapshot["recommendations"] = report
    return report


def render_recommendation_report(report: dict[str, Any]) -> str:
    lines = ["OPTIMIZATION RECOMMENDATIONS", "=" * 72]
    lines.append(f"Status          : {report.get('status', 'UNKNOWN')}")
    lines.append(f"Recommendations : {report.get('recommendation_count', 0)}")

    if not report.get("recommendations"):
        lines.append(report.get("message", "No recommendation available."))
        return "\n".join(lines)

    for index, item in enumerate(report["recommendations"], start=1):
        impact = item.get("impact", {})
        lines.extend(
            [
                "",
                f"{index}. [{item.get('priority', 'LOW')}] {item.get('title')}",
                (
                    f"   Impact : {impact.get('impact_level', 'LOW')} "
                    f"({float(impact.get('impact_score', 0.0)):.1f}/100)"
                ),
                f"   Safety : {item.get('safety_level', 'MANUAL_REVIEW')}",
                f"   Why    : {item.get('reason')}",
                f"   Action : {item.get('action')}",
            ]
        )

    lines.extend(
        [
            "",
            "M6 is advisory only; no system changes are applied automatically.",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Show M6 optimization recommendations for the latest stored snapshot."
    )
    parser.add_argument("--history-file", default=HISTORY_FILE)
    parser.add_argument("--limit", type=int, default=RECOMMENDATION_MAX_ITEMS)
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    history = HistoryManager(args.history_file)
    snapshot = history.latest_snapshot()
    if snapshot is None:
        report = {
            "status": "NO_DATA",
            "recommendation_count": 0,
            "recommendations": [],
            "message": "No stored monitoring snapshot is available.",
        }
    else:
        report = snapshot.get("recommendations")
        if not isinstance(report, dict):
            report = analyze_recommendations(snapshot, max_items=args.limit)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_recommendation_report(report))


if __name__ == "__main__":
    main()
