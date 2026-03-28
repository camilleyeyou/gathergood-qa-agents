---
phase: 02-core-api-tests
verified: 2026-03-28T00:00:00Z
status: passed
score: 33/33 must-haves verified
human_verification:
  - test: "Run the full test suite against the live API"
    expected: "All 33 tests pass with no failures or network errors"
    why_human: "Tests require a live network connection to the deployed backend at event-management-production-ad62.up.railway.app; cannot execute from a static file check"
  - test: "Confirm TAUTH-04 returns the generic 'If an account exists...' message"
    expected: "POST /auth/forgot-password/ returns 200 with a privacy-safe generic message"
    why_human: "Test only verifies len(response_text) > 0, not the exact message content; message wording needs human confirmation against VALIDATION.md note"
---

# Phase 2: Core API Tests Verification Report

**Phase Goal:** All core domain API endpoints are covered by tests that produce clear pass/fail results mapped to TEST_SPEC requirement IDs
**Verified:** 2026-03-28
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Registration, login, token refresh, and password reset all produce pass/fail results against the live backend | VERIFIED | test_auth.py: 5 tests (TAUTH-01 through TAUTH-05) each call real endpoints and assert status codes + response fields |
| 2 | The full org-to-event chain (create org → create team → create venue → create event → publish → cancel) runs end-to-end with no test-order dependencies | VERIFIED | Session fixtures in tests/api/conftest.py create org/venue/event once; each status-transition test creates its own event via _create_minimal_event() helper |
| 3 | Ticket tier visibility options and promo code validation rules each produce an explicit test result | VERIFIED | TTICK-03 tests all 3 visibility values; TPRMO-03 tests empty tier_ids; TPRMO-04 tests active/deactivated/tier-scoped validation |
| 4 | Every test in this phase carries a requirement ID marker and appears by name in the console output | VERIFIED | All 33 tests have @pytest.mark.req markers; pytest.ini configures req marker; pytest collects all 33 tests with their function names |

**Score:** 4/4 success criteria satisfied

---

## Required Artifacts

| Artifact | Plan | Expected | Status | Details |
|----------|------|----------|--------|---------|
| `conftest.py` | 02-01 | Teardown cleanup wired (not placeholder comment) | VERIFIED | _cleanup() function implements 4-step reverse-dependency teardown; placeholder comment absent |
| `factories/common.py` | 02-01 | tier_name() and promo_code() factory functions | VERIFIED | Both functions present and importable; tier_name() returns test-{run}-tier-{4hex}, promo_code() returns TEST{RUN}{4HEX} |
| `tests/api/conftest.py` | 02-01 | 4 session-scoped fixtures: org, venue, event, published_event | VERIFIED | All 4 fixtures present, scope="session", all use assert_status, all register in teardown_registry with parent slug context |
| `tests/api/test_auth.py` | 02-02 | 5 tests, TAUTH-01 through TAUTH-05, @pytest.mark.req markers | VERIFIED | Exactly 5 test functions; all 5 markers present; password_confirm used; no assertion on old token rejection |
| `tests/api/test_profile.py` | 02-02 | 2 tests, TPROF-01 and TPROF-02, @pytest.mark.req markers | VERIFIED | Exactly 2 test functions; both markers present; TPROF-02 restores original profile values after PATCH |
| `tests/api/test_organizations.py` | 02-03 | 4 tests, TORG-01 through TORG-04, @pytest.mark.req markers | VERIFIED | Exactly 4 test functions; all 4 markers present; all URLs use slugs (not UUIDs) |
| `tests/api/test_venues.py` | 02-03 | 3 tests, TVENU-01 through TVENU-03, @pytest.mark.req markers | VERIFIED | Exactly 3 test functions; all 3 markers present; org slug used for org part, venue UUID for venue detail |
| `tests/api/test_teams.py` | 02-04 | 4 tests, TTEAM-01 through TTEAM-04, @pytest.mark.req markers | VERIFIED | Exactly 4 test functions; all 4 markers present; _create_user_client() helper; membership_id used for DELETE (not user UUID) |
| `tests/api/test_events.py` | 02-05 | 7 tests, TEVNT-01 through TEVNT-07, @pytest.mark.req markers | VERIFIED | Exactly 7 test functions; all 7 markers present; start_datetime field used (not start_date); venue UUID passed as "venue" field |
| `tests/api/test_ticket_tiers.py` | 02-05 | 4 tests, TTICK-01 through TTICK-04, @pytest.mark.req markers | VERIFIED | Exactly 4 test functions; all 4 markers present; quantity_remaining, HIDDEN, INVITE_ONLY all tested |
| `tests/api/test_promos.py` | 02-05 | 4 tests, TPRMO-01 through TPRMO-04, @pytest.mark.req markers | VERIFIED | Exactly 4 test functions; all 4 markers present; validate endpoint called via auth_client; is_invalid check accepts both valid=False and 4xx |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tests/api/conftest.py` | `conftest.py` | auth_client and teardown_registry injection | VERIFIED | def org(auth_client, teardown_registry) — both fixtures injected from root conftest |
| `conftest.py` | API endpoints | teardown HTTP calls in reverse dependency order | VERIFIED | _cleanup() calls /ticket-tiers/{id}/ DELETE, /promo-codes/{id}/ PATCH, /events/{slug}/cancel/ POST, /venues/{id}/ DELETE |
| `tests/api/test_auth.py` | `/auth/register/`, `/auth/login/`, `/auth/token/refresh/`, `/auth/forgot-password/`, `/auth/reset-password/` | httpx.Client via _fresh_client() helper | VERIFIED | All 5 endpoints called; responses asserted with assert_status and field checks |
| `tests/api/test_profile.py` | `/auth/me/` | auth_client.get() and auth_client.patch() | VERIFIED | GET and PATCH both called; all required fields asserted |
| `tests/api/test_organizations.py` | `/organizations/` | auth_client POST/GET/PATCH, slug-based URLs | VERIFIED | All 4 tests use auth_client; no UUID in org URL paths |
| `tests/api/test_venues.py` | `tests/api/conftest.py` org fixture | org fixture injection for slug-based URLs | VERIFIED | test_list_venues_for_org(auth_client, org, venue) — org fixture injected |
| `tests/api/test_teams.py` | `/organizations/{slug}/members/` | httpx POST invite, GET list, DELETE remove | VERIFIED | /members/invite/ used in TTEAM-01/02/03; /members/ GET in TTEAM-03/04; /members/{membership_id}/ DELETE in TTEAM-04 |
| `tests/api/test_events.py` | `/organizations/{slug}/events/` | httpx POST/GET plus /publish/ and /cancel/ actions | VERIFIED | All event lifecycle endpoints called with correct slug-based URLs |
| `tests/api/test_ticket_tiers.py` | `/organizations/{slug}/events/{event-slug}/ticket-tiers/` | httpx POST/PATCH | VERIFIED | Base URL pattern used throughout; tier UUID used for detail URL |
| `tests/api/test_promos.py` | `/organizations/{slug}/events/{event-slug}/promo-codes/` | httpx POST/PATCH plus /validate/ | VERIFIED | All promo endpoints called; validate always uses auth_client |

---

## Data-Flow Trace (Level 4)

Not applicable. This project tests a live external API — test files are verification agents, not data-rendering components. All dynamic data comes from live API responses and is asserted in-test; no rendering pipeline to trace.

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| factories/common.py exports tier_name, promo_code | `python3 -c "from factories.common import tier_name, promo_code; print(tier_name()); print(promo_code())"` | Outputs test-{run}-tier-{hex} and TEST{RUN}{HEX} | PASS |
| tests/api/conftest.py has all 4 session fixtures | ast.parse check for org, venue, event, published_event | All 4 functions found | PASS |
| All 33 tests collected by pytest | `pytest tests/api/ --collect-only -q` | 33 tests collected in 0.04s | PASS |
| Test counts match plan specs per file | ast.parse function count vs expected | 5+2+4+3+4+7+4+4 = 33/33 all match | PASS |
| All 33 @pytest.mark.req markers present | `grep -rh @pytest.mark.req tests/api/` | 33 unique markers, one per required ID | PASS |
| conftest.py placeholder comment removed | `grep "Cleanup logic wired in Phase 2" conftest.py` | No matches — comment absent | PASS |
| conftest.py has teardown keywords | `grep -c "cancel\|ticket_tier_ids\|promo_code_ids\|venue_id" conftest.py` | 13 matches | PASS |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| TAUTH-01 | 02-02 | Test user registration with email, password, first name, last name | SATISFIED | test_register_user in test_auth.py; asserts 201, user.email, user.id, message |
| TAUTH-02 | 02-02 | Test login returns JWT access + refresh tokens | SATISFIED | test_login_returns_jwt_tokens; asserts "access" and "refresh" in response, len > 10 |
| TAUTH-03 | 02-02 | Test token refresh with rotation | SATISFIED | test_token_refresh_issues_new_tokens; asserts new tokens issued (access and refresh differ from originals); correctly skips old-token-invalidation check per RESEARCH.md |
| TAUTH-04 | 02-02 | Test password reset request sends email | SATISFIED | test_password_reset_request; asserts 200 returned regardless of email existence; email delivery is manual-only per VALIDATION.md |
| TAUTH-05 | 02-02 | Test password reset via uid + token link | SATISFIED | test_password_reset_bad_token; asserts 400 + "Invalid or expired reset link" message |
| TPROF-01 | 02-02 | Test GET /auth/me/ returns user profile | SATISFIED | test_get_profile; asserts all 8 required fields; email contains "@" |
| TPROF-02 | 02-02 | Test PATCH profile updates first name, last name, phone | SATISFIED | test_patch_profile; updates + asserts 3 fields; restores originals after test |
| TORG-01 | 02-03 | Test create organization (auto-assigned OWNER role) | SATISFIED | test_create_org_assigns_owner_role; asserts role=="OWNER", slug, id; registers for teardown |
| TORG-02 | 02-03 | Test list organizations where user is a member | SATISFIED | test_list_orgs_for_member; asserts list len >= 1, each item has "role", at least one OWNER |
| TORG-03 | 02-03 | Test OWNER/MANAGER can update organization details | SATISFIED | test_update_org_as_owner; PATCH with slug URL; asserts description updated |
| TORG-04 | 02-03 | Test organization slug is auto-generated from name with dedup suffix | SATISFIED | test_org_slug_auto_generated_with_dedup; creates two orgs with same name; slug2 startswith slug1 and slug1 != slug2 |
| TTEAM-01 | 02-04 | Test OWNER/MANAGER can invite a member by email with role | SATISFIED | test_owner_can_invite_member; OWNER invites registered user as VOLUNTEER; asserts 201 |
| TTEAM-02 | 02-04 | Test MANAGER cannot assign OWNER role when inviting | SATISFIED | test_manager_cannot_assign_owner_role; asserts 403 + "Managers cannot assign the Owner role" message; positive control: MANAGER can invite as VOLUNTEER (201) |
| TTEAM-03 | 02-04 | Test any org member can list team members | SATISFIED | test_any_member_can_list_team; VOLUNTEER client calls GET /members/; asserts 200, list len >= 2, each member has id/email/role |
| TTEAM-04 | 02-04 | Test only OWNER can remove a member | SATISFIED | test_only_owner_can_remove_member; MANAGER DELETE returns 403 + "Only owners can remove members"; OWNER DELETE returns 204; uses membership_id (not user UUID) |
| TVENU-01 | 02-03 | Test create venue with full details (name, address, capacity, etc.) | SATISFIED | test_create_venue_full_details; asserts 201 + 7 required fields; capacity==200 |
| TVENU-02 | 02-03 | Test list venues for organization | SATISFIED | test_list_venues_for_org; asserts 200, isinstance list, len >= 1 |
| TVENU-03 | 02-03 | Test update venue | SATISFIED | test_update_venue; PATCH capacity=999; asserts 200 + updated value; restores original |
| TEVNT-01 | 02-05 | Test create event with all fields (title, format, category, dates, venue, tags) | SATISFIED | test_create_event_all_fields; all fields posted including venue UUID as "venue"; asserts all required response fields |
| TEVNT-02 | 02-05 | Test event defaults to DRAFT status on creation | SATISFIED | test_event_defaults_to_draft; asserts status=="DRAFT" |
| TEVNT-03 | 02-05 | Test event slug is auto-generated from title | SATISFIED | test_event_slug_auto_generated; two events with same title produce different slugs |
| TEVNT-04 | 02-05 | Test publish DRAFT event (status -> PUBLISHED) | SATISFIED | test_publish_draft_event; POST /publish/ returns 200; asserts status=="PUBLISHED" |
| TEVNT-05 | 02-05 | Test cancel event from any status (status -> CANCELLED) | SATISFIED | test_cancel_event_from_any_status; tests cancel from DRAFT and from PUBLISHED; both return status=="CANCELLED" |
| TEVNT-06 | 02-05 | Test cannot publish CANCELLED event (400) | SATISFIED | test_cannot_publish_cancelled_event; asserts 400 + "Only draft events can be published" |
| TEVNT-07 | 02-05 | Test cannot publish already-published event (400) | SATISFIED | test_cannot_publish_already_published_event; asserts 400 + same error message |
| TTICK-01 | 02-05 | Test create ticket tier with all options (price, quantity, visibility, etc.) | SATISFIED | test_create_tier_all_options; all 10 response fields verified; visibility=="PUBLIC", is_active==True |
| TTICK-02 | 02-05 | Test quantity_remaining is calculated correctly | SATISFIED | test_quantity_remaining_calculated; quantity_total=50, quantity_sold==0, quantity_remaining==50 |
| TTICK-03 | 02-05 | Test visibility options (PUBLIC, HIDDEN, INVITE_ONLY) | SATISFIED | test_visibility_options; loop creates one tier per visibility; each returns matching value |
| TTICK-04 | 02-05 | Test soft-delete tier (is_active = false) | SATISFIED | test_soft_delete_tier; PATCH is_active=False returns 200 with is_active==False |
| TPRMO-01 | 02-05 | Test create promo code (PERCENTAGE and FIXED discount types) | SATISFIED | test_create_promo_percentage_and_fixed; both types created; discount_type asserted on each |
| TPRMO-02 | 02-05 | Test promo code stored uppercase | SATISFIED | test_promo_code_stored_uppercase; submits "lowercasecode"; asserts response code=="LOWERCASECODE" |
| TPRMO-03 | 02-05 | Test empty applicable_tier_ids means code applies to ALL tiers | SATISFIED | test_empty_tier_ids_applies_to_all; creates promo with [], validates against tier; asserts valid==True |
| TPRMO-04 | 02-05 | Test promo validate endpoint checks active, expired, tier match | SATISFIED | test_validate_promo_active_expired_tier; 3 cases: active (valid=True), deactivated (invalid), wrong tier (invalid) |

**All 33 phase 2 requirements: SATISFIED**

---

## Anti-Patterns Found

No blockers or warnings found.

| File | Pattern | Severity | Assessment |
|------|---------|----------|------------|
| None | — | — | No TODO/FIXME/placeholder comments found in any test file, conftest.py, or factories/common.py |
| None | — | — | No empty return stubs (return null, return [], return {}) found |

---

## Process Gaps (Non-Blocking)

These items are documentation/process gaps, not goal gaps. The code is fully implemented.

1. **02-02-SUMMARY.md and 02-03-SUMMARY.md are missing.** Plans 02-02 and 02-03 have no SUMMARY.md files, and ROADMAP.md marks them as `[ ]` (incomplete). However, all test files they were supposed to produce (test_auth.py, test_profile.py, test_organizations.py, test_venues.py) exist with full, substantive implementations covering all required requirement IDs. The phase goal is achieved; these are process artifacts that were not written.

2. **ROADMAP.md completion markers not updated for 02-02 and 02-03.** The `[ ]` next to those plans in ROADMAP.md should be `[x]`.

3. **VALIDATION.md nyquist_compliant: false.** The validation frontmatter was never updated to `true`. This is a sign-off item, not a code gap.

---

## Human Verification Required

### 1. Full Suite Live Run

**Test:** Run `pytest tests/api/ -v --tb=short` from the project root
**Expected:** All 33 tests pass; total runtime approximately 30 seconds (network-bound); teardown cleanup prints confirmation for all registered resources
**Why human:** Tests require live network access to the deployed backend at event-management-production-ad62.up.railway.app

### 2. TAUTH-04 Generic Message Content

**Test:** Run test_password_reset_request in isolation and inspect the response body
**Expected:** Response body contains a privacy-safe generic message (e.g., "If an account exists with that email...") as documented in VALIDATION.md
**Why human:** The test only asserts `len(response_text) > 0`, not the specific message wording; exact message requires live API observation

---

## Gaps Summary

No gaps. All 33 must-have tests exist, are substantive (real assertions against real API endpoints, not stubs), are wired (actual HTTP calls, not placeholders), and carry correct requirement ID markers. The phase goal is achieved.

The two human verification items (live test run and TAUTH-04 message wording) are standard operational checks, not code deficiencies.

---

_Verified: 2026-03-28_
_Verifier: Claude (gsd-verifier)_
