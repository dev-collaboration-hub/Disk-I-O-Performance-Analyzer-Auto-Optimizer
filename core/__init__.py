"""Scratch implementation core contracts."""

from .collectors import (
    CollectorBundle,
    DiskCapacityCollector,
    DiskDiscoveryCollector,
    DiskIOCollector,
    PlatformKind,
    ProcessIOCollector,
    detect_platform,
)
from .configuration import DEFAULT_CONFIG, RuntimeConfig, load_json_config
from .errors import (
    CollectorError,
    CollectorErrorCode,
    ConfigurationError,
    CoreError,
    CoreErrorCode,
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
    "ConfigurationError",
    "CoreError",
    "CoreErrorCode",
    "DEFAULT_CONFIG",
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
    "RuntimeConfig",
    "Severity",
    "detect_platform",
    "load_json_config",
]
