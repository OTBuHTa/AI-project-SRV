# v0.1.38-alpha

## Summary
Extends release metadata verification across the complete historical alpha release-note set while preserving supported legacy header formats.

## Changes
- validates version/header consistency for all matching historical release notes
- accepts the existing canonical and legacy release-note header formats
- rejects historical headers whose version does not match the filename
- preserves strict canonical `# vX.Y.Z-alpha` formatting for the current release
- adds regression coverage for supported legacy headers and historical mismatches
- advances runtime API version and README milestone to `0.1.38-alpha`

## Validation
- exact CI dependency baseline: 49 pins verified
- release metadata consistency verified
- historical release-note integrity verified
- full API suite: 322 passed
- pip check, compile, critical Ruff and whitespace checks passed

## Runtime / database
- runtime/API version: `0.1.38-alpha`
- package metadata remains unchanged
- no dependency changes
- no database migration
- Alembic head remains `0021_worker_operational_state`
- `/ready` semantics unchanged
