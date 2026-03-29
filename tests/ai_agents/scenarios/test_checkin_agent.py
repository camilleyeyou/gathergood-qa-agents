"""AI agent scenarios for check-in page verification."""
import httpx
import pytest

from factories.common import unique_email, org_name, event_title, tier_name
from helpers.api import assert_status
from settings import Settings
from tests.ai_agents.agent_runner import run_agent_scenario

_settings = Settings()


def _create_event_with_checkout():
    """Register user, create org, published event, free tier, and complete a checkout.

    Returns dict with: email, password, access, org_slug, event_slug.
    """
    email = unique_email()
    password = "AgentTest123!"

    with httpx.Client(base_url=_settings.API_URL, timeout=30) as client:
        # Register
        reg_resp = client.post(
            "/auth/register/",
            json={
                "email": email,
                "password": password,
                "password_confirm": password,
                "first_name": "Agent",
                "last_name": "CheckinTester",
            },
        )
        assert_status(reg_resp, 201, "checkin_agent: Register")

        # Login
        login_resp = client.post(
            "/auth/login/",
            json={"email": email, "password": password},
        )
        assert_status(login_resp, 200, "checkin_agent: Login")
        tokens = login_resp.json()
        access = tokens["access"]

        client.headers["Authorization"] = f"Bearer {access}"

        # Create org
        name = org_name()
        org_resp = client.post(
            "/organizations/",
            json={"name": name, "description": "AI agent check-in test org"},
        )
        assert_status(org_resp, 201, "checkin_agent: Create org")
        org_slug = org_resp.json()["slug"]

        # Create event
        title = event_title()
        event_resp = client.post(
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
        assert_status(event_resp, 201, "checkin_agent: Create event")
        event_slug = event_resp.json()["slug"]

        # Create free tier
        t_name = tier_name()
        tier_resp = client.post(
            f"/organizations/{org_slug}/events/{event_slug}/ticket-tiers/",
            json={
                "name": t_name,
                "price": "0.00",
                "quantity_total": 100,
                "min_per_order": 1,
                "max_per_order": 10,
                "visibility": "PUBLIC",
            },
        )
        assert_status(tier_resp, 201, "checkin_agent: Create tier")
        tier_id = tier_resp.json()["id"]

        # Publish
        pub_resp = client.post(
            f"/organizations/{org_slug}/events/{event_slug}/publish/",
        )
        assert_status(pub_resp, 200, "checkin_agent: Publish")

        # Complete a free checkout to create an attendee
        checkout_resp = client.post(
            f"/organizations/{org_slug}/events/{event_slug}/checkout/",
            json={
                "items": [{"tier_id": tier_id, "quantity": 1}],
                "billing_name": "Agent CheckinTester",
                "billing_email": email,
            },
        )
        assert_status(checkout_resp, 201, "checkin_agent: Checkout")

    return {
        "email": email,
        "password": password,
        "access": access,
        "org_slug": org_slug,
        "event_slug": event_slug,
    }


@pytest.mark.req("AIQA-07")
@pytest.mark.ai_agent
def test_checkin_page_agent(agent_backend, claude_client, base_url, agent_system_prompt, record_agent_result):
    """AI agent verifies the check-in page has scanner, search, and stats."""
    data = _create_event_with_checkout()

    # Log in via the browser first, then navigate to check-in
    agent_backend.page.goto(f"{base_url}/login", timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_agent_scenario(
        backend=agent_backend,
        client=claude_client,
        goal=(
            f"You are on the GatherGood login page. Log in with email "
            f"'{data['email']}' and password '{data['password']}'. "
            "After login, navigate to the check-in page for the event "
            "(look for 'Check-in' or 'Check In' in the event management area, "
            "or navigate to the dashboard and find your event's check-in section). "
            "Verify: "
            "1) There is a QR scanner section or camera/scan button. "
            "2) There is a search field to look up attendees by name, email, "
            "or confirmation code. "
            "3) There are check-in statistics showing counts (total registered, "
            "checked in, etc.). "
            "Report PASS if all three elements are present, FAIL if any are "
            "missing, INCONCLUSIVE if you cannot find the check-in page."
        ),
        system_prompt=agent_system_prompt,
        max_iterations=18,
    )
    record_agent_result(result)

    assert result["verdict"] != "FAIL", (
        f"Agent reported FAIL after {result['steps']} steps.\n"
        f"Reasoning: {result['reasoning']}"
    )
