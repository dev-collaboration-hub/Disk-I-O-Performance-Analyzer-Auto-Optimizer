"""M4 root-cause analysis and reporting."""

from __future__ import annotations

from typing import Any

from analysis.bottleneck_detector import (
    detect_bottleneck,
    detect_snapshot_bottleneck,
)
from analysis.cause_classifier import classify_process
from analysis.confidence_engine import calculate_confidence
from config.settings import (
    ROOT_CAUSE_PROCESS_SHARE_PERCENT,
    ROOT_CAUSE_SUSTAINED_SAMPLES,
)

_RECOMMENDATIONS = {
    "Windows Search Indexing": "Pause or reschedule indexing if it is disrupting foreground work.",
    "Windows Defender Scan": "Schedule full scans for idle periods and verify exclusions carefully.",
    "Antivirus Scan": "Move intensive scans to idle periods and review scan scope.",
    "Browser Activity": "Reduce disk-heavy tabs, downloads, caches, or extensions.",
    "Development Environment Activity": "Close unused projects and inspect build/indexing activity.",
    "Python Runtime Activity": "Inspect the active script's file access pattern and batching behavior.",
    "JavaScript Runtime or Build Activity": "Inspect build/watch tasks and dependency-cache writes.",
    "Database Activity": "Inspect query load, checkpoints, compaction, and database file growth.",
    "File Synchronization": "Pause or rate-limit large synchronization jobs during foreground work.",
    "Backup Activity": "Move backup jobs to idle periods or reduce their I/O concurrency.",
    "Windows Background Service": "Identify the specific hosted service before changing its behavior.",
    "Unknown Process Activity": "Inspect the process command, owner, open files, and recent activity.",
    "Disk Capacity Pressure": "Free disk space or move large data before performance degrades further.",
    "System Disk I/O Spike": "Inspect recent processes and events to identify the source of the spike.",
}


def _share(process: dict[str, Any]) -> float:
    return max(
        0.0,
        float(process.get("io_share_percent", process.get("percentage", 0.0))),
    )


def _top_process(
    top_processes: list[dict[str, Any]] | None,
) -> dict[str, Any] | None:
    processes = [item for item in (top_processes or []) if isinstance(item, dict)]
    if not processes:
        return None
    return max(
        processes,
        key=lambda item: (
            _share(item),
            float(item.get("total_bytes_per_second", 0.0)),
            -int(item.get("pid", 0) or 0),
        ),
    )


def _is_sustained_process_activity(
    history: list[dict[str, Any]] | None,
    process_name: str | None,
    *,
    required_samples: int = ROOT_CAUSE_SUSTAINED_SAMPLES,
    minimum_share_percent: float = ROOT_CAUSE_PROCESS_SHARE_PERCENT,
) -> bool:
    if not process_name or required_samples <= 1:
        return bool(process_name)
    records = [item for item in (history or []) if isinstance(item, dict)]
    if len(records) < required_samples:
        return False

    selected = records[-required_samples:]
    expected = process_name.casefold()
    for snapshot in selected:
        consumers = snapshot.get("processes", {}).get("top_consumers", [])
        top = _top_process(consumers)
        if top is None:
            return False
        if str(top.get("name", "")).casefold() != expected:
            return False
        if _share(top) < minimum_share_percent:
            return False
    return True


def generate_root_cause_report(
    disk_usage_percent: float,
    top_processes: list[dict[str, Any]] | None,
    spike_detected: bool = False,
    sustained_activity: bool = False,
) -> dict[str, Any]:
    """Generate a structured M4 root-cause report.

    This keeps the repository's original public function signature while using
    the new bottleneck detector and richer evidence.
    """

    bottleneck = detect_bottleneck(
        disk_usage_percent,
        top_processes,
        spike_detected=spike_detected,
    )

    if not bottleneck["bottleneck_detected"]:
        return {
            "status": "NO_BOTTLENECK",
            "severity": "NORMAL",
            "confidence": 0.0,
            "signals": [],
            "evidence": [],
            "message": "No significant disk bottleneck evidence detected.",
            "recommendation": "Continue monitoring.",
        }

    process_name = bottleneck["likely_process"]
    process_share = float(bottleneck["process_share_percent"])

    if process_name:
        cause_info = classify_process(process_name)
        cause = cause_info["cause"]
        category = cause_info["category"]
        confidence = calculate_confidence(
            process_share=process_share,
            spike_detected=spike_detected,
            sustained_activity=sustained_activity,
        )
        if cause_info.get("matched_rule") != "unknown":
            confidence = min(100.0, round(confidence + 10.0, 2))
    elif any(
        signal in bottleneck["signals"]
        for signal in ("CAPACITY_PRESSURE", "CRITICAL_CAPACITY_PRESSURE")
    ):
        cause = "Disk Capacity Pressure"
        category = "Storage Capacity"
        confidence = min(100.0, max(70.0, float(disk_usage_percent)))
    else:
        cause = "System Disk I/O Spike"
        category = "System I/O"
        confidence = 60.0 if spike_detected else 40.0

    evidence = list(bottleneck["evidence"])
    if sustained_activity and process_name:
        evidence.append(
            f"{process_name} remained dominant across recent monitoring samples."
        )

    return {
        "status": "BOTTLENECK_DETECTED",
        "severity": bottleneck["severity"],
        "signals": list(bottleneck["signals"]),
        "process": process_name,
        "pid": bottleneck["likely_pid"],
        "process_share_percent": process_share,
        "process_rate_bytes_per_second": bottleneck[
            "process_rate_bytes_per_second"
        ],
        "disk_usage_percent": bottleneck["disk_usage_percent"],
        "cause": cause,
        "category": category,
        "confidence": round(float(confidence), 2),
        "sustained_activity": bool(sustained_activity),
        "evidence": evidence,
        "recommendation": _RECOMMENDATIONS.get(
            cause,
            "Collect more evidence before changing system behavior.",
        ),
    }


def analyze_snapshot_root_cause(
    snapshot: dict[str, Any],
    *,
    recent_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Analyze one current M1-M3 snapshot and return its M4 assessment."""

    bottleneck = detect_snapshot_bottleneck(snapshot)
    process_name = bottleneck.get("likely_process")
    sustained = _is_sustained_process_activity(
        recent_history,
        process_name,
    )
    spike_detected = "RECENT_IO_SPIKE" in bottleneck.get("signals", [])

    process_data = snapshot.get("processes", {})
    top_processes = (
        process_data.get("top_consumers", [])
        if isinstance(process_data, dict)
        else []
    )

    report = generate_root_cause_report(
        bottleneck.get("disk_usage_percent", 0.0),
        top_processes,
        spike_detected=spike_detected,
        sustained_activity=sustained,
    )

    io_stats = snapshot.get("io", {})
    report["analysis_version"] = 1
    report["timestamp"] = snapshot.get("timestamp")
    report["system_io_bytes_per_second"] = round(
        max(
            0.0,
            float(io_stats.get("read_bytes_per_second", 0.0))
            + float(io_stats.get("write_bytes_per_second", 0.0)),
        ),
        2,
    )
    return report


def attach_root_cause_analysis(
    snapshot: dict[str, Any],
    *,
    recent_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Attach an M4 root-cause assessment to a monitoring snapshot."""

    report = analyze_snapshot_root_cause(
        snapshot,
        recent_history=recent_history,
    )
    snapshot["root_cause"] = report
    return report


def render_root_cause_report(report: dict[str, Any]) -> str:
    lines = ["ROOT CAUSE ANALYSIS", "=" * 72]
    if report.get("status") != "BOTTLENECK_DETECTED":
        lines.append(report.get("message", "No bottleneck detected."))
        return "\n".join(lines)

    lines.extend(
        [
            f"Cause      : {report.get('cause')}",
            f"Process    : {report.get('process') or 'n/a'}",
            f"Category   : {report.get('category')}",
            f"Severity   : {report.get('severity')}",
            f"Confidence : {float(report.get('confidence', 0.0)):.2f}%",
            "",
            "Evidence",
            "-" * 72,
        ]
    )
    lines.extend(f"- {item}" for item in report.get("evidence", []))
    lines.extend(
        [
            "",
            "Recommendation",
            "-" * 72,
            str(report.get("recommendation", "Continue monitoring.")),
        ]
    )
    return "\n".join(lines)


def print_root_cause_report(report: dict[str, Any]) -> None:
    print(render_root_cause_report(report))


if __name__ == "__main__":
    sample_processes = [
        {
            "pid": 101,
            "name": "SearchIndexer.exe",
            "percentage": 72.5,
            "total_bytes_per_second": 5_000_000,
        }
    ]
    print_root_cause_report(
        generate_root_cause_report(
            disk_usage_percent=92,
            top_processes=sample_processes,
            spike_detected=True,
            sustained_activity=True,
        )
    )
