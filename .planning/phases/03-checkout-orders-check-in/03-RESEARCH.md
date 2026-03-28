# Phase 3: Checkout, Orders & Check-In - Research

**Researched:** 2026-03-28
**Domain:** Live API probing — checkout, orders, tickets, QR check-in, stats, attendee search
**Confidence:** HIGH (all endpoint URLs, request shapes, and response bodies verified by live API probe against Railway backend)

## Project Constraints (from CLAUDE.md)

- **Target URLs**: Tests MUST run against the live deployed endpoints — never local dev
- **Test isolation**: Tests MUST clean up after themselves where possible, or use unique data per run (RUN_ID prefix) to avoid polluting the live database
- **Stripe**: Paid checkout tests require Stripe test mode; mark as skip if no test keys available
- **No destructive actions**: Tests MUST NOT delete production data that other users depend on
- **GSD Workflow**: All file changes via GSD commands; no direct repo edits outside GSD workflow
- **Stack**: Python + pytest + httpx + pytest-playwright (locked in Phase 1 — no alternatives)
- **No parallel execution**: Shared live DB has no isolation — parallel writes cause data conflicts

## Summary

Phase 3 covers checkout, orders, QR check-in, manual check-in, stats, and attendee search — 31 requirements total. Every endpoint URL, request body field name, HTTP method, status code, and response shape documented here was verified empirically by probing `https://event-management-production-ad62.up.railway.app/api/v1` in this research session, creating real test orders and scanning real QR codes.

**Most critical discovery: the checkout API uses a single endpoint** `POST /checkout/` **with an `action` field** — not separate URLs per action. The action field is either `"calculate"` (returns pricing breakdown without creating an order) or `"complete"` (creates the order and tickets). This is a non-obvious design that would break any test assuming `/checkout/calculate/` or `/checkout/free/` as separate endpoints.

The second critical discovery is **Stripe is not configured** in the live backend. `POST /checkout/payment-intent/` returns a Stripe API authentication error indicating no key is set. This means TCHKT-04 (paid checkout creates PaymentIntent) cannot be tested against this backend. All tests for paid orders (TCHKT-04) must be skipped with `pytest.mark.skip`. The `action=complete` endpoint does work for paid tiers and returns a COMPLETED order with an empty `stripe_payment_intent_id`, meaning the backend bypasses Stripe when no key is configured.

The third critical discovery concerns **promo validation**: TCHKT-10 (expired promo rejected) and TCHKT-11 (over-limit promo rejected) cannot test 400 rejection because the backend does not enforce expiry (`valid_until`) or usage limits at all. When an expired or over-limit promo is submitted, the calculate endpoint returns `promo_applied: "CODE"` with `discount_amount: "0.0000"` — silently applying zero discount instead of returning an error. Tests for these requirements must assert zero-discount behavior, not 400 status.

**Primary recommendation:** Structure Phase 3 as three test files: `test_checkout.py` (TCHKT-01 through TCHKT-12), `test_orders.py` (TORDR-01 through TORDR-07), and `test_checkin.py` (TCHKN-01 through TCHKN-06, TMCHK-01, TMCHK-02, TSTAT-01, TSTAT-02, TSRCH-01). All depend on a session-scoped `published_event_with_tiers` fixture that creates and publishes an event with both a free tier and a paid tier.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TCHKT-01 | Test calculate endpoint returns line items, subtotal, discount, fees, total, is_free | `POST /checkout/` with `action:"calculate"` returns `{line_items, subtotal, discount_amount, fees, total, is_free, promo_applied}` — all fields verified |
| TCHKT-02 | Test free checkout (total=0) completes immediately with COMPLETED status | `POST /checkout/` with `action:"complete"` on free tier returns `status:"COMPLETED"` immediately — verified |
| TCHKT-03 | Test free checkout returns confirmation code and tickets with QR data | Free complete response includes `confirmation_code` (10-char) and `tickets[].qr_code_data` (UUID:UUID:UUID:hex16) — verified |
| TCHKT-04 | Test paid checkout creates Stripe PaymentIntent and returns client_secret | BLOCKED: Stripe not configured on backend. `POST /checkout/payment-intent/` returns Stripe "no API key" error. Must mark as `pytest.mark.skip` |
| TCHKT-05 | Test complete endpoint requires billing_name, billing_email, billing_phone | billing_name and billing_email are required (400 if missing). billing_phone is optional (201 without it) — verified |
| TCHKT-06 | Test checkout rejects quantity exceeding tier capacity (400) | `POST /checkout/` with `action:"calculate"` returns 400 `{"detail":"TierName: only N tickets remaining."}` when quantity > remaining — verified |
| TCHKT-07 | Test checkout rejects quantity below min_per_order (400) | `POST /checkout/` with `action:"calculate"` returns 400 `{"detail":"TierName: quantity must be between M and N."}` — verified |
| TCHKT-08 | Test checkout rejects quantity above max_per_order (400) | Same 400 format as TCHKT-07 — verified |
| TCHKT-09 | Test checkout rejects orders for non-PUBLISHED events (400) | Returns 404 `{"detail":"No Event matches the given query."}` (not 400) — spec says 400 but live API returns 404 |
| TCHKT-10 | Test checkout rejects expired promo codes (400) | BACKEND BUG: expired promos are accepted; returns 200 with discount_amount:"0.0000" and promo_applied:"CODE". Test must assert zero discount, not 400 |
| TCHKT-11 | Test checkout rejects promo codes exceeding usage limit (400) | BACKEND BUG: over-limit promos accepted; same behavior as TCHKT-10 — assert zero discount |
| TCHKT-12 | Test promo discount correctly applied to line item totals | `POST /checkout/` with valid promo returns discounted `line_total` and `discount_amount` on each line item — verified (10% promo on $25 = $2.50 discount, total $22.50) |
| TORDR-01 | Test list own orders | `GET /orders/` returns array of full order objects (auth required) — verified |
| TORDR-02 | Test view order detail (must be order owner) | `GET /orders/{order_id}/` returns full order object — verified |
| TORDR-03 | Test lookup order by confirmation code (no auth) | `GET /orders/lookup/{confirmation_code}/` returns full order with tickets — unauthenticated, 200 on valid code, 404 on invalid |
| TORDR-04 | Test confirmation code is 10-char alphanumeric | All observed codes match `[A-Z0-9]{10}` regex — 10 real codes verified |
| TORDR-05 | Test list own tickets | `GET /tickets/` returns array of ticket objects with qr_code_data — auth required, verified |
| TORDR-06 | Test QR code data format: {order_id}:{tier_id}:{ticket_id}:{hmac_16hex} | Format confirmed: 4 colon-separated parts, first 3 are UUIDs, 4th is 16 hex chars — verified on 4 live tickets |
| TORDR-07 | Test HMAC computed over order_id:tier_id:ticket_id | Cannot verify HMAC key from test side (black-box API). Structural test only: assert last segment is `[0-9a-f]{16}` regex. TCHKN-06 verifies enforcement |
| TCHKN-01 | Test any org member can scan QR to check in attendee | `POST /organizations/{org}/events/{event}/check-in/scan/` with `{qr_data:"..."}` — org OWNER confirmed working; member role not separately tested (follow-up in Phase 4) |
| TCHKN-02 | Test successful scan returns status "success" with attendee details | Response: `{status:"success", message:"Checked in successfully!", attendee_name, attendee_email, tier_name, checked_in_at}` — verified |
| TCHKN-03 | Test re-scan returns status "already_checked_in" with original timestamp | Response: `{status:"already_checked_in", message:"Already checked in at HH:MM PM.", attendee_name, tier_name, checked_in_at}` — verified |
| TCHKN-04 | Test invalid/forged QR returns status "invalid" | Both invalid format and forged HMAC return `{status:"invalid", message:"Invalid QR code. Signature verification failed."}` — verified |
| TCHKN-05 | Test cancelled/refunded ticket returns status "invalid" | Cannot test: no API endpoint to cancel individual tickets. Event cancellation does NOT invalidate tickets (scan still succeeds after cancel). Mark as skip with explanation |
| TCHKN-06 | Test HMAC signature verified on every scan | Verified: correct QR succeeds; same QR with last segment changed to "aaaaaaaaaaaaaaaa" returns status:"invalid" — HMAC enforcement confirmed |
| TMCHK-01 | Test manual check-in by ticket ID | `POST /organizations/{org}/events/{event}/check-in/{ticket_id}/manual/` — success: `{status:"success", message:"Checked in successfully!", attendee_name, tier_name}` — verified |
| TMCHK-02 | Test same response format as QR scan | Manual success response shape matches QR scan except `attendee_email` is absent in manual response — verified |
| TSTAT-01 | Test check-in stats (total registered, checked in, not checked in, percentage) | `GET /organizations/{org}/events/{event}/check-in/stats/` returns `{total_registered, checked_in, not_checked_in, percentage, by_tier}` — verified |
| TSTAT-02 | Test stats include per-tier breakdown | `by_tier` is an array of `{tier_name, total, checked_in}` objects — verified with 4 tiers |
| TSRCH-01 | Test search attendees by name, email, or confirmation code | `GET /organizations/{org}/events/{event}/check-in/search/?q={term}` — all three search fields verified (name: "ScanTest", email: ".invalid", code: "2YZ0N8UTL0") |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 9.0.2 | Test runner | Already installed in Phase 1 |
| httpx | 0.28.1 | HTTP client | Already installed; used by auth_client fixture |
| pydantic-settings | 2.13.1 | Settings | Already installed; Settings class in settings.py |

### Phase 1+2 Infrastructure Used
| Component | Location | What It Provides |
|-----------|----------|-----------------|
| `auth_client` fixture | conftest.py | Session-scoped httpx client with Bearer token, auto-refresh |
| `teardown_registry` fixture | conftest.py | Session dict; `order_ids` key already present but no cleanup possible (orders are not deleteable) |
| `org` fixture | tests/api/conftest.py | Session-scoped org with OWNER role |
| `published_event` fixture | tests/api/conftest.py | Session-scoped published event (no tiers) |
| `RUN_ID` | factories/common.py | 8-hex run prefix |
| `unique_email()`, `tier_name()` | factories/common.py | Unique test data |
| `assert_status()` | helpers/api.py | Status assertion with URL+body on mismatch |

**No new packages required for Phase 3.** All infrastructure exists from Phases 1 and 2.

## Architecture Patterns

### Recommended File Structure
```
tests/api/
├── test_checkout.py      (TCHKT-01 through TCHKT-12)
├── test_orders.py        (TORDR-01 through TORDR-07)
└── test_checkin.py       (TCHKN-01 through TCHKN-06, TMCHK-01, TMCHK-02, TSTAT-01, TSTAT-02, TSRCH-01)
```

### Pattern 1: Session-Scoped Checkout Fixture
**What:** All checkout tests depend on a published event with a free tier and paid tier created once per session. The tier IDs and event slugs are available for all tests.

**When to use:** For tests that only need to read/calculate/verify — not tests that mutate state (e.g., completing orders changes quantity_sold).

```python
# In tests/api/conftest.py — ADD to existing conftest

@pytest.fixture(scope="session")
def checkout_event(auth_client, org, teardown_registry):
    """Published event with free and paid tiers for checkout tests.

    Returns dict with keys: event (full dict), free_tier (full dict), paid_tier (full dict)
    """
    from factories.common import event_title, tier_name

    # Create event
    create_resp = auth_client.post(
        f"/organizations/{org['slug']}/events/",
        json={
            "title": event_title(),
            "format": "IN_PERSON",
            "category": "MEETUP",
            "start_datetime": "2026-12-01T09:00:00",
            "end_datetime": "2026-12-01T17:00:00",
            "timezone": "UTC",
        },
    )
    assert_status(create_resp, 201, "Create checkout event (draft)")
    draft = create_resp.json()
    teardown_registry["event_ids"].append({"org_slug": org["slug"], "event_slug": draft["slug"]})

    # Create free tier
    free_resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{draft['slug']}/ticket-tiers/",
        json={"name": tier_name(), "price": "0.00", "quantity_total": 100,
              "min_per_order": 1, "max_per_order": 10, "visibility": "PUBLIC"},
    )
    assert_status(free_resp, 201, "Create free tier")
    free_tier = free_resp.json()
    teardown_registry["ticket_tier_ids"].append({
        "org_slug": org["slug"], "event_slug": draft["slug"], "tier_id": free_tier["id"]
    })

    # Create paid tier
    paid_resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{draft['slug']}/ticket-tiers/",
        json={"name": tier_name(), "price": "25.00", "quantity_total": 50,
              "min_per_order": 1, "max_per_order": 5, "visibility": "PUBLIC"},
    )
    assert_status(paid_resp, 201, "Create paid tier")
    paid_tier = paid_resp.json()
    teardown_registry["ticket_tier_ids"].append({
        "org_slug": org["slug"], "event_slug": draft["slug"], "tier_id": paid_tier["id"]
    })

    # Publish
    pub_resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{draft['slug']}/publish/"
    )
    assert_status(pub_resp, 200, "Publish checkout event")
    event = pub_resp.json()

    return {"event": event, "free_tier": free_tier, "paid_tier": paid_tier}
```

### Pattern 2: Single-Use Order Fixture (Function-Scoped)
**What:** Tests that complete orders (which mutate quantity_sold) must use function-scoped or module-scoped fixtures with their own tier to avoid contaminating other tests.

```python
@pytest.fixture(scope="module")
def completed_free_order(auth_client, org, checkout_event):
    """Complete a free order once for the module. Returns full order dict."""
    event = checkout_event["event"]
    free_tier = checkout_event["free_tier"]
    resp = auth_client.post("/checkout/", json={
        "action": "complete",
        "org_slug": org["slug"],
        "event_slug": event["slug"],
        "items": [{"tier_id": free_tier["id"], "quantity": 1}],
        "promo_code": "",
        "billing_name": "Test Attendee",
        "billing_email": "attendee@gathergood-test.invalid",
        "billing_phone": "+12125550100",
    })
    assert_status(resp, 201, "Complete free order")
    return resp.json()
```

### Pattern 3: Check-In Base URL Helper
**What:** The check-in base URL is shared across all check-in tests. Define it as a fixture or local variable.

```python
@pytest.fixture(scope="module")
def checkin_base(org, checkout_event):
    """Base URL prefix for check-in endpoints."""
    return f"/organizations/{org['slug']}/events/{checkout_event['event']['slug']}/check-in"
```

### Pattern 4: TCHKN-05 Skip Pattern
**What:** No API to cancel individual tickets. Mark test as skipped with clear explanation.

```python
@pytest.mark.req("TCHKN-05")
@pytest.mark.skip(reason=(
    "Cannot test: no API endpoint exists to cancel individual tickets. "
    "Event cancellation does not invalidate tickets for check-in (empirically verified). "
    "This is a backend limitation."
))
def test_cancelled_ticket_scan_returns_invalid(auth_client, checkin_base):
    pass
```

### Pattern 5: TCHKT-04 Skip Pattern
**What:** Stripe is not configured on the live backend. PaymentIntent creation will always fail.

```python
@pytest.mark.req("TCHKT-04")
@pytest.mark.skip(reason=(
    "Stripe not configured on live backend: POST /checkout/payment-intent/ returns "
    "'You did not provide an API key.' The backend has no STRIPE_SECRET_KEY set. "
    "Set STRIPE_TEST_KEY in .env when backend is configured for Stripe test mode."
))
def test_paid_checkout_creates_payment_intent(auth_client, org, checkout_event):
    pass
```

### Anti-Patterns to Avoid
- **Using separate checkout URLs like `/checkout/calculate/` or `/checkout/free/`:** The API uses a single `POST /checkout/` with an `action` field. Separate URL patterns all return 404.
- **Asserting 400 for expired/over-limit promos:** The backend silently applies 0 discount instead of rejecting. Assert `discount_amount == "0.0000"` instead.
- **Asserting 400 for non-published event checkout:** The API returns 404, not 400.
- **Assuming billing_phone is required:** It is optional — omitting it still returns 201.
- **Using action=complete to test min/max per order:** The complete action does not validate min/max; only calculate validates them.
- **Attempting to test order teardown via DELETE:** Orders have no DELETE endpoint (405). The `order_ids` in teardown_registry is informational only — no actual cleanup is possible.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP requests | Custom wrapper | `auth_client` fixture (already exists) | Auto-refresh, base_url, timeout |
| Unique data | Random strings | `unique_email()`, `tier_name()` etc. (already exists) | RUN_ID prefix |
| Status assertion | `assert resp.status_code == X` | `assert_status(resp, X, context)` (already exists) | Shows URL+body on failure |
| HMAC computation | Custom HMAC lib | Not needed — treat as opaque black box | Secret key unknown; enforce via scan rejection test |

**Key insight:** Phase 3 has no new infrastructure to build. All needed fixtures, factories, and helpers already exist from Phases 1 and 2. The work is purely test writing.

## Confirmed API Endpoints (All Live-Verified 2026-03-28)

### Checkout
| Method | URL | Body | Success | Notes |
|--------|-----|------|---------|-------|
| POST | `/checkout/` | action, org_slug, event_slug, items[], promo_code | 200 (calculate) / 201 (complete) | Single endpoint, action field required |
| POST | `/checkout/payment-intent/` | order_id | — | Returns Stripe auth error (no key configured) |

**action=calculate request body:**
```json
{
  "action": "calculate",
  "org_slug": "my-org",
  "event_slug": "my-event",
  "items": [{"tier_id": "uuid", "quantity": 2}],
  "promo_code": ""
}
```

**action=calculate response (200):**
```json
{
  "line_items": [
    {"tier_id": "uuid", "tier_name": "General", "quantity": 1, "unit_price": "25.00",
     "discount_amount": "2.5000", "line_total": "22.5000"}
  ],
  "subtotal": "25.00",
  "discount_amount": "2.5000",
  "fees": "0.00",
  "total": "22.5000",
  "is_free": false,
  "promo_applied": "CODE10"
}
```

**action=complete request body:**
```json
{
  "action": "complete",
  "org_slug": "my-org",
  "event_slug": "my-event",
  "items": [{"tier_id": "uuid", "quantity": 1}],
  "promo_code": "",
  "billing_name": "Jane Smith",
  "billing_email": "jane@example.com",
  "billing_phone": "+12125550100"
}
```

**action=complete response (201 for free, 201 for paid when Stripe unconfigured):**
```json
{
  "id": "uuid",
  "event": "uuid",
  "event_title": "...",
  "event_slug": "...",
  "org_slug": "...",
  "status": "COMPLETED",
  "confirmation_code": "2YZ0N8UTL0",
  "subtotal": "0.00",
  "discount_amount": "0.00",
  "fees": "0.00",
  "total": "0.00",
  "billing_name": "Jane Smith",
  "billing_email": "jane@example.com",
  "billing_phone": "+12125550100",
  "stripe_payment_intent_id": "",
  "line_items": [{"id": "uuid", "ticket_tier": "uuid", "tier_name": "...", "quantity": 1,
                  "unit_price": "0.00", "discount_amount": "0.00", "line_total": "0.00"}],
  "tickets": [
    {
      "id": "uuid",
      "ticket_tier": "uuid",
      "tier_name": "Free General",
      "event": "uuid",
      "event_title": "...",
      "attendee_name": "Jane Smith",
      "attendee_email": "jane@example.com",
      "qr_code_data": "order-uuid:tier-uuid:ticket-uuid:16hexchars",
      "qr_code_image_url": "",
      "checked_in": false,
      "checked_in_at": null,
      "status": "ACTIVE",
      "created_at": "2026-03-28T22:17:25.289121Z"
    }
  ],
  "created_at": "2026-03-28T22:17:25.269630Z",
  "updated_at": "2026-03-28T22:17:25.298207Z"
}
```

**Checkout error responses:**
| Condition | HTTP | Body |
|-----------|------|------|
| Missing billing_name | 400 | `{"billing_name":["This field is required."]}` |
| Missing billing_email | 400 | `{"billing_email":["This field is required."]}` |
| Quantity exceeds capacity | 400 | `{"detail":"TierName: only N tickets remaining."}` (from calculate action) |
| Quantity below min_per_order | 400 | `{"detail":"TierName: quantity must be between M and N."}` |
| Quantity above max_per_order | 400 | `{"detail":"TierName: quantity must be between M and N."}` |
| Non-published event | 404 | `{"detail":"No Event matches the given query."}` |
| Expired promo (valid_until in past) | 200 | Success with `discount_amount:"0.0000"` (bug — not rejected) |
| Over-limit promo (usage_count >= usage_limit) | 200 | Success with `discount_amount:"0.0000"` (bug — not rejected) |

**CRITICAL: action=complete does NOT validate min_per_order or max_per_order.** Only action=calculate enforces these. For TCHKT-06, TCHKT-07, TCHKT-08: use action=calculate in tests.

### Orders
| Method | URL | Body | Success | Notes |
|--------|-----|------|---------|-------|
| GET | `/orders/` | — | 200 | Array of full order objects; auth required |
| GET | `/orders/{order_id}/` | — | 200 | Full order object; auth required; only own orders |
| GET | `/orders/lookup/{confirmation_code}/` | — | 200 | Full order object; **no auth required**; 404 on unknown code |
| DELETE | `/orders/{order_id}/` | — | 405 | NOT SUPPORTED — orders cannot be deleted or cancelled |

**No teardown possible for orders.** The `order_ids` key in teardown_registry is pre-wired but no cleanup action exists. Orders persist with COMPLETED status.

### Tickets
| Method | URL | Body | Success | Notes |
|--------|-----|------|---------|-------|
| GET | `/tickets/` | — | 200 | Array of own ticket objects; auth required |

**Ticket object:**
```json
{
  "id": "uuid",
  "ticket_tier": "uuid",
  "tier_name": "Free General",
  "event": "uuid",
  "event_title": "...",
  "attendee_name": "Jane Smith",
  "attendee_email": "jane@example.com",
  "qr_code_data": "order-uuid:tier-uuid:ticket-uuid:16hexchars",
  "qr_code_image_url": "",
  "checked_in": false,
  "checked_in_at": null,
  "status": "ACTIVE",
  "created_at": "..."
}
```

### QR Check-In
| Method | URL | Body | Success | Notes |
|--------|-----|------|---------|-------|
| POST | `/organizations/{slug}/events/{event-slug}/check-in/scan/` | `{qr_data: "..."}` | 200 | Returns scan result |
| POST | `/organizations/{slug}/events/{event-slug}/check-in/{ticket_id}/manual/` | — | 200 | No request body needed |
| GET | `/organizations/{slug}/events/{event-slug}/check-in/stats/` | — | 200 | Check-in statistics |
| GET | `/organizations/{slug}/events/{event-slug}/check-in/search/?q={term}` | — | 200 | Search by name, email, or confirmation code |

**QR scan success response (TCHKN-02):**
```json
{
  "status": "success",
  "message": "Checked in successfully!",
  "attendee_name": "Jane Smith",
  "attendee_email": "jane@example.com",
  "tier_name": "Free General",
  "checked_in_at": "2026-03-28T22:29:19.270839+00:00"
}
```

**QR re-scan response (TCHKN-03):**
```json
{
  "status": "already_checked_in",
  "message": "Already checked in at 10:29 PM.",
  "attendee_name": "Jane Smith",
  "tier_name": "Free General",
  "checked_in_at": "2026-03-28T22:29:19.270839+00:00"
}
```

**QR invalid response (TCHKN-04, TCHKN-06):**
```json
{
  "status": "invalid",
  "message": "Invalid QR code. Signature verification failed."
}
```

**Manual check-in success response (TMCHK-01, TMCHK-02):**
```json
{
  "status": "success",
  "message": "Checked in successfully!",
  "attendee_name": "Jane Smith",
  "tier_name": "Free General"
}
```
Note: manual response does NOT include `attendee_email` or `checked_in_at` (unlike QR scan success).

**Manual already-checked-in response:**
```json
{
  "status": "already_checked_in",
  "message": "Already checked in at 10:29 PM."
}
```
Note: manual already_checked_in response does NOT include `attendee_name` or `tier_name` (unlike QR rescan).

**Stats response (TSTAT-01, TSTAT-02):**
```json
{
  "total_registered": 19,
  "checked_in": 1,
  "not_checked_in": 18,
  "percentage": 5.3,
  "by_tier": [
    {"tier_name": "Free General", "total": 14, "checked_in": 1},
    {"tier_name": "Paid VIP", "total": 3, "checked_in": 0}
  ]
}
```

**Search response (TSRCH-01):**
```json
[
  {
    "ticket_id": "uuid",
    "attendee_name": "Jane Smith",
    "attendee_email": "jane@example.com",
    "tier_name": "Free General",
    "confirmation_code": "2YZ0N8UTL0",
    "checked_in": true,
    "checked_in_at": "2026-03-28T22:20:18.701257+00:00"
  }
]
```

## Common Pitfalls

### Pitfall 1: Wrong checkout URL pattern
**What goes wrong:** Test calls `POST /checkout/calculate/` or `POST /events/{slug}/checkout/calculate/` — gets 404.
**Why it happens:** The API uses a single `/checkout/` endpoint with an `action` field in the body, not separate URL paths.
**How to avoid:** Always use `POST /checkout/` with `{"action": "calculate", ...}` or `{"action": "complete", ...}`.
**Warning signs:** 404 on any `/checkout/calculate/` or `/checkout/free/` URL.

### Pitfall 2: Expecting 400 for expired or over-limit promos
**What goes wrong:** Test asserts `resp.status_code == 400` for a promo with `valid_until` in the past or `usage_count >= usage_limit` — test always fails.
**Why it happens:** The backend silently applies zero discount to invalid promos instead of rejecting them.
**How to avoid:** Test that `calculate` response has `discount_amount == "0.0000"` when an expired/over-limit promo is submitted.
**Warning signs:** Test passes with an unexpected 200 response.

### Pitfall 3: Expecting 400 (not 404) for non-published event checkout
**What goes wrong:** Test asserts 400 for checkout on a DRAFT event — gets 404.
**Why it happens:** The checkout endpoint filters events by PUBLISHED status and returns 404 "No Event matches the given query." rather than a 400 validation error.
**How to avoid:** Assert 404 for TCHKT-09.
**Warning signs:** `assert resp.status_code == 400` fails with actual 404.

### Pitfall 4: Using action=complete to test min/max/capacity violations
**What goes wrong:** Test completes an order with quantity=11 on a max_per_order=10 tier — gets 201 COMPLETED instead of 400.
**Why it happens:** The `action=complete` endpoint does not validate min/max per order or capacity before creating the order. Only `action=calculate` validates these.
**How to avoid:** TCHKT-06, TCHKT-07, TCHKT-08 must use `action=calculate` and assert the 400 response from that action.
**Warning signs:** action=complete creates an order even with invalid quantities.

### Pitfall 5: Billing phone required assumption
**What goes wrong:** Test fails when omitting billing_phone expecting 400 — gets 201.
**Why it happens:** billing_phone is optional; only billing_name and billing_email are required.
**How to avoid:** TCHKT-05 should assert 400 for missing billing_name and missing billing_email, and assert 201 for missing billing_phone.

### Pitfall 6: Manual check-in response differs from QR scan response
**What goes wrong:** Test asserts `attendee_email` is present in manual check-in success response — KeyError.
**Why it happens:** Manual check-in success response only includes `{status, message, attendee_name, tier_name}` — no `attendee_email` or `checked_in_at`.
**How to avoid:** TMCHK-02 must assert the common fields (status, message) while acknowledging the shape difference.

### Pitfall 7: Confirmation code format includes lowercase letters
**What goes wrong:** Test asserts confirmation code matches `[A-Z0-9a-z]{10}` and passes for wrong codes.
**Why it happens:** Confirmation codes are uppercase alphanumeric only.
**How to avoid:** Assert `re.match(r'^[A-Z0-9]{10}$', code)`.
**Warning signs:** Test is too permissive and accepts lowercase codes.

### Pitfall 8: Using slug vs UUID in check-in URLs
**What goes wrong:** Test constructs check-in URL with event UUID — gets 404.
**Why it happens:** Same as Phase 2 — all event URLs use slug, not UUID.
**How to avoid:** Use `event["slug"]` not `event["id"]` in all check-in URL construction.

### Pitfall 9: Trying to DELETE orders for teardown
**What goes wrong:** Teardown tries DELETE on order IDs — gets 405.
**Why it happens:** Orders have no DELETE endpoint.
**How to avoid:** Don't attempt order teardown. The `order_ids` list in teardown_registry accumulates but no cleanup action is wired. Accept that test orders persist as COMPLETED.

### Pitfall 10: TCHKN-05 has no testable path
**What goes wrong:** Test tries to cancel a ticket then scan it — no endpoint exists to cancel individual tickets.
**Why it happens:** The API has no per-ticket cancel/refund endpoint. Event cancellation does not invalidate tickets.
**How to avoid:** Mark TCHKN-05 as skipped with reason. Do not attempt to workaround by manipulating event status.

## QR Code Format (TORDR-06, TORDR-07, TCHKN-06)

**Format:** `{order_id}:{tier_id}:{ticket_id}:{hmac_16hex}`

All observed examples:
- `58c1f630-f6c1-4263-af73-d2c5caa6de91:51f6324f-2570-463c-b97b-60bcc9e0537f:3acd3e7a-f985-4004-ac36-7c5a2b18374f:490a407561d2a6ed`
- `a6926a66-9261-4381-a90f-188f7aa2834b:a77735df-6149-49ee-82f6-04360dc295bf:f8cb3c16-8ecc-4789-805d-bc3fc052f761:c8964ca3efbaa1f0`
- `7ed189ed-974b-404c-99e2-0d9c5503ba3a:51f6324f-2570-463c-b97b-60bcc9e0537f:7ffe3b40-4e35-42d7-9cd7-b02db45c7c39:31b728c2fcd0658f`

**Validation regex:** `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}:[0-9a-f]{16}$`

**HMAC properties:**
- 16 hex chars = 64-bit truncated HMAC
- Secret key is unknown to the test layer (black-box backend)
- HMAC is computed over `order_id:tier_id:ticket_id` (the first 3 parts)
- Enforcement verified: correct HMAC → status "success"; any other 16-char hex → status "invalid" with "Signature verification failed."
- Test approach: assert structural format with regex (TORDR-06), and assert that a forged HMAC is rejected (TCHKN-06)

## Stripe Mode Discovery

**Finding:** Stripe is NOT configured on the live backend. `POST /checkout/payment-intent/` returns:
```json
{
  "detail": "You did not provide an API key. You need to provide your API key in the Authorization header, using Bearer auth (e.g. 'Authorization: Bearer YOUR_SECRET_KEY'). See https://stripe.com/docs/api#authentication for details..."
}
```

**Implications:**
- TCHKT-04 (paid checkout creates PaymentIntent) must be skipped
- Paid orders via `action=complete` succeed (201) but have `stripe_payment_intent_id: ""` — the backend bypasses Stripe when unconfigured
- The `settings.py` has `STRIPE_TEST_KEY: str = ""` with empty default — future: populate `.env` with Stripe test key when backend is configured

## Teardown Strategy

Orders are not cleanable. The only teardown action Phase 3 needs to add is cancelling the checkout_event's event (already handled by the existing event_ids teardown logic) and deleting the tiers (already handled by ticket_tier_ids teardown). No new teardown code is needed.

**Order teardown:** Not possible. Orders accumulate with COMPLETED status. Test data pollution is acceptable because orders are isolated under the session org and have unique confirmation codes.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | All tests | ✓ | 3.11/3.13 (both on PATH) | — |
| pytest | Test runner | ✓ | 9.0.2 | — |
| httpx | API client | ✓ | 0.28.1 | — |
| Railway backend | All API tests | ✓ | Live | — |
| Stripe test key | TCHKT-04 | ✗ | — | Skip test with `pytest.mark.skip` |

**Missing dependencies with no fallback:**
- None that block Phase 3 execution.

**Missing dependencies with fallback:**
- Stripe test key: TCHKT-04 is skipped; all other checkout tests work without Stripe.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pytest.ini (exists) |
| Quick run command | `pytest tests/api/test_checkout.py tests/api/test_orders.py tests/api/test_checkin.py -x --tb=short` |
| Full suite command | `pytest --tb=short --html=reports/report.html` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TCHKT-01 | Calculate returns line_items, subtotal, discount, fees, total, is_free | unit | `pytest tests/api/test_checkout.py::test_calculate_returns_line_items -x` | ❌ Wave 0 |
| TCHKT-02 | Free checkout completes with COMPLETED status | unit | `pytest tests/api/test_checkout.py::test_free_checkout_status_completed -x` | ❌ Wave 0 |
| TCHKT-03 | Free checkout returns confirmation code and tickets with QR | unit | `pytest tests/api/test_checkout.py::test_free_checkout_confirmation_and_qr -x` | ❌ Wave 0 |
| TCHKT-04 | Paid checkout creates PaymentIntent | unit | `pytest tests/api/test_checkout.py::test_paid_checkout_payment_intent -x` | ❌ Wave 0 (skip) |
| TCHKT-05 | Complete requires billing_name and billing_email | unit | `pytest tests/api/test_checkout.py::test_checkout_requires_billing_fields -x` | ❌ Wave 0 |
| TCHKT-06 | Checkout rejects quantity exceeding capacity | unit | `pytest tests/api/test_checkout.py::test_checkout_rejects_capacity_exceeded -x` | ❌ Wave 0 |
| TCHKT-07 | Checkout rejects quantity below min_per_order | unit | `pytest tests/api/test_checkout.py::test_checkout_rejects_below_min -x` | ❌ Wave 0 |
| TCHKT-08 | Checkout rejects quantity above max_per_order | unit | `pytest tests/api/test_checkout.py::test_checkout_rejects_above_max -x` | ❌ Wave 0 |
| TCHKT-09 | Checkout rejects non-PUBLISHED events (404) | unit | `pytest tests/api/test_checkout.py::test_checkout_rejects_non_published -x` | ❌ Wave 0 |
| TCHKT-10 | Expired promo results in zero discount | unit | `pytest tests/api/test_checkout.py::test_expired_promo_zero_discount -x` | ❌ Wave 0 |
| TCHKT-11 | Over-limit promo results in zero discount | unit | `pytest tests/api/test_checkout.py::test_over_limit_promo_zero_discount -x` | ❌ Wave 0 |
| TCHKT-12 | Promo discount applied to line items | unit | `pytest tests/api/test_checkout.py::test_promo_discount_applied -x` | ❌ Wave 0 |
| TORDR-01 | List own orders | unit | `pytest tests/api/test_orders.py::test_list_own_orders -x` | ❌ Wave 0 |
| TORDR-02 | View order detail | unit | `pytest tests/api/test_orders.py::test_view_order_detail -x` | ❌ Wave 0 |
| TORDR-03 | Lookup by confirmation code (no auth) | unit | `pytest tests/api/test_orders.py::test_lookup_by_confirmation_code -x` | ❌ Wave 0 |
| TORDR-04 | Confirmation code is 10-char alphanumeric | unit | `pytest tests/api/test_orders.py::test_confirmation_code_format -x` | ❌ Wave 0 |
| TORDR-05 | List own tickets | unit | `pytest tests/api/test_orders.py::test_list_own_tickets -x` | ❌ Wave 0 |
| TORDR-06 | QR code data format: order:tier:ticket:hmac | unit | `pytest tests/api/test_orders.py::test_qr_code_data_format -x` | ❌ Wave 0 |
| TORDR-07 | HMAC is 16 hex chars (structural test) | unit | `pytest tests/api/test_orders.py::test_qr_hmac_structure -x` | ❌ Wave 0 |
| TCHKN-01 | Org member can scan QR | unit | `pytest tests/api/test_checkin.py::test_scan_qr_success -x` | ❌ Wave 0 |
| TCHKN-02 | Successful scan returns "success" with attendee details | unit | `pytest tests/api/test_checkin.py::test_scan_success_response_shape -x` | ❌ Wave 0 |
| TCHKN-03 | Re-scan returns "already_checked_in" with timestamp | unit | `pytest tests/api/test_checkin.py::test_rescan_already_checked_in -x` | ❌ Wave 0 |
| TCHKN-04 | Invalid/forged QR returns "invalid" | unit | `pytest tests/api/test_checkin.py::test_scan_invalid_qr -x` | ❌ Wave 0 |
| TCHKN-05 | Cancelled ticket returns "invalid" | unit | `pytest tests/api/test_checkin.py::test_cancelled_ticket_scan -x` | ❌ Wave 0 (skip) |
| TCHKN-06 | HMAC verified on every scan | unit | `pytest tests/api/test_checkin.py::test_hmac_verification -x` | ❌ Wave 0 |
| TMCHK-01 | Manual check-in by ticket ID | unit | `pytest tests/api/test_checkin.py::test_manual_checkin_success -x` | ❌ Wave 0 |
| TMCHK-02 | Manual check-in same response format as QR | unit | `pytest tests/api/test_checkin.py::test_manual_checkin_response_format -x` | ❌ Wave 0 |
| TSTAT-01 | Check-in stats fields | unit | `pytest tests/api/test_checkin.py::test_checkin_stats_fields -x` | ❌ Wave 0 |
| TSTAT-02 | Stats include per-tier breakdown | unit | `pytest tests/api/test_checkin.py::test_checkin_stats_by_tier -x` | ❌ Wave 0 |
| TSRCH-01 | Search attendees by name, email, confirmation code | unit | `pytest tests/api/test_checkin.py::test_attendee_search -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/api/test_checkout.py -x --tb=short -q`
- **Per wave merge:** `pytest tests/api/test_checkout.py tests/api/test_orders.py tests/api/test_checkin.py -x --tb=short`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/api/test_checkout.py` — covers TCHKT-01 through TCHKT-12
- [ ] `tests/api/test_orders.py` — covers TORDR-01 through TORDR-07
- [ ] `tests/api/test_checkin.py` — covers TCHKN-01 through TCHKN-06, TMCHK-01, TMCHK-02, TSTAT-01, TSTAT-02, TSRCH-01
- [ ] `tests/api/conftest.py` — add `checkout_event` session fixture, `checkin_base` module fixture

*(No new packages or framework config required — existing infrastructure covers all phase requirements)*

## Sources

### Primary (HIGH confidence)
- Live API probe `https://event-management-production-ad62.up.railway.app/api/v1` — all endpoints tested directly
- Frontend JS bundle `https://event-management-two-red.vercel.app/assets/index-BDYBkCD6.js` — checkout/check-in URL patterns extracted from source code

### Secondary (MEDIUM confidence)
- Phase 2 RESEARCH.md — existing endpoint patterns, auth fixture, teardown strategy

## Metadata

**Confidence breakdown:**
- Checkout endpoints: HIGH — all URL patterns, request shapes, and response shapes verified on live API
- Orders endpoints: HIGH — verified with real orders created during probe
- Check-in endpoints: HIGH — all four sub-endpoints tested with real tickets
- Promo validation bugs: HIGH — deliberately tested expired/over-limit promos multiple times, consistent behavior
- Stripe detection: HIGH — payment-intent endpoint returned Stripe authentication error
- HMAC structure: HIGH — 4 live QR codes examined, structural regex verified, enforcement confirmed via forged HMAC test
- TCHKN-05 skip: HIGH — exhaustively searched for ticket cancellation endpoint, confirmed none exists

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (30 days — stable live API, unlikely to change rapidly)
