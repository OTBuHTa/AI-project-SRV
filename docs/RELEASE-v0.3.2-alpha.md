# v0.3.2-alpha

## Summary

v0.3.2-alpha fixes one-off database migration execution in the Docker Compose deployment workflow.

The API service uses a static address on the proxy network so the Web reverse proxy can remain restricted to the expected trusted proxy address.

Running `docker compose run api ...` inherited that static proxy address and collided with the already running API container.

This release introduces a dedicated migration tool service that runs only on the default internal network and does not inherit the API proxy address.

## Migration runner

The Compose configuration now includes a `migration` service under the `tools` profile.

The service:

- uses the API image build context;
- receives the existing environment configuration;
- waits for PostgreSQL health;
- runs `alembic upgrade head`;
- joins only the default Compose network;
- publishes no ports;
- has no static proxy address;
- does not modify the normal seven-service runtime topology.

The supported migration command is now:

`docker compose --profile tools run --rm --build migration`

The Makefile and Quick Start documentation use the same command.

## Proxy contract

The existing proxy network contract remains unchanged:

- Web: `172.30.0.2`;
- API: `172.30.0.3`;
- API `FORWARDED_ALLOW_IPS`: `172.30.0.2`.

The migration runner is not attached to the proxy network.

## Backend contracts

No API endpoint, authentication, workspace isolation, RBAC, Policy Engine, approval, agent execution or audit contract is changed.

No Web mutation is introduced.

## Runtime

No Alembic revision is added.

Database head remains `0021_worker_operational_state`.

No application dependency is added.

The normal runtime remains seven services; the migration runner is opt-in through the `tools` profile.

## Release identity

- API version: `0.3.2-alpha`
- Python package version: `0.3.2a0`
