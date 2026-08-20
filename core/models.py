"""Scratch-first domain contracts for the rebuilt disk I/O analyzer.

This module intentionally depends only on the Python standard library.  It is
shared by later measurement, reasoning, recommendation, and optimization
layers so those layers exchange normalized data instead of importing legacy
implementation details.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TypeAlias


MetricValue: TypeAlias = str | int | float | bool | None


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def _require_text(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} must be non-empty")


def _require_aware_timestamp(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _require_non_negative(value: int | None, field_name: str) -> None:
    if value is not None and value < 0:
        raise ValueError(f"{field_name} must be non-negative")


@dataclass(frozen=True, slots=True)
class DiskDevice:
    """Normalized identity and mount metadata for one storage device."""

    device_id: str
    platform: str
    name: str
    mount_points: tuple[str, ...] = ()
    fs_type: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.device_id, "device_id")
        _require_text(self.platform, "platform")
        _require_text(self.name, "name")
        for mount_point in self.mount_points:
            _require_text(mount_point, "mount_point")


@dataclass(frozen=True, slots=True)
class DiskSample:
    """Timestamped normalized disk counters and capacity measurements."""

    device_id: str
    timestamp: datetime
    total_bytes: int | None = None
    used_bytes: int | None = None
    free_bytes: int | None = None
    read_bytes: int | None = None
    write_bytes: int | None = None
    read_ops: int | None = None
    write_ops: int | None = None

    def __post_init__(self) -> None:
        _require_text(self.device_id, "device_id")
        _require_aware_timestamp(self.timestamp, "timestamp")
        for field_name in (
            "total_bytes",
            "used_bytes",
            "free_bytes",
            "read_bytes",
            "write_bytes",
            "read_ops",
            "write_ops",
        ):
            _require_non_negative(getattr(self, field_name), field_name)

        if self.total_bytes is not None:
            if self.used_bytes is not None and self.used_bytes > self.total_bytes:
                raise ValueError("used_bytes cannot exceed total_bytes")
            if self.free_bytes is not None and self.free_bytes > self.total_bytes:
                raise ValueError("free_bytes cannot exceed total_bytes")


@dataclass(frozen=True, slots=True)
class ProcessIdentity:
    """Stable process identity. PID alone is deliberately insufficient."""

    pid: int
    started_at_ns: int
    name: str
    executable: str | None = None

    def __post_init__(self) -> None:
        if self.pid < 0:
            raise ValueError("pid must be non-negative")
        if self.started_at_ns < 0:
            raise ValueError("started_at_ns must be non-negative")
        _require_text(self.name, "name")


@dataclass(frozen=True, slots=True)
class ProcessIO:
    """Timestamped cumulative I/O counters for one stable process instance."""

    process: ProcessIdentity
    timestamp: datetime
    read_bytes: int | None = None
    write_bytes: int | None = None
    read_ops: int | None = None
    write_ops: int | None = None

    def __post_init__(self) -> None:
        _require_aware_timestamp(self.timestamp, "timestamp")
        for field_name in ("read_bytes", "write_bytes", "read_ops", "write_ops"):
            _require_non_negative(getattr(self, field_name), field_name)


@dataclass(frozen=True, slots=True)
class Evidence:
    """One atomic, inspectable fact supporting an event or decision."""

    key: str
    value: MetricValue
    source: str
    unit: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.key, "key")
        _require_text(self.source, "source")


@dataclass(frozen=True, slots=True)
class Event:
    event_type: str
    timestamp: datetime
    severity: Severity
    message: str
    evidence: tuple[Evidence, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.event_type, "event_type")
        _require_text(self.message, "message")
        _require_aware_timestamp(self.timestamp, "timestamp")


@dataclass(frozen=True, slots=True)
class Diagnosis:
    code: str
    timestamp: datetime
    summary: str
    confidence: float
    evidence: tuple[Evidence, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.code, "code")
        _require_text(self.summary, "summary")
        _require_aware_timestamp(self.timestamp, "timestamp")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True)
class Recommendation:
    code: str
    timestamp: datetime
    summary: str
    rationale: str
    risk: RiskLevel
    diagnosis_code: str | None = None
    evidence: tuple[Evidence, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.code, "code")
        _require_text(self.summary, "summary")
        _require_text(self.rationale, "rationale")
        _require_aware_timestamp(self.timestamp, "timestamp")
        if self.diagnosis_code is not None:
            _require_text(self.diagnosis_code, "diagnosis_code")


@dataclass(frozen=True, slots=True)
class OptimizationAction:
    action_type: str
    timestamp: datetime
    target: str
    rationale: str
    reversible: bool
    requires_confirmation: bool = True
    parameters: tuple[tuple[str, str], ...] = ()
    evidence: tuple[Evidence, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.action_type, "action_type")
        _require_text(self.target, "target")
        _require_text(self.rationale, "rationale")
        _require_aware_timestamp(self.timestamp, "timestamp")
        for key, _value in self.parameters:
            _require_text(key, "parameter key")
