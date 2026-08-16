# M8 Completion — Alerting & Notifications

## Status

**Complete**

M8 makes the monitoring/analysis pipeline proactive by emitting stateful alerts from M1–M6 evidence and recording M7 optimization events.

## Delivered

- Stateful alert keys for capacity pressure, M3 spikes, M4 bottlenecks, M5 anomalies/runaways, and high-priority M6 recommendations.
- `TRIGGERED`, `ESCALATED`, `REMINDER`, and `RECOVERED` lifecycle events.
- Duplicate suppression during a configurable cooldown.
- Severity escalation bypassing cooldown.
- Recovery protection: a subsystem not evaluated in the current sample is not falsely marked recovered.
- Crash-tolerant `logs/alerts.jsonl` history with retention and active-state reconstruction.
- M7 apply/failure/rollback operational events in the same alert stream.
- M8 dashboard section with emitted/suppressed/active counts.
- Standalone `reporting.alert_report` CLI for history, active alerts, and JSON.
- M8 configuration and integration tests.

## Commands

```bash
python -m reporting.alert_report
python -m reporting.alert_report --active
python -m reporting.alert_report --json
```

M7 dry-runs do not create false action notifications. Actual apply/failure/rollback outcomes do.

## Completion criteria

M8 is complete because important conditions can trigger timely stateful notifications, duplicate spam is controlled, recovery is visible, alert state survives restarts, current active alerts can be reconstructed, and M7 execution outcomes are recorded.
