# AI-project SRV v0.1.12-alpha

## Backup alert notification delivery

v0.1.12-alpha adds reliable persistent notification delivery for backup alert
events.

The release introduces a PostgreSQL-backed delivery queue, retry scheduling,
crash recovery, concurrent worker claiming, and webhook delivery.

## Persistent delivery queue

Added `backup_alert_deliveries` with:

- workspace ID
- alert event ID
- channel
- status
- attempts
- maximum attempts
- next attempt timestamp
- last attempt timestamp
- delivered timestamp
- last error
- creation and update timestamps

A unique constraint on:

`(alert_event_id, channel)`

prevents duplicate delivery records for the same alert event and channel.

## Delivery states

Supported states:

- `pending`
- `sending`
- `failed`
- `delivered`

Successful flow:

`pending -> sending -> delivered`

Retry flow:

`pending -> sending -> failed -> sending -> delivered`

## Retry policy

Failed deliveries use exponential backoff.

Default behavior:

- first retry: 60 seconds
- subsequent retries: exponential growth
- maximum backoff: 3600 seconds
- maximum attempts: 5

Terminal failures remain failed and have no next attempt scheduled.

## Concurrent queue workers

Due deliveries are claimed using:

`FOR UPDATE SKIP LOCKED`

This allows multiple workers to process the queue without double-claiming the
same row.

## Crash recovery

Stale `sending` deliveries become claimable again after the claim timeout.

This prevents deliveries from becoming permanently stuck if a worker exits
after claiming a row.

## Webhook transport

Added HTTP webhook delivery using `httpx`.

Webhook payloads contain:

- delivery ID
- workspace ID
- alert event ID
- alert code
- severity
- message

Transport failures are recorded in `last_error` and follow the normal retry
policy.

## Delivery worker

Added a dedicated `backup-alert-delivery` Compose service.

The worker:

1. claims due deliveries;
2. loads the alert event;
3. performs the webhook POST;
4. records success or failure;
5. schedules retries when required.

Configuration:

- `BACKUP_ALERT_WEBHOOK_URL`
- `BACKUP_ALERT_WEBHOOK_TIMEOUT_SECONDS`

If no webhook URL is configured, the worker performs no delivery work.

## Alert integration

A new persistent backup alert event enqueues one webhook delivery.

Repeated reconciliation of an already-active alert does not enqueue another
delivery.

Reopened alerts create a new alert event and therefore a new delivery.

## Database migration

Added:

- `0011_backup_alert_deliveries`

The migration creates the delivery queue, indexes, foreign key to
`backup_alert_events`, and the event/channel uniqueness constraint.

## Validation

Automated tests cover:

- enqueue idempotency
- queue claiming
- retry transitions
- exponential backoff
- terminal failure
- stale sending recovery
- webhook transport
- worker success and failure paths
- alert-to-delivery integration

Full API test suite:

`71 passed`

## End-to-end smoke test

A real HTTP webhook delivery was tested through Docker networking.

The first delivery attempt intentionally failed with a connection timeout.

Database state after failure:

- status: `failed`
- attempts: `1`
- error persisted

The delivery was then retried against a reachable HTTP receiver.

Final database state:

- status: `delivered`
- attempts: `2`
- `delivered_at` populated
- `last_error` cleared

End-to-end result:

`pending -> sending -> failed -> retry -> sending -> delivered`

## Architecture

See:

- `ADR-016 — Persistent Backup Alert Events`
- `ADR-017 — Race-safe Backup Alert Reconciliation`
- `ADR-018 — Backup Alert Notification Delivery`

Notification delivery remains separate from acknowledgement, alert resolution,
and infrastructure remediation.
