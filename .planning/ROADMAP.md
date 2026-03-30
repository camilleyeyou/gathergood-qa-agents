# Roadmap: GatherGood E2E Testing Agent

## Overview

Build a Python-based automated QA agent that runs the full TEST_SPEC.md integration sequence against the live GatherGood platform. The build proceeds in five phases: foundation infrastructure first (auth, data isolation, teardown), then core API domain tests, then payment-sensitive checkout and check-in tests, then remaining API domains plus browser UI tests, and finally edge cases and report polish. Each phase produces a directly runnable, verifiable test capability before the next begins.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Project scaffold, auth fixture, data factories, teardown harness, and CLI entry point (completed 2026-03-28)
- [ ] **Phase 2: Core API Tests** - API test coverage for auth, profiles, orgs, teams, venues, events, ticket tiers, and promo codes
- [x] **Phase 3: Checkout, Orders & Check-In** - Payment-sensitive checkout tests with Stripe gating, order verification, and QR/manual check-in (completed 2026-03-28)
- [x] **Phase 4: Permissions, Analytics & Browser UI** - Permission boundary matrix, guest list, email, analytics, public pages, and all Playwright browser tests (completed 2026-03-29)
- [x] **Phase 5: Edge Cases & Reporting** - Edge case coverage, status transition guards, idempotency verification, and HTML report completeness (completed 2026-03-29)
- [ ] **Phase 6: AI QA Agents** - Claude Computer Use powered browser agents that test the site like human QA testers
- [ ] **Phase 7: Digital Literacy Persona Agents** - AI agents simulating users with varying digital literacy to find UX friction and accessibility gaps, deployable on Railway/Vercel

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
**Plans:** 2/2 plans complete

Plans:
- [x] 01-01-PLAN.md — Project scaffold, dependencies, config, factories, helpers, conftest with auth/teardown/markers
- [x] 01-02-PLAN.md — Smoke tests validating foundation against live backend

### Phase 2: Core API Tests
**Goal**: All core domain API endpoints are covered by tests that produce clear pass/fail results mapped to TEST_SPEC requirement IDs
**Depends on**: Phase 1
**Requirements**: TAUTH-01, TAUTH-02, TAUTH-03, TAUTH-04, TAUTH-05, TPROF-01, TPROF-02, TORG-01, TORG-02, TORG-03, TORG-04, TTEAM-01, TTEAM-02, TTEAM-03, TTEAM-04, TVENU-01, TVENU-02, TVENU-03, TEVNT-01, TEVNT-02, TEVNT-03, TEVNT-04, TEVNT-05, TEVNT-06, TEVNT-07, TTICK-01, TTICK-02, TTICK-03, TTICK-04, TPRMO-01, TPRMO-02, TPRMO-03, TPRMO-04
**Success Criteria** (what must be TRUE):
  1. Registration, login, token refresh, and password reset all produce pass/fail results against the live backend
  2. The full org-to-event chain (create org → create team → create venue → create event → publish → cancel) runs end-to-end with no test-order dependencies
  3. Ticket tier visibility options and promo code validation rules each produce an explicit test result
  4. Every test in this phase carries a requirement ID marker and appears by name in the console output
**Plans:** 5 plans

Plans:
- [x] 02-01-PLAN.md — Teardown cleanup, extended factories, shared session-scoped API fixtures
- [ ] 02-02-PLAN.md — Auth and profile API tests (TAUTH-01 to TAUTH-05, TPROF-01, TPROF-02)
- [ ] 02-03-PLAN.md — Organization and venue API tests (TORG-01 to TORG-04, TVENU-01 to TVENU-03)
- [x] 02-04-PLAN.md — Team management API tests (TTEAM-01 to TTEAM-04)
- [x] 02-05-PLAN.md — Event, ticket tier, and promo code API tests (TEVNT-01 to TEVNT-07, TTICK-01 to TTICK-04, TPRMO-01 to TPRMO-04)

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
**Plans:** 3/3 plans complete

Plans:
- [x] 03-01-PLAN.md — Checkout fixtures and all 12 checkout tests (TCHKT-01 to TCHKT-12)
- [x] 03-02-PLAN.md — Order and ticket tests (TORDR-01 to TORDR-07)
- [x] 03-03-PLAN.md — QR/manual check-in, stats, and search tests (TCHKN-01 to TCHKN-06, TMCHK-01/02, TSTAT-01/02, TSRCH-01)

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
**Plans:** 5/5 plans complete

Plans:
- [x] 04-01-PLAN.md — Permission boundary tests for VOLUNTEER, MANAGER, and non-member roles (TPERM-01 to TPERM-05)
- [x] 04-02-PLAN.md — Guest list, email settings, and analytics API tests (TGUST-01/02, TEMAL-01 to TEMAL-04, TANLT-01 to TANLT-03)
- [x] 04-03-PLAN.md — Public browse, org page, and event detail with tier visibility filtering (TPUBL-01 to TPUBL-05)
- [x] 04-04-PLAN.md — Playwright setup and homepage, navbar, responsive, touch target browser tests (TFEND-01/02/03/07/08/09)
- [x] 04-05-PLAN.md — Checkout flow, confirmation, and check-in page browser tests (TFEND-04/05/06/10)

### Phase 5: Edge Cases & Reporting
**Goal**: The suite handles known failure modes cleanly and produces a human-readable HTML report with 100% requirement ID coverage
**Depends on**: Phase 4
**Requirements**: TRPT-01, TRPT-02, TRPT-03
**Success Criteria** (what must be TRUE):
  1. The HTML report lists every TEST_SPEC requirement ID with a PASS, FAIL, or SKIP status and includes total counts and pass percentage
  2. Failed browser tests include a screenshot and Playwright trace file attached to the report entry
  3. Running the full suite twice in sequence produces identical results — no test fails on second run due to leftover data from the first
**Plans:** 1 plan

Plans:
- [x] 05-01-PLAN.md — HTML report plugin with requirement ID coverage, screenshot/trace capture, and idempotency verification

### Phase 6: AI QA Agents
**Goal**: Claude Computer Use powered browser agents test the live GatherGood site like human QA testers, layered on top of the existing deterministic test suite
**Depends on**: Phase 5
**Requirements**: AIQA-01, AIQA-02, AIQA-03, AIQA-04, AIQA-05, AIQA-06, AIQA-07, AIQA-08, AIQA-09, AIQA-10, AIQA-11, AIQA-12
**Success Criteria** (what must be TRUE):
  1. The agent framework takes a screenshot, sends it to Claude Sonnet via Computer Use API, executes the returned browser action, and loops until Claude signals completion or the iteration cap (20 steps) is hit
  2. Running `pytest tests/ai_agents/` executes all AI agent scenarios with `@pytest.mark.req` markers and produces PASS/FAIL/INCONCLUSIVE verdicts in the HTML report
  3. Agent scenarios cover auth flow, event management, checkout, check-in, and permission boundaries — each producing a natural language observation alongside the verdict
  4. The `ANTHROPIC_API_KEY` is loaded via pydantic-settings and agent tests skip cleanly with an explicit message when the key is not configured
  5. Each scenario respects MAX_ITERATIONS=20 to prevent runaway API costs, and logs step count and token usage
**Plans:** 3 plans

Plans:
- [x] 06-01-PLAN.md — Agent framework: anthropic SDK, PlaywrightComputerBackend, agent loop, pytest fixtures, env config
- [x] 06-02-PLAN.md — Agent test scenarios: auth, event management, checkout, check-in, permissions
- [x] 06-03-PLAN.md — Report integration: natural language verdicts, token usage, and HTML report extras

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 2/2 | Complete   | 2026-03-28 |
| 2. Core API Tests | 2/5 | In progress | - |
| 3. Checkout, Orders & Check-In | 3/3 | Complete   | 2026-03-28 |
| 4. Permissions, Analytics & Browser UI | 5/5 | Complete   | 2026-03-29 |
| 5. Edge Cases & Reporting | 1/1 | Complete   | 2026-03-29 |
| 6. AI QA Agents | 0/3 | Not started | - |
| 7. Digital Literacy Persona Agents | 3/4 | In Progress|  |

### Phase 7: Digital Literacy Persona Agents
**Goal**: AI agents simulate users of varying digital literacy (tech-savvy, casual, low-literacy, non-native English, impatient) across core flows, reporting friction scores, confusion points, and UX improvement suggestions — deployable on Railway and Vercel
**Depends on**: Phase 6
**Requirements**: P7-SC1, P7-SC2, P7-SC3, P7-SC4, P7-SC5
**Success Criteria** (what must be TRUE):
  1. Each persona agent completes core flows (registration, event browsing, checkout) and produces a structured usability report with friction score, confusion points, and improvement suggestions
  2. At least 5 distinct digital literacy personas are configurable via prompt templates
  3. An aggregate report compares persona results side-by-side, highlighting where low-literacy personas fail or struggle vs tech-savvy ones
  4. The system is deployable on Railway (backend/agent runner) and Vercel (report dashboard) with environment-based configuration
  5. Running a full persona sweep produces actionable UX insights, not just pass/fail
**Plans:** 3/4 plans executed

Plans:
- [x] 07-01-PLAN.md — Core persona library: persona definitions, friction scorer, persona runner, artifact writer
- [x] 07-02-PLAN.md — Report generation: Jinja2 heatmap template and CLI report script
- [ ] 07-03-PLAN.md — Pytest test sweep: conftest, fixtures, and 15 persona test functions (5 personas x 3 flows)
- [x] 07-04-PLAN.md — Deployment: FastAPI endpoint for Railway trigger, Procfile, and .env.example
