"""pytest-html reporting plugin for GatherGood E2E test suite.

Implements:
- TRPT-01: Collect requirement IDs from @pytest.mark.req markers
- TRPT-02: Generate requirement coverage summary table in HTML report
- TRPT-03: Attach screenshots and Playwright trace files for failed browser tests

Auto-loaded by pytest as a conftest plugin (placed at project root).
"""
import os
import re

import pytest


# Session-level storage for requirement ID -> test outcome mapping.
# Populated by pytest_runtest_makereport; consumed by pytest_html_results_summary.
_req_results: dict = {}


def pytest_sessionstart(session):
    """Create reports directory tree at session start."""
    os.makedirs(os.path.join("reports", "screenshots"), exist_ok=True)
    os.makedirs(os.path.join("reports", "traces"), exist_ok=True)


def _sanitize_nodeid(nodeid: str) -> str:
    """Convert a pytest node ID to a filesystem-safe string."""
    safe = re.sub(r"[/\\::\[\]<>|?*]", "_", nodeid)
    # Collapse consecutive underscores
    safe = re.sub(r"_+", "_", safe)
    return safe.strip("_")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test outcomes, attach screenshots/traces for failed browser tests,
    and record requirement ID coverage.

    Runs with tryfirst=True so we get the report object after test execution.
    """
    outcome = yield
    report = outcome.get_result()

    # Only process the 'call' phase (not setup/teardown)
    if report.when != "call":
        return

    # --- TRPT-01: Record requirement ID outcomes ---
    for marker in item.iter_markers("req"):
        if marker.args:
            req_id = marker.args[0]
            if report.passed:
                status = "PASS"
            elif report.failed:
                status = "FAIL"
            else:
                status = "SKIP"

            # Keep the worst outcome if a req ID appears on multiple tests
            existing = _req_results.get(req_id)
            if existing is None or _status_rank(status) > _status_rank(existing["status"]):
                _req_results[req_id] = {
                    "test_name": item.name,
                    "nodeid": item.nodeid,
                    "status": status,
                }

    # --- TRPT-03: Attach screenshot and trace for failed browser tests ---
    if report.failed:
        try:
            import pytest_html
        except ImportError:
            return

        page = item.funcargs.get("page") if hasattr(item, "funcargs") else None

        # Ensure extras list exists on report
        if not hasattr(report, "extras"):
            report.extras = []

        safe_name = _sanitize_nodeid(item.nodeid)

        # Screenshot
        if page is not None:
            screenshot_path = os.path.join("reports", "screenshots", f"{safe_name}.png")
            try:
                page.screenshot(path=screenshot_path)
                report.extras.append(pytest_html.extras.png(screenshot_path))
            except Exception as exc:
                print(f"\n[conftest_report] WARNING: Could not capture screenshot: {exc}")

        # Trace (written by tests/ui/conftest.py tracing fixture)
        trace_path = os.path.join("reports", "traces", f"{safe_name}.zip")
        if os.path.exists(trace_path):
            report.extras.append(
                pytest_html.extras.url(trace_path, name="Playwright Trace")
            )


def _status_rank(status: str) -> int:
    """Return a numeric rank for status priority (FAIL > SKIP > PASS)."""
    return {"FAIL": 2, "SKIP": 1, "PASS": 0}.get(status, 0)


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_summary(prefix, summary, postfix):
    """Inject a Requirements Coverage table into the HTML report summary section.

    Implements TRPT-02: table with columns Requirement ID, Test Name, Status,
    plus a summary line showing counts and pass percentage.
    """
    if not _req_results:
        prefix.append("<p>No @pytest.mark.req markers found in this test run.</p>")
        return

    total = len(_req_results)
    passed = sum(1 for v in _req_results.values() if v["status"] == "PASS")
    failed = sum(1 for v in _req_results.values() if v["status"] == "FAIL")
    skipped = sum(1 for v in _req_results.values() if v["status"] == "SKIP")
    pass_pct = (passed / total * 100) if total > 0 else 0.0

    # Build summary line
    summary_line = (
        f"<p><strong>Requirements:</strong> "
        f"{passed} passed, {failed} failed, {skipped} skipped "
        f"out of {total} total ({pass_pct:.1f}% pass rate)</p>"
    )

    # Build HTML table rows sorted by requirement ID
    rows_html = []
    for req_id in sorted(_req_results.keys()):
        entry = _req_results[req_id]
        status = entry["status"]
        test_name = entry["test_name"]

        if status == "PASS":
            bg = "#d4edda"
            color = "#155724"
        elif status == "FAIL":
            bg = "#f8d7da"
            color = "#721c24"
        else:  # SKIP
            bg = "#fff3cd"
            color = "#856404"

        rows_html.append(
            f'<tr style="background-color:{bg};color:{color};">'
            f"<td>{req_id}</td>"
            f"<td>{test_name}</td>"
            f'<td><strong>{status}</strong></td>'
            f"</tr>"
        )

    table_html = (
        "<h2>Requirements Coverage</h2>"
        + summary_line
        + "<table style='border-collapse:collapse;width:100%;font-family:monospace;font-size:0.9em;'>"
        + "<thead>"
        + "<tr style='background-color:#343a40;color:#fff;'>"
        + "<th style='padding:8px;text-align:left;border:1px solid #dee2e6;'>Requirement ID</th>"
        + "<th style='padding:8px;text-align:left;border:1px solid #dee2e6;'>Test Name</th>"
        + "<th style='padding:8px;text-align:left;border:1px solid #dee2e6;'>Status</th>"
        + "</tr>"
        + "</thead>"
        + "<tbody>"
        + "".join(
            r.replace("<td>", "<td style='padding:6px 8px;border:1px solid #dee2e6;'>")
            for r in rows_html
        )
        + "</tbody>"
        + "</table>"
    )

    prefix.append(table_html)
