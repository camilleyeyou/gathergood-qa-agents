# Roadmap: GatherGood

## Overview

GatherGood is built along its strict data dependency chain: users and organizations must exist before events can be created, events must exist before ticket tiers and checkout can function, orders must exist before QR codes can be generated, and all write paths must be stable before analytics can return meaningful data. Six phases follow this chain directly — each phase delivers a complete, testable capability and unblocks the next. The end-to-end happy path (create event, register attendee, receive QR ticket, check in at the door) is complete after Phase 4. Phases 5 and 6 add the communication and reporting layer that turns the platform into a complete community organizer tool.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation** - Users, organizations, teams, and venues are operational with correct permission enforcement
- [ ] **Phase 2: Events** - Events and ticket tiers are created, published, and discoverable by the public
- [ ] **Phase 3: Checkout & Orders** - Attendees can register for free and paid events with confirmed tickets
- [ ] **Phase 4: QR Check-In** - Organizers can check in attendees at the door via QR scan or manual search
- [ ] **Phase 5: Email & Notifications** - Attendees receive confirmation emails; organizers can send reminders and bulk messages
- [ ] **Phase 6: Analytics & Polish** - Organizers can view event analytics; all pages are responsive and production-ready

## Phase Details

### Phase 1: Foundation
**Goal**: Users can register, log in, and manage organizations with correct role-based access
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, PROF-01, PROF-02, ORG-01, ORG-02, ORG-03, ORG-04, TEAM-01, TEAM-02, TEAM-03, TEAM-04, VENU-01, VENU-02, VENU-03
**Success Criteria** (what must be TRUE):
  1. A new user can register with email and password, log in, and receive a JWT access and refresh token pair that persists across page loads
  2. A logged-in user can request a password reset email and successfully change their password via the emailed link
  3. A user can create an organization and be automatically assigned the OWNER role; a MANAGER they invite cannot assign the OWNER role to others
  4. An OWNER can remove a team member; any org member can list team members and view venues
  5. An org member can create, list, and update venues for their organization
**Plans**: TBD
**UI hint**: yes

### Phase 2: Events
**Goal**: Organizers can create events with ticket tiers and promo codes, and the public can discover and browse them
**Depends on**: Phase 1
**Requirements**: EVNT-01, EVNT-02, EVNT-03, EVNT-04, EVNT-05, EVNT-06, EVNT-07, EVNT-08, EVNT-09, TICK-01, TICK-02, TICK-03, TICK-04, PRMO-01, PRMO-02, PRMO-03, PRMO-04, PUBL-01, PUBL-02, PUBL-03, PUBL-04, PUBL-05, FEND-01, FEND-02, FEND-03
**Success Criteria** (what must be TRUE):
  1. An OWNER or MANAGER can create an event in DRAFT status and publish it; a published event appears in the public browse feed; a cancelled event does not
  2. The system automatically transitions an event from PUBLISHED to LIVE when the start time passes, and from LIVE to COMPLETED when the end time passes
  3. An org member can create ticket tiers with free, paid, and invite-only pricing; PUBLIC tiers appear on the public event page; HIDDEN and INVITE_ONLY tiers do not
  4. An OWNER or MANAGER can create a promo code with percentage or fixed discount, applicable tier targeting, and usage limits; the public validate endpoint correctly accepts and rejects codes
  5. Anyone can browse published events with search and category/format filters and view a public organization page with its upcoming events
**Plans**: TBD
**UI hint**: yes

### Phase 3: Checkout & Orders
**Goal**: Attendees can complete registration for free and paid events and receive confirmed tickets with QR data
**Depends on**: Phase 2
**Requirements**: CHKT-01, CHKT-02, CHKT-03, CHKT-04, CHKT-05, CHKT-06, CHKT-07, CHKT-08, CHKT-09, CHKT-10, CHKT-11, CHKT-12, ORDR-01, ORDR-02, ORDR-03, ORDR-04, ORDR-05, ORDR-06, ORDR-07
**Success Criteria** (what must be TRUE):
  1. An attendee registering for a free event receives an immediate order confirmation with a 10-character confirmation code and QR-encoded ticket data
  2. An attendee registering for a paid event is presented with a Stripe card form; on successful payment the order is confirmed with tickets
  3. Checkout correctly rejects orders that exceed tier capacity, violate min/max per order, target non-published events, or use expired or over-limit promo codes
  4. A logged-in user can list their orders and tickets; anyone can look up an order by confirmation code without authentication
  5. Each ticket carries an HMAC-SHA256 signed QR payload in the correct format; the signing key is independent of Django's SECRET_KEY
**Plans**: TBD
**UI hint**: yes

### Phase 4: QR Check-In
**Goal**: Organizers can check in attendees at the event door via QR scan or manual search, with live stats
**Depends on**: Phase 3
**Requirements**: CHKN-01, CHKN-02, CHKN-03, CHKN-04, CHKN-05, CHKN-06, MCHK-01, MCHK-02, STAT-01, STAT-02, STAT-03, SRCH-01, GUST-01, GUST-02, FEND-10
**Success Criteria** (what must be TRUE):
  1. Any org member can scan a QR code and receive a "success" response with attendee name, email, tier, and timestamp; scanning the same ticket again returns "already_checked_in"; a forged or cancelled ticket returns "invalid"
  2. Any org member can manually check in a ticket by ID with the same response format as QR scan
  3. Any org member can search for an attendee by name, email, or confirmation code and check them in from the search result
  4. The check-in dashboard shows total registered, checked-in, and remaining counts with per-tier breakdown, and auto-refreshes every 10 seconds
  5. An OWNER or MANAGER can view the full guest list and export it as a CSV file
**Plans**: TBD
**UI hint**: yes

### Phase 5: Email & Notifications
**Goal**: Attendees receive confirmation emails on registration; organizers can configure and send event emails
**Depends on**: Phase 3
**Requirements**: EMAL-01, EMAL-02, EMAL-03, EMAL-04
**Success Criteria** (what must be TRUE):
  1. An attendee receives a confirmation email immediately after order completion (free or paid)
  2. An OWNER or MANAGER can view and toggle email config for an event (confirmation, reminders, notifications)
  3. An OWNER or MANAGER can send a bulk email to all event attendees and view the resulting email log
**Plans**: TBD

### Phase 6: Analytics & Polish
**Goal**: Organizers can view event analytics and the full application is responsive and production-ready
**Depends on**: Phase 4, Phase 5
**Requirements**: ANLT-01, ANLT-02, ANLT-03, FEND-04, FEND-05, FEND-06, FEND-07, FEND-08, FEND-09
**Success Criteria** (what must be TRUE):
  1. An OWNER or MANAGER can view total registrations, revenue, fees, net revenue, and attendance rate for an event, along with per-tier and time-series breakdowns
  2. The checkout flow displays step indicators with the current step highlighted; billing info is pre-filled for logged-in users; the confirmation page shows the confirmation code prominently with QR codes for each ticket
  3. All pages render correctly at 375px (mobile), 768px (tablet), and 1280px+ (desktop) with no horizontal overflow and touch targets at least 44x44px on mobile
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 0/TBD | Not started | - |
| 2. Events | 0/TBD | Not started | - |
| 3. Checkout & Orders | 0/TBD | Not started | - |
| 4. QR Check-In | 0/TBD | Not started | - |
| 5. Email & Notifications | 0/TBD | Not started | - |
| 6. Analytics & Polish | 0/TBD | Not started | - |
