# ADR-015 — Backup observability and alerting

## Decision

AI-project SRV exposes read-only backup protection status derived from existing backup jobs, artifacts, and schedules.

The observability layer evaluates:

- age of the latest restore-verified backup
- recent backup failures
- scheduler lag
- presence or absence of verified protection
- active backup alerts

No new persistence model is required for this release.

## Status levels

Backup protection uses three states:

- healthy
- degraded
- failed

A missing restore-verified backup is failed.

A stale verified backup, scheduler lag, or recent backup failure produces degraded status.

## Failure window

Backup failures are evaluated within a bounded recent time window rather than across all historical jobs.

The default failure window is 24 hours.

## Alerts

Read-only alerts are generated from the evaluated backup status.

Alert codes include:

- backup_missing
- backup_stale
- scheduler_lag
- recent_failures

Alerts do not directly trigger mutations or remediation actions.

## Protection summary

The protection endpoint exposes a compact representation suitable for AI and operator interfaces.

A workspace is considered protected only when:

- overall status is healthy
- a restore-verified backup exists
- no active degradation condition is present

## Security

All observability endpoints require workspace.read permission.

The observability layer is advisory and read-only.
