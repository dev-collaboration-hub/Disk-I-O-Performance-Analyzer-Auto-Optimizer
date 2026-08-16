# M9 Completion — Reporting & Analytics

## Status

**Complete**

M9 turns retained M3–M8 operational data into an on-demand analytics layer without adding repeated historical scans to the live monitoring loop.

## Delivered

### 1. Disk-capacity trend analytics

`analytics/history_analytics.py` aggregates retained per-disk samples and reports:

- sample count
- average, minimum, maximum, and latest usage
- usage change in percentage points
- trend direction
- timestamp-aware slope in percentage points per hour

If there are not enough samples, trend status is explicitly `INSUFFICIENT_DATA`.

### 2. System I/O analytics

The same history analyzer reports:

- average total throughput
- median total throughput
- P95 total throughput
- maximum throughput
- average read/write rates
- peak timestamp
- throughput trend

P95 is computed deterministically with standard-library interpolation; no numerical dependency is added.

### 3. Detection-frequency analytics

Retained snapshots are also summarized for:

- M4 bottleneck samples
- M5 anomaly samples
- M5 runaway samples
- M6 recommendation samples
- M8 alert-emission samples

### 4. Process-consumer analytics

`analytics/process_analytics.py` summarizes the top consumers retained by M2 history:

- samples observed
- top-consumer/dominance frequency
- average and maximum I/O rate
- average and maximum I/O share
- latest rate/share/PID
- anomaly and runaway occurrence counts
- observation frequency across retained snapshots

The report clearly states that this is retained top-consumer coverage, not a record of every system process.

### 5. Alert lifecycle analytics

`analytics/outcome_analytics.py` summarizes M8 alert history by:

- event type
- severity
- alert group
- source milestone
- currently active alerts
- recovered condition count
- average and median recovery time where a trigger/recovery pair is available

### 6. M7 optimization outcome analytics

The optimization journal is summarized by:

- journal event type
- session count
- actions applied
- actions rolled back
- rolled-back sessions
- committed sessions
- sessions that still retain rollback availability

No unsupported success-rate claim is invented from the journal.

### 7. Unified report CLI

`reporting/analytics_report.py` combines snapshot, alert, and optimization analytics.

Text report:

```bash
python -m reporting.analytics_report
```

Bounded retained window:

```bash
python -m reporting.analytics_report --limit 2000 --top-processes 15
```

Machine-readable report:

```bash
python -m reporting.analytics_report --json
```

Custom stores can be supplied with `--history-file`, `--alert-file`, and `--journal-file`.

### 8. Crash/legacy tolerant reading

The M9 loader:

- skips malformed JSONL lines
- tolerates an interrupted/corrupt tail
- accepts legacy JSON-array history
- applies an explicit recent-record limit

### 9. Tests

`tests/test_m9_integration.py` covers:

- increasing disk trend and slope
- I/O percentile/peak analytics
- process aggregation
- anomaly/runaway occurrence aggregation
- alert recovery duration
- active-alert reconstruction
- M7 outcome aggregation
- combined report rendering
- corrupt JSONL recovery and limit
- explicit no-data status

Local M9 validation: **10/10 tests passed** and M9 Python modules compile successfully.

## Design boundary

M9 is descriptive analytics over retained evidence. It does not invent missing historical data, does not treat retained top consumers as every process, and does not claim causal performance improvement from M7 actions.

## Completion criteria

M9 is complete because the project can now produce deterministic retained-history trend analysis and usage reports across disk capacity, system I/O, process activity, alerts, recovery, and optimization outcomes, with text/JSON output and integration tests.
