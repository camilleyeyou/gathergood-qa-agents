# GatherGood E2E Testing Agent

## What This Is

An autonomous end-to-end testing agent that runs the full TEST_SPEC.md integration sequence against the live GatherGood event management platform. It verifies every API endpoint, UI flow, and business rule works correctly before shipping — like automated QA testers following a detailed test script.

## Core Value

Every feature in TEST_SPEC.md is tested automatically and reports clear pass/fail results so the team knows the platform is ready to ship.

## Requirements

### Validated

- Test harness scaffold with pytest + httpx + Playwright — Phase 1
- JWT auth fixture with token refresh against live backend — Phase 1
- Unique test data factories (uuid4 prefixes) for live DB isolation — Phase 1
- Teardown registry for test cleanup — Phase 1
- @pytest.mark.req markers linking tests to TEST_SPEC IDs — Phase 1
- Auth API tests (register, login, token refresh, password reset) — Phase 2
- Profile API tests (view, update) — Phase 2
- Organization API tests (create, list, update, slug dedup) — Phase 2
- Team management API tests (invite, roles, listing, removal) — Phase 2
- Venue API tests (create, list, update) — Phase 2
- Event lifecycle API tests (create, publish, cancel, invalid transitions) — Phase 2
- Ticket tier API tests (create, quantity, visibility, soft-delete) — Phase 2
- Promo code API tests (create, uppercase, tier applicability, validation) — Phase 2
- Teardown cleanup wired with 4-step reverse-dependency deletion — Phase 2
- Checkout API tests (calculate, free complete, quantity/promo validation) — Phase 3
- Order & ticket API tests (list, detail, confirmation code, QR format, HMAC) — Phase 3
- QR check-in API tests (scan, re-scan, invalid, manual, stats, search) — Phase 3
- Permission boundary tests (VOLUNTEER/MANAGER/non-member restrictions) — Phase 4
- Guest list and CSV export tests — Phase 4
- Email settings tests (config, bulk send, log) — Phase 4
- Event analytics tests (revenue, per-tier, timeline) — Phase 4
- Public pages tests (browse, org page, event detail, tier visibility) — Phase 4
- Playwright browser tests (homepage, navbar, responsive, touch targets, checkout flow, confirmation, check-in page) — Phase 4
- HTML report with requirement ID coverage table (pass/fail/skip per req) — Phase 5
- Screenshot and Playwright trace capture for failed browser tests — Phase 5
- Idempotent test runs via RUN_ID isolation — Phase 5
- AI QA agent framework with Claude Computer Use API + Playwright backend — Phase 6
- Agent test scenarios covering auth, events, checkout, check-in, permissions (10 tests) — Phase 6
- Natural language agent verdicts with token usage in HTML report — Phase 6
- ANTHROPIC_API_KEY env config with clean skip-when-missing behavior — Phase 6
- Digital literacy persona agents (5 personas x 3 flows = 15 test functions) with friction scoring — Phase 7
- Heatmap matrix HTML report comparing persona results side-by-side — Phase 7
- FastAPI deployment endpoint for Railway + static report for Vercel — Phase 7
- Next.js dashboard with interactive heatmap matrix and confusion drill-down slide-over — Phase 8
- Historical run selector with delta badges and sparkline trend charts — Phase 8
- Vercel-deployable static dashboard reading JSON artifacts from persona runs — Phase 8

### Active

All phases complete including Phase 8 persona dashboard frontend. Human verification pending for Vercel deployment and visual responsive testing.

### Out of Scope

- Building or modifying the GatherGood platform itself — it already exists and is deployed
- Load testing / performance benchmarking — this is functional QA only
- Visual regression testing — focus on functional correctness
- CI/CD pipeline integration — v1 is local CLI execution

## Context

**Target system (already deployed):**
- Frontend: `https://event-management-two-red.vercel.app/`
- Backend API: `https://event-management-production-ad62.up.railway.app/api/v1`
- Source repo: `https://github.com/camilleyeyou/Event-Management`
- Stack: Django REST Framework backend, Next.js frontend, PostgreSQL 16, Stripe payments
- Deployment: Vercel (frontend) + Railway (backend + DB)

**TEST_SPEC.md coverage (79 requirements across 10 domains):**
1. Authentication (AUTH-01 to AUTH-05) — register, login, JWT tokens, password reset
2. User Profile (PROF-01, PROF-02) — view and update profile
3. Organizations (ORG-01 to ORG-04) — create, list, update, auto-slug
4. Team Management (TEAM-01 to TEAM-04) — invite, roles, permissions
5. Venues (VENU-01 to VENU-03) — create, list, update
6. Events (EVNT-01 to EVNT-09) — full lifecycle with status transitions
7. Ticket Tiers (TICK-01 to TICK-04) — create, capacity, visibility, soft-delete
8. Promo Codes (PRMO-01 to PRMO-04) — create, validate, apply
9. Checkout (CHKT-01 to CHKT-12) — calculate, free/paid flows, validation errors
10. Orders & Tickets (ORDR-01 to ORDR-07) — list, detail, confirmation code, QR format
11. QR Check-In (CHKN-01 to CHKN-06) — scan, verify HMAC, status responses
12. Manual Check-In (MCHK-01, MCHK-02)
13. Check-In Stats (STAT-01 to STAT-03) and Search (SRCH-01)
14. Guest List (GUST-01, GUST-02) — view and CSV export
15. Email Settings (EMAL-01 to EMAL-04) — config, bulk send, log
16. Public Pages (PUBL-01 to PUBL-05) — browse, org page, event detail
17. Event Analytics (ANLT-01 to ANLT-03) — revenue, tiers, time series
18. Frontend & UX (FEND-01 to FEND-10) — responsive, navigation, checkout flow

**QR code format:** `{order_id}:{tier_id}:{ticket_id}:{hmac_sha256_first_16_hex_chars}`

**Authentication:** JWT with 30min access tokens, 7-day refresh with rotation, Bearer header

**Role hierarchy:** OWNER > MANAGER > VOLUNTEER

## Constraints

- **Target URLs**: Tests must run against the live deployed endpoints (not local dev)
- **Test isolation**: Tests should clean up after themselves where possible, or use unique data per run to avoid polluting the live database
- **Stripe**: Paid checkout tests will need Stripe test mode or may need to be marked as manual/skipped if no test keys available
- **No destructive actions**: Tests must not delete production data that other users depend on

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Test against live deployment, not local | User wants to verify the deployed site works, not a local copy | — Pending |
| Full E2E agent approach | User wants comprehensive automated QA, not just unit tests | — Pending |
| TEST_SPEC.md as source of truth | All test cases derived from the existing spec document | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-31 after Phase 8 completion — persona dashboard frontend*
