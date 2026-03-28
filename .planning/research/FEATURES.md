# Feature Research

**Domain:** Community event management platform (nonprofits, libraries, volunteer groups)
**Researched:** 2026-03-28
**Confidence:** HIGH (cross-verified against Eventbrite, Luma, Wild Apricot, Whova, and nonprofit-specific platforms)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete or untrustworthy.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| User registration and login | Every authenticated platform has this | LOW | JWT with email/password is sufficient for v1 — OAuth is additive |
| User profile management | Users expect to manage their own account | LOW | Name, email, password reset minimum |
| Event creation with full metadata | The core product action — must be complete | MEDIUM | Title, description, date, timezone, format, category, venue, capacity |
| Event lifecycle (draft → published → live → completed) | Organizers need staging before going public | MEDIUM | Cancel from any state is expected; soft deletes expected |
| Public event page with ticket tiers displayed | Attendees navigate directly to this | LOW | Must be readable without login |
| Public event browse / discovery | Users expect to find events if they don't have a direct link | MEDIUM | Search + category filters minimum |
| Free event registration (no payment) | Many community events are free; friction here kills conversion | LOW | Skip payment entirely — confirmation email + ticket |
| Paid ticketing with card payment (Stripe) | Commercial expectation for paid events | HIGH | PaymentIntent flow, card form, confirmation; Stripe is standard |
| Order confirmation with ticket / QR code | Attendees expect a ticket in email immediately after checkout | MEDIUM | HMAC-signed QR payload; confirmation code lookup |
| QR code check-in (mobile scan) | Door workflow expectation at any modern event | MEDIUM | Volunteer-friendly — must handle duplicate/invalid gracefully |
| Manual check-in fallback | Phones die, QR codes fail — organizers need backup | LOW | Search by name, email, or confirmation code |
| Attendee list with export | Post-event follow-up, compliance, accessibility requests | LOW | CSV export is the minimum expectation |
| Email confirmation to attendees | Attendees expect immediate confirmation | LOW | Triggered on order completion |
| Responsive / mobile-friendly UI | Most attendees register on phones | MEDIUM | 375px mobile minimum |
| Organization page with upcoming events | Community orgs run multiple events; a branded home is expected | MEDIUM | Public-facing, no login required |

### Differentiators (Competitive Advantage)

Features that set GatherGood apart for the nonprofit/community segment. Not universal, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Role-based team permissions (OWNER / MANAGER / VOLUNTEER) | Community orgs have volunteers at the door, not just staff — they need scoped access | MEDIUM | Three-tier model matches real org structure; competitors often only have admin vs. user |
| Promo codes with targeting (tier, date range, usage limit) | Nonprofits offer member discounts, early-bird pricing, sponsor comps | MEDIUM | Percentage and fixed discounts; tie to specific ticket tiers |
| Tiered ticketing with visibility controls (PUBLIC / HIDDEN / INVITE_ONLY) | Orgs need invite-only tiers for board members, donors, volunteers | MEDIUM | Standard on Eventbrite but poorly executed in many nonprofit tools |
| Check-in stats with live polling (per-tier breakdown) | Door coordinator needs real-time head count — especially for capacity-limited venues | MEDIUM | Total / checked-in / remaining; per-tier is unusual and high-value for multi-tier events |
| Ticket tier: invite-only type | Nonprofits regularly need comp tickets for donors, sponsors, staff | LOW | Distinct from promo codes — the ticket itself is invite-gated |
| Event reminder emails with bulk send | Most nonprofit platforms lack built-in email — organizers resort to Mailchimp | MEDIUM | Per-event email settings; confirmation + reminder + bulk send |
| Email log per event | Organizers need audit trail of what was sent to whom | LOW | Common complaint about competitor platforms lacking this |
| Event analytics (registrations, revenue, attendance rate, time series) | Org leadership needs data for grant reporting and board updates | MEDIUM | Attendance rate as a metric is specifically relevant to nonprofits |
| Slug-based public URLs (org and event) | Clean, shareable URLs for social media and newsletters | LOW | Auto-generation with dedup suffix — professional appearance matters to community orgs |
| Venue management per organization | Orgs reuse their own venues (libraries, community centers) — must not re-enter every time | LOW | Simple CRUD; reuse across events |
| Checkout validation (capacity, min/max per order, promo rules) | Prevents overselling and abuse — critical for limited-capacity community events | MEDIUM | Real-time enforcement at checkout |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create disproportionate complexity or shift product focus.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Real-time attendee chat / messaging | "Make it social" — communities want conversation | High infrastructure complexity (WebSockets), moderation burden, unrelated to core ticketing value | Email blast to attendees covers the primary communication need |
| Video / livestream integration | Virtual or hybrid events are common | Storage costs, CDN complexity, encoding pipelines — a separate product concern | Link to Zoom/YouTube in event description |
| OAuth login (Google, GitHub, social) | Reduces registration friction | Auth complexity doubles; social login has different token lifecycle; email/password already works | Password reset flow covers the friction problem adequately |
| Native mobile app | Volunteers want an app for check-in | Separate codebase, App Store approval delays, fragmented maintenance | Mobile-responsive web app + PWA is sufficient for check-in workflow |
| Seating chart / seat selection | Premium events have assigned seating | Complex UI (drag-and-drop canvas), significant backend modeling, niche for community orgs | Capacity limit with ticket tiers covers most community event needs |
| Multi-currency / international payments | Feels like global readiness | Stripe multi-currency adds complexity; community orgs are local by definition | USD-only for v1; Stripe makes adding currencies later straightforward |
| Donation processing (on top of ticketing) | Nonprofits want to fundraise | Overlaps with dedicated fundraising tools (RallyUp, Bloomerang); different regulatory/tax surface area | Ticket price can include a "donation" component; defer integrated donations to v2 |
| CRM integration (Salesforce, HubSpot) | Org admins want data in their CRM | Integration maintenance is ongoing; v1 has no integration API | CSV export covers the data portability need for v1 |
| Dynamic / demand-based pricing | Maximizes revenue | Anti-aligned with nonprofit mission; community members distrust surge pricing | Early-bird tiers and time-limited promo codes achieve similar outcomes without the optics problem |
| Multi-language / i18n | Serves diverse communities | Doubles content maintenance; translation quality inconsistency | English-first; localization is a v2 concern once product-market fit is established |

---

## Feature Dependencies

```
[Auth / User Accounts]
    └──required by──> [Organization Management]
                          └──required by──> [Venue Management]
                          └──required by──> [Team Permissions]
                          └──required by──> [Event Creation]
                                                └──required by──> [Ticket Tiers]
                                                                      └──required by──> [Promo Codes]
                                                                      └──required by──> [Checkout Flow]
                                                                                            └──required by──> [Orders + Tickets]
                                                                                            └──required by──> [QR Code Generation]
                                                                                                                  └──required by──> [QR Check-in]
                                                                                                                  └──required by──> [Check-in Stats]

[Event Creation]
    └──required by──> [Public Event Page]
    └──required by──> [Event Analytics]
    └──required by──> [Email Settings / Reminders]

[Checkout Flow: Free]
    └──skips──> [Stripe PaymentIntent]
    └──directly produces──> [Order + Ticket]

[Checkout Flow: Paid]
    └──requires──> [Stripe PaymentIntent]
    └──produces──> [Order + Ticket]

[Team Permissions]
    └──scopes──> [Event Creation] (OWNER / MANAGER)
    └──scopes──> [Check-in] (VOLUNTEER and above)
    └──scopes──> [Analytics] (OWNER / MANAGER)
```

### Dependency Notes

- **Auth is the foundation of everything:** No user accounts = no org, no events, no tickets. Must be phase 1.
- **Organization must precede events:** Events belong to orgs; org must exist first.
- **Ticket tiers must exist before checkout:** You cannot sell something that has no price definition.
- **QR generation requires completed orders:** The ticket payload is generated at order time; check-in requires a token to scan.
- **Promo codes require ticket tiers to target:** The tier association is part of the promo code model.
- **Check-in stats enhance check-in:** Stats are additive — check-in works without them, but live polling makes it valuable for real events.
- **Email settings enhance orders:** Confirmation email is close-coupled to order completion; reminders/bulk send are additive.
- **Free and paid checkout conflict in implementation approach:** Free events must bypass Stripe entirely — this is a deliberate branch in checkout logic, not a fallback.

---

## MVP Definition

### Launch With (v1)

Minimum viable product — the end-to-end happy path must work flawlessly.

- [x] Auth (register, login, token refresh, password reset) — nothing else works without this
- [x] Organization CRUD with owner role — events belong to orgs
- [x] Event creation with full metadata and lifecycle management — the core action
- [x] Venue management — reusable across events, part of event creation
- [x] Ticket tier management (free, paid, invite-only) — prerequisite for checkout
- [x] Promo code management — high-value for community orgs; relatively low complexity
- [x] Checkout flow — free events (immediate) and paid events (Stripe PaymentIntent) — core value delivery
- [x] Order and ticket management — attendees need to retrieve their tickets
- [x] QR code generation on tickets — required for check-in
- [x] QR check-in with duplicate/invalid state handling — the door experience
- [x] Manual check-in fallback — operations safety net
- [x] Check-in stats (live polling, per-tier breakdown) — real-time door management
- [x] Guest list with CSV export — post-event utility
- [x] Email confirmation on order — attendee expectation
- [x] Public event browse + search + category filters — discovery
- [x] Public org page with upcoming events — org branding
- [x] Public event detail page with ticket tiers — conversion page
- [x] Team permissions (OWNER / MANAGER / VOLUNTEER) — volunteer check-in without full admin access
- [x] Responsive design (375px / 768px / 1280px+) — most registrations happen on mobile

### Add After Validation (v1.x)

Features to add once core flow is working and user feedback confirms direction.

- [ ] Event reminder emails + bulk send — high value, but confirmation is the must-have; reminders are additive
- [ ] Email log per event — audit trail; useful but not blocking launch
- [ ] Event analytics (time series, revenue, attendance rate) — needed for org reporting; can launch with basic counts first
- [ ] Invite-only ticket type workflow — edge case at launch; most orgs start with free/paid

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] OAuth / social login — friction reduction, not blocking; email/password works
- [ ] Donation processing integration — different product surface, different compliance
- [ ] CRM / Zapier integration — integration API needs stable v1 contract first
- [ ] Waitlist management — complex state machine; low priority for community events
- [ ] Recurring events — calendar complexity; can be solved with duplicate-event workflow for v1
- [ ] Multi-org event co-hosting — niche requirement; complex permission model
- [ ] Native mobile app / PWA — responsive web covers check-in; defer native to proven demand

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Auth (JWT, register, login, reset) | HIGH | LOW | P1 |
| Organization CRUD | HIGH | LOW | P1 |
| Event creation + lifecycle | HIGH | MEDIUM | P1 |
| Ticket tier management | HIGH | MEDIUM | P1 |
| Checkout (free + Stripe paid) | HIGH | HIGH | P1 |
| QR code generation + check-in | HIGH | MEDIUM | P1 |
| Public event page + browse | HIGH | MEDIUM | P1 |
| Team permissions (3-tier) | HIGH | MEDIUM | P1 |
| Responsive design | HIGH | MEDIUM | P1 |
| Promo codes | MEDIUM | MEDIUM | P1 |
| Venue management | MEDIUM | LOW | P1 |
| Manual check-in fallback | HIGH | LOW | P1 |
| Check-in stats (live) | MEDIUM | MEDIUM | P1 |
| Email confirmation | HIGH | LOW | P1 |
| Guest list + CSV export | MEDIUM | LOW | P1 |
| Event analytics | MEDIUM | MEDIUM | P2 |
| Reminder emails + bulk send | MEDIUM | MEDIUM | P2 |
| Email log | LOW | LOW | P2 |
| Invite-only ticket type | LOW | LOW | P2 |
| OAuth login | LOW | MEDIUM | P3 |
| Donation processing | MEDIUM | HIGH | P3 |
| CRM integrations | LOW | HIGH | P3 |
| Seating charts | LOW | HIGH | P3 |
| Native mobile app | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

| Feature | Eventbrite | Luma | Wild Apricot | GatherGood Approach |
|---------|------------|------|--------------|---------------------|
| Free event registration | Yes | Yes | Yes | Yes — skip payment entirely |
| Paid ticketing (Stripe) | Yes (own processor) | Yes | Yes | Yes — standard PaymentIntent flow |
| Ticket tiers | Yes | Limited | Yes | Yes — with visibility controls (PUBLIC/HIDDEN/INVITE_ONLY) |
| Promo codes | Yes (Pro plan) | No | Yes | Yes — for all orgs, not paywalled |
| QR check-in | Yes (mobile app) | Yes | Limited | Yes — mobile web, no app required |
| Team / volunteer roles | Limited | No | Yes | Yes — OWNER / MANAGER / VOLUNTEER three-tier |
| Organization page | Yes | Yes (calendar) | Yes | Yes — with upcoming events |
| Email reminders | Yes | Yes | Yes | Yes — per-event settings with log |
| Analytics / reporting | Yes (Pro) | Basic | Yes | Yes — attendance rate, revenue, time series |
| Nonprofit pricing | Yes (discount) | Free | Yes (nonprofit plan) | Designed for this segment from the start |
| Native mobile app | Yes | Yes | No | No (v1) — responsive web sufficient |
| Donation processing | No | No | Yes | No (v1) — out of scope |
| Social / community features | Limited | Yes (chat, calendar) | Yes (membership) | No — focused on event management |

---

## Sources

- [Eventbrite features and pricing](https://www.eventbrite.com/organizer/pricing/) — HIGH confidence (official)
- [Whova: 14 Best Eventbrite Alternatives 2026](https://whova.com/blog/eventbrite-alternatives-competitors/) — MEDIUM confidence
- [Bloomerang: 20+ Event Management Tools for Nonprofits](https://bloomerang.com/blog/event-management-software-for-nonprofits/) — MEDIUM confidence
- [RallyUp: Best Fundraising Event Management for Nonprofits 2026](https://rallyup.com/blog/event-management-software/) — MEDIUM confidence
- [NeonOne: 26 Best Event Management Tools for Nonprofits](https://neonone.com/resources/blog/event-management-software-nonprofits/) — MEDIUM confidence
- [Luma pricing and features](https://luma.com/pricing) — MEDIUM confidence (official)
- [Zoho Backstage: Event Ticketing Industry Trends 2026](https://www.zoho.com/backstage/event-ticketing-software/industry-trends.html) — MEDIUM confidence
- [Nutickets: 8 Essential Features for Event Ticketing Software](https://www.nutickets.com/blog/ticketing/event-ticketing-software-features) — MEDIUM confidence
- [G2: Eventbrite Reviews 2026](https://www.g2.com/products/eventbrite/reviews) — MEDIUM confidence (user reviews)
- [vFairs: Eventbrite Review](https://www.vfairs.com/blog/eventbrite-review/) — LOW confidence (analyst)

---

*Feature research for: Community event management platform (GatherGood)*
*Researched: 2026-03-28*
