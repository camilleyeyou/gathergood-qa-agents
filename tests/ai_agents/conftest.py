"""AI agent test fixtures — claude_client, agent_backend, skip-when-no-key,
report integration hooks, and configurable agent settings."""
import sys

import pytest
import anthropic

from settings import Settings
from tests.ai_agents.computer_use_backend import PlaywrightComputerBackend

try:
    from pytest_html import extras as html_extras
    HAS_PYTEST_HTML = True
except ImportError:
    HAS_PYTEST_HTML = False

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


@pytest.fixture(scope="session")
def agent_config():
    """Centralized, overridable agent configuration.

    Returns a dict with default max_iterations and model settings.
    Override in conftest or via fixture parametrize for custom scenarios.
    """
    return {"max_iterations": 20, "model": "claude-sonnet-4-6"}


@pytest.fixture(scope="function")
def record_agent_result(request):
    """Bridge between test functions and the pytest_runtest_makereport hook.

    Returns a callable that stores the agent result dict on the test item
    so the report hook can access it.

    Usage in tests:
        result = run_agent_scenario(...)
        record_agent_result(result)
        assert result["verdict"] != "FAIL", ...
    """
    def _record(result: dict):
        request.node._agent_result = result
    return _record


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Attach AI agent reasoning, verdict, and metrics to the HTML report
    and print a summary line to the console.

    Gracefully skips if _agent_result is not set (test crashed before
    recording or test doesn't use the record_agent_result fixture).
    """
    outcome = yield
    report = outcome.get_result()

    if report.when != "call":
        return

    # Only process tests with the ai_agent marker
    if not any(item.iter_markers("ai_agent")):
        return

    agent_result = getattr(item, "_agent_result", None)
    if agent_result is None:
        return

    verdict = agent_result.get("verdict", "UNKNOWN")
    steps = agent_result.get("steps", 0)
    input_tokens = agent_result.get("input_tokens", 0)
    output_tokens = agent_result.get("output_tokens", 0)
    reasoning = agent_result.get("reasoning", "")

    # Console output
    sys.stdout.write(
        f"\n[AI Agent] Verdict: {verdict} | Steps: {steps} "
        f"| Tokens: {input_tokens} in / {output_tokens} out\n"
    )
    reasoning_preview = reasoning[:200] + "..." if len(reasoning) > 200 else reasoning
    sys.stdout.write(f"[AI Agent] Reasoning: {reasoning_preview}\n")

    # HTML report extras
    if HAS_PYTEST_HTML:
        if not hasattr(report, "extras"):
            report.extras = []

        verdict_color = {
            "PASS": "#155724",
            "FAIL": "#721c24",
            "INCONCLUSIVE": "#856404",
        }.get(verdict, "#333")
        verdict_bg = {
            "PASS": "#d4edda",
            "FAIL": "#f8d7da",
            "INCONCLUSIVE": "#fff3cd",
        }.get(verdict, "#f8f9fa")

        html_content = (
            f'<div style="font-family:monospace;padding:10px;border:1px solid #dee2e6;'
            f'border-radius:4px;margin:5px 0;">'
            f'<p style="background:{verdict_bg};color:{verdict_color};'
            f'padding:6px 10px;border-radius:3px;display:inline-block;">'
            f'<strong>Verdict: {verdict}</strong></p>'
            f'<p><strong>Steps:</strong> {steps} | '
            f'<strong>Tokens:</strong> {input_tokens} in / {output_tokens} out</p>'
            f'<pre style="white-space:pre-wrap;background:#f8f9fa;padding:10px;'
            f'border-radius:4px;max-height:400px;overflow-y:auto;">{reasoning}</pre>'
            f'</div>'
        )
        report.extras.append(html_extras.html(html_content))
