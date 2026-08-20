"""Scratch implementation core contracts."""

from .collectors import (
    CollectorBundle,
    CollectorError,
    CollectorErrorCode,
    DiskCapacityCollector,
    DiskDiscoveryCollector,
    DiskIOCollector,
    PlatformKind,
    ProcessIOCollector,
    detect_platform,
)
from .models import (
    Diagnosis,
    DiskDevice,
    DiskSample,
    Event,
    Evidence,
    OptimizationAction,
    ProcessIO,
    ProcessIdentity,
    Recommendation,
    RiskLevel,
    Severity,
)

__all__ = [
    "CollectorBundle",
    "CollectorError",
    "CollectorErrorCode",
    "Diagnosis",
    "DiskCapacityCollector",
    "DiskDevice",
    "DiskDiscoveryCollector",
    "DiskIOCollector",
    "DiskSample",
    "Event",
    "Evidence",
    "OptimizationAction",
    "PlatformKind",
    "ProcessIO",
    "ProcessIOCollector",
    "ProcessIdentity",
    "Recommendation",
    "RiskLevel",
    "Severity",
    "detect_platform",
]
