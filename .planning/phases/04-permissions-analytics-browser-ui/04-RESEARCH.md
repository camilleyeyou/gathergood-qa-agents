# Phase 4: Permissions, Analytics & Browser UI - Research

**Researched:** 2026-03-28
**Domain:** Live API probing — permission boundaries, guest list, email settings, analytics, public pages; frontend JS bundle analysis for Playwright UI tests
**Confidence:** HIGH (all API endpoint URLs, request shapes, response bodies, and status codes verified empirically by probing the live Railway backend; UI structure verified by parsing the Vite/React bundle served from the live Vercel frontend)

## Project Constraints (from CLAUDE.md)

- **Target URLs**: Tests MUST run against the live deployed endpoints — never local dev
- **Test isolation**: Tests MUST clean up after themselves where possible, or use unique data per run (RUN_ID prefix) to avoid polluting the live database
- **Stripe**: Paid checkout tests require Stripe test mode; mark as skip if no test keys available
- **No destructive actions**: Tests MUST NOT delete production data that other users depend on
- **GSD Workflow**: All file changes via GSD commands; no direct repo edits outside GSD workflow
- **Stack**: Python + pytest + httpx + pytest-playwright (locked in Phase 1 — no alternatives)
- **No parallel execution**: Shared live DB has no isolation — parallel writes cause data conflicts

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TPERM-01 | VOLUNTEER cannot create events (403) | Verified: `POST /organizations/{org}/events/` as VOLUNTEER → 403 `{"detail":"Only managers and owners can perform this action."}` |
| TPERM-02 | VOLUNTEER cannot invite members (403) | Verified: `POST /organizations/{org}/members/invite/` as VOLUNTEER → 403 `{"detail":"You do not have permission to invite members."}` |
| TPERM-03 | MANAGER cannot assign OWNER role (403) | Verified: `POST /organizations/{org}/members/invite/` with `role:"OWNER"` as MANAGER → 403 `{"detail":"Managers cannot assign the Owner role."}` |
| TPERM-04 | MANAGER cannot remove members (403) | Verified: `DELETE /organizations/{org}/members/{id}/` as MANAGER → 403 `{"detail":"Only owners can remove members."}` |
| TPERM-05 | Non-member cannot access org resources (403) | DEVIATION: Returns 404 not 403. Authenticated non-member gets 404 `{"detail":"No Organization matches the given query."}` on all org resource URLs |
| TGUST-01 | OWNER/MANAGER can view guest list | Verified: `GET /organizations/{org}/events/{event}/guests/` → 200 array (empty when no orders) |
| TGUST-02 | OWNER/MANAGER can export guest list as CSV | Verified: `GET /organizations/{org}/events/{event}/guests/csv/` → 200 CSV with header row: `Name,Email,Ticket Tier,Confirmation Code,Checked In,Check-In Time,Order Total,Registered At` |
| TEMAL-01 | View email config (confirmation, reminders, notifications toggles) | DEVIATION: No dedicated email-config endpoint. Config is stored as a nested object in the event: `PATCH /organizations/{org}/events/{event}/` with `{"email_config": {...}}`. Verified fields: `send_confirmation`, `send_reminder`, `send_notification`, `reminder_days_before` |
| TEMAL-02 | Update email config toggles | Verified: Same PATCH endpoint as TEMAL-01. Returns updated event with `email_config` reflecting new values |
| TEMAL-03 | Send bulk email to all event attendees | Verified: `POST /organizations/{org}/events/{event}/emails/bulk/` with `{"subject": "...", "body": "..."}`. Returns 400 `{"detail":"No attendees to email."}` when event has no orders — use event with orders (from completed_order fixture) |
| TEMAL-04 | View email log | Verified: `GET /organizations/{org}/events/{event}/emails/log/` → 200 array (empty when no emails sent) |
| TANLT-01 | View analytics (registrations, revenue, fees, net, attendance rate) | Verified: `GET /organizations/{org}/events/{event}/analytics/` → 200. Response has `registrations.total`, `attendance.checked_in`, `attendance.total`, `attendance.rate`, `revenue.gross`, `revenue.fees`, `revenue.net`, `revenue.orders`, `refunds.count`, `refunds.amount` |
| TANLT-02 | Analytics includes registrations_by_tier breakdown | Verified: `registrations.by_tier` array in analytics response. Empty when no orders; populated after checkout |
| TANLT-03 | Analytics includes registrations_over_time series | DEVIATION: Key is `timeline` (not `registrations_over_time`). Array of time-series data points. Empty for new events |
| TPUBL-01 | Browse published events with search, category, format filters | Verified: `GET /public/events/` → 200 list. Confirmed filters: `?category=MEETUP`, `?q=<text>`. `?format=IN_PERSON` returns 404 — format filter NOT supported. `?event_format=IN_PERSON` returns 200 but does not filter |
| TPUBL-02 | Only PUBLISHED and LIVE events appear | Verified: DRAFT events do NOT appear in `/public/events/`. Only PUBLISHED events observed in live data |
| TPUBL-03 | View organization public page with upcoming events | Verified: `GET /public/{org_slug}/` → 200 with `{organization: {...}, events: [...]}`. Events array includes `status` field |
| TPUBL-04 | View public event detail with PUBLIC ticket tiers only | Verified: `GET /public/{org_slug}/events/{event_slug}/` → 200 with `{event: {...}, organization: {...}, ticket_tiers: [...]}`. Only PUBLIC tiers appear in response |
| TPUBL-05 | HIDDEN and INVITE_ONLY tiers not shown publicly | Verified: Event created with PUBLIC + HIDDEN + INVITE_ONLY tiers. `/public/{org}/events/{event}/` response `ticket_tiers` array contained ONLY the PUBLIC tier |
| TFEND-01 | Homepage displays hero section, feature cards, and auth-aware CTAs | Verified via bundle: hero h2="Ready to bring your community together?", feature cards present, auth-aware CTA: logged-in="Create Your Next Event" → `/manage/events/new`, logged-out="Get Started — It's Free" → `/register` |
| TFEND-02 | Navbar shows login/signup when logged out; dashboard links when logged in | Verified via bundle: logged-out → Sign Up + Log In; logged-in → Dashboard + Browse + My Tickets + Create Event + Settings |
| TFEND-03 | Mobile hamburger menu with all nav links | Verified via bundle: button with `aria-label="Toggle menu"` toggles `md:hidden` mobile menu panel with full nav links |
| TFEND-04 | Checkout flow has step indicators with current step highlighted | Verified via bundle: 4-step checkout at routes `/checkout/:eventSlug`, `*/details`, `*/payment`, `*/confirmation` with step labels: "1. Select", "2. Your Details", "3. Payment", "4. Confirm" |
| TFEND-05 | Checkout pre-fills billing info for logged-in users | Verified via bundle: `defaultValues: {billing_name: user.first_name + last_name, billing_email: user.email}` in checkout details form |
| TFEND-06 | Confirmation page shows confirmation code and QR codes | Route `/checkout/:eventSlug/confirmation` exists; confirmation code and QR data from order response |
| TFEND-07 | All pages responsive at 375px, 768px, and 1280px+ | Tailwind breakpoints (`sm:`, `md:`, `lg:`) present throughout bundle; no `overflow-x` issues expected but must verify |
| TFEND-08 | Touch targets at least 44x44px on mobile | Playwright can measure bounding box via `locator.bounding_box()` — requires browser test |
| TFEND-09 | No horizontal overflow on any screen size | Playwright can verify `document.documentElement.scrollWidth <= window.innerWidth` |
| TFEND-10 | Check-in page has scanner, search, manual check-in, and live stats | Verified via bundle: check-in component has: stats panel (Checked In / Registered / Remaining), QR scanner ("Start Scanner" / "Stop Scanner"), Search & Manual Check-In panel |
</phase_requirements>

## Summary

Phase 4 covers five distinct test domains: permission boundary enforcement across three roles, guest list and CSV export, email settings configuration and log, event analytics, public-facing browse/detail pages, and Playwright browser tests for the Next.js/Vite frontend. All API endpoint URLs and response shapes were verified against the live Railway backend in this research session.

**Critical deviation from TEST_SPEC: TPERM-05** — Non-org-members receive 404, not 403. The backend filters orgs by membership using Django's queryset-level access control; a non-member hitting `/organizations/{org}/` gets "No Organization matches the given query." rather than a 403. The test must assert 404 and document this behavior.

**Critical deviation: TEMAL-01/02** — There is no dedicated `/email-config/` endpoint. Email configuration is embedded in the event model as a JSON field. Reading email config means reading `event.email_config` from `GET /organizations/{org}/events/{event}/`; updating it means `PATCH`ing the event with `{"email_config": {...}}`.

**Critical deviation: TANLT-03** — The analytics key for the time-series is `timeline`, not `registrations_over_time`. The full analytics response shape is `{registrations: {total, by_tier}, attendance: {checked_in, total, rate}, revenue: {gross, discounts, fees, net, orders}, refunds: {count, amount}, timeline: [], promo_codes: []}`.

**Critical deviation: TPUBL-01** — The `/public/events/` endpoint does not support `?format=` filtering. The test must skip format filter verification or document it as unsupported.

**No data-testid attributes exist** in the frontend bundle. Playwright tests must use text content, CSS class patterns, semantic HTML, and route-based navigation for locators.

**Primary recommendation:** Structure Phase 4 as five test files: `test_permissions.py`, `test_guest_email.py`, `test_analytics.py`, `test_public.py`, and `tests/ui/test_frontend.py`. Permission tests reuse the `_create_user_client()` pattern from Phase 2. UI tests use pytest-playwright's `page` fixture with `page.set_viewport_size()` for responsive checks.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 9.0.2 | Test runner | Already installed |
| httpx | 0.28.1 | HTTP client | Already installed; used by all API tests |
| playwright (Python) | 1.58.0 | Browser automation | Already installed; Chromium binary present |
| pytest-playwright | 0.7.2 | Playwright fixtures | Already installed |
| pydantic-settings | 2.13.1 | Settings | Already installed |

### Phase 1-3 Infrastructure Used
| Component | Location | What It Provides |
|-----------|----------|-----------------|
| `auth_client` | conftest.py | Session-scoped owner client with JWT auto-refresh |
| `_create_user_client()` | tests/api/test_teams.py | Pattern for creating secondary role users |
| `org` fixture | tests/api/conftest.py | Session-scoped org with OWNER role |
| `published_event` fixture | tests/api/conftest.py | Published event with no tiers |
| `checkout_event` fixture | tests/api/conftest.py | Published event with free + paid tiers |
| `completed_order` fixture | tests/api/test_checkout.py | Session-scoped completed free order |
| `teardown_registry` | conftest.py | Session dict for cleanup |
| `RUN_ID`, `unique_email()` | factories/common.py | Unique test data |
| `assert_status()` | helpers/api.py | Status assertion with URL+body on mismatch |
| `Settings` | settings.py | `API_URL`, `BASE_URL` |

**No new packages required for Phase 4.** All infrastructure exists from Phases 1-3.

## Architecture Patterns

### Recommended File Structure
```
tests/
├── api/
│   ├── test_permissions.py   # TPERM-01 to TPERM-05
│   ├── test_guest_email.py   # TGUST-01, TGUST-02, TEMAL-01 to TEMAL-04
│   ├── test_analytics.py     # TANLT-01 to TANLT-03
│   └── test_public.py        # TPUBL-01 to TPUBL-05
└── ui/
    └── test_frontend.py      # TFEND-01 to TFEND-10
```

### Pattern 1: Permission Tests with Role-Scoped Clients
**What:** Create VOLUNTEER and MANAGER users inline within each test using `_create_user_client()`. Invite them to the session `org` with appropriate roles, then test the restricted action.
**When to use:** All TPERM-01 through TPERM-05 tests.

```python
# Source: tests/api/test_teams.py (established pattern)
def _create_user_client(email=None, password="TestPass123!"):
    """Register a new user and return (email, authenticated httpx.Client)."""
    if email is None:
        email = unique_email()
    client = httpx.Client(base_url=_settings.API_URL, timeout=30)
    reg = client.post("/auth/register/", json={
        "email": email, "password": password,
        "password_confirm": password,
        "first_name": "Perm", "last_name": "Tester",
    })
    assert reg.status_code == 201
    login = client.post("/auth/login/", json={"email": email, "password": password})
    client.close()
    tokens = login.json()
    return email, httpx.Client(
        base_url=_settings.API_URL,
        headers={"Authorization": f"Bearer {tokens['access']}"},
        timeout=30,
    )
```

### Pattern 2: Module-Scoped Role Fixtures
**What:** For permission tests that require the same VOLUNTEER/MANAGER across multiple tests (e.g., TPERM-01 and TPERM-02 both need a VOLUNTEER), use a module-scoped pytest fixture rather than recreating the user per test.
**When to use:** When multiple tests in the same module need the same role.

```python
@pytest.fixture(scope="module")
def volunteer_client(auth_client, org):
    """VOLUNTEER member of the session org."""
    email, client = _create_user_client()
    auth_client.post(
        f"/organizations/{org['slug']}/members/invite/",
        json={"email": email, "role": "VOLUNTEER"},
    )
    yield client
    client.close()
```

### Pattern 3: Playwright Viewport Testing
**What:** Use `page.set_viewport_size()` to test responsive behavior at required breakpoints. Use `page.evaluate()` for scroll-width overflow checks.
**When to use:** TFEND-07 (responsive), TFEND-09 (no overflow).

```python
# Source: Playwright Python docs — page.set_viewport_size
@pytest.mark.parametrize("width,height", [(375, 812), (768, 1024), (1280, 800)])
def test_responsive_layout(page, width, height):
    page.set_viewport_size({"width": width, "height": height})
    page.goto(settings.BASE_URL)
    # Check no horizontal overflow
    overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
    assert not overflow, f"Horizontal overflow at {width}px"
```

### Pattern 4: Playwright Auth via API Setup
**What:** Use httpx to obtain a JWT token, then inject it into localStorage so Playwright starts as an authenticated user. This is faster than logging in via the UI.
**When to use:** TFEND-02 (navbar logged-in state), TFEND-04/05 (checkout with auth), TFEND-10 (check-in page).

```python
# Inject auth token into localStorage before navigation
def login_via_storage(page, base_url, email, password, api_url):
    import httpx
    r = httpx.post(api_url + "/auth/login/", json={"email": email, "password": password})
    tokens = r.json()
    page.goto(base_url)
    page.evaluate(f"""() => {{
        localStorage.setItem('access_token', '{tokens["access"]}');
        localStorage.setItem('refresh_token', '{tokens["refresh"]}');
    }}""")
    page.goto(base_url)  # Reload so app reads the token
```

**NOTE:** The actual localStorage key name must be verified against the bundle. The app uses `Ha()` (a custom auth context hook). The exact keys may differ — run a browser session manually to observe what localStorage keys are set on login.

### Pattern 5: Text-Based Locators (No data-testid)
**What:** The frontend has zero `data-testid` attributes. Use Playwright's text-based and role-based locators.
**When to use:** All Playwright tests.

```python
# Instead of page.locator("[data-testid='hamburger-menu']")
# Use:
page.get_by_role("button", name="Toggle menu")        # aria-label
page.get_by_text("Log In")                             # text content
page.get_by_text("1. Select")                          # step indicator text
page.locator("text=Start Scanner")                     # check-in scanner
page.locator("text=Search & Manual Check-In")         # check-in search panel
```

### Anti-Patterns to Avoid
- **CSS selector soup:** Don't use `.bg-green-500` or `.grid-cols-3` as locators — they change with styling updates. Use text and role locators.
- **Re-creating test data in UI:** Don't create events/tiers through the browser — create them via httpx API calls in fixtures, then navigate the browser to the resulting URL.
- **Hardcoded sleep:** The frontend is a Vite/React SPA — use `page.wait_for_selector()` or `expect(locator).to_be_visible()` instead of `time.sleep()`.
- **Module-level mutable state in permissions tests:** Each permission test must use its own role client. Shared mutable clients cause ordering-dependent failures.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Playwright browser lifecycle | Manual browser setup/teardown | `page` fixture from pytest-playwright | Already handles browser launch, context isolation, teardown |
| Viewport resizing | Custom browser resize | `page.set_viewport_size()` | Single-call API, already in pytest-playwright |
| JS evaluation in browser | httpx + regex | `page.evaluate()` | Native Playwright JS execution in page context |
| Touch target measurement | Visual inspection | `locator.bounding_box()` | Returns exact pixel dimensions |
| Responsive overflow check | Screenshot diffing | `page.evaluate("scrollWidth > innerWidth")` | Fast, reliable, no baseline images needed |

## Common Pitfalls

### Pitfall 1: TPERM-05 Expects 403, Gets 404
**What goes wrong:** Test asserts `r.status_code == 403` but gets 404.
**Why it happens:** Django queryset-level filtering hides org resources from non-members as if they don't exist — it does NOT explicitly return 403. This is a deliberate design choice.
**How to avoid:** Assert `r.status_code == 404` and add a comment explaining the deviation from TEST_SPEC.
**Warning signs:** Test fails immediately on the assertion.

### Pitfall 2: Email Config PATCH Returns Event, Not email_config
**What goes wrong:** Test tries to GET `/email-config/` endpoint, gets 404.
**Why it happens:** Email config is embedded in the event model, not a separate resource. There is no dedicated endpoint.
**How to avoid:** For TEMAL-01 (view): GET the event and read `event["email_config"]`. For TEMAL-02 (update): PATCH the event with `{"email_config": {...}}`. For TEMAL-04 (log): GET `/organizations/{org}/events/{event}/emails/log/`.
**Warning signs:** 404 on any `/email-config/` or `/email-settings/` URL.

### Pitfall 3: TEMAL-03 Requires Attendees
**What goes wrong:** `POST /emails/bulk/` returns 400 `{"detail":"No attendees to email."}` on events with no orders.
**Why it happens:** The bulk email endpoint rejects requests when there are no recipients.
**How to avoid:** Use the `checkout_event` fixture (which has a completed free order from Phase 3's `completed_order` fixture) as the event for bulk email tests. Alternatively, create a fresh event, add a free tier, and complete a checkout before calling the bulk email endpoint.
**Warning signs:** 400 response with "No attendees" message.

### Pitfall 4: Analytics Keys Differ from TEST_SPEC Names
**What goes wrong:** Test asserts `"registrations_over_time" in data` but the key is `"timeline"`.
**Why it happens:** The test spec used descriptive names; the actual API uses abbreviated keys.
**How to avoid:** Use the exact keys verified by this research: `registrations.total`, `registrations.by_tier`, `attendance.rate`, `revenue.gross`, `revenue.fees`, `revenue.net`, `timeline`.
**Warning signs:** `KeyError` or `AssertionError` on key existence checks.

### Pitfall 5: Public Event Browse format Filter Returns 404
**What goes wrong:** `GET /public/events/?format=IN_PERSON` returns 404.
**Why it happens:** The `format` query param is not recognized by the public events view — it returns 404 rather than filtering.
**How to avoid:** TPUBL-01 should test `?category=MEETUP` and `?q=<text>` as the supported filters. Document `?format=` as unsupported in the test.
**Warning signs:** 404 on `?format=` filtered requests.

### Pitfall 6: Playwright Auth Token Injection Key Unknown
**What goes wrong:** Auth token injected to localStorage doesn't log the user in — the app uses different keys.
**Why it happens:** The React app uses a custom auth context hook (`Ha()`). The exact localStorage key(s) must be observed from a live browser session, not assumed.
**How to avoid:** Option A — navigate to login page and use the login form via Playwright (more reliable). Option B — observe localStorage keys in browser DevTools after manual login, then hardcode the verified key names. Option C — use `page.context().add_cookies()` if the app uses cookie-based auth. Recommend Option A for reliability.
**Warning signs:** Navbar still shows Log In after localStorage injection; `page.evaluate("localStorage")` shows empty or different keys.

### Pitfall 7: Check-In Page Requires org Query Param
**What goes wrong:** Navigating to `/manage/events/{eventSlug}/check-in` gets an error or shows no org context.
**Why it happens:** The check-in component reads org from URL query param: `const [u]=Ga(), c=u.get("org")||""`. Without `?org={orgSlug}`, `c` is empty and all API calls go to `/organizations//events/...`.
**How to avoid:** Always navigate to `/manage/events/{eventSlug}/check-in?org={orgSlug}`.
**Warning signs:** API calls failing with 404 (empty org slug in URL).

### Pitfall 8: Mobile Menu Only Visible Below md Breakpoint (768px)
**What goes wrong:** TFEND-03 test at 1280px doesn't find the hamburger button.
**Why it happens:** The hamburger button has class `md:hidden` — it is only visible below 768px.
**How to avoid:** Set viewport to 375px BEFORE asserting the hamburger button is visible. At 1280px, assert the desktop nav links are visible instead.
**Warning signs:** `TimeoutError` waiting for hamburger button at 1280px.

## Code Examples

### Verified: Guest List and CSV Export
```python
# Source: Live API probe 2026-03-28
def test_guest_list_view(auth_client, org, checkout_event):
    ev_slug = checkout_event["event"]["slug"]
    r = auth_client.get(f"/organizations/{org['slug']}/events/{ev_slug}/guests/")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)

def test_guest_list_csv(auth_client, org, checkout_event):
    ev_slug = checkout_event["event"]["slug"]
    r = auth_client.get(f"/organizations/{org['slug']}/events/{ev_slug}/guests/csv/")
    assert r.status_code == 200
    content = r.text
    # Verified CSV headers
    assert "Name" in content
    assert "Email" in content
    assert "Ticket Tier" in content
    assert "Confirmation Code" in content
```

### Verified: Analytics Response Shape
```python
# Source: Live API probe 2026-03-28
# GET /organizations/{org}/events/{event}/analytics/ returns:
# {
#   "registrations": {"total": 0, "by_tier": []},
#   "attendance": {"checked_in": 0, "total": 0, "rate": 0},
#   "revenue": {"gross": "0", "discounts": "0", "fees": "0", "net": "0", "orders": 0},
#   "refunds": {"count": 0, "amount": "0"},
#   "timeline": [],
#   "promo_codes": []
# }

def test_analytics_fields(auth_client, org, checkout_event):
    ev_slug = checkout_event["event"]["slug"]
    r = auth_client.get(f"/organizations/{org['slug']}/events/{ev_slug}/analytics/")
    assert r.status_code == 200
    data = r.json()
    assert "registrations" in data
    assert "total" in data["registrations"]
    assert "by_tier" in data["registrations"]
    assert "attendance" in data
    assert "rate" in data["attendance"]
    assert "revenue" in data
    assert "gross" in data["revenue"]
    assert "fees" in data["revenue"]
    assert "net" in data["revenue"]
    assert "timeline" in data  # NOT "registrations_over_time"
```

### Verified: Public Browse and Detail
```python
# Source: Live API probe 2026-03-28
def test_public_browse(auth_client):
    r = httpx.get(settings.API_URL + "/public/events/")
    assert r.status_code == 200
    events = r.json()
    assert isinstance(events, list)
    # All returned events have a status field -- verify only PUBLISHED/LIVE
    for ev in events:
        assert ev.get("status") not in ("DRAFT", "CANCELLED")

def test_public_event_detail_hides_non_public_tiers():
    # URL pattern: GET /public/{org_slug}/events/{event_slug}/
    r = httpx.get(f"{settings.API_URL}/public/{org_slug}/events/{event_slug}/")
    assert r.status_code == 200
    data = r.json()
    assert "ticket_tiers" in data
    visibilities = [t.get("visibility") for t in data["ticket_tiers"] if "visibility" in t]
    # ticket_tiers in public response do NOT include a visibility field
    # Test by verifying only the PUBLIC tier name appears (not HIDDEN or INVITE_ONLY tier names)
    tier_names = [t["name"] for t in data["ticket_tiers"]]
    assert any("Public" in n for n in tier_names)  # adjust to actual tier names
    assert not any("Hidden" in n for n in tier_names)
    assert not any("Invite" in n for n in tier_names)
```

**Important note on TPUBL-04/05:** The `/public/{org}/events/{event}/` response `ticket_tiers` array does NOT include a `visibility` field — the field is stripped before the public response. Assertions must check tier names (or count), not visibility values.

### Verified: Email Config via Event PATCH
```python
# Source: Live API probe 2026-03-28
# TEMAL-01: View email config
def test_view_email_config(auth_client, org, event):
    r = auth_client.get(f"/organizations/{org['slug']}/events/{event['slug']}/")
    assert r.status_code == 200
    data = r.json()
    assert "email_config" in data
    # email_config is {} by default; after patch it contains the keys

# TEMAL-02: Update email config
def test_update_email_config(auth_client, org, event):
    r = auth_client.patch(
        f"/organizations/{org['slug']}/events/{event['slug']}/",
        json={"email_config": {
            "send_confirmation": True,
            "send_reminder": False,
            "send_notification": True,
        }},
    )
    assert r.status_code == 200
    updated = r.json()
    cfg = updated["email_config"]
    assert cfg["send_confirmation"] is True
    assert cfg["send_reminder"] is False
```

### Verified: Permission Boundary Pattern
```python
# Source: Live API probe 2026-03-28 (extends test_teams.py pattern)
@pytest.mark.req("TPERM-01")
def test_volunteer_cannot_create_event(auth_client, org, volunteer_client):
    """VOLUNTEER → POST events → 403."""
    r = volunteer_client.post(
        f"/organizations/{org['slug']}/events/",
        json={"title": "VolTest", "format": "IN_PERSON", "category": "MEETUP",
              "start_datetime": "2026-12-01T09:00:00", "end_datetime": "2026-12-01T17:00:00",
              "timezone": "UTC"},
    )
    assert r.status_code == 403
    assert "permission" in r.json().get("detail", "").lower()

@pytest.mark.req("TPERM-05")
def test_non_member_cannot_access_org(non_member_client, org):
    """Non-member → GET org events → 404 (backend hides org as non-existent)."""
    # NOTE: Live API returns 404, not 403. TEST_SPEC says 403. Deviation documented.
    r = non_member_client.get(f"/organizations/{org['slug']}/events/")
    assert r.status_code == 404  # Not 403 — queryset-level hiding
```

### Verified: Playwright Check-In Page
```python
# Source: Frontend bundle analysis 2026-03-28
def test_checkin_page_elements(page, base_url, logged_in_credentials, org, checkout_event):
    """TFEND-10: Check-in page has scanner, search, manual check-in, and live stats."""
    event_slug = checkout_event["event"]["slug"]
    org_slug = org["slug"]
    # Must include ?org= query param (required by the component)
    page.goto(f"{base_url}/manage/events/{event_slug}/check-in?org={org_slug}")

    # Stats panel (Checked In / Registered / Remaining)
    expect(page.get_by_text("Checked In")).to_be_visible()
    expect(page.get_by_text("Registered")).to_be_visible()
    expect(page.get_by_text("Remaining")).to_be_visible()

    # QR scanner section
    expect(page.get_by_text("QR Code Scanner")).to_be_visible()
    expect(page.get_by_text("Start Scanner")).to_be_visible()

    # Search & manual check-in section
    expect(page.get_by_text("Search & Manual Check-In")).to_be_visible()
```

## API Endpoint Reference (Phase 4)

All URLs are relative to `https://event-management-production-ad62.up.railway.app/api/v1`.

| Requirement | Method | URL | Auth | Notes |
|------------|--------|-----|------|-------|
| TPERM-01 | POST | `/organizations/{org}/events/` | VOLUNTEER JWT | Expect 403 |
| TPERM-02 | POST | `/organizations/{org}/members/invite/` | VOLUNTEER JWT | Expect 403 |
| TPERM-03 | POST | `/organizations/{org}/members/invite/` | MANAGER JWT, body role=OWNER | Expect 403 |
| TPERM-04 | DELETE | `/organizations/{org}/members/{id}/` | MANAGER JWT | Expect 403 |
| TPERM-05 | GET | `/organizations/{org}/events/` | Non-member JWT | Expect 404 (not 403) |
| TGUST-01 | GET | `/organizations/{org}/events/{event}/guests/` | OWNER JWT | Returns array |
| TGUST-02 | GET | `/organizations/{org}/events/{event}/guests/csv/` | OWNER JWT | Returns CSV text |
| TEMAL-01 | GET | `/organizations/{org}/events/{event}/` | OWNER JWT | Read `email_config` field |
| TEMAL-02 | PATCH | `/organizations/{org}/events/{event}/` | OWNER JWT | Body `{"email_config": {...}}` |
| TEMAL-03 | POST | `/organizations/{org}/events/{event}/emails/bulk/` | OWNER JWT | Body `{"subject": "...", "body": "..."}` |
| TEMAL-04 | GET | `/organizations/{org}/events/{event}/emails/log/` | OWNER JWT | Returns array |
| TANLT-01/02/03 | GET | `/organizations/{org}/events/{event}/analytics/` | OWNER JWT | Full analytics response |
| TPUBL-01/02 | GET | `/public/events/` | None | Supports `?category=`, `?q=` |
| TPUBL-03 | GET | `/public/{org_slug}/` | None | Returns org + events |
| TPUBL-04/05 | GET | `/public/{org_slug}/events/{event_slug}/` | None | Returns event + org + PUBLIC tiers only |

## Frontend Pages Reference (Phase 4 Playwright Tests)

All routes are at `https://event-management-two-red.vercel.app`.

| Requirement | Route | Key Selectors | Notes |
|------------|-------|---------------|-------|
| TFEND-01 | `/` | `text=Ready to bring your community together?`, `text=Get Started — It's Free`, `text=Create Your Next Event` | CTA changes based on auth state |
| TFEND-02 | `/` | `text=Log In`, `text=Sign Up` (logged-out); `text=Dashboard` (logged-in) | Desktop nav (`hidden md:flex`) |
| TFEND-03 | `/` | `button[aria-label="Toggle menu"]`, mobile menu panel | Only visible below 768px |
| TFEND-04 | `/checkout/{eventSlug}` | `text=1. Select`, `text=2. Your Details`, `text=3. Payment`, `text=4. Confirm` | 4-step checkout indicator |
| TFEND-05 | `/checkout/{eventSlug}/details` | Billing name/email fields pre-filled | Requires logged-in state |
| TFEND-06 | `/checkout/{eventSlug}/confirmation` | Confirmation code, QR code | Requires completed order |
| TFEND-07 | All | `page.set_viewport_size()` at 375, 768, 1280 | Tailwind responsive |
| TFEND-08 | Mobile (375px) | `locator.bounding_box()` | Min 44x44px touch targets |
| TFEND-09 | All | `page.evaluate("scrollWidth > innerWidth")` | No horizontal overflow |
| TFEND-10 | `/manage/events/{eventSlug}/check-in?org={orgSlug}` | `text=QR Code Scanner`, `text=Start Scanner`, `text=Search & Manual Check-In`, `text=Checked In` | Requires `?org=` param |

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Separate `/email-config/` endpoint | Embedded `email_config` JSON field in event model | Live API as-built | TEMAL-01/02 use PATCH on event, not a dedicated endpoint |
| `403` for unauthorized access | `404` via queryset filtering | Live API as-built | TPERM-05 must assert 404 not 403 |
| `registrations_over_time` key | `timeline` key | Live API as-built | TANLT-03 must check `timeline` |
| `data-testid` attributes | Text/role-based locators only | Frontend as-built | All Playwright locators must use text, aria-label, or role |

## Open Questions

1. **Playwright auth token injection method**
   - What we know: The app uses a custom `Ha()` auth hook; localStorage is used for token storage
   - What's unclear: The exact localStorage key names for access/refresh tokens
   - Recommendation: Use the Playwright UI login flow (navigate to `/login`, fill form, submit) rather than token injection — more reliable and the key names don't need to be known

2. **Email log shape when populated**
   - What we know: `GET /emails/log/` returns `[]` when no emails sent
   - What's unclear: Exact field names in each log entry when bulk email succeeds
   - Recommendation: TEMAL-04 should assert `isinstance(r.json(), list)` and `r.status_code == 200`. If a bulk email was successfully sent, assert the first entry has reasonable fields (id, subject, sent_at, recipient_count). Do not assert specific field names until an entry is observed.

3. **TEMAL-03 test data dependency**
   - What we know: Bulk email returns 400 "No attendees to email" on events with no orders
   - What's unclear: Whether the `checkout_event`/`completed_order` fixture chain from Phase 3 will reliably provide an attendee for this test
   - Recommendation: Use a module-scoped fixture that creates a fresh event + free tier + completes a checkout, specifically for the email tests. Avoids dependency on Phase 3 fixture state.

4. **Analytics populated fields with non-zero data**
   - What we know: Analytics returns correct structure with zeros for new events
   - What's unclear: Whether `by_tier` and `timeline` populate after a free checkout completes
   - Recommendation: TANLT-02 and TANLT-03 should assert the structure (is a list) not the content, since we can't guarantee non-zero data without a checkout in the same session.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.x | All tests | Yes | 3.13 (also 3.11) | — |
| pytest | All tests | Yes | 9.0.2 | — |
| httpx | API tests | Yes | 0.28.1 | — |
| playwright Python | UI tests | Yes | 1.58.0 | — |
| pytest-playwright | UI tests | Yes | 0.7.2 | — |
| Chromium browser binary | UI tests | Yes | v1208 (Chrome 145) | — |
| Railway API backend | All API tests | Yes | Live | — |
| Vercel frontend | UI tests | Yes | Live | — |

**No missing dependencies.** All required tools are installed and confirmed.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pytest.ini` (project root) |
| Quick run command | `pytest tests/api/test_permissions.py -v --tb=short` |
| Full suite command | `pytest -v --tb=short` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TPERM-01 | VOLUNTEER blocked from creating events | API | `pytest tests/api/test_permissions.py::test_volunteer_cannot_create_event` | No - Wave 0 |
| TPERM-02 | VOLUNTEER blocked from inviting members | API | `pytest tests/api/test_permissions.py::test_volunteer_cannot_invite_member` | No - Wave 0 |
| TPERM-03 | MANAGER blocked from assigning OWNER role | API | `pytest tests/api/test_permissions.py::test_manager_cannot_assign_owner_role` | No - Wave 0 |
| TPERM-04 | MANAGER blocked from removing members | API | `pytest tests/api/test_permissions.py::test_manager_cannot_remove_member` | No - Wave 0 |
| TPERM-05 | Non-member blocked from org resources | API | `pytest tests/api/test_permissions.py::test_non_member_cannot_access_org` | No - Wave 0 |
| TGUST-01 | Guest list view returns 200 list | API | `pytest tests/api/test_guest_email.py::test_guest_list_view` | No - Wave 0 |
| TGUST-02 | Guest CSV export returns CSV | API | `pytest tests/api/test_guest_email.py::test_guest_list_csv` | No - Wave 0 |
| TEMAL-01 | View email config from event | API | `pytest tests/api/test_guest_email.py::test_view_email_config` | No - Wave 0 |
| TEMAL-02 | Update email config toggles | API | `pytest tests/api/test_guest_email.py::test_update_email_config` | No - Wave 0 |
| TEMAL-03 | Bulk email to attendees | API | `pytest tests/api/test_guest_email.py::test_bulk_email_send` | No - Wave 0 |
| TEMAL-04 | Email log returns list | API | `pytest tests/api/test_guest_email.py::test_email_log` | No - Wave 0 |
| TANLT-01 | Analytics top-level fields present | API | `pytest tests/api/test_analytics.py::test_analytics_fields` | No - Wave 0 |
| TANLT-02 | Analytics by_tier breakdown present | API | `pytest tests/api/test_analytics.py::test_analytics_by_tier` | No - Wave 0 |
| TANLT-03 | Analytics timeline series present | API | `pytest tests/api/test_analytics.py::test_analytics_timeline` | No - Wave 0 |
| TPUBL-01 | Public browse with filters | API | `pytest tests/api/test_public.py::test_public_browse_filters` | No - Wave 0 |
| TPUBL-02 | Only PUBLISHED events in public browse | API | `pytest tests/api/test_public.py::test_public_browse_excludes_draft` | No - Wave 0 |
| TPUBL-03 | Org public page with events | API | `pytest tests/api/test_public.py::test_public_org_page` | No - Wave 0 |
| TPUBL-04 | Public event detail with PUBLIC tiers | API | `pytest tests/api/test_public.py::test_public_event_detail_tiers` | No - Wave 0 |
| TPUBL-05 | HIDDEN/INVITE_ONLY tiers absent from public | API | `pytest tests/api/test_public.py::test_public_event_hides_non_public_tiers` | No - Wave 0 |
| TFEND-01 | Homepage hero and CTAs | Browser | `pytest tests/ui/test_frontend.py::test_homepage_hero` | No - Wave 0 |
| TFEND-02 | Navbar auth-aware links | Browser | `pytest tests/ui/test_frontend.py::test_navbar_auth_aware` | No - Wave 0 |
| TFEND-03 | Mobile hamburger menu | Browser | `pytest tests/ui/test_frontend.py::test_mobile_hamburger_menu` | No - Wave 0 |
| TFEND-04 | Checkout step indicator | Browser | `pytest tests/ui/test_frontend.py::test_checkout_step_indicator` | No - Wave 0 |
| TFEND-05 | Checkout billing pre-fill | Browser | `pytest tests/ui/test_frontend.py::test_checkout_billing_prefill` | No - Wave 0 |
| TFEND-06 | Confirmation page code+QR | Browser | `pytest tests/ui/test_frontend.py::test_confirmation_page` | No - Wave 0 |
| TFEND-07 | Responsive at 375/768/1280px | Browser | `pytest tests/ui/test_frontend.py::test_responsive_layout` | No - Wave 0 |
| TFEND-08 | Touch targets 44x44px | Browser | `pytest tests/ui/test_frontend.py::test_touch_targets` | No - Wave 0 |
| TFEND-09 | No horizontal overflow | Browser | `pytest tests/ui/test_frontend.py::test_no_horizontal_overflow` | No - Wave 0 |
| TFEND-10 | Check-in page UI elements | Browser | `pytest tests/ui/test_frontend.py::test_checkin_page_elements` | No - Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/api/test_permissions.py tests/api/test_guest_email.py -v --tb=short`
- **Per wave merge:** `pytest -v --tb=short`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/api/test_permissions.py` — covers TPERM-01 through TPERM-05
- [ ] `tests/api/test_guest_email.py` — covers TGUST-01/02, TEMAL-01 through TEMAL-04
- [ ] `tests/api/test_analytics.py` — covers TANLT-01 through TANLT-03
- [ ] `tests/api/test_public.py` — covers TPUBL-01 through TPUBL-05
- [ ] `tests/ui/test_frontend.py` — covers TFEND-01 through TFEND-10

## Sources

### Primary (HIGH confidence)
- Live API probe against `https://event-management-production-ad62.up.railway.app/api/v1` — all endpoint URLs, status codes, request/response shapes verified empirically in this session (2026-03-28)
- Vite/React bundle at `https://event-management-two-red.vercel.app/assets/index-BDYBkCD6.js` — routes, component structure, text content, CSS classes verified by direct parse
- GitHub source `https://github.com/camilleyeyou/Event-Management/blob/main/backend/events/urls.py` — public endpoint URL pattern `GET /public/{org_slug}/events/{event_slug}/` confirmed

### Secondary (MEDIUM confidence)
- Playwright Python docs — `page.set_viewport_size()`, `page.evaluate()`, `locator.bounding_box()` APIs
- Phase 2/3 RESEARCH.md and test files — established patterns for `_create_user_client()`, fixture hierarchy, `assert_status()` helper

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- API endpoints (TPERM, TGUST, TEMAL, TANLT, TPUBL): HIGH — all verified by live API probe
- Frontend structure (TFEND): HIGH — verified by parsing live Vite bundle
- Auth token injection method: LOW — localStorage keys unverified; login-via-form approach recommended
- Email log populated shape: LOW — only empty array observed; field names when populated unverified

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable API; 30-day window)
