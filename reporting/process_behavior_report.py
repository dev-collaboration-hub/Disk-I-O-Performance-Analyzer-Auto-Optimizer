"""M5 process behavior analysis and report attachment."""

from __future__ import annotations

from typing import Any

from analysis.anomaly_detector import detect_process_anomalies
from analysis.process_profiler import (
    build_process_profiles,
    normalize_process_name,
)
from analysis.runaway_detector import detect_runaway_processes
from config.settings import PROCESS_PROFILE_HISTORY_SAMPLES
from utils.formatter import format_size


def _current_process_keys(snapshot: dict[str, Any]) -> set[str]:
    processes = snapshot.get("processes", {})
    if not isinstance(processes, dict):
        return set()
    return {
        normalize_process_name(item.get("name"))
        for item in processes.get("top_consumers", [])
        if isinstance(item, dict)
    }


def _analysis_history(
    snapshot: dict[str, Any],
    recent_history: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    records = [item for item in (recent_history or []) if isinstance(item, dict)]
    if not records or records[-1].get("timestamp") != snapshot.get("timestamp"):
        records.append(snapshot)
    return records[-PROCESS_PROFILE_HISTORY_SAMPLES:]


def analyze_process_behavior(
    snapshot: dict[str, Any],
    *,
    recent_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    history = _analysis_history(snapshot, recent_history)
    profiles = build_process_profiles(
        history,
        max_samples=PROCESS_PROFILE_HISTORY_SAMPLES,
    )
    current_keys = _current_process_keys(snapshot)
    current_profiles = [
        profile
        for profile in profiles
        if profile["process_key"] in current_keys
    ]
    anomalies = detect_process_anomalies(snapshot, history)
    runaways = detect_runaway_processes(snapshot, history)

    if runaways:
        status = "RUNAWAY_DETECTED"
        message = "One or more process instances show sustained runaway disk I/O."
    elif anomalies:
        status = "ANOMALY_DETECTED"
        message = "One or more processes departed materially from their baseline."
    elif current_profiles:
        status = "NORMAL"
        message = "No process behavior anomaly detected in the current sample."
    else:
        status = "NO_PROCESS_ACTIVITY"
        message = "No current process disk I/O activity is available for analysis."

    return {
        "analysis_version": 1,
        "timestamp": snapshot.get("timestamp"),
        "status": status,
        "message": message,
        "history_window_samples": len(history),
        "profiles": current_profiles,
        "profile_count": len(current_profiles),
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
        "runaways": runaways,
        "runaway_count": len(runaways),
    }


def attach_process_behavior_analysis(
    snapshot: dict[str, Any],
    *,
    recent_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    report = analyze_process_behavior(
        snapshot,
        recent_history=recent_history,
    )
    snapshot["process_behavior"] = report

    from reporting.recommendation_report import attach_recommendation_analysis

    attach_recommendation_analysis(snapshot)
    return report


def render_process_behavior_report(report: dict[str, Any]) -> str:
    lines = ["PROCESS BEHAVIOR ANALYSIS", "=" * 72]
    lines.append(f"Status   : {report.get('status', 'UNKNOWN')}")
    lines.append(
        "Profiles : "
        f"{report.get('profile_count', 0)} | "
        f"Anomalies: {report.get('anomaly_count', 0)} | "
        f"Runaways: {report.get('runaway_count', 0)}"
    )

    for runaway in report.get("runaways", []):
        lines.append(
            "RUNAWAY  : "
            f"{runaway.get('name')} (PID {runaway.get('pid')}) | "
            f"{format_size(runaway.get('latest_rate_bytes_per_second', 0.0))}/s | "
            f"{float(runaway.get('latest_share_percent', 0.0)):.1f}% share"
        )
    for anomaly in report.get("anomalies", []):
        lines.append(
            "ANOMALY  : "
            f"{anomaly.get('name')} (PID {anomaly.get('pid')}) | "
            + ", ".join(anomaly.get("signals", []))
        )

    if not report.get("runaways") and not report.get("anomalies"):
        lines.append(report.get("message", "No anomaly detected."))
    return "\n".join(lines)
