# Disk I/O Performance Analyzer & Auto Optimizer

A cross-platform diagnostics project for monitoring disk capacity, system-wide I/O, active process disk consumers, and historical disk activity.

## Milestone status

- **M1 — Disk Monitoring Foundation: complete**
- **M2 — Process-Level Disk Analysis: complete**
- **M3 — Historical Data Collection: complete**

M3 adds:

- append-only metrics history
- structured event timeline
- configurable retention
- corrupt/partial record recovery
- capacity-utilization and throughput spike detection
- disk status and top-consumer transition events
- integrated historical dashboard section
- standalone history report

Completion reports:

- [`docs/M1_COMPLETION.md`](docs/M1_COMPLETION.md)
- [`docs/M2_COMPLETION.md`](docs/M2_COMPLETION.md)
- [`docs/M3_COMPLETION.md`](docs/M3_COMPLETION.md)

## Quick start

```bash
python -m pip install -r requirements.txt
python main.py
```

One snapshot without clearing the terminal:

```bash
python main.py --once --no-clear
```

Use custom M3 history files:

```bash
python main.py --once --no-clear \
  --history-file logs/my-history.jsonl \
  --event-file logs/my-events.jsonl
```

Disable historical persistence:

```bash
python main.py --once --no-clear --no-history
```

Inspect historical activity:

```bash
python -m reporting.history_report --limit 20
```

Machine-readable historical report:

```bash
python -m reporting.history_report --json
```

Standalone current process report:

```bash
python -m reporting.process_report --limit 10 --sample-interval 1
```

Use `python main.py --help` for process, retention, logging, and spike-threshold options.

## Tests

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
```

## Project structure

```text
.
├── analysis/
│   ├── spike_detector.py            # Capacity and I/O spike detection
│   └── timeline_builder.py          # Structured persistent event timeline
├── config/settings.py               # M1-M3 runtime defaults
├── docs/
│   ├── M1_COMPLETION.md
│   ├── M2_COMPLETION.md
│   └── M3_COMPLETION.md
├── logs/                             # Runtime JSONL files
├── monitoring/
│   ├── disk_capacity.py
│   ├── disk_detector.py
│   ├── disk_monitor.py
│   ├── disk_stats.py
│   ├── metrics_snapshot.py           # Versioned unified snapshot
│   ├── process_detector.py
│   ├── process_io_monitor.py
│   └── top_disk_consumers.py
├── reporting/
│   ├── cli_dashboard.py              # Integrated M3 dashboard
│   ├── history_report.py             # Historical report CLI
│   └── process_report.py
├── tests/
│   ├── test_m1_integration.py
│   ├── test_m2_integration.py
│   └── test_m3_integration.py
├── utils/
│   ├── history_manager.py            # Crash-tolerant JSONL store
│   └── logger.py
├── main.py
└── requirements.txt
```

## How M3 history works

Each monitoring cycle creates a versioned snapshot containing disk metrics, system I/O rates, and process-level activity. M3 appends this snapshot to `metrics_history.jsonl`; it does not rewrite the complete history on every cycle.

Before storing a new snapshot, M3 compares it with the most recent stored snapshot. Meaningful changes become structured events in `event_timeline.jsonl`, including spikes, threshold transitions, collection warnings, and top disk-consumer changes.

Malformed or incomplete JSONL records are skipped during reads, so an interrupted final write does not make earlier history unusable. Retention limits prevent indefinite growth.

## Roadmap

### M1 — Disk Monitoring Foundation ✅

- System-wide disk monitoring
- Read/write statistics
- Logging infrastructure
- CLI dashboard
- Integration testing

### M2 — Process-Level Disk Analysis ✅

- Process enumeration
- Per-process disk I/O tracking
- Top consumer identification
- Dashboard and process report
- Integration testing

### M3 — Historical Data Collection ✅

- Metrics history
- Event timeline
- Disk spike recording
- Retention and recovery
- Historical report
- Integration testing

### M4 — Root Cause Detection Engine

- Cause classification
- Bottleneck identification
- Root-cause reporting

### M5 — Process Behavior Analysis

- Process profiling
- Anomaly detection
- Runaway process detection

### M6 — Recommendation Engine

- Optimization recommendations
- Impact estimation

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
- Standard-library JSONL persistence

## License

License to be determined.
