---
phase: 04-permissions-analytics-browser-ui
plan: 05
subsystem: testing
tags: [playwright, browser-automation, checkout, check-in, ui-tests]

# Dependency graph
requires:
  - phase: 04-04
    provides: "tests/ui/conftest.py with base_url/api_url fixtures and tests/ui/test_frontend.py with 7 browser tests"
provides:
  - "login_via_ui() browser-based auth helper in tests/ui/conftest.py"
  - "ui_test_user, ui_auth_client, ui_checkout_data module-scoped fixtures"
  - "4 new browser tests: TFEND-04 (checkout steps), TFEND-05 (billing prefill), TFEND-06 (confirmation), TFEND-10 (check-in)"
  - "Full authenticated checkout UI flow automation via Playwright"
affects:
  - "05-full-e2e" (if any phase adding end-to-end orchestration)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "login_via_ui() helper: browser-based auth using input[type='email'] and input[type='password'] locators + button[type='submit']"
    - "Checkout UI flow: + button → Review Order → Continue → Complete Registration → confirmation"
    - "Module-scoped fixtures for UI tests: create user+org+event per module run, not per session"
    - "exact=True on get_by_text() to avoid strict mode violations when text appears in multiple elements"
    - "Step 1 must be traversed before details form is accessible — direct /details URL redirects to step 1"

key-files:
  created: []
  modified:
    - tests/ui/conftest.py
    - tests/ui/test_frontend.py

key-decisions:
  - "Checkout step labels differ from RESEARCH.md: live site uses '1. Select Tickets' and '4. Confirmation' (not '1. Select' and '4. Confirm') — tests updated to match live site"
  - "Confirmation page requires full browser checkout flow (React context state) — direct URL navigation shows 'No checkout data found.' — test completes full UI flow via Playwright"
  - "TFEND-04 requires login — the checkout page shows 'Could not load event.' for unauthenticated users but renders correctly for logged-in users"
  - "get_by_text('Checked In', exact=True) required — 'Checked In' also appears in '0% checked in' text, causing strict mode violation without exact=True"
  - "UI tests use module-scoped fixtures (not session-scoped) to isolate UI test user/org/event from API test suite resources"

patterns-established:
  - "UI checkout flow pattern: login_via_ui() → goto checkout → click + → Review Order → Continue → Complete Registration"
  - "Module-scoped UI data fixtures: create fresh user + org + event per test module run for isolation"

requirements-completed: [TFEND-04, TFEND-05, TFEND-06, TFEND-10]

# Metrics
duration: 13min
completed: 2026-03-28
---

# Phase 04 Plan 05: Authenticated Browser UI Tests Summary

**Playwright browser tests for checkout step indicators, billing pre-fill, order confirmation, and check-in page — all 4 new tests passing (11 total)**

## Performance

- **Duration:** 13 min
- **Started:** 2026-03-28T23:50:56Z
- **Completed:** 2026-03-28T24:04:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `login_via_ui()` browser-based auth helper and 4 module-scoped fixtures (`ui_test_user`, `ui_auth_client`, `ui_checkout_data`) to `tests/ui/conftest.py`
- TFEND-04: Verifies checkout has 4 step indicators (1. Select Tickets, 2. Your Details, 3. Payment, 4. Confirmation)
- TFEND-05: Verifies billing form pre-fills `billing_name` and `billing_email` for logged-in users after navigating through step 1
- TFEND-06: Completes full browser checkout flow and verifies "You're registered!", "Confirmation Code", and "Your Tickets" appear on confirmation page
- TFEND-10: Verifies check-in page has QR Code Scanner, Start Scanner, Search & Manual Check-In, and Checked In/Registered stats (with ?org= query param)
- All 11 UI tests pass (7 from Plan 04 + 4 from this plan)

## Task Commits

1. **Task 1: Add auth helper and checkout data fixtures to UI conftest** - `3aabbd8` (feat)
2. **Task 2: Add checkout, confirmation, and check-in browser tests** - `1f3a3bb` (feat)

**Plan metadata:** (docs commit to follow)

## Files Created/Modified

- `tests/ui/conftest.py` - Added login_via_ui() helper, ui_test_user, ui_auth_client, ui_checkout_data fixtures
- `tests/ui/test_frontend.py` - Added 4 browser tests: TFEND-04, TFEND-05, TFEND-06, TFEND-10

## Decisions Made

- Step labels verified empirically against live site: "1. Select Tickets" and "4. Confirmation" (RESEARCH.md had "1. Select" and "4. Confirm")
- Confirmation page requires full browser checkout flow; API-side checkout does not populate React context state needed by the confirmation page
- Login required for checkout page; unauthenticated navigation shows "Could not load event." error
- Used `exact=True` on "Checked In" get_by_text to prevent strict mode violation (text also appears in "0% checked in" stat)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected checkout step indicator label text to match live site**
- **Found during:** Task 2 (test_checkout_step_indicator initial run)
- **Issue:** RESEARCH.md stated labels as "1. Select" and "4. Confirm" — live site uses "1. Select Tickets" and "4. Confirmation"
- **Fix:** Updated assertions in test_checkout_step_indicator to use live site label text
- **Files modified:** tests/ui/test_frontend.py
- **Verification:** TFEND-04 passes against live Vercel site
- **Committed in:** 1f3a3bb (Task 2 commit)

**2. [Rule 1 - Bug] TFEND-04 requires login — checkout page shows error for unauthenticated users**
- **Found during:** Task 2 (test_checkout_step_indicator failure — "element not found")**
- **Issue:** Without auth, checkout page renders "Could not load event." — step indicators invisible
- **Fix:** Added login_via_ui() call before navigating to checkout in TFEND-04
- **Files modified:** tests/ui/test_frontend.py
- **Verification:** TFEND-04 passes after adding login
- **Committed in:** 1f3a3bb (Task 2 commit)

**3. [Rule 1 - Bug] TFEND-05 billing prefill requires navigating through step 1 first**
- **Found during:** Task 2 (test_checkout_billing_prefill — timeout on label locator)
- **Issue:** Direct navigation to /checkout/{slug}/details redirects back to step 1 (select tickets); form inputs not accessible until ticket selected and "Continue" clicked
- **Fix:** Test now navigates step 1 (+ button → Review Order → Continue) before checking billing inputs
- **Files modified:** tests/ui/test_frontend.py
- **Verification:** TFEND-05 passes — billing_name="UI Tester", billing_email pre-filled correctly
- **Committed in:** 1f3a3bb (Task 2 commit)

**4. [Rule 1 - Bug] TFEND-06 confirmation page requires full browser flow, not API checkout**
- **Found during:** Task 2 (test_confirmation_page — checkout API returned 400 billing fields required)
- **Issue:** API checkout required billing_name/billing_email; even with those fields, direct URL navigation to /confirmation shows "No checkout data found." (React context not populated)
- **Fix:** Test performs full browser UI checkout: login → select ticket → Review Order → Continue → Complete Registration → verify confirmation
- **Files modified:** tests/ui/test_frontend.py
- **Verification:** TFEND-06 passes — "You're registered!", "Confirmation Code", "Your Tickets" all visible
- **Committed in:** 1f3a3bb (Task 2 commit)

**5. [Rule 1 - Bug] TFEND-10 strict mode violation on "Checked In" text**
- **Found during:** Task 2 (test_checkin_page_elements — strict mode violation)
- **Issue:** get_by_text("Checked In") matched 2 elements: "Checked In" stat label and "0% checked in" progress text
- **Fix:** Used get_by_text("Checked In", exact=True) to target only the exact label
- **Files modified:** tests/ui/test_frontend.py
- **Verification:** TFEND-10 passes with no strict mode violation
- **Committed in:** 1f3a3bb (Task 2 commit)

---

**Total deviations:** 5 auto-fixed (all Rule 1 - Bug, empirical live site behavior differing from RESEARCH.md)
**Impact on plan:** All auto-fixes required for tests to pass against live site. No scope creep.

## Issues Encountered

- test_homepage_hero_and_ctas experienced a transient Vercel cold-start timeout (60s exceeded) on one run but passed on retry — pre-existing flakiness not related to this plan's changes.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 11 UI browser tests pass against the live GatherGood Vercel deployment
- Phase 04 is now fully complete with all 5 plans executed
- Authenticated checkout and check-in flows verified with real data via Playwright
- The test suite is ready for Phase 05 if planned

---
*Phase: 04-permissions-analytics-browser-ui*
*Completed: 2026-03-28*

## Self-Check: PASSED

- tests/ui/conftest.py: FOUND
- tests/ui/test_frontend.py: FOUND
- .planning/phases/04-permissions-analytics-browser-ui/04-05-SUMMARY.md: FOUND
- commit 3aabbd8 (Task 1): FOUND
- commit 1f3a3bb (Task 2): FOUND
