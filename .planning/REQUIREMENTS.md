# Requirements: GatherGood

**Defined:** 2026-03-28
**Core Value:** Community organizers can create an event, publish it, and have people register (free or paid) with working tickets and QR check-in.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Authentication

- [ ] **AUTH-01**: User can register with email, password, first name, and last name
- [ ] **AUTH-02**: User can log in with email/password and receive JWT access + refresh tokens
- [ ] **AUTH-03**: User can refresh an expired access token using a valid refresh token (rotation enabled)
- [ ] **AUTH-04**: User can request a password reset email
- [ ] **AUTH-05**: User can reset password via emailed uid + token link

### User Profile

- [ ] **PROF-01**: User can view their own profile (GET /auth/me/)
- [ ] **PROF-02**: User can update their first name, last name, phone, and avatar URL

### Organizations

- [ ] **ORG-01**: Authenticated user can create an organization (auto-assigned OWNER role)
- [ ] **ORG-02**: User can list organizations where they are a member
- [ ] **ORG-03**: OWNER or MANAGER can update organization details
- [ ] **ORG-04**: Organization slug is auto-generated from name with dedup suffix

### Team Management

- [ ] **TEAM-01**: OWNER or MANAGER can invite a member by email with a role assignment
- [ ] **TEAM-02**: MANAGER cannot assign the OWNER role when inviting
- [ ] **TEAM-03**: Any org member can list team members
- [ ] **TEAM-04**: Only OWNER can remove a member from the organization

### Venues

- [ ] **VENU-01**: Org member can create a venue with name, address, city, state, postal code, capacity, accessibility info, and parking notes
- [ ] **VENU-02**: Org member can list venues for their organization
- [ ] **VENU-03**: Org member can update a venue

### Events

- [ ] **EVNT-01**: OWNER or MANAGER can create an event with title, subtitle, description, format, category, start/end datetime, timezone, venue, and tags
- [ ] **EVNT-02**: Event status defaults to DRAFT on creation
- [ ] **EVNT-03**: Event slug is auto-generated from title with dedup suffix
- [ ] **EVNT-04**: OWNER or MANAGER can publish a DRAFT event (status → PUBLISHED)
- [ ] **EVNT-05**: OWNER or MANAGER can cancel an event from any status (status → CANCELLED)
- [ ] **EVNT-06**: System auto-transitions PUBLISHED → LIVE when current time passes start_datetime
- [ ] **EVNT-07**: System auto-transitions LIVE → COMPLETED when current time passes end_datetime
- [ ] **EVNT-08**: Cannot publish a CANCELLED event (400 error)
- [ ] **EVNT-09**: Cannot publish an already-published event (400 error)

### Ticket Tiers

- [ ] **TICK-01**: OWNER or MANAGER can create a ticket tier with name, description, price, quantity, min/max per order, visibility, attendance mode, and sort order
- [ ] **TICK-02**: Ticket tier tracks quantity_remaining as a calculated field
- [ ] **TICK-03**: Ticket tier supports visibility options: PUBLIC, HIDDEN, INVITE_ONLY
- [ ] **TICK-04**: Ticket tier can be soft-deleted (is_active = false)

### Promo Codes

- [ ] **PRMO-01**: OWNER or MANAGER can create a promo code with code, discount type (PERCENTAGE/FIXED), discount value, applicable tiers, usage limit, per-customer limit, valid date range
- [ ] **PRMO-02**: Promo code is stored uppercase automatically
- [ ] **PRMO-03**: Empty applicable_tier_ids means code applies to ALL tiers
- [ ] **PRMO-04**: Public endpoint to validate a promo code against specific tier IDs (checks active, not expired, under usage limit, tier applicability)

### Checkout

- [ ] **CHKT-01**: Calculate endpoint returns line items, subtotal, discount, fees, total, and is_free flag
- [ ] **CHKT-02**: Free checkout (total=0) completes immediately with status COMPLETED
- [ ] **CHKT-03**: Free checkout returns confirmation code and tickets with QR code data
- [ ] **CHKT-04**: Paid checkout creates a PaymentIntent via Stripe and returns client_secret
- [ ] **CHKT-05**: Complete endpoint requires billing_name, billing_email, billing_phone
- [ ] **CHKT-06**: Checkout rejects quantity exceeding tier capacity (400)
- [ ] **CHKT-07**: Checkout rejects quantity below tier min_per_order (400)
- [ ] **CHKT-08**: Checkout rejects quantity above tier max_per_order (400)
- [ ] **CHKT-09**: Checkout rejects orders for non-PUBLISHED events (400)
- [ ] **CHKT-10**: Checkout rejects expired promo codes (400)
- [ ] **CHKT-11**: Checkout rejects promo codes that have exceeded usage limit (400)
- [ ] **CHKT-12**: Promo discount is correctly applied to line item totals

### Orders & Tickets

- [ ] **ORDR-01**: Authenticated user can list their own orders
- [ ] **ORDR-02**: Authenticated user can view order detail (must be order owner)
- [ ] **ORDR-03**: Anyone can look up an order by confirmation code (no auth)
- [ ] **ORDR-04**: Confirmation code is a 10-character alphanumeric string
- [ ] **ORDR-05**: Authenticated user can list their own tickets
- [ ] **ORDR-06**: Each ticket has QR code data in format: {order_id}:{tier_id}:{ticket_id}:{hmac_16hex}
- [ ] **ORDR-07**: HMAC is computed over order_id:tier_id:ticket_id using a dedicated signing key

### QR Check-In

- [ ] **CHKN-01**: Any org member can scan a QR code to check in an attendee
- [ ] **CHKN-02**: Successful scan returns status "success" with attendee name, email, tier, and timestamp
- [ ] **CHKN-03**: Scanning an already-checked-in ticket returns status "already_checked_in" with original timestamp
- [ ] **CHKN-04**: Scanning an invalid/forged QR returns status "invalid" with appropriate message
- [ ] **CHKN-05**: Scanning a cancelled/refunded ticket returns status "invalid"
- [ ] **CHKN-06**: HMAC signature is verified on every scan (not just on generation)

### Manual Check-In

- [ ] **MCHK-01**: Any org member can manually check in a ticket by ticket ID
- [ ] **MCHK-02**: Same response format as QR scan check-in

### Check-In Stats & Search

- [ ] **STAT-01**: Any org member can view check-in stats (total registered, checked in, not checked in, percentage)
- [ ] **STAT-02**: Stats include per-tier breakdown
- [ ] **STAT-03**: Frontend polls stats every 10 seconds for live updates
- [ ] **SRCH-01**: Any org member can search attendees by name, email, or confirmation code

### Guest List

- [ ] **GUST-01**: OWNER or MANAGER can view the guest list for an event
- [ ] **GUST-02**: OWNER or MANAGER can export the guest list as CSV

### Event Analytics

- [ ] **ANLT-01**: OWNER or MANAGER can view event analytics (total registrations, total revenue, fees, net revenue, attendance rate)
- [ ] **ANLT-02**: Analytics includes registrations_by_tier breakdown
- [ ] **ANLT-03**: Analytics includes registrations_over_time time series

### Email Settings

- [ ] **EMAL-01**: OWNER or MANAGER can view email config for an event (confirmation, reminders, notifications toggles)
- [ ] **EMAL-02**: OWNER or MANAGER can update email config toggles
- [ ] **EMAL-03**: OWNER or MANAGER can send a bulk email to all event attendees
- [ ] **EMAL-04**: OWNER or MANAGER can view the email log for an event

### Public Pages

- [ ] **PUBL-01**: Anyone can browse published events with search, category, and format filters
- [ ] **PUBL-02**: Only PUBLISHED and LIVE events appear in browse (no DRAFT or CANCELLED)
- [ ] **PUBL-03**: Anyone can view an organization's public page with upcoming events
- [ ] **PUBL-04**: Anyone can view a public event detail page with PUBLIC ticket tiers only
- [ ] **PUBL-05**: HIDDEN and INVITE_ONLY tiers are not shown on the public event page

### Frontend & UX

- [ ] **FEND-01**: Homepage displays hero section, feature cards, and auth-aware footer/CTAs
- [ ] **FEND-02**: Navbar shows login/signup when logged out; dashboard/browse/tickets/avatar when logged in
- [ ] **FEND-03**: Mobile hamburger menu with all nav links
- [ ] **FEND-04**: Checkout flow has step indicators with current step highlighted
- [ ] **FEND-05**: Checkout pre-fills billing info for logged-in users
- [ ] **FEND-06**: Confirmation page shows confirmation code prominently and QR codes for each ticket
- [ ] **FEND-07**: All pages responsive at mobile (375px), tablet (768px), and desktop (1280px+)
- [ ] **FEND-08**: Touch targets at least 44x44px on mobile
- [ ] **FEND-09**: No horizontal overflow on any screen size
- [ ] **FEND-10**: Check-in page has scanner, search, manual check-in, and live stats with auto-refresh

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Social Login

- **SLGN-01**: User can log in via Google OAuth
- **SLGN-02**: User can log in via GitHub OAuth

### Notifications

- **NOTF-01**: User receives push notifications for event updates
- **NOTF-02**: User can configure notification preferences

### Advanced Features

- **ADVN-01**: Multi-currency payment support
- **ADVN-02**: Donation processing alongside ticketing
- **ADVN-03**: CRM integration (Salesforce, HubSpot) via API
- **ADVN-04**: Multi-language / i18n support

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Real-time chat / messaging | High infrastructure complexity, moderation burden, unrelated to core ticketing |
| Video / livestream integration | Storage/CDN costs, encoding pipelines — link to Zoom/YouTube instead |
| Native mobile app | Mobile-responsive web app sufficient; separate codebase not justified for v1 |
| Seating charts / seat selection | Complex UI, niche for community orgs — capacity limits with tiers covers the need |
| Dynamic / demand-based pricing | Anti-aligned with nonprofit mission; promo codes achieve similar outcomes |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Pending |
| AUTH-02 | Phase 1 | Pending |
| AUTH-03 | Phase 1 | Pending |
| AUTH-04 | Phase 1 | Pending |
| AUTH-05 | Phase 1 | Pending |
| PROF-01 | Phase 1 | Pending |
| PROF-02 | Phase 1 | Pending |
| ORG-01 | Phase 1 | Pending |
| ORG-02 | Phase 1 | Pending |
| ORG-03 | Phase 1 | Pending |
| ORG-04 | Phase 1 | Pending |
| TEAM-01 | Phase 1 | Pending |
| TEAM-02 | Phase 1 | Pending |
| TEAM-03 | Phase 1 | Pending |
| TEAM-04 | Phase 1 | Pending |
| VENU-01 | Phase 1 | Pending |
| VENU-02 | Phase 1 | Pending |
| VENU-03 | Phase 1 | Pending |
| EVNT-01 | Phase 2 | Pending |
| EVNT-02 | Phase 2 | Pending |
| EVNT-03 | Phase 2 | Pending |
| EVNT-04 | Phase 2 | Pending |
| EVNT-05 | Phase 2 | Pending |
| EVNT-06 | Phase 2 | Pending |
| EVNT-07 | Phase 2 | Pending |
| EVNT-08 | Phase 2 | Pending |
| EVNT-09 | Phase 2 | Pending |
| TICK-01 | Phase 2 | Pending |
| TICK-02 | Phase 2 | Pending |
| TICK-03 | Phase 2 | Pending |
| TICK-04 | Phase 2 | Pending |
| PRMO-01 | Phase 2 | Pending |
| PRMO-02 | Phase 2 | Pending |
| PRMO-03 | Phase 2 | Pending |
| PRMO-04 | Phase 2 | Pending |
| PUBL-01 | Phase 2 | Pending |
| PUBL-02 | Phase 2 | Pending |
| PUBL-03 | Phase 2 | Pending |
| PUBL-04 | Phase 2 | Pending |
| PUBL-05 | Phase 2 | Pending |
| FEND-01 | Phase 2 | Pending |
| FEND-02 | Phase 2 | Pending |
| FEND-03 | Phase 2 | Pending |
| CHKT-01 | Phase 3 | Pending |
| CHKT-02 | Phase 3 | Pending |
| CHKT-03 | Phase 3 | Pending |
| CHKT-04 | Phase 3 | Pending |
| CHKT-05 | Phase 3 | Pending |
| CHKT-06 | Phase 3 | Pending |
| CHKT-07 | Phase 3 | Pending |
| CHKT-08 | Phase 3 | Pending |
| CHKT-09 | Phase 3 | Pending |
| CHKT-10 | Phase 3 | Pending |
| CHKT-11 | Phase 3 | Pending |
| CHKT-12 | Phase 3 | Pending |
| ORDR-01 | Phase 3 | Pending |
| ORDR-02 | Phase 3 | Pending |
| ORDR-03 | Phase 3 | Pending |
| ORDR-04 | Phase 3 | Pending |
| ORDR-05 | Phase 3 | Pending |
| ORDR-06 | Phase 3 | Pending |
| ORDR-07 | Phase 3 | Pending |
| CHKN-01 | Phase 4 | Pending |
| CHKN-02 | Phase 4 | Pending |
| CHKN-03 | Phase 4 | Pending |
| CHKN-04 | Phase 4 | Pending |
| CHKN-05 | Phase 4 | Pending |
| CHKN-06 | Phase 4 | Pending |
| MCHK-01 | Phase 4 | Pending |
| MCHK-02 | Phase 4 | Pending |
| STAT-01 | Phase 4 | Pending |
| STAT-02 | Phase 4 | Pending |
| STAT-03 | Phase 4 | Pending |
| SRCH-01 | Phase 4 | Pending |
| GUST-01 | Phase 4 | Pending |
| GUST-02 | Phase 4 | Pending |
| EMAL-01 | Phase 5 | Pending |
| EMAL-02 | Phase 5 | Pending |
| EMAL-03 | Phase 5 | Pending |
| EMAL-04 | Phase 5 | Pending |
| ANLT-01 | Phase 6 | Pending |
| ANLT-02 | Phase 6 | Pending |
| ANLT-03 | Phase 6 | Pending |
| FEND-04 | Phase 6 | Pending |
| FEND-05 | Phase 6 | Pending |
| FEND-06 | Phase 6 | Pending |
| FEND-07 | Phase 6 | Pending |
| FEND-08 | Phase 6 | Pending |
| FEND-09 | Phase 6 | Pending |
| FEND-10 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 79 total
- Mapped to phases: 79
- Unmapped: 0

---
*Requirements defined: 2026-03-28*
*Last updated: 2026-03-28 after roadmap creation*
