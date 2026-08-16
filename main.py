"""Command-line entry point for M1-M6 disk monitoring and analysis."""

from __future__ import annotations

import argparse

from config.settings import (
    EVENT_RETENTION_RECORDS,
    EVENT_TIMELINE_FILE,
    HISTORY_FILE,
    HISTORY_RETENTION_RECORDS,
    IO_SAMPLE_INTERVAL_SECONDS,
    MINIMUM_PROCESS_IO_BYTES,
    REFRESH_INTERVAL_SECONDS,
    SPIKE_IO_MIN_BYTES_PER_SECOND,
    SPIKE_IO_MULTIPLIER,
    SPIKE_USAGE_DELTA_PERCENT,
    TOP_PROCESS_LIMIT,
)
from reporting.cli_dashboard import run_dashboard


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Monitor disk capacity and system/process I/O, retain metrics "
            "history, detect spikes, explain likely bottlenecks, analyze "
            "process behavior, and persist M6 recommendations."
        )
    )
    parser.add_argument(
        "--path",
        action="append",
        dest="paths",
        help="Disk or mount path to monitor. Repeat for multiple paths.",
    )
    parser.add_argument(
        "--refresh-interval",
        type=float,
        default=REFRESH_INTERVAL_SECONDS,
    )
    parser.add_argument(
        "--sample-interval",
        type=float,
        default=IO_SAMPLE_INTERVAL_SECONDS,
    )
    parser.add_argument("--process-limit", type=int, default=TOP_PROCESS_LIMIT)
    parser.add_argument(
        "--minimum-process-io-bytes",
        type=int,
        default=MINIMUM_PROCESS_IO_BYTES,
    )
    parser.add_argument("--hide-processes", action="store_true")
    parser.add_argument("--history-file", default=HISTORY_FILE)
    parser.add_argument("--event-file", default=EVENT_TIMELINE_FILE)
    parser.add_argument(
        "--history-retention",
        type=int,
        default=HISTORY_RETENTION_RECORDS,
    )
    parser.add_argument(
        "--event-retention",
        type=int,
        default=EVENT_RETENTION_RECORDS,
    )
    parser.add_argument("--no-history", action="store_true")
    parser.add_argument(
        "--spike-usage-delta",
        type=float,
        default=SPIKE_USAGE_DELTA_PERCENT,
    )
    parser.add_argument(
        "--spike-io-multiplier",
        type=float,
        default=SPIKE_IO_MULTIPLIER,
    )
    parser.add_argument(
        "--spike-io-minimum-rate",
        type=float,
        default=SPIKE_IO_MIN_BYTES_PER_SECOND,
    )
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--no-clear", action="store_true")
    parser.add_argument("--no-log", action="store_true")
    parser.add_argument("--log-file")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    run_dashboard(
        paths=args.paths,
        refresh_interval=args.refresh_interval,
        io_sample_interval=args.sample_interval,
        process_limit=args.process_limit,
        minimum_process_io_bytes=args.minimum_process_io_bytes,
        include_processes=not args.hide_processes,
        log_file=args.log_file,
        enable_logging=not args.no_log,
        history_file=args.history_file,
        event_file=args.event_file,
        enable_history=not args.no_history,
        history_retention=args.history_retention,
        event_retention=args.event_retention,
        spike_usage_delta=args.spike_usage_delta,
        spike_io_multiplier=args.spike_io_multiplier,
        spike_io_minimum_rate=args.spike_io_minimum_rate,
        clear_between_updates=not args.no_clear,
        once=args.once,
    )


if __name__ == "__main__":
    main()
