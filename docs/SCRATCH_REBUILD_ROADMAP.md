# Scratch Rebuild Roadmap

## Project Direction

This repository is entering a new implementation cycle: the Disk I/O Performance Analyzer & Auto Optimizer will be rebuilt from first principles.

The previous v1.0.0 milestone sequence is considered a completed legacy cycle. It is retained only as historical evidence and is no longer the active development roadmap.

## Scratch-first rules

- Do not treat the v1.0.0 implementation as the architecture to extend.
- Define contracts before implementations.
- Prefer direct operating-system telemetry over convenience abstractions in the core measurement path.
- Keep platform-specific collectors behind narrow interfaces.
- Separate measurement, interpretation, recommendation, and action.
- Every automated action must be safety-gated and reversible where possible.
- Each milestone must include tests, evidence, and a capability-unlock note.

## Active milestones

### S0 — Scratch Architecture Foundation

**Goal:** establish a clean first-principles architecture before adding disk logic.

Deliverables:
- domain model for devices, samples, processes, events, diagnoses, recommendations, and actions
- platform boundary and collector contracts
- deterministic configuration and error model
- test fixtures and capability/evidence format
- minimal CLI bootstrap

Capability unlocked: a stable skeleton in which later disk capabilities can be implemented without inheriting the legacy architecture.

### S1 — Native Disk Discovery & Capacity

**Goal:** discover storage devices/mounts and measure capacity using platform-native mechanisms.

Deliverables:
- Windows collector
- Linux collector
- normalized device/mount records
- total/used/free capacity metrics
- unsupported/permission error handling

Capability unlocked: the system can identify what storage exists and its capacity state without relying on the old monitoring stack.

### S2 — Native Disk I/O Telemetry

**Goal:** measure real disk read/write activity from OS counters.

Deliverables:
- cumulative read/write bytes and operation counters
- sampled throughput and IOPS
- counter reset/wrap handling
- timestamped samples
- collector validation tests

Capability unlocked: the system can quantify live disk activity.

### S3 — Process I/O Attribution

**Goal:** connect disk activity to processes where the operating system exposes sufficient evidence.

Deliverables:
- stable process identity model
- per-process read/write samples
- throughput ranking
- PID reuse/termination handling
- inaccessible-process handling

Capability unlocked: the system can identify which processes are contributing to I/O pressure.

### S4 — Historical Evidence Engine

**Goal:** retain trustworthy time-series evidence without coupling persistence to the live loop.

Deliverables:
- append-oriented history store
- retention policy
- event timeline
- baseline computation
- spike/change detection primitives

Capability unlocked: the system can compare current activity with prior behavior.

### S5 — Bottleneck Reasoning Engine

**Goal:** infer likely causes from collected evidence instead of only displaying metrics.

Deliverables:
- evidence graph/model
- hypotheses for capacity pressure, sustained throughput, burst activity, process-dominated load, and telemetry gaps
- confidence scoring
- competing-hypothesis handling
- explanation trace

Capability unlocked: the system can answer “what is happening and why?” with inspectable evidence.

### S6 — Process Behavior Analysis

**Goal:** identify abnormal or harmful I/O behavior over time.

Deliverables:
- behavioral baselines
- burst/sustained-pattern classification
- repeated offender tracking
- anomaly evidence records
- false-positive controls

Capability unlocked: the system can distinguish ordinary disk use from unusual process behavior.

### S7 — Recommendation Engine

**Goal:** convert diagnosis into safe, evidence-backed user actions.

Deliverables:
- diagnosis-to-recommendation rules
- confidence and evidence requirements
- impact/risk metadata
- no-op recommendation when evidence is insufficient
- recommendation CLI/report

Capability unlocked: the system can propose what to do next and explain why.

### S8 — Safety-Gated Optimizer

**Goal:** execute only narrowly defined, reversible optimizations.

Deliverables:
- explicit action allowlist
- dry-run default
- protected-process/resource checks
- before/after evidence
- rollback journal
- failure-safe behavior

Capability unlocked: the system can safely apply selected optimizations rather than only recommend them.

### S9 — Alerts & Predictive Signals

**Goal:** surface important state changes before a user has to inspect the dashboard.

Deliverables:
- trigger/escalation/recovery lifecycle
- cooldown/deduplication
- trend-based early-warning signals where evidence supports them
- alert history

Capability unlocked: the system can proactively notify about meaningful disk-health or I/O-risk changes.

### S10 — Analytics & Operator UI

**Goal:** make the evidence and reasoning easy to inspect.

Deliverables:
- historical analytics
- process/device trends
- diagnosis and action timelines
- usable CLI/TUI or GUI surface chosen after core behavior is stable

Capability unlocked: the user can explore the system state without reading raw logs.

### S11 — Production Hardening & Release

**Goal:** turn the rebuilt implementation into a reproducible release.

Deliverables:
- cross-platform test matrix
- packaging
- release gates
- performance/soak tests
- security/safety documentation
- migration/legacy notes
- versioned release

Capability unlocked: a supportable scratch-built release suitable for real use.

## Legacy milestone policy

The previous M1–M10/v1.0.0 cycle is not the active roadmap. Legacy completion files may remain under `docs/` as historical records until a dedicated archive cleanup is performed. New implementation work must reference S0–S11 only.

## Current status

**Active milestone: S0 — Scratch Architecture Foundation**
