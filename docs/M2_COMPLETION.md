# M2 — Process-Level Disk Analysis Completion

## Status

Complete.

## Delivered capabilities

- Cross-platform process enumeration with stable, JSON-serializable metadata.
- Safe handling of inaccessible, terminated, and zombie processes.
- Cumulative per-process read/write byte and operation counters.
- Sampled per-process throughput and IOPS.
- PID reuse protection by matching both PID and process creation time.
- Top disk-consumer ranking based on activity in the current sample window.
- Process I/O share calculation.
- Integrated M2 dashboard and standalone process report.
- Structured JSONL snapshots containing process summary and top consumers.
- M1 regression tests and dedicated M2 integration tests.

## Design decision

Lifetime I/O totals are not used to decide which process is active now. M2 takes
two counter snapshots and ranks the positive deltas observed during the sampling
window. This prevents an old process with large historical counters from
incorrectly appearing as the current top consumer.

## Validation

Run:

```bash
python -m unittest discover -s tests -v
python -m compileall .
python main.py --once --no-clear --no-log
python -m reporting.process_report --sample-interval 0.2
```

## M2 acceptance mapping

| Milestone requirement | Implementation |
| --- | --- |
| Process enumeration | `monitoring/process_detector.py` |
| Per-process disk I/O tracking | `monitoring/process_io_monitor.py` |
| Top disk consumer identification | `monitoring/top_disk_consumers.py` |
| Reporting and integration | `reporting/process_report.py`, dashboard, tests |
