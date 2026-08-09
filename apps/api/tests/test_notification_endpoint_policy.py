from unittest.mock import patch

import pytest

from app.services.notification_endpoint_policy import (
    NotificationEndpointPolicyError,
    validate_notification_endpoint,
)


def test_accepts_public_https_endpoint():
    with patch(
        "app.services.notification_endpoint_policy.socket.getaddrinfo",
        return_value=[
            (
                2,
                1,
                6,
                "",
                ("93.184.216.34", 443),
            )
        ],
    ):
        result = validate_notification_endpoint(
            "https://example.com/webhook"
        )

    assert result == "https://example.com/webhook"


@pytest.mark.parametrize(
    "url",
    [
        "file:///tmp/webhook",
        "ftp://example.com/webhook",
        "javascript:alert(1)",
    ],
)
def test_rejects_unsupported_scheme(url):
    with pytest.raises(NotificationEndpointPolicyError):
        validate_notification_endpoint(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/hook",
        "http://[::1]/hook",
        "http://169.254.169.254/latest/meta-data",
        "http://0.0.0.0/hook",
    ],
)
def test_rejects_special_addresses(url):
    with pytest.raises(NotificationEndpointPolicyError):
        validate_notification_endpoint(url)


def test_rejects_private_ip_by_default():
    with pytest.raises(NotificationEndpointPolicyError):
        validate_notification_endpoint(
            "http://192.168.1.10/hook"
        )


def test_allows_private_ip_when_explicitly_enabled():
    result = validate_notification_endpoint(
        "http://192.168.1.10/hook",
        allow_private_networks=True,
    )

    assert result == "http://192.168.1.10/hook"


def test_rejects_userinfo():
    with pytest.raises(NotificationEndpointPolicyError):
        validate_notification_endpoint(
            "https://user:secret@example.com/hook",
            resolve_hostname=False,
        )


def test_rejects_fragment():
    with pytest.raises(NotificationEndpointPolicyError):
        validate_notification_endpoint(
            "https://example.com/hook#secret",
            resolve_hostname=False,
        )


def test_rejects_hostname_resolving_to_private_ip():
    with patch(
        "app.services.notification_endpoint_policy.socket.getaddrinfo",
        return_value=[
            (
                2,
                1,
                6,
                "",
                ("10.10.0.5", 443),
            )
        ],
    ):
        with pytest.raises(NotificationEndpointPolicyError):
            validate_notification_endpoint(
                "https://internal.example/hook"
            )


def test_allows_hostname_resolving_to_private_when_enabled():
    with patch(
        "app.services.notification_endpoint_policy.socket.getaddrinfo",
        return_value=[
            (
                2,
                1,
                6,
                "",
                ("10.10.0.5", 443),
            )
        ],
    ):
        result = validate_notification_endpoint(
            "https://internal.example/hook",
            allow_private_networks=True,
        )

    assert result == "https://internal.example/hook"
