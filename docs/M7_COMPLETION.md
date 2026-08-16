# M7 Completion — Auto Optimization Engine

## Status

**Complete**

M7 converts a narrow, high-confidence subset of M6 recommendations into reversible automatic mitigation actions.

The implementation is safety-first. It does **not** automatically delete files, kill or suspend processes, stop services, tune databases, change antivirus exclusions, or modify storage settings.

## Delivered

### 1. Automatic optimization planner

`optimizer/auto_optimizer.py` consumes M6 recommendations and creates a bounded M7 action plan.

Only recommendations that pass all M7 policy checks can become executable actions. The current automatic action is:

- `LOWER_PROCESS_PRIORITY`

This mitigation is intentionally reversible and non-destructive.

### 2. Strict safety gate

`optimizer/safety_guard.py` requires:

- sustained `RUNAWAY_PROCESS` evidence from M5
- HIGH or CRITICAL recommendation priority
- minimum M6 impact score
- valid PID
- target process name
- process creation time
- target not equal to the analyzer or its parent
- target not present in the system-process denylist

Immediately before mutation, M7 verifies the live process name + PID + creation time. This prevents a reused PID from receiving an action intended for an older process instance.

Capacity cleanup, one-sample anomalies, unknown investigation items, and other advisory recommendations are blocked from automatic execution.

### 3. Reversible priority mitigation

On POSIX systems, actual auto-apply is refused unless the optimizer has privilege to restore the original niceness. This check happens **before** mutation, preventing a one-way priority reduction that the rollback path could not safely reverse.

`optimizer/process_priority.py` lowers process scheduling priority:

- POSIX: increases niceness by the configured bounded step
- Windows: moves the process to below-normal priority when supported

Before changing priority M7 captures PID, process name, creation time, previous priority, and applied priority. The captured state becomes a rollback token.

### 4. Dry-run by default

`python -m reporting.optimization_report` builds and displays the safe M7 plan without changing the system.

Actual mutation requires explicit opt-in:

```bash
python -m reporting.optimization_report --apply
```

### 5. Transactional rollback protection

If an optimization session contains multiple actions and a later action fails, execution stops and previously applied actions are rolled back in reverse order. The report is marked `ROLLED_BACK_AFTER_FAILURE`.

### 6. Durable optimization journal

`optimizer/rollback_manager.py` writes structured JSONL records to `logs/optimization_journal.jsonl`.

The journal records session starts, applied actions, rollback tokens, and rollback completion.

### 7. Manual rollback of latest active session

```bash
python -m reporting.optimization_report --rollback-last
```

Rollback re-verifies PID + process name + creation time before restoring priority. A reused PID is never touched.

### 8. Configuration

M7 adds explicit configuration for maximum automatic actions per cycle, minimum impact score, priority-reduction step, optimization journal file, protected process denylist, and default disabled auto-apply state.

### 9. Tests

`tests/test_m7_integration.py` covers blocking non-runaway recommendations, low-impact rejection, same-instance planning, dry-run no-mutation behavior, rollback token persistence, transactional rollback after failure, reverse-order rollback, and protected system-process rejection.

## Safety boundary

M7 can reduce scheduling priority for a verified runaway process instance. It cannot terminate or suspend a process, delete files, clean caches automatically, stop/start services, change security software configuration, alter database configuration, or change filesystem/storage-device settings.

## Completion criteria

M7 is complete because the project now has automatic mitigation for a safety-approved class of M6 recommendations, explicit dry-run/apply separation, live process identity verification, protected-process safety checks, bounded action count, reversible state capture, automatic rollback on transaction failure, a durable rollback journal, an explicit rollback command, and integration tests for safety and recovery.
