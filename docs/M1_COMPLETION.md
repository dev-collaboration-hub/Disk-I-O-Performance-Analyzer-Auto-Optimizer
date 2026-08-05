# M1 — Disk Monitoring Foundation

M1 delivers a complete, cross-platform command-line monitoring foundation.

## Delivered

- Mounted disk discovery through `psutil.disk_partitions`
- Total, used, free, and utilization metrics for every selected disk
- System-wide cumulative read/write bytes and operation counts
- Sampled read/write throughput and IOPS
- Structured JSON Lines metrics and event logging
- Live CLI dashboard with configurable refresh and sampling intervals
- One-shot mode for scripts and diagnostics
- Standard-library unit and end-to-end integration tests
- Graceful handling of inaccessible filesystems and unavailable I/O counters

## Run

```bash
python -m pip install -r requirements.txt
python main.py
```

One snapshot without clearing the screen:

```bash
python main.py --once --no-clear
```

Monitor a specific path:

```bash
python main.py --path / --once --no-clear
```

On Windows, for example:

```powershell
python main.py --path C:\ --once --no-clear
```

## Test

```bash
python -m unittest discover -s tests -v
```

## Acceptance verification

| M1 requirement | Verification |
|---|---|
| Disk discovery | `get_mounted_disks()` returns unique mount paths |
| Capacity | Total, used, and free byte values are exposed consistently |
| Usage percentage | `get_disk_usage_percentage()` and live snapshots report utilization |
| Read statistics | Cumulative bytes/operations and sampled rate are displayed |
| Write statistics | Cumulative bytes/operations and sampled rate are displayed |
| Logging | Every snapshot is persisted as one timestamped JSONL record |
| Dashboard | All M1 metrics render and refresh continuously |
| Integration | Automated tests cover collection, logging, and dashboard rendering |
