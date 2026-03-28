---
phase: 04-permissions-analytics-browser-ui
plan: "03"
subsystem: public-pages-api-tests
tags: [api-tests, public-endpoints, ticket-tiers, visibility, unauthenticated]
dependency_graph:
  requires: [tests/api/conftest.py, conftest.py, factories/common.py, helpers/api.py, settings.py]
  provides: [tests/api/test_public.py]
  affects: []
tech_stack:
  added: []
  patterns: [module-scoped-fixture, unauthenticated-httpx, tier-visibility-verification-by-name-prefix]
key_files:
  created:
    - tests/api/test_public.py
  modified: []
key_decisions:
  - "TPUBL-01: ?format= filter returns 404 on live API — test documents this as unsupported and skips format filter"
  - "TPUBL-04/05: ticket_tiers response strips the visibility field — tier filtering verified by name prefix (Public-/Hidden-/Invite-)"
  - "visibility_event fixture is module-scoped (not session-scoped) to isolate tier creation from other test modules"
metrics:
  duration: "~13 minutes"
  completed_date: "2026-03-28"
  tasks_completed: 1
  files_created: 1
requirements:
  - TPUBL-01
  - TPUBL-02
  - TPUBL-03
  - TPUBL-04
  - TPUBL-05
---

# Phase 04 Plan 03: Public Pages API Tests Summary

**One-liner:** Unauthenticated public browse/detail tests verifying PUBLISHED-only events and PUBLIC-only ticket tier visibility using name-prefix strategy.

## What Was Built

`tests/api/test_public.py` with 5 tests covering the three public-facing API endpoints. All requests use raw `httpx.get()` (no auth header) against the live Railway backend.

### Tests Created

| Test | Req ID | What it verifies |
|------|--------|-----------------|
| `test_public_browse_events` | TPUBL-01 | `/public/events/` returns 200 list; `?category=MEETUP` and `?q=test` filters return 200 list |
| `test_public_browse_excludes_draft` | TPUBL-02 | No DRAFT or CANCELLED events appear in public browse |
| `test_public_org_page` | TPUBL-03 | `/public/{slug}/` returns `{organization, events}` with matching slug |
| `test_public_event_detail_public_tiers_only` | TPUBL-04 | Public event detail includes a PUBLIC tier; excludes HIDDEN/INVITE_ONLY |
| `test_public_event_hides_non_public_tiers` | TPUBL-05 | Exactly 1 tier (the PUBLIC one) appears; HIDDEN and INVITE_ONLY are absent |

### Key Fixture: `visibility_event` (module-scoped)

Creates an event with three ticket tiers (one PUBLIC, one HIDDEN, one INVITE_ONLY), publishes it, and returns all four objects. Tiers use prefixed names (`Public-...`, `Hidden-...`, `Invite-...`) as a verification handle since the public response strips the `visibility` field.

## Test Results

All 5 tests passed on first run against the live API in 12.41 seconds.

```
tests/api/test_public.py::test_public_browse_events PASSED
tests/api/test_public.py::test_public_browse_excludes_draft PASSED
tests/api/test_public.py::test_public_org_page PASSED
tests/api/test_public.py::test_public_event_detail_public_tiers_only PASSED
tests/api/test_public.py::test_public_event_hides_non_public_tiers PASSED
5 passed in 12.41s
```

## Deviations from Plan

### Known API Behaviors Documented

**1. [Research-confirmed] `?format=` filter returns 404**
- **Found during:** Task 1 (documented in RESEARCH.md)
- **Issue:** `/public/events/?format=IN_PERSON` returns 404, not a filtered list
- **Fix:** Test adds comment `# DEVIATION: ?format= filter returns 404 — not supported by live API. Skipped.` and skips format filter assertion
- **Files modified:** tests/api/test_public.py

**2. [Research-confirmed] `visibility` field stripped from public tier response**
- **Found during:** Task 1 (documented in RESEARCH.md)
- **Issue:** `ticket_tiers` in the public event detail response do NOT include a `visibility` field — it is stripped server-side
- **Fix:** Tier filtering verification uses name prefixes (`Public-`, `Hidden-`, `Invite-`) instead of checking the visibility field directly. Comment explains the strategy.
- **Files modified:** tests/api/test_public.py

None — plan executed as designed. Both deviations were pre-researched and the plan already accounted for them.

## Known Stubs

None. All tests wire real data and make live assertions against the deployed API.

## Self-Check: PASSED

- tests/api/test_public.py: FOUND
- Commit 00d1bdc: FOUND (verified via git log)
