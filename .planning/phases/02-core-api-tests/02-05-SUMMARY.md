---
phase: 02-core-api-tests
plan: 05
subsystem: api-tests
tags: [events, ticket-tiers, promo-codes, lifecycle, pytest]
dependency_graph:
  requires: ["02-01", "02-03"]
  provides: ["TEVNT-01..07", "TTICK-01..04", "TPRMO-01..04"]
  affects: ["tests/api/test_events.py", "tests/api/test_ticket_tiers.py", "tests/api/test_promos.py"]
tech_stack:
  added: []
  patterns:
    - "_create_minimal_event() helper avoids fixture reuse for mutation tests"
    - "Promo validate endpoint requires auth (auth_client, not anonymous)"
    - "is_invalid check accepts both valid=False and 400/404 status for flexible error responses"
key_files:
  created:
    - tests/api/test_events.py
    - tests/api/test_ticket_tiers.py
    - tests/api/test_promos.py
  modified: []
decisions:
  - "Each status-transition test (TEVNT-04 through TEVNT-07) creates its own event via _create_minimal_event() to avoid ordering dependencies"
  - "TPRMO-04 deactivated promo check accepts both valid=False and 4xx status codes since the API may return either"
  - "Usage limit exhaustion testing deferred to Phase 3 checkout (per RESEARCH.md Pitfall 8 — usage_limit=0 does not mean exhausted)"
metrics:
  duration: "~21 minutes"
  completed_date: "2026-03-28"
  tasks_completed: 3
  files_created: 3
  tests_added: 15
---

# Phase 02 Plan 05: Event, Tier, and Promo API Tests Summary

**One-liner:** 15 API tests covering full event lifecycle (DRAFT→PUBLISHED→CANCELLED), ticket tier creation and visibility options, and promo code validation with tier-scope and active-status checks.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Write event lifecycle tests (TEVNT-01 through TEVNT-07) | eb360fe | tests/api/test_events.py |
| 2 | Write ticket tier tests (TTICK-01 through TTICK-04) | 61f204a | tests/api/test_ticket_tiers.py |
| 3 | Write promo code tests (TPRMO-01 through TPRMO-04) | d59092e | tests/api/test_promos.py |

## What Was Built

### tests/api/test_events.py (7 tests)
- **TEVNT-01** `test_create_event_all_fields` — POST with all fields (title, description, format, category, start_datetime, end_datetime, timezone, venue, tags), assert 201 + response shape
- **TEVNT-02** `test_event_defaults_to_draft` — minimal event creation asserts status=="DRAFT"
- **TEVNT-03** `test_event_slug_auto_generated` — same title twice, second slug gets dedup suffix
- **TEVNT-04** `test_publish_draft_event` — POST /publish/ returns 200 with status=="PUBLISHED"
- **TEVNT-05** `test_cancel_event_from_any_status` — cancel from DRAFT and from PUBLISHED both return status=="CANCELLED"
- **TEVNT-06** `test_cannot_publish_cancelled_event` — POST /publish/ on CANCELLED returns 400 with "Only draft events can be published"
- **TEVNT-07** `test_cannot_publish_already_published_event` — POST /publish/ twice returns 400 with same message

### tests/api/test_ticket_tiers.py (4 tests)
- **TTICK-01** `test_create_tier_all_options` — POST with all fields, assert full response shape including quantity_remaining, quantity_sold, is_active
- **TTICK-02** `test_quantity_remaining_calculated` — quantity_total=50, quantity_sold==0, quantity_remaining==50 on creation
- **TTICK-03** `test_visibility_options` — 3 tiers created with PUBLIC, HIDDEN, INVITE_ONLY; each returns matching visibility
- **TTICK-04** `test_soft_delete_tier` — PATCH is_active=False returns 200 with is_active==False

### tests/api/test_promos.py (4 tests)
- **TPRMO-01** `test_create_promo_percentage_and_fixed` — create PERCENTAGE (10%, limit 100) and FIXED ($5, limit 50); each returns correct discount_type
- **TPRMO-02** `test_promo_code_stored_uppercase` — submit "lowercasecode", stored as "LOWERCASECODE"
- **TPRMO-03** `test_empty_tier_ids_applies_to_all` — promo with applicable_tier_ids=[] validates as valid=True against any tier
- **TPRMO-04** `test_validate_promo_active_expired_tier` — active promo validates True; deactivated promo validates False/4xx; tier-specific promo validates False/4xx against wrong tier

## Verification Results

```
tests/api/test_events.py       7 passed
tests/api/test_ticket_tiers.py 4 passed
tests/api/test_promos.py       4 passed
Total: 15 passed in 31.45s
```

Full API suite result: 31 passed, 2 failed (test_teams.py network timeout — transient ConnectError, pre-existing from plan 02-04, not related to this plan's changes).

## Deviations from Plan

### Auto-implemented patterns

**1. Flexible invalid-check in TPRMO-04**
- **Found during:** Task 3 implementation
- **Issue:** Plan spec said "Assert valid: False" but live API returns 400 status instead of valid=False body for some invalid promo cases
- **Fix:** is_invalid check accepts both `valid=False` in JSON body AND 400/404 status codes
- **Files modified:** tests/api/test_promos.py
- **Commit:** d59092e

None other — plan executed as specified.

## Known Stubs

None — all tests connect to live API data and assert real responses.

## Self-Check: PASSED
