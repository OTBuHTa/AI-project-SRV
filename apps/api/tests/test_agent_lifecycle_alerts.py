from app.services.agent_lifecycle_alerts import (
    evaluate_agent_lifecycle_alerts,
)


def test_healthy_diagnostics_produce_no_alerts():
    alerts = evaluate_agent_lifecycle_alerts(
        {
            "expired_pending_rotations": 0,
            "incomplete_pending_rotations": 0,
            "revoked_with_pending_rotation": 0,
        }
    )

    assert alerts == []


def test_expired_rotation_produces_warning():
    alerts = evaluate_agent_lifecycle_alerts(
        {
            "expired_pending_rotations": 2,
            "incomplete_pending_rotations": 0,
            "revoked_with_pending_rotation": 0,
        }
    )

    assert len(alerts) == 1
    assert alerts[0].severity == "warning"
    assert alerts[0].code == "agent_token_rotation_expired"
    assert "2 expired" in alerts[0].message


def test_incomplete_rotation_produces_critical():
    alerts = evaluate_agent_lifecycle_alerts(
        {
            "expired_pending_rotations": 0,
            "incomplete_pending_rotations": 3,
            "revoked_with_pending_rotation": 0,
        }
    )

    assert len(alerts) == 1
    assert alerts[0].severity == "critical"
    assert alerts[0].code == "agent_token_rotation_incomplete"
    assert "3 agent token rotation" in alerts[0].message


def test_revoked_pending_rotation_produces_critical():
    alerts = evaluate_agent_lifecycle_alerts(
        {
            "expired_pending_rotations": 0,
            "incomplete_pending_rotations": 0,
            "revoked_with_pending_rotation": 1,
        }
    )

    assert len(alerts) == 1
    assert alerts[0].severity == "critical"
    assert alerts[0].code == "agent_revoked_pending_rotation"
    assert "1 revoked agent" in alerts[0].message


def test_multiple_lifecycle_issues_produce_separate_alerts():
    alerts = evaluate_agent_lifecycle_alerts(
        {
            "expired_pending_rotations": 2,
            "incomplete_pending_rotations": 1,
            "revoked_with_pending_rotation": 1,
        }
    )

    assert [
        (alert.code, alert.severity)
        for alert in alerts
    ] == [
        ("agent_token_rotation_expired", "warning"),
        ("agent_token_rotation_incomplete", "critical"),
        ("agent_revoked_pending_rotation", "critical"),
    ]


def test_unrelated_diagnostics_do_not_generate_alerts():
    alerts = evaluate_agent_lifecycle_alerts(
        {
            "status": "healthy",
            "agents_total": 20,
            "pending_rotations": 4,
            "expired_pending_rotations": 0,
            "incomplete_pending_rotations": 0,
            "revoked_with_pending_rotation": 0,
        }
    )

    assert alerts == []
