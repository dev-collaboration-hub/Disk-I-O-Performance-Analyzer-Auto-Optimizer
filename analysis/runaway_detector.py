"""M5 sustained runaway-process detection."""

from __future__ import annotations

from typing import Any

from config.settings import (
    RUNAWAY_PROCESS_MIN_RATE_BYTES_PER_SECOND,
    RUNAWAY_PROCESS_SAMPLES,
    RUNAWAY_PROCESS_SHARE_PERCENT,
)
from analysis.process_profiler import process_rate, process_share


def _consumers(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    processes = snapshot.get("processes", {})
    if not isinstance(processes, dict):
        return []
    return [
        item
        for item in processes.get("top_consumers", [])
        if isinstance(item, dict)
    ]


def _identity(process: dict[str, Any]) -> tuple[str, int, float]:
    return (
        str(process.get("name", "<unknown>")).strip().casefold(),
        int(process.get("pid", 0) or 0),
        float(process.get("create_time", 0.0) or 0.0),
    )


def _find_identity(
    snapshot: dict[str, Any],
    identity: tuple[str, int, float],
) -> dict[str, Any] | None:
    for process in _consumers(snapshot):
        if _identity(process) == identity:
            return process
    return None


def detect_runaway_processes(
    current: dict[str, Any],
    recent_history: list[dict[str, Any]] | None,
    *,
    required_samples: int = RUNAWAY_PROCESS_SAMPLES,
    minimum_share_percent: float = RUNAWAY_PROCESS_SHARE_PERCENT,
    minimum_rate_bytes_per_second: float = (
        RUNAWAY_PROCESS_MIN_RATE_BYTES_PER_SECOND
    ),
) -> list[dict[str, Any]]:
    """Detect one process instance sustaining dominant, high-rate disk I/O."""

    if required_samples < 2:
        raise ValueError("required_samples must be at least 2")
    if minimum_share_percent < 0 or minimum_rate_bytes_per_second < 0:
        raise ValueError("runaway thresholds must be non-negative")

    records = [item for item in (recent_history or []) if isinstance(item, dict)]
    if not records or records[-1].get("timestamp") != current.get("timestamp"):
        records.append(current)
    if len(records) < required_samples:
        return []

    selected = records[-required_samples:]
    runaways: list[dict[str, Any]] = []

    for process in _consumers(current):
        if (
            process_share(process) < minimum_share_percent
            or process_rate(process) < minimum_rate_bytes_per_second
        ):
            continue

        identity = _identity(process)
        observed: list[dict[str, Any]] = []
        for snapshot in selected:
            matching = _find_identity(snapshot, identity)
            if matching is None:
                observed = []
                break
            if (
                process_share(matching) < minimum_share_percent
                or process_rate(matching) < minimum_rate_bytes_per_second
            ):
                observed = []
                break
            observed.append(matching)

        if len(observed) != required_samples:
            continue

        rates = [process_rate(item) for item in observed]
        shares = [process_share(item) for item in observed]
        trend_ratio = rates[-1] / rates[0] if rates[0] > 0 else None
        severity = "WARNING"
        if (
            shares[-1] >= 80.0
            and rates[-1] >= minimum_rate_bytes_per_second * 2
        ) or (trend_ratio is not None and trend_ratio >= 2.0):
            severity = "CRITICAL"

        evidence = [
            (
                f"Same process instance stayed above {minimum_share_percent:.1f}% "
                f"I/O share for {required_samples} consecutive samples."
            ),
            (
                f"Same process instance stayed above "
                f"{minimum_rate_bytes_per_second:.0f} bytes/s for "
                f"{required_samples} consecutive samples."
            ),
        ]
        if trend_ratio is not None:
            evidence.append(
                f"Latest rate is {trend_ratio:.2f}x the first rate in the window."
            )

        runaways.append(
            {
                "name": str(process.get("name", "<unknown>")),
                "pid": int(process.get("pid", 0) or 0),
                "create_time": float(process.get("create_time", 0.0) or 0.0),
                "severity": severity,
                "samples": required_samples,
                "latest_rate_bytes_per_second": round(rates[-1], 2),
                "average_rate_bytes_per_second": round(
                    sum(rates) / len(rates), 2
                ),
                "latest_share_percent": round(shares[-1], 2),
                "average_share_percent": round(
                    sum(shares) / len(shares), 2
                ),
                "trend_ratio": round(trend_ratio, 2)
                if trend_ratio is not None
                else None,
                "evidence": evidence,
            }
        )

    runaways.sort(
        key=lambda item: (
            item["severity"] == "CRITICAL",
            item["latest_rate_bytes_per_second"],
            item["latest_share_percent"],
            item["name"].casefold(),
        ),
        reverse=True,
    )
    return runaways
