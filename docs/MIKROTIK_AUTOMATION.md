# MikroTik Automation

AI-project SRV can monitor a MikroTik RouterOS 7 device through the RouterOS REST API and expose a deliberately small recovery surface.

## Security model

- The browser never connects to RouterOS directly.
- RouterOS credentials exist only in the server environment.
- HTTPS is mandatory for the RouterOS REST endpoint.
- TLS certificate verification is enabled by default.
- Read access and write access are separate.
- Write operations are disabled by default.
- No arbitrary RouterOS command endpoint is exposed.
- The first write operation is restricted to renewing an existing DHCP client lease.
- The DHCP client is resolved by interface name and the RouterOS internal ID is looked up server-side before the renew command is sent.
- Every successful recovery action is appended to the existing AI-project SRV audit log.

## RouterOS preparation

Create a dedicated RouterOS user for AI-project SRV. For the current integration the account needs RouterOS `rest-api` and `read` policies. Add `write` only when the allowlisted recovery action is intentionally enabled. User-management rights are not required.

Do not use RouterOS default `read` or `write` groups for automation because those groups include additional login and diagnostic capabilities. Create a dedicated group instead:

```routeros
/user group
add name=ai-srv policy=read,rest-api
```

When write recovery is intentionally enabled, update the group to:

```routeros
/user group
set [find name="ai-srv"] policy=read,write,rest-api
```

Restrict the service account to the AI-project SRV host wherever possible:

```routeros
/user
set [find name="gpt"] group=ai-srv address=<AI_SRV_HOST_IP>/32
```

Enable `www-ssl` and use a certificate trusted by the AI-project SRV host. On RouterOS versions that expose `available-from` in `/ip service`, use that field instead of the deprecated `address` field:

```routeros
/ip service
set [find name="www-ssl"] available-from=<AI_SRV_HOST_IP>/32 certificate=<SERVER_CERTIFICATE> disabled=no
```

Do not expose RouterOS REST directly to the public Internet. The public WAN HTTPS port is not required for this integration; AI-project SRV should connect directly to the router's LAN management address.

## Server configuration

Add these values to the deployment environment:

```env
MIKROTIK_ENABLED=true
MIKROTIK_BASE_URL=https://192.168.88.1
MIKROTIK_USERNAME=ai-srv
MIKROTIK_PASSWORD=replace-me
MIKROTIK_VERIFY_TLS=true
MIKROTIK_TIMEOUT_SECONDS=5
MIKROTIK_ALLOW_WRITE=false
MIKROTIK_WAN_INTERFACE=ether1
MIKROTIK_EXPECTED_WAN_IP=
```

`MIKROTIK_EXPECTED_WAN_IP` is optional. When set locally, the status endpoint reports whether the DHCP-derived WAN address matches the expected value. Do not place site-specific addresses or credentials in the committed example files.

Start with `MIKROTIK_ALLOW_WRITE=false`. The Infrastructure page will provide monitoring while mutating recovery operations remain blocked.

After validating monitoring and the RouterOS account permissions, set:

```env
MIKROTIK_ALLOW_WRITE=true
```

This enables only the allowlisted recovery actions implemented by the API.

## Runtime preflight

Run the preflight from the API environment after the local secret is configured:

```bash
cd apps/api
python scripts/mikrotik_preflight.py
```

A healthy result is `PASS`. The preflight fails when the default route is missing, the configured WAN interface is down, WAN DHCP is not bound, or a configured expected WAN IP no longer matches.

## API

- `GET /api/v1/mikrotik/status`
- `GET /api/v1/mikrotik/snapshot`
- `POST /api/v1/mikrotik/actions/dhcp-renew`

The write endpoint requires the AI-project SRV `network.execute` permission in addition to `MIKROTIK_ALLOW_WRITE=true`.

## Current scope

The initial integration reads:

- system identity and resource state;
- interfaces;
- IP addresses;
- routes;
- DHCP clients;
- DNS state;
- configured WAN link and DHCP state;
- optional expected-WAN-IP drift state.

The initial recovery action renews an already-configured RouterOS DHCP client. Firewall changes, route creation, service changes, user management, configuration imports, reboots, and arbitrary scripts are intentionally not exposed.
