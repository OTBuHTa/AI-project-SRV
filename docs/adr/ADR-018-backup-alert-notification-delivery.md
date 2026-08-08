# ADR-018: Backup Alert Notification Delivery

## Status

Accepted

## Context

ADR-016 introduced persistent backup alert events.

ADR-017 made alert reconciliation safe under concurrent workers.

The next requirement is reliable operator notification delivery without coupling
network I/O to read-only APIs or to alert reconciliation itself.

The notification path must:

- persist delivery state;
- deduplicate delivery attempts per alert event and channel;
- support retries with backoff;
- survive worker crashes;
- allow concurrent workers without double-claiming the same delivery;
- keep notification delivery separate from acknowledgement and remediation.

## Decision

Introduce a persistent backup alert delivery queue and a dedicated delivery
worker.

Each delivery records:

- workspace;
- alert event;
- channel;
- status;
- attempt count;
- maximum attempts;
- next attempt timestamp;
- last attempt timestamp;
- delivered timestamp;
- last error;
- creation and update timestamps.

## Delivery identity

A delivery is uniquely identified by:

`(alert_event_id, channel)`

This prevents repeated reconciliation of the same active alert from creating
duplicate notification records.

## Delivery states

Supported delivery states are:

- `pending`
- `sending`
- `failed`
- `delivered`

Normal success flow:

`pending -> sending -> delivered`

Retry flow:

`pending -> sending -> failed -> sending -> delivered`

A delivery that reaches `max_attempts` remains failed and is not scheduled for
another attempt.

## Queue claiming

Workers claim due deliveries using PostgreSQL row locking:

`FOR UPDATE SKIP LOCKED`

This allows multiple workers to process the queue concurrently without waiting
on or double-claiming rows already locked by another worker.

## Retry and backoff

Failed delivery attempts use exponential backoff.

The initial backoff is 60 seconds and grows exponentially up to a maximum of
3600 seconds.

The queue stores `next_attempt_at` so retry timing survives process restarts.

## Stale sending recovery

A delivery may remain in `sending` if a worker crashes after claiming it but
before marking success or failure.

Sending deliveries older than the configured claim timeout are eligible to be
claimed again.

This prevents permanently orphaned queue records.

## Webhook transport

The initial transport channel is `webhook`.

Webhook delivery uses HTTP POST and includes:

- delivery ID;
- workspace ID;
- alert event ID;
- alert code;
- severity;
- message.

Transport failures are converted into queue failures and follow the normal
retry policy.

## Worker

A dedicated `backup-alert-delivery` service processes due delivery records.

The worker:

1. claims due deliveries;
2. loads the referenced alert event;
3. performs webhook delivery;
4. marks the delivery as delivered or failed;
5. records failure details and retry scheduling.

No notification network I/O is performed from GET API requests.

## Alert integration

When reconciliation creates a new persistent alert event, one webhook delivery
record is enqueued.

Existing active events do not create another delivery during repeated
reconciliation.

A resolved alert that later reopens as a new event receives a new delivery
record because it has a new alert event ID.

## Security and safety

Notification delivery is operational messaging only.

It does not:

- acknowledge alerts;
- resolve alerts;
- authorize actions;
- trigger automatic remediation.

The existing Policy Engine remains authoritative for mutating infrastructure
actions.

## Consequences

### Positive

- delivery state survives worker and process restarts;
- duplicate notifications are prevented at the database level;
- retries are bounded and observable;
- multiple delivery workers can safely share the queue;
- transient network failures do not lose notifications;
- alert reconciliation remains independent from network delivery.

### Trade-offs

- webhook delivery currently uses one configured endpoint;
- delivery semantics depend on PostgreSQL locking behavior;
- webhook delivery is at-least-once at the transport boundary if a worker
  crashes after the receiver accepts a request but before the database marks
  it delivered;
- webhook authentication and signing are not part of this release.

## Verification

Automated tests cover:

- idempotent enqueue;
- due delivery claiming;
- successful delivery;
- failure handling;
- exponential backoff;
- terminal failure;
- stale `sending` recovery;
- webhook transport success and error handling;
- delivery worker behavior;
- new-alert enqueue behavior;
- prevention of repeated enqueue for an existing active alert.

The full API test suite passes with:

`71 passed`

Real PostgreSQL and HTTP smoke tests confirmed:

- delivery enqueue deduplication;
- `pending -> sending`;
- failed transport and retry scheduling;
- retry claim;
- successful webhook delivery;
- final `delivered` state;
- two total attempts after one network failure;
- `delivered_at` persisted;
- `last_error` cleared after successful retry.

The tested end-to-end sequence was:

`pending -> sending -> failed -> retry -> sending -> delivered`
