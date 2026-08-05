"""Structured JSON Lines logging for monitoring data."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import LOG_FILE


class MonitoringLogger:
    """Append timestamped monitoring records to a JSON Lines file."""

    def __init__(self, log_file: str | Path = LOG_FILE) -> None:
        self.log_file = Path(log_file)

    def _append(self, record: dict[str, Any]) -> None:
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        with self.log_file.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            file.write("\n")

    def log_snapshot(self, snapshot: dict[str, Any]) -> None:
        self._append({"record_type": "metrics", **snapshot})

    def log_event(self, message: str, level: str = "INFO") -> None:
        self._append(
            {
                "record_type": "event",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": level.upper(),
                "message": message,
            }
        )


def log_event(message: str, log_file: str | Path = LOG_FILE) -> None:
    """Compatibility function for event logging."""

    MonitoringLogger(log_file).log_event(message)


def log_metrics(snapshot: dict[str, Any], log_file: str | Path = LOG_FILE) -> None:
    """Write one structured metrics snapshot."""

    MonitoringLogger(log_file).log_snapshot(snapshot)
