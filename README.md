# Disk I/O Performance Analyzer & Auto Optimizer

A cross-platform diagnostics project for monitoring disk capacity, system-wide I/O, active process disk consumers, historical activity, likely root causes, process-behavior anomalies, and evidence-backed optimization recommendations.

## Milestone status

- **M1 — Disk Monitoring Foundation: complete**
- **M2 — Process-Level Disk Analysis: complete**
- **M3 — Historical Data Collection: complete**
- **M4 — Root Cause Detection Engine: complete**
- **M5 — Process Behavior Analysis: complete**
- **M6 — Recommendation Engine: complete**

M6 adds:

- ranked evidence-backed optimization recommendations
- M4 root-cause + M5 behavior integration
- cause-specific manual actions
- recommendation safety metadata
- conservative impact scoring
- low-confidence gating
- recommendation persistence in new snapshots
- standalone text/JSON recommendation reports
- M6 integration tests

Completion reports:

- [`docs/M1_COMPLETION.md`](docs/M1_COMPLETION.md)
- [`docs/M2_COMPLETION.md`](docs/M2_COMPLETION.md)
- [`docs/M3_COMPLETION.md`](docs/M3_COMPLETION.md)
- [`docs/M4_COMPLETION.md`](docs/M4_COMPLETION.md)
- [`docs/M5_COMPLETION.md`](docs/M5_COMPLETION.md)
- [`docs/M6_COMPLETION.md`](docs/M6_COMPLETION.md)

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

Machine-readable M6 report:

```bash
python -m reporting.recommendation_report --json
```

## Tests

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
```

## Project structure

```text
.
├── analysis/
│   ├── anomaly_detector.py
│   ├── bottleneck_detector.py
│   ├── cause_classifier.py
│   ├── confidence_engine.py
│   ├── impact_estimator.py           # M6 impact opportunity estimate
│   ├── process_profiler.py
│   ├── recommendation_engine.py      # M6 ranked recommendations
│   ├── runaway_detector.py
│   ├── spike_detector.py
│   └── timeline_builder.py
├── config/settings.py                # M1-M6 runtime defaults
├── docs/
│   ├── M1_COMPLETION.md
│   ├── M2_COMPLETION.md
│   ├── M3_COMPLETION.md
│   ├── M4_COMPLETION.md
│   ├── M5_COMPLETION.md
│   └── M6_COMPLETION.md
├── monitoring/
├── reporting/
│   ├── cli_dashboard.py
│   ├── history_report.py
│   ├── process_behavior_report.py
│   ├── process_report.py
│   ├── recommendation_report.py      # M6 text/JSON report
│   └── root_cause_report.py
├── tests/
│   ├── test_m1_integration.py
│   ├── test_m2_integration.py
│   ├── test_m3_integration.py
│   ├── test_m4_integration.py
│   ├── test_m5_integration.py
│   └── test_m6_integration.py
├── utils/
├── main.py
└── requirements.txt
```

## How M6 works

M6 consumes the evidence already produced by earlier milestones instead of creating a second monitoring pipeline.

It considers capacity pressure, M4 root-cause confidence, M5 anomalies, sustained runaway process instances, and current process I/O share/rate. Recommendations are deduplicated and ranked by priority.

Each recommendation includes safety metadata and an impact estimate. The impact score is an evidence-weighted opportunity score, **not a guaranteed speedup**. Exact performance gain is intentionally not claimed because storage hardware has different performance ceilings.

M6 is advisory only: `automation_eligible` is false and `automatic_changes_applied` is false. Automated mitigation, rollback, and safety enforcement belong to M7.

## Roadmap

### M1 — Disk Monitoring Foundation ✅
- System-wide disk monitoring
- Read/write statistics
- Logging and CLI

### M2 — Process-Level Disk Analysis ✅
- Process enumeration
- Per-process disk I/O
- Top consumer ranking

### M3 — Historical Data Collection ✅
- Metrics history
- Event timeline
- Spike detection

### M4 — Root Cause Detection Engine ✅
- Cause classification
- Bottleneck identification
- Confidence/evidence reporting

### M5 — Process Behavior Analysis ✅
- Process profiling
- Baseline-aware anomaly detection
- Runaway process detection

### M6 — Recommendation Engine ✅
- Optimization recommendations
- Recommendation ranking and safety metadata
- Impact estimation
- Historical persistence
- Standalone reporting

### M7 — Auto Optimization Engine
- Automated mitigation
- Rollback protection
- Safety checks

### M8 — Alerting & Notifications
- Real-time alerts
- Event notifications

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
