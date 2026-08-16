# Security Policy

## Supported release

The current supported stable line is **1.0.x**.

## Reporting a vulnerability

Please report security issues privately to the repository maintainers using GitHub's private security-reporting mechanism when it is enabled. Do not publish exploit details in a public issue before maintainers have had a reasonable opportunity to investigate.

Include the affected version, operating system, reproduction steps, expected/actual behavior, and whether the issue can cause an unintended system mutation.

## Safety-sensitive areas

The highest-risk code is under `optimizer/`. M7 is intentionally constrained to a reversible process-priority change after live PID/name/creation-time verification, policy gating, protected-process checks, and rollback-state capture.

Changes that add process termination, file deletion, service mutation, security configuration changes, database tuning, filesystem mutation, or storage-device configuration require a new explicit safety design and tests. They must not be added as silent extensions of the existing M7 action.

## Secrets and telemetry

The project stores monitoring data locally in JSONL files. Operators should treat process names, PIDs, file paths, timestamps, and operational events as potentially sensitive host telemetry and protect exported logs accordingly.
