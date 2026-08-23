# TLS deployment profile

The TLS deployment profile is opt-in and does not change the default development runtime.

## Current development runtime

The default Compose deployment continues to publish:

- Web UI: TCP 8080
- API: TCP 8000

The TLS profile is activated only by adding `docker-compose.tls.yml`.

## Requirements

Before TLS activation:

- configure a trusted DNS/FQDN for the deployment;
- obtain a certificate whose SAN covers that name;
- keep the private key outside the Git repository;
- create a real `.env.production`;
- make the production security preflight pass;
- explicitly permit TCP 80 and 443 through the intended firewall boundary.

Do not use `.env.production.example` as a production environment file.

## Required TLS variables

Configure these values in `.env.production`:

```text
AI_SRV_ENV_FILE=.env.production
AI_SRV_SERVER_NAME=ai.example.com
AI_SRV_TLS_CERT_PATH=/absolute/path/to/fullchain.pem
AI_SRV_TLS_KEY_PATH=/absolute/path/to/privkey.pem
```

The certificate and private key are mounted read-only into the Web container.

## Production security preflight

Run `./scripts/production-preflight.py .env.production` before activation.

The preflight must succeed before the production deployment is started.

## Compose validation

Validate the merged deployment model before activation:

```bash
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.tls.yml config -q
```

The TLS override replaces the development Web publication on TCP 8080 with TCP 80 and TCP 443.

The TLS profile also restricts host-side API TCP 8000 to `127.0.0.1`. Nginx reaches the API through the internal Docker proxy network.

## Transport behavior

- TCP 80 redirects to HTTPS.
- TCP 443 terminates TLS and serves HTTPS/WSS.
- Nginx overwrites forwarded client-address headers.
- The API trusts forwarded headers only from the dedicated proxy address.
- HSTS is emitted only by the TLS deployment path.

## Activation

Activate only after DNS, certificates, production preflight, and firewall rules are ready:

```bash
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.tls.yml up -d --build
```

## Certificate handling

Production certificate and private-key material must never be committed to the repository.

The TLS profile accepts them only through external host paths:

- `AI_SRV_TLS_CERT_PATH`
- `AI_SRV_TLS_KEY_PATH`

Self-signed certificates may be used for isolated configuration tests but are not production trust material.
