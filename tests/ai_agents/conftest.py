"""AI agent test fixtures — claude_client, agent_backend, skip-when-no-key."""
import pytest
import anthropic

from settings import Settings
from tests.ai_agents.computer_use_backend import PlaywrightComputerBackend

_settings = Settings()

AGENT_SYSTEM_PROMPT = """\
You are a QA testing agent verifying the GatherGood event management platform.
Your task is to navigate the live website, perform the specified test scenario, and report your findings.

Rules:
- After each action, observe the screenshot carefully before proceeding.
- If something looks wrong or unexpected, note it in your reasoning.
- Do NOT fabricate observations — only report what you actually see in screenshots.
- When done, output your verdict on its own line: PASS, FAIL, or INCONCLUSIVE
- Provide brief reasoning explaining what you observed and why you chose that verdict.

Verdicts:
- PASS: The feature works as specified in the test goal.
- FAIL: The feature is broken, missing, or does not match the specification.
- INCONCLUSIVE: You could not complete the verification due to environment issues, timeouts, or ambiguity."""


def pytest_configure(config):
    """Register the ai_agent marker."""
    config.addinivalue_line(
        "markers", "ai_agent: AI QA agent test (requires ANTHROPIC_API_KEY)"
    )


def pytest_collection_modifyitems(config, items):
    """Skip all ai_agents tests when ANTHROPIC_API_KEY is not configured."""
    if _settings.ANTHROPIC_API_KEY:
        return
    skip_marker = pytest.mark.skip(
        reason="ANTHROPIC_API_KEY not configured in .env — skipping AI agent tests"
    )
    for item in items:
        if "ai_agents" in str(item.fspath):
            item.add_marker(skip_marker)


@pytest.fixture(scope="session")
def claude_client():
    """Anthropic client for Computer Use API calls.

    Session-scoped — one client shared across all agent tests.
    """
    return anthropic.Anthropic(api_key=_settings.ANTHROPIC_API_KEY)


@pytest.fixture(scope="function")
def agent_backend(page):
    """PlaywrightComputerBackend wrapping the current pytest-playwright page.

    Function-scoped — each test gets a fresh backend with a clean viewport.
    """
    return PlaywrightComputerBackend(page)


@pytest.fixture(scope="session")
def base_url():
    """Frontend base URL from settings."""
    return _settings.BASE_URL


@pytest.fixture(scope="session")
def api_url():
    """API base URL from settings."""
    return _settings.API_URL


@pytest.fixture(scope="session")
def agent_system_prompt():
    """Default system prompt for AI agent scenarios."""
    return AGENT_SYSTEM_PROMPT
