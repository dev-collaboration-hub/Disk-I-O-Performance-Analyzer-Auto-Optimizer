"""Command-line entry point for the M2 disk and process monitoring system."""

from __future__ import annotations

import argparse

from config.settings import (
    IO_SAMPLE_INTERVAL_SECONDS,
    MINIMUM_PROCESS_IO_BYTES,
    REFRESH_INTERVAL_SECONDS,
    TOP_PROCESS_LIMIT,
)
from reporting.cli_dashboard import run_dashboard


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Monitor disk capacity, system-wide I/O, and current process-level "
            "disk consumers."
        ),
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
        help="Seconds between dashboard refreshes.",
    )
    parser.add_argument(
        "--sample-interval",
        type=float,
        default=IO_SAMPLE_INTERVAL_SECONDS,
        help="Seconds used to calculate system and process I/O rates.",
    )
    parser.add_argument(
        "--process-limit",
        type=int,
        default=TOP_PROCESS_LIMIT,
        help="Maximum number of active disk-consuming processes to display.",
    )
    parser.add_argument(
        "--minimum-process-io-bytes",
        type=int,
        default=MINIMUM_PROCESS_IO_BYTES,
        help="Minimum bytes transferred in a sample for a process to be shown.",
    )
    parser.add_argument(
        "--hide-processes",
        action="store_true",
        help="Disable process-level sampling and show only M1 disk metrics.",
    )
    parser.add_argument("--once", action="store_true", help="Collect and print one snapshot.")
    parser.add_argument("--no-clear", action="store_true", help="Do not clear the terminal.")
    parser.add_argument("--no-log", action="store_true", help="Disable JSONL metric logging.")
    parser.add_argument("--log-file", help="Override the default JSONL log path.")
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
        clear_between_updates=not args.no_clear,
        once=args.once,
    )


if __name__ == "__main__":
    main()
