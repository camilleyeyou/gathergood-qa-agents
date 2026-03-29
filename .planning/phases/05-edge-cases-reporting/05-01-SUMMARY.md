---
phase: 05-edge-cases-reporting
plan: "01"
subsystem: reporting
tags: [pytest-html, playwright-tracing, requirement-coverage, test-reporting]
dependency_graph:
  requires: [conftest.py, tests/ui/conftest.py, pytest.ini]
  provides: [conftest_report.py, reports/report.html, reports/traces/, reports/screenshots/]
  affects: [every pytest run now auto-generates HTML report with requirement coverage]
tech_stack:
  added: [pytest-html 4.x hooks, Playwright tracing API]
  patterns:
    - hookwrapper with tryfirst for outcome capture in pytest_runtest_makereport
    - optionalhook for pytest_html_results_summary (pytest-html 4.x API)
    - Function-scoped context/page fixtures overriding pytest-playwright defaults
    - Sanitized node IDs for filesystem-safe trace/screenshot filenames
key_files:
  created:
    - conftest_report.py
  modified:
    - pytest.ini
    - tests/ui/conftest.py
decisions:
  - Always save Playwright traces (not just on failure) — simpler fixture, conftest_report.py selectively attaches for failures only
  - Use _status_rank() to handle worst-outcome tracking when a req ID appears on multiple tests
  - Use optionalhook=True decorator for pytest_html_results_summary to avoid errors when pytest-html not installed
  - Trace path uses _sanitize_nodeid() regex to replace all path-unsafe characters with underscores
metrics:
  duration: "2 minutes"
  completed_date: "2026-03-29"
  tasks_completed: 2
  files_created: 1
  files_modified: 2
---

# Phase 05 Plan 01: HTML Reporting with Requirement Coverage Summary

HTML reporting plugin (conftest_report.py) and Playwright tracing fixtures added to produce a single self-contained report.html on every pytest run, with a Requirements Coverage table mapping every TEST_SPEC req ID to PASS/FAIL/SKIP, and screenshot/trace attachments for failed browser tests.

## What Was Built

### Task 1: conftest_report.py + pytest.ini (TRPT-01, TRPT-02, TRPT-03 screenshot/trace)

Created `conftest_report.py` — a pytest plugin auto-loaded at project root — implementing three reporting hooks:

**pytest_sessionstart:** Creates `reports/screenshots/` and `reports/traces/` directories at session start so they exist before any test writes to them.

**pytest_runtest_makereport (hookwrapper, tryfirst):** Processes the `call` phase report to:
1. Extract `@pytest.mark.req("ID")` markers via `item.iter_markers("req")`, records outcome to `_req_results` dict (tracks worst outcome when multiple tests cover the same req ID)
2. For failed tests: captures a screenshot via `page.screenshot()` if a `page` fixture is present, then attaches screenshot PNG and Playwright trace ZIP to `report.extras` via `pytest_html.extras`

**pytest_html_results_summary (optionalhook):** Injects a "Requirements Coverage" section at the top of the HTML report summary with:
- Summary line: "X passed, Y failed, Z skipped out of N total (XX.X% pass rate)"
- Table with columns: Requirement ID, Test Name, Status — rows sorted by req ID, color-coded (green/red/yellow)

Updated `pytest.ini` addopts from `-v --tb=short` to `-v --tb=short --html=reports/report.html --self-contained-html` so every `pytest` invocation auto-generates the report.

### Task 2: tests/ui/conftest.py Playwright tracing (TRPT-03 trace capture)

Added two function-scoped fixtures that override pytest-playwright defaults:

**context fixture:** Wraps `browser.new_context()` with `ctx.tracing.start(screenshots=True, snapshots=True)` and always saves a trace ZIP to `reports/traces/{sanitized_nodeid}.zip` on teardown. Always saving (vs only on failure) keeps the fixture simple — conftest_report.py attaches the trace to the report only when the test failed.

**page fixture:** Creates a page from the traced context, yields it, and closes it. This is the `page` object that `conftest_report.py` captures screenshots from on failure.

All existing module-scoped fixtures (ui_test_user, ui_auth_client, ui_checkout_data, login_via_ui helper) are unchanged.

**Idempotency:** No code changes needed. The existing RUN_ID (uuid4 per session in factories/common.py) already ensures each run creates unique test-{uuid4}-prefixed resources, preventing data collisions across consecutive runs.

## Deviations from Plan

None — plan executed exactly as written. The "simpler approach" for tracing (always save, attach only on failure) was already the preferred approach documented in the plan.

## Known Stubs

None. All hooks are fully wired: markers flow from tests -> _req_results dict -> HTML table; page fixture flows from tracing context -> screenshot on failure -> report extras; pytest.ini auto-triggers HTML generation.

## Verification

```
python -c "
import ast
tree = ast.parse(open('conftest_report.py').read())
funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
assert 'pytest_runtest_makereport' in funcs
assert 'pytest_html_results_summary' in funcs
assert 'pytest_sessionstart' in funcs
ini = open('pytest.ini').read()
assert '--html=' in ini
assert '--self-contained-html' in ini
print('PASS')
"
```

## Self-Check: PASSED

- conftest_report.py: EXISTS (created at project root)
- pytest.ini: UPDATED (contains --html=reports/report.html --self-contained-html)
- tests/ui/conftest.py: UPDATED (context + page fixtures with tracing.start/stop)
- Task 1 commit e5b9a4d: EXISTS
- Task 2 commit fb15fd8: EXISTS
