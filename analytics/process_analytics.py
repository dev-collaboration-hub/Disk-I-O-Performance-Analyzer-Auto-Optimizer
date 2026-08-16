"""M9 aggregate analytics for observed top disk-I/O consumers."""

from __future__ import annotations

from statistics import mean
from typing import Any

from config.settings import ANALYTICS_TOP_PROCESSES


def _rate(process: dict[str, Any]) -> float:
    if "total_bytes_per_second" in process:
        return max(0.0, float(process.get("total_bytes_per_second", 0.0)))
    return max(0.0, float(process.get("read_bytes_per_second", 0.0))) + max(
        0.0, float(process.get("write_bytes_per_second", 0.0))
    )


def _share(process: dict[str, Any]) -> float:
    return max(
        0.0,
        float(process.get("io_share_percent", process.get("percentage", 0.0))),
    )


def analyze_processes(
    records: list[dict[str, Any]] | None,
    *,
    top_n: int = ANALYTICS_TOP_PROCESSES,
) -> dict[str, Any]:
    """Summarize only the process consumers retained in monitoring snapshots."""

    if top_n < 0:
        raise ValueError("top_n must be non-negative")

    snapshots = [item for item in (records or []) if isinstance(item, dict)]
    aggregates: dict[str, dict[str, Any]] = {}

    for record in snapshots:
        processes = record.get("processes", {})
        consumers = processes.get("top_consumers", []) if isinstance(processes, dict) else []
        seen_names: set[str] = set()
        for index, process in enumerate(consumers if isinstance(consumers, list) else []):
            if not isinstance(process, dict):
                continue
            display_name = str(process.get("name") or "<unknown>")
            key = display_name.casefold()
            if key in seen_names:
                continue
            seen_names.add(key)
            bucket = aggregates.setdefault(
                key,
                {
                    "name": display_name,
                    "samples_seen": 0,
                    "dominant_samples": 0,
                    "rates": [],
                    "shares": [],
                    "latest_rate_bytes_per_second": 0.0,
                    "latest_share_percent": 0.0,
                    "latest_pid": None,
                    "last_timestamp": None,
                    "anomaly_events": 0,
                    "runaway_events": 0,
                },
            )
            rate, share = _rate(process), _share(process)
            bucket["samples_seen"] += 1
            bucket["dominant_samples"] += int(index == 0)
            bucket["rates"].append(rate)
            bucket["shares"].append(share)
            bucket["latest_rate_bytes_per_second"] = rate
            bucket["latest_share_percent"] = share
            bucket["latest_pid"] = process.get("pid")
            bucket["last_timestamp"] = record.get("timestamp")

        behavior = record.get("process_behavior", {})
        if isinstance(behavior, dict):
            for anomaly in behavior.get("anomalies", []):
                if isinstance(anomaly, dict):
                    key = str(anomaly.get("name") or "<unknown>").casefold()
                    aggregates.setdefault(
                        key,
                        {
                            "name": str(anomaly.get("name") or "<unknown>"),
                            "samples_seen": 0,
                            "dominant_samples": 0,
                            "rates": [],
                            "shares": [],
                            "latest_rate_bytes_per_second": 0.0,
                            "latest_share_percent": 0.0,
                            "latest_pid": anomaly.get("pid"),
                            "last_timestamp": record.get("timestamp"),
                            "anomaly_events": 0,
                            "runaway_events": 0,
                        },
                    )["anomaly_events"] += 1
            for runaway in behavior.get("runaways", []):
                if isinstance(runaway, dict):
                    key = str(runaway.get("name") or "<unknown>").casefold()
                    aggregates.setdefault(
                        key,
                        {
                            "name": str(runaway.get("name") or "<unknown>"),
                            "samples_seen": 0,
                            "dominant_samples": 0,
                            "rates": [],
                            "shares": [],
                            "latest_rate_bytes_per_second": 0.0,
                            "latest_share_percent": 0.0,
                            "latest_pid": runaway.get("pid"),
                            "last_timestamp": record.get("timestamp"),
                            "anomaly_events": 0,
                            "runaway_events": 0,
                        },
                    )["runaway_events"] += 1

    reports: list[dict[str, Any]] = []
    for bucket in aggregates.values():
        rates = bucket.pop("rates")
        shares = bucket.pop("shares")
        samples = int(bucket["samples_seen"])
        reports.append(
            {
                **bucket,
                "average_rate_bytes_per_second": round(mean(rates), 2) if rates else 0.0,
                "maximum_rate_bytes_per_second": round(max(rates), 2) if rates else 0.0,
                "average_share_percent": round(mean(shares), 2) if shares else 0.0,
                "maximum_share_percent": round(max(shares), 2) if shares else 0.0,
                "observation_frequency_percent": round(
                    (samples / len(snapshots) * 100.0) if snapshots else 0.0, 2
                ),
                "dominance_frequency_percent": round(
                    (bucket["dominant_samples"] / samples * 100.0) if samples else 0.0,
                    2,
                ),
            }
        )

    reports.sort(
        key=lambda item: (
            item["runaway_events"],
            item["anomaly_events"],
            item["maximum_rate_bytes_per_second"],
            item["dominant_samples"],
            item["name"].casefold(),
        ),
        reverse=True,
    )
    return {
        "status": "OK" if snapshots else "NO_DATA",
        "snapshot_count": len(snapshots),
        "observed_process_count": len(reports),
        "processes": reports[:top_n] if top_n else [],
        "coverage_note": (
            "Process analytics cover retained top-consumer observations, not every system process."
        ),
    }
