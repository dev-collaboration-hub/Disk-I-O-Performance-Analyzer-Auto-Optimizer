# M6 Completion — Recommendation Engine

## Status

**Complete**

M6 converts M4 root-cause evidence and M5 process-behavior evidence into ranked, manual optimization recommendations with conservative impact estimation.

M6 is advisory only. It does not stop processes, delete files, change services, tune databases, or modify system settings. Automated mitigation remains M7.

## Delivered

### 1. Recommendation engine

`analysis/recommendation_engine.py` generates recommendations from:

- disk-capacity pressure
- M4 root-cause attribution and confidence
- M5 anomalies
- M5 sustained runaway-process detections
- system I/O spike evidence

Recommendations are deduplicated and ranked by explicit priority scores.

### 2. Cause-aware actions

Known M4 causes map to conservative actions for:

- indexing and antivirus background work
- browsers
- development/build activity
- Python and JavaScript runtimes
- databases
- file synchronization
- backup activity
- Windows background services
- unknown processes

Unknown or low-confidence evidence does not trigger aggressive advice.

### 3. Safety metadata

Every recommendation contains:

- priority and priority score
- reason/evidence
- target process/PID when available
- safety level
- `requires_confirmation = true`
- `automation_eligible = false`

This keeps M6 clearly separated from M7 automatic optimization.

### 4. Impact estimation

`analysis/impact_estimator.py` produces an evidence-weighted opportunity estimate using observed data such as:

- current process I/O share
- current process I/O rate
- M4 confidence
- M5 runaway evidence
- M5 anomaly evidence
- disk-capacity utilization

The result contains:

- impact score from 0–100
- LOW / MEDIUM / HIGH impact level
- evidence basis
- observed supporting metrics
- confidence

The score is not presented as a guaranteed speedup because the project does not yet benchmark each storage device's performance ceiling.

### 5. Historical integration

M6 is attached after M5 analysis. New snapshots saved by the existing monitoring pipeline therefore contain:

- M4 `root_cause`
- M5 `process_behavior`
- M6 `recommendations`

### 6. Recommendation report CLI

Use:

```bash
python -m reporting.recommendation_report
```

Machine-readable output:

```bash
python -m reporting.recommendation_report --json
```

Custom history file:

```bash
python -m reporting.recommendation_report --history-file logs/my-history.jsonl
```

### 7. Configuration

M6 adds:

- `RECOMMENDATION_MAX_ITEMS`
- `RECOMMENDATION_MIN_ROOT_CAUSE_CONFIDENCE`
- `RECOMMENDATION_MEDIUM_IMPACT_SCORE`
- `RECOMMENDATION_HIGH_IMPACT_SCORE`

### 8. Tests

`tests/test_m6_integration.py` covers:

- no-evidence behavior
- capacity-pressure recommendations
- runaway recommendation priority
- impact estimation
- cause-specific actions
- low-confidence gating
- advisory-only safety behavior
- M5→M6 attachment
- historical persistence

## Completion criteria

M6 is complete when recommendations are evidence-backed, ranked, safety-labelled, impact-estimated, persisted with snapshots, and accessible as a standalone report without making automatic system changes.

All criteria are implemented.
