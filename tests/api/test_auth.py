"""Auth endpoint tests: TAUTH-01 through TAUTH-05."""
import httpx
import pytest

from factories.common import unique_email
from helpers.api import assert_status
from settings import Settings

_settings = Settings()


def _fresh_client():
    return httpx.Client(base_url=_settings.API_URL, timeout=30)


def _register_and_login():
    """Helper: register a fresh user and return (email, password, tokens)."""
    client = _fresh_client()
    email = unique_email()
    password = "TestPass123!"
    client.post("/auth/register/", json={
        "email": email,
        "password": password,
        "password_confirm": password,
        "first_name": "Test",
        "last_name": "User",
    })
    login_resp = client.post("/auth/login/", json={"email": email, "password": password})
    client.close()
    return email, password, login_resp.json()


@pytest.mark.req("TAUTH-01")
def test_register_user():
    """POST /auth/register/ with valid fields returns 201 and user object."""
    client = _fresh_client()
    email = unique_email()
    resp = client.post("/auth/register/", json={
        "email": email,
        "password": "TestPass123!",
        "password_confirm": "TestPass123!",
        "first_name": "Test",
        "last_name": "User",
    })
    client.close()

    assert_status(resp, 201, "POST /auth/register/")
    data = resp.json()
    assert data["user"]["email"] == email
    assert "id" in data["user"]
    assert data["message"] == "Account created successfully."


@pytest.mark.req("TAUTH-02")
def test_login_returns_jwt_tokens():
    """POST /auth/login/ returns both access and refresh JWT tokens."""
    client = _fresh_client()
    email = unique_email()
    password = "TestPass123!"

    # Register first
    client.post("/auth/register/", json={
        "email": email,
        "password": password,
        "password_confirm": password,
        "first_name": "Test",
        "last_name": "User",
    })

    # Now login
    resp = client.post("/auth/login/", json={"email": email, "password": password})
    client.close()

    assert_status(resp, 200, "POST /auth/login/")
    data = resp.json()
    assert "access" in data
    assert "refresh" in data
    assert isinstance(data["access"], str) and len(data["access"]) > 10
    assert isinstance(data["refresh"], str) and len(data["refresh"]) > 10


@pytest.mark.req("TAUTH-03")
def test_token_refresh_issues_new_tokens():
    """POST /auth/token/refresh/ issues new access and refresh tokens (rotation)."""
    _email, _password, login_data = _register_and_login()

    client = _fresh_client()
    resp = client.post("/auth/token/refresh/", json={"refresh": login_data["refresh"]})
    client.close()

    assert_status(resp, 200, "POST /auth/token/refresh/")
    data = resp.json()
    assert "access" in data
    assert "refresh" in data
    assert data["access"] != login_data["access"]
    assert data["refresh"] != login_data["refresh"]
    # NOTE: old refresh token is NOT asserted as rejected (Pitfall 7 — old tokens remain valid)


@pytest.mark.req("TAUTH-04")
def test_password_reset_request():
    """POST /auth/forgot-password/ returns 200 regardless of email existence."""
    client = _fresh_client()
    resp = client.post("/auth/forgot-password/", json={"email": "nonexistent@example.com"})
    client.close()

    assert_status(resp, 200, "POST /auth/forgot-password/")
    # API returns a generic message regardless of whether the email exists
    response_text = resp.text
    assert len(response_text) > 0


@pytest.mark.req("TAUTH-05")
def test_password_reset_bad_token():
    """POST /auth/reset-password/ with bad token returns 400 with error message."""
    client = _fresh_client()
    resp = client.post("/auth/reset-password/", json={
        "uid": "baduid",
        "token": "badtoken",
        "password": "NewPass123!",
        "password_confirm": "NewPass123!",
    })
    client.close()

    assert_status(resp, 400, "POST /auth/reset-password/")
    assert "Invalid or expired reset link" in resp.text
