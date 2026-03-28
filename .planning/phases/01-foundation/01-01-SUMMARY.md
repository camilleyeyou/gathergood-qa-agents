---
phase: 01-foundation
plan: 01
subsystem: testing
tags: [pytest, httpx, playwright, pydantic-settings, faker, jwt, fixtures]

# Dependency graph
requires: []
provides:
  - pytest 9.0.2 test harness scaffold with directory structure
  - pydantic-settings Settings class for type-safe env config
  - uuid4-prefixed data factories (unique_email, org_name, event_title, venue_name)
  - httpx assert_status helper
  - session-scoped auth_client fixture with JWT auto-refresh
  - session-scoped teardown_registry for resource cleanup tracking
  - pytest_configure for req(id) marker registration
  - pytest_sessionstart health check against Railway backend
affects: [02-api-tests, 03-ui-tests, 04-integration, 05-reporting]

# Tech tracking
tech-stack:
  added:
    - pytest==9.0.2
    - httpx==0.28.1
    - playwright==1.58.0
    - pytest-playwright==0.7.2
    - pydantic-settings==2.13.1
    - python-dotenv>=1.0.0
    - faker>=33.0.0
    - pytest-html>=4.0.0
  patterns:
    - RUN_ID-prefixed test data for live DB isolation (no rollback available)
    - Session-scoped auth fixture with proactive JWT refresh (15% margin or 60s)
    - Base64 JWT decode without PyJWT dependency
    - Session teardown registry for reverse-order resource cleanup

key-files:
  created:
    - requirements.txt
    - settings.py
    - conftest.py
    - factories/common.py
    - helpers/api.py
    - pytest.ini
    - .env.example
    - .gitignore
    - tests/__init__.py
    - tests/api/__init__.py
    - tests/ui/__init__.py
    - tests/smoke/__init__.py
    - factories/__init__.py
    - helpers/__init__.py
    - reports/.gitkeep
  modified: []

key-decisions:
  - "Install packages for both Python 3.11 (python) and Python 3.13 (pytest CLI) to ensure all entry points work"
  - "pytest exit code 5 (NO_TESTS_COLLECTED) is correct for empty test suite — not an error, no import issues"
  - "Health check accepts 404 on API root (only 5xx or connection failure aborts session)"

patterns-established:
  - "RUN_ID prefix pattern: all test data prefixed with test-{8hex} to identify and clean up per-run data"
  - "JWT decode pattern: base64.urlsafe_b64decode without PyJWT, fallback exp to time.time()+300"
  - "Token refresh pattern: check remaining < max(60, ttl*0.15) before each request"

requirements-completed: [INFR-01, INFR-02, INFR-04, INFR-06, INFR-07]

# Metrics
duration: 7min
completed: 2026-03-28
---

# Phase 01 Plan 01: Foundation Scaffold Summary

**pytest 9.0.2 test harness with pydantic-settings config, uuid4 data factories, session-scoped JWT auth client with auto-refresh, and teardown registry — all validated via `pytest --co` with zero import errors**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-03-28T19:32:30Z
- **Completed:** 2026-03-28T19:39:57Z
- **Tasks:** 3
- **Files modified:** 15

## Accomplishments
- Full project scaffold (requirements.txt, pytest.ini, .env.example, .gitignore, all __init__.py files, reports/.gitkeep)
- Type-safe settings via pydantic-settings with default API_URL and BASE_URL
- uuid4-prefixed data factories ensuring test isolation against live DB with no rollback
- Root conftest.py with backend health check, req marker, teardown registry, and session auth client
- JWT auto-refresh using base64 decode (no external dependency) with 15%/60s margin
- All 8 packages importable; `pytest --co` completes with no import errors or marker warnings

## Task Commits

Each task was committed atomically:

1. **Task 1: Install dependencies and create project scaffold** - `bec0d29` (feat)
2. **Task 2: Create settings, factories, and helpers modules** - `d4083da` (feat)
3. **Task 3: Create root conftest.py with auth fixture, teardown registry, health check, and markers** - `84792da` (feat)

## Files Created/Modified
- `requirements.txt` - Pinned pytest==9.0.2, httpx==0.28.1, playwright==1.58.0, pydantic-settings==2.13.1 and supporting packages
- `pytest.ini` - testpaths=tests, addopts=-v --tb=short, req(id) marker declaration
- `.env.example` - API_URL and BASE_URL placeholders for live Railway/Vercel endpoints
- `.gitignore` - Excludes .env, __pycache__, reports/*.html/xml, playwright/.auth/
- `settings.py` - Settings class with API_URL, BASE_URL, STRIPE_TEST_KEY fields with defaults
- `factories/common.py` - RUN_ID + unique_email(), org_name(), event_title(), venue_name()
- `helpers/api.py` - assert_status() with URL and body in error messages
- `conftest.py` - pytest_configure, pytest_sessionstart, teardown_registry, auth_client

## Decisions Made
- Installed packages for both Python 3.11 (`python`) and Python 3.13 (`pytest` CLI binary) since both are on PATH and pip defaults to 3.13
- Exit code 5 from `pytest --co` on empty test suite is correct pytest 9 behavior (NO_TESTS_COLLECTED), not an error
- API health check accepts 404 on root endpoint since DRF may not define a view there — only 5xx or connection failure aborts

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed packages for both Python 3.11 and Python 3.13**
- **Found during:** Task 1 (dependency installation)
- **Issue:** `pip` on this machine is Python 3.13's pip, but the `python` binary resolves to Python 3.11. Initial install only covered Python 3.13. The plan's verification command `python -c "import pytest..."` uses Python 3.11 which had no packages.
- **Fix:** Ran `pip-3.11 install -r requirements.txt` to install packages for both Python versions.
- **Files modified:** None (system-level pip install)
- **Verification:** `python -c "import pytest, httpx, playwright, pydantic_settings, faker"` exits 0 on both Python versions
- **Committed in:** bec0d29 (Task 1 commit, structural fix inline)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary for cross-Python-version compatibility on this machine. No scope creep.

## Issues Encountered
- `pytest --co` returns exit code 5 (NO_TESTS_COLLECTED) not 0 — this is correct pytest 9 behavior and confirms zero import errors; exit code 2 would indicate import failures

## User Setup Required
None - no external service configuration required. Create a `.env` file from `.env.example` before running tests that make live network calls (Phase 2+).

## Next Phase Readiness
- All infrastructure fixtures available for Phase 2 API tests
- Settings class ready for .env-based configuration
- auth_client fixture will make live network call to Railway backend when tests actually run (not during --co)
- Known concern: pytest_sessionstart health check will run on first non-collection invocation — must verify live backend is up

---
*Phase: 01-foundation*
*Completed: 2026-03-28*
