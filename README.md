# Disk I/O Performance Analyzer & Auto Optimizer

Cross-platform disk diagnostics, historical analysis, root-cause detection, process behavior analysis, recommendations, reversible mitigation, and proactive alerting.

## Milestone status

- **M1 — Disk Monitoring Foundation: complete**
- **M2 — Process-Level Disk Analysis: complete**
- **M3 — Historical Data Collection: complete**
- **M4 — Root Cause Detection Engine: complete**
- **M5 — Process Behavior Analysis: complete**
- **M6 — Recommendation Engine: complete**
- **M7 — Auto Optimization Engine: complete**
- **M8 — Alerting & Notifications: complete**

M8 adds stateful real-time alerts, cooldown/deduplication, severity escalation, recovery notifications, persistent alert history, active-alert reconstruction, M7 operational events, dashboard integration, and standalone alert reporting.

## Quick start

```bash
python -m pip install -r requirements.txt
python main.py
python main.py --once --no-clear
```

## M8 alerts

```bash
python -m reporting.alert_report
python -m reporting.alert_report --active
python -m reporting.alert_report --json
```

Lifecycle:
- first active observation → `TRIGGERED`
- higher severity → `ESCALATED`
- same unresolved state after cooldown → `REMINDER`
- condition disappears after being evaluated → `RECOVERED`

Alert history is stored separately in `logs/alerts.jsonl`.

## M7 safe optimization

```bash
python -m reporting.optimization_report
python -m reporting.optimization_report --apply
python -m reporting.optimization_report --rollback-last
```

M7 apply/failure/rollback outcomes are written to the M8 alert stream; dry-run planning is not reported as an executed action.

## Completion reports

`docs/M1_COMPLETION.md` through `docs/M8_COMPLETION.md`.

## Tests

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
```

## Roadmap

M1 ✅ · M2 ✅ · M3 ✅ · M4 ✅ · M5 ✅ · M6 ✅ · M7 ✅ · M8 ✅

### M9 — Reporting & Analytics
- Trend analysis
- Usage reports

### M10 — Production Release
- Packaging
- Stable release
- Production documentation

## Technology

Python 3.10+, `psutil`, `unittest`, standard-library JSON/JSONL persistence.

## License

License to be determined.
