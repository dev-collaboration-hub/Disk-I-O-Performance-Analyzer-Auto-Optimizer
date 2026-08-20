# S0 Task 1 — Core Domain Model

## Status

**Complete**

## Goal

Define the normalized data contracts that the scratch implementation will use across measurement, reasoning, recommendation, and action layers without depending on the legacy v1.0.0 architecture.

## Delivered

- `core/models.py`
- `core/__init__.py`
- `tests/test_s0_models.py`

### Contracts

- `DiskDevice`
- `DiskSample`
- `ProcessIdentity`
- `ProcessIO`
- `Evidence`
- `Event`
- `Diagnosis`
- `Recommendation`
- `OptimizationAction`
- `Severity`
- `RiskLevel`

## Invariants

- models are immutable
- timestamps must be timezone-aware
- counters cannot be negative
- capacity values cannot exceed total capacity
- process identity includes process start time so PID reuse does not silently reuse identity
- diagnosis confidence is constrained to `0.0..1.0`
- evidence is explicit and source-labelled
- optimization actions carry explicit reversibility and confirmation metadata

## Dependency boundary

The new core domain layer uses only the Python standard library. It imports no `psutil` modules and no legacy monitoring, analysis, reporting, or optimizer modules.

## Tests

`tests/test_s0_models.py` covers the principal invariants and safety metadata.

Run from the repository root:

```bash
python -m unittest tests.test_s0_models -v
```

The connected GitHub environment can commit and inspect repository source but does not execute repository tests. Test execution must therefore be confirmed by CI or a checked-out runtime environment.

## Capability unlocked

The scratch rebuild now has a shared vocabulary for storage devices, telemetry samples, stable process identities, evidence, diagnoses, recommendations, and optimization actions. Later S0 tasks can build platform interfaces and reasoning boundaries against these contracts instead of inheriting the legacy architecture.
