import ipaddress
import socket
from urllib.parse import urlsplit


class NotificationEndpointPolicyError(ValueError):
    pass


def _validate_ip_address(
    address: str,
    *,
    allow_private_networks: bool,
) -> None:
    ip = ipaddress.ip_address(address)

    if ip.is_loopback:
        raise NotificationEndpointPolicyError(
            "loopback notification endpoints are not allowed"
        )

    if ip.is_link_local:
        raise NotificationEndpointPolicyError(
            "link-local notification endpoints are not allowed"
        )

    if ip.is_multicast:
        raise NotificationEndpointPolicyError(
            "multicast notification endpoints are not allowed"
        )

    if ip.is_unspecified:
        raise NotificationEndpointPolicyError(
            "unspecified notification endpoints are not allowed"
        )

    if ip.is_reserved:
        raise NotificationEndpointPolicyError(
            "reserved notification endpoints are not allowed"
        )

    if ip.is_private and not allow_private_networks:
        raise NotificationEndpointPolicyError(
            "private notification endpoints are not allowed"
        )


def validate_notification_endpoint(
    url: str,
    *,
    allow_private_networks: bool = False,
    resolve_hostname: bool = True,
) -> str:
    parsed = urlsplit(url)

    if parsed.scheme not in {"http", "https"}:
        raise NotificationEndpointPolicyError(
            "notification endpoint must use http or https"
        )

    if not parsed.hostname:
        raise NotificationEndpointPolicyError(
            "notification endpoint hostname is required"
        )

    if parsed.username is not None or parsed.password is not None:
        raise NotificationEndpointPolicyError(
            "notification endpoint userinfo is not allowed"
        )

    if parsed.fragment:
        raise NotificationEndpointPolicyError(
            "notification endpoint fragment is not allowed"
        )

    hostname = parsed.hostname

    try:
        _validate_ip_address(
            hostname,
            allow_private_networks=allow_private_networks,
        )
        return url

    except ValueError:
        pass

    if not resolve_hostname:
        return url

    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(
                hostname,
                parsed.port or (
                    443
                    if parsed.scheme == "https"
                    else 80
                ),
                type=socket.SOCK_STREAM,
            )
        }
    except socket.gaierror as exc:
        raise NotificationEndpointPolicyError(
            "notification endpoint hostname cannot be resolved"
        ) from exc

    if not addresses:
        raise NotificationEndpointPolicyError(
            "notification endpoint hostname cannot be resolved"
        )

    for address in addresses:
        _validate_ip_address(
            address,
            allow_private_networks=allow_private_networks,
        )

    return url
