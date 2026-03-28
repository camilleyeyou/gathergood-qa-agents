---
phase: 04-permissions-analytics-browser-ui
plan: 01
subsystem: testing
tags: [pytest, httpx, permissions, rbac, role-based-access-control]

# Dependency graph
requires:
  - phase: 02-core-api-tests
    provides: _create_user_client pattern, org fixture, auth_client fixture
  - phase: 01-foundation
    provides: conftest.py auth_client, teardown_registry, unique_email factories
provides:
  - Permission boundary tests for VOLUNTEER, MANAGER, and non-member roles (TPERM-01 to TPERM-05)
affects: [04-02, 04-03, 04-04, 04-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Module-scoped role-client fixtures (volunteer_client, manager_client, non_member_client)
    - Throwaway user pattern for TPERM-04 — create, test, cleanup within single test
    - DEVIATION comment inline at assertion for live API behavior differences

key-files:
  created:
    - tests/api/test_permissions.py
  modified: []

key-decisions:
  - "TPERM-01 assertion changed: live API message is 'Only managers and owners can perform this action.' (not 'permission') — assertion broadened to match either pattern"
  - "TPERM-05 asserts 404 (not 403) — Django queryset-level filtering hides org from non-members entirely"
  - "Module-scoped role fixtures (not session-scoped) to isolate permission tests from other Phase 4 plans"

patterns-established:
  - "Role-scoped client fixtures: create user + invite to org in fixture, yield client, close in finally"
  - "Throwaway user pattern: create user inline in test, use for target, OWNER cleans up — no fixture needed"

requirements-completed:
  - TPERM-01
  - TPERM-02
  - TPERM-03
  - TPERM-04
  - TPERM-05

# Metrics
duration: 7min
completed: 2026-03-28
---

# Phase 4 Plan 01: Permission Boundary Tests Summary

**Five pytest tests confirming VOLUNTEER, MANAGER, and non-member role restrictions via live Railway API — all 5 pass with documented deviations for real API message wording and queryset-level 404 behavior**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-03-28T23:42:14Z
- **Completed:** 2026-03-28T23:49:18Z
- **Tasks:** 1 of 1
- **Files modified:** 1

## Accomplishments

- TPERM-01: VOLUNTEER is blocked from creating events with 403 (role message verified)
- TPERM-02: VOLUNTEER is blocked from inviting members with 403 (permission message verified)
- TPERM-03: MANAGER is blocked from assigning OWNER role with 403 (exact message verified)
- TPERM-04: MANAGER is blocked from removing members with 403; OWNER cleans up throwaway member
- TPERM-05: Non-org-member gets 404 on org resources (queryset-level hiding, not 403)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create permission boundary tests with role-scoped clients** - `fa4e2ae` (feat)

## Files Created/Modified

- `/Users/user/Test event planning website/tests/api/test_permissions.py` - Five permission boundary tests with module-scoped role fixtures

## Decisions Made

- TPERM-01 assertion broadened: live API says "Only managers and owners can perform this action." — not "permission" — assertion checks for "managers and owners" or "permission" to be future-proof
- TPERM-05 asserts 404: Django queryset-level filtering means non-members get "No Organization matches the given query." (404) instead of 403 — matches research finding
- Module-scoped fixtures chosen over session-scoped to keep permission test setup independent from Phase 4's other test files

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] TPERM-01 assertion fixed to match live API message**
- **Found during:** Task 1 (running tests against live API)
- **Issue:** Plan specified `assert "permission" in r.json().get("detail", "").lower()` but live API returns "Only managers and owners can perform this action." — no "permission" substring present
- **Fix:** Changed assertion to `assert "managers and owners" in detail.lower() or "permission" in detail.lower()` to match the actual live API response while remaining future-proof
- **Files modified:** tests/api/test_permissions.py
- **Verification:** All 5 tests pass (re-run confirmed)
- **Committed in:** fa4e2ae (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Auto-fix necessary for correctness. The plan's assertion was based on an incorrect assumption about the live API message. No scope creep.

## Issues Encountered

None beyond the TPERM-01 message mismatch, which was auto-fixed per Rule 1.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Permission boundary tests complete (TPERM-01 to TPERM-05 all passing)
- Module-scoped `volunteer_client`, `manager_client`, and `non_member_client` fixtures available for reuse if needed
- Phase 4 Plan 02 can proceed: guest list and email settings tests

---
*Phase: 04-permissions-analytics-browser-ui*
*Completed: 2026-03-28*
