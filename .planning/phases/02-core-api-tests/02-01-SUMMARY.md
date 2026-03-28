---
phase: 02-core-api-tests
plan: "01"
subsystem: test-infrastructure
tags: [fixtures, teardown, factories, conftest, session-scoped]
dependency_graph:
  requires: [01-01-PLAN, 01-02-PLAN]
  provides: [teardown-cleanup, org-fixture, venue-fixture, event-fixture, published-event-fixture, tier-name-factory, promo-code-factory]
  affects: [02-02-PLAN, 02-03-PLAN, 02-04-PLAN, 02-05-PLAN]
tech_stack:
  added: []
  patterns:
    - Session-scoped pytest fixtures for shared resource hierarchy (org → venue → event)
    - Reverse-dependency-order teardown using dict entries with parent slugs
    - Mixed teardown strategy: hard-delete tiers/venues, cancel events, deactivate promos
key_files:
  created:
    - tests/api/conftest.py
  modified:
    - conftest.py
    - factories/common.py
decisions:
  - "Teardown runs inside auth_client fixture after yield (not in teardown_registry), since auth_client depends on teardown_registry and tears down first — so auth_client still has a live HTTP client when cleanup runs"
  - "Registry entries store dicts with parent slugs (not bare IDs) to support nested URL routing"
  - "published_event registers for teardown before calling publish endpoint to ensure cleanup even if publish fails"
metrics:
  duration: ~10min
  completed: "2026-03-28"
  tasks: 2
  files: 3
---

# Phase 2 Plan 1: Teardown Cleanup and Shared Fixtures Summary

Wired teardown cleanup into conftest.py and created shared session-scoped resource fixtures for all Phase 2 API tests, using mixed hard-delete/cancel/deactivate strategy per live API constraints.

## Tasks Completed

### Task 1: Wire teardown cleanup and extend factories

**Files modified:** `conftest.py`, `factories/common.py`

- Added `_cleanup(client, registry)` function to `conftest.py` implementing 4-step reverse-dependency teardown: DELETE ticket tiers → PATCH deactivate promos → POST cancel events → DELETE venues
- Moved `instance.close()` to after `_cleanup()` call in `auth_client` fixture teardown
- Removed placeholder comment "Cleanup logic wired in Phase 2 once domain endpoints are known"
- Registry entry values are now dicts with parent slugs (e.g., `{"org_slug": ..., "event_slug": ..., "tier_id": ...}`)
- Added `tier_name()` factory: `test-{RUN_ID}-tier-{4hex}`
- Added `promo_code()` factory: `TEST{RUN_ID}{4HEX}` (uppercase)

### Task 2: Create shared session-scoped API test fixtures

**Files created:** `tests/api/conftest.py`

- `org(auth_client, teardown_registry)` — POST `/organizations/`, assert 201, register `{"slug": ...}`, return full dict
- `venue(auth_client, org, teardown_registry)` — POST `/organizations/{slug}/venues/`, assert 201, register `{"org_slug": ..., "venue_id": ...}`, return full dict
- `event(auth_client, org, teardown_registry)` — POST `/organizations/{slug}/events/`, assert 201, register `{"org_slug": ..., "event_slug": ...}`, return DRAFT dict
- `published_event(auth_client, org, teardown_registry)` — creates separate event, registers for teardown first, then POSTs to `/publish/`, returns PUBLISHED dict
- All fixtures: `scope="session"`, use `assert_status` for checks, slug-based URL routing throughout (never UUID for org/event lookups)

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None - all fixtures wire real API calls with proper assertion and teardown registration.

## Self-Check

### Created files exist:
- tests/api/conftest.py: CREATED
- .planning/phases/02-core-api-tests/02-01-SUMMARY.md: CREATED

### Modified files verified:
- conftest.py: Contains `_cleanup` function, `ticket_tier_ids`, `promo_code_ids`, `/cancel/`, `venue_id` in teardown
- factories/common.py: Contains `def tier_name()` and `def promo_code()`

## Self-Check: PASSED
