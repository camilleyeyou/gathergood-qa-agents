---
phase: 04-permissions-analytics-browser-ui
plan: "02"
subsystem: api-tests
tags: [guest-list, email-settings, analytics, api-tests]
dependency_graph:
  requires:
    - tests/api/conftest.py (org, event, checkout_event fixtures)
    - conftest.py (auth_client, teardown_registry)
    - helpers/api.py (assert_status)
    - factories/common.py (unique_email, event_title, tier_name)
  provides:
    - tests/api/test_guest_email.py (6 tests: TGUST-01/02, TEMAL-01-04)
    - tests/api/test_analytics.py (3 tests: TANLT-01-03)
  affects: []
tech_stack:
  added: []
  patterns:
    - Module-scoped fixture with inline checkout to create attendees for email tests
    - PATCH event endpoint used for email_config (no dedicated endpoint exists)
key_files:
  created:
    - tests/api/test_guest_email.py
    - tests/api/test_analytics.py
  modified: []
decisions:
  - "checkout_action_complete_uses_201: completed free checkout returns 201 not 200"
  - "checkout_api_shape: POST /checkout/ requires org_slug+event_slug+items fields, not tickets"
  - "email_config_via_patch: no dedicated email-config endpoint, config is nested in event PATCH"
  - "analytics_timeline_key: key is 'timeline' not 'registrations_over_time' per TEST_SPEC"
metrics:
  duration: "14 minutes"
  completed: "2026-03-28"
  tasks_completed: 2
  files_created: 2
---

# Phase 4 Plan 2: Guest List, Email Settings, and Analytics Tests Summary

**One-liner:** 9 pytest API tests covering guest list JSON+CSV export, email config read/write via event PATCH, bulk email with module-scoped attendee fixture, email log, and analytics field/tier/timeline assertions against live GatherGood backend.

## What Was Built

### Task 1: Guest List and Email Settings Tests (tests/api/test_guest_email.py)

6 tests covering guest list and email management features:

| Test | Req ID | What It Verifies |
|------|--------|-----------------|
| `test_guest_list_view` | TGUST-01 | GET /guests/ returns JSON array with >= 1 attendee |
| `test_guest_list_csv` | TGUST-02 | GET /guests/csv/ returns 200 with Name/Email/Ticket Tier/Confirmation Code/Checked In headers |
| `test_view_email_config` | TEMAL-01 | GET event response includes email_config field |
| `test_update_email_config` | TEMAL-02 | PATCH event with email_config toggles persists send_confirmation/send_reminder/send_notification |
| `test_bulk_email_send` | TEMAL-03 | POST /emails/bulk/ accepts subject+body when attendees exist (200 or 201) |
| `test_email_log` | TEMAL-04 | GET /emails/log/ returns a list |

A module-scoped `email_test_event` fixture creates its own published event + free tier + completed free checkout to ensure attendees exist for TGUST-01/02, TEMAL-03/04. The TEMAL-01/02 tests use the session-scoped `event` fixture (DRAFT event is sufficient for reading/writing email config).

### Task 2: Analytics Endpoint Tests (tests/api/test_analytics.py)

3 tests covering the event analytics endpoint:

| Test | Req ID | What It Verifies |
|------|--------|-----------------|
| `test_analytics_fields` | TANLT-01 | All top-level keys (registrations, attendance, revenue, refunds, timeline) and nested keys present |
| `test_analytics_by_tier` | TANLT-02 | registrations.by_tier is a list |
| `test_analytics_timeline` | TANLT-03 | timeline key exists and is a list (DEVIATION: not registrations_over_time) |

Both test files use the `checkout_event` session fixture (published event with orders from prior test run state) for analytics data.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed checkout API request shape in email_test_event fixture**
- **Found during:** Task 1 verification run
- **Issue:** Plan specified checkout payload as `{"action": "complete", "event_slug": ..., "tickets": [...], ...}` but live API returns 400 with `{"org_slug":["This field is required."],"items":["This field is required."]}`. The correct shape requires `org_slug`, `event_slug`, and `items` (not `tickets`), consistent with how test_checkout.py calls the same endpoint.
- **Fix:** Updated fixture to use `org_slug`, `items` fields, and assert 201 (not 200) for completed orders.
- **Files modified:** tests/api/test_guest_email.py
- **Commit:** 5f6fa5d

### Pre-existing Deviations (from RESEARCH.md, implemented as designed)

**TEMAL-01/02 — No dedicated email-config endpoint**
Email configuration is embedded in the event model. Reading email_config means checking `event.email_config` from `GET /organizations/{org}/events/{event}/`. Updating it means `PATCH`ing the event with `{"email_config": {...}}`. Tests reflect this correctly.

**TANLT-03 — timeline key (not registrations_over_time)**
TEST_SPEC.md refers to "registrations_over_time" but the live API uses `"timeline"`. Both tests and inline comments document this deviation explicitly.

## Known Stubs

None. All tests make live API calls and assert real response data.

## Self-Check: PASSED

- tests/api/test_guest_email.py: FOUND
- tests/api/test_analytics.py: FOUND
- Commit 5f6fa5d (task 1): FOUND
- Commit d4762ff (task 2): FOUND
- All 9 tests: PASSED (confirmed by final combined run)
