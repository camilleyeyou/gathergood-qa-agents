"""AI agent scenarios for authentication flows."""
import httpx
import pytest

from factories.common import unique_email
from helpers.api import assert_status
from settings import Settings
from tests.ai_agents.agent_runner import run_agent_scenario

_settings = Settings()


@pytest.mark.req("AIQA-04")
@pytest.mark.ai_agent
def test_auth_login_page_agent(agent_backend, claude_client, base_url, agent_system_prompt, record_agent_result):
    """AI agent verifies login page has all expected form elements."""
    agent_backend.page.goto(f"{base_url}/login", timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_agent_scenario(
        backend=agent_backend,
        client=claude_client,
        goal=(
            "You are on the GatherGood login page. Verify: "
            "1) There is an email input field. "
            "2) There is a password input field. "
            "3) There is a Login/Sign In submit button. "
            "4) There is a link to the registration page. "
            "Report PASS if all four elements are visible, FAIL otherwise."
        ),
        system_prompt=agent_system_prompt,
        max_iterations=10,
    )
    record_agent_result(result)

    assert result["verdict"] != "FAIL", (
        f"Agent reported FAIL after {result['steps']} steps.\n"
        f"Reasoning: {result['reasoning']}"
    )


@pytest.mark.req("AIQA-04")
@pytest.mark.ai_agent
def test_auth_register_page_agent(agent_backend, claude_client, base_url, agent_system_prompt, record_agent_result):
    """AI agent verifies registration page has all expected form elements."""
    agent_backend.page.goto(f"{base_url}/register", timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_agent_scenario(
        backend=agent_backend,
        client=claude_client,
        goal=(
            "You are on the GatherGood registration page. Verify: "
            "1) There are input fields for email, password, first name, and last name. "
            "2) There is a Register/Sign Up submit button. "
            "3) There is a link back to the login page. "
            "Report PASS if all elements are present, FAIL otherwise."
        ),
        system_prompt=agent_system_prompt,
        max_iterations=10,
    )
    record_agent_result(result)

    assert result["verdict"] != "FAIL", (
        f"Agent reported FAIL after {result['steps']} steps.\n"
        f"Reasoning: {result['reasoning']}"
    )


@pytest.mark.req("AIQA-04")
@pytest.mark.ai_agent
def test_auth_login_flow_agent(agent_backend, claude_client, base_url, agent_system_prompt, record_agent_result):
    """AI agent performs a full login flow with a real test user."""
    # Create a test user via API before agent runs
    email = unique_email()
    password = "AgentTest123!"

    with httpx.Client(base_url=_settings.API_URL, timeout=30) as client:
        reg_resp = client.post(
            "/auth/register/",
            json={
                "email": email,
                "password": password,
                "password_confirm": password,
                "first_name": "Agent",
                "last_name": "Tester",
            },
        )
        assert_status(reg_resp, 201, "test_auth_login_flow_agent: Register test user")

    agent_backend.page.goto(f"{base_url}/login", timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_agent_scenario(
        backend=agent_backend,
        client=claude_client,
        goal=(
            f"You are on the GatherGood login page. "
            f"Type the email '{email}' into the email field and "
            f"'{password}' into the password field. Click the login button. "
            f"After login, verify that the page navigates away from /login and "
            f"shows a dashboard or home page with user-specific content "
            f"(like a navigation menu with Dashboard or profile links). "
            f"Report PASS if login succeeds and you see authenticated content, "
            f"FAIL if login fails or you remain on the login page."
        ),
        system_prompt=agent_system_prompt,
        max_iterations=15,
    )
    record_agent_result(result)

    assert result["verdict"] != "FAIL", (
        f"Agent reported FAIL after {result['steps']} steps.\n"
        f"Reasoning: {result['reasoning']}"
    )
