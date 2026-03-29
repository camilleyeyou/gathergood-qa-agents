"""AI agent scenarios for checkout flows."""
import httpx
import pytest

from factories.common import unique_email, org_name, event_title, tier_name
from helpers.api import assert_status
from settings import Settings
from tests.ai_agents.agent_runner import run_agent_scenario

_settings = Settings()


def _create_event_with_free_tier():
    """Register user, create org, published event with free tier via API.

    Returns dict with: email, password, access, org_slug, event_slug, tier_id, event_title.
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
                "last_name": "CheckoutTester",
            },
        )
        assert_status(reg_resp, 201, "checkout_agent: Register")

        # Login
        login_resp = client.post(
            "/auth/login/",
            json={"email": email, "password": password},
        )
        assert_status(login_resp, 200, "checkout_agent: Login")
        tokens = login_resp.json()
        access = tokens["access"]

        client.headers["Authorization"] = f"Bearer {access}"

        # Create org
        name = org_name()
        org_resp = client.post(
            "/organizations/",
            json={"name": name, "description": "AI agent checkout test org"},
        )
        assert_status(org_resp, 201, "checkout_agent: Create org")
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
        assert_status(event_resp, 201, "checkout_agent: Create event")
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
        assert_status(tier_resp, 201, "checkout_agent: Create tier")
        tier_id = tier_resp.json()["id"]

        # Publish
        pub_resp = client.post(
            f"/organizations/{org_slug}/events/{event_slug}/publish/",
        )
        assert_status(pub_resp, 200, "checkout_agent: Publish")

    return {
        "email": email,
        "password": password,
        "access": access,
        "org_slug": org_slug,
        "event_slug": event_slug,
        "tier_id": tier_id,
        "event_title": title,
    }


@pytest.mark.req("AIQA-06")
@pytest.mark.ai_agent
def test_checkout_flow_agent(agent_backend, claude_client, base_url, agent_system_prompt, record_agent_result):
    """AI agent completes a full free checkout flow end-to-end."""
    data = _create_event_with_free_tier()

    agent_backend.page.goto(
        f"{base_url}/events/{data['org_slug']}/{data['event_slug']}",
        timeout=60000,
    )
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_agent_scenario(
        backend=agent_backend,
        client=claude_client,
        goal=(
            "You are on a GatherGood event detail page. Verify the checkout flow: "
            "1) Find and click a 'Get Tickets', 'Register', or 'Buy Tickets' button. "
            "2) On the checkout page, verify there are step indicators showing the "
            "checkout progress (like 'Select Tickets', 'Your Details', 'Payment', "
            "'Confirmation'). "
            "3) Select 1 ticket from the available tier. "
            "4) Proceed through the checkout steps — this is a free event so no "
            "payment is needed. "
            "5) Fill in billing/contact details if prompted (use name 'Agent Tester', "
            "email 'agent@test.invalid', phone '555-0100'). "
            "6) Complete the checkout and verify you reach a confirmation page "
            "showing a confirmation code. "
            "Report PASS if you complete the full checkout and see a confirmation "
            "code, FAIL if any step fails, INCONCLUSIVE if you get stuck."
        ),
        system_prompt=agent_system_prompt,
        max_iterations=20,
    )
    record_agent_result(result)

    assert result["verdict"] != "FAIL", (
        f"Agent reported FAIL after {result['steps']} steps.\n"
        f"Reasoning: {result['reasoning']}"
    )


@pytest.mark.req("AIQA-06")
@pytest.mark.ai_agent
def test_checkout_page_structure_agent(agent_backend, claude_client, base_url, agent_system_prompt, record_agent_result):
    """AI agent verifies checkout page structure (steps, ticket selection)."""
    data = _create_event_with_free_tier()

    agent_backend.page.goto(
        f"{base_url}/events/{data['org_slug']}/{data['event_slug']}",
        timeout=60000,
    )
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_agent_scenario(
        backend=agent_backend,
        client=claude_client,
        goal=(
            "You are on a GatherGood event page. Click to start the "
            "checkout/ticket purchase flow. Once on the checkout page, verify: "
            "1) There are step indicators (numbered steps like 1, 2, 3, 4 or "
            "labeled steps). "
            "2) The current step is highlighted differently from future steps. "
            "3) There is a ticket selection area with quantity controls. "
            "Report PASS if the checkout page has clear step progression and "
            "ticket selection, FAIL otherwise."
        ),
        system_prompt=agent_system_prompt,
        max_iterations=15,
    )
    record_agent_result(result)

    assert result["verdict"] != "FAIL", (
        f"Agent reported FAIL after {result['steps']} steps.\n"
        f"Reasoning: {result['reasoning']}"
    )
