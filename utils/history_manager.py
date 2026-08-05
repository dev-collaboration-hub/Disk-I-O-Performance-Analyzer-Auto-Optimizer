"""Append-only, crash-tolerant storage for historical monitoring records."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

from config.settings import HISTORY_FILE, HISTORY_RETENTION_RECORDS

_FILE_LOCKS: dict[str, threading.RLock] = {}
_FILE_LOCKS_GUARD = threading.Lock()


def _lock_for(path: Path) -> threading.RLock:
    key = str(path.resolve())
    with _FILE_LOCKS_GUARD:
        return _FILE_LOCKS.setdefault(key, threading.RLock())


class JsonlStore:
    """Store dictionaries as JSON Lines with bounded retention.

    Readers ignore malformed trailing/partial lines so an interrupted write does
    not make the rest of the history unreadable. Legacy JSON-array files are
    accepted during reads to support the repository's original M3 prototype.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        max_records: int | None = None,
        durable: bool = False,
    ) -> None:
        if max_records is not None and max_records < 0:
            raise ValueError("max_records must be non-negative or None")
        self.path = Path(path)
        self.max_records = max_records
        self.durable = durable
        self._lock = _lock_for(self.path)
        self._appends_since_prune = 0
        self._prune_interval = (
            1 if max_records is not None and max_records < 1_000 else 100
        )

    def _read_all_unlocked(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []

        text = self.path.read_text(encoding="utf-8")
        stripped = text.lstrip()
        if not stripped:
            return []

        if stripped.startswith("["):
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                return []
            if not isinstance(payload, list):
                return []
            return [item for item in payload if isinstance(item, dict)]

        records: list[dict[str, Any]] = []
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                records.append(item)
        return records

    def load(
        self,
        *,
        limit: int | None = None,
        newest_first: bool = False,
    ) -> list[dict[str, Any]]:
        """Load records; ``limit`` selects the most recent records."""

        if limit is not None and limit < 0:
            raise ValueError("limit must be non-negative or None")
        with self._lock:
            records = self._read_all_unlocked()
        if limit is not None:
            records = records[-limit:] if limit else []
        if newest_first:
            records.reverse()
        return records

    def append(self, record: dict[str, Any]) -> None:
        if not isinstance(record, dict):
            raise TypeError("record must be a dictionary")

        encoded = json.dumps(
            record,
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
            separators=(",", ":"),
        )
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8", newline="\n") as file:
                file.write(encoded)
                file.write("\n")
                file.flush()
                if self.durable:
                    os.fsync(file.fileno())
            self._appends_since_prune += 1
            if self._appends_since_prune >= self._prune_interval:
                self._prune_unlocked()
                self._appends_since_prune = 0

    def append_many(self, records: list[dict[str, Any]]) -> None:
        for record in records:
            self.append(record)

    def _prune_unlocked(self) -> None:
        if self.max_records is None:
            return
        records = self._read_all_unlocked()
        if len(records) <= self.max_records:
            return
        retained = records[-self.max_records :] if self.max_records else []
        self._write_all_unlocked(retained)

    def _write_all_unlocked(self, records: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f".{self.path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as file:
            for record in records:
                file.write(
                    json.dumps(
                        record,
                        ensure_ascii=False,
                        sort_keys=True,
                        allow_nan=False,
                        separators=(",", ":"),
                    )
                )
                file.write("\n")
            file.flush()
            if self.durable:
                os.fsync(file.fileno())
        os.replace(temporary, self.path)

    def clear(self) -> None:
        with self._lock:
            self._write_all_unlocked([])

    def count(self) -> int:
        with self._lock:
            return len(self._read_all_unlocked())


class HistoryManager:
    """Persist and query monitoring snapshots."""

    def __init__(
        self,
        history_file: str | Path = HISTORY_FILE,
        *,
        max_records: int | None = HISTORY_RETENTION_RECORDS,
        durable: bool = False,
    ) -> None:
        self.history_file = Path(history_file)
        self.store = JsonlStore(
            self.history_file,
            max_records=max_records,
            durable=durable,
        )
        self._latest_cache: dict[str, Any] | None = None
        self._count_cache: int | None = None

    def load_history(
        self,
        limit: int | None = None,
        *,
        newest_first: bool = False,
    ) -> list[dict[str, Any]]:
        return self.store.load(limit=limit, newest_first=newest_first)

    def save_snapshot(self, snapshot: dict[str, Any]) -> None:
        previous_count = self.count()
        self.store.append(snapshot)
        if self.store.max_records == 0:
            self._latest_cache = None
            self._count_cache = 0
        else:
            self._latest_cache = snapshot
            self._count_cache = previous_count + 1

    def latest_snapshot(self) -> dict[str, Any] | None:
        if self._latest_cache is None:
            records = self.load_history(limit=1)
            self._latest_cache = records[0] if records else None
        return self._latest_cache

    def clear_history(self) -> None:
        self.store.clear()
        self._latest_cache = None
        self._count_cache = 0

    def count(self) -> int:
        if self._count_cache is None:
            self._count_cache = self.store.count()
        return self._count_cache

    def summarize(self) -> dict[str, Any]:
        records = self.load_history()
        usages = [
            float(disk.get("usage_percent", 0.0))
            for record in records
            for disk in record.get("disks", [])
            if isinstance(disk, dict)
        ]
        throughput = [
            float(record.get("io", {}).get("read_bytes_per_second", 0.0))
            + float(record.get("io", {}).get("write_bytes_per_second", 0.0))
            for record in records
        ]
        return {
            "record_count": len(records),
            "first_timestamp": records[0].get("timestamp") if records else None,
            "last_timestamp": records[-1].get("timestamp") if records else None,
            "maximum_disk_usage_percent": max(usages, default=0.0),
            "maximum_io_bytes_per_second": max(throughput, default=0.0),
        }
