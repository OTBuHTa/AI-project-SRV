# v0.2.4-alpha

## Summary
Hardens CI build provenance by verifying that Docker image identity and Docker Compose build wiring remain bound to the exact checked-out Git revision.

## Changes
- adds a dedicated Docker build identity job to API CI
- resolves the exact checked-out Git revision after repository checkout
- builds the API Docker image with that revision as `APP_BUILD_REVISION`
- verifies the OCI `org.opencontainers.image.revision` label against the checked-out revision
- verifies the image `APP_BUILD_REVISION` environment value against the checked-out revision
- adds a reusable Docker Compose build identity verifier
- verifies build revision propagation across all four API-based services
- verifies the explicit `AI_SRV_BUILD_REVISION` Compose path
- verifies the development-safe `unknown` Compose fallback
- adds unit coverage for matching, mismatched, missing-service, and missing-build-args cases
- keeps provenance checks fail-closed in GitHub Actions

## Validation
- full API suite: 348 passed
- Compose build identity verifier tests: 4 passed
- explicit Compose build revision verification passed
- default Compose build revision fallback verification passed
- CI-equivalent critical Ruff checks passed
- Docker Compose configuration validated successfully
- GitHub Actions Docker build identity job passed
- GitHub Actions API test job passed
- Docker image OCI revision label matched the exact checked-out Git revision
- Docker image `APP_BUILD_REVISION` matched the exact checked-out Git revision
- Compose build identity wiring passed for all four API-based services
- git diff --check passed

## Runtime / database
- runtime/API version: `0.2.4-alpha`
- Python package version: `0.2.4a0`
- no dependency changes
- no database migration
- Alembic head remains `0021_worker_operational_state`
- no runtime service topology changes
- no firewall or TLS changes
