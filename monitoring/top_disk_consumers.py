"""Ranking helpers for current process-level disk I/O activity."""

from __future__ import annotations

from monitoring.process_io_monitor import ProcessIORates, sample_process_io_rates


class TopDiskConsumer(ProcessIORates):
    io_share_percent: float
    percentage: float


def rank_process_io(
    process_rates: list[ProcessIORates],
    *,
    limit: int = 10,
    minimum_io_bytes: int = 1,
) -> list[TopDiskConsumer]:
    """Rank processes by bytes transferred during the sample window."""

    if limit < 0:
        raise ValueError("limit must be non-negative")
    if minimum_io_bytes < 0:
        raise ValueError("minimum_io_bytes must be non-negative")
    if limit == 0:
        return []

    active = [
        item
        for item in process_rates
        if item["total_io_bytes_delta"] >= minimum_io_bytes
    ]
    active.sort(
        key=lambda item: (
            item["total_io_bytes_delta"],
            item["write_bytes_delta"],
            item["read_bytes_delta"],
            -item["pid"],
        ),
        reverse=True,
    )

    total_active_bytes = sum(item["total_io_bytes_delta"] for item in active)
    ranked: list[TopDiskConsumer] = []

    for item in active[:limit]:
        share = (
            (item["total_io_bytes_delta"] / total_active_bytes) * 100
            if total_active_bytes
            else 0.0
        )
        ranked.append(
            {
                **item,
                "io_share_percent": round(share, 2),
                "percentage": round(share, 2),
            }
        )

    return ranked


def get_top_disk_consumers(
    limit: int = 10,
    *,
    sample_interval: float = 1.0,
    minimum_io_bytes: int = 1,
) -> list[TopDiskConsumer]:
    """Sample process I/O and return the most active disk consumers."""

    rates = sample_process_io_rates(sample_interval)
    return rank_process_io(
        rates,
        limit=limit,
        minimum_io_bytes=minimum_io_bytes,
    )


if __name__ == "__main__":
    for process in get_top_disk_consumers():
        print(process)
