# Requirements: GatherGood E2E Testing Agent

**Defined:** 2026-03-28
**Core Value:** Every feature in TEST_SPEC.md is tested automatically and reports clear pass/fail results so the team knows the platform is ready to ship.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Test Infrastructure

- [x] **INFR-01**: Project scaffolded with pytest, httpx, and Playwright Python bindings
- [x] **INFR-02**: Environment config via pydantic-settings (.env for BASE_URL, credentials, secrets)
- [ ] **INFR-03**: Session-scoped JWT auth fixture that registers/logs in and auto-refreshes tokens before expiry
- [x] **INFR-04**: Unique test data factories using uuid4 suffixes to avoid live DB pollution
- [ ] **INFR-05**: Teardown harness that cleans up test-created data after each run where API allows
- [x] **INFR-06**: Requirement ID markers (@pytest.mark.req) mapping each test to its TEST_SPEC ID
- [x] **INFR-07**: Single CLI command to run the full test suite (pytest entry point)

### API Tests — Authentication

- [ ] **TAUTH-01**: Test user registration with email, password, first name, last name
- [ ] **TAUTH-02**: Test login returns JWT access + refresh tokens
- [ ] **TAUTH-03**: Test token refresh with rotation (old refresh token invalidated)
- [ ] **TAUTH-04**: Test password reset request sends email
- [ ] **TAUTH-05**: Test password reset via uid + token link

### API Tests — User Profile

- [ ] **TPROF-01**: Test GET /auth/me/ returns user profile
- [ ] **TPROF-02**: Test PATCH profile updates first name, last name, phone, avatar URL

### API Tests — Organizations

- [ ] **TORG-01**: Test create organization (auto-assigned OWNER role)
- [ ] **TORG-02**: Test list organizations where user is a member
- [ ] **TORG-03**: Test OWNER/MANAGER can update organization details
- [ ] **TORG-04**: Test organization slug is auto-generated from name with dedup suffix

### API Tests — Team Management

- [ ] **TTEAM-01**: Test OWNER/MANAGER can invite a member by email with role
- [ ] **TTEAM-02**: Test MANAGER cannot assign OWNER role when inviting
- [ ] **TTEAM-03**: Test any org member can list team members
- [ ] **TTEAM-04**: Test only OWNER can remove a member

### API Tests — Venues

- [ ] **TVENU-01**: Test create venue with full details (name, address, capacity, etc.)
- [ ] **TVENU-02**: Test list venues for organization
- [ ] **TVENU-03**: Test update venue

### API Tests — Events

- [ ] **TEVNT-01**: Test create event with all fields (title, format, category, dates, venue, tags)
- [ ] **TEVNT-02**: Test event defaults to DRAFT status on creation
- [ ] **TEVNT-03**: Test event slug is auto-generated from title
- [ ] **TEVNT-04**: Test publish DRAFT event (status → PUBLISHED)
- [ ] **TEVNT-05**: Test cancel event from any status (status → CANCELLED)
- [ ] **TEVNT-06**: Test cannot publish CANCELLED event (400)
- [ ] **TEVNT-07**: Test cannot publish already-published event (400)

### API Tests — Ticket Tiers

- [ ] **TTICK-01**: Test create ticket tier with all options (price, quantity, visibility, etc.)
- [ ] **TTICK-02**: Test quantity_remaining is calculated correctly
- [ ] **TTICK-03**: Test visibility options (PUBLIC, HIDDEN, INVITE_ONLY)
- [ ] **TTICK-04**: Test soft-delete tier (is_active = false)

### API Tests — Promo Codes

- [ ] **TPRMO-01**: Test create promo code (PERCENTAGE and FIXED discount types)
- [ ] **TPRMO-02**: Test promo code stored uppercase
- [ ] **TPRMO-03**: Test empty applicable_tier_ids means code applies to ALL tiers
- [ ] **TPRMO-04**: Test public endpoint validates promo code (active, not expired, under limit, tier match)

### API Tests — Checkout

- [ ] **TCHKT-01**: Test calculate endpoint returns line items, subtotal, discount, fees, total, is_free
- [ ] **TCHKT-02**: Test free checkout (total=0) completes immediately with COMPLETED status
- [ ] **TCHKT-03**: Test free checkout returns confirmation code and tickets with QR data
- [ ] **TCHKT-04**: Test paid checkout creates Stripe PaymentIntent and returns client_secret
- [ ] **TCHKT-05**: Test complete endpoint requires billing_name, billing_email, billing_phone
- [ ] **TCHKT-06**: Test checkout rejects quantity exceeding tier capacity (400)
- [ ] **TCHKT-07**: Test checkout rejects quantity below min_per_order (400)
- [ ] **TCHKT-08**: Test checkout rejects quantity above max_per_order (400)
- [ ] **TCHKT-09**: Test checkout rejects orders for non-PUBLISHED events (400)
- [ ] **TCHKT-10**: Test checkout rejects expired promo codes (400)
- [ ] **TCHKT-11**: Test checkout rejects promo codes exceeding usage limit (400)
- [ ] **TCHKT-12**: Test promo discount correctly applied to line item totals

### API Tests — Orders & Tickets

- [ ] **TORDR-01**: Test list own orders
- [ ] **TORDR-02**: Test view order detail (must be order owner)
- [ ] **TORDR-03**: Test lookup order by confirmation code (no auth)
- [ ] **TORDR-04**: Test confirmation code is 10-char alphanumeric
- [ ] **TORDR-05**: Test list own tickets
- [ ] **TORDR-06**: Test QR code data format: {order_id}:{tier_id}:{ticket_id}:{hmac_16hex}
- [ ] **TORDR-07**: Test HMAC computed over order_id:tier_id:ticket_id

### API Tests — QR Check-In

- [ ] **TCHKN-01**: Test any org member can scan QR to check in attendee
- [ ] **TCHKN-02**: Test successful scan returns status "success" with attendee details
- [ ] **TCHKN-03**: Test re-scan returns status "already_checked_in" with original timestamp
- [ ] **TCHKN-04**: Test invalid/forged QR returns status "invalid"
- [ ] **TCHKN-05**: Test cancelled/refunded ticket returns status "invalid"
- [ ] **TCHKN-06**: Test HMAC signature verified on every scan

### API Tests — Manual Check-In & Stats

- [ ] **TMCHK-01**: Test manual check-in by ticket ID
- [ ] **TMCHK-02**: Test same response format as QR scan
- [ ] **TSTAT-01**: Test check-in stats (total registered, checked in, not checked in, percentage)
- [ ] **TSTAT-02**: Test stats include per-tier breakdown
- [ ] **TSRCH-01**: Test search attendees by name, email, or confirmation code

### API Tests — Guest List

- [ ] **TGUST-01**: Test OWNER/MANAGER can view guest list
- [ ] **TGUST-02**: Test OWNER/MANAGER can export guest list as CSV

### API Tests — Email Settings

- [ ] **TEMAL-01**: Test view email config (confirmation, reminders, notifications toggles)
- [ ] **TEMAL-02**: Test update email config toggles
- [ ] **TEMAL-03**: Test send bulk email to all event attendees
- [ ] **TEMAL-04**: Test view email log

### API Tests — Event Analytics

- [ ] **TANLT-01**: Test view analytics (registrations, revenue, fees, net, attendance rate)
- [ ] **TANLT-02**: Test analytics includes registrations_by_tier breakdown
- [ ] **TANLT-03**: Test analytics includes registrations_over_time series

### API Tests — Public Pages

- [ ] **TPUBL-01**: Test browse published events with search, category, format filters
- [ ] **TPUBL-02**: Test only PUBLISHED and LIVE events appear (no DRAFT/CANCELLED)
- [ ] **TPUBL-03**: Test view organization public page with upcoming events
- [ ] **TPUBL-04**: Test view public event detail with PUBLIC ticket tiers only
- [ ] **TPUBL-05**: Test HIDDEN and INVITE_ONLY tiers not shown publicly

### API Tests — Permission Boundaries

- [ ] **TPERM-01**: Test VOLUNTEER cannot create events (403)
- [ ] **TPERM-02**: Test VOLUNTEER cannot invite members (403)
- [ ] **TPERM-03**: Test MANAGER cannot assign OWNER role (403)
- [ ] **TPERM-04**: Test MANAGER cannot remove members (403)
- [ ] **TPERM-05**: Test non-org-member cannot access org resources (403)

### Browser Tests — Frontend & UX

- [ ] **TFEND-01**: Test homepage displays hero section, feature cards, and auth-aware CTAs
- [ ] **TFEND-02**: Test navbar shows login/signup when logged out; dashboard links when logged in
- [ ] **TFEND-03**: Test mobile hamburger menu with all nav links
- [ ] **TFEND-04**: Test checkout flow has step indicators with current step highlighted
- [ ] **TFEND-05**: Test checkout pre-fills billing info for logged-in users
- [ ] **TFEND-06**: Test confirmation page shows confirmation code and QR codes
- [ ] **TFEND-07**: Test all pages responsive at 375px, 768px, and 1280px+
- [ ] **TFEND-08**: Test touch targets at least 44x44px on mobile
- [ ] **TFEND-09**: Test no horizontal overflow on any screen size
- [ ] **TFEND-10**: Test check-in page has scanner, search, manual check-in, and live stats

### Reporting

- [ ] **TRPT-01**: Test run produces HTML report with pass/fail per requirement ID
- [ ] **TRPT-02**: Report includes total pass/fail/skip counts and percentage
- [ ] **TRPT-03**: Failed tests include error details and screenshots (browser tests)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### CI/CD Integration

- **TCICD-01**: Tests run automatically on push via GitHub Actions
- **TCICD-02**: Test results posted as PR comment

### Performance Testing

- **TPERF-01**: Response time assertions on critical endpoints (< 500ms)
- **TPERF-02**: Concurrent user load simulation

### Advanced Reporting

- **TRPT-04**: Allure report integration with trend graphs
- **TRPT-05**: Slack notification on test failure

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Building/modifying the GatherGood platform | Already exists and is deployed — this project tests it |
| Visual regression testing | Focus is functional correctness, not pixel-level comparison |
| Load/stress testing | Functional QA only in v1 |
| Mocking or stubbing the backend | Tests must hit the real live API |
| Running tests in parallel | Shared live DB with no isolation — parallel writes would cause data conflicts |
| Mobile native app testing | Web-only platform, responsive browser tests are sufficient |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFR-01 | Phase 1 | Complete |
| INFR-02 | Phase 1 | Complete |
| INFR-03 | Phase 1 | Pending |
| INFR-04 | Phase 1 | Complete |
| INFR-05 | Phase 1 | Pending |
| INFR-06 | Phase 1 | Complete |
| INFR-07 | Phase 1 | Complete |
| TAUTH-01 | Phase 2 | Pending |
| TAUTH-02 | Phase 2 | Pending |
| TAUTH-03 | Phase 2 | Pending |
| TAUTH-04 | Phase 2 | Pending |
| TAUTH-05 | Phase 2 | Pending |
| TPROF-01 | Phase 2 | Pending |
| TPROF-02 | Phase 2 | Pending |
| TORG-01 | Phase 2 | Pending |
| TORG-02 | Phase 2 | Pending |
| TORG-03 | Phase 2 | Pending |
| TORG-04 | Phase 2 | Pending |
| TTEAM-01 | Phase 2 | Pending |
| TTEAM-02 | Phase 2 | Pending |
| TTEAM-03 | Phase 2 | Pending |
| TTEAM-04 | Phase 2 | Pending |
| TVENU-01 | Phase 2 | Pending |
| TVENU-02 | Phase 2 | Pending |
| TVENU-03 | Phase 2 | Pending |
| TEVNT-01 | Phase 2 | Pending |
| TEVNT-02 | Phase 2 | Pending |
| TEVNT-03 | Phase 2 | Pending |
| TEVNT-04 | Phase 2 | Pending |
| TEVNT-05 | Phase 2 | Pending |
| TEVNT-06 | Phase 2 | Pending |
| TEVNT-07 | Phase 2 | Pending |
| TTICK-01 | Phase 2 | Pending |
| TTICK-02 | Phase 2 | Pending |
| TTICK-03 | Phase 2 | Pending |
| TTICK-04 | Phase 2 | Pending |
| TPRMO-01 | Phase 2 | Pending |
| TPRMO-02 | Phase 2 | Pending |
| TPRMO-03 | Phase 2 | Pending |
| TPRMO-04 | Phase 2 | Pending |
| TCHKT-01 | Phase 3 | Pending |
| TCHKT-02 | Phase 3 | Pending |
| TCHKT-03 | Phase 3 | Pending |
| TCHKT-04 | Phase 3 | Pending |
| TCHKT-05 | Phase 3 | Pending |
| TCHKT-06 | Phase 3 | Pending |
| TCHKT-07 | Phase 3 | Pending |
| TCHKT-08 | Phase 3 | Pending |
| TCHKT-09 | Phase 3 | Pending |
| TCHKT-10 | Phase 3 | Pending |
| TCHKT-11 | Phase 3 | Pending |
| TCHKT-12 | Phase 3 | Pending |
| TORDR-01 | Phase 3 | Pending |
| TORDR-02 | Phase 3 | Pending |
| TORDR-03 | Phase 3 | Pending |
| TORDR-04 | Phase 3 | Pending |
| TORDR-05 | Phase 3 | Pending |
| TORDR-06 | Phase 3 | Pending |
| TORDR-07 | Phase 3 | Pending |
| TCHKN-01 | Phase 3 | Pending |
| TCHKN-02 | Phase 3 | Pending |
| TCHKN-03 | Phase 3 | Pending |
| TCHKN-04 | Phase 3 | Pending |
| TCHKN-05 | Phase 3 | Pending |
| TCHKN-06 | Phase 3 | Pending |
| TMCHK-01 | Phase 3 | Pending |
| TMCHK-02 | Phase 3 | Pending |
| TSTAT-01 | Phase 3 | Pending |
| TSTAT-02 | Phase 3 | Pending |
| TSRCH-01 | Phase 3 | Pending |
| TPERM-01 | Phase 4 | Pending |
| TPERM-02 | Phase 4 | Pending |
| TPERM-03 | Phase 4 | Pending |
| TPERM-04 | Phase 4 | Pending |
| TPERM-05 | Phase 4 | Pending |
| TGUST-01 | Phase 4 | Pending |
| TGUST-02 | Phase 4 | Pending |
| TEMAL-01 | Phase 4 | Pending |
| TEMAL-02 | Phase 4 | Pending |
| TEMAL-03 | Phase 4 | Pending |
| TEMAL-04 | Phase 4 | Pending |
| TANLT-01 | Phase 4 | Pending |
| TANLT-02 | Phase 4 | Pending |
| TANLT-03 | Phase 4 | Pending |
| TPUBL-01 | Phase 4 | Pending |
| TPUBL-02 | Phase 4 | Pending |
| TPUBL-03 | Phase 4 | Pending |
| TPUBL-04 | Phase 4 | Pending |
| TPUBL-05 | Phase 4 | Pending |
| TFEND-01 | Phase 4 | Pending |
| TFEND-02 | Phase 4 | Pending |
| TFEND-03 | Phase 4 | Pending |
| TFEND-04 | Phase 4 | Pending |
| TFEND-05 | Phase 4 | Pending |
| TFEND-06 | Phase 4 | Pending |
| TFEND-07 | Phase 4 | Pending |
| TFEND-08 | Phase 4 | Pending |
| TFEND-09 | Phase 4 | Pending |
| TFEND-10 | Phase 4 | Pending |
| TRPT-01 | Phase 5 | Pending |
| TRPT-02 | Phase 5 | Pending |
| TRPT-03 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 88 total
- Mapped to phases: 88
- Unmapped: 0

---
*Requirements defined: 2026-03-28*
*Last updated: 2026-03-28 after roadmap creation*
