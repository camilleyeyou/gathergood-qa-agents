"""Persona agent test fixtures — claude_client, agent_backend, skip-when-no-key,
run_id, report generation hook, and per-test result recording."""
import os
import sys
import uuid

# Set PLAYWRIGHT_BROWSERS_PATH before importing playwright/pytest-playwright
# so it finds browsers installed at /app/.browsers on Railway.
if os.path.exists("/app/.browsers"):
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/app/.browsers"

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

# Module-level list to accumulate results across all persona tests in the session.
_collected_results: list[dict] = []

# Module-level storage for the session run_id so pytest_sessionfinish can access it.
_session_run_id: str = ""


def pytest_configure(config):
    """Register the persona_agent marker."""
    config.addinivalue_line(
        "markers",
        "persona_agent: Digital literacy persona agent test (requires ANTHROPIC_API_KEY)",
    )


def pytest_collection_modifyitems(config, items):
    """Skip all persona_agents tests when ANTHROPIC_API_KEY is not configured."""
    if _settings.ANTHROPIC_API_KEY:
        return
    skip_marker = pytest.mark.skip(
        reason="ANTHROPIC_API_KEY not configured in .env -- skipping persona agent tests"
    )
    for item in items:
        if "persona_agents" in str(item.fspath):
            item.add_marker(skip_marker)


@pytest.fixture(scope="session")
def claude_client():
    """Anthropic client for Computer Use API calls.

    Session-scoped — one client shared across all persona tests.
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
def run_id():
    """Unique run identifier for this test session.

    Session-scoped — all tests in a run share the same run_id so JSON
    artifacts and the HTML report land in the same directory.
    """
    global _session_run_id
    _session_run_id = f"run_{uuid.uuid4().hex[:8]}"
    return _session_run_id


@pytest.fixture(scope="function")
def record_persona_result(request):
    """Bridge between test functions and the report hook / sessionfinish.

    Returns a callable that:
      1. Appends the result dict to the module-level _collected_results list.
      2. Stores the result on request.node._persona_result for the makereport hook.

    Usage in tests::

        result = run_persona_scenario(...)
        record_persona_result(result)
    """
    def _record(result: dict) -> None:
        _collected_results.append(result)
        request.node._persona_result = result

    return _record


def pytest_sessionfinish(session, exitstatus):
    """Generate the HTML matrix report after all persona tests finish.

    Runs only when at least one result was recorded.  Import errors and
    missing templates are caught so they never fail the overall test run.
    """
    if not _collected_results:
        return

    run_id_value = _session_run_id or "run_unknown"
    output_dir = f"reports/persona/{run_id_value}"

    try:
        from scripts.generate_persona_report import generate_report_from_results
        path = generate_report_from_results(_collected_results, run_id_value, output_dir)
        sys.stdout.write(f"\n[Persona Report] Generated: {path}\n")
    except Exception as exc:  # noqa: BLE001
        sys.stdout.write(f"\n[Persona Report] Could not generate report: {exc}\n")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Attach persona friction score, verdict, and metrics to the HTML report
    and print a console summary line per test.

    Gracefully skips if _persona_result is not set (test crashed before
    recording or test doesn't use the record_persona_result fixture).
    """
    outcome = yield
    report = outcome.get_result()

    if report.when != "call":
        return

    # Only process tests with the persona_agent marker.
    if not any(item.iter_markers("persona_agent")):
        return

    persona_result = getattr(item, "_persona_result", None)
    if persona_result is None:
        return

    persona = persona_result.get("persona", "UNKNOWN")
    flow = persona_result.get("flow", "UNKNOWN")
    friction_score = persona_result.get("friction_score", 0)
    verdict = persona_result.get("verdict", "UNKNOWN")
    steps_taken = persona_result.get("steps_taken", 0)
    tokens_used = persona_result.get("tokens_used", 0)

    # Console summary line.
    sys.stdout.write(
        f"\n[Persona] {persona}/{flow} | Friction: {friction_score}/10 "
        f"| Verdict: {verdict} | Steps: {steps_taken} | Tokens: {tokens_used}\n"
    )

    confusion_points = persona_result.get("confusion_points", [])
    if confusion_points:
        sys.stdout.write(
            f"[Persona] Confusion points: {len(confusion_points)} — "
            f"{confusion_points[0].get('description', '')[:100]}\n"
        )

    # HTML report extras.
    if HAS_PYTEST_HTML:
        if not hasattr(report, "extras"):
            report.extras = []

        if friction_score <= 3:
            score_color, score_bg = "#155724", "#d4edda"  # green
        elif friction_score <= 6:
            score_color, score_bg = "#856404", "#fff3cd"  # yellow
        else:
            score_color, score_bg = "#721c24", "#f8d7da"  # red

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

        confusion_html = ""
        if confusion_points:
            items_html = "".join(
                f"<li><strong>Step {cp.get('step', '?')} [{cp.get('severity', '?')}]:</strong> "
                f"{cp.get('description', '')}</li>"
                for cp in confusion_points[:5]
            )
            confusion_html = f"<ul>{items_html}</ul>"

        html_content = (
            f'<div style="font-family:monospace;padding:10px;border:1px solid #dee2e6;'
            f'border-radius:4px;margin:5px 0;">'
            f'<p><strong>Persona:</strong> {persona} | <strong>Flow:</strong> {flow}</p>'
            f'<p style="background:{score_bg};color:{score_color};'
            f'padding:6px 10px;border-radius:3px;display:inline-block;">'
            f'<strong>Friction Score: {friction_score}/10</strong></p>'
            f'&nbsp;'
            f'<span style="background:{verdict_bg};color:{verdict_color};'
            f'padding:6px 10px;border-radius:3px;">'
            f'<strong>Verdict: {verdict}</strong></span>'
            f'<p><strong>Steps taken:</strong> {steps_taken} | '
            f'<strong>Tokens used:</strong> {tokens_used}</p>'
        )
        if confusion_points:
            html_content += (
                f'<p><strong>Confusion points ({len(confusion_points)}):</strong></p>'
                f'{confusion_html}'
            )
        html_content += "</div>"

        report.extras.append(html_extras.html(html_content))
