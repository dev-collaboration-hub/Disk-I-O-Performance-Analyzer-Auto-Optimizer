# Disk I/O Performance Analyzer & Auto Optimizer

A cross-platform disk diagnostics and optimization project.

## Project status

**Scratch rebuild in progress.**

The previous v1.0.0 implementation cycle (M1–M10) is complete and is no longer the active development roadmap. The project is now being rebuilt from first principles so that the core telemetry, reasoning, recommendations, and optimization pipeline are designed explicitly instead of extending the legacy architecture.

The previous release remains available through Git history. Active development follows the new scratch roadmap:

- [`docs/SCRATCH_REBUILD_ROADMAP.md`](docs/SCRATCH_REBUILD_ROADMAP.md)
- [`docs/LEGACY_V1_HISTORY.md`](docs/LEGACY_V1_HISTORY.md)

## Active roadmap

- **S0 — Scratch Architecture Foundation** ← current
- **S1 — Native Disk Discovery & Capacity**
- **S2 — Native Disk I/O Telemetry**
- **S3 — Process I/O Attribution**
- **S4 — Historical Evidence Engine**
- **S5 — Bottleneck Reasoning Engine**
- **S6 — Process Behavior Analysis**
- **S7 — Recommendation Engine**
- **S8 — Safety-Gated Optimizer**
- **S9 — Alerts & Predictive Signals**
- **S10 — Analytics & Operator UI**
- **S11 — Production Hardening & Release**

## Scratch-first development rules

- Do not extend the v1.0.0 architecture by default.
- Define contracts before implementations.
- Prefer direct operating-system telemetry in the core measurement path.
- Keep Windows/Linux collectors behind narrow platform interfaces.
- Separate measurement, interpretation, recommendation, and action.
- Require evidence for diagnosis and recommendations.
- Keep automated actions narrowly scoped, safety-gated, and reversible where possible.
- Every milestone must include tests and a capability-unlock note.

## Current implementation boundary

Existing v1.0.0 source remains in the repository temporarily as legacy reference code while the scratch implementation begins. New work must use the S0–S11 roadmap and must not claim legacy modules as completion evidence for the new cycle.

## Technology direction

- Python 3.10+
- standard library where practical
- platform-native OS interfaces for core telemetry
- minimal external dependencies
- cross-platform architecture

## License

License to be determined.
