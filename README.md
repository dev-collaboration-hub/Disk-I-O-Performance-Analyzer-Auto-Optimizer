# Disk I/O Performance Analyzer & Auto Optimizer

A cross-platform diagnostics project for monitoring disk capacity, system-wide I/O, active process disk consumers, historical activity, root causes, process-behavior anomalies, optimization recommendations, and safety-gated reversible mitigation.

## Milestone status

- **M1 — Disk Monitoring Foundation: complete**
- **M2 — Process-Level Disk Analysis: complete**
- **M3 — Historical Data Collection: complete**
- **M4 — Root Cause Detection Engine: complete**
- **M5 — Process Behavior Analysis: complete**
- **M6 — Recommendation Engine: complete**
- **M7 — Auto Optimization Engine: complete**

M7 adds:

- safety-gated automatic mitigation
- dry-run by default
- reversible process-priority reduction
- PID + name + creation-time verification
- protected system-process denylist
- bounded automatic action count
- transactional rollback on failure
- durable optimization journal
- explicit rollback of the latest active session
- M7 integration tests

Completion reports:

- [`docs/M1_COMPLETION.md`](docs/M1_COMPLETION.md)
- [`docs/M2_COMPLETION.md`](docs/M2_COMPLETION.md)
- [`docs/M3_COMPLETION.md`](docs/M3_COMPLETION.md)
- [`docs/M4_COMPLETION.md`](docs/M4_COMPLETION.md)
- [`docs/M5_COMPLETION.md`](docs/M5_COMPLETION.md)
- [`docs/M6_COMPLETION.md`](docs/M6_COMPLETION.md)
- [`docs/M7_COMPLETION.md`](docs/M7_COMPLETION.md)

## Quick start

```bash
python -m pip install -r requirements.txt
python main.py
```

One snapshot:

```bash
python main.py --once --no-clear
```

Inspect historical activity:

```bash
python -m reporting.history_report --limit 20
```

Inspect M6 recommendations:

```bash
python -m reporting.recommendation_report
```

## M7 auto optimization

Preview the safe optimization plan without making changes:

```bash
python -m reporting.optimization_report
```

Apply only safety-approved reversible actions:

```bash
python -m reporting.optimization_report --apply
```

Rollback the latest still-active M7 session:

```bash
python -m reporting.optimization_report --rollback-last
```

Machine-readable plan/result:

```bash
python -m reporting.optimization_report --json
```

M7 does not automatically delete files, kill/suspend processes, stop services, change security settings, or tune databases/storage.

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
│   ├── impact_estimator.py
│   ├── process_profiler.py
│   ├── recommendation_engine.py
│   ├── runaway_detector.py
│   ├── spike_detector.py
│   └── timeline_builder.py
├── config/settings.py                # M1-M7 runtime/safety defaults
├── docs/
│   ├── M1_COMPLETION.md
│   ├── M2_COMPLETION.md
│   ├── M3_COMPLETION.md
│   ├── M4_COMPLETION.md
│   ├── M5_COMPLETION.md
│   ├── M6_COMPLETION.md
│   └── M7_COMPLETION.md
├── monitoring/
├── optimizer/
│   ├── auto_optimizer.py             # M7 planning/execution transaction
│   ├── process_priority.py           # Reversible process-priority action
│   ├── rollback_manager.py           # Durable journal + rollback
│   └── safety_guard.py               # M7 eligibility and identity checks
├── reporting/
│   ├── cli_dashboard.py
│   ├── history_report.py
│   ├── optimization_report.py        # M7 dry-run/apply/rollback CLI
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
│   └── test_m7_integration.py
├── utils/
├── main.py
└── requirements.txt
```

## How M7 works

M7 does not trust an M6 recommendation merely because it exists. An automatic action must pass an independent safety policy. The current policy accepts only sustained runaway-process cases with strong evidence, a sufficiently high impact score, a stable process identity, and a non-protected target.

The only automatic mutation is a bounded reduction in process scheduling priority. Before mutation, M7 captures the previous priority as a rollback token. If a later action in the same transaction fails, earlier actions are rolled back in reverse order.

Successful actions are written to a JSONL optimization journal so the latest active session can be explicitly rolled back later. Before rollback, process identity is checked again to avoid modifying a reused PID.

Default behavior is dry-run. `--apply` is required to make a system change. On POSIX, actual apply is refused unless the process has enough privilege to restore the original niceness during rollback.

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
- Ranking and safety metadata
- Impact estimation
- Historical persistence

### M7 — Auto Optimization Engine ✅
- Safety-gated automated mitigation
- Rollback protection
- Live process identity and protected-process checks
- Durable optimization journal
- Dry-run/apply separation
- Integration testing

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
