"""Permission boundary tests: TPERM-01 through TPERM-05.

Verifies that role-based access control is enforced server-side across all
three role levels: VOLUNTEER, MANAGER, and non-member.

- TPERM-01: VOLUNTEER cannot create events (403)
- TPERM-02: VOLUNTEER cannot invite members (403)
- TPERM-03: MANAGER cannot assign OWNER role (403)
- TPERM-04: MANAGER cannot remove members (403)
- TPERM-05: Non-member gets 404 on org resources (queryset-level hiding)
"""
import httpx
import pytest

from factories.common import unique_email, event_title
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
        "first_name": "Perm",
        "last_name": "Test",
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


@pytest.fixture(scope="module")
def volunteer_client(auth_client, org):
    """Create a user, invite as VOLUNTEER to the session org, yield client.

    Module-scoped so it is shared across TPERM-01 and TPERM-02.
    """
    email, client = _create_user_client()
    try:
        invite = auth_client.post(
            f"/organizations/{org['slug']}/members/invite/",
            json={"email": email, "role": "VOLUNTEER"},
        )
        assert_status(invite, 201, "Invite VOLUNTEER for permission tests")
        yield client
    finally:
        client.close()


@pytest.fixture(scope="module")
def manager_client(auth_client, org):
    """Create a user, invite as MANAGER to the session org, yield client.

    Module-scoped so it is shared across TPERM-03 and TPERM-04.
    """
    email, client = _create_user_client()
    try:
        invite = auth_client.post(
            f"/organizations/{org['slug']}/members/invite/",
            json={"email": email, "role": "MANAGER"},
        )
        assert_status(invite, 201, "Invite MANAGER for permission tests")
        yield client
    finally:
        client.close()


@pytest.fixture(scope="module")
def non_member_client():
    """Create a user that is NOT invited to any org, yield client."""
    _email, client = _create_user_client()
    try:
        yield client
    finally:
        client.close()


@pytest.mark.req("TPERM-01")
def test_volunteer_cannot_create_event(volunteer_client, org):
    """VOLUNTEER cannot POST to create events (403)."""
    r = volunteer_client.post(
        f"/organizations/{org['slug']}/events/",
        json={
            "title": event_title(),
            "format": "IN_PERSON",
            "category": "MEETUP",
            "start_datetime": "2026-12-01T09:00:00",
            "end_datetime": "2026-12-01T17:00:00",
            "timezone": "UTC",
        },
    )
    assert r.status_code == 403, (
        f"Expected 403, got {r.status_code}\nBody: {r.text[:300]}"
    )
    # Live API message: "Only managers and owners can perform this action."
    # DEVIATION from plan: actual message does not contain "permission" — assert the real message.
    detail = r.json().get("detail", "")
    assert "managers and owners" in detail.lower() or "permission" in detail.lower(), (
        f"Expected role-restriction message in detail, got: {r.text[:300]}"
    )


@pytest.mark.req("TPERM-02")
def test_volunteer_cannot_invite_member(volunteer_client, org):
    """VOLUNTEER cannot POST to invite members (403)."""
    r = volunteer_client.post(
        f"/organizations/{org['slug']}/members/invite/",
        json={"email": unique_email(), "role": "VOLUNTEER"},
    )
    assert r.status_code == 403, (
        f"Expected 403, got {r.status_code}\nBody: {r.text[:300]}"
    )
    assert "permission" in r.json().get("detail", "").lower(), (
        f"Expected 'permission' in detail, got: {r.text[:300]}"
    )


@pytest.mark.req("TPERM-03")
def test_manager_cannot_assign_owner_role(manager_client, org):
    """MANAGER cannot invite a user with role=OWNER (403)."""
    r = manager_client.post(
        f"/organizations/{org['slug']}/members/invite/",
        json={"email": unique_email(), "role": "OWNER"},
    )
    assert r.status_code == 403, (
        f"Expected 403, got {r.status_code}\nBody: {r.text[:300]}"
    )
    assert "Managers cannot assign the Owner role" in r.text, (
        f"Expected error message not found in: {r.text[:300]}"
    )


@pytest.mark.req("TPERM-04")
def test_manager_cannot_remove_member(auth_client, manager_client, org):
    """MANAGER cannot DELETE a member (403); OWNER cleans up afterward."""
    # Create a throwaway VOLUNTEER to attempt removal
    throwaway_email, throwaway_client = _create_user_client()
    try:
        # OWNER invites throwaway as VOLUNTEER
        invite = auth_client.post(
            f"/organizations/{org['slug']}/members/invite/",
            json={"email": throwaway_email, "role": "VOLUNTEER"},
        )
        assert_status(invite, 201, "OWNER invites throwaway VOLUNTEER for TPERM-04")

        # Fetch membership list via OWNER to find the membership_id (not user uuid)
        list_resp = auth_client.get(f"/organizations/{org['slug']}/members/")
        assert_status(list_resp, 200, "GET member list to find throwaway membership_id")
        members = list_resp.json()
        throwaway_member = next(
            (m for m in members if m.get("email") == throwaway_email),
            None,
        )
        assert throwaway_member is not None, (
            f"Throwaway VOLUNTEER ({throwaway_email}) not found in member list: {members}"
        )
        membership_id = throwaway_member["id"]

        # MANAGER tries to remove (must fail)
        r = manager_client.delete(
            f"/organizations/{org['slug']}/members/{membership_id}/",
        )
        assert r.status_code == 403, (
            f"Expected 403, got {r.status_code}\nBody: {r.text[:300]}"
        )
        assert "Only owners can remove members" in r.text, (
            f"Expected error message not found in: {r.text[:300]}"
        )

        # OWNER cleans up: removes the throwaway VOLUNTEER
        del_resp = auth_client.delete(
            f"/organizations/{org['slug']}/members/{membership_id}/",
        )
        assert_status(del_resp, 204, "OWNER removes throwaway VOLUNTEER (cleanup)")
    finally:
        throwaway_client.close()


@pytest.mark.req("TPERM-05")
def test_non_member_cannot_access_org(non_member_client, org):
    """Non-org-member gets 404 on org event resources (queryset-level hiding).

    # DEVIATION: Live API returns 404, not 403. Backend uses queryset-level
    # access control — a non-member sees "No Organization matches the given
    # query." because the org is filtered out of the queryset entirely.
    """
    r = non_member_client.get(f"/organizations/{org['slug']}/events/")
    # DEVIATION: Live API returns 404, not 403. Backend uses queryset-level access control.
    assert r.status_code == 404, (
        f"Expected 404 (queryset-level hiding), got {r.status_code}\nBody: {r.text[:300]}"
    )
