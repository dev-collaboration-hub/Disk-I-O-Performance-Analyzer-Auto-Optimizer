"""Detect disk-utilization and I/O-throughput spikes between snapshots."""

from __future__ import annotations

from typing import Any

from config.settings import (
    CRITICAL_DISK_USAGE_PERCENT,
    SPIKE_IO_MIN_BYTES_PER_SECOND,
    SPIKE_IO_MULTIPLIER,
    SPIKE_USAGE_DELTA_PERCENT,
)

SPIKE_THRESHOLD_PERCENT = SPIKE_USAGE_DELTA_PERCENT


def _disk_usage_map(snapshot: dict[str, Any]) -> dict[str, float]:
    disks = snapshot.get("disks")
    if isinstance(disks, list):
        return {
            str(item.get("path", "<unknown>")): float(
                item.get("usage_percent", 0.0)
            )
            for item in disks
            if isinstance(item, dict)
        }
    if "disk_usage_percent" in snapshot:
        return {
            str(snapshot.get("path", "<legacy>")): float(
                snapshot.get("disk_usage_percent", 0.0)
            )
        }
    return {}


def _total_io_rate(snapshot: dict[str, Any]) -> float:
    io = snapshot.get("io", {})
    if not isinstance(io, dict):
        return 0.0
    return max(
        0.0,
        float(io.get("read_bytes_per_second", 0.0))
        + float(io.get("write_bytes_per_second", 0.0)),
    )


def _event(
    *,
    timestamp: str | None,
    event_type: str,
    severity: str,
    message: str,
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "timestamp": timestamp,
        "event_type": event_type,
        "event": event_type,
        "severity": severity,
        "source": "spike_detector",
        "message": message,
        "details": details,
    }


def detect_snapshot_spikes(
    previous: dict[str, Any] | None,
    current: dict[str, Any],
    *,
    usage_delta_threshold: float = SPIKE_USAGE_DELTA_PERCENT,
    critical_usage_threshold: float = CRITICAL_DISK_USAGE_PERCENT,
    io_multiplier: float = SPIKE_IO_MULTIPLIER,
    io_minimum_bytes_per_second: float = SPIKE_IO_MIN_BYTES_PER_SECOND,
) -> list[dict[str, Any]]:
    """Return structured spike events observed from ``previous`` to ``current``."""

    if previous is None:
        return []
    if usage_delta_threshold < 0 or critical_usage_threshold < 0:
        raise ValueError("usage thresholds must be non-negative")
    if io_multiplier <= 1:
        raise ValueError("io_multiplier must be greater than 1")
    if io_minimum_bytes_per_second < 0:
        raise ValueError("io minimum must be non-negative")

    timestamp = current.get("timestamp")
    events: list[dict[str, Any]] = []
    previous_disks = _disk_usage_map(previous)
    current_disks = _disk_usage_map(current)

    for path, current_usage in current_disks.items():
        if path not in previous_disks:
            continue
        previous_usage = previous_disks[path]
        difference = current_usage - previous_usage
        if difference >= usage_delta_threshold:
            severity = (
                "CRITICAL"
                if current_usage >= critical_usage_threshold
                else "WARNING"
            )
            events.append(
                _event(
                    timestamp=timestamp,
                    event_type="DISK_USAGE_SPIKE",
                    severity=severity,
                    message=(
                        f"Disk usage on {path} increased by {difference:.1f} "
                        "percentage points."
                    ),
                    details={
                        "path": path,
                        "previous_usage_percent": previous_usage,
                        "current_usage_percent": current_usage,
                        "difference_percent": difference,
                    },
                )
            )
        if previous_usage < critical_usage_threshold <= current_usage:
            events.append(
                _event(
                    timestamp=timestamp,
                    event_type="CRITICAL_DISK_USAGE_ENTERED",
                    severity="CRITICAL",
                    message=f"Disk {path} entered critical capacity utilization.",
                    details={
                        "path": path,
                        "previous_usage_percent": previous_usage,
                        "current_usage_percent": current_usage,
                        "threshold_percent": critical_usage_threshold,
                    },
                )
            )

    previous_rate = _total_io_rate(previous)
    current_rate = _total_io_rate(current)
    if (
        previous_rate > 0
        and current_rate >= io_minimum_bytes_per_second
        and current_rate >= previous_rate * io_multiplier
    ):
        events.append(
            _event(
                timestamp=timestamp,
                event_type="DISK_IO_SPIKE",
                severity="WARNING",
                message=(
                    f"System disk throughput increased to {current_rate:.0f} "
                    f"bytes/s ({current_rate / previous_rate:.2f}x baseline)."
                ),
                details={
                    "previous_bytes_per_second": previous_rate,
                    "current_bytes_per_second": current_rate,
                    "multiplier": current_rate / previous_rate,
                    "configured_multiplier": io_multiplier,
                },
            )
        )

    return events


def detect_spikes(
    history: list[dict[str, Any]],
    *,
    usage_delta_threshold: float = SPIKE_USAGE_DELTA_PERCENT,
    critical_usage_threshold: float = CRITICAL_DISK_USAGE_PERCENT,
    io_multiplier: float = SPIKE_IO_MULTIPLIER,
    io_minimum_bytes_per_second: float = SPIKE_IO_MIN_BYTES_PER_SECOND,
) -> list[dict[str, Any]]:
    """Detect spikes across a chronological history (legacy-compatible API)."""

    events: list[dict[str, Any]] = []
    for previous, current in zip(history, history[1:]):
        events.extend(
            detect_snapshot_spikes(
                previous,
                current,
                usage_delta_threshold=usage_delta_threshold,
                critical_usage_threshold=critical_usage_threshold,
                io_multiplier=io_multiplier,
                io_minimum_bytes_per_second=io_minimum_bytes_per_second,
            )
        )
    return events


def print_spikes(history: list[dict[str, Any]]) -> None:
    events = detect_spikes(history)
    print("Disk Spike Report")
    print("=" * 72)
    if not events:
        print("No spikes detected.")
        return
    for event in events:
        print(
            f"{event.get('timestamp')} | {event['severity']} | "
            f"{event['message']}"
        )
