---
phase: 02-core-api-tests
plan: "04"
subsystem: api-tests
tags: [team-management, permissions, multi-user, httpx]
dependency_graph:
  requires: [02-01-PLAN.md]
  provides: [tests/api/test_teams.py]
  affects: []
tech_stack:
  added: []
  patterns:
    - Module-level _create_user_client() helper registers+logins secondary users via httpx
    - try/finally blocks ensure all extra httpx.Client instances are closed
    - Membership ID (from GET /members/ response id field) used for DELETE — not user UUID
key_files:
  created:
    - tests/api/test_teams.py
  modified: []
decisions:
  - "_create_user_client() returns authenticated httpx.Client (not the auth_client wrapper) — secondary users don't need JWT auto-refresh for short-lived permission tests"
  - "TTEAM-02 includes positive control: MANAGER CAN invite as VOLUNTEER (201) in addition to the 403 negative assertion"
  - "TTEAM-04 fetches member list via OWNER client to get membership_id — MANAGER client not used for lookup to avoid any permission ambiguity"
metrics:
  duration: ~5min
  completed: "2026-03-28"
  tasks_completed: 1
  files_created: 1
---

# Phase 02 Plan 04: Team Management API Tests Summary

**One-liner:** 4 team permission tests using multi-user httpx clients — OWNER invite, MANAGER role restriction, VOLUNTEER listing, OWNER-only removal via membership ID.

## What Was Built

`tests/api/test_teams.py` — 4 test functions covering TTEAM-01 through TTEAM-04:

| Test | Requirement | What It Verifies |
|------|-------------|-----------------|
| `test_owner_can_invite_member` | TTEAM-01 | OWNER invites a registered user as VOLUNTEER → 201 |
| `test_manager_cannot_assign_owner_role` | TTEAM-02 | MANAGER → OWNER invite returns 403 with "Managers cannot assign the Owner role"; MANAGER → VOLUNTEER invite returns 201 |
| `test_any_member_can_list_team` | TTEAM-03 | VOLUNTEER can GET /members/ → 200 list with id, email, role fields; at least 2 members returned |
| `test_only_owner_can_remove_member` | TTEAM-04 | MANAGER DELETE → 403 "Only owners can remove members"; OWNER DELETE → 204 using membership_id from GET list |

### Key Implementation Details

**Multi-user approach:** A module-level `_create_user_client()` helper function registers a new user and returns `(email, authenticated_httpx_client)`. Each test that needs additional roles creates users on the fly, uses them, then closes the client in a `finally` block.

**Membership ID vs User ID:** The DELETE endpoint at `/organizations/{slug}/members/{membership_id}/` uses the `id` field from the GET /members/ response — not the user's UUID. TTEAM-04 explicitly fetches the member list and extracts the correct ID by matching email.

**Error message assertions:** Both permission-boundary tests (`TTEAM-02`, `TTEAM-04`) assert on the exact error text returned by the live API: `"Managers cannot assign the Owner role"` and `"Only owners can remove members"`.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. All tests wire directly to live API endpoints with real assertions.

## Self-Check

### Files Created
- `tests/api/test_teams.py` — CREATED

### Markers Verified (by inspection)
- `@pytest.mark.req("TTEAM-01")` — present on `test_owner_can_invite_member`
- `@pytest.mark.req("TTEAM-02")` — present on `test_manager_cannot_assign_owner_role`
- `@pytest.mark.req("TTEAM-03")` — present on `test_any_member_can_list_team`
- `@pytest.mark.req("TTEAM-04")` — present on `test_only_owner_can_remove_member`
- `members/invite/` — present in all invite calls
- `membership_id` variable used for DELETE — present in TTEAM-04
- `"Managers cannot assign the Owner role"` — present in TTEAM-02 assertion
- `"Only owners can remove members"` — present in TTEAM-04 assertion

## Self-Check: PASSED (static; pytest run requires Bash access)

Note: File creation and static inspection checks pass. Live API test execution (`pytest tests/api/test_teams.py -v`) must be run by the user to confirm all 4 tests pass against the deployed backend.
