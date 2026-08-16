# Disk I/O Performance Analyzer & Auto Optimizer

A cross-platform diagnostics project for monitoring disk capacity, system-wide I/O, active process disk consumers, historical activity, likely root causes, process-behavior anomalies, evidence-backed optimization recommendations, safety-gated reversible mitigation, proactive alerts, and historical analytics.

## Milestone status

- **M1 — Disk Monitoring Foundation: complete**
- **M2 — Process-Level Disk Analysis: complete**
- **M3 — Historical Data Collection: complete**
- **M4 — Root Cause Detection Engine: complete**
- **M5 — Process Behavior Analysis: complete**
- **M6 — Recommendation Engine: complete**
- **M7 — Auto Optimization Engine: complete**
- **M8 — Alerting & Notifications: complete**
- **M9 — Reporting & Analytics: complete**

M9 adds:

- disk-usage trend analysis with change and slope
- system I/O average, median, P95, peak, and trend
- retained top-process consumer analytics
- anomaly/runaway occurrence aggregation
- alert lifecycle and recovery-time analytics
- M7 optimization journal outcome analytics
- retention-aware text and JSON reports
- M9 integration tests

Completion reports:

- [`docs/M1_COMPLETION.md`](docs/M1_COMPLETION.md)
- [`docs/M2_COMPLETION.md`](docs/M2_COMPLETION.md)
- [`docs/M3_COMPLETION.md`](docs/M3_COMPLETION.md)
- [`docs/M4_COMPLETION.md`](docs/M4_COMPLETION.md)
- [`docs/M5_COMPLETION.md`](docs/M5_COMPLETION.md)
- [`docs/M6_COMPLETION.md`](docs/M6_COMPLETION.md)
- [`docs/M7_COMPLETION.md`](docs/M7_COMPLETION.md)
- [`docs/M8_COMPLETION.md`](docs/M8_COMPLETION.md)
- [`docs/M9_COMPLETION.md`](docs/M9_COMPLETION.md)

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

Generate the M9 analytics report:

```bash
python -m reporting.analytics_report
python -m reporting.analytics_report --limit 2000 --top-processes 15
python -m reporting.analytics_report --json
```

## How M8 alerting works

M8 consumes evidence already produced by earlier milestones instead of creating another sampler.

Each active condition has a stable alert key. First observation emits `TRIGGERED`; higher severity emits `ESCALATED`; unchanged conditions are suppressed during cooldown and can later emit `REMINDER`; when an evaluated condition disappears M8 emits `RECOVERED`.

Alert history is stored independently in `logs/alerts.jsonl`. Missing telemetry does not count as recovery. M7 actual apply/failure/rollback outcomes are also recorded in the M8 stream; dry-run planning is not reported as an executed action.

## How M9 analytics works

M9 is an on-demand reporting layer, so the live monitoring loop does not repeatedly scan historical files.

The report consumes retained M3 monitoring snapshots, M8 alert history, and the M7 optimization journal. It summarizes disk-capacity trends, system I/O distributions, observed top process consumers, detection frequencies, alert lifecycle outcomes, recovery timing, and optimization actions.

Trend slope uses timestamps when enough valid timestamps exist. P95 uses deterministic standard-library interpolation. Process analytics are intentionally labeled as **retained top-consumer observations** because M2 stores the ranked active subset rather than every process on the machine.

M9 is retention-aware: reports describe the records that still exist in the configured JSONL stores, not an implied all-time history.

## Tests

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
```

## Project structure

```text
.
├── alerts/
│   ├── alert_engine.py
│   ├── alert_store.py
│   └── notifier.py
├── analytics/
│   ├── history_analytics.py          # M9 disk/system-I/O trends
│   ├── outcome_analytics.py          # M9 alert/M7 outcome analytics
│   └── process_analytics.py          # M9 process-consumer aggregates
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
│   ├── M8_COMPLETION.md
│   └── M9_COMPLETION.md
├── monitoring/
├── optimizer/
├── reporting/
│   ├── alert_report.py
│   ├── analytics_report.py           # M9 text/JSON analytics CLI
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
│   ├── test_m8_integration.py
│   └── test_m9_integration.py
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
### M9 — Reporting & Analytics ✅

- Trend analysis
- Disk usage analytics
- System I/O distribution reporting
- Process-consumer analytics
- Alert/recovery analytics
- Optimization outcome analytics
- Text and JSON reports

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
