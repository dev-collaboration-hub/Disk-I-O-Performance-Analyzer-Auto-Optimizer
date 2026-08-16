"""Crash-tolerant JSONL persistence for M8 alert state and history."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config.settings import ALERT_RETENTION_RECORDS


class AlertStore:
    def __init__(self, alert_file: str | Path, *, max_records: int = ALERT_RETENTION_RECORDS) -> None:
        if max_records < 0:
            raise ValueError("max_records must be non-negative")
        self.alert_file = Path(alert_file)
        self.max_records = max_records

    def _load_records(self) -> list[dict[str, Any]]:
        if not self.alert_file.exists():
            return []
        records: list[dict[str, Any]] = []
        try:
            with self.alert_file.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        item = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(item, dict):
                        records.append(item)
        except OSError:
            return []
        return records

    def load(self, *, limit: int | None = None) -> list[dict[str, Any]]:
        records = self._load_records()
        if limit is None:
            return records
        if limit < 0:
            raise ValueError("limit must be non-negative")
        if limit == 0:
            return []
        return records[-limit:]

    def append(self, event: dict[str, Any]) -> None:
        if not isinstance(event, dict):
            raise TypeError("event must be a dictionary")
        self.alert_file.parent.mkdir(parents=True, exist_ok=True)
        with self.alert_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
        self._trim()

    def _trim(self) -> None:
        if self.max_records <= 0:
            return
        records = self._load_records()
        if len(records) <= self.max_records:
            return
        retained = records[-self.max_records:]
        temp = self.alert_file.with_suffix(self.alert_file.suffix + ".tmp")
        with temp.open("w", encoding="utf-8") as handle:
            for item in retained:
                handle.write(json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n")
        temp.replace(self.alert_file)

    def latest_by_key(self) -> dict[str, dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for event in self._load_records():
            key = event.get("alert_key")
            if key:
                latest[str(key)] = event
        return latest

    def active_alerts(self) -> dict[str, dict[str, Any]]:
        return {
            key: event
            for key, event in self.latest_by_key().items()
            if bool(event.get("active", False))
        }
