"""Standalone M2 process-level disk I/O report."""

from __future__ import annotations

import argparse
from typing import Any

from config.settings import (
    IO_SAMPLE_INTERVAL_SECONDS,
    MINIMUM_PROCESS_IO_BYTES,
    TOP_PROCESS_LIMIT,
)
from monitoring.top_disk_consumers import get_top_disk_consumers
from utils.formatter import format_size


def get_risk_level(percentage: float) -> str:
    """Classify a process by its share of active process disk I/O."""

    if percentage >= 50:
        return "DOMINANT"
    if percentage >= 25:
        return "HIGH"
    if percentage >= 10:
        return "MEDIUM"
    return "LOW"


def generate_process_report(
    limit: int = TOP_PROCESS_LIMIT,
    *,
    sample_interval: float = IO_SAMPLE_INTERVAL_SECONDS,
    minimum_io_bytes: int = MINIMUM_PROCESS_IO_BYTES,
) -> list[dict[str, Any]]:
    """Sample and return ranked process-level disk I/O records."""

    report: list[dict[str, Any]] = []
    for process in get_top_disk_consumers(
        limit,
        sample_interval=sample_interval,
        minimum_io_bytes=minimum_io_bytes,
    ):
        report.append(
            {
                **process,
                "risk_level": get_risk_level(process["io_share_percent"]),
            }
        )
    return report


def render_process_report(report: list[dict[str, Any]]) -> str:
    """Render ranked process activity as a compact table."""

    lines = [
        "=" * 94,
        "M2 PROCESS-LEVEL DISK I/O REPORT",
        "=" * 94,
        f"{'PID':>7}  {'PROCESS':<28} {'READ/s':>13} {'WRITE/s':>13} "
        f"{'TOTAL/s':>13} {'SHARE':>8} {'LEVEL':>9}",
        "-" * 94,
    ]

    if not report:
        lines.append("No process disk I/O activity was observed during the sample.")
    else:
        for item in report:
            lines.append(
                f"{item['pid']:>7}  {item['name'][:28]:<28} "
                f"{format_size(item['read_bytes_per_second']):>13} "
                f"{format_size(item['write_bytes_per_second']):>13} "
                f"{format_size(item['total_bytes_per_second']):>13} "
                f"{item['io_share_percent']:>7.2f}% {item['risk_level']:>9}"
            )

    lines.append("=" * 94)
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Show the processes currently generating the most disk I/O."
    )
    parser.add_argument("--limit", type=int, default=TOP_PROCESS_LIMIT)
    parser.add_argument(
        "--sample-interval",
        type=float,
        default=IO_SAMPLE_INTERVAL_SECONDS,
    )
    parser.add_argument(
        "--minimum-io-bytes",
        type=int,
        default=MINIMUM_PROCESS_IO_BYTES,
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    report = generate_process_report(
        args.limit,
        sample_interval=args.sample_interval,
        minimum_io_bytes=args.minimum_io_bytes,
    )
    print(render_process_report(report))


if __name__ == "__main__":
    main()
