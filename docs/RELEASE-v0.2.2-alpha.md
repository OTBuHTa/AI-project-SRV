# v0.2.2-alpha

## Summary
Hardens the production runtime trust boundary, realtime WebSocket behavior, production configuration preflight, and opt-in TLS deployment path without changing the default LAN development runtime.

## Changes
- hardens WebSocket pre-authentication disconnect handling so early client disconnects terminate cleanly without secondary close errors
- disables the duplicate Uvicorn Date header while preserving a single valid WebSocket handshake Date header
- introduces a dedicated Docker reverse-proxy network with fixed Web and API proxy addresses
- restricts Uvicorn forwarded-header trust to the dedicated Nginx proxy address
- overwrites client-supplied X-Forwarded-For headers at Nginx instead of extending untrusted forwarded chains
- applies the same proxy trust boundary to API, health, readiness, and WebSocket traffic
- strengthens production JWT validation by rejecting known example/default secrets and secrets shorter than 32 bytes
- adds a fail-closed production environment preflight that reuses the API production security policy
- adds an executable production preflight CLI with automatic project virtual-environment selection
- ignores real environment-specific .env files while keeping example templates trackable
- adds a production environment template with explicit production security controls
- allows Compose services to select an environment file through AI_SRV_ENV_FILE while preserving .env as the default
- adds an opt-in TLS Compose profile with external read-only certificate and private-key mounts
- adds Nginx HTTP-to-HTTPS redirect, TLS 1.2/1.3 termination, HTTPS/WSS proxying, and HSTS on the TLS deployment path
- replaces the Web 8080 publication with ports 80 and 443 only when the TLS override is explicitly enabled
- documents DNS, certificate, preflight, firewall, and TLS activation requirements

## Validation
- full API suite: 331 passed
- production security/preflight suite: 18 passed
- direct production preflight rejects the incomplete production template with the expected security validation error
- direct production preflight accepts a hardened temporary production environment
- Web ESLint checks passed
- Web TypeScript/Vite production build passed
- default Docker Compose configuration validates successfully
- opt-in TLS Compose configuration validates successfully
- TLS override removes Web port 8080 and publishes only ports 80 and 443
- TLS Nginx configuration test passed with an isolated temporary test certificate
- reverse-proxy spoof test confirms client-supplied X-Forwarded-For is not trusted
- production WebSocket proxy returns HTTP 101 after runtime hardening
- /ready reports database and Redis healthy
- default Web runtime remains healthy on LAN port 8080
- fresh API/Web logs contain no recent runtime errors
- git diff --check passed

## Runtime / database
- runtime/API version: `0.2.2-alpha`
- Python package version: `0.2.2a0`
- default Web runtime remains Nginx on container port 80, published on host port 8080
- TLS deployment remains opt-in and is not activated without a real DNS name, certificate material, and firewall preparation
- API host port 8000 remains published for existing clients and is not migrated in this release
- no API dependency changes
- no database migration
- Alembic head remains `0021_worker_operational_state`
