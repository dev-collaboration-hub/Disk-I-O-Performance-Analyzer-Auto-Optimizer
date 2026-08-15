"""M4 disk bottleneck identification.

The detector combines capacity pressure, current process I/O dominance, and
M3 spike evidence. It intentionally avoids treating raw throughput alone as a
bottleneck because storage devices have very different performance ceilings.
"""

from __future__ import annotations

from typing import Any

from config.settings import (
    CRITICAL_DISK_USAGE_PERCENT,
    ROOT_CAUSE_MIN_PROCESS_RATE_BYTES_PER_SECOND,
    ROOT_CAUSE_PROCESS_SHARE_PERCENT,
    WARNING_DISK_USAGE_PERCENT,
)


def _process_share(process: dict[str, Any]) -> float:
    return max(
        0.0,
        float(
            process.get(
                "io_share_percent",
                process.get("percentage", 0.0),
            )
        ),
    )


def _process_rate(process: dict[str, Any]) -> float:
    if "total_bytes_per_second" in process:
        return max(0.0, float(process.get("total_bytes_per_second", 0.0)))
    return max(
        0.0,
        float(process.get("read_bytes_per_second", 0.0))
        + float(process.get("write_bytes_per_second", 0.0)),
    )


def _select_top_process(
    top_processes: list[dict[str, Any]] | None,
) -> dict[str, Any] | None:
    candidates = [
        item for item in (top_processes or []) if isinstance(item, dict)
    ]
    if not candidates:
        return None

    return max(
        candidates,
        key=lambda item: (
            _process_share(item),
            _process_rate(item),
            -int(item.get("pid", 0) or 0),
            str(item.get("name", "")).casefold(),
        ),
    )


def detect_bottleneck(
    disk_usage_percent: float,
    top_processes: list[dict[str, Any]] | None,
    *,
    spike_detected: bool = False,
    warning_usage_percent: float = WARNING_DISK_USAGE_PERCENT,
    critical_usage_percent: float = CRITICAL_DISK_USAGE_PERCENT,
    process_share_threshold: float = ROOT_CAUSE_PROCESS_SHARE_PERCENT,
    minimum_process_rate: float = ROOT_CAUSE_MIN_PROCESS_RATE_BYTES_PER_SECOND,
) -> dict[str, Any]:
    """Identify meaningful disk pressure and the most likely active process.

    ``disk_usage_percent`` represents capacity utilization, not device busy
    time. Therefore high capacity is reported as a capacity-pressure signal,
    while current process dominance and M3 spike evidence are separate signals.
    """

    if warning_usage_percent < 0 or critical_usage_percent < 0:
        raise ValueError("disk usage thresholds must be non-negative")
    if critical_usage_percent < warning_usage_percent:
        raise ValueError("critical threshold must be >= warning threshold")
    if not 0 <= process_share_threshold <= 100:
        raise ValueError("process share threshold must be between 0 and 100")
    if minimum_process_rate < 0:
        raise ValueError("minimum process rate must be non-negative")

    usage = max(0.0, float(disk_usage_percent))
    top_process = _select_top_process(top_processes)
    process_share = _process_share(top_process) if top_process else 0.0
    process_rate = _process_rate(top_process) if top_process else 0.0

    capacity_warning = usage >= warning_usage_percent
    critical_capacity = usage >= critical_usage_percent
    process_dominance = bool(
        top_process
        and process_share >= process_share_threshold
        and process_rate >= minimum_process_rate
    )

    signals: list[str] = []
    evidence: list[str] = []

    if critical_capacity:
        signals.append("CRITICAL_CAPACITY_PRESSURE")
        evidence.append(
            f"Disk capacity utilization is critical at {usage:.1f}%."
        )
    elif capacity_warning:
        signals.append("CAPACITY_PRESSURE")
        evidence.append(
            f"Disk capacity utilization is elevated at {usage:.1f}%."
        )

    if process_dominance and top_process is not None:
        signals.append("PROCESS_IO_DOMINANCE")
        evidence.append(
            f"{top_process.get('name', '<unknown>')} accounts for "
            f"{process_share:.2f}% of active process disk I/O "
            f"at {process_rate:.0f} bytes/s."
        )

    if spike_detected:
        signals.append("RECENT_IO_SPIKE")
        evidence.append("A recent disk activity spike was detected by M3.")

    bottleneck_detected = bool(signals)
    severity = "NORMAL"
    if bottleneck_detected:
        severity = "WARNING"
        if (
            critical_capacity
            or process_share >= 85.0
            or (spike_detected and process_dominance)
        ):
            severity = "CRITICAL"

    return {
        "bottleneck_detected": bottleneck_detected,
        "severity": severity,
        "signals": signals,
        "likely_process": (
            str(top_process.get("name", "<unknown>"))
            if top_process is not None and process_dominance
            else None
        ),
        "likely_pid": (
            int(top_process.get("pid", 0) or 0)
            if top_process is not None and process_dominance
            else None
        ),
        "process_share_percent": round(process_share, 2),
        "process_rate_bytes_per_second": round(process_rate, 2),
        "disk_usage_percent": round(usage, 2),
        "evidence": evidence,
    }


def detect_snapshot_bottleneck(
    snapshot: dict[str, Any],
    *,
    spike_detected: bool | None = None,
) -> dict[str, Any]:
    """Run M4 bottleneck detection directly against an M1-M3 snapshot."""

    disks = snapshot.get("disks", [])
    disk_usage = max(
        (
            float(item.get("usage_percent", 0.0))
            for item in disks
            if isinstance(item, dict)
        ),
        default=0.0,
    )

    process_data = snapshot.get("processes", {})
    top_processes = (
        process_data.get("top_consumers", [])
        if isinstance(process_data, dict)
        else []
    )

    if spike_detected is None:
        recent_events = snapshot.get("history", {}).get("recent_events", [])
        spike_detected = any(
            isinstance(event, dict)
            and event.get("event_type") in {"DISK_IO_SPIKE", "DISK_USAGE_SPIKE"}
            for event in recent_events
        )

    return detect_bottleneck(
        disk_usage,
        top_processes,
        spike_detected=bool(spike_detected),
    )
