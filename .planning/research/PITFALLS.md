# Pitfalls Research

**Domain:** Event management platform (community organizations, ticketing, QR check-in)
**Researched:** 2026-03-28
**Confidence:** HIGH — findings verified across official docs, documented CVEs, and multiple community sources

---

## Critical Pitfalls

### Pitfall 1: Ticket Overselling via Race Condition

**What goes wrong:**
Two concurrent checkout requests read the same ticket tier capacity simultaneously, both see `remaining > 0`, both proceed to create orders, and the tier ends up selling more tickets than its capacity limit allows. This is the most common failure mode in ticketing systems and it is invisible in single-user testing.

**Why it happens:**
Developers write a check-then-act sequence (`SELECT capacity → check → INSERT order`) as separate operations without holding a database lock between the check and the insert. Under concurrent load, PostgreSQL's default READ COMMITTED isolation allows both reads to complete before either write, so both transactions believe capacity is available.

**How to avoid:**
Use `SELECT ... FOR UPDATE` on the ticket tier row inside a database transaction when checking capacity. In Django ORM: `TicketTier.objects.select_for_update().get(pk=tier_id)`. This serializes access — the second request blocks until the first commits, then re-checks with the updated value. Alternatively, use a `CHECK` constraint or atomic `UPDATE ... WHERE remaining_capacity > 0 RETURNING id` and check rows-affected.

**Warning signs:**
- Checkout tests pass but no concurrent tests exist
- Capacity check and order creation happen in separate try/except blocks without a wrapping `transaction.atomic()`
- Unit tests mock the capacity check rather than testing at the DB level

**Phase to address:**
Checkout / ticketing phase — must be implemented correctly from day one, not retrofitted. Wrap all checkout logic in `transaction.atomic()` with `select_for_update()` before the first real order is ever created.

---

### Pitfall 2: Promo Code Usage Limit Bypass via Race Condition

**What goes wrong:**
Two users apply the same promo code with `max_uses=1` simultaneously. Both requests query usage count, both see `0 < 1`, both apply the discount, both complete checkout — the code is used twice (or more). This is a documented CVE in the alf.io ticketing platform (GHSA-67jg-m6f3-473g).

**Why it happens:**
Same root cause as ticket overselling: usage count is read and checked before the increment, without locking. The problem is worse for promo codes because usage counts are a separate table from the order itself, making it easy to forget to lock both resources.

**How to avoid:**
Use `select_for_update()` on the promo code row when validating. Validate and increment usage atomically within `transaction.atomic()`. For high-contention codes (e.g., "FIRST100"), consider a database-level unique constraint on (promo_code_id, user_id) to enforce per-user limits without locking.

**Warning signs:**
- Promo validation and order creation are in separate code paths
- Promo usage is incremented after payment confirmation rather than reserved at checkout initiation
- No test exists for concurrent promo code application

**Phase to address:**
Checkout / promo codes phase — promo validation must happen inside the same `transaction.atomic()` block as order creation.

---

### Pitfall 3: Stripe Webhook Raw Body Destruction

**What goes wrong:**
Django's request processing or custom middleware reads/parses `request.body` before the Stripe webhook handler can access it. Stripe's `stripe.Webhook.construct_event()` requires the **raw, unmodified** byte string to verify the HMAC signature. Once parsed, signature verification fails with a `SignatureVerificationError`, causing all webhooks to be rejected or — worse — silently skipped.

**Why it happens:**
Django's `request.body` can only be read once in some middleware configurations. Any logging middleware, body inspection middleware, or DRF's default parsers that read the body before the webhook view will corrupt the raw bytes needed for verification.

**How to avoid:**
Access `request.body` directly in the webhook view before any other processing. Mark the webhook endpoint with `@csrf_exempt`. Do not apply DRF's default authentication/permission classes to the webhook endpoint (use `authentication_classes = []`, `permission_classes = []`). Never add body-logging middleware that eagerly reads all request bodies.

**Warning signs:**
- Webhook endpoint uses `request.data` (DRF's parsed body) instead of `request.body`
- Global middleware logs or inspects all request bodies
- Stripe dashboard shows webhook deliveries as "Failed" after integration

**Phase to address:**
Stripe integration phase — test webhook signature verification with the Stripe CLI locally (`stripe listen --forward-to`) before moving to any other payment logic.

---

### Pitfall 4: Duplicate Order Creation from Webhook Replay

**What goes wrong:**
Stripe delivers webhooks with at-least-once semantics — the same `payment_intent.succeeded` event may arrive 2+ times due to retries or network failures. Without idempotency protection, each delivery creates a new order, sends duplicate confirmation emails, and decrements ticket capacity multiple times.

**Why it happens:**
Developers handle the happy path (first delivery) but do not account for Stripe's retry behavior. Stripe retries failed webhooks up to 3 days with exponential backoff. A brief Railway server restart or timeout will trigger retries.

**How to avoid:**
Store processed Stripe event IDs in a database table (`StripeWebhookEvent` with `event_id` unique). Before processing any webhook: check if `event_id` exists — if yes, return `200 OK` immediately without processing. Use `transaction.atomic()` for the insert + business logic. Process webhooks asynchronously (Celery task or Django-Q) to keep response time under Stripe's 30-second timeout.

**Warning signs:**
- No `stripe_event_id` field on Order model or webhook event log table
- Webhook handler has no idempotency check at the top
- Confirmation emails sent synchronously inside the webhook handler

**Phase to address:**
Stripe integration phase — implement idempotency check before writing any order-creation webhook logic.

---

### Pitfall 5: Object-Level Permission Check Omission in DRF

**What goes wrong:**
Django REST Framework's `has_object_permission()` is **not automatically called** — it only runs if the view explicitly calls `self.check_object_permissions(request, obj)`. A MANAGER for Organization A can access, edit, or delete resources belonging to Organization B if object-level checks are missing. This is a cross-tenant data leak.

**Why it happens:**
DRF's `has_permission()` (view-level) is called automatically, giving developers confidence that permissions are checked. But the object-level check, which verifies org membership, requires an extra explicit call that is easy to forget — especially in `ViewSet` methods like `update()`, `partial_update()`, and `destroy()`.

**How to avoid:**
Create a base permission class that enforces org membership checks. In `GenericAPIView` subclasses, call `self.check_object_permissions(request, self.get_object())` — note that `get_object()` does call it if `self.get_object()` is used correctly. Verify by explicitly testing that a MANAGER from Org B cannot access Org A's events/tickets/orders by hitting those endpoints in tests.

**Warning signs:**
- Permission classes only check `has_permission()`, with no `has_object_permission()` implementation
- Integration tests only test valid access, not cross-org access attempts
- `ViewSet.retrieve()` overrides call `get_queryset().filter(pk=pk).first()` instead of `self.get_object()`

**Phase to address:**
Auth / RBAC phase — establish the permission class pattern before building any resource endpoint. Every subsequent phase inherits the pattern.

---

### Pitfall 6: Timezone Stored Without Context

**What goes wrong:**
Event start/end times are stored as naive datetimes (no timezone) or as UTC without preserving the event's named timezone. A "7:00 PM EST" event becomes "2024-01-15T00:00:00Z" in the database. When displayed back to attendees in different timezones, or when evaluating "is this event live right now?", the logic silently uses server timezone or UTC and produces wrong results.

**Why it happens:**
Developers test locally where server timezone matches expected behavior. The problem surfaces after deployment (Railway may use UTC) or when attendees in different timezones see the event page.

**How to avoid:**
Store two fields: `start_datetime` as a timezone-aware datetime in UTC, plus `timezone` as an IANA timezone string (e.g., `"America/New_York"`). Use `USE_TZ = True` in Django settings (default). Display times by converting from UTC to the event's named timezone using `pytz` or `zoneinfo`. Never store naive datetimes.

**Warning signs:**
- `USE_TZ = False` in Django settings
- Event model has `start_datetime` but no `timezone` field
- Frontend displays times using `new Date()` without timezone conversion

**Phase to address:**
Event creation phase — the model schema must include a `timezone` field from the start. Retrofit is painful and risks corrupting existing data.

---

### Pitfall 7: JWT Stored in localStorage (XSS Vulnerability)

**What goes wrong:**
Access tokens stored in `localStorage` or `sessionStorage` are readable by any JavaScript running in the browser, including injected scripts from XSS attacks. An attacker who finds an XSS vector (e.g., in event descriptions rendered without sanitization) can exfiltrate all tokens.

**Why it happens:**
`localStorage` is the simplest storage mechanism. It survives page reloads, works with SSR hydration easily, and requires no backend cookie configuration. Developers choose it for convenience without fully weighing the XSS exposure.

**How to avoid:**
Store access tokens in memory (React state or a module-level variable) and refresh tokens in `HttpOnly, Secure, SameSite=Strict` cookies. The access token's 30-minute lifetime limits exposure if leaked. Configure Django's `SESSION_COOKIE_SECURE` and CORS settings (`CORS_ALLOW_CREDENTIALS = True` with explicit `CORS_ALLOWED_ORIGINS`, never `CORS_ALLOW_ALL_ORIGINS = True`).

**Warning signs:**
- `localStorage.setItem('access_token', ...)` anywhere in frontend code
- CORS configured with `CORS_ALLOW_ALL_ORIGINS = True`
- No `HttpOnly` flag on refresh token cookie

**Phase to address:**
Auth / frontend phase — establish secure token storage before building any authenticated page.

---

### Pitfall 8: QR Code HMAC Uses Django SECRET_KEY Directly

**What goes wrong:**
The QR payload is HMAC-signed with Django's `SECRET_KEY`. If `SECRET_KEY` must be rotated (security incident, team member departure, key compromise), all previously issued QR codes become invalid immediately. Every ticket holder's QR code stops scanning at the door.

**Why it happens:**
`SECRET_KEY` is already available everywhere in Django and is the obvious "use this secret" candidate. The spec explicitly calls this out, which suggests it was an intentional design decision — but the rotation risk is real.

**How to avoid:**
Use a dedicated `QR_SIGNING_KEY` environment variable separate from `SECRET_KEY`. Document key rotation procedure: new key → re-sign all future tickets → old key remains valid for a configurable grace period (e.g., 30 days for tickets already issued). For events actively in check-in, never rotate without a migration window.

**Warning signs:**
- `settings.SECRET_KEY` referenced directly in QR signing code
- No `QR_SIGNING_KEY` environment variable defined
- No documented key rotation runbook

**Phase to address:**
QR check-in phase — separate the signing key at implementation time, not after first security incident.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip `select_for_update()` on ticket capacity | Simpler checkout code | Overselling at any concurrent load | Never |
| Stripe webhook without idempotency check | Faster to implement | Duplicate orders, duplicate emails on retries | Never |
| `localStorage` for JWT | Simple auth persistence | Full token theft on any XSS | Never |
| No dedicated `QR_SIGNING_KEY` | One fewer env var | All QR codes invalid on SECRET_KEY rotation | Never |
| Soft delete without unique constraint scoping | Simpler model | Duplicate email errors when user re-registers after soft delete | Never — add `unique_together` with `is_active` from the start |
| Check-in stats via count queries on every poll | Simple implementation | Database hammered during large events with live polling | Acceptable for MVP; cache or denormalize at scale |
| Synchronous email sending in webhook handler | Simpler code path | Webhook times out (>30s), Stripe retries, duplicate emails | Never — always async |
| Django `DEBUG=True` on Railway | See full error traces | Exposes stack traces and env vars to public internet | Never in production |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Stripe webhooks | Using `request.data` (parsed body) instead of `request.body` for signature verification | Access `request.body` directly; never let middleware parse it first |
| Stripe webhooks | Returning `4xx` on business logic errors, causing Stripe to retry | Always return `200 OK` after receiving a valid signed event; handle errors internally |
| Stripe PaymentIntent | Treating the success redirect URL as proof of payment | Only fulfill orders on `payment_intent.succeeded` webhook, not on redirect |
| Stripe PaymentIntent | Creating a new PaymentIntent on every page load/retry | Create once, store `payment_intent_id` on the order, retrieve existing on retry |
| djangorestframework-simplejwt | `BLACKLIST_AFTER_ROTATION = False` with rotation enabled | Set both `ROTATE_REFRESH_TOKENS = True` AND `BLACKLIST_AFTER_ROTATION = True`; otherwise old refresh tokens remain valid |
| djangorestframework-simplejwt | No rate limiting on `/token/refresh/` | Apply throttling — unlimited refresh attempts enable token stuffing attacks |
| Railway (backend) + Vercel (frontend) | `CORS_ALLOWED_ORIGINS` missing or using wildcard with credentials | Set exact Vercel domain; `CORS_ALLOW_CREDENTIALS = True` requires non-wildcard origin |
| Vercel environment variables | Using same env vars for preview and production | Separate `NEXT_PUBLIC_API_URL` per environment; preview deployments hitting production API causes data contamination |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| N+1 queries on guest list / attendee list | Guest list page slow; Django Debug Toolbar shows 100s of queries | `select_related('ticket_tier', 'order__user')` on attendee querysets | At ~50 attendees with eager loading off |
| Polling check-in stats without caching | Database CPU spikes during events; Railway hobby tier connection limit hit | Cache stats with 5-second TTL (Django cache framework + Railway Redis add-on) or compute in a periodic background task | At ~10 concurrent scanner devices polling every 2s |
| Unindexed order lookup by confirmation code | Attendee lookup slow at check-in under time pressure | Add `db_index=True` on `confirmation_code` field; add composite index on `(event_id, status)` for ticket queries | At ~500 orders per event |
| Generating all QR codes at order time synchronously | Checkout response slow for multi-ticket orders | Generate QR codes asynchronously (post-order task) or lazily on first access | At 5+ tickets per order |
| Full-text search on events without index | Public browse page times out | Use PostgreSQL `GIN` index on `tsvector` for event name/description search, or prefix with `ILIKE` + index on name | At ~1,000 events in the database |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| QR codes embody ticket data without server-side re-validation on scan | Forged/altered QR codes grant entry | Always re-validate ticket status (`VALID` not `USED` or `CANCELLED`) in database on every scan, regardless of HMAC validity |
| Org membership not checked on nested resources | Cross-org data access — MANAGER from Org B reads Org A's revenue analytics | Every view on org-scoped resources must verify `request.user` has a role in the resource's org, at object level |
| Promo codes exposed in URL parameters | Code harvesting from browser history, server logs, referrer headers | POST promo code application, never GET; never log promo codes in access logs |
| Ticket tier `INVITE_ONLY` visibility enforced only in frontend | Direct API call bypasses frontend filter and purchases invite-only tickets | Enforce visibility rules in backend serializer/queryset; never trust frontend to hide restricted tiers |
| Django `SECRET_KEY` in version control | Full session/token/QR compromise if repo is public or leaked | Require `SECRET_KEY` as environment variable; fail fast with `ImproperlyConfigured` if not set; add to `.gitignore` |
| HMAC truncated to first 16 hex chars (64-bit) | Brute-force feasible with high-volume scanning | Acceptable for check-in where server validates, but document that HMAC truncation is a deliberate tradeoff; consider full SHA256 hex if forgery risk increases |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No confirmation email retry / resend | Attendee never received email (spam folder, typo); contacts organizer; no self-serve resolution | Add "Resend confirmation" button on order detail page; log all email sends with status |
| Check-in scanner shows generic "invalid" for all failure modes | Volunteer cannot distinguish expired ticket, already checked in, or wrong event; slows check-in line | Show distinct states: "Already Checked In" (yellow), "Invalid Code" (red), "Wrong Event" (red with event name), "Valid" (green) |
| Ticket capacity shown as depleted due to abandoned checkouts | Event appears sold out; potential attendees leave; org loses revenue | Implement checkout session timeout (15 min) with capacity reservation that releases on expiry |
| Paid event shows card form before user knows total | Surprise fees after entering card details; abandonment | Show full order summary (subtotal, fees, promo discount, total) before Stripe card element mounts |
| Event status transitions not communicated | Attendees try to register for COMPLETED events; confusing error messages | Public event page shows clear status badge; registration button disabled with "Registration closed" for non-PUBLISHED states |
| CSV export includes PII without access control | VOLUNTEER role exports full attendee list including email/phone | Restrict CSV export to OWNER/MANAGER roles; VOLUNTEER role gets check-in view only |

---

## "Looks Done But Isn't" Checklist

- [ ] **Checkout:** Capacity check uses `select_for_update()` — verify by running two concurrent requests against a single-capacity tier and confirming only one order is created
- [ ] **Promo codes:** Usage limit enforced with row-level lock — verify concurrent application does not exceed `max_uses`
- [ ] **Stripe webhooks:** Idempotency table exists — verify second delivery of same event ID returns 200 without creating a second order
- [ ] **Stripe webhooks:** Raw body preserved — verify `stripe.Webhook.construct_event()` does not raise `SignatureVerificationError` in staging with real Stripe CLI
- [ ] **JWT:** Blacklist app enabled — verify that after refresh, the old refresh token is rejected (not accepted)
- [ ] **Permissions:** Object-level org check exists — verify MANAGER from Org B gets 403 on Org A's event endpoints (not 200 or 404)
- [ ] **QR check-in:** Duplicate scan returns `already_checked_in` state, not success — verify by scanning same code twice
- [ ] **Ticket tier visibility:** INVITE_ONLY tier not purchasable via direct API call by non-invited user — verify without frontend
- [ ] **Soft delete:** Re-registration after soft-delete user does not hit unique constraint error — verify email uniqueness scoped correctly
- [ ] **Timezone:** Event displayed in event's named timezone, not server timezone — verify with UTC-offset event created from a non-UTC browser
- [ ] **Email:** Confirmation email sent exactly once per order even when webhook retries — verify with Stripe CLI replay
- [ ] **Check-in stats:** Live polling does not degrade under 10 concurrent scanner sessions — verify with simple load test

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Ticket overselling discovered post-event | MEDIUM | Audit orders vs capacity; refund overflow orders; communicate to affected attendees; add `select_for_update()` |
| Promo code over-use discovered post-checkout | MEDIUM | Audit usage vs `max_uses`; contact abusing accounts; issue credit notes or void excess orders; add locking |
| Duplicate orders from webhook replay | HIGH | Identify duplicates by `stripe_payment_intent_id`; void duplicate orders; reverse capacity decrements; send apology emails; add idempotency key table |
| SECRET_KEY rotation invalidating all QR codes during active event | CRITICAL | Revert to old key immediately if pre-event; for active event, switch to manual check-in fallback; issue new QR codes post-event |
| Cross-org data leak discovered | HIGH | Rotate all API tokens; audit access logs for scope of exposure; notify affected orgs; patch permission checks; security disclosure if required |
| JWT tokens in localStorage with XSS found | HIGH | Rotate signing keys; invalidate all outstanding tokens; force re-login; fix XSS source; migrate to HttpOnly cookies |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Ticket overselling (race condition) | Checkout / ticketing | Concurrent checkout test against single-capacity tier |
| Promo code bypass (race condition) | Checkout / promo codes | Concurrent promo application test |
| Stripe webhook raw body | Stripe integration | Stripe CLI replay in staging; check signature verification passes |
| Webhook duplicate order | Stripe integration | Send same event ID twice; confirm single order |
| DRF object-level permission omission | Auth / RBAC (foundational) | Cross-org access test on every resource type |
| Timezone storage | Event creation / data model | Create event as UTC, read back in named timezone |
| JWT in localStorage | Auth / frontend | Code review + CSP header review |
| QR signing key tied to SECRET_KEY | QR check-in | Env var audit; rotation runbook exists |
| Soft delete unique constraint | Data model (foundational) | Re-register deleted user test |
| Missing email idempotency | Email / notifications | Resend confirmation twice; verify single email delivered |

---

## Sources

- [SELECT FOR UPDATE Race Condition Prevention in Django & PostgreSQL — DEV Community](https://dev.to/alairjt/guarding-critical-operations-mastering-select-for-update-for-race-condition-prevention-in-django--32mg)
- [Bypassing promo code limitations with race conditions — alf.io CVE GHSA-67jg-m6f3-473g](https://github.com/alfio-event/alf.io/security/advisories/GHSA-67jg-m6f3-473g)
- [Stripe Webhooks Best Practices — Stigg Engineering Blog](https://www.stigg.io/blog-posts/best-practices-i-wish-we-knew-when-integrating-stripe-webhooks)
- [Handling Payment Webhooks Reliably — Medium](https://medium.com/@sohail_saifii/handling-payment-webhooks-reliably-idempotency-retries-validation-69b762720bf5)
- [Receive Stripe events in your webhook endpoint — Stripe Official Docs](https://docs.stripe.com/webhooks)
- [Idempotent requests — Stripe API Reference](https://docs.stripe.com/api/idempotent_requests)
- [Django REST Framework Permissions — Official Docs](https://www.django-rest-framework.org/api-guide/permissions/)
- [Permission OR and AND check order bug — DRF GitHub Issue #6402](https://github.com/encode/django-rest-framework/issues/6402)
- [djangorestframework-simplejwt Settings — Official Docs](https://django-rest-framework-simplejwt.readthedocs.io/en/stable/settings.html)
- [Soft Delete Pattern: Why It Creates More Problems — byteiota](https://byteiota.com/soft-delete-pattern-why-it-creates-more-problems/)
- [How to Handle Date and Time Correctly to Avoid Timezone Bugs — DEV Community](https://dev.to/kcsujeet/how-to-handle-date-and-time-correctly-to-avoid-timezone-bugs-4o03)
- [How to prevent replay attacks when using HMAC — LinkedIn](https://www.linkedin.com/advice/0/how-do-you-prevent-replay-attacks-when-using-hmac-authentication)
- [Next.js HTTP-Only Cookies for Secure Authentication — Max Schmitt](https://maxschmitt.me/posts/next-js-http-only-cookie-auth-tokens)
- [PostgreSQL Row-Level Locks: FOR UPDATE Complete Guide](https://scalablearchitect.com/postgresql-row-level-locks-a-complete-guide-to-for-update-for-share-skip-locked-and-nowait/)
- [Transactional Email Best Practices 2026 — Postmark](https://postmarkapp.com/guides/transactional-email-best-practices)

---
*Pitfalls research for: GatherGood event management platform*
*Researched: 2026-03-28*
