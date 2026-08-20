# S0 Task 2 — Platform Boundary & Collector Interfaces

## Status

**Complete**

## Goal

Define a narrow boundary between platform-native telemetry code and the scratch core so Windows/Linux implementations can change internally without leaking OS-specific structures into reasoning, persistence, recommendations, or optimization.

## Delivered

- `core/collectors.py`
- collector exports in `core/__init__.py`
- `tests/test_s0_collectors.py`

## Platform contract

Supported platform identities are normalized to:

- `PlatformKind.WINDOWS`
- `PlatformKind.LINUX`

`detect_platform()` converts the operating-system name into this closed contract and raises an explicit `CollectorError` for unsupported systems.

## Collector interfaces

The scratch core now defines four independent collector protocols:

1. `DiskDiscoveryCollector` — discovers normalized `DiskDevice` records.
2. `DiskCapacityCollector` — collects total/used/free capacity into `DiskSample`.
3. `DiskIOCollector` — collects cumulative device read/write counters into `DiskSample`.
4. `ProcessIOCollector` — collects normalized `ProcessIO` records.

Collectors expose only core domain models. Platform-native objects, third-party objects, command output, registry structures, `/proc` parsing details, and similar implementation details must stay behind the collector boundary.

## Error contract

`CollectorErrorCode` provides explicit failure classes:

- `UNSUPPORTED`
- `PERMISSION_DENIED`
- `UNAVAILABLE`
- `INVALID_DATA`
- `IO_ERROR`

This prevents later layers from inferring failure meaning from arbitrary exception text.

## Collector bundle

`CollectorBundle` groups collectors for one platform and rejects Windows/Linux collector mixing. Optional collectors allow S1–S3 to be implemented incrementally while preserving one stable boundary.

## Dependency boundary

This task uses only the Python standard library and `core.models`. It imports no `psutil` code and no legacy monitoring, analysis, reporting, or optimizer implementation.

## Tests

Run:

```bash
python -m unittest tests.test_s0_collectors -v
```

The tests cover supported/unsupported platform detection, protocol conformance, staged collector bundles, cross-platform mixing rejection, and structured collector errors.

## Capability unlocked

The scratch rebuild can now add Windows and Linux native collectors behind stable interfaces. Later S1–S3 code can focus on obtaining trustworthy OS telemetry while the rest of the system remains platform-independent.

## Next S0 task

**Task 3 — deterministic configuration and core error model.**
