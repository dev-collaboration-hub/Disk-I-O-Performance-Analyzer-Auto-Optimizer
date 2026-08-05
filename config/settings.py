"""Runtime configuration for the disk monitoring application."""

REFRESH_INTERVAL_SECONDS = 2.0
IO_SAMPLE_INTERVAL_SECONDS = 1.0
LOG_FILE = "logs/disk_monitor.jsonl"
WARNING_DISK_USAGE_PERCENT = 80.0
CRITICAL_DISK_USAGE_PERCENT = 95.0
SHOW_CONSOLE_OUTPUT = True

# M2 process-level monitoring defaults.
TOP_PROCESS_LIMIT = 5
MINIMUM_PROCESS_IO_BYTES = 1

# Backward-compatible name used by earlier versions.
REFRESH_INTERVAL = REFRESH_INTERVAL_SECONDS
