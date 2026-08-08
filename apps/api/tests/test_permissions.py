from app.core.permissions import has_permission
from app.models.core import Role


def test_viewer_cannot_execute_resource():
    assert not has_permission(Role.VIEWER.value, "resource.execute")


def test_operator_can_execute_resource():
    assert has_permission(Role.OPERATOR.value, "resource.execute")


def test_org_owner_has_all_permissions():
    assert has_permission(Role.ORGANIZATION_OWNER.value, "future.permission")
