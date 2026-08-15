# Disk I/O Performance Analyzer & Auto Optimizer

A cross-platform diagnostics project for monitoring disk capacity, system-wide I/O, active process disk consumers, historical disk activity, likely root causes, and process-behavior anomalies.

## Milestone status

- **M1 — Disk Monitoring Foundation: complete**
- **M2 — Process-Level Disk Analysis: complete**
- **M3 — Historical Data Collection: complete**
- **M4 — Root Cause Detection Engine: complete**
- **M5 — Process Behavior Analysis: complete**

M5 adds:

- bounded historical process profiling
- per-process rate/share baselines
- baseline-aware anomaly detection
- sustained runaway-process detection
- PID + creation-time identity protection
- integrated M5 dashboard output
- M5 results persisted with monitoring snapshots
- M5 regression and integration tests

Completion reports:

- [`docs/M1_COMPLETION.md`](docs/M1_COMPLETION.md)
- [`docs/M2_COMPLETION.md`](docs/M2_COMPLETION.md)
- [`docs/M3_COMPLETION.md`](docs/M3_COMPLETION.md)
- [`docs/M4_COMPLETION.md`](docs/M4_COMPLETION.md)
- [`docs/M5_COMPLETION.md`](docs/M5_COMPLETION.md)

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

Disable historical persistence:

```bash
python main.py --once --no-clear --no-history
```

M5 still profiles the current sample with history disabled, but it does not claim a historical anomaly or runaway until enough prior evidence exists.

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
│   ├── anomaly_detector.py           # M5 baseline-aware anomaly detection
│   ├── bottleneck_detector.py        # M4 bottleneck evidence engine
│   ├── cause_classifier.py           # M4 process-to-cause rules
│   ├── confidence_engine.py          # Root-cause confidence scoring
│   ├── process_profiler.py           # M5 historical behavior profiles
│   ├── runaway_detector.py           # M5 sustained same-process detection
│   ├── spike_detector.py             # M3 capacity and I/O spike detection
│   └── timeline_builder.py           # Structured persistent event timeline
├── config/settings.py                # M1-M5 runtime defaults
├── docs/
│   ├── M1_COMPLETION.md
│   ├── M2_COMPLETION.md
│   ├── M3_COMPLETION.md
│   ├── M4_COMPLETION.md
│   └── M5_COMPLETION.md
├── logs/                              # Runtime JSONL files
├── monitoring/
│   ├── disk_capacity.py
│   ├── disk_detector.py
│   ├── disk_monitor.py
│   ├── disk_stats.py
│   ├── metrics_snapshot.py           # Versioned unified metrics snapshot
│   ├── process_detector.py
│   ├── process_io_monitor.py
│   └── top_disk_consumers.py
├── reporting/
│   ├── cli_dashboard.py              # Integrated M5 dashboard
│   ├── history_report.py
│   ├── process_behavior_report.py    # Structured M5 analysis/reporting
│   ├── process_report.py
│   └── root_cause_report.py          # Structured M4 analysis/reporting
├── tests/
│   ├── test_m1_integration.py
│   ├── test_m2_integration.py
│   ├── test_m3_integration.py
│   ├── test_m4_integration.py
│   └── test_m5_integration.py
├── utils/
│   ├── history_manager.py
│   └── logger.py
├── main.py
└── requirements.txt
```

## How M3 history works

Each monitoring cycle creates a versioned snapshot containing disk metrics, system I/O rates, and process-level activity. M3 appends the snapshot to `metrics_history.jsonl`; it does not rewrite the complete history on every cycle.

Before storing a new snapshot, M3 compares it with the most recent stored snapshot. Meaningful changes become structured events in `event_timeline.jsonl`, including spikes, threshold transitions, collection warnings, and top disk-consumer changes.

Malformed or incomplete JSONL records are skipped during reads, so an interrupted final write does not make earlier history unusable. Retention limits prevent indefinite growth.

## How M4 root-cause detection works

M4 does not assume that high raw throughput automatically means a bottleneck because storage devices have different performance ceilings. Instead, it combines independent evidence:

1. **Capacity pressure** — warning or critical disk-space utilization.
2. **Process I/O dominance** — one process owns a configurable share of active process disk I/O.
3. **Recent spike evidence** — M3 detected a disk-usage or throughput spike.
4. **Sustained activity** — the same process remains dominant across recent snapshots.

The root-cause report classifies the process when possible, assigns severity and confidence, keeps the evidence visible, and produces a conservative recommendation.

## How M5 process behavior analysis works

M5 analyzes the already-collected top process consumers instead of adding another sampler.

For each current process it can build a recent profile containing median/average/max I/O rate, I/O share, read/write mix, dominance frequency, trend, and burst ratio.

An anomaly requires an established per-process baseline. The current sample can be flagged when its rate grows by a configurable multiple of its own historical median or its I/O share jumps materially above its own median.

A runaway requires stronger evidence: the same process **instance** must stay above both the configured rate and share thresholds for consecutive samples. Identity uses process name + PID + creation time so PID reuse does not create false continuity.

M5 is diagnostic only. It does not kill, pause, throttle, or reconfigure processes.

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

### M4 — Root Cause Detection Engine ✅

- Cause classification
- Bottleneck identification
- Root-cause reporting
- Confidence and evidence
- Historical-context integration
- Dashboard integration
- Integration testing

### M5 — Process Behavior Analysis ✅

- Process profiling
- Baseline-aware anomaly detection
- Runaway process detection
- Same-instance identity protection
- Historical persistence
- Dashboard integration
- Integration testing

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
- Standard-library JSONL persistence and statistics

## License

License to be determined.
