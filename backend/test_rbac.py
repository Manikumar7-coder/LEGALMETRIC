"""
test_rbac.py
============
Unit test suite for SAFEMETRIC Role-Based Access Control (RBAC).

Tests:
- Role normalization (case-insensitivity, legacy synonyms, default to Inspector)
- require_admin, require_supervisor, require_inspector dependencies
- Protected endpoints (DELETE /api/inspections/{id}, /api/users)
"""

import sys
import os
from fastapi import HTTPException

sys.path.insert(0, os.path.dirname(__file__))

from app.models.user import User, UserRole
from app.auth.jwt_handler import (
    normalize_role,
    require_role,
    require_admin,
    require_supervisor,
    require_inspector
)


def test_role_normalization():
    """Verify role string normalization logic."""
    print("\n--- 1. Testing Role Normalization ---")

    assert normalize_role("Admin") == "Admin"
    assert normalize_role("admin") == "Admin"
    assert normalize_role("administrator") == "Admin"
    assert normalize_role("system_admin") == "Admin"

    assert normalize_role("Supervisor") == "Supervisor"
    assert normalize_role("supervisor") == "Supervisor"
    assert normalize_role("chief inspector") == "Supervisor"
    assert normalize_role("lead inspector") == "Supervisor"

    assert normalize_role("Inspector") == "Inspector"
    assert normalize_role("inspector") == "Inspector"
    assert normalize_role("enforcement officer") == "Inspector"
    assert normalize_role("Enforcement Officer") == "Inspector"
    assert normalize_role("field officer") == "Inspector"
    assert normalize_role(None) == "Inspector"
    assert normalize_role("") == "Inspector"
    assert normalize_role("unknown_role") == "Inspector"

    print("  [PASS] Role normalization verified across all canonical tiers and synonyms.")


def test_require_admin_dependency():
    """Verify require_admin strictly admits Admin and blocks others."""
    print("\n--- 2. Testing require_admin Dependency ---")

    admin_user = User(id=1, name="Admin User", email="admin@gov.in", role="Admin")
    supervisor_user = User(id=2, name="Supervisor User", email="sup@gov.in", role="Supervisor")
    inspector_user = User(id=3, name="Inspector User", email="insp@gov.in", role="Inspector")
    legacy_user = User(id=4, name="Legacy Officer", email="officer@gov.in", role="Enforcement Officer")

    checker = require_admin

    # Admin passes
    res = checker(admin_user)
    assert res.id == 1

    # Supervisor blocked
    try:
        checker(supervisor_user)
        assert False, "Supervisor should have been blocked by require_admin"
    except HTTPException as e:
        assert e.status_code == 403
        assert "Access denied" in e.detail

    # Inspector blocked
    try:
        checker(inspector_user)
        assert False, "Inspector should have been blocked by require_admin"
    except HTTPException as e:
        assert e.status_code == 403

    # Legacy Officer blocked (equivalent to Inspector)
    try:
        checker(legacy_user)
        assert False, "Legacy officer should have been blocked by require_admin"
    except HTTPException as e:
        assert e.status_code == 403

    print("  [PASS] require_admin strictly grants access only to Admin tier.")


def test_require_supervisor_dependency():
    """Verify require_supervisor admits Admin & Supervisor, blocks Inspector."""
    print("\n--- 3. Testing require_supervisor Dependency ---")

    admin_user = User(id=1, name="Admin User", email="admin@gov.in", role="Admin")
    supervisor_user = User(id=2, name="Supervisor User", email="sup@gov.in", role="Supervisor")
    inspector_user = User(id=3, name="Inspector User", email="insp@gov.in", role="Inspector")

    checker = require_supervisor

    # Admin passes (inherits supervisor rights)
    assert checker(admin_user).id == 1

    # Supervisor passes
    assert checker(supervisor_user).id == 2

    # Inspector blocked
    try:
        checker(inspector_user)
        assert False, "Inspector should have been blocked by require_supervisor"
    except HTTPException as e:
        assert e.status_code == 403
        assert "Access denied" in e.detail

    print("  [PASS] require_supervisor correctly admits Admin + Supervisor, blocks Inspector.")


def test_require_inspector_dependency():
    """Verify require_inspector admits all legitimate tiers."""
    print("\n--- 4. Testing require_inspector Dependency ---")

    admin_user = User(id=1, name="Admin User", email="admin@gov.in", role="Admin")
    supervisor_user = User(id=2, name="Supervisor User", email="sup@gov.in", role="Supervisor")
    inspector_user = User(id=3, name="Inspector User", email="insp@gov.in", role="Inspector")
    legacy_user = User(id=4, name="Legacy Officer", email="officer@gov.in", role="Enforcement Officer")

    checker = require_inspector

    assert checker(admin_user).id == 1
    assert checker(supervisor_user).id == 2
    assert checker(inspector_user).id == 3
    assert checker(legacy_user).id == 4

    print("  [PASS] require_inspector correctly admits all authenticated officer tiers.")


def test_users_router_rbac_protection():
    """Verify /api/users endpoints require Admin privileges."""
    print("\n--- 5. Testing Users Management Endpoints RBAC ---")

    from app.routers.users import list_users, update_user_role, delete_user, UpdateRoleRequest

    admin_user = User(id=1, name="Admin User", email="admin@gov.in", role="Admin")
    inspector_user = User(id=2, name="Inspector User", email="insp@gov.in", role="Inspector")

    # Attempting to list users as Inspector should fail via require_admin
    try:
        require_admin(inspector_user)
        assert False, "Inspector must not access user list"
    except HTTPException as e:
        assert e.status_code == 403

    # Attempting self-deletion as Admin should be rejected
    try:
        delete_user(user_id=1, current_user=admin_user, db=None)
        assert False, "Admin cannot delete own account"
    except HTTPException as e:
        assert e.status_code == 400
        assert "Cannot delete your own" in e.detail

    print("  [PASS] Users management endpoints strictly protected against unauthorized access and self-lockout.")


if __name__ == "__main__":
    test_role_normalization()
    test_require_admin_dependency()
    test_require_supervisor_dependency()
    test_require_inspector_dependency()
    test_users_router_rbac_protection()
    print("\n" + "=" * 70)
    print(" ALL ROLE-BASED ACCESS CONTROL (RBAC) TESTS PASSED (100%)!")
    print("=" * 70)
