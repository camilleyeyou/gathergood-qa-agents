"""Team management API tests: TTEAM-01 through TTEAM-04.

Tests multi-user permission boundaries for member invite, role restrictions,
listing, and removal within an organization.
"""
import httpx
import pytest

from factories.common import unique_email
from helpers.api import assert_status
from settings import Settings

_settings = Settings()


def _create_user_client(email=None, password="TestPass123!"):
    """Register a new user and return (email, authenticated httpx.Client).

    The caller is responsible for closing the returned client.
    """
    if email is None:
        email = unique_email()
    client = httpx.Client(base_url=_settings.API_URL, timeout=30)
    # Register
    reg = client.post("/auth/register/", json={
        "email": email,
        "password": password,
        "password_confirm": password,
        "first_name": "Team",
        "last_name": "Member",
    })
    assert reg.status_code == 201, f"Register failed: {reg.text[:200]}"
    # Login
    login = client.post("/auth/login/", json={"email": email, "password": password})
    assert login.status_code == 200, f"Login failed: {login.text[:200]}"
    tokens = login.json()
    client.close()
    # Return authenticated client
    authed = httpx.Client(
        base_url=_settings.API_URL,
        headers={"Authorization": f"Bearer {tokens['access']}"},
        timeout=30,
    )
    return email, authed


@pytest.mark.req("TTEAM-01")
def test_owner_can_invite_member(auth_client, org, teardown_registry):
    """OWNER can invite a registered user as VOLUNTEER (POST /members/invite/ → 201)."""
    email, extra_client = _create_user_client()
    try:
        resp = auth_client.post(
            f"/organizations/{org['slug']}/members/invite/",
            json={"email": email, "role": "VOLUNTEER"},
        )
        assert_status(resp, 201, "POST invite member (OWNER → VOLUNTEER)")
    finally:
        extra_client.close()


@pytest.mark.req("TTEAM-02")
def test_manager_cannot_assign_owner_role(auth_client, org, teardown_registry):
    """MANAGER cannot invite a user with role=OWNER (403); can invite as VOLUNTEER (201)."""
    # Create user A and invite as MANAGER
    email_a, client_a = _create_user_client()
    email_b, client_b = _create_user_client()
    try:
        # OWNER invites user A as MANAGER
        invite_a = auth_client.post(
            f"/organizations/{org['slug']}/members/invite/",
            json={"email": email_a, "role": "MANAGER"},
        )
        assert_status(invite_a, 201, "OWNER invites user A as MANAGER")

        # MANAGER tries to invite user B with role=OWNER (must fail)
        resp_owner = client_a.post(
            f"/organizations/{org['slug']}/members/invite/",
            json={"email": email_b, "role": "OWNER"},
        )
        assert_status(resp_owner, 403, "MANAGER cannot assign OWNER role")
        assert "Managers cannot assign the Owner role" in resp_owner.text, (
            f"Expected error message not found in: {resp_owner.text[:300]}"
        )

        # MANAGER CAN invite user B as VOLUNTEER (positive control)
        resp_volunteer = client_a.post(
            f"/organizations/{org['slug']}/members/invite/",
            json={"email": email_b, "role": "VOLUNTEER"},
        )
        assert_status(resp_volunteer, 201, "MANAGER can invite as VOLUNTEER")
    finally:
        client_a.close()
        client_b.close()


@pytest.mark.req("TTEAM-03")
def test_any_member_can_list_team(auth_client, org, teardown_registry):
    """Any org member (VOLUNTEER) can GET /members/ and see the member list (200)."""
    email, client_v = _create_user_client()
    try:
        # OWNER invites the new user as VOLUNTEER
        invite = auth_client.post(
            f"/organizations/{org['slug']}/members/invite/",
            json={"email": email, "role": "VOLUNTEER"},
        )
        assert_status(invite, 201, "OWNER invites VOLUNTEER for listing test")

        # VOLUNTEER lists team members
        resp = client_v.get(f"/organizations/{org['slug']}/members/")
        assert_status(resp, 200, "VOLUNTEER can list team members")

        data = resp.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}: {str(data)[:200]}"
        assert len(data) >= 2, (
            f"Expected at least OWNER + VOLUNTEER in list, got {len(data)}: {data}"
        )
        for member in data:
            assert "id" in member, f"Member missing 'id' field: {member}"
            assert "email" in member, f"Member missing 'email' field: {member}"
            assert "role" in member, f"Member missing 'role' field: {member}"
    finally:
        client_v.close()


@pytest.mark.req("TTEAM-04")
def test_only_owner_can_remove_member(auth_client, org, teardown_registry):
    """MANAGER cannot remove a member (403); OWNER can remove via membership ID (204)."""
    email_mgr, client_mgr = _create_user_client()
    email_vol, client_vol = _create_user_client()
    try:
        # Invite MANAGER
        invite_mgr = auth_client.post(
            f"/organizations/{org['slug']}/members/invite/",
            json={"email": email_mgr, "role": "MANAGER"},
        )
        assert_status(invite_mgr, 201, "OWNER invites MANAGER")

        # Invite VOLUNTEER (to be removed)
        invite_vol = auth_client.post(
            f"/organizations/{org['slug']}/members/invite/",
            json={"email": email_vol, "role": "VOLUNTEER"},
        )
        assert_status(invite_vol, 201, "OWNER invites VOLUNTEER (to be removed)")

        # Fetch member list to find VOLUNTEER's membership_id (NOT user uuid)
        list_resp = auth_client.get(f"/organizations/{org['slug']}/members/")
        assert_status(list_resp, 200, "GET member list to find membership_id")
        members = list_resp.json()
        vol_member = next(
            (m for m in members if m.get("email") == email_vol),
            None,
        )
        assert vol_member is not None, (
            f"VOLUNTEER ({email_vol}) not found in member list: {members}"
        )
        membership_id = vol_member["id"]

        # MANAGER tries to delete (must fail)
        del_mgr = client_mgr.delete(
            f"/organizations/{org['slug']}/members/{membership_id}/",
        )
        assert_status(del_mgr, 403, "MANAGER cannot remove member")
        assert "Only owners can remove members" in del_mgr.text, (
            f"Expected error message not found in: {del_mgr.text[:300]}"
        )

        # OWNER removes the VOLUNTEER (must succeed)
        del_owner = auth_client.delete(
            f"/organizations/{org['slug']}/members/{membership_id}/",
        )
        assert_status(del_owner, 204, "OWNER removes VOLUNTEER")
    finally:
        client_mgr.close()
        client_vol.close()
