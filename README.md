# Disk I/O Performance Analyzer & Auto Optimizer

A cross-platform diagnostics project for monitoring disk capacity, system-wide I/O, active process disk consumers, historical activity, likely root causes, process-behavior anomalies, evidence-backed optimization recommendations, safety-gated reversible mitigation, proactive alerts, historical analytics, and production packaging.

## Release status

**Stable source version: 1.0.0**

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
- **M10 — Production Release: complete**

M10 adds:

- PEP 517 installable packaging through `pyproject.toml`
- stable version metadata (`1.0.0`)
- installed console commands for monitoring, alerts, analytics, optimization, and recommendations
- Python 3.10–3.13 CI test matrix
- wheel/source-distribution build validation
- tag-triggered GitHub release workflow
- production deployment, security, changelog, and release-check documentation
- release-specific integration tests

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
- [`docs/M10_COMPLETION.md`](docs/M10_COMPLETION.md)

## Install

From a checked-out release:

```bash
python -m pip install .
```

Development/source install remains supported:

```bash
python -m pip install -r requirements.txt
python main.py
```

Installed commands:

```bash
disk-io-analyzer --help
disk-io-alerts --help
disk-io-analytics --help
disk-io-optimize --help
disk-io-recommendations --help
```

## Common workflows

One monitoring snapshot:

```bash
disk-io-analyzer --once --no-clear
```

Historical activity:

```bash
python -m reporting.history_report --limit 20
```

M6 recommendations:

```bash
disk-io-recommendations
```

M7 safe optimization:

```bash
disk-io-optimize
disk-io-optimize --apply
disk-io-optimize --rollback-last
```

M8 alerts:

```bash
disk-io-alerts
disk-io-alerts --active
disk-io-alerts --json
```

M9 analytics:

```bash
disk-io-analytics
disk-io-analytics --limit 2000 --top-processes 15
disk-io-analytics --json
```

## M7 safety boundary

Automatic optimization is deliberately narrow. M7 is dry-run by default and only applies safety-approved, reversible process-priority mitigation after process identity and protected-process checks. It does not automatically delete files, terminate/suspend processes, stop services, alter security configuration, tune databases, or change storage-device settings.

## M8 alerting

M8 emits stateful `TRIGGERED`, `ESCALATED`, `REMINDER`, and `RECOVERED` events from M1–M6 evidence and records actual M7 apply/failure/rollback outcomes. Missing telemetry is not treated as recovery.

## M9 analytics

M9 is on-demand and retention-aware. It summarizes retained M3 monitoring snapshots, M8 alert history, and M7 optimization journal records without repeatedly scanning history in the live monitoring loop.

## Production release validation

Run the source release gate before publishing:

```bash
python scripts/release_check.py
```

Build distributions:

```bash
python -m pip install build
python -m build
```

See [`docs/PRODUCTION_DEPLOYMENT.md`](docs/PRODUCTION_DEPLOYMENT.md) and [`docs/RELEASE_CHECKLIST.md`](docs/RELEASE_CHECKLIST.md).

## Tests

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
```

## Project structure

```text
.
├── .github/workflows/                 # CI and tag release automation
├── alerts/                            # M8 alerting
├── analytics/                         # M9 analytics
├── analysis/                          # M4-M6 diagnosis/recommendation logic
├── config/                            # runtime settings + stable version
├── docs/                              # milestone and production documentation
├── monitoring/                        # M1-M3 monitoring
├── optimizer/                         # M7 safety-gated optimization
├── reporting/                         # dashboard and report CLIs
├── scripts/release_check.py           # M10 release gate
├── tests/                             # M1-M10 tests
├── CHANGELOG.md
├── SECURITY.md
├── main.py
├── pyproject.toml
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
### M10 — Production Release ✅

The M1–M10 implementation roadmap is complete.

## Technology

- Python 3.10+
- `psutil`
- `unittest`
- standard-library JSONL persistence/statistics
- PEP 517 / setuptools packaging

## License

License to be determined.
