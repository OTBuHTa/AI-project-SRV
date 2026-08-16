from unittest.mock import Mock

from app.services.auth_rate_limit import (
    _account_key,
    _ip_key,
    clear_login_failures,
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


def test_success_clears_ip_and_account_failures():
    redis = Mock()

    clear_login_failures(
        redis,
        source_ip="192.0.2.10",
        email="user@example.com",
    )

    redis.delete.assert_called_once()

    keys = redis.delete.call_args.args

    assert len(keys) == 2
    assert "192.0.2.10" not in keys[0]
    assert "user@example.com" not in keys[1]
