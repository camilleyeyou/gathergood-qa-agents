"""Profile endpoint tests: TPROF-01 and TPROF-02."""
import pytest

from factories.common import RUN_ID
from helpers.api import assert_status


@pytest.mark.req("TPROF-01")
def test_get_profile(auth_client):
    """GET /auth/me/ returns authenticated user profile with all expected fields."""
    resp = auth_client.get("/auth/me/")
    assert_status(resp, 200, "GET /auth/me/")

    data = resp.json()
    for field in ("id", "email", "first_name", "last_name", "phone", "avatar_url",
                  "email_verified", "created_at"):
        assert field in data, f"Missing field: {field}"
    assert isinstance(data["email"], str) and "@" in data["email"]


@pytest.mark.req("TPROF-02")
def test_patch_profile(auth_client):
    """PATCH /auth/me/ updates profile fields and returns the updated object."""
    # Get original values first
    original_resp = auth_client.get("/auth/me/")
    assert_status(original_resp, 200, "GET /auth/me/ (before patch)")
    original = original_resp.json()
    original_first = original.get("first_name", "Test")
    original_last = original.get("last_name", f"User-{RUN_ID}")

    # Patch with new values
    resp = auth_client.patch("/auth/me/", json={
        "first_name": "Updated",
        "last_name": "Name",
        "phone": "+15551234567",
    })
    assert_status(resp, 200, "PATCH /auth/me/")

    data = resp.json()
    assert data["first_name"] == "Updated"
    assert data["last_name"] == "Name"
    assert data["phone"] == "+15551234567"

    # Restore original values to avoid polluting auth user for other tests
    auth_client.patch("/auth/me/", json={
        "first_name": original_first,
        "last_name": original_last,
    })
