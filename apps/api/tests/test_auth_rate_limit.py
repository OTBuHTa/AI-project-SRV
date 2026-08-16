from unittest.mock import Mock

from app.services.auth_rate_limit import (
    _account_key,
    account_fingerprint,
    _ip_key,
    clear_account_login_failures,
    login_rate_limit_exceeded,
    record_failed_login,
)


def test_rate_limit_keys_do_not_expose_raw_identity():
    ip = "192.0.2.10"
    email = "User@example.com"

    ip_key = _ip_key(ip)
    account_key = _account_key(email)

    assert ip not in ip_key
    assert email.lower() not in account_key
    assert "user@example.com" not in account_key


def test_rate_limit_detects_ip_limit():
    redis = Mock()
    redis.get.side_effect = [b"20"]

    assert login_rate_limit_exceeded(
        redis,
        source_ip="192.0.2.10",
        email="user@example.com",
        ip_limit=20,
        account_limit=10,
    )


def test_rate_limit_detects_account_limit():
    redis = Mock()
    redis.get.side_effect = [b"0", b"10"]

    assert login_rate_limit_exceeded(
        redis,
        source_ip="192.0.2.10",
        email="user@example.com",
        ip_limit=20,
        account_limit=10,
    )


def test_rate_limit_allows_below_limits():
    redis = Mock()
    redis.get.side_effect = [b"3", b"4"]

    assert not login_rate_limit_exceeded(
        redis,
        source_ip="192.0.2.10",
        email="user@example.com",
        ip_limit=20,
        account_limit=10,
    )


def test_failed_login_records_ip_and_account():
    redis = Mock()
    pipeline = redis.pipeline.return_value

    record_failed_login(
        redis,
        source_ip="192.0.2.10",
        email="user@example.com",
        window_seconds=300,
    )

    assert pipeline.incr.call_count == 2
    assert pipeline.expire.call_count == 2
    assert pipeline.execute.call_count == 2


def test_success_clears_only_account_failures():
    redis = Mock()

    clear_account_login_failures(
        redis,
        email="user@example.com",
    )

    redis.delete.assert_called_once_with(
        _account_key("user@example.com")
    )

    deleted_key = redis.delete.call_args.args[0]

    assert deleted_key != _ip_key("192.0.2.10")
    assert "user@example.com" not in deleted_key



def test_account_fingerprint_is_normalized_and_stable():
    left = account_fingerprint(
        " User@Example.com "
    )
    right = account_fingerprint(
        "user@example.com"
    )

    assert left == right
    assert len(left) == 64
    assert "user@example.com" not in left
