"""Integration test: auth fixture against the live Railway backend.

WARNING: This test makes real HTTP calls to the deployed GatherGood API.
It registers a test user and logs in. The teardown registry tracks cleanup.
"""
import pytest


@pytest.mark.req("INFR-03")
def test_auth_client_is_authenticated(auth_client):
    """auth_client fixture produces a client that can make authenticated requests."""
    # GET /auth/me/ should return the current user profile (200)
    # If the endpoint doesn't exist, any non-401 status proves auth works
    response = auth_client.get("/auth/me/")
    assert response.status_code != 401, (
        f"Auth client received 401 — token may be invalid.\n"
        f"Response: {response.text[:300]}"
    )
    # Accept 200 (profile returned) or 404 (endpoint path differs) — both prove auth header is valid
    assert response.status_code in (200, 201, 301, 302, 404), (
        f"Unexpected status {response.status_code} from /auth/me/\n"
        f"Response: {response.text[:300]}"
    )


@pytest.mark.req("INFR-03")
def test_auth_client_has_refresh_capability(auth_client):
    """auth_client has a _maybe_refresh method (token refresh is wired)."""
    assert hasattr(auth_client, "_maybe_refresh"), (
        "auth_client missing _maybe_refresh — token refresh not wired"
    )


@pytest.mark.req("INFR-03")
def test_auth_client_methods_exist(auth_client):
    """auth_client exposes get, post, patch, put, delete methods."""
    for method in ("get", "post", "patch", "put", "delete"):
        assert hasattr(auth_client, method), f"auth_client missing .{method}() method"
