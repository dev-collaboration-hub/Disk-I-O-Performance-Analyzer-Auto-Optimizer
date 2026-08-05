# Disk I/O Performance Analyzer & Auto Optimizer

A cross-platform system diagnostics project for monitoring disk capacity, utilization, and I/O activity, with later milestones for process analysis, root-cause detection, recommendations, and safe optimization.

## Milestone status

**M1 — Disk Monitoring Foundation: complete**

M1 includes:

- mounted disk discovery
- total, used, and free space monitoring
- disk utilization percentage
- cumulative read/write bytes and operation counts
- sampled read/write throughput and IOPS
- structured JSON Lines logging
- live and one-shot CLI dashboard
- automated unit and end-to-end integration tests

See [`docs/M1_COMPLETION.md`](docs/M1_COMPLETION.md) for the acceptance report.

## Quick start

```bash
python -m pip install -r requirements.txt
python main.py
```

Run one snapshot without clearing the terminal:

```bash
python main.py --once --no-clear
```

Monitor a particular path:

```bash
python main.py --path / --once --no-clear
```

Windows example:

```powershell
python main.py --path C:\ --once --no-clear
```

Use `python main.py --help` for all options, including refresh interval, I/O sampling interval, logging controls, and custom log paths.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Project structure

```text
.
├── analysis/                  # Later analysis milestones
├── config/
│   └── settings.py            # Runtime defaults and thresholds
├── docs/
│   └── M1_COMPLETION.md        # M1 delivery and acceptance report
├── logs/                       # Generated JSONL monitoring logs
├── monitoring/
│   ├── disk_capacity.py        # Total, used, and free bytes
│   ├── disk_detector.py        # Mounted disk discovery
│   ├── disk_monitor.py         # Cumulative I/O and sampled rates
│   ├── disk_stats.py           # Utilization percentage
│   └── metrics_snapshot.py     # Unified M1 snapshot collection
├── reporting/
│   └── cli_dashboard.py        # Live terminal dashboard
├── tests/
│   └── test_m1_integration.py  # Unit and end-to-end tests
├── utils/
│   ├── formatter.py            # Human-readable byte formatting
│   └── logger.py               # Structured JSONL logging
├── main.py                     # CLI entry point
└── requirements.txt
```

## M1 output

```text
========================================================================
DISK I/O PERFORMANCE ANALYZER — M1 MONITORING DASHBOARD
========================================================================
Disk: C:\
Status      : NORMAL
Usage       : 42.5%
Total Space : 476.94 GiB
Used Space  : 202.70 GiB
Free Space  : 274.24 GiB

System-wide Disk I/O
Read Operations  : 15,420
Write Operations : 12,340
Bytes Read       : 1.25 GiB
Bytes Written    : 850.00 MiB
Read Rate        : 24.20 MiB/s
Write Rate       : 8.10 MiB/s
========================================================================
```

## Roadmap

### M1 — Disk Monitoring Foundation ✅

- System-wide disk monitoring
- Read/write statistics
- Logging infrastructure
- CLI dashboard
- Integration testing

### M2 — Process-Level Disk Analysis

- Process enumeration
- Per-process disk I/O tracking
- Top consumer identification

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
