"""Platform boundary and collector contracts for the scratch rebuild.

Collectors are deliberately narrow: platform-specific code may use native OS
APIs internally, but it must return normalized objects from ``core.models``.
Nothing in this module imports the legacy monitoring stack or third-party
telemetry libraries.
"""

from __future__ import annotations

import platform as _platform
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol, runtime_checkable

from .models import DiskDevice, DiskSample, ProcessIO


class PlatformKind(str, Enum):
    WINDOWS = "windows"
    LINUX = "linux"


class CollectorErrorCode(str, Enum):
    UNSUPPORTED = "UNSUPPORTED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    UNAVAILABLE = "UNAVAILABLE"
    INVALID_DATA = "INVALID_DATA"
    IO_ERROR = "IO_ERROR"


class CollectorError(RuntimeError):
    """Explicit failure crossing a platform collector boundary."""

    def __init__(
        self,
        code: CollectorErrorCode,
        operation: str,
        message: str,
        *,
        platform: PlatformKind | None = None,
    ) -> None:
        if not operation or not operation.strip():
            raise ValueError("operation must be non-empty")
        if not message or not message.strip():
            raise ValueError("message must be non-empty")

        self.code = code
        self.operation = operation
        self.platform = platform
        self.detail = message
        super().__init__(f"{code.value}: {operation}: {message}")


def detect_platform(system_name: str | None = None) -> PlatformKind:
    """Resolve the current supported platform without leaking platform strings."""

    raw_name = system_name if system_name is not None else _platform.system()
    normalized = raw_name.strip().casefold()

    if normalized == "windows":
        return PlatformKind.WINDOWS
    if normalized == "linux":
        return PlatformKind.LINUX

    raise CollectorError(
        CollectorErrorCode.UNSUPPORTED,
        "detect_platform",
        f"unsupported operating system: {raw_name or '<empty>'}",
    )


@runtime_checkable
class DiskDiscoveryCollector(Protocol):
    """Discover storage devices and mounts visible to one operating system."""

    platform: PlatformKind

    def discover_devices(self) -> tuple[DiskDevice, ...]:
        """Return normalized, stable device records."""
        ...


@runtime_checkable
class DiskCapacityCollector(Protocol):
    """Collect capacity state for a previously discovered device."""

    platform: PlatformKind

    def collect_capacity(
        self,
        device: DiskDevice,
        *,
        timestamp: datetime,
    ) -> DiskSample:
        """Return a sample containing capacity fields for ``device``."""
        ...


@runtime_checkable
class DiskIOCollector(Protocol):
    """Collect cumulative device-level read/write counters."""

    platform: PlatformKind

    def collect_disk_io(
        self,
        device: DiskDevice,
        *,
        timestamp: datetime,
    ) -> DiskSample:
        """Return a sample containing cumulative disk-I/O counters."""
        ...


@runtime_checkable
class ProcessIOCollector(Protocol):
    """Collect cumulative I/O counters for accessible process instances."""

    platform: PlatformKind

    def collect_process_io(self, *, timestamp: datetime) -> tuple[ProcessIO, ...]:
        """Return normalized process-I/O records for one observation time."""
        ...


@dataclass(frozen=True, slots=True)
class CollectorBundle:
    """One platform's collector set.

    S0 allows later collectors to be absent while their milestones are not yet
    implemented, but every present collector must target the same platform.
    """

    platform: PlatformKind
    discovery: DiskDiscoveryCollector
    capacity: DiskCapacityCollector | None = None
    disk_io: DiskIOCollector | None = None
    process_io: ProcessIOCollector | None = None

    def __post_init__(self) -> None:
        collectors = (
            ("discovery", self.discovery),
            ("capacity", self.capacity),
            ("disk_io", self.disk_io),
            ("process_io", self.process_io),
        )
        for name, collector in collectors:
            if collector is None:
                continue
            collector_platform = getattr(collector, "platform", None)
            if collector_platform != self.platform:
                raise ValueError(
                    f"{name} collector platform {collector_platform!r} "
                    f"does not match bundle platform {self.platform.value!r}"
                )
