# Roadmap: GatherGood E2E Testing Agent

## Overview

Build a Python-based automated QA agent that runs the full TEST_SPEC.md integration sequence against the live GatherGood platform. The build proceeds in five phases: foundation infrastructure first (auth, data isolation, teardown), then core API domain tests, then payment-sensitive checkout and check-in tests, then remaining API domains plus browser UI tests, and finally edge cases and report polish. Each phase produces a directly runnable, verifiable test capability before the next begins.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation** - Project scaffold, auth fixture, data factories, teardown harness, and CLI entry point
- [ ] **Phase 2: Core API Tests** - API test coverage for auth, profiles, orgs, teams, venues, events, ticket tiers, and promo codes
- [ ] **Phase 3: Checkout, Orders & Check-In** - Payment-sensitive checkout tests with Stripe gating, order verification, and QR/manual check-in
- [ ] **Phase 4: Permissions, Analytics & Browser UI** - Permission boundary matrix, guest list, email, analytics, public pages, and all Playwright browser tests
- [ ] **Phase 5: Edge Cases & Reporting** - Edge case coverage, status transition guards, idempotency verification, and HTML report completeness

## Phase Details

### Phase 1: Foundation
**Goal**: The test harness is safe to run against the live database and every downstream test can be written against it
**Depends on**: Nothing (first phase)
**Requirements**: INFR-01, INFR-02, INFR-03, INFR-04, INFR-05, INFR-06, INFR-07
**Success Criteria** (what must be TRUE):
  1. Running `pytest` from the project root executes the full suite with a single command and exits with a clear pass/fail code
  2. A session-scoped auth fixture logs in once and proactively refreshes the JWT token before expiry — no test fails with 401 due to token age
  3. All test-created resources use unique `test-{run-id}-` prefixed names, preventing collision with live data across runs
  4. The teardown harness deletes test-created resources in reverse dependency order after the session, leaving the live database clean
  5. Each test function carries a `@pytest.mark.req("SPEC-ID")` marker that links it to its TEST_SPEC.md requirement
**Plans**: TBD

### Phase 2: Core API Tests
**Goal**: All core domain API endpoints are covered by tests that produce clear pass/fail results mapped to TEST_SPEC requirement IDs
**Depends on**: Phase 1
**Requirements**: TAUTH-01, TAUTH-02, TAUTH-03, TAUTH-04, TAUTH-05, TPROF-01, TPROF-02, TORG-01, TORG-02, TORG-03, TORG-04, TTEAM-01, TTEAM-02, TTEAM-03, TTEAM-04, TVENU-01, TVENU-02, TVENU-03, TEVNT-01, TEVNT-02, TEVNT-03, TEVNT-04, TEVNT-05, TEVNT-06, TEVNT-07, TTICK-01, TTICK-02, TTICK-03, TTICK-04, TPRMO-01, TPRMO-02, TPRMO-03, TPRMO-04
**Success Criteria** (what must be TRUE):
  1. Registration, login, token refresh, and password reset all produce pass/fail results against the live backend
  2. The full org-to-event chain (create org → create team → create venue → create event → publish → cancel) runs end-to-end with no test-order dependencies
  3. Ticket tier visibility options and promo code validation rules each produce an explicit test result
  4. Every test in this phase carries a requirement ID marker and appears by name in the console output
**Plans**: TBD

### Phase 3: Checkout, Orders & Check-In
**Goal**: Checkout, order, and check-in flows are fully tested with Stripe live-mode damage prevention in place
**Depends on**: Phase 2
**Requirements**: TCHKT-01, TCHKT-02, TCHKT-03, TCHKT-04, TCHKT-05, TCHKT-06, TCHKT-07, TCHKT-08, TCHKT-09, TCHKT-10, TCHKT-11, TCHKT-12, TORDR-01, TORDR-02, TORDR-03, TORDR-04, TORDR-05, TORDR-06, TORDR-07, TCHKN-01, TCHKN-02, TCHKN-03, TCHKN-04, TCHKN-05, TCHKN-06, TMCHK-01, TMCHK-02, TSTAT-01, TSTAT-02, TSRCH-01
**Success Criteria** (what must be TRUE):
  1. Free checkout completes end-to-end and produces a confirmation code plus QR-formatted ticket data from the live API
  2. Paid checkout tests either execute against Stripe test mode or are cleanly skipped with an explicit SKIP reason — no live-mode payment is ever attempted with a test card
  3. QR check-in tests use real QR strings retrieved from the orders API — re-scan returns "already_checked_in", forged QR returns "invalid"
  4. Manual check-in and check-in stats (per-tier breakdown, percentage) each produce a pass/fail result
  5. Order confirmation code is verified as 10-character alphanumeric and HMAC format is verified as `{order_id}:{tier_id}:{ticket_id}:{hmac_16hex}`
**Plans**: TBD

### Phase 4: Permissions, Analytics & Browser UI
**Goal**: Permission boundaries are verified across all three roles, remaining API domains are covered, and all frontend UI flows pass automated browser tests
**Depends on**: Phase 3
**Requirements**: TPERM-01, TPERM-02, TPERM-03, TPERM-04, TPERM-05, TGUST-01, TGUST-02, TEMAL-01, TEMAL-02, TEMAL-03, TEMAL-04, TANLT-01, TANLT-02, TANLT-03, TPUBL-01, TPUBL-02, TPUBL-03, TPUBL-04, TPUBL-05, TFEND-01, TFEND-02, TFEND-03, TFEND-04, TFEND-05, TFEND-06, TFEND-07, TFEND-08, TFEND-09, TFEND-10
**Success Criteria** (what must be TRUE):
  1. VOLUNTEER is blocked from creating events and inviting members (403), MANAGER is blocked from assigning OWNER role and removing members (403), and non-members are blocked from org resources (403) — each as an explicit test result
  2. Guest list CSV export and email log endpoints produce pass/fail results
  3. Analytics endpoint returns registrations, revenue, per-tier breakdown, and time series — each field verified
  4. Public browse shows only PUBLISHED and LIVE events; HIDDEN and INVITE_ONLY tiers are absent from public event detail
  5. Playwright browser tests verify responsive layout at 375px, 768px, and 1280px, the checkout step indicator, and the check-in page scanner/search/stats UI
**UI hint**: yes
**Plans**: TBD

### Phase 5: Edge Cases & Reporting
**Goal**: The suite handles known failure modes cleanly and produces a human-readable HTML report with 100% requirement ID coverage
**Depends on**: Phase 4
**Requirements**: TRPT-01, TRPT-02, TRPT-03
**Success Criteria** (what must be TRUE):
  1. The HTML report lists every TEST_SPEC requirement ID with a PASS, FAIL, or SKIP status and includes total counts and pass percentage
  2. Failed browser tests include a screenshot and Playwright trace file attached to the report entry
  3. Running the full suite twice in sequence produces identical results — no test fails on second run due to leftover data from the first
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 0/TBD | Not started | - |
| 2. Core API Tests | 0/TBD | Not started | - |
| 3. Checkout, Orders & Check-In | 0/TBD | Not started | - |
| 4. Permissions, Analytics & Browser UI | 0/TBD | Not started | - |
| 5. Edge Cases & Reporting | 0/TBD | Not started | - |
