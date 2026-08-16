# Disk I/O Performance Analyzer & Auto Optimizer

A cross-platform diagnostics project for monitoring disk capacity, system-wide I/O, active process disk consumers, historical activity, likely root causes, process-behavior anomalies, evidence-backed optimization recommendations, safety-gated reversible mitigation, and proactive alerts.

## Milestone status

- **M1 — Disk Monitoring Foundation: complete**
- **M2 — Process-Level Disk Analysis: complete**
- **M3 — Historical Data Collection: complete**
- **M4 — Root Cause Detection Engine: complete**
- **M5 — Process Behavior Analysis: complete**
- **M6 — Recommendation Engine: complete**
- **M7 — Auto Optimization Engine: complete**
- **M8 — Alerting & Notifications: complete**

M8 adds:

- stateful alerts from M1-M6 evidence
- `TRIGGERED`, `ESCALATED`, `REMINDER`, and `RECOVERED` lifecycle
- duplicate suppression and configurable cooldown
- persistent active-alert state and history
- M7 apply/failure/rollback operational notifications
- live dashboard alert section
- standalone active/history/JSON alert reports
- M8 integration tests

Completion reports:

- [`docs/M1_COMPLETION.md`](docs/M1_COMPLETION.md)
- [`docs/M2_COMPLETION.md`](docs/M2_COMPLETION.md)
- [`docs/M3_COMPLETION.md`](docs/M3_COMPLETION.md)
- [`docs/M4_COMPLETION.md`](docs/M4_COMPLETION.md)
- [`docs/M5_COMPLETION.md`](docs/M5_COMPLETION.md)
- [`docs/M6_COMPLETION.md`](docs/M6_COMPLETION.md)
- [`docs/M7_COMPLETION.md`](docs/M7_COMPLETION.md)
- [`docs/M8_COMPLETION.md`](docs/M8_COMPLETION.md)

## Quick start

```bash
python -m pip install -r requirements.txt
python main.py
```

One snapshot without clearing the terminal:

```bash
python main.py --once --no-clear
```

Use custom history files:

```bash
python main.py --once --no-clear \
  --history-file logs/my-history.jsonl \
  --event-file logs/my-events.jsonl
```

Inspect historical activity:

```bash
python -m reporting.history_report --limit 20
```

Inspect M6 recommendations:

```bash
python -m reporting.recommendation_report
```

M7 safe optimization:

```bash
python -m reporting.optimization_report
python -m reporting.optimization_report --apply
python -m reporting.optimization_report --rollback-last
```

Inspect M8 alerts:

```bash
python -m reporting.alert_report
python -m reporting.alert_report --active
python -m reporting.alert_report --json
```

## How M8 alerting works

M8 consumes evidence already produced by earlier milestones instead of creating another sampler.

Each active condition has a stable alert key. First observation emits `TRIGGERED`; higher severity emits `ESCALATED`; unchanged conditions are suppressed during cooldown and can later emit `REMINDER`; when an evaluated condition disappears M8 emits `RECOVERED`.

Alert history is stored independently in `logs/alerts.jsonl`. Missing telemetry does not count as recovery. M7 actual apply/failure/rollback outcomes are also recorded in the M8 stream; dry-run planning is not reported as an executed action.

## Tests

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
```

## Project structure

```text
.
├── alerts/
│   ├── alert_engine.py               # M8 lifecycle and evidence mapping
│   ├── alert_store.py                # M8 JSONL state/history
│   └── notifier.py                   # Notification formatting/dispatch
├── analysis/
│   ├── anomaly_detector.py
│   ├── bottleneck_detector.py
│   ├── cause_classifier.py
│   ├── confidence_engine.py
│   ├── impact_estimator.py
│   ├── process_profiler.py
│   ├── recommendation_engine.py
│   ├── runaway_detector.py
│   ├── spike_detector.py
│   └── timeline_builder.py
├── config/settings.py
├── docs/
│   ├── M1_COMPLETION.md
│   ├── M2_COMPLETION.md
│   ├── M3_COMPLETION.md
│   ├── M4_COMPLETION.md
│   ├── M5_COMPLETION.md
│   ├── M6_COMPLETION.md
│   ├── M7_COMPLETION.md
│   └── M8_COMPLETION.md
├── monitoring/
├── optimizer/
├── reporting/
│   ├── alert_report.py               # M8 active/history report
│   ├── cli_dashboard.py
│   ├── history_report.py
│   ├── optimization_report.py
│   ├── process_behavior_report.py
│   ├── process_report.py
│   ├── recommendation_report.py
│   └── root_cause_report.py
├── tests/
│   ├── test_m1_integration.py
│   ├── test_m2_integration.py
│   ├── test_m3_integration.py
│   ├── test_m4_integration.py
│   ├── test_m5_integration.py
│   ├── test_m6_integration.py
│   ├── test_m7_integration.py
│   └── test_m8_integration.py
├── main.py
└── requirements.txt
```

## Roadmap

### M1 — Disk Monitoring Foundation ✅
### M2 — Process-Level Disk Analysis ✅
### M3 — Historical Data Collection ✅
### M4 — Root Cause Detection Engine ✅
### M5 — Process Behavior Analysis ✅
### M6 — Recommendation Engine ✅
### M7 — Auto Optimization Engine ✅
### M8 — Alerting & Notifications ✅

### M9 — Reporting & Analytics
- Trend analysis
- Usage reports

### M10 — Production Release
- Packaging
- Stable release
- Production documentation

## Technology

- Python 3.10+
- `psutil`
- `unittest`
- Standard-library JSONL persistence and statistics

## License

License to be determined.
