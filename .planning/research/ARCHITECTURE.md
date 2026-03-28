# Architecture Research

**Domain:** Event management platform (community organizations — nonprofits, libraries, volunteer groups)
**Researched:** 2026-03-28
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ Public Pages │  │ Organizer    │  │ Check-In     │               │
│  │ (Browse,     │  │ Dashboard    │  │ App (mobile  │               │
│  │  Event Detail│  │ (Events,     │  │  web, QR     │               │
│  │  Org Page)   │  │  Orders,     │  │  scanning)   │               │
│  │              │  │  Analytics)  │  │              │               │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │
│         │                 │                  │                        │
│  Next.js App Router (Vercel) — SSR + Client Components               │
├─────────┴─────────────────┴──────────────────┴────────────────────── ┤
│                         API LAYER (JWT Auth)                          │
│                  HTTPS REST — /api/v1/                                │
├──────────────────────────────────────────────────────────────────────┤
│                         BACKEND LAYER (Railway)                       │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  Auth App  │  │  Orgs App    │  │ Events App  │  │ Tickets App │ │
│  │  (users,   │  │  (org, roles,│  │ (event,     │  │ (checkout,  │ │
│  │   JWT,     │  │   venues,    │  │  tiers,     │  │  orders,    │  │
│  │   profiles)│  │   team)      │  │  promos)    │  │  QR codes)  │ │
│  └────────────┘  └──────────────┘  └─────────────┘  └─────────────┘ │
│  ┌──────────────────┐  ┌───────────────────────────────────────────┐ │
│  │  Analytics App   │  │  Notifications App                        │ │
│  │  (time series,   │  │  (email confirm, reminders, bulk send)    │ │
│  │   attendance,    │  │                                           │ │
│  │   revenue)       │  │                                           │ │
│  └──────────────────┘  └───────────────────────────────────────────┘ │
│  Django REST Framework (Python) — all apps share service layer        │
├──────────────────────────────────────────────────────────────────────┤
│                         DATA + EXTERNAL LAYER                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ PostgreSQL 16│  │   Stripe     │  │  SMTP /      │               │
│  │ (Railway)    │  │  Payments    │  │  Email SVC   │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| Next.js frontend | All UI rendering (SSR public pages + client dashboard) | Django API via fetch/axios |
| Auth app (Django) | User registration, JWT issue/refresh, password reset, profiles | All other Django apps |
| Orgs app (Django) | Organization CRUD, role-based membership, venue management | Events app, Auth app |
| Events app (Django) | Event lifecycle, ticket tiers, promo codes | Tickets app, Orgs app |
| Tickets app (Django) | Checkout, order creation, QR generation, check-in | Events app, Stripe |
| Analytics app (Django) | Registration/revenue aggregation, time series, attendance rate | Events app, Tickets app |
| Notifications app (Django) | Email confirmation, reminders, bulk send, email log | Orders app, SMTP provider |
| PostgreSQL 16 | All persistent data | Django ORM |
| Stripe | Payment processing (PaymentIntent flow) | Tickets app webhook receiver |
| SMTP provider | Transactional + bulk email delivery | Notifications app |

## Recommended Project Structure

### Backend (Django)

```
backend/
├── config/
│   ├── settings/
│   │   ├── base.py           # shared settings
│   │   ├── local.py          # dev overrides
│   │   └── production.py     # Railway / prod overrides
│   ├── urls.py               # root URL conf — mounts /api/v1/
│   └── wsgi.py
├── apps/
│   ├── accounts/             # User model, JWT auth, profiles
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── services.py       # business logic isolated from views
│   │   ├── urls.py
│   │   └── tests/
│   ├── organizations/        # Org, OrganizationMember, Venue
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── services.py
│   │   ├── permissions.py    # OWNER/MANAGER/VOLUNTEER checks
│   │   ├── urls.py
│   │   └── tests/
│   ├── events/               # Event, TicketTier, PromoCode
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── services.py
│   │   ├── urls.py
│   │   └── tests/
│   ├── orders/               # Order, Ticket, QR generation
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── services.py       # checkout logic, HMAC QR signing
│   │   ├── urls.py
│   │   └── tests/
│   ├── checkin/              # CheckIn records, scan validation
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── services.py       # duplicate/invalid/success states
│   │   ├── urls.py
│   │   └── tests/
│   ├── analytics/            # Read-only aggregation views
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── services.py
│   │   ├── urls.py
│   │   └── tests/
│   └── notifications/        # Email log, send logic
│       ├── models.py
│       ├── services.py
│       └── tests/
├── common/
│   ├── permissions.py        # shared DRF permission classes
│   ├── pagination.py
│   ├── utils.py              # slug generation, HMAC helpers
│   └── mixins.py
└── requirements/
    ├── base.txt
    └── production.txt
```

### Frontend (Next.js)

```
frontend/
├── src/
│   ├── app/                          # App Router root
│   │   ├── layout.tsx                # root layout (auth-aware nav)
│   │   ├── page.tsx                  # homepage
│   │   ├── (public)/                 # route group — no auth required
│   │   │   ├── events/
│   │   │   │   ├── page.tsx          # public event browse + search
│   │   │   │   └── [slug]/
│   │   │   │       └── page.tsx      # public event detail + ticket tiers
│   │   │   └── organizations/
│   │   │       └── [slug]/
│   │   │           └── page.tsx      # public org page
│   │   ├── (auth)/                   # route group — login/register flows
│   │   │   ├── login/page.tsx
│   │   │   ├── register/page.tsx
│   │   │   └── forgot-password/page.tsx
│   │   ├── dashboard/                # authenticated organizer area
│   │   │   ├── layout.tsx            # dashboard shell (sidebar nav)
│   │   │   ├── page.tsx              # org switcher / landing
│   │   │   ├── [orgSlug]/
│   │   │   │   ├── events/
│   │   │   │   │   ├── page.tsx      # event list
│   │   │   │   │   ├── new/page.tsx
│   │   │   │   │   └── [eventSlug]/
│   │   │   │   │       ├── page.tsx  # event detail / edit
│   │   │   │   │       ├── tickets/page.tsx
│   │   │   │   │       ├── orders/page.tsx
│   │   │   │   │       ├── checkin/page.tsx
│   │   │   │   │       └── analytics/page.tsx
│   │   │   │   ├── team/page.tsx
│   │   │   │   └── settings/page.tsx
│   │   │   └── profile/page.tsx
│   │   └── checkout/
│   │       ├── [eventSlug]/page.tsx  # ticket selection + payment
│   │       └── success/page.tsx
│   ├── components/
│   │   ├── ui/                       # base design system (Button, Input, etc.)
│   │   ├── events/                   # event-specific components
│   │   ├── orders/                   # checkout / ticket components
│   │   ├── checkin/                  # QR scanner, check-in UI
│   │   └── dashboard/                # nav, sidebar, analytics widgets
│   ├── lib/
│   │   ├── api/                      # typed fetch wrappers per resource
│   │   │   ├── auth.ts
│   │   │   ├── events.ts
│   │   │   ├── orders.ts
│   │   │   └── checkin.ts
│   │   ├── auth.ts                   # JWT token management (access + refresh)
│   │   └── utils.ts
│   ├── hooks/                        # React hooks (useAuth, usePolling, etc.)
│   └── types/                        # TypeScript interfaces mirroring API shapes
├── public/
└── next.config.ts
```

### Structure Rationale

- **apps/ (backend):** Each Django app owns one domain slice — models, serializers, views, services, and tests together. Cross-cutting concerns (permissions, slugs, HMAC) live in `common/`.
- **services.py per app:** Business logic never lives in views. Views are thin HTTP adapters; services own domain logic. This makes testing straightforward and prevents fat-view anti-pattern.
- **route groups (frontend):** `(public)` vs `(auth)` vs `dashboard` have different layouts and auth requirements. Route groups let them share layout without polluting URLs.
- **lib/api/ (frontend):** All backend calls go through typed functions here, never directly from components. One place to update base URL, token injection, and error handling.

## Architectural Patterns

### Pattern 1: Service Layer in Django

**What:** Views delegate all business logic to service functions in `services.py`. Views only handle HTTP concerns (auth, request parsing, response serialization).
**When to use:** Always for operations with side effects — order creation, check-in validation, email sending, QR generation.
**Trade-offs:** Slightly more files; significantly easier to test and reuse logic (e.g., checkout service called by both the API view and a management command).

**Example:**
```python
# views.py — thin HTTP adapter
class CheckoutView(APIView):
    def post(self, request, event_slug):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = checkout_service.create_order(
            user=request.user,
            event_slug=event_slug,
            validated_data=serializer.validated_data,
        )
        return Response(OrderSerializer(order).data, status=201)

# services.py — owns the logic
def create_order(user, event_slug, validated_data):
    event = get_object_or_404(Event, slug=event_slug)
    _validate_capacity(event, validated_data)
    _validate_promo(event, validated_data)
    order = Order.objects.create(user=user, event=event, ...)
    _generate_tickets(order)
    return order
```

### Pattern 2: Stripe PaymentIntent Flow (Client-Confirmed)

**What:** Backend creates a PaymentIntent and returns `client_secret` to the frontend. Frontend mounts Stripe Elements, user enters card details, and Stripe.js confirms the payment client-side. Backend webhook receives `payment_intent.succeeded` to finalize the order.
**When to use:** All paid ticket checkouts. Free events bypass Stripe entirely and confirm the order immediately server-side.
**Trade-offs:** Requires webhook handling for final confirmation; but card data never touches your servers (PCI compliance).

**Example flow:**
```
POST /api/v1/checkout/create-intent/
  → Backend: creates pending Order + PaymentIntent
  → Returns: { client_secret, order_id }

Frontend: stripe.confirmCardPayment(client_secret, { payment_method: ... })
  → Stripe confirms payment

POST Stripe webhook → /api/v1/webhooks/stripe/
  → Backend: verifies signature, marks Order as CONFIRMED, generates tickets
```

### Pattern 3: HMAC-Signed QR Tickets

**What:** Each ticket's QR payload is a JSON blob signed with HMAC-SHA256 using Django's SECRET_KEY (first 16 hex chars). The check-in endpoint re-computes the signature and rejects any tampered or forged codes.
**When to use:** All ticket QR generation and check-in validation.
**Trade-offs:** Stateless verification is fast and works offline; the SECRET_KEY must never rotate without invalidating all existing QR codes.

**Example payload:**
```python
# orders/services.py
import hmac, hashlib, json

def generate_qr_payload(ticket):
    data = {"ticket_id": str(ticket.id), "event_id": str(ticket.event_id)}
    raw = json.dumps(data, separators=(',', ':'), sort_keys=True)
    sig = hmac.new(settings.SECRET_KEY.encode(), raw.encode(), hashlib.sha256).hexdigest()[:16]
    return json.dumps({"data": data, "sig": sig})
```

### Pattern 4: Polling for Live Check-In Stats

**What:** The check-in dashboard polls `GET /api/v1/events/{slug}/checkin/stats/` every N seconds to show live totals (total / checked-in / remaining, per-tier breakdown) without WebSockets.
**When to use:** Check-in stats page during events.
**Trade-offs:** Simpler than WebSockets, sufficient for typical community event scale (hundreds of check-ins/hour). If polling adds noticeable load at scale, switch to Server-Sent Events.

## Data Flow

### Checkout Flow (Paid Event)

```
User selects tickets + enters promo code
        ↓
POST /api/v1/checkout/create-intent/
        ↓
Django: validate capacity → validate promo → create pending Order
        → create Stripe PaymentIntent → return client_secret
        ↓
Next.js: stripe.confirmCardPayment(client_secret)
        ↓ (payment confirmed by Stripe)
Stripe webhook → POST /api/v1/webhooks/stripe/
        ↓
Django: verify HMAC webhook sig → mark Order CONFIRMED
        → generate Tickets with HMAC-signed QR payloads
        → trigger confirmation email (async)
        ↓
User sees confirmation page with QR ticket
```

### Checkout Flow (Free Event)

```
User selects tickets
        ↓
POST /api/v1/checkout/free/
        ↓
Django: validate capacity → create Order CONFIRMED immediately
        → generate Tickets with QR payloads
        → trigger confirmation email
        ↓
User sees confirmation page with QR ticket
```

### QR Check-In Flow

```
Staff opens /dashboard/{orgSlug}/events/{eventSlug}/checkin/
        ↓
Camera / scan input captures QR payload
        ↓
POST /api/v1/events/{slug}/checkin/scan/
        ↓
Django: decode payload → verify HMAC signature
        → check ticket status (UNUSED / USED / INVALID)
        → mark as checked in → return { status: "success" | "duplicate" | "invalid" }
        ↓
Frontend displays green / yellow / red feedback
```

### Auth Flow (JWT)

```
POST /api/v1/auth/login/ → { access (30min), refresh (7-day) }
        ↓
Frontend stores tokens (memory for access, httpOnly cookie for refresh)
        ↓
Every request: Authorization: Bearer {access}
        ↓
Token expiry: POST /api/v1/auth/token/refresh/ → new access + rotated refresh
```

### State Management (Frontend)

```
Server state (API data):  React Query / SWR — per-resource cache
Auth state:               React Context or Zustand — current user + tokens
Form state:               React Hook Form — local to each form
UI state:                 Local useState — modals, loading spinners
```

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Stripe | PaymentIntent (client-confirmed) + webhook receiver | Webhook endpoint must verify `Stripe-Signature` header before processing; use Stripe CLI for local testing |
| SMTP / Email | Django email backend (send_mail or task queue) | For v1, synchronous send is acceptable; extract to task queue (Celery/RQ) when send volume grows |
| Vercel | Frontend deployment — automatic on push to main | Environment variables for API base URL, Stripe public key |
| Railway | Backend + PostgreSQL — managed containers | DATABASE_URL injected at deploy time; SECRET_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET in env |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Frontend ↔ Django API | HTTPS REST + JWT Bearer | All API calls go through `lib/api/` typed wrappers in Next.js |
| Orders ↔ Events | Django ORM (same DB) | Orders app queries Event/TicketTier from events app directly |
| Orders ↔ Stripe | stripe-python SDK | PaymentIntent create in checkout, webhook handler in separate view |
| CheckIn ↔ Orders | Django ORM | CheckIn service reads Ticket and Order records from orders app |
| Analytics ↔ Events+Orders | Django ORM aggregations | Read-only; no writes from analytics app |
| Notifications ↔ Orders | Function call (services) | notifications.services.send_confirmation(order) called from orders service |

## Build Order (Dependency Graph)

The components have hard dependencies that dictate build order:

```
1. Auth (accounts app + JWT)
        ↓
2. Organizations (orgs app + roles/permissions)
        ↓
3. Events (events + ticket tiers + promo codes)
        ↓
4. Orders + Checkout (free path first, then Stripe)
        ↓
5. QR generation → Check-In (depends on Order/Ticket records existing)
        ↓
6. Analytics (depends on Orders + CheckIn data existing)
        ↓
7. Notifications / Email (can be added alongside checkout; solidified in phase 6)
        ↓
8. Public pages + search (depends on Event records existing)
```

**Rationale:**
- Auth must exist before any permission-protected endpoint is built.
- Organizations are the ownership container for all Events — must exist before Events.
- Events must exist before checkout can be built (need TicketTier to purchase).
- Free checkout must be validated before adding Stripe — isolates payment complexity.
- QR check-in needs real Order/Ticket rows — cannot be tested in isolation.
- Analytics is pure read — add it after the write paths stabilize.
- Public browse pages are mostly read-only frontend work — can be done in parallel with later backend phases once Events API is stable.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-1k users | Monolith is fine; single Railway dyno + hobby PostgreSQL plan; synchronous email send |
| 1k-10k users | Add DB connection pooling (PgBouncer or Railway connection limits); move email to async task queue (RQ or Celery + Redis); add PostgreSQL indexes on event slug, order confirmation code |
| 10k+ users | Cache public event browse (Redis or CDN); read replicas for analytics queries; consider separating analytics into materialized views or background aggregation jobs |

### Scaling Priorities

1. **First bottleneck:** PostgreSQL connection exhaustion under concurrent checkout load. Fix: PgBouncer or pgpool; Railway's connection limit is low on starter plans.
2. **Second bottleneck:** Email send latency blocking checkout confirmation. Fix: async task queue (RQ is simpler than Celery for Railway).
3. **Third bottleneck:** Check-in poll requests at large events. Fix: reduce poll interval for small events, add short-lived Redis cache for stats, or switch to Server-Sent Events.

## Anti-Patterns

### Anti-Pattern 1: Business Logic in Views

**What people do:** Put checkout validation, capacity checks, promo logic, and QR generation directly inside DRF APIView or ViewSet methods.
**Why it's wrong:** Views become untestable, logic gets duplicated across endpoints, and adding a management command (e.g., bulk ticket generation) requires copy-pasting view internals.
**Do this instead:** Keep views as thin HTTP adapters. All logic lives in `services.py`; views call service functions and serialize the result.

### Anti-Pattern 2: Confirming Orders on PaymentIntent Creation

**What people do:** Mark an order as CONFIRMED when the backend creates the PaymentIntent, before payment is actually collected.
**Why it's wrong:** The payment can fail, be cancelled, or the user can close the browser. You end up with ghost confirmed orders and over-consumed capacity.
**Do this instead:** Orders stay PENDING until the `payment_intent.succeeded` webhook fires. Only then mark CONFIRMED and generate tickets. Always verify the Stripe webhook signature.

### Anti-Pattern 3: Storing QR Payload Without Signature Verification on Scan

**What people do:** The check-in endpoint trusts the ticket_id in the QR payload without verifying the HMAC signature.
**Why it's wrong:** Anyone can craft a QR code with an arbitrary ticket_id and check in as any attendee.
**Do this instead:** Always re-compute the HMAC on scan and reject the check-in if signatures don't match, before touching the database.

### Anti-Pattern 4: Mixing Server and Client Components Carelessly in Next.js

**What people do:** Fetch API data directly in client components using useEffect, even for public event pages.
**Why it's wrong:** Public pages (event browse, event detail, org page) should be server-rendered for SEO and performance. useEffect data fetching creates loading flicker and poor Core Web Vitals.
**Do this instead:** Use Server Components for public read-only pages (async page.tsx that fetches data server-side). Reserve client components for interactive elements (checkout form, QR scanner, live polling dashboard).

### Anti-Pattern 5: Single Monolithic Permissions Module

**What people do:** One giant permissions.py at project root that handles all org role checks for every app.
**Why it's wrong:** Org role logic (OWNER > MANAGER > VOLUNTEER) gets intertwined with check-in logic, event edit logic, analytics access logic — hard to reason about and test.
**Do this instead:** Each app has its own `permissions.py` that imports the base role-checking utilities from `common/permissions.py`. App-level permissions compose the shared primitives.

## Sources

- [Next.js App Router Project Structure — Official Docs (v16.2.1, 2026-03-25)](https://nextjs.org/docs/app/getting-started/project-structure)
- [Building Robust APIs with DRF: Best Practices and Project Structure](https://medium.com/@anindya.lokeswara/building-robust-apis-with-django-rest-framework-best-practices-and-project-structure-9d5f4447539f)
- [Stripe Webhooks — Official Documentation](https://docs.stripe.com/webhooks)
- [Django Stripe Tutorial — TestDriven.io](https://testdriven.io/blog/django-stripe-tutorial/)
- [Next.js + Django SaaS Architecture Guide 2025](https://techarion.com/blog/building-saas-application-nextjs-django-rest-framework)

---
*Architecture research for: GatherGood — event management platform for community organizations*
*Researched: 2026-03-28*
