---
phase: 03-checkout-orders-check-in
plan: 02
subsystem: orders-tickets-api-tests
tags: [orders, tickets, qr-code, api-tests, pytest, httpx, live-api]
dependency_graph:
  requires: [tests/api/conftest.py checkout_event fixture, factories/common.py, helpers/api.py, settings.py]
  provides: [tests/api/test_orders.py]
  affects: [teardown_registry (order_ids informational only — no DELETE endpoint)]
tech_stack:
  added: []
  patterns: [module-scoped completed_order fixture, unauthenticated plain httpx.Client, regex format validation]
key_files:
  created:
    - tests/api/test_orders.py
  modified: []
decisions:
  - completed_order fixture is module-scoped (not session-scoped) to isolate order creation from checkout tests while sharing the checkout_event
  - Unauthenticated lookup test uses a plain httpx.Client with no Bearer token — not the auth_client wrapper
  - QR format tested twice: TORDR-06 validates via regex groups, TORDR-07 validates via split(':') structural check (4 parts, UUID format for first 3)
metrics:
  duration: 2 minutes
  completed_date: "2026-03-28T22:59:41Z"
  tasks_completed: 1
  files_changed: 1
---

# Phase 03 Plan 02: Order and Ticket API Tests (TORDR-01 through TORDR-07) Summary

**One-liner:** 7 order and ticket tests using module-scoped completed_order fixture — all 7 pass against live API; confirmation code validated as [A-Z0-9]{10}, QR validated as UUID:UUID:UUID:16hex, unauthenticated lookup verified.

## What Was Built

Created `tests/api/test_orders.py` with a module-scoped `completed_order` fixture and all 7 order/ticket tests.

The `completed_order` fixture completes a free order via `POST /checkout/` (action=complete) once per module, returning the full order dict including `confirmation_code` and `tickets[].qr_code_data`. This is reused by all 7 tests to avoid redundant network calls.

### Fixture Added (tests/api/test_orders.py)

- **completed_order** (module-scoped): Posts to `/checkout/` with `action=complete`, free tier, unique billing email. Returns 201 order dict.

### Tests Written (tests/api/test_orders.py)

| Test | Requirement | Result | Notes |
|------|-------------|--------|-------|
| test_list_own_orders | TORDR-01 | PASSED | GET /orders/ returns list; confirms completed_order id present |
| test_view_order_detail | TORDR-02 | PASSED | GET /orders/{id}/ returns full detail with confirmation_code, tickets, line_items |
| test_lookup_by_confirmation_code_no_auth | TORDR-03 | PASSED | Unauthenticated plain httpx.Client; 200 on valid code; 404 on ZZZZZZZZZZ |
| test_confirmation_code_format | TORDR-04 | PASSED | Regex ^[A-Z0-9]{10}$ — uppercase only, exactly 10 chars |
| test_list_own_tickets | TORDR-05 | PASSED | GET /tickets/ returns list; confirms ticket id present; qr_code_data non-empty |
| test_qr_code_data_format | TORDR-06 | PASSED | Full regex match: UUID:UUID:UUID:hex16 with group extraction |
| test_qr_hmac_structure | TORDR-07 | PASSED | split(':') gives 4 parts; first 3 are UUIDs; last is [0-9a-f]{16} |

## Deviations from Plan

None — plan executed exactly as written. All 7 tests passed on first run against the live API.

## Known Stubs

None — all tests make real API calls and assert real response data.

## Self-Check: PASSED

- FOUND: tests/api/test_orders.py (165 lines, 7 tests)
- FOUND: commit 168ccf4 (feat(03-02): add 7 order and ticket tests)
- Live API verification: 7 PASSED, 0 SKIPPED, 0 FAILED (9.42s)
