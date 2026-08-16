# Production Deployment Guide

## Release

Stable source version: **1.0.0**

Supported Python: **3.10+**

Runtime dependency: `psutil>=5.9`

## Install from a checked-out release

```bash
python -m pip install .
```

For an isolated environment:

```bash
python -m venv .venv
# activate the environment for your platform
python -m pip install --upgrade pip
python -m pip install .
```

## Installed commands

```bash
disk-io-analyzer --help
disk-io-alerts --help
disk-io-analytics --help
disk-io-optimize --help
disk-io-recommendations --help
```

The original module commands remain supported.

## Recommended production posture

1. Start with monitoring/history enabled.
2. Keep M7 in dry-run mode until observed recommendations and protected-process rules are validated on the target host.
3. Use `disk-io-optimize --apply` only when automatic reversible mitigation is intentionally enabled by an operator.
4. Keep the optimization journal and alert history on a writable local path.
5. Apply operating-system permissions so untrusted users cannot alter monitoring, alert, or rollback records.
6. Size history/alert retention for the host and reporting horizon.
7. Back up operational logs only if required; they can contain sensitive host metadata.

## Validation before deployment

Install release tooling and run:

```bash
python -m pip install ".[release]"
python scripts/release_check.py
```

The release check validates metadata/version consistency, required release files, Python compilation, and the repository test suite.

For package build validation:

```bash
python -m build
```

## Upgrade

Before upgrading, preserve any JSONL files you need for historical continuity. Install the new version in the same environment and run the release checks applicable to the new release notes.

## Rollback

Application-code rollback is performed by reinstalling the previous known-good package/release. M7 runtime priority changes use their own rollback journal and `disk-io-optimize --rollback-last` path.

## Operational boundaries

M7 automatic mutation is intentionally limited. Production deployment does not turn capacity cleanup, process termination, service changes, security configuration changes, database tuning, or storage changes into automatic actions.
