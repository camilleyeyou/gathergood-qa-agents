"""AI agent scenarios for event management flows."""
import httpx
import pytest

from factories.common import unique_email, org_name, event_title, tier_name
from helpers.api import assert_status
from settings import Settings
from tests.ai_agents.agent_runner import run_agent_scenario

_settings = Settings()


def _create_published_event():
    """Register user, create org, event, free tier, and publish via API.

    Returns dict with: email, password, access, org_slug, event_slug, event_title.
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
                "last_name": "EventTester",
            },
        )
        assert_status(reg_resp, 201, "event_agent: Register")

        # Login
        login_resp = client.post(
            "/auth/login/",
            json={"email": email, "password": password},
        )
        assert_status(login_resp, 200, "event_agent: Login")
        tokens = login_resp.json()
        access = tokens["access"]

        client.headers["Authorization"] = f"Bearer {access}"

        # Create org
        name = org_name()
        org_resp = client.post(
            "/organizations/",
            json={"name": name, "description": "AI agent test org"},
        )
        assert_status(org_resp, 201, "event_agent: Create org")
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
        assert_status(event_resp, 201, "event_agent: Create event")
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
        assert_status(tier_resp, 201, "event_agent: Create tier")

        # Publish
        pub_resp = client.post(
            f"/organizations/{org_slug}/events/{event_slug}/publish/",
        )
        assert_status(pub_resp, 200, "event_agent: Publish")

    return {
        "email": email,
        "password": password,
        "access": access,
        "org_slug": org_slug,
        "event_slug": event_slug,
        "event_title": title,
    }


@pytest.mark.req("AIQA-05")
@pytest.mark.ai_agent
def test_event_public_page_agent(agent_backend, claude_client, base_url, agent_system_prompt):
    """AI agent browses public events and views an event detail page."""
    data = _create_published_event()
    # Use a unique substring from the title for searching
    title_substring = data["event_title"]

    agent_backend.page.goto(f"{base_url}/events", timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_agent_scenario(
        backend=agent_backend,
        client=claude_client,
        goal=(
            "You are on the GatherGood events listing page. Verify: "
            "1) The page shows a list or grid of events. "
            f"2) Look for an event with a title containing '{title_substring}'. "
            "3) If found, click on it to view the event detail page. "
            "4) On the detail page, verify there is event information "
            "(title, date, description area) and a ticket/registration section. "
            "Report PASS if you can browse events and view event details, "
            "FAIL otherwise."
        ),
        system_prompt=agent_system_prompt,
        max_iterations=15,
    )

    assert result["verdict"] != "FAIL", (
        f"Agent reported FAIL after {result['steps']} steps.\n"
        f"Reasoning: {result['reasoning']}"
    )


@pytest.mark.req("AIQA-05")
@pytest.mark.ai_agent
def test_event_dashboard_agent(agent_backend, claude_client, base_url, agent_system_prompt):
    """AI agent logs in and verifies the event management dashboard."""
    data = _create_published_event()

    agent_backend.page.goto(f"{base_url}/login", timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_agent_scenario(
        backend=agent_backend,
        client=claude_client,
        goal=(
            f"You are on the GatherGood login page. Log in with email "
            f"'{data['email']}' and password '{data['password']}'. "
            "After login, navigate to the dashboard. Verify: "
            "1) You can see a dashboard page with organization or event "
            "management options. "
            "2) There are options to create or manage events. "
            "Report PASS if the dashboard is accessible and shows management "
            "features, FAIL otherwise."
        ),
        system_prompt=agent_system_prompt,
        max_iterations=18,
    )

    assert result["verdict"] != "FAIL", (
        f"Agent reported FAIL after {result['steps']} steps.\n"
        f"Reasoning: {result['reasoning']}"
    )
