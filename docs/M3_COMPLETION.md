# M3 — Historical Data Collection Completion

## Status

Complete.

## Delivered capabilities

- Append-only JSON Lines metrics history.
- Crash-tolerant readers that skip malformed or partial records.
- Legacy JSON-array history compatibility.
- Configurable snapshot and event retention.
- In-process caching and batched pruning to avoid full-file work every cycle.
- Structured persistent event timeline with filtering by type and severity.
- Disk-capacity utilization spike detection.
- Critical disk-utilization threshold crossing events.
- System-wide disk-throughput spike detection using a configurable multiplier and minimum rate.
- Disk status transition, collection warning, and top-consumer change events.
- Integrated M3 dashboard history section.
- Standalone historical report in text or JSON form.
- M1/M2 regression coverage and dedicated M3 tests.

## Storage files

Default runtime files:

- `logs/metrics_history.jsonl`
- `logs/event_timeline.jsonl`
- `logs/disk_monitor.jsonl` (existing operational log)

The history and event files use one JSON object per line. This permits append-only writes and recovery when the final line is incomplete.

## Spike rules

M3 records structured events when:

1. A disk's capacity utilization rises by the configured percentage-point threshold.
2. A disk crosses into critical capacity utilization.
3. Current system disk throughput is above the configured minimum and exceeds the previous sample by the configured multiplier.

All thresholds are available through CLI options and `config/settings.py`.

## Validation

Executed successfully:

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
python main.py --once --no-clear --no-log --sample-interval 0.05 \
  --history-file /tmp/m3-history.jsonl \
  --event-file /tmp/m3-events.jsonl
python -m reporting.history_report \
  --history-file /tmp/m3-history.jsonl \
  --event-file /tmp/m3-events.jsonl
```

Result: 24 tests passed, compilation passed, one-shot dashboard passed, and historical report generation passed.

## Scope boundary

M3 stores and organizes historical evidence. Root-cause classification remains part of M4; behavioral anomaly profiling remains part of M5; notification delivery remains part of M8.
