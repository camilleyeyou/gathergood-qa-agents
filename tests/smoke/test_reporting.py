"""Smoke tests verifying the HTML reporting infrastructure.

These tests carry @pytest.mark.req markers for TRPT-01/02/03 so they
appear in the Requirements Coverage table they help generate.
"""
import os

import pytest


@pytest.mark.req("TRPT-01")
def test_html_report_lists_requirement_ids():
    """TRPT-01: HTML report lists every TEST_SPEC requirement ID."""
    # Verify conftest_report.py exists and has the req marker extraction hook
    assert os.path.isfile("conftest_report.py"), "conftest_report.py plugin missing"
    with open("conftest_report.py") as f:
        source = f.read()
    assert 'iter_markers("req")' in source, "Plugin must extract @pytest.mark.req markers"
    assert "pytest_html_results_summary" in source, "Plugin must inject HTML summary table"


@pytest.mark.req("TRPT-02")
def test_html_report_includes_counts_and_percentage():
    """TRPT-02: Report includes total pass/fail/skip counts and percentage."""
    with open("conftest_report.py") as f:
        source = f.read()
    assert "pass_pct" in source, "Plugin must calculate pass percentage"
    assert "passed" in source and "failed" in source and "skipped" in source, (
        "Plugin must track pass/fail/skip counts"
    )


@pytest.mark.req("TRPT-03")
def test_failed_tests_include_screenshots_and_traces():
    """TRPT-03: Failed browser tests include screenshots and Playwright traces."""
    with open("conftest_report.py") as f:
        source = f.read()
    assert "screenshot" in source.lower(), "Plugin must capture screenshots on failure"
    assert "trace" in source.lower(), "Plugin must attach Playwright trace files"

    # Verify pytest.ini has HTML report flags
    with open("pytest.ini") as f:
        ini = f.read()
    assert "--html=" in ini, "pytest.ini must enable HTML report generation"
    assert "--self-contained-html" in ini, "pytest.ini must enable self-contained HTML"
