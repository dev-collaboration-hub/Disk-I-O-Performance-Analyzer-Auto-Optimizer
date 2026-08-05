# Disk I/O Performance Analyzer & Auto Optimizer

A cross-platform diagnostics project for monitoring disk capacity, system-wide
I/O, and the processes currently generating disk activity.

## Milestone status

- **M1 — Disk Monitoring Foundation: complete**
- **M2 — Process-Level Disk Analysis: complete**

M2 adds:

- safe process enumeration
- cumulative per-process read/write counters
- sampled per-process throughput and IOPS
- PID-reuse-safe process matching
- top current disk-consumer ranking
- process share percentages
- integrated dashboard and standalone process report
- M1 regression tests and M2 integration tests

See [`docs/M1_COMPLETION.md`](docs/M1_COMPLETION.md) and
[`docs/M2_COMPLETION.md`](docs/M2_COMPLETION.md).

## Quick start

```bash
python -m pip install -r requirements.txt
python main.py
```

One snapshot:

```bash
python main.py --once --no-clear
```

Show more process consumers:

```bash
python main.py --once --no-clear --process-limit 10
```

Disable process collection and show only M1 metrics:

```bash
python main.py --once --no-clear --hide-processes
```

Standalone process report:

```bash
python -m reporting.process_report --limit 10 --sample-interval 1
```

Use `python main.py --help` for all options.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Project structure

```text
.
├── analysis/                       # Later analysis milestones
├── config/settings.py              # Runtime defaults
├── docs/
│   ├── M1_COMPLETION.md
│   └── M2_COMPLETION.md
├── logs/                            # Generated JSONL monitoring logs
├── monitoring/
│   ├── disk_capacity.py
│   ├── disk_detector.py
│   ├── disk_monitor.py
│   ├── disk_stats.py
│   ├── metrics_snapshot.py          # Shared system/process sample window
│   ├── process_detector.py          # Process enumeration
│   ├── process_io_monitor.py        # Per-process counters and rates
│   └── top_disk_consumers.py        # Current-activity ranking
├── reporting/
│   ├── cli_dashboard.py             # Integrated M2 dashboard
│   └── process_report.py            # Standalone process report
├── tests/
│   ├── test_m1_integration.py
│   └── test_m2_integration.py
├── main.py
└── requirements.txt
```

## How M2 identifies a top consumer

Process I/O counters are cumulative. Ranking those lifetime totals would make an
old process look busy even when it is currently idle. M2 records counters before
and after one sampling window, calculates non-negative deltas, then ranks the
processes by bytes transferred during that window.

Processes are matched using both PID and creation time so a reused PID cannot
inherit another process's counters.

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

### M3 — Historical Data Collection

- Metrics history
- Event timeline
- Disk spike recording

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

## License

License to be determined.
