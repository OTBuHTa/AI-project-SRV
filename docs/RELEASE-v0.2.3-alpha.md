# v0.2.3-alpha

## Summary
Adds verifiable runtime build identity across the API and API-based workers, embeds Git revision metadata into Docker images, and rejects unidentified production runtime artifacts.

## Changes
- exposes API version and build revision through `/health`
- exposes build revision alongside the existing API version through `/api/v1`
- adds `APP_BUILD_REVISION` runtime configuration with a development-safe `unknown` default
- propagates a single build revision into all four API-based Docker images
- embeds the build revision in container environment metadata
- adds the OCI `org.opencontainers.image.revision` label to API-based images
- preserves a common revision across the API, backup scheduler, backup alert delivery worker, and agent lifecycle alert delivery worker
- adds a production-only runtime build identity validator
- requires production build revisions to be full 40-character lowercase Git SHA values
- keeps development runtime compatible with an unknown build revision
- applies the production build identity guard to FastAPI startup and all three long-running API-based workers
- keeps production environment-file preflight independent from image build metadata

## Validation
- full API suite: 344 passed
- runtime identity tests passed
- production startup security tests passed
- worker build identity wiring tests passed
- production preflight regression tests passed
- CI-equivalent critical Ruff checks passed
- default Docker Compose configuration validates successfully
- all four API-based images built successfully with the same Git revision
- OCI revision labels match the expected Git revision on all four images
- container `APP_BUILD_REVISION` values match the expected Git revision on all four services
- `/health`, `/api/v1`, and the Web reverse proxy expose the running build revision
- API runtime settings match the deployed image revision
- backup scheduler, backup alert delivery, and agent lifecycle alert delivery workers start successfully
- default runtime remains on host ports 8000 and 8080
- ports 80 and 443 remain inactive in the default deployment
- fresh API and worker logs contain no recent runtime errors
- git diff --check passed

## Runtime / database
- runtime/API version: `0.2.3-alpha`
- Python package version: `0.2.3a0`
- build identity is represented by a full Git commit SHA
- default development builds may use `unknown` when no build revision is supplied
- production runtime requires a valid full lowercase Git SHA
- no API dependency changes
- no database migration
- Alembic head remains `0021_worker_operational_state`
