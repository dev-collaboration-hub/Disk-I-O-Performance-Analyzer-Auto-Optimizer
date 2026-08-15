# M5 Completion — Process Behavior Analysis

## Status

**Complete**

M5 turns the process-level I/O snapshots from M2 and the historical storage from M3 into a lightweight behavioral analysis layer. It profiles recent process activity, compares the current sample with each process's own recent baseline, and flags sustained runaway process instances.

The implementation is intentionally deterministic and CPU-light. It uses only the already-collected top-consumer snapshots and Python standard-library statistics; it does not add a background sampler, ML dependency, or separate database.

## Delivered

### 1. Process profiling

`analysis/process_profiler.py` builds recent name-level behavior profiles with:

- samples observed
- average, median, maximum, and latest I/O rate
- average, median, maximum, and latest I/O share
- read/write activity ratios
- dominant-sample count
- simple recent trend direction
- burst ratio

When multiple instances share the same process name in one snapshot, the most active instance is used for that name-level sample so one timestamp cannot artificially inflate the baseline sample count.

### 2. Anomaly detection

`analysis/anomaly_detector.py` compares each current top consumer with its own prior baseline.

The detector requires a minimum number of prior samples and can flag:

- `RATE_SPIKE` — current I/O rate exceeds both an absolute floor and a configurable multiple of the historical median
- `SHARE_JUMP` — current process I/O share rises materially above its historical median

This avoids global fixed-rate assumptions across unrelated applications and avoids calling a first observation anomalous when no baseline exists.

### 3. Runaway process detection

`analysis/runaway_detector.py` detects sustained high disk activity from the same process instance.

A runaway requires the configured number of consecutive recent samples to preserve the same:

- normalized process name
- PID
- process creation time

Every sample must also remain above both the configured minimum I/O share and minimum I/O rate.

Using PID plus creation time prevents a reused PID from inheriting another process instance's history.

### 4. Integrated M5 report

`reporting/process_behavior_report.py` produces and attaches a structured `process_behavior` record containing:

- analysis status
- current process profiles
- anomaly list and count
- runaway list and count
- history-window size
- evidence and severity for detections

Status values are:

- `NO_PROCESS_ACTIVITY`
- `NORMAL`
- `ANOMALY_DETECTED`
- `RUNAWAY_DETECTED`

Runaway status takes precedence over a one-sample anomaly because it represents sustained evidence.

### 5. Historical integration

The dashboard loads a bounded recent history window and attaches M4 and M5 analysis before saving the current snapshot.

As a result, every new persisted snapshot contains:

- raw M1-M3 monitoring data
- M4 root-cause assessment
- M5 process-behavior assessment

When history is disabled or unavailable, M5 still produces a current-sample profile. Baseline anomaly and runaway claims remain unavailable until enough history exists.

### 6. Dashboard integration

The live CLI now includes an **M5 Process Behavior Analysis** section showing:

- current status
- number of profiles
- anomaly count
- runaway count
- detected anomaly signals
- detected runaway process instances
- top current profile when behavior is normal

### 7. Configuration

M5 adds explicit defaults for:

- profile history window
- minimum anomaly baseline samples
- anomaly rate multiplier
- anomaly I/O-share delta
- anomaly minimum current rate
- runaway consecutive samples
- runaway minimum I/O share
- runaway minimum I/O rate

All thresholds remain deterministic and testable in `config/settings.py`.

### 8. Tests

`tests/test_m5_integration.py` covers:

- profile construction and trend detection
- rate and share anomaly detection
- minimum-baseline protection
- sustained runaway detection
- PID-change / process-identity protection
- report status priority
- persistence of M5 analysis
- dashboard rendering

## Safety and interpretation

M5 describes process behavior, not storage-device health. A detected anomaly means a process changed materially relative to its observed baseline. A runaway means one process instance sustained dominant high-rate disk I/O across consecutive samples.

Neither result automatically terminates, throttles, or modifies a process. Automated mitigation remains a later milestone and must use explicit safety and rollback controls.

## Completion criteria

M5 is complete when:

- process profiles can be built from bounded recent history
- anomalies require an established baseline
- runaway detection requires sustained same-instance evidence
- M5 works with existing M1-M4 snapshots
- analysis is persisted with new historical snapshots
- dashboard output exposes the M5 result
- regression/integration tests cover the M5 behavior

All criteria are implemented.
