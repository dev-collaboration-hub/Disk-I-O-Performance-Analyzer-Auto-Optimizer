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

# M3 history, timeline, and spike-detection defaults.
HISTORY_FILE = "logs/metrics_history.jsonl"
EVENT_TIMELINE_FILE = "logs/event_timeline.jsonl"
HISTORY_RETENTION_RECORDS = 10_000
EVENT_RETENTION_RECORDS = 5_000
SPIKE_USAGE_DELTA_PERCENT = 20.0
SPIKE_IO_MULTIPLIER = 3.0
SPIKE_IO_MIN_BYTES_PER_SECOND = 1_048_576.0

# M4 root-cause detection defaults.
ROOT_CAUSE_PROCESS_SHARE_PERCENT = 50.0
ROOT_CAUSE_MIN_PROCESS_RATE_BYTES_PER_SECOND = 1.0
ROOT_CAUSE_SUSTAINED_SAMPLES = 3

# Backward-compatible name used by earlier versions.
REFRESH_INTERVAL = REFRESH_INTERVAL_SECONDS
