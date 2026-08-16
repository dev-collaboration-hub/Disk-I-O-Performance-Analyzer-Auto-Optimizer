"""M9 historical disk and system-I/O trend analytics."""

from __future__ import annotations

from datetime import datetime, timezone
from statistics import mean, median
from typing import Any

from config.settings import ANALYTICS_MIN_TREND_SAMPLES


def _timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * min(1.0, max(0.0, percentile))
    lower = int(rank)
    upper = min(len(ordered) - 1, lower + 1)
    fraction = rank - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _trend(
    points: list[tuple[datetime | None, float]],
    *,
    minimum_samples: int = ANALYTICS_MIN_TREND_SAMPLES,
) -> dict[str, Any]:
    if len(points) < minimum_samples:
        return {
            "direction": "INSUFFICIENT_DATA",
            "slope_per_hour": None,
            "samples": len(points),
        }

    dated = [(stamp, value) for stamp, value in points if stamp is not None]
    if len(dated) >= minimum_samples:
        origin = dated[0][0]
        xs = [(stamp - origin).total_seconds() / 3600.0 for stamp, _ in dated]
        ys = [value for _, value in dated]
        if max(xs, default=0.0) > min(xs, default=0.0):
            x_mean, y_mean = mean(xs), mean(ys)
            denominator = sum((x - x_mean) ** 2 for x in xs)
            slope = (
                sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
                / denominator
                if denominator
                else 0.0
            )
        else:
            slope = 0.0
    else:
        ys = [value for _, value in points]
        x_mean = (len(ys) - 1) / 2.0
        y_mean = mean(ys)
        denominator = sum((index - x_mean) ** 2 for index in range(len(ys)))
        per_sample = (
            sum(
                (index - x_mean) * (value - y_mean)
                for index, value in enumerate(ys)
            )
            / denominator
            if denominator
            else 0.0
        )
        slope = per_sample

    magnitude = abs(slope)
    direction = "STABLE" if magnitude < 0.01 else ("INCREASING" if slope > 0 else "DECREASING")
    return {
        "direction": direction,
        "slope_per_hour": round(slope, 4),
        "samples": len(points),
    }


def _io_total(record: dict[str, Any]) -> float:
    io = record.get("io", {})
    if not isinstance(io, dict):
        return 0.0
    return max(0.0, float(io.get("read_bytes_per_second", 0.0))) + max(
        0.0, float(io.get("write_bytes_per_second", 0.0))
    )


def analyze_history(
    records: list[dict[str, Any]] | None,
    *,
    minimum_trend_samples: int = ANALYTICS_MIN_TREND_SAMPLES,
) -> dict[str, Any]:
    """Aggregate retained snapshots into disk, I/O, and detection trends."""

    snapshots = [item for item in (records or []) if isinstance(item, dict)]
    if not snapshots:
        return {
            "status": "NO_DATA",
            "record_count": 0,
            "first_timestamp": None,
            "last_timestamp": None,
            "duration_seconds": 0.0,
            "disks": [],
            "system_io": {},
            "detections": {},
        }

    times = [_timestamp(item.get("timestamp")) for item in snapshots]
    valid_times = [item for item in times if item is not None]
    duration = (
        max(0.0, (valid_times[-1] - valid_times[0]).total_seconds())
        if len(valid_times) >= 2
        else 0.0
    )

    disk_points: dict[str, list[tuple[datetime | None, float]]] = {}
    for record, stamp in zip(snapshots, times):
        disks = record.get("disks", [])
        if not isinstance(disks, list):
            continue
        for disk in disks:
            if not isinstance(disk, dict):
                continue
            path = str(disk.get("path") or "<unknown>")
            disk_points.setdefault(path, []).append(
                (stamp, max(0.0, float(disk.get("usage_percent", 0.0))))
            )

    disk_reports: list[dict[str, Any]] = []
    for path, points in sorted(disk_points.items()):
        values = [value for _, value in points]
        trend = _trend(points, minimum_samples=minimum_trend_samples)
        disk_reports.append(
            {
                "path": path,
                "sample_count": len(values),
                "average_usage_percent": round(mean(values), 2),
                "minimum_usage_percent": round(min(values), 2),
                "maximum_usage_percent": round(max(values), 2),
                "latest_usage_percent": round(values[-1], 2),
                "change_percentage_points": round(values[-1] - values[0], 2),
                "trend": trend,
            }
        )
    disk_reports.sort(
        key=lambda item: (
            item["maximum_usage_percent"],
            item["latest_usage_percent"],
            item["path"],
        ),
        reverse=True,
    )

    totals = [_io_total(record) for record in snapshots]
    read_rates = [
        max(0.0, float(record.get("io", {}).get("read_bytes_per_second", 0.0)))
        for record in snapshots
    ]
    write_rates = [
        max(0.0, float(record.get("io", {}).get("write_bytes_per_second", 0.0)))
        for record in snapshots
    ]
    io_points = list(zip(times, totals))
    peak_index = max(range(len(totals)), key=totals.__getitem__) if totals else 0

    detections = {
        "bottleneck_samples": sum(
            isinstance(item.get("root_cause"), dict)
            and item["root_cause"].get("status") == "BOTTLENECK_DETECTED"
            for item in snapshots
        ),
        "anomaly_samples": sum(
            isinstance(item.get("process_behavior"), dict)
            and int(item["process_behavior"].get("anomaly_count", 0) or 0) > 0
            for item in snapshots
        ),
        "runaway_samples": sum(
            isinstance(item.get("process_behavior"), dict)
            and int(item["process_behavior"].get("runaway_count", 0) or 0) > 0
            for item in snapshots
        ),
        "recommendation_samples": sum(
            isinstance(item.get("recommendations"), dict)
            and int(item["recommendations"].get("recommendation_count", 0) or 0) > 0
            for item in snapshots
        ),
        "alert_emission_samples": sum(
            isinstance(item.get("alerts"), dict)
            and int(item["alerts"].get("emitted_count", 0) or 0) > 0
            for item in snapshots
        ),
    }

    return {
        "status": "OK",
        "record_count": len(snapshots),
        "first_timestamp": snapshots[0].get("timestamp"),
        "last_timestamp": snapshots[-1].get("timestamp"),
        "duration_seconds": round(duration, 3),
        "disks": disk_reports,
        "system_io": {
            "average_total_bytes_per_second": round(mean(totals), 2),
            "median_total_bytes_per_second": round(median(totals), 2),
            "p95_total_bytes_per_second": round(_percentile(totals, 0.95), 2),
            "maximum_total_bytes_per_second": round(max(totals), 2),
            "average_read_bytes_per_second": round(mean(read_rates), 2),
            "average_write_bytes_per_second": round(mean(write_rates), 2),
            "peak_timestamp": snapshots[peak_index].get("timestamp"),
            "trend": _trend(io_points, minimum_samples=minimum_trend_samples),
        },
        "detections": detections,
    }
