"""M6 conservative recommendation impact estimation."""

from __future__ import annotations

from typing import Any

from config.settings import (
    RECOMMENDATION_HIGH_IMPACT_SCORE,
    RECOMMENDATION_MEDIUM_IMPACT_SCORE,
)


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return min(high, max(low, value))


def _process_share(item: dict[str, Any]) -> float:
    return _clamp(
        float(item.get("io_share_percent", item.get("percentage", 0.0)))
    )


def _process_rate(item: dict[str, Any]) -> float:
    return max(
        0.0,
        float(
            item.get(
                "total_bytes_per_second",
                float(item.get("read_bytes_per_second", 0.0))
                + float(item.get("write_bytes_per_second", 0.0)),
            )
        ),
    )


def _find_target_process(
    snapshot: dict[str, Any],
    recommendation: dict[str, Any],
) -> dict[str, Any] | None:
    target_name = str(recommendation.get("target_process") or "").casefold()
    target_pid = recommendation.get("target_pid")
    consumers = snapshot.get("processes", {}).get("top_consumers", [])
    for item in consumers:
        if not isinstance(item, dict):
            continue
        name_matches = (
            not target_name
            or str(item.get("name", "")).casefold() == target_name
        )
        pid_matches = target_pid is None or item.get("pid") == target_pid
        if name_matches and pid_matches:
            return item
    return None


def _maximum_disk_usage(snapshot: dict[str, Any]) -> float:
    return max(
        (
            float(item.get("usage_percent", 0.0))
            for item in snapshot.get("disks", [])
            if isinstance(item, dict)
        ),
        default=0.0,
    )


def estimate_recommendation_impact(
    snapshot: dict[str, Any],
    recommendation: dict[str, Any],
) -> dict[str, Any]:
    """Estimate opportunity using observed evidence, not promised speedups.

    The score is an evidence-weighted prioritization aid. It deliberately does
    not predict exact throughput or latency improvement because M1-M5 do not
    benchmark the storage device's performance ceiling.
    """

    target = _find_target_process(snapshot, recommendation)
    root_cause = snapshot.get("root_cause", {})
    behavior = snapshot.get("process_behavior", {})

    priority = _clamp(float(recommendation.get("priority_score", 0.0)))
    confidence = _clamp(float(root_cause.get("confidence", 0.0)))
    score = priority * 0.35 + confidence * 0.20

    observed: dict[str, Any] = {}
    basis: list[str] = []

    if target is not None:
        share = _process_share(target)
        rate = _process_rate(target)
        observed.update(
            {
                "process_io_share_percent": round(share, 2),
                "process_io_rate_bytes_per_second": round(rate, 2),
            }
        )
        score += share * 0.30
        basis.append("current process I/O share")

        for runaway in behavior.get("runaways", []):
            if (
                str(runaway.get("name", "")).casefold()
                == str(target.get("name", "")).casefold()
                and runaway.get("pid") == target.get("pid")
            ):
                score += 20.0
                basis.append("sustained runaway evidence")
                break

        for anomaly in behavior.get("anomalies", []):
            if (
                str(anomaly.get("name", "")).casefold()
                == str(target.get("name", "")).casefold()
                and anomaly.get("pid") == target.get("pid")
            ):
                score += 10.0
                basis.append("baseline anomaly evidence")
                break

    maximum_usage = _maximum_disk_usage(snapshot)
    if recommendation.get("category") == "CAPACITY":
        observed["maximum_disk_usage_percent"] = round(maximum_usage, 2)
        score += (
            20.0
            if maximum_usage >= 95.0
            else 10.0
            if maximum_usage >= 80.0
            else 0.0
        )
        basis.append("disk capacity utilization")

    score = round(_clamp(score), 2)
    if score >= RECOMMENDATION_HIGH_IMPACT_SCORE:
        level = "HIGH"
    elif score >= RECOMMENDATION_MEDIUM_IMPACT_SCORE:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "impact_score": score,
        "impact_level": level,
        "confidence_percent": round(confidence, 2),
        "basis": basis,
        "observed": observed,
        "estimate_type": "EVIDENCE_WEIGHTED_OPPORTUNITY",
        "note": (
            "Impact is an evidence-weighted opportunity estimate, not a "
            "guaranteed performance gain. Re-measure after any manual change."
        ),
    }
