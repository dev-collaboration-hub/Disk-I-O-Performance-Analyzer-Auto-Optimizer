# Changelog

All notable production changes are documented here.

## 1.0.0 — 2026-08-16

First stable production release.

### Monitoring and history
- M1 system-wide disk capacity and I/O monitoring.
- M2 per-process disk I/O sampling and top-consumer ranking.
- M3 crash-tolerant JSONL history, event timeline, spike detection, and retention.

### Diagnosis and behavior
- M4 evidence-backed bottleneck/root-cause detection.
- M5 historical process profiling, anomaly detection, and sustained runaway detection.
- M6 ranked recommendations with conservative impact estimates.

### Safe optimization and notifications
- M7 opt-in, safety-gated reversible process-priority mitigation with rollback journal.
- M8 stateful alerts with cooldown, escalation, reminders, recovery, and M7 outcome events.

### Analytics and production readiness
- M9 retained-history disk, I/O, process, alert, recovery, and optimization analytics.
- M10 installable Python package metadata, stable versioning, console entry points, CI/build workflows, production/security documentation, and release validation.

### Safety boundary
Automatic optimization remains deliberately narrow. The stable release does not automatically delete files, terminate/suspend processes, stop services, change security software configuration, tune databases, or modify storage-device settings.
