---
phase: 01-foundation
plan: 02
subsystem: testing
tags: [pytest, httpx, smoke-tests, auth, jwt, factories, teardown-registry]

# Dependency graph
requires:
  - phase: 01-foundation plan 01
    provides: conftest.py, settings.py, factories/common.py, helpers/api.py — full harness foundation

provides:
  - 16 smoke tests validating every non-network and live-backend aspect of the Phase 1 harness
  - Live registration + login + authenticated request verified against Railway backend
  - Factory uniqueness, teardown registry, marker, and import correctness proven

affects:
  - 02-auth-tests
  - All future phases — these smoke tests serve as the harness health check baseline

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "@pytest.mark.req decorator pattern for tracing tests to TEST_SPEC.md requirement IDs"
    - "session-scoped teardown_registry fixture accumulates resource IDs for cleanup"
    - "auth_client fixture: register + login + _maybe_refresh pattern for JWT auto-refresh"

key-files:
  created:
    - tests/smoke/test_smoke.py
    - tests/smoke/test_factories.py
    - tests/smoke/test_teardown.py
    - tests/smoke/test_auth_fixture.py
  modified:
    - conftest.py

key-decisions:
  - "Live API requires password_confirm field on registration — conftest.py updated to include it"
  - "test_teardown_registry_has_expected_keys uses issubset (not equality) to allow extra keys auth_client adds"

patterns-established:
  - "smoke tests run with single command: pytest tests/smoke/ -v"
  - "non-network tests separated from live-backend tests within same suite but grouped by fixture dependency"

requirements-completed: [INFR-03, INFR-05, INFR-07]

# Metrics
duration: 3min
completed: 2026-03-28
---

# Phase 01 Plan 02: Smoke Tests Summary

**16 pytest smoke tests verify the Phase 1 harness end-to-end: imports, settings, factory uniqueness, teardown registry, JWT auth against live Railway backend, and single-command suite execution**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-28T19:43:10Z
- **Completed:** 2026-03-28T19:46:18Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- 13 non-network tests: imports, settings load, factory format/uniqueness, teardown registry accumulation, marker registration
- 3 live-backend tests: auth_client fixture registers, logs in, and makes authenticated requests against Railway
- JWT TTL decoding confirmed working (log line "[auth_client] JWT TTL: Xs" printed during live test)
- No PytestUnknownMarkWarning — @pytest.mark.req marker registered correctly
- Single command `pytest tests/smoke/ -v` runs all 16 tests and exits 0

## Task Commits

Each task was committed atomically:

1. **Task 1: Non-network smoke tests (imports, factories, teardown)** - `a50cddc` (feat)
2. **Task 2: Auth fixture integration test + conftest fix** - `0fd8840` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `tests/smoke/test_smoke.py` - Import, settings, marker, and collection smoke tests
- `tests/smoke/test_factories.py` - RUN_ID format, unique_email/org/event/venue format and no-collision tests
- `tests/smoke/test_teardown.py` - Registry key presence, accumulation, and list-type assertion tests
- `tests/smoke/test_auth_fixture.py` - Live backend: register, login, authenticated GET, refresh capability, method existence
- `conftest.py` - Added password_confirm field to registration payload (live API validation requirement)

## Decisions Made
- `password_confirm` field added to registration payload — live API returns 400 without it (confirmed empirically)
- `test_teardown_registry_has_expected_keys` uses `issubset` rather than strict equality — `auth_client` fixture appends `test_user_email` (a string, not a list key) to the registry, so strict equality would fail when both fixtures are active in the same session

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed registration payload missing password_confirm field**
- **Found during:** Task 2 (auth fixture integration test)
- **Issue:** Live API `/auth/register/` returned 400 with body `{"password_confirm":["This field is required."]}` — the conftest.py registration payload omitted this field
- **Fix:** Added `"password_confirm": password` to the registration JSON in conftest.py `auth_client` fixture
- **Files modified:** conftest.py
- **Verification:** All 3 auth tests PASSED, registration returns 201
- **Committed in:** `0fd8840` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Essential correctness fix — the live API requires password_confirm; without it the entire auth fixture setup fails. No scope creep.

## Issues Encountered
- Transient `httpx.ConnectError: Connection reset by peer` on first run of non-network tests — re-running immediately succeeded. Not a recurring issue; Railway backend was momentarily unresponsive.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 1 foundation fully validated — all 16 smoke tests green
- auth_client fixture confirmed working against live Railway backend
- Teardown registry, factories, and markers all confirmed operational
- Phase 2 can write API domain tests directly using auth_client and teardown_registry fixtures
- Known blocker carried forward: Stripe mode (test vs live) of deployed backend still unconfirmed — Phase 3 concern

---
*Phase: 01-foundation*
*Completed: 2026-03-28*
