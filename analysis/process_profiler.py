"""M5 process behavior profiling from recent monitoring snapshots."""

from __future__ import annotations

from statistics import mean, median
from typing import Any

from config.settings import ROOT_CAUSE_PROCESS_SHARE_PERCENT


def _consumers(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    processes = snapshot.get("processes", {})
    if not isinstance(processes, dict):
        return []
    return [
        item
        for item in processes.get("top_consumers", [])
        if isinstance(item, dict)
    ]


def process_rate(process: dict[str, Any]) -> float:
    if "total_bytes_per_second" in process:
        return max(0.0, float(process.get("total_bytes_per_second", 0.0)))
    return max(
        0.0,
        float(process.get("read_bytes_per_second", 0.0))
        + float(process.get("write_bytes_per_second", 0.0)),
    )


def process_share(process: dict[str, Any]) -> float:
    return max(
        0.0,
        float(
            process.get(
                "io_share_percent",
                process.get("percentage", 0.0),
            )
        ),
    )


def normalize_process_name(name: object) -> str:
    return str(name or "<unknown>").strip().casefold()


def _snapshot_best_by_name(
    snapshot: dict[str, Any],
) -> dict[str, dict[str, Any]]:
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


def _trend_label(rates: list[float]) -> tuple[str, float | None]:
    if len(rates) < 2:
        return "INSUFFICIENT_HISTORY", None
    first = rates[0]
    last = rates[-1]
    if first <= 0:
        if last > 0:
            return "INCREASING", None
        return "STABLE", 1.0
    ratio = last / first
    if ratio >= 1.5:
        return "INCREASING", round(ratio, 2)
    if ratio <= 0.67:
        return "DECREASING", round(ratio, 2)
    return "STABLE", round(ratio, 2)


def build_process_profiles(
    history: list[dict[str, Any]],
    *,
    max_samples: int = 20,
    dominance_share_percent: float = ROOT_CAUSE_PROCESS_SHARE_PERCENT,
) -> list[dict[str, Any]]:
    """Build deterministic name-level behavior profiles from recent snapshots."""

    if max_samples < 0:
        raise ValueError("max_samples must be non-negative")
    if dominance_share_percent < 0:
        raise ValueError("dominance_share_percent must be non-negative")
    if max_samples == 0:
        return []

    records = [
        item for item in history if isinstance(item, dict)
    ][-max_samples:]
    samples: dict[str, list[dict[str, Any]]] = {}

    for snapshot in records:
        timestamp = snapshot.get("timestamp")
        for key, process in _snapshot_best_by_name(snapshot).items():
            rate = process_rate(process)
            share = process_share(process)
            read_rate = max(
                0.0,
                float(process.get("read_bytes_per_second", 0.0)),
            )
            write_rate = max(
                0.0,
                float(process.get("write_bytes_per_second", 0.0)),
            )
            samples.setdefault(key, []).append(
                {
                    "timestamp": timestamp,
                    "name": str(process.get("name", "<unknown>")),
                    "pid": int(process.get("pid", 0) or 0),
                    "create_time": float(process.get("create_time", 0.0) or 0.0),
                    "rate": rate,
                    "share": share,
                    "read_rate": read_rate,
                    "write_rate": write_rate,
                }
            )

    profiles: list[dict[str, Any]] = []
    for key, process_samples in samples.items():
        rates = [item["rate"] for item in process_samples]
        shares = [item["share"] for item in process_samples]
        total_read = sum(item["read_rate"] for item in process_samples)
        total_write = sum(item["write_rate"] for item in process_samples)
        total_directional = total_read + total_write
        trend, trend_ratio = _trend_label(rates)
        rate_median = median(rates)
        burst_ratio = (
            round(max(rates) / rate_median, 2)
            if rate_median > 0
            else None
        )
        latest = process_samples[-1]

        profiles.append(
            {
                "process_key": key,
                "name": latest["name"],
                "latest_pid": latest["pid"],
                "samples_observed": len(process_samples),
                "first_timestamp": process_samples[0]["timestamp"],
                "last_timestamp": latest["timestamp"],
                "average_rate_bytes_per_second": round(mean(rates), 2),
                "median_rate_bytes_per_second": round(rate_median, 2),
                "maximum_rate_bytes_per_second": round(max(rates), 2),
                "latest_rate_bytes_per_second": round(latest["rate"], 2),
                "average_share_percent": round(mean(shares), 2),
                "median_share_percent": round(median(shares), 2),
                "maximum_share_percent": round(max(shares), 2),
                "latest_share_percent": round(latest["share"], 2),
                "dominance_samples": sum(
                    share >= dominance_share_percent for share in shares
                ),
                "read_ratio_percent": round(
                    (total_read / total_directional) * 100, 2
                )
                if total_directional
                else 0.0,
                "write_ratio_percent": round(
                    (total_write / total_directional) * 100, 2
                )
                if total_directional
                else 0.0,
                "trend": trend,
                "trend_ratio": trend_ratio,
                "burst_ratio": burst_ratio,
            }
        )

    profiles.sort(
        key=lambda item: (
            item["latest_rate_bytes_per_second"],
            item["average_rate_bytes_per_second"],
            item["latest_share_percent"],
            item["process_key"],
        ),
        reverse=True,
    )
    return profiles
