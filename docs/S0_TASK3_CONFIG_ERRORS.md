# S0 Task 3 — Deterministic Configuration & Core Error Model

## Status

**Complete**

## Goal

Give the scratch implementation one explicit configuration contract and one machine-readable error boundary before platform implementations, persistence, reasoning, or optimization are added.

## Delivered

- `core/configuration.py`
- `core/errors.py`
- centralized collector errors in `core/errors.py`
- updated exports in `core/__init__.py`
- `tests/test_s0_config_errors.py`

## Deterministic configuration

`RuntimeConfig` is immutable and uses explicit defaults for the foundational runtime policy:

- schema version
- sampling interval
- refresh interval
- collector timeout
- history retention
- automatic-action enablement

`automatic_actions_enabled` is `False` by default.

Configuration rules:

- no implicit environment-variable lookup
- no fallback to the legacy `config/` package
- unknown keys are rejected
- invalid values are rejected instead of silently coerced
- JSON configuration must have an object at its root
- the same validated values produce the same SHA-256 configuration fingerprint

This makes configuration identity inspectable and reproducible.

## Core error model

`CoreError` carries:

- a machine-readable error code
- the operation that failed
- a human-readable detail
- explicit retryability
- deterministic sorted context

Core-level codes currently include:

- `INVALID_CONFIG`
- `CONTRACT_VIOLATION`
- `INTERNAL_ERROR`

Collector-specific codes remain:

- `UNSUPPORTED`
- `PERMISSION_DENIED`
- `UNAVAILABLE`
- `INVALID_DATA`
- `IO_ERROR`

`CollectorError` now derives from `CoreError` while preserving the Task 2 import contract through `core.collectors`.

## Dependency boundary

Task 3 is Python-standard-library only. It does not import `psutil` or the legacy monitoring/configuration implementation.

## Tests

Run:

```bash
python -m unittest tests.test_s0_config_errors -v
python -m unittest tests.test_s0_collectors -v
python -m unittest tests.test_s0_models -v
```

The connected GitHub environment can write and inspect source but does not execute the repository test suite, so runtime confirmation must come from CI or a checked-out repository.

## Capability unlocked

The scratch rebuild now has reproducible runtime policy and structured failure semantics. Later code can receive explicit configuration and react to typed failures without reading legacy globals or parsing arbitrary exception messages.

## Next S0 task

**Task 4 — test fixtures + capability/evidence format.**
