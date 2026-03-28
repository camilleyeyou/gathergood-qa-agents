# Project Research Summary

**Project:** GatherGood — Community Event Management Platform
**Domain:** Event ticketing and management for nonprofits, libraries, and volunteer organizations
**Researched:** 2026-03-28
**Confidence:** HIGH

## Executive Summary

GatherGood is a full-stack event management platform targeting community organizations: nonprofits, libraries, and volunteer groups. The architecture follows a well-established SaaS pattern — Django REST Framework on Railway for the API backend, Next.js on Vercel for the frontend, and PostgreSQL 16 as the primary datastore. This stack has excellent documented precedent for this class of application, verified version compatibility as of March 2026, and maps directly to the three-tier permission model (OWNER / MANAGER / VOLUNTEER) that differentiates GatherGood from general-purpose event tools. The build order is dictated by hard data dependencies: Auth, then Organizations, then Events, then Orders and Checkout, then QR Check-in, then Analytics and Email.

The recommended approach is to implement the full end-to-end happy path for free and paid event registration before expanding to analytics, reminder emails, or advanced invite-only flows. Research confirms this is the correct prioritization for community-focused event tools — the core conversion loop (discover event, register, receive QR ticket, check in at door) must work flawlessly before any adjacent features add value. Promo codes and team permissions are included in v1 because they are differentiating features for this segment and have relatively low implementation cost compared to their value. Event analytics, reminder emails, and email logs are high-value but additive — they belong in v1.x once the core loop is validated.

The two most critical risk areas are payment integrity and concurrency correctness. Ticket overselling via race condition and promo code bypass via concurrent usage are both well-documented failure modes in ticketing systems (one of them is a documented CVE in alf.io). Both must be addressed from day one using PostgreSQL row-level locking (`SELECT FOR UPDATE` inside `transaction.atomic()`). The Stripe integration has three distinct pitfalls — raw body destruction for webhook signature verification, duplicate order creation from webhook replay, and premature order confirmation — all of which require specific implementation choices that must be made during the checkout phase, not retrofitted. JWT token storage in memory (not localStorage) and object-level DRF permission checks are foundational security requirements that must be established in Phase 1 before any other endpoint is built.

## Key Findings

### Recommended Stack

The backend uses Django 5.2 LTS (supported through April 2028) with Django REST Framework 3.17.1, deployed to Railway via Gunicorn. djangorestframework-simplejwt 5.5.1 handles JWT auth with mandatory `ROTATE_REFRESH_TOKENS = True` and `BLACKLIST_AFTER_ROTATION = True`. Celery 5.6.3 with Redis handles async email and slow operations (QR generation for large orders, CSV export). The frontend uses Next.js 16.2.1 with React 19.2 and the App Router, deployed to Vercel. TanStack Query handles all server state; Zustand handles auth tokens and cart state client-side. Stripe Python SDK 15.0.0 (March 2026 major release — review changelog before pinning) pairs with @stripe/react-stripe-js 6.0.0 on the frontend.

**Core technologies:**
- Django 5.2 LTS: Backend framework — LTS window matches project lifetime; avoids Django 6.0.x's short mainstream support ending August 2026
- djangorestframework-simplejwt: JWT auth — maps directly to spec's 30-min access / 7-day refresh with rotation
- PostgreSQL 16: Primary datastore — native JSON, full-text search, and LISTEN/NOTIFY; already decided
- Next.js 16 (App Router): Frontend — Server Components for public SEO pages; client components for interactive checkout and check-in
- Celery + Redis: Async tasks — email confirmation, reminders, bulk send; prevents webhook timeout on Railway
- Stripe Python 15 + @stripe/react-stripe-js 6: Payments — PaymentIntent client-confirmed flow; card data never touches servers

**Critical version notes:**
- Stripe 15.0.0 is a March 2026 major release — verify changelog before pinning
- Zod 4.x requires `@hookform/resolvers` >=3.x
- Tailwind v4 uses zero-config install; some Shadcn components may need updates

### Expected Features

Research cross-validated against Eventbrite, Luma, Wild Apricot, Whova, and nonprofit-specific platforms. The feature dependency graph is strict: Auth → Orgs → Events → Ticket Tiers → Checkout → Orders → QR Generation → Check-in.

**Must have (table stakes):**
- Auth (register, login, JWT refresh, password reset) — nothing else works without this
- Organization CRUD with owner role — events belong to orgs
- Event creation with full metadata and lifecycle (draft → published → live → completed → cancelled)
- Ticket tier management (free, paid, invite-only) with visibility controls (PUBLIC / HIDDEN / INVITE_ONLY)
- Checkout flow — free (immediate) and paid (Stripe PaymentIntent)
- QR code generation on tickets with HMAC-SHA256 signing
- QR check-in with distinct states (success / duplicate / invalid / wrong event)
- Manual check-in fallback — search by name, email, or confirmation code
- Public event browse with search and category filters
- Public event detail page and organization page — readable without login
- Email confirmation on order completion
- Guest list with CSV export
- Responsive design (375px / 768px / 1280px+)
- Team permissions: OWNER / MANAGER / VOLUNTEER with scoped access
- Promo codes with percentage and fixed discounts, per-tier targeting, usage limits

**Should have (competitive differentiators):**
- Live check-in stats with per-tier breakdown and polling (5s interval via TanStack Query)
- Event analytics: registrations, revenue, attendance rate, time series
- Reminder emails + bulk send per-event settings
- Email log per event (audit trail)
- Venue management per organization (reusable across events)
- Slug-based clean URLs for orgs and events

**Defer (v2+):**
- OAuth / social login — email/password sufficient for v1
- Donation processing — different compliance surface
- CRM / Zapier integrations — needs stable v1 API contract first
- Waitlist management — complex state machine
- Recurring events — duplicate-event workflow covers v1
- Native mobile app / PWA — responsive web covers check-in

### Architecture Approach

The system separates into three deployment targets: Next.js (Vercel) for the frontend, Django + Gunicorn (Railway) for the API, and PostgreSQL 16 + Redis (Railway) for data. Django is organized into focused apps: accounts, organizations, events, orders, checkin, analytics, and notifications. Each app owns its models, serializers, views, services, and tests. Business logic lives exclusively in `services.py` — views are thin HTTP adapters. Cross-cutting concerns (HMAC helpers, slug generation, base permission primitives) live in `common/`. The frontend uses Next.js App Router route groups: `(public)` for SSR event browse and org pages (SEO-critical), `(auth)` for login/register, and `dashboard/` for the authenticated organizer area. All API calls route through typed wrappers in `lib/api/`.

**Major components:**
1. Auth app (Django) — user registration, JWT issue/refresh/blacklist, password reset; foundation for all permission checks
2. Organizations app (Django) — org CRUD, OrganizationMember roles, venue management; owns the OWNER/MANAGER/VOLUNTEER model
3. Events app (Django) — event lifecycle, ticket tiers with visibility, promo codes with locking
4. Orders/Checkin apps (Django) — checkout (free and paid), HMAC-signed QR generation, scan validation with duplicate detection
5. Analytics + Notifications apps (Django) — read-only aggregations, email confirmation/reminder/log
6. Next.js frontend — SSR public pages, authenticated dashboard, mobile-responsive check-in UI

**Key patterns:**
- Service layer: all side-effect logic in `services.py`; views are HTTP adapters only
- PaymentIntent client-confirmed: backend creates intent, frontend confirms with Stripe.js, webhook finalizes order
- HMAC-signed QR: dedicated `QR_SIGNING_KEY` env var (not SECRET_KEY); full signature verification on every scan
- Polling for live stats: TanStack Query `refetchInterval: 5000`; upgrade to SSE only if poll load becomes a problem at scale

### Critical Pitfalls

1. **Ticket overselling via race condition** — Use `select_for_update()` on TicketTier inside `transaction.atomic()` during checkout. No concurrent tests = invisible in development. Must be implemented from day one.

2. **Promo code bypass via concurrent usage** — Same fix as above: lock the promo code row within the same atomic block as order creation. Documented as a real CVE (alf.io GHSA-67jg-m6f3-473g). Per-user unique constraint adds an additional layer.

3. **Stripe webhook raw body destruction** — Access `request.body` directly in the webhook view. DRF parsers and logging middleware that read the body first will break `stripe.Webhook.construct_event()` signature verification. Test with Stripe CLI before any other payment logic.

4. **Duplicate orders from webhook replay** — Store processed Stripe event IDs in a unique DB table. Check before processing. Return `200 OK` immediately on duplicate. Stripe retries for 3 days — a Railway restart will trigger retries.

5. **DRF object-level permission omission** — `has_object_permission()` is not called automatically; must explicitly call `self.check_object_permissions(request, obj)`. A MANAGER from Org B can access Org A's data without this. Establish the pattern in Phase 1; every subsequent phase inherits it.

6. **JWT in localStorage** — Store access tokens in memory (React state/module variable) and refresh tokens in `HttpOnly, Secure, SameSite=Strict` cookies. Any XSS vector on the site will exfiltrate localStorage tokens.

7. **QR signing key tied to SECRET_KEY** — Use a dedicated `QR_SIGNING_KEY` env var. Rotating `SECRET_KEY` (for any security reason) immediately invalidates all outstanding QR codes.

## Implications for Roadmap

Based on the dependency graph from FEATURES.md and the build order from ARCHITECTURE.md, the following phase structure is recommended. Phases follow hard data dependencies and group related pitfall-prevention work together.

### Phase 1: Foundation — Auth, Organizations, and Core Permissions

**Rationale:** Nothing else is buildable without users, orgs, and a correct permission model. DRF object-level permissions and JWT token security are established here and inherited by every subsequent phase. Getting this wrong requires fixing every downstream endpoint.
**Delivers:** User registration, login, JWT with rotation and blacklist, password reset; Organization CRUD with owner bootstrapping; OWNER/MANAGER/VOLUNTEER role model; object-level permission pattern; venue management (low complexity, belongs here as an org resource)
**Addresses:** Auth, Organization CRUD, Venue Management, Team Permissions (all P1 features)
**Avoids:** JWT in localStorage (must use HttpOnly cookies from day one); DRF object-level permission omission (establish `has_object_permission()` pattern here)
**Research flag:** Standard patterns — JWT + DRF permissions are well-documented; skip research-phase

### Phase 2: Event Management

**Rationale:** Events are the core entity that all downstream features (checkout, check-in, analytics) depend on. The event model schema must include the `timezone` field from the start — retrofit is painful. Event lifecycle and ticket tier visibility controls belong here because they inform checkout logic.
**Delivers:** Event CRUD with full metadata, lifecycle state machine (draft → published → live → completed → cancel), ticket tier management (free/paid/invite-only) with PUBLIC/HIDDEN/INVITE_ONLY visibility, promo code management, slug-based URLs with dedup, public event page and public org page (SSR), public event browse with search and category filters
**Addresses:** Event creation + lifecycle, Ticket tier management, Promo codes, Public event page + browse, Public org page (all P1 features)
**Avoids:** Timezone stored without named IANA field (schema decision made here); INVITE_ONLY tier enforced backend-only (not frontend-only)
**Research flag:** Standard patterns for event lifecycle and slug generation; skip research-phase

### Phase 3: Checkout and Orders

**Rationale:** Checkout is the highest-complexity phase and the biggest source of correctness pitfalls. Build free checkout first to validate the order creation pipeline before adding Stripe. Both concurrent-access pitfalls (overselling and promo bypass) must be addressed in this phase. Stripe webhook idempotency must be implemented before any real payment processing.
**Delivers:** Free event checkout (immediate order confirmation), paid event checkout (Stripe PaymentIntent client-confirmed flow), order and ticket creation, capacity enforcement with `select_for_update()`, promo code validation with row-level lock, Stripe webhook handler with signature verification and idempotency table, confirmation code generation, checkout session timeout to prevent capacity hoarding
**Addresses:** Checkout flow (free + Stripe paid), Orders and ticket management (all P1 features)
**Avoids:** Ticket overselling race condition; promo code bypass; Stripe raw body destruction; duplicate orders from webhook replay; premature order confirmation on PaymentIntent creation
**Research flag:** Needs attention — Stripe 15.0.0 is a March 2026 major release; verify API changes before implementation. Consider a targeted research-phase on the Stripe changelog.

### Phase 4: QR Generation and Check-in

**Rationale:** QR check-in depends on real Order and Ticket records from Phase 3. HMAC signing key separation from SECRET_KEY must be established at implementation time. Check-in stats polling is additive and included here as the primary value-add for real events.
**Delivers:** HMAC-signed QR code generation per ticket (dedicated `QR_SIGNING_KEY`), QR check-in endpoint with full signature re-validation on every scan, distinct scan states (success/duplicate/invalid/wrong-event), manual check-in fallback (name/email/confirmation code search), live check-in stats with per-tier breakdown (TanStack Query polling at 5s), guest list with CSV export (OWNER/MANAGER only)
**Addresses:** QR code generation, QR check-in, Manual check-in fallback, Check-in stats, Guest list + CSV export (all P1 features)
**Avoids:** QR signing tied to SECRET_KEY; storing QR payload without server-side re-validation on scan; CSV export accessible to VOLUNTEER role
**Research flag:** Standard patterns for HMAC and QR; skip research-phase

### Phase 5: Email and Notifications

**Rationale:** Email confirmation is close-coupled to order completion but involves Celery task infrastructure that benefits from being established after the checkout flow is stable. Reminder emails and bulk send are v1.x features that build on the same infrastructure once confirmation is validated.
**Delivers:** Async email confirmation triggered on order completion (Celery + Redis), email log per event (audit trail), event reminder emails with configurable send settings, bulk send to attendees, resend confirmation self-serve on order detail page
**Addresses:** Email confirmation (P1), Email log, Reminder emails + bulk send (P2 features)
**Avoids:** Synchronous email in webhook handler (causes Stripe retry); duplicate confirmation emails on webhook replay (requires idempotency, tied back to Phase 3's event ID table)
**Research flag:** Standard Celery + Django email patterns; skip research-phase

### Phase 6: Analytics and Dashboard Polish

**Rationale:** Analytics is purely read-only and depends on the write paths from Phases 3 and 4 being stable. Event analytics (registration counts, revenue, attendance rate, time series) are high-value for nonprofit grant reporting but do not block the core flow. Dashboard polish (responsive design verification, UX edge cases) is included here as a final integration pass.
**Delivers:** Event analytics views (registrations, revenue, attendance rate, time-series charts), per-tier registration breakdown, responsive design verification (375px / 768px / 1280px+), UX edge cases (status badges on public event pages, order summary before card form mounts, event status communication)
**Addresses:** Event analytics, Responsive design (P1 feature), UX polish items from PITFALLS.md
**Avoids:** N+1 queries on attendee lists (use `select_related`); unindexed lookups (add DB indexes on confirmation_code and (event_id, status)); check-in poll degradation under concurrent scanners
**Research flag:** Standard Django ORM aggregation patterns; skip research-phase. Consider performance testing of check-in stats polling under concurrent load before marking complete.

### Phase Ordering Rationale

- Auth must exist before any permission-protected endpoint is built — this is a hard dependency
- Organizations own Events; Events own Ticket Tiers; Ticket Tiers are required before any Checkout can be built — strict sequential dependency
- Free checkout must be validated before Stripe is added — isolates payment complexity and makes debugging easier
- QR check-in requires real Order/Ticket rows — cannot be meaningfully tested in isolation
- Celery email infrastructure benefits from being solidified after checkout is stable (avoids changing the task invocation contract mid-development)
- Analytics is pure read — adding it after write paths stabilize means queries will return real data from day one
- Pitfall prevention is front-loaded: the three "never acceptable" shortcuts (no `select_for_update`, no webhook idempotency, JWT in localStorage) are addressed in Phases 1 and 3, before they can compound into downstream problems

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (Checkout/Stripe):** Stripe Python SDK 15.0.0 is a March 2026 major release. Verify API surface changes (PaymentIntent, webhook event types, SDK method signatures) against the changelog before implementation begins. One targeted research-phase is recommended.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Auth + Orgs):** JWT with simplejwt and DRF permissions are extensively documented with stable patterns
- **Phase 2 (Events):** Event CRUD, lifecycle state machines, and slug generation are well-understood Django patterns
- **Phase 4 (QR Check-in):** HMAC signing with Python stdlib `hmac`, QR generation with `qrcode` library — straightforward
- **Phase 5 (Email/Notifications):** Celery + Django email backend patterns are well-documented; Railway Redis add-on has templates
- **Phase 6 (Analytics):** Django ORM aggregations and TanStack Query polling are standard; no novel integrations

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All package versions verified against PyPI and npm as of March 2026. One caveat: Stripe 15.0.0 and Next.js 16.2.1 are very recent — verify changelogs before pinning |
| Features | HIGH | Cross-validated against 5+ competitor platforms (Eventbrite, Luma, Wild Apricot, Whova, Bloomerang). Feature dependency graph is internally consistent |
| Architecture | HIGH | Official Next.js App Router docs, DRF official docs, Stripe official webhook docs. Patterns are established and well-tested in production systems |
| Pitfalls | HIGH | Critical pitfalls backed by official docs, documented CVEs, and community post-mortems. Prevention strategies are concrete and verifiable |

**Overall confidence:** HIGH

### Gaps to Address

- **Stripe 15.0.0 API changes:** This is a major version release in March 2026 (same month as this research). The Python SDK changelog must be reviewed before Phase 3 implementation. Specifically: PaymentIntent creation parameters, webhook event payload shape, and any deprecated methods.
- **Railway connection limits:** Railway's PostgreSQL starter plan has low connection limits. For concurrent checkout load, PgBouncer or pgpool may be needed earlier than the "1k-10k users" threshold suggests. Validate actual connection limit on the chosen Railway plan during Phase 3 setup.
- **Tailwind v4 + third-party components:** Tailwind v4 zero-config install is recommended, but some Shadcn/UI components may need updates. If using a component library, verify v4 compatibility before committing to it in Phase 1 frontend setup.
- **HMAC truncation security trade-off:** The QR signing uses first 16 hex chars of SHA256 (64-bit). This is acknowledged as a deliberate trade-off in PITFALLS.md. If forgery risk increases post-launch, plan a migration to full SHA256 hex with a versioned payload schema.
- **Email provider selection:** SMTP provider for production is not specified. Postmark, SendGrid, and AWS SES are all viable. This decision affects deliverability and is needed before Phase 5.

## Sources

### Primary (HIGH confidence)
- PyPI package registry — all backend package versions verified (Django, DRF, simplejwt, Stripe, Celery, Pillow, qrcode, gunicorn, whitenoise, psycopg2-binary, pytest-django, factory-boy)
- npm registry — all frontend package versions verified (@stripe/react-stripe-js, @tanstack/react-query, zustand, react-hook-form, zod)
- [Next.js 16 official blog](https://nextjs.org/blog/next-16) — React Compiler stable, Turbopack default, React 19.2 confirmed
- [Next.js App Router Project Structure — Official Docs](https://nextjs.org/docs/app/getting-started/project-structure)
- [Django download page](https://www.djangoproject.com/download/) — 5.2 LTS vs 6.0.x support window guidance
- [Stripe Webhooks — Official Documentation](https://docs.stripe.com/webhooks)
- [Stripe Idempotent Requests — Stripe API Reference](https://docs.stripe.com/api/idempotent_requests)
- [Django REST Framework Permissions — Official Docs](https://www.django-rest-framework.org/api-guide/permissions/)
- [djangorestframework-simplejwt Settings — Official Docs](https://django-rest-framework-simplejwt.readthedocs.io/en/stable/settings.html)
- [tailwindcss v4 blog](https://tailwindcss.com/blog/tailwindcss-v4)
- [Railway Django + Celery + Redis template](https://railway.com/deploy/NBR_V3)
- [Promo code race condition CVE — alf.io GHSA-67jg-m6f3-473g](https://github.com/alfio-event/alf.io/security/advisories/GHSA-67jg-m6f3-473g)

### Secondary (MEDIUM confidence)
- [Whova: 14 Best Eventbrite Alternatives 2026](https://whova.com/blog/eventbrite-alternatives-competitors/) — competitor feature comparison
- [Bloomerang: 20+ Event Management Tools for Nonprofits](https://bloomerang.com/blog/event-management-software-for-nonprofits/) — nonprofit segment feature expectations
- [NeonOne: 26 Best Event Management Tools for Nonprofits](https://neonone.com/resources/blog/event-management-software-nonprofits/) — nonprofit segment feature expectations
- [Next.js 16.2 announcement](https://medium.com/@onix_react/release-next-js-16-2-377798369d25) — 16.2.1 version confirmation (not official blog)
- [Next.js + Django SaaS Architecture Guide 2025](https://techarion.com/blog/building-saas-application-nextjs-django-rest-framework) — architecture pattern validation
- [Django Stripe Tutorial — TestDriven.io](https://testdriven.io/blog/django-stripe-tutorial/) — PaymentIntent implementation pattern
- [SELECT FOR UPDATE in Django — DEV Community](https://dev.to/alairjt/guarding-critical-operations-mastering-select-for-update-for-race-condition-prevention-in-django--32mg) — race condition prevention
- [PostgreSQL Row-Level Locks complete guide](https://scalablearchitect.com/postgresql-row-level-locks-a-complete-guide-to-for-update-for-share-skip-locked-and-nowait/) — locking semantics
- [Next.js HTTP-Only Cookies for Secure Authentication](https://maxschmitt.me/posts/next-js-http-only-cookie-auth-tokens) — JWT storage pattern
- [Stripe Webhooks Best Practices — Stigg Engineering Blog](https://www.stigg.io/blog-posts/best-practices-i-wish-we-knew-when-integrating-stripe-webhooks) — webhook implementation pitfalls

### Tertiary (LOW confidence)
- [G2: Eventbrite Reviews 2026](https://www.g2.com/products/eventbrite/reviews) — user sentiment on competitor gaps
- [vFairs: Eventbrite Review](https://www.vfairs.com/blog/eventbrite-review/) — analyst competitor analysis

---
*Research completed: 2026-03-28*
*Ready for roadmap: yes*
