"""AI agent scenarios for permission boundary verification."""
import httpx
import pytest

from factories.common import unique_email, org_name, event_title, tier_name
from helpers.api import assert_status
from settings import Settings
from tests.ai_agents.agent_runner import run_agent_scenario

_settings = Settings()


def _create_org_with_volunteer():
    """Create an org with OWNER and invite a VOLUNTEER user.

    Returns dict with: owner_email, owner_password, volunteer_email,
    volunteer_password, org_slug, org_name.
    """
    owner_email = unique_email()
    volunteer_email = unique_email()
    password = "AgentTest123!"

    with httpx.Client(base_url=_settings.API_URL, timeout=30) as client:
        # Register owner
        reg_resp = client.post(
            "/auth/register/",
            json={
                "email": owner_email,
                "password": password,
                "password_confirm": password,
                "first_name": "Agent",
                "last_name": "Owner",
            },
        )
        assert_status(reg_resp, 201, "permissions_agent: Register owner")

        # Login owner
        login_resp = client.post(
            "/auth/login/",
            json={"email": owner_email, "password": password},
        )
        assert_status(login_resp, 200, "permissions_agent: Login owner")
        owner_access = login_resp.json()["access"]

        client.headers["Authorization"] = f"Bearer {owner_access}"

        # Create org
        name = org_name()
        org_resp = client.post(
            "/organizations/",
            json={"name": name, "description": "AI agent permissions test org"},
        )
        assert_status(org_resp, 201, "permissions_agent: Create org")
        org_slug = org_resp.json()["slug"]

        # Register volunteer
        vol_reg_resp = client.post(
            "/auth/register/",
            json={
                "email": volunteer_email,
                "password": password,
                "password_confirm": password,
                "first_name": "Agent",
                "last_name": "Volunteer",
            },
            headers={"Authorization": ""},  # Clear auth for registration
        )
        # Registration may not need auth header cleared — try with, then without
        if vol_reg_resp.status_code != 201:
            del client.headers["Authorization"]
            vol_reg_resp = client.post(
                "/auth/register/",
                json={
                    "email": volunteer_email,
                    "password": password,
                    "password_confirm": password,
                    "first_name": "Agent",
                    "last_name": "Volunteer",
                },
            )
            client.headers["Authorization"] = f"Bearer {owner_access}"
        assert_status(vol_reg_resp, 201, "permissions_agent: Register volunteer")

        # Invite volunteer to org
        invite_resp = client.post(
            f"/organizations/{org_slug}/members/invite/",
            json={
                "email": volunteer_email,
                "role": "VOLUNTEER",
            },
        )
        assert_status(invite_resp, 201, "permissions_agent: Invite volunteer")

    return {
        "owner_email": owner_email,
        "owner_password": password,
        "volunteer_email": volunteer_email,
        "volunteer_password": password,
        "org_slug": org_slug,
        "org_name": name,
    }


def _create_org_with_non_member():
    """Create an org and a separate non-member user.

    Returns dict with: owner_email, owner_password, non_member_email,
    non_member_password, org_slug.
    """
    owner_email = unique_email()
    non_member_email = unique_email()
    password = "AgentTest123!"

    with httpx.Client(base_url=_settings.API_URL, timeout=30) as client:
        # Register owner
        reg_resp = client.post(
            "/auth/register/",
            json={
                "email": owner_email,
                "password": password,
                "password_confirm": password,
                "first_name": "Agent",
                "last_name": "OrgOwner",
            },
        )
        assert_status(reg_resp, 201, "permissions_agent: Register owner")

        # Login owner
        login_resp = client.post(
            "/auth/login/",
            json={"email": owner_email, "password": password},
        )
        assert_status(login_resp, 200, "permissions_agent: Login owner")
        owner_access = login_resp.json()["access"]

        client.headers["Authorization"] = f"Bearer {owner_access}"

        # Create org
        name = org_name()
        org_resp = client.post(
            "/organizations/",
            json={"name": name, "description": "AI agent non-member test org"},
        )
        assert_status(org_resp, 201, "permissions_agent: Create org")
        org_slug = org_resp.json()["slug"]

        # Register non-member (no org invitation)
        del client.headers["Authorization"]
        nm_reg_resp = client.post(
            "/auth/register/",
            json={
                "email": non_member_email,
                "password": password,
                "password_confirm": password,
                "first_name": "Agent",
                "last_name": "NonMember",
            },
        )
        assert_status(nm_reg_resp, 201, "permissions_agent: Register non-member")

    return {
        "owner_email": owner_email,
        "owner_password": password,
        "non_member_email": non_member_email,
        "non_member_password": password,
        "org_slug": org_slug,
    }


@pytest.mark.req("AIQA-08")
@pytest.mark.ai_agent
def test_permission_boundary_volunteer_agent(
    agent_backend, claude_client, base_url, agent_system_prompt, record_agent_result
):
    """AI agent verifies volunteer role restrictions on org dashboard."""
    data = _create_org_with_volunteer()

    agent_backend.page.goto(f"{base_url}/login", timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_agent_scenario(
        backend=agent_backend,
        client=claude_client,
        goal=(
            f"You are on the GatherGood login page. Log in with email "
            f"'{data['volunteer_email']}' and password "
            f"'{data['volunteer_password']}'. "
            "After login, navigate to the organization dashboard. Verify: "
            "1) You can see the organization page. "
            "2) You do NOT see options to create new events (no 'Create Event' "
            "button, or it is disabled/hidden). "
            "3) You do NOT see options to invite/manage team members. "
            "Report PASS if the volunteer role correctly restricts event creation "
            "and team management, FAIL if you can access these restricted features, "
            "INCONCLUSIVE if you cannot determine the restrictions."
        ),
        system_prompt=agent_system_prompt,
        max_iterations=18,
    )
    record_agent_result(result)

    assert result["verdict"] != "FAIL", (
        f"Agent reported FAIL after {result['steps']} steps.\n"
        f"Reasoning: {result['reasoning']}"
    )


@pytest.mark.req("AIQA-08")
@pytest.mark.ai_agent
def test_permission_boundary_non_member_agent(
    agent_backend, claude_client, base_url, agent_system_prompt, record_agent_result
):
    """AI agent verifies non-members cannot access org management."""
    data = _create_org_with_non_member()

    agent_backend.page.goto(f"{base_url}/login", timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_agent_scenario(
        backend=agent_backend,
        client=claude_client,
        goal=(
            f"You are on the GatherGood login page. Log in with email "
            f"'{data['non_member_email']}' and password "
            f"'{data['non_member_password']}'. "
            "After login, try to access an organization's dashboard or "
            "management pages. Verify: "
            "1) You cannot see other organizations' private dashboards. "
            "2) Attempting to access management URLs shows an error, redirect, "
            "or empty state. "
            "Report PASS if non-members are properly restricted, FAIL if you "
            "can access organization management features."
        ),
        system_prompt=agent_system_prompt,
        max_iterations=15,
    )
    record_agent_result(result)

    assert result["verdict"] != "FAIL", (
        f"Agent reported FAIL after {result['steps']} steps.\n"
        f"Reasoning: {result['reasoning']}"
    )
