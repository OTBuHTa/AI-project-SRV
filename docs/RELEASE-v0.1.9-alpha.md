# AI-project SRV v0.1.9-alpha

## Backup observability

Added aggregated backup protection status with:

- healthy, degraded and failed states
- latest restore-verified backup timestamp
- verified backup age
- recent failed job count
- last failure timestamp
- scheduler lag

## Backup status API

Added:

- GET /api/v1/backups/status

The endpoint evaluates backup health for the current workspace.

## Backup alerts

Added:

- GET /api/v1/backups/alerts

Alert conditions include:

- missing restore-verified backup
- stale restore-verified backup
- scheduler lag
- recent backup failures

## Backup protection summary

Added:

- GET /api/v1/backups/protection

This provides a compact read-only representation suitable for operator and AI interfaces.

## Safety

- observability endpoints require workspace.read
- no automatic remediation is triggered
- alerts are derived from authoritative backup state
- historical failures outside the recent failure window do not permanently degrade protection status

## Validation

Automated tests cover:

- healthy protection
- missing backups
- stale backups
- scheduler lag
- recent failures
- expired failure-window events
- alert generation
- protection summary evaluation
