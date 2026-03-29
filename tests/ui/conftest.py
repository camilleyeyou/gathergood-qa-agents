"""Playwright browser test fixtures for UI tests."""
import os
import re

import pytest
import httpx
from settings import Settings
from factories.common import unique_email, org_name, event_title, tier_name
from helpers.api import assert_status

_settings = Settings()


def _sanitize_nodeid(nodeid: str) -> str:
    """Convert a pytest node ID to a filesystem-safe string."""
    safe = re.sub(r"[/\\::\[\]<>|?*]", "_", nodeid)
    safe = re.sub(r"_+", "_", safe)
    return safe.strip("_")


@pytest.fixture(scope="function")
def context(browser, request):
    """Browser context with Playwright tracing enabled for all UI tests.

    Starts tracing at setup, saves trace zip to reports/traces/ at teardown.
    Trace is always saved; conftest_report.py attaches it only for failed tests.
    """
    ctx = browser.new_context()
    ctx.tracing.start(screenshots=True, snapshots=True)
    yield ctx
    # Save trace
    trace_dir = os.path.join("reports", "traces")
    os.makedirs(trace_dir, exist_ok=True)
    safe_name = _sanitize_nodeid(request.node.nodeid)
    trace_path = os.path.join(trace_dir, f"{safe_name}.zip")
    ctx.tracing.stop(path=trace_path)
    ctx.close()


@pytest.fixture(scope="function")
def page(context):
    """Page from traced browser context."""
    pg = context.new_page()
    yield pg
    pg.close()


@pytest.fixture(scope="session")
def base_url():
    """Frontend base URL from settings."""
    return _settings.BASE_URL


@pytest.fixture(scope="session")
def api_url():
    """API base URL from settings."""
    return _settings.API_URL


def login_via_ui(page, base_url, email, password):
    """Log in to the GatherGood frontend via the /login page.

    Uses Playwright to fill the login form and submit it.
    Waits for the URL to change away from /login before returning.

    Args:
        page: Playwright page object
        base_url: Frontend base URL string
        email: User email address
        password: User password
    """
    page.goto(f"{base_url}/login", timeout=60000)
    page.wait_for_load_state("networkidle")

    # Fill email — try label-based first, fall back to type-based
    email_field = page.locator("input[type='email']")
    email_field.fill(email)

    # Fill password
    password_field = page.locator("input[type='password']")
    password_field.fill(password)

    # Click submit — try button text first, fall back to submit type
    submit_btn = page.locator("button[type='submit']")
    submit_btn.click()

    # Wait for navigation away from /login
    page.wait_for_url(lambda url: "/login" not in url, timeout=15000)


@pytest.fixture(scope="module")
def ui_test_user():
    """Register a fresh user for UI authenticated tests.

    Returns dict: {email, password, access, first_name, last_name}
    This user is separate from the session auth_client user to avoid interference.
    """
    email = unique_email()
    password = "TestPass123!"
    first_name = "UI"
    last_name = "Tester"

    client = httpx.Client(base_url=_settings.API_URL, timeout=30)

    # Register user
    reg_resp = client.post(
        "/auth/register/",
        json={
            "email": email,
            "password": password,
            "password_confirm": password,
            "first_name": first_name,
            "last_name": last_name,
        },
    )
    assert_status(reg_resp, 201, "ui_test_user: Register")

    # Login to get tokens
    login_resp = client.post(
        "/auth/login/",
        json={"email": email, "password": password},
    )
    assert_status(login_resp, 200, "ui_test_user: Login")
    tokens = login_resp.json()

    client.close()

    return {
        "email": email,
        "password": password,
        "access": tokens["access"],
        "first_name": first_name,
        "last_name": last_name,
    }


@pytest.fixture(scope="module")
def ui_auth_client(ui_test_user):
    """HTTP client authenticated as the UI test user.

    Used for API-side data setup in UI tests (e.g., creating orgs, events).
    Yields an httpx.Client with Bearer auth header set.
    """
    client = httpx.Client(
        base_url=_settings.API_URL,
        headers={"Authorization": f"Bearer {ui_test_user['access']}"},
        timeout=30,
    )
    yield client
    client.close()


@pytest.fixture(scope="module")
def ui_checkout_data(ui_auth_client):
    """Create an org, published event with free tier for UI checkout and check-in tests.

    Returns dict: {org_slug, event_slug, tier_id, event_title}
    """
    # Create org
    org_resp = ui_auth_client.post(
        "/organizations/",
        json={"name": org_name(), "description": "UI test org"},
    )
    assert_status(org_resp, 201, "ui_checkout_data: Create org")
    org_data = org_resp.json()
    org_slug = org_data["slug"]

    # Create event
    title = event_title()
    event_resp = ui_auth_client.post(
        f"/organizations/{org_slug}/events/",
        json={
            "title": title,
            "format": "IN_PERSON",
            "category": "MEETUP",
            "start_datetime": "2026-12-01T09:00:00",
            "end_datetime": "2026-12-01T17:00:00",
            "timezone": "UTC",
        },
    )
    assert_status(event_resp, 201, "ui_checkout_data: Create event")
    event_data = event_resp.json()
    event_slug = event_data["slug"]

    # Create free ticket tier
    tier_resp = ui_auth_client.post(
        f"/organizations/{org_slug}/events/{event_slug}/ticket-tiers/",
        json={
            "name": tier_name(),
            "price": "0.00",
            "quantity_total": 100,
            "min_per_order": 1,
            "max_per_order": 10,
            "visibility": "PUBLIC",
        },
    )
    assert_status(tier_resp, 201, "ui_checkout_data: Create free tier")
    tier_data = tier_resp.json()
    tier_id = tier_data["id"]

    # Publish event
    pub_resp = ui_auth_client.post(
        f"/organizations/{org_slug}/events/{event_slug}/publish/",
    )
    assert_status(pub_resp, 200, "ui_checkout_data: Publish event")

    return {
        "org_slug": org_slug,
        "event_slug": event_slug,
        "tier_id": tier_id,
        "event_title": title,
    }
