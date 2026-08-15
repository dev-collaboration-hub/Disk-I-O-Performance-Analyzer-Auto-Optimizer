# M4 Completion — Root Cause Detection Engine

## Status

**Complete**

M4 turns M1-M3 monitoring data into an evidence-backed explanation of likely disk pressure. The milestone is intentionally conservative: it reports observable signals and likely causes without claiming hardware saturation that the project does not directly measure.

## Delivered

### 1. Bottleneck detection

`analysis/bottleneck_detector.py` now detects three independent signals:

- elevated or critical disk-capacity pressure
- dominant current process disk I/O
- recent M3 disk spike evidence

The detector returns structured severity, signals, likely process/PID, current process share, process rate, disk usage, and human-readable evidence.

### 2. Cause classification

`analysis/cause_classifier.py` now provides:

- case-insensitive exact process matching
- path-safe process-name normalization
- cross-platform pattern rules
- explicit unknown classification when no supported rule matches

Unknown processes are not silently assigned a fabricated cause.

### 3. Historical sustained-activity evidence

M4 uses recent M3 snapshots to determine whether the same process remains dominant across multiple samples. The default requirement is three consecutive samples with at least the configured process-share threshold.

### 4. Root-cause reporting

`reporting/root_cause_report.py` now produces a structured report containing:

- bottleneck status
- severity
- signals
- suspected process and PID
- cause and category
- confidence
- disk and process metrics
- sustained-activity state
- evidence
- conservative recommendation

The original `generate_root_cause_report(...)` function signature is preserved for backward compatibility.

### 5. Dashboard integration

The main dashboard now attaches M4 analysis before historical snapshots are persisted. This means stored snapshots contain their root-cause assessment and the live dashboard shows the same M4 result.

M4 still works when history is disabled; only sustained-history and M3-event evidence become unavailable.

### 6. Configuration

M4 adds:

- `ROOT_CAUSE_PROCESS_SHARE_PERCENT`
- `ROOT_CAUSE_MIN_PROCESS_RATE_BYTES_PER_SECOND`
- `ROOT_CAUSE_SUSTAINED_SAMPLES`

These defaults keep the policy explicit and testable.

### 7. Tests

`tests/test_m4_integration.py` covers:

- no-signal behavior
- critical capacity pressure
- dominant process identification
- M3 spike integration
- case-insensitive/cross-platform cause classification
- evidence and recommendation output
- sustained historical activity
- persistence of M4 analysis
- dashboard rendering

Existing M1-M3 APIs and dashboard sections remain supported.

## Design boundary

Disk capacity utilization is not the same metric as device busy-time or latency. M4 therefore labels capacity pressure separately and does not infer physical storage saturation from throughput alone.

Future M5 behavior analysis can add richer baselines and anomaly models without changing this M4 evidence contract.
