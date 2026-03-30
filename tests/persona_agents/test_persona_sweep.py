"""15 persona test functions (5 personas x 3 flows) for digital literacy UX evaluation.

Each function runs a persona agent through a specific flow, records a friction score,
saves a JSON artifact, and asserts the score is in the valid range [1, 10].

Run all 15 with:
    pytest tests/persona_agents/

Run a single persona/flow combination with -k:
    pytest tests/persona_agents/ -k "low_literacy and registration"
"""
import pytest
import httpx

from factories.common import unique_email, org_name, event_title, tier_name
from helpers.api import assert_status
from settings import Settings
from tests.persona_agents.personas import (
    TECH_SAVVY,
    CASUAL,
    LOW_LITERACY,
    NON_NATIVE,
    IMPATIENT,
    OPTIMAL_STEPS,
)
from tests.persona_agents.persona_runner import run_persona_scenario
from tests.persona_agents.artifact_writer import save_persona_result

_settings = Settings()

# ---------------------------------------------------------------------------
# Natural-language flow goal strings passed to Claude as the task description.
# ---------------------------------------------------------------------------
FLOW_GOALS = {
    "registration": (
        "You are on a website registration page. Create a new account by filling in "
        "the registration form with an email address, password, and your name. Act "
        "exactly as described in your character description. When done or if you give "
        "up, output your verdict and the JSON block."
    ),
    "browsing": (
        "You are on an event listing page. Browse the available events, find an "
        "interesting one, and view its details page. Act exactly as described in your "
        "character description. When done or if you give up, output your verdict and "
        "the JSON block."
    ),
    "checkout": (
        "You are on an event listing page. Find an event with free tickets, go to its "
        "page, select a free ticket, and complete the checkout process. Act exactly as "
        "described in your character description. When done or if you give up, output "
        "your verdict and the JSON block."
    ),
}

# ---------------------------------------------------------------------------
# API setup helpers — create necessary prerequisite data before browser tests.
# ---------------------------------------------------------------------------

def _setup_registration_flow() -> dict:
    """No API setup needed — registration starts from the /register page.

    Returns:
        Dict with start_url pointing to the registration page.
    """
    return {"start_url": f"{_settings.BASE_URL}/register"}


def _setup_browsing_flow() -> dict:
    """Register a user, create org, create and publish an event via API.

    Ensures there is at least one published event visible on the events listing
    page so the browsing flow has something to navigate to.

    Returns:
        Dict with start_url pointing to the events listing page.
    """
    email = unique_email()
    password = "PersonaTest123!"

    with httpx.Client(base_url=_settings.API_URL, timeout=30) as client:
        # Register
        reg_resp = client.post(
            "/auth/register/",
            json={
                "email": email,
                "password": password,
                "password_confirm": password,
                "first_name": "Persona",
                "last_name": "BrowsingSetup",
            },
        )
        assert_status(reg_resp, 201, "persona_sweep: Register (browsing setup)")

        # Login
        login_resp = client.post(
            "/auth/login/",
            json={"email": email, "password": password},
        )
        assert_status(login_resp, 200, "persona_sweep: Login (browsing setup)")
        access = login_resp.json()["access"]
        client.headers["Authorization"] = f"Bearer {access}"

        # Create org
        org_resp = client.post(
            "/organizations/",
            json={"name": org_name(), "description": "Persona browsing setup org"},
        )
        assert_status(org_resp, 201, "persona_sweep: Create org (browsing setup)")
        org_slug = org_resp.json()["slug"]

        # Create event
        event_resp = client.post(
            f"/organizations/{org_slug}/events/",
            json={
                "title": event_title(),
                "format": "IN_PERSON",
                "category": "MEETUP",
                "start_datetime": "2026-12-01T09:00:00",
                "end_datetime": "2026-12-01T17:00:00",
                "timezone": "UTC",
            },
        )
        assert_status(event_resp, 201, "persona_sweep: Create event (browsing setup)")
        event_slug = event_resp.json()["slug"]

        # Create free tier so the event is browsable
        client.post(
            f"/organizations/{org_slug}/events/{event_slug}/ticket-tiers/",
            json={
                "name": tier_name(),
                "price": "0.00",
                "quantity_total": 50,
                "min_per_order": 1,
                "max_per_order": 5,
                "visibility": "PUBLIC",
            },
        )

        # Publish
        pub_resp = client.post(
            f"/organizations/{org_slug}/events/{event_slug}/publish/",
        )
        assert_status(pub_resp, 200, "persona_sweep: Publish (browsing setup)")

    return {"start_url": f"{_settings.BASE_URL}/events"}


def _setup_checkout_flow() -> dict:
    """Register user, create org, create event, publish, and create a free ticket tier.

    Returns:
        Dict with start_url, event_slug, and org_slug.
    """
    email = unique_email()
    password = "PersonaTest123!"

    with httpx.Client(base_url=_settings.API_URL, timeout=30) as client:
        # Register
        reg_resp = client.post(
            "/auth/register/",
            json={
                "email": email,
                "password": password,
                "password_confirm": password,
                "first_name": "Persona",
                "last_name": "CheckoutSetup",
            },
        )
        assert_status(reg_resp, 201, "persona_sweep: Register (checkout setup)")

        # Login
        login_resp = client.post(
            "/auth/login/",
            json={"email": email, "password": password},
        )
        assert_status(login_resp, 200, "persona_sweep: Login (checkout setup)")
        access = login_resp.json()["access"]
        client.headers["Authorization"] = f"Bearer {access}"

        # Create org
        org_resp = client.post(
            "/organizations/",
            json={"name": org_name(), "description": "Persona checkout setup org"},
        )
        assert_status(org_resp, 201, "persona_sweep: Create org (checkout setup)")
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
        assert_status(event_resp, 201, "persona_sweep: Create event (checkout setup)")
        event_slug = event_resp.json()["slug"]

        # Create free tier
        tier_resp = client.post(
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
        assert_status(tier_resp, 201, "persona_sweep: Create tier (checkout setup)")

        # Publish
        pub_resp = client.post(
            f"/organizations/{org_slug}/events/{event_slug}/publish/",
        )
        assert_status(pub_resp, 200, "persona_sweep: Publish (checkout setup)")

    return {
        "start_url": f"{_settings.BASE_URL}/events",
        "event_slug": event_slug,
        "org_slug": org_slug,
    }


# ---------------------------------------------------------------------------
# Test functions — 15 total (5 personas x 3 flows)
# max_iterations: 15 for fast personas (tech_savvy, impatient), 25 for others
# ---------------------------------------------------------------------------

# -- TECH_SAVVY ---------------------------------------------------------------

@pytest.mark.persona_agent
def test_tech_savvy_registration(agent_backend, claude_client, base_url, run_id, record_persona_result):
    """'TECH_SAVVY' persona attempts registration flow."""
    setup = _setup_registration_flow()
    agent_backend.page.goto(setup["start_url"], timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_persona_scenario(
        backend=agent_backend,
        client=claude_client,
        persona=TECH_SAVVY,
        flow_goal=FLOW_GOALS["registration"],
        optimal_steps=OPTIMAL_STEPS["registration"],
        max_iterations=15,
    )
    result["flow"] = "registration"
    save_persona_result(result, run_id)
    record_persona_result(result)

    assert result["friction_score"] is not None, "Friction score must be calculated"
    assert 1 <= result["friction_score"] <= 10, (
        f"Friction score {result['friction_score']} out of range"
    )


@pytest.mark.persona_agent
def test_tech_savvy_browsing(agent_backend, claude_client, base_url, run_id, record_persona_result):
    """'TECH_SAVVY' persona attempts browsing flow."""
    setup = _setup_browsing_flow()
    agent_backend.page.goto(setup["start_url"], timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_persona_scenario(
        backend=agent_backend,
        client=claude_client,
        persona=TECH_SAVVY,
        flow_goal=FLOW_GOALS["browsing"],
        optimal_steps=OPTIMAL_STEPS["browsing"],
        max_iterations=15,
    )
    result["flow"] = "browsing"
    save_persona_result(result, run_id)
    record_persona_result(result)

    assert result["friction_score"] is not None, "Friction score must be calculated"
    assert 1 <= result["friction_score"] <= 10, (
        f"Friction score {result['friction_score']} out of range"
    )


@pytest.mark.persona_agent
def test_tech_savvy_checkout(agent_backend, claude_client, base_url, run_id, record_persona_result):
    """'TECH_SAVVY' persona attempts checkout flow."""
    setup = _setup_checkout_flow()
    agent_backend.page.goto(setup["start_url"], timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_persona_scenario(
        backend=agent_backend,
        client=claude_client,
        persona=TECH_SAVVY,
        flow_goal=FLOW_GOALS["checkout"],
        optimal_steps=OPTIMAL_STEPS["checkout"],
        max_iterations=15,
    )
    result["flow"] = "checkout"
    save_persona_result(result, run_id)
    record_persona_result(result)

    assert result["friction_score"] is not None, "Friction score must be calculated"
    assert 1 <= result["friction_score"] <= 10, (
        f"Friction score {result['friction_score']} out of range"
    )


# -- CASUAL -------------------------------------------------------------------

@pytest.mark.persona_agent
def test_casual_registration(agent_backend, claude_client, base_url, run_id, record_persona_result):
    """'CASUAL' persona attempts registration flow."""
    setup = _setup_registration_flow()
    agent_backend.page.goto(setup["start_url"], timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_persona_scenario(
        backend=agent_backend,
        client=claude_client,
        persona=CASUAL,
        flow_goal=FLOW_GOALS["registration"],
        optimal_steps=OPTIMAL_STEPS["registration"],
        max_iterations=25,
    )
    result["flow"] = "registration"
    save_persona_result(result, run_id)
    record_persona_result(result)

    assert result["friction_score"] is not None, "Friction score must be calculated"
    assert 1 <= result["friction_score"] <= 10, (
        f"Friction score {result['friction_score']} out of range"
    )


@pytest.mark.persona_agent
def test_casual_browsing(agent_backend, claude_client, base_url, run_id, record_persona_result):
    """'CASUAL' persona attempts browsing flow."""
    setup = _setup_browsing_flow()
    agent_backend.page.goto(setup["start_url"], timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_persona_scenario(
        backend=agent_backend,
        client=claude_client,
        persona=CASUAL,
        flow_goal=FLOW_GOALS["browsing"],
        optimal_steps=OPTIMAL_STEPS["browsing"],
        max_iterations=25,
    )
    result["flow"] = "browsing"
    save_persona_result(result, run_id)
    record_persona_result(result)

    assert result["friction_score"] is not None, "Friction score must be calculated"
    assert 1 <= result["friction_score"] <= 10, (
        f"Friction score {result['friction_score']} out of range"
    )


@pytest.mark.persona_agent
def test_casual_checkout(agent_backend, claude_client, base_url, run_id, record_persona_result):
    """'CASUAL' persona attempts checkout flow."""
    setup = _setup_checkout_flow()
    agent_backend.page.goto(setup["start_url"], timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_persona_scenario(
        backend=agent_backend,
        client=claude_client,
        persona=CASUAL,
        flow_goal=FLOW_GOALS["checkout"],
        optimal_steps=OPTIMAL_STEPS["checkout"],
        max_iterations=25,
    )
    result["flow"] = "checkout"
    save_persona_result(result, run_id)
    record_persona_result(result)

    assert result["friction_score"] is not None, "Friction score must be calculated"
    assert 1 <= result["friction_score"] <= 10, (
        f"Friction score {result['friction_score']} out of range"
    )


# -- LOW_LITERACY -------------------------------------------------------------

@pytest.mark.persona_agent
def test_low_literacy_registration(agent_backend, claude_client, base_url, run_id, record_persona_result):
    """'LOW_LITERACY' persona attempts registration flow."""
    setup = _setup_registration_flow()
    agent_backend.page.goto(setup["start_url"], timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_persona_scenario(
        backend=agent_backend,
        client=claude_client,
        persona=LOW_LITERACY,
        flow_goal=FLOW_GOALS["registration"],
        optimal_steps=OPTIMAL_STEPS["registration"],
        max_iterations=25,
    )
    result["flow"] = "registration"
    save_persona_result(result, run_id)
    record_persona_result(result)

    assert result["friction_score"] is not None, "Friction score must be calculated"
    assert 1 <= result["friction_score"] <= 10, (
        f"Friction score {result['friction_score']} out of range"
    )


@pytest.mark.persona_agent
def test_low_literacy_browsing(agent_backend, claude_client, base_url, run_id, record_persona_result):
    """'LOW_LITERACY' persona attempts browsing flow."""
    setup = _setup_browsing_flow()
    agent_backend.page.goto(setup["start_url"], timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_persona_scenario(
        backend=agent_backend,
        client=claude_client,
        persona=LOW_LITERACY,
        flow_goal=FLOW_GOALS["browsing"],
        optimal_steps=OPTIMAL_STEPS["browsing"],
        max_iterations=25,
    )
    result["flow"] = "browsing"
    save_persona_result(result, run_id)
    record_persona_result(result)

    assert result["friction_score"] is not None, "Friction score must be calculated"
    assert 1 <= result["friction_score"] <= 10, (
        f"Friction score {result['friction_score']} out of range"
    )


@pytest.mark.persona_agent
def test_low_literacy_checkout(agent_backend, claude_client, base_url, run_id, record_persona_result):
    """'LOW_LITERACY' persona attempts checkout flow."""
    setup = _setup_checkout_flow()
    agent_backend.page.goto(setup["start_url"], timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_persona_scenario(
        backend=agent_backend,
        client=claude_client,
        persona=LOW_LITERACY,
        flow_goal=FLOW_GOALS["checkout"],
        optimal_steps=OPTIMAL_STEPS["checkout"],
        max_iterations=25,
    )
    result["flow"] = "checkout"
    save_persona_result(result, run_id)
    record_persona_result(result)

    assert result["friction_score"] is not None, "Friction score must be calculated"
    assert 1 <= result["friction_score"] <= 10, (
        f"Friction score {result['friction_score']} out of range"
    )


# -- NON_NATIVE ---------------------------------------------------------------

@pytest.mark.persona_agent
def test_non_native_registration(agent_backend, claude_client, base_url, run_id, record_persona_result):
    """'NON_NATIVE' persona attempts registration flow."""
    setup = _setup_registration_flow()
    agent_backend.page.goto(setup["start_url"], timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_persona_scenario(
        backend=agent_backend,
        client=claude_client,
        persona=NON_NATIVE,
        flow_goal=FLOW_GOALS["registration"],
        optimal_steps=OPTIMAL_STEPS["registration"],
        max_iterations=25,
    )
    result["flow"] = "registration"
    save_persona_result(result, run_id)
    record_persona_result(result)

    assert result["friction_score"] is not None, "Friction score must be calculated"
    assert 1 <= result["friction_score"] <= 10, (
        f"Friction score {result['friction_score']} out of range"
    )


@pytest.mark.persona_agent
def test_non_native_browsing(agent_backend, claude_client, base_url, run_id, record_persona_result):
    """'NON_NATIVE' persona attempts browsing flow."""
    setup = _setup_browsing_flow()
    agent_backend.page.goto(setup["start_url"], timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_persona_scenario(
        backend=agent_backend,
        client=claude_client,
        persona=NON_NATIVE,
        flow_goal=FLOW_GOALS["browsing"],
        optimal_steps=OPTIMAL_STEPS["browsing"],
        max_iterations=25,
    )
    result["flow"] = "browsing"
    save_persona_result(result, run_id)
    record_persona_result(result)

    assert result["friction_score"] is not None, "Friction score must be calculated"
    assert 1 <= result["friction_score"] <= 10, (
        f"Friction score {result['friction_score']} out of range"
    )


@pytest.mark.persona_agent
def test_non_native_checkout(agent_backend, claude_client, base_url, run_id, record_persona_result):
    """'NON_NATIVE' persona attempts checkout flow."""
    setup = _setup_checkout_flow()
    agent_backend.page.goto(setup["start_url"], timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_persona_scenario(
        backend=agent_backend,
        client=claude_client,
        persona=NON_NATIVE,
        flow_goal=FLOW_GOALS["checkout"],
        optimal_steps=OPTIMAL_STEPS["checkout"],
        max_iterations=25,
    )
    result["flow"] = "checkout"
    save_persona_result(result, run_id)
    record_persona_result(result)

    assert result["friction_score"] is not None, "Friction score must be calculated"
    assert 1 <= result["friction_score"] <= 10, (
        f"Friction score {result['friction_score']} out of range"
    )


# -- IMPATIENT ----------------------------------------------------------------

@pytest.mark.persona_agent
def test_impatient_registration(agent_backend, claude_client, base_url, run_id, record_persona_result):
    """'IMPATIENT' persona attempts registration flow."""
    setup = _setup_registration_flow()
    agent_backend.page.goto(setup["start_url"], timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_persona_scenario(
        backend=agent_backend,
        client=claude_client,
        persona=IMPATIENT,
        flow_goal=FLOW_GOALS["registration"],
        optimal_steps=OPTIMAL_STEPS["registration"],
        max_iterations=15,
    )
    result["flow"] = "registration"
    save_persona_result(result, run_id)
    record_persona_result(result)

    assert result["friction_score"] is not None, "Friction score must be calculated"
    assert 1 <= result["friction_score"] <= 10, (
        f"Friction score {result['friction_score']} out of range"
    )


@pytest.mark.persona_agent
def test_impatient_browsing(agent_backend, claude_client, base_url, run_id, record_persona_result):
    """'IMPATIENT' persona attempts browsing flow."""
    setup = _setup_browsing_flow()
    agent_backend.page.goto(setup["start_url"], timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_persona_scenario(
        backend=agent_backend,
        client=claude_client,
        persona=IMPATIENT,
        flow_goal=FLOW_GOALS["browsing"],
        optimal_steps=OPTIMAL_STEPS["browsing"],
        max_iterations=15,
    )
    result["flow"] = "browsing"
    save_persona_result(result, run_id)
    record_persona_result(result)

    assert result["friction_score"] is not None, "Friction score must be calculated"
    assert 1 <= result["friction_score"] <= 10, (
        f"Friction score {result['friction_score']} out of range"
    )


@pytest.mark.persona_agent
def test_impatient_checkout(agent_backend, claude_client, base_url, run_id, record_persona_result):
    """'IMPATIENT' persona attempts checkout flow."""
    setup = _setup_checkout_flow()
    agent_backend.page.goto(setup["start_url"], timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_persona_scenario(
        backend=agent_backend,
        client=claude_client,
        persona=IMPATIENT,
        flow_goal=FLOW_GOALS["checkout"],
        optimal_steps=OPTIMAL_STEPS["checkout"],
        max_iterations=15,
    )
    result["flow"] = "checkout"
    save_persona_result(result, run_id)
    record_persona_result(result)

    assert result["friction_score"] is not None, "Friction score must be calculated"
    assert 1 <= result["friction_score"] <= 10, (
        f"Friction score {result['friction_score']} out of range"
    )
