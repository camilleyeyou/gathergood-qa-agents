# GatherGood

## What This Is

GatherGood is an event management platform for community organizations — nonprofits, libraries, volunteer groups — to create events, sell or RSVP tickets, manage attendees, and check in guests with QR codes. It covers the full lifecycle from organization setup through post-event analytics.

## Core Value

Community organizers can create an event, publish it, and have people register (free or paid) with working tickets and QR check-in — the end-to-end happy path must work flawlessly.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] JWT authentication with register, login, token refresh, password reset
- [ ] User profile management (view, edit)
- [ ] Organization CRUD with role-based access (OWNER, MANAGER, VOLUNTEER)
- [ ] Team management — invite members, assign roles, remove members
- [ ] Venue management per organization
- [ ] Event creation with full metadata (format, category, dates, timezone, venue, tags)
- [ ] Event lifecycle management (DRAFT → PUBLISHED → LIVE → COMPLETED, cancel from any state)
- [ ] Ticket tier management (free, paid, invite-only; PUBLIC/HIDDEN/INVITE_ONLY visibility)
- [ ] Promo code management (percentage and fixed discounts, usage limits, date ranges, tier targeting)
- [ ] Checkout flow — free events skip payment, complete immediately
- [ ] Checkout flow — paid events via Stripe (PaymentIntent, card form, confirmation)
- [ ] Checkout validation (capacity, min/max per order, promo rules, event status)
- [ ] Order and ticket management (list orders, lookup by confirmation code, list tickets)
- [ ] QR code generation on tickets with HMAC-signed payloads
- [ ] QR code check-in with scan (success/duplicate/invalid states)
- [ ] Manual check-in fallback
- [ ] Check-in stats with live polling (total/checked-in/remaining, per-tier breakdown)
- [ ] Check-in search by name, email, or confirmation code
- [ ] Guest list with CSV export
- [ ] Event analytics (registrations, revenue, attendance rate, time series)
- [ ] Email settings per event (confirmation, reminders, bulk send, email log)
- [ ] Public event browse with search and category/format filters
- [ ] Public organization page with upcoming events
- [ ] Public event detail page with ticket tiers
- [ ] Responsive design (mobile 375px, tablet 768px, desktop 1280px+)
- [ ] Homepage with auth-aware content (hero, feature cards, footer)

### Out of Scope

- Real-time chat — high complexity, not core to event management
- Video/livestream integration — storage/bandwidth costs, defer to future
- OAuth login (Google, GitHub) — email/password sufficient for v1
- Native mobile app — web-first, mobile later
- Multi-language / i18n — English only for v1
- Payment methods beyond cards — Stripe card payments only for v1

## Context

- **Test spec provided:** Comprehensive TEST_SPEC.md covers every endpoint, request/response format, permission matrix, and UI checklist — use as the source of truth for API contracts
- **Stack:** Django REST Framework backend, Next.js frontend, PostgreSQL 16, Stripe for payments
- **Deployment:** Frontend on Vercel, backend + database on Railway
- **Auth:** JWT via djangorestframework-simplejwt (30min access, 7-day refresh, rotation enabled)
- **Existing references:**
  - Live frontend: https://event-management-two-red.vercel.app/
  - Live API: https://event-management-production-ad62.up.railway.app/api/v1
  - Source repo: https://github.com/camilleyeyou/Event-Management
- **Slug auto-generation:** Organization and event names auto-generate URL slugs with dedup suffixes
- **Soft deletes:** System uses status flags, nothing is hard-deleted
- **QR security:** HMAC-SHA256 signed with Django SECRET_KEY, first 16 hex chars

## Constraints

- **Tech stack**: Django REST Framework + Next.js + PostgreSQL + Stripe — per spec requirements
- **Deployment**: Vercel (frontend) + Railway (backend + DB) — target platforms
- **API contract**: Must match TEST_SPEC.md endpoint signatures, request/response shapes, and status codes exactly
- **Permission model**: Three-tier roles (OWNER > MANAGER > VOLUNTEER) with specific permission boundaries per the spec

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Django + Next.js stack | Matches existing spec and deployment targets | — Pending |
| JWT with refresh rotation | Spec requires 30min access / 7-day refresh with rotation | — Pending |
| Stripe PaymentIntent flow | Spec defines client_secret based payment flow | — Pending |
| HMAC-signed QR codes | Security requirement from spec — prevents forgery | — Pending |
| Soft deletes everywhere | Spec states nothing is hard-deleted, uses status flags | — Pending |

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
*Last updated: 2026-03-28 after initialization*
