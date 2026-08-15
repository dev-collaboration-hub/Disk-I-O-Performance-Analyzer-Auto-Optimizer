"""M5 anomaly detection for current process disk-I/O behavior."""

from __future__ import annotations

from statistics import median
from typing import Any

from config.settings import (
    PROCESS_ANOMALY_MIN_BASELINE_SAMPLES,
    PROCESS_ANOMALY_MIN_RATE_BYTES_PER_SECOND,
    PROCESS_ANOMALY_RATE_MULTIPLIER,
    PROCESS_ANOMALY_SHARE_DELTA_PERCENT,
)
from analysis.process_profiler import (
    normalize_process_name,
    process_rate,
    process_share,
)


def _consumers(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    processes = snapshot.get("processes", {})
    if not isinstance(processes, dict):
        return []
    return [
        item
        for item in processes.get("top_consumers", [])
        if isinstance(item, dict)
    ]


def _best_by_name(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    for process in _consumers(snapshot):
        key = normalize_process_name(process.get("name"))
        current = best.get(key)
        if current is None or (
            process_rate(process),
            process_share(process),
            -int(process.get("pid", 0) or 0),
        ) > (
            process_rate(current),
            process_share(current),
            -int(current.get("pid", 0) or 0),
        ):
            best[key] = process
    return best


def _prior_records(
    current: dict[str, Any],
    history: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    records = [item for item in (history or []) if isinstance(item, dict)]
    if records and records[-1].get("timestamp") == current.get("timestamp"):
        records = records[:-1]
    return records


def detect_process_anomalies(
    current: dict[str, Any],
    recent_history: list[dict[str, Any]] | None,
    *,
    minimum_baseline_samples: int = PROCESS_ANOMALY_MIN_BASELINE_SAMPLES,
    rate_multiplier: float = PROCESS_ANOMALY_RATE_MULTIPLIER,
    share_delta_percent: float = PROCESS_ANOMALY_SHARE_DELTA_PERCENT,
    minimum_rate_bytes_per_second: float = (
        PROCESS_ANOMALY_MIN_RATE_BYTES_PER_SECOND
    ),
) -> list[dict[str, Any]]:
    """Detect current processes that depart materially from their own baseline."""

    if minimum_baseline_samples < 1:
        raise ValueError("minimum_baseline_samples must be at least 1")
    if rate_multiplier <= 1:
        raise ValueError("rate_multiplier must be greater than 1")
    if share_delta_percent < 0 or minimum_rate_bytes_per_second < 0:
        raise ValueError("anomaly thresholds must be non-negative")

    priors = _prior_records(current, recent_history)
    baseline: dict[str, list[tuple[float, float]]] = {}
    for snapshot in priors:
        for key, process in _best_by_name(snapshot).items():
            baseline.setdefault(key, []).append(
                (process_rate(process), process_share(process))
            )

    anomalies: list[dict[str, Any]] = []
    for key, process in _best_by_name(current).items():
        samples = baseline.get(key, [])
        if len(samples) < minimum_baseline_samples:
            continue

        rates = [item[0] for item in samples]
        shares = [item[1] for item in samples]
        baseline_rate = float(median(rates))
        baseline_share = float(median(shares))
        current_rate = process_rate(process)
        current_share = process_share(process)

        rate_threshold = max(
            minimum_rate_bytes_per_second,
            baseline_rate * rate_multiplier,
        )
        rate_anomaly = (
            current_rate >= rate_threshold
            and current_rate > baseline_rate
        )
        share_anomaly = (
            current_rate >= minimum_rate_bytes_per_second
            and current_share >= baseline_share + share_delta_percent
        )
        if not (rate_anomaly or share_anomaly):
            continue

        signals: list[str] = []
        evidence: list[str] = []
        rate_ratio: float | None = None
        if rate_anomaly:
            signals.append("RATE_SPIKE")
            if baseline_rate > 0:
                rate_ratio = current_rate / baseline_rate
                evidence.append(
                    f"Current rate is {rate_ratio:.2f}x the historical median."
                )
            else:
                evidence.append(
                    "Current process I/O is active while the historical median is zero."
                )
        if share_anomaly:
            signals.append("SHARE_JUMP")
            evidence.append(
                "Current I/O share is "
                f"{current_share - baseline_share:.1f} percentage points "
                "above the historical median."
            )

        severity = "WARNING"
        if (
            current_share >= 90.0
            or (rate_ratio is not None and rate_ratio >= rate_multiplier * 2)
        ):
            severity = "CRITICAL"

        anomalies.append(
            {
                "name": str(process.get("name", "<unknown>")),
                "pid": int(process.get("pid", 0) or 0),
                "severity": severity,
                "signals": signals,
                "baseline_samples": len(samples),
                "current_rate_bytes_per_second": round(current_rate, 2),
                "baseline_rate_bytes_per_second": round(baseline_rate, 2),
                "rate_ratio": round(rate_ratio, 2)
                if rate_ratio is not None
                else None,
                "current_share_percent": round(current_share, 2),
                "baseline_share_percent": round(baseline_share, 2),
                "evidence": evidence,
            }
        )

    anomalies.sort(
        key=lambda item: (
            item["severity"] == "CRITICAL",
            item["current_rate_bytes_per_second"],
            item["current_share_percent"],
            item["name"].casefold(),
        ),
        reverse=True,
    )
    return anomalies
