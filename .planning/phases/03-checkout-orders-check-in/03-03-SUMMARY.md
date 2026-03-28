---
phase: 03-checkout-orders-check-in
plan: 03
subsystem: checkin-api-tests
tags: [check-in, qr-scan, manual-check-in, stats, search, api-tests, pytest, httpx, live-api]
dependency_graph:
  requires: [tests/api/conftest.py checkout_event fixture, factories/common.py, helpers/api.py]
  provides: [tests/api/test_checkin.py with 11 check-in tests]
  affects: [teardown_registry (informational; orders not deleteable)]
tech_stack:
  added: []
  patterns: [module-scoped fixture ordering for sequential scan tests, skip marker for backend limitation, HMAC forgery test pattern]
key_files:
  created:
    - tests/api/test_checkin.py
  modified: []
decisions:
  - TCHKN-05 skipped with explicit reason — no ticket cancel API on backend, event cancellation does not invalidate tickets (empirically verified in RESEARCH.md)
  - TMCHK-02 re-checks an already-checked-in ticket to verify the already_checked_in response shape from the manual endpoint (shares status/message keys with QR scan)
  - TCHKN-01 and TCHKN-02 intentionally scan different tickets (tickets[0] and tickets[1]) to ensure TCHKN-03 re-scan gets already_checked_in on ticket[1] without test ordering dependency issues
metrics:
  duration: 15 minutes
  completed_date: "2026-03-28T23:15:00Z"
  tasks_completed: 2
  files_changed: 1
---

# Phase 03 Plan 03: Check-In API Tests (TCHKN-01 through TSRCH-01) Summary

**One-liner:** 11 check-in tests covering QR scan, HMAC forgery, manual check-in, stats, and attendee search — 10 pass, 1 skipped (TCHKN-05, no ticket cancel API).

## What Was Built

Created `tests/api/test_checkin.py` with 11 tests covering the full check-in lifecycle.

Two module-scoped fixtures support the tests:
- **checkin_order**: Completes a free order with 2 tickets (billing_name="ScanTest Attendee") for QR scan tests. tickets[0] is scanned by TCHKN-01; tickets[1] is scanned by TCHKN-02 and re-scanned by TCHKN-03.
- **manual_checkin_order**: Completes a separate free order with 1 ticket (billing_name="ManualTest User") for manual check-in tests.

The `checkin_base_url` fixture provides `/organizations/{slug}/events/{slug}/check-in` as a shared prefix.

### Tests Written (tests/api/test_checkin.py)

| Test | Requirement | Result | Notes |
|------|-------------|--------|-------|
| test_scan_qr_success | TCHKN-01 | PASSED | ticket[0] QR returns status=success |
| test_scan_success_response_shape | TCHKN-02 | PASSED | ticket[1] scan; verifies attendee_name, attendee_email, tier_name, checked_in_at, message |
| test_rescan_returns_already_checked_in | TCHKN-03 | PASSED | ticket[1] re-scan returns already_checked_in with original checked_in_at |
| test_scan_invalid_qr_returns_invalid | TCHKN-04 | PASSED | "not-a-valid-qr-string" returns status=invalid |
| test_cancelled_ticket_scan_returns_invalid | TCHKN-05 | SKIPPED | No ticket cancel API on backend |
| test_hmac_verification_on_scan | TCHKN-06 | PASSED | Forged HMAC (aaaaaaaaaaaaaaaa) returns status=invalid with "Signature verification failed" |
| test_manual_checkin_by_ticket_id | TMCHK-01 | PASSED | POST /check-in/{id}/manual/ returns status=success, message, attendee_name |
| test_manual_checkin_response_format | TMCHK-02 | PASSED | Re-check returns already_checked_in; verifies status and message keys shared with QR scan |
| test_checkin_stats_fields | TSTAT-01 | PASSED | total_registered, checked_in, not_checked_in, percentage, by_tier all present; total == checked_in + not_checked_in |
| test_checkin_stats_by_tier_breakdown | TSTAT-02 | PASSED | by_tier is list of {tier_name, total, checked_in} objects |
| test_search_attendees | TSRCH-01 | PASSED | Search by name "ScanTest" and confirmation_code both return >= 1 result; shape verified |

### Live API Run Result

```
10 passed, 1 skipped in 12.90s
```

## Deviations from Plan

None — plan executed exactly as written. All API contracts matched the RESEARCH.md specifications. The module-scoped fixture ordering (tickets[0] for TCHKN-01, tickets[1] for TCHKN-02 and TCHKN-03) worked deterministically as documented in the plan.

## Known Stubs

None — all tests make real API calls against the live backend and assert real response data.

## Self-Check: PASSED

- FOUND: tests/api/test_checkin.py (391 lines, 11 test functions, >= 150 line minimum met)
- FOUND: commit 5be82cb (Task 1+2: all 11 tests in single file)
- FOUND: TCHKN-01 through TCHKN-06 in source
- FOUND: TMCHK-01, TMCHK-02, TSTAT-01, TSTAT-02, TSRCH-01 in source
- FOUND: pytest.mark.skip for TCHKN-05
- FOUND: aaaaaaaaaaaaaaaa (forged HMAC in TCHKN-06)
- Live API verification: 10 PASSED, 1 SKIPPED (TCHKN-05 backend limitation)
