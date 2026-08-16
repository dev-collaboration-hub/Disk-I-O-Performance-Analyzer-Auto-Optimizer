# Release Checklist

## Source and metadata
- [x] M1–M10 completion documents present.
- [x] Stable version is `1.0.0`.
- [x] `pyproject.toml` defines Python/runtime requirements and console entry points.
- [x] Changelog and security policy are present.
- [x] Production deployment guide is present.

## Validation
- [x] M10 release tests validate metadata and release files.
- [x] Release-check script runs compile and unit-test gates.
- [x] CI matrix covers Python 3.10–3.13.
- [x] CI builds wheel and source distribution.
- [x] Tag workflow validates and builds release artifacts.

## Safety
- [x] M7 remains opt-in and dry-run by default.
- [x] Automatic action scope remains reversible process-priority mitigation.
- [x] Rollback journal remains part of the production boundary.
- [x] Security-sensitive extension policy is documented.

## Publication
A Git tag `v1.0.0` is the publication trigger. The release workflow builds the distribution and creates the GitHub release from that tag.

The repository connector used to prepare M10 does not expose tag/release creation; therefore source readiness and publication automation are committed, while the tag itself must be created through a Git-capable client or GitHub UI.
