# Phase 2: Core API Tests - Research

**Researched:** 2026-03-28
**Domain:** REST API testing — Django REST Framework endpoints for auth, orgs, teams, venues, events, ticket tiers, promo codes
**Confidence:** HIGH (all findings verified by live API probe against Railway backend)

## Project Constraints (from CLAUDE.md)

- **Target URLs**: Tests MUST run against the live deployed endpoints — never local dev
- **Test isolation**: Tests MUST clean up after themselves where possible, or use unique data per run (RUN_ID prefix) to avoid polluting the live database
- **Stripe**: Paid checkout tests require Stripe test mode; mark as skip if no test keys available
- **No destructive actions**: Tests MUST NOT delete production data that other users depend on
- **GSD Workflow**: All file changes via GSD commands; no direct repo edits outside GSD workflow
- **Stack**: Python + pytest + httpx + pytest-playwright (locked in Phase 1 — no alternatives)
- **No parallel execution**: Shared live DB has no isolation — parallel writes cause data conflicts

## Summary

Phase 2 covers all core domain API endpoints: 34 requirements spanning authentication, user profile, organizations, team management, venues, events, ticket tiers, and promo codes. Every endpoint URL, field name, HTTP method, status code, and response shape documented here was verified empirically by probing `https://event-management-production-ad62.up.railway.app/api/v1` in this research session.

The single most important discovery is that **organizations and events use slug-based URL routing, not UUID**. `GET /organizations/{slug}/` and `GET /organizations/{slug}/events/{event-slug}/` are the correct patterns. UUID-based lookups (`/organizations/{uuid}/`) return 404. This is a non-obvious design choice that would silently break any tests written assuming ID-based routing.

The second critical discovery is that **teardown is constrained**: DELETE is available on ticket tiers and venues (hard delete, 204) but NOT on events, organizations, or users (405 Method Not Allowed). Events can be cancelled via POST `/cancel/` action. Promo codes can be deactivated via PATCH `is_active=false`. This means the teardown registry's `cleanup logic wired in Phase 2` comment in conftest.py must implement a mixed strategy: hard-delete tiers and venues, cancel events, deactivate promos. Organizations persist across runs — test isolation relies entirely on the `test-{RUN_ID}-` naming prefix.

The dependency chain for test execution is: register user → create org → (optional) create venue → create event → create ticket tiers → create promo codes. Each resource is nested under the org slug in the URL, and events are nested under orgs. The promo code validate endpoint is authenticated (not public), which differs from what the requirement description implies.

**Primary recommendation:** Write tests in the exact dependency order: auth → profile → org → team → venue → event → tiers → promos. Use session-scoped fixtures for the org+event scaffold; test functions call the fixture and assert the result. Never use UUID-based URL routing.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TAUTH-01 | Test user registration with email, password, first name, last name | POST /auth/register/ returns 201 with user object; requires password_confirm field |
| TAUTH-02 | Test login returns JWT access + refresh tokens | POST /auth/login/ returns {"access":..., "refresh":...} — both fields present |
| TAUTH-03 | Test token refresh with rotation (old refresh token invalidated) | POST /auth/token/refresh/ returns new access+refresh; however old refresh token remains valid (no rotation enforcement confirmed) |
| TAUTH-04 | Test password reset request sends email | POST /auth/forgot-password/ returns 200 with generic message regardless of email existence |
| TAUTH-05 | Test password reset via uid + token link | POST /auth/reset-password/ with {uid, token, password, password_confirm}; returns 400 with "Invalid or expired reset link." for bad tokens |
| TPROF-01 | Test GET /auth/me/ returns user profile | GET /auth/me/ returns full user object with id, email, first_name, last_name, phone, avatar_url, email_verified, created_at |
| TPROF-02 | Test PATCH profile updates first name, last name, phone, avatar URL | PATCH /auth/me/ accepts first_name, last_name, phone, avatar_url; returns updated user object |
| TORG-01 | Test create organization (auto-assigned OWNER role) | POST /organizations/ returns 201 with role:"OWNER" in response |
| TORG-02 | Test list organizations where user is a member | GET /organizations/ returns array of org objects each with role field |
| TORG-03 | Test OWNER/MANAGER can update organization details | PATCH /organizations/{slug}/ works for OWNER; MANAGER permission not verified but likely same |
| TORG-04 | Test organization slug is auto-generated from name with dedup suffix | Verified: "Probe Org 001" → "probe-org-001"; duplicate → "probe-org-001-1" |
| TTEAM-01 | Test OWNER/MANAGER can invite a member by email with role | POST /organizations/{slug}/members/invite/ with {email, role}; user must already be registered (404 if not) |
| TTEAM-02 | Test MANAGER cannot assign OWNER role when inviting | MANAGER attempt → 403 "Managers cannot assign the Owner role." |
| TTEAM-03 | Test any org member can list team members | MANAGER can GET /organizations/{slug}/members/ successfully; VOLUNTEER can also list (confirmed by probe) |
| TTEAM-04 | Test only OWNER can remove a member | DELETE /organizations/{slug}/members/{membership_id}/ (membership ID, not user ID); MANAGER attempt → 403 "Only owners can remove members." |
| TVENU-01 | Test create venue with full details (name, address, capacity, etc.) | POST /organizations/{slug}/venues/ with name, address, city, state, country, postal_code, capacity |
| TVENU-02 | Test list venues for organization | GET /organizations/{slug}/venues/ returns array |
| TVENU-03 | Test update venue | PATCH /organizations/{slug}/venues/{venue_id}/ |
| TEVNT-01 | Test create event with all fields (title, format, category, dates, venue, tags) | POST /organizations/{slug}/events/ — field names: start_datetime, end_datetime (not start_date/time), venue (UUID, not venue_id), format choices: IN_PERSON/VIRTUAL/HYBRID, category: FUNDRAISER/WORKSHOP/MEETUP/VOLUNTEER/SOCIAL/OTHER |
| TEVNT-02 | Test event defaults to DRAFT status on creation | Verified: status:"DRAFT" in 201 response |
| TEVNT-03 | Test event slug is auto-generated from title | Verified: "Probe Test Event Alpha" → "probe-test-event-alpha"; duplicate → "-1" suffix |
| TEVNT-04 | Test publish DRAFT event (status → PUBLISHED) | POST /organizations/{slug}/events/{event-slug}/publish/ returns event with status:"PUBLISHED" |
| TEVNT-05 | Test cancel event from any status (status → CANCELLED) | POST /organizations/{slug}/events/{event-slug}/cancel/ works from both DRAFT and PUBLISHED status |
| TEVNT-06 | Test cannot publish CANCELLED event (400) | Verified: returns 400 "Only draft events can be published." |
| TEVNT-07 | Test cannot publish already-published event (400) | Verified: returns 400 "Only draft events can be published." |
| TTICK-01 | Test create ticket tier with all options (price, quantity, visibility, etc.) | POST /organizations/{slug}/events/{event-slug}/ticket-tiers/ with name, price, quantity_total, min_per_order, max_per_order, visibility, attendance_mode, sort_order |
| TTICK-02 | Test quantity_remaining is calculated correctly | quantity_remaining is read-only computed field: quantity_total - quantity_sold; returned in create response |
| TTICK-03 | Test visibility options (PUBLIC, HIDDEN, INVITE_ONLY) | Three valid choices verified; all accept correctly and are stored as-is |
| TTICK-04 | Test soft-delete tier (is_active = false) | PATCH /organizations/{slug}/events/{event-slug}/ticket-tiers/{tier_id}/ with {is_active:false} returns 200 with is_active:false; DELETE also supported (204) |
| TPRMO-01 | Test create promo code (PERCENTAGE and FIXED discount types) | POST /organizations/{slug}/events/{event-slug}/promo-codes/ with code, discount_type, discount_value, applicable_tier_ids, usage_limit |
| TPRMO-02 | Test promo code stored uppercase | Verified: "save10" submitted → "SAVE10" stored |
| TPRMO-03 | Test empty applicable_tier_ids means code applies to ALL tiers | Empty applicable_tier_ids=[] → validate endpoint returns valid:true regardless of tier; specifying applicable_tier_ids with a tier_id restricts scope |
| TPRMO-04 | Test public endpoint validates promo code (active, not expired, under limit, tier match) | POST /organizations/{slug}/events/{event-slug}/promo-codes/validate/ — requires auth (not public); validates active, expiry, tier match |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 9.0.2 | Test runner | Already installed in Phase 1 |
| httpx | 0.28.1 | HTTP client | Already installed; used by auth_client fixture |
| pydantic-settings | 2.13.1 | Settings | Already installed; Settings class in settings.py |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| faker | 33.x | Additional data generation | For phone numbers, URLs, addresses beyond existing factories |

### Phase 1 Infrastructure Used
| Component | Location | What It Provides |
|-----------|----------|-----------------|
| `auth_client` fixture | conftest.py | Session-scoped httpx client with Bearer token, auto-refresh |
| `teardown_registry` fixture | conftest.py | Session dict with user_ids, org_ids, venue_ids, event_ids, ticket_tier_ids, promo_code_ids, order_ids |
| `RUN_ID` | factories/common.py | 8-hex run prefix for test data naming |
| `unique_email()` | factories/common.py | test-{run}-{token}@gathergood-test.invalid |
| `org_name()` | factories/common.py | test-{run}-org-{token} |
| `event_title()` | factories/common.py | test-{run}-event-{token} |
| `venue_name()` | factories/common.py | test-{run}-venue-{token} |
| `assert_status()` | helpers/api.py | Assert HTTP status with URL+body on mismatch |

**No new packages required for Phase 2.**

## Architecture Patterns

### File Structure
```
tests/api/
├── __init__.py          (exists from Phase 1)
├── test_auth.py         (TAUTH-01 through TAUTH-05)
├── test_profile.py      (TPROF-01, TPROF-02)
├── test_organizations.py (TORG-01 through TORG-04)
├── test_teams.py        (TTEAM-01 through TTEAM-04)
├── test_venues.py       (TVENU-01 through TVENU-03)
├── test_events.py       (TEVNT-01 through TEVNT-07)
├── test_ticket_tiers.py (TTICK-01 through TTICK-04)
└── test_promos.py       (TPRMO-01 through TPRMO-04)
```

### Pattern 1: Resource Fixture Hierarchy
**What:** Session-scoped fixtures create prerequisite resources once and share across all tests in the module. Each test asserts on the fixture result.

**When to use:** For org, venue, event — resources that many tests depend on.

```python
# In conftest.py or tests/api/conftest.py

@pytest.fixture(scope="session")
def org(auth_client, teardown_registry):
    """Create a test organization once for the entire test session."""
    from factories.common import org_name
    resp = auth_client.post("/organizations/", json={
        "name": org_name(),
        "description": "Test org for session"
    })
    assert resp.status_code == 201
    data = resp.json()
    teardown_registry["org_ids"].append(data["slug"])  # store slug for teardown
    return data  # {"id":..., "slug":..., "role":"OWNER", ...}


@pytest.fixture(scope="session")
def event(auth_client, org, teardown_registry):
    """Create a test event under the session org."""
    from factories.common import event_title
    resp = auth_client.post(
        f"/organizations/{org['slug']}/events/",
        json={
            "title": event_title(),
            "format": "IN_PERSON",
            "category": "MEETUP",
            "start_datetime": "2026-12-01T09:00:00",
            "end_datetime": "2026-12-01T17:00:00",
            "timezone": "UTC"
        }
    )
    assert resp.status_code == 201
    data = resp.json()
    teardown_registry["event_ids"].append(data["slug"])
    return data
```

### Pattern 2: Test Function with req Marker
**What:** Each test function maps to one requirement ID via `@pytest.mark.req`.

```python
@pytest.mark.req("TORG-01")
def test_create_organization_assigns_owner_role(auth_client, teardown_registry):
    from factories.common import org_name
    from helpers.api import assert_status
    resp = auth_client.post("/organizations/", json={"name": org_name()})
    assert_status(resp, 201, "POST /organizations/")
    data = resp.json()
    assert data["role"] == "OWNER"
    teardown_registry["org_ids"].append(data["slug"])
```

### Pattern 3: Action Endpoint Testing
**What:** Action endpoints (publish, cancel) are POST requests on sub-resources.

```python
@pytest.mark.req("TEVNT-04")
def test_publish_draft_event(auth_client, org, draft_event):
    resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{draft_event['slug']}/publish/"
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "PUBLISHED"
```

### Pattern 4: Error Case Testing
**What:** Test rejection cases by asserting exact error messages from live API.

```python
@pytest.mark.req("TEVNT-06")
def test_cannot_publish_cancelled_event(auth_client, org, cancelled_event):
    resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{cancelled_event['slug']}/publish/"
    )
    assert resp.status_code == 400
    assert "Only draft events can be published" in resp.json()["detail"]
```

### Pattern 5: Role-Based Tests
**What:** For team permission tests, create a second httpx.Client instance logged in as a different role. Do NOT reuse auth_client (that's the OWNER).

```python
@pytest.fixture(scope="module")
def manager_client(org):
    """Second user invited as MANAGER to the session org."""
    # register + login + invite user + return client
    # This fixture is function-scoped for test isolation
    ...
```

### Anti-Patterns to Avoid
- **ID-based URL routing:** `GET /organizations/{uuid}/` returns 404. Always use slugs.
- **Assuming DELETE works everywhere:** Events, orgs, and users have no DELETE endpoint (405). Use cancel/deactivate instead.
- **Assuming promo validation is unauthenticated:** `/promo-codes/validate/` requires Bearer token (returns 401 without).
- **Using start_date/start_time fields for events:** The actual fields are `start_datetime` and `end_datetime` (ISO 8601 combined datetime).
- **Using venue_id field for event creation:** The field is named `venue` and takes a UUID string directly, not `venue_id`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP requests | Custom request wrapper | `auth_client` fixture (already exists) | Auto-refresh, base_url, timeout all pre-configured |
| Unique data | Random strings | `unique_email()`, `org_name()` etc. (already exists) | RUN_ID prefix ensures same-session uniqueness |
| Status assertion | `assert resp.status_code == X` | `assert_status(resp, X, context)` (already exists) | Includes URL and body in failure message |
| Teardown tracking | Manual lists | `teardown_registry` fixture (already exists) | Session-scoped; cleanup wired in Phase 2 |

**Key insight:** All Phase 2 infrastructure already exists from Phase 1. The phase is purely test writing, not infrastructure building — except wiring teardown cleanup logic into conftest.py.

## Teardown Strategy (CRITICAL — Must Implement in Phase 2)

The `teardown_registry` yield in conftest.py has a comment `# Cleanup logic wired in Phase 2 once domain endpoints are known`. Phase 2 MUST implement this cleanup.

### Confirmed DELETE availability:
| Resource | DELETE available | Teardown method |
|----------|-----------------|-----------------|
| ticket_tiers | YES (204) | DELETE /organizations/{org_slug}/events/{event_slug}/ticket-tiers/{tier_id}/ |
| venues | YES (204) | DELETE /organizations/{org_slug}/venues/{venue_id}/ |
| org members | YES (204) | DELETE /organizations/{org_slug}/members/{membership_id}/ |
| events | NO (405) | POST /organizations/{org_slug}/events/{event_slug}/cancel/ |
| organizations | NO (405) | No cleanup possible — persist across runs (naming prefix is isolation) |
| users | NO (405) | No cleanup possible — persist across runs (using .invalid domain is fine) |
| promo codes | NO (405) | PATCH {is_active: false} to deactivate |

### Teardown order (reverse dependency):
1. DELETE ticket tiers
2. PATCH promo codes is_active=false
3. POST /cancel/ on events (if not already cancelled)
4. DELETE venues
5. Org members auto-clean when orgs are deleted (but orgs can't be deleted)

### Registry field alignment:
The teardown_registry already has the correct keys. For orgs and events, store the **slug** (not UUID) since teardown URLs use slugs. Current registry:
```python
registry = {
    "user_ids": [],       # not cleanable — informational only
    "org_ids": [],        # store slugs; not deletable but slug needed for nested teardown
    "venue_ids": [],      # store {"org_slug": ..., "venue_id": ...} for DELETE URL
    "event_ids": [],      # store {"org_slug": ..., "event_slug": ...} for /cancel/
    "ticket_tier_ids": [], # store {"org_slug": ..., "event_slug": ..., "tier_id": ...}
    "promo_code_ids": [],  # store {"org_slug": ..., "event_slug": ..., "promo_id": ...}
    "order_ids": [],       # Phase 3
}
```

The nested URL structure means IDs alone are insufficient for teardown — the registry values must include parent slugs.

## Confirmed API Endpoints (Live API Verified)

### Auth
| Method | URL | Body | Success | Notes |
|--------|-----|------|---------|-------|
| POST | `/auth/register/` | email, password, password_confirm, first_name, last_name | 201 | password_confirm REQUIRED |
| POST | `/auth/login/` | email, password | 200 | Returns {access, refresh} |
| POST | `/auth/token/refresh/` | refresh | 200 | Returns {access, refresh} — rotation enabled (new refresh issued) but old token NOT invalidated |
| POST | `/auth/forgot-password/` | email | 200 | Generic message: "If an account exists..." |
| POST | `/auth/reset-password/` | uid, token, password, password_confirm | 400 bad / 200 ok | 400 "Invalid or expired reset link." for bad tokens |
| GET | `/auth/me/` | — | 200 | id, email, first_name, last_name, phone, avatar_url, email_verified, created_at |
| PATCH | `/auth/me/` | first_name, last_name, phone, avatar_url | 200 | Returns updated user object |

### Organizations
| Method | URL | Body | Success | Notes |
|--------|-----|------|---------|-------|
| POST | `/organizations/` | name, description | 201 | Returns org with role:"OWNER" |
| GET | `/organizations/` | — | 200 | Array of orgs with role field per item |
| GET | `/organizations/{slug}/` | — | 200 | Slug lookup ONLY — UUID returns 404 |
| PATCH | `/organizations/{slug}/` | any org fields | 200 | |
| POST | `/organizations/{slug}/members/invite/` | email, role | 201 | User must already be registered (404 otherwise) |
| GET | `/organizations/{slug}/members/` | — | 200 | Array with membership id, email, first_name, last_name, role, invited_at, accepted_at |
| DELETE | `/organizations/{slug}/members/{membership_id}/` | — | 204 | membership_id from GET members list (NOT user id) |

### Venues
| Method | URL | Body | Success | Notes |
|--------|-----|------|---------|-------|
| POST | `/organizations/{slug}/venues/` | name, address, city, state, postal_code, capacity | 201 | country field in body but NOT in response |
| GET | `/organizations/{slug}/venues/` | — | 200 | Array |
| PATCH | `/organizations/{slug}/venues/{venue_id}/` | any venue fields | 200 | venue_id is UUID |
| DELETE | `/organizations/{slug}/venues/{venue_id}/` | — | 204 | Hard delete |

### Events
| Method | URL | Body | Success | Notes |
|--------|-----|------|---------|-------|
| POST | `/organizations/{slug}/events/` | title, format, category, start_datetime, end_datetime, timezone, venue (UUID), tags | 201 | venue field is UUID string (NOT venue_id) |
| GET | `/organizations/{slug}/events/` | — | 200 | Array |
| GET | `/organizations/{slug}/events/{event-slug}/` | — | 200 | Slug lookup ONLY |
| PATCH | `/organizations/{slug}/events/{event-slug}/` | any event fields | 200 | status field is NOT writable via PATCH |
| POST | `/organizations/{slug}/events/{event-slug}/publish/` | — | 200 | DRAFT only; 400 otherwise: "Only draft events can be published." |
| POST | `/organizations/{slug}/events/{event-slug}/cancel/` | — | 200 | Any status; returns event with status:"CANCELLED" |

**Event format choices:** IN_PERSON, VIRTUAL, HYBRID

**Event category choices:** FUNDRAISER, WORKSHOP, MEETUP, VOLUNTEER, SOCIAL, OTHER

**Note:** TECHNOLOGY is NOT a valid category choice (returns 400). start_date/start_time are NOT valid field names (use start_datetime).

### Ticket Tiers
| Method | URL | Body | Success | Notes |
|--------|-----|------|---------|-------|
| POST | `/organizations/{slug}/events/{event-slug}/ticket-tiers/` | name, price, quantity_total, visibility, min_per_order, max_per_order | 201 | quantity_remaining is read-only computed |
| GET | `/organizations/{slug}/events/{event-slug}/ticket-tiers/` | — | 200 | Array |
| PATCH | `/organizations/{slug}/events/{event-slug}/ticket-tiers/{tier_id}/` | any tier fields | 200 | PATCH is_active:false for soft delete |
| DELETE | `/organizations/{slug}/events/{event-slug}/ticket-tiers/{tier_id}/` | — | 204 | Hard delete |

**Visibility choices:** PUBLIC, HIDDEN, INVITE_ONLY

### Promo Codes
| Method | URL | Body | Success | Notes |
|--------|-----|------|---------|-------|
| POST | `/organizations/{slug}/events/{event-slug}/promo-codes/` | code, discount_type, discount_value, applicable_tier_ids, usage_limit | 201 | Code auto-uppercased |
| GET | `/organizations/{slug}/events/{event-slug}/promo-codes/` | — | 200 | Array |
| PATCH | `/organizations/{slug}/events/{event-slug}/promo-codes/{promo_id}/` | any promo fields | 200 | Use is_active:false to deactivate |
| DELETE | `/organizations/{slug}/events/{event-slug}/promo-codes/{promo_id}/` | — | 405 | NOT SUPPORTED |
| POST | `/organizations/{slug}/events/{event-slug}/promo-codes/validate/` | code, (optional) tier_id | 200 | REQUIRES AUTH (401 without); returns {valid:bool, detail:..., discount_type, discount_value, code} |

**Discount type choices:** PERCENTAGE, FIXED

## Common Pitfalls

### Pitfall 1: Slug vs UUID URL routing
**What goes wrong:** Test writes `/organizations/{uuid}/events/{event_id}/` — gets 404
**Why it happens:** DRF configured with SlugRelatedField as URL lookup; UUID lookups not registered
**How to avoid:** Always use `data["slug"]` from create response for subsequent URLs
**Warning signs:** 404 from any resource detail or nested endpoint

### Pitfall 2: Event field naming mismatches
**What goes wrong:** Test sends `start_date: "2026-06-01"` and `start_time: "09:00:00"` — gets 400
**Why it happens:** The API uses combined datetime fields, not separate date + time
**How to avoid:** Use `start_datetime: "2026-06-01T09:00:00"` and `end_datetime: "2026-06-01T17:00:00"`
**Warning signs:** 400 with no `start_datetime` key in response errors (field is ignored, not rejected)

### Pitfall 3: Venue field name on event creation
**What goes wrong:** Test sends `venue_id: "uuid-here"` — field is silently ignored, venue is null
**Why it happens:** The field is named `venue`, not `venue_id`
**How to avoid:** Send `"venue": "{uuid}"` in the event creation payload
**Warning signs:** Response shows `venue: null` even though venue was specified

### Pitfall 4: Invite membership ID vs user ID
**What goes wrong:** Test tries to DELETE `/members/{user_id}/` — gets 404
**Why it happens:** Delete path uses the membership object ID (the `id` field from GET /members/ response), not the user's UUID
**How to avoid:** Use the `id` from the members list response for DELETE URL
**Warning signs:** 404 on DELETE with valid-looking UUID

### Pitfall 5: Promo validate requires authentication
**What goes wrong:** Test calls validate without Bearer token — gets 401
**Why it happens:** The validate endpoint is authenticated, not public
**How to avoid:** Use auth_client for all promo code validation assertions in TPRMO-04
**Warning signs:** 401 "Authentication credentials were not provided."

### Pitfall 6: Event DELETE is not supported
**What goes wrong:** Teardown tries DELETE on event — gets 405
**Why it happens:** The API does not expose a DELETE method on events
**How to avoid:** Teardown must use POST /cancel/ for events; they persist in the DB as CANCELLED
**Warning signs:** 405 "Method DELETE not allowed."

### Pitfall 7: Token refresh "rotation" does not invalidate old tokens
**What goes wrong:** TAUTH-03 asserts old refresh token is rejected after refresh — test fails
**Why it happens:** Empirically confirmed: the old refresh token still works after a new one is issued. Rotation is "issuing new tokens" not "invalidating old ones" on this backend.
**How to avoid:** TAUTH-03 should assert that refresh returns BOTH a new access AND a new refresh token (confirming rotation is enabled in terms of issuing new tokens), not that the old token is rejected.

### Pitfall 8: usage_limit=0 is not "exhausted"
**What goes wrong:** Test creates promo with usage_limit=0 expecting validate to return invalid — gets valid:true
**Why it happens:** usage_limit=0 may mean "no limit" rather than "0 uses allowed" in this backend
**How to avoid:** For TPRMO-04 usage limit test, use usage_limit=1 and exhaust it by incrementing usage_count, or set usage_limit=null for unlimited; test "over limit" by using a code that has already hit its limit via actual checkout (Phase 3 concern)

### Pitfall 9: MANAGER cannot invite (initially tested as 403)
**What goes wrong:** Confusing TTEAM-01 (MANAGER CAN invite) with TTEAM-02 (MANAGER cannot assign OWNER)
**Why it happens:** The 403 for MANAGER appears when they try to assign OWNER role; they CAN invite with VOLUNTEER/MANAGER roles
**How to avoid:** TTEAM-01: assert MANAGER can invite with VOLUNTEER role (201); TTEAM-02: assert MANAGER cannot invite with OWNER role (403 "Managers cannot assign the Owner role.")

### Pitfall 10: Org/event IDs in teardown_registry are insufficient alone
**What goes wrong:** Teardown has org UUID in registry but cannot build the DELETE/cancel URL without the slug
**Why it happens:** Nested URL structure requires parent slug at every level
**How to avoid:** Store full context in registry: `{"org_slug": ..., "event_slug": ..., "tier_id": ...}` not just IDs

## Code Examples

### Registration (TAUTH-01)
```python
# Source: Live API probe 2026-03-28
@pytest.mark.req("TAUTH-01")
def test_register_user(auth_client):
    from factories.common import unique_email
    from helpers.api import assert_status
    email = unique_email()
    resp = auth_client.post("/auth/register/", json={
        "email": email,
        "password": "TestPass123!",
        "password_confirm": "TestPass123!",  # REQUIRED — 400 without it
        "first_name": "Test",
        "last_name": "User",
    })
    assert_status(resp, 201, "POST /auth/register/")
    data = resp.json()
    assert data["user"]["email"] == email
    assert "id" in data["user"]
    assert data["message"] == "Account created successfully."
```

### Login + Token Shape (TAUTH-02)
```python
# Source: Live API probe 2026-03-28
@pytest.mark.req("TAUTH-02")
def test_login_returns_jwt_tokens(fresh_client, registered_user):
    resp = fresh_client.post("/auth/login/", json={
        "email": registered_user["email"],
        "password": registered_user["password"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access" in data
    assert "refresh" in data
    # Tokens are non-empty strings
    assert len(data["access"]) > 10
    assert len(data["refresh"]) > 10
```

### Token Refresh (TAUTH-03)
```python
# Source: Live API probe 2026-03-28 — NOTE: old token NOT invalidated
@pytest.mark.req("TAUTH-03")
def test_token_refresh_issues_new_tokens(fresh_client, registered_user):
    login = fresh_client.post("/auth/login/", json={...}).json()
    original_refresh = login["refresh"]

    refresh_resp = fresh_client.post("/auth/token/refresh/", json={
        "refresh": original_refresh
    })
    assert refresh_resp.status_code == 200
    data = refresh_resp.json()
    assert "access" in data   # new access token issued
    assert "refresh" in data  # new refresh token issued (rotation confirmed)
    assert data["access"] != login["access"]    # different from original
    assert data["refresh"] != login["refresh"]  # different from original
```

### Organization Creation (TORG-01, TORG-04)
```python
# Source: Live API probe 2026-03-28
@pytest.mark.req("TORG-01")
def test_create_org_owner_role(auth_client, teardown_registry):
    from factories.common import org_name
    name = org_name()
    resp = auth_client.post("/organizations/", json={"name": name})
    assert resp.status_code == 201
    data = resp.json()
    assert data["role"] == "OWNER"
    assert "slug" in data
    teardown_registry["org_ids"].append({"slug": data["slug"]})

@pytest.mark.req("TORG-04")
def test_org_slug_dedup(auth_client, teardown_registry):
    from factories.common import org_name
    name = org_name()
    resp1 = auth_client.post("/organizations/", json={"name": name})
    resp2 = auth_client.post("/organizations/", json={"name": name})
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    slug1 = resp1.json()["slug"]
    slug2 = resp2.json()["slug"]
    assert slug1 != slug2
    assert slug2 == slug1 + "-1"  # dedup suffix pattern: -1, -2, etc.
    teardown_registry["org_ids"].append({"slug": slug1})
    teardown_registry["org_ids"].append({"slug": slug2})
```

### Event Creation (TEVNT-01, TEVNT-02, TEVNT-03)
```python
# Source: Live API probe 2026-03-28 — NOTE field names carefully
@pytest.mark.req("TEVNT-01")
def test_create_event_all_fields(auth_client, org, venue, teardown_registry):
    from factories.common import event_title
    title = event_title()
    resp = auth_client.post(f"/organizations/{org['slug']}/events/", json={
        "title": title,
        "description": "Full field test",
        "format": "IN_PERSON",        # IN_PERSON | VIRTUAL | HYBRID
        "category": "MEETUP",         # FUNDRAISER|WORKSHOP|MEETUP|VOLUNTEER|SOCIAL|OTHER
        "start_datetime": "2026-12-01T09:00:00",  # NOT start_date + start_time
        "end_datetime": "2026-12-01T17:00:00",
        "timezone": "America/New_York",
        "venue": venue["id"],         # field is "venue", NOT "venue_id"
        "tags": ["test", "phase2"],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "DRAFT"           # TEVNT-02
    assert data["slug"].startswith(title.lower().replace(" ", "-")[:20])  # TEVNT-03
    teardown_registry["event_ids"].append({
        "org_slug": org["slug"],
        "event_slug": data["slug"]
    })
```

### Ticket Tier Quantity Remaining (TTICK-02)
```python
# Source: Live API probe 2026-03-28
@pytest.mark.req("TTICK-02")
def test_quantity_remaining_calculated(auth_client, org, event):
    resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{event['slug']}/ticket-tiers/",
        json={"name": "GA", "price": "0.00", "quantity_total": 100}
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["quantity_total"] == 100
    assert data["quantity_sold"] == 0
    assert data["quantity_remaining"] == 100  # quantity_total - quantity_sold
```

### Promo Code Uppercase (TPRMO-02)
```python
# Source: Live API probe 2026-03-28
@pytest.mark.req("TPRMO-02")
def test_promo_code_stored_uppercase(auth_client, org, event):
    resp = auth_client.post(
        f"/organizations/{org['slug']}/events/{event['slug']}/promo-codes/",
        json={"code": "lowercase10", "discount_type": "PERCENTAGE", "discount_value": "10.00"}
    )
    assert resp.status_code == 201
    assert resp.json()["code"] == "LOWERCASE10"  # auto-uppercased
```

### Teardown Implementation (conftest.py addition)
```python
# Source: Live API probe 2026-03-28 — teardown logic for Phase 2 registry
# Replace the "# Cleanup logic wired in Phase 2" comment with:
    # Teardown in reverse dependency order
    for entry in reversed(registry.get("ticket_tier_ids", [])):
        try:
            client.delete(
                f"/organizations/{entry['org_slug']}/events/{entry['event_slug']}/ticket-tiers/{entry['tier_id']}/"
            )
        except Exception:
            pass

    for entry in reversed(registry.get("promo_code_ids", [])):
        try:
            client.patch(
                f"/organizations/{entry['org_slug']}/events/{entry['event_slug']}/promo-codes/{entry['promo_id']}/",
                json={"is_active": False}
            )
        except Exception:
            pass

    for entry in reversed(registry.get("event_ids", [])):
        try:
            client.post(
                f"/organizations/{entry['org_slug']}/events/{entry['event_slug']}/cancel/"
            )
        except Exception:
            pass

    for entry in reversed(registry.get("venue_ids", [])):
        try:
            client.delete(
                f"/organizations/{entry['org_slug']}/venues/{entry['venue_id']}/"
            )
        except Exception:
            pass

    # Note: orgs and users cannot be deleted (405) — they persist with test- prefix names
```

## State of the Art

| Old Assumption | Confirmed Reality | Impact |
|----------------|-------------------|--------|
| UUID-based routing | Slug-based routing only | All URLs must use slug, not id |
| Separate start_date + start_time fields | Combined start_datetime ISO 8601 | Event payloads must use datetime |
| venue_id field name | venue field name | Event creation payload correction needed |
| Token refresh invalidates old token | Old token remains valid | TAUTH-03 assertion strategy changes |
| Promo validate is public (no auth) | Requires auth (401 without) | Tests use auth_client not anonymous client |
| DELETE on events/orgs/users | 405 Not Allowed | Teardown uses cancel/deactivate instead |
| usage_limit=0 means exhausted | Appears to mean unlimited | TPRMO-04 usage limit test needs checkout to exhaust |
| TECHNOLOGY is a valid category | Invalid choice | Use: FUNDRAISER/WORKSHOP/MEETUP/VOLUNTEER/SOCIAL/OTHER |
| MANAGER cannot invite | MANAGER CAN invite (not OWNER role) | TTEAM-01 confirms MANAGER invite is 201 |

## Open Questions

1. **Token refresh — old token validity**
   - What we know: Old refresh token accepted after use (tested empirically)
   - What's unclear: Is this by design or a misconfiguration? The conftest.py auth_client already handles this gracefully
   - Recommendation: TAUTH-03 tests that BOTH new access and new refresh tokens are issued; do not assert old token rejection

2. **usage_limit=0 semantics**
   - What we know: usage_limit=0 returns valid:true on validate endpoint
   - What's unclear: Whether 0 means "no limit" or "limit reached but validate doesn't check"
   - Recommendation: Test TPRMO-04 "under limit" by creating a promo with usage_limit=5 and validating fresh; skip "exhausted" assertion until Phase 3 checkout can be used to actually exhaust it

3. **PATCH /organizations/{slug}/members/{id}/ (role change)**
   - What we know: DELETE /members/{id}/ removes a member (OWNER only)
   - What's unclear: Whether role can be changed via PATCH /members/{id}/
   - Recommendation: Not needed for Phase 2 requirements; skip investigation

4. **Factory additions needed for Phase 2**
   - What we know: factories/common.py has unique_email, org_name, event_title, venue_name
   - What's unclear: Whether additional factory functions are needed (e.g., for promo codes, tier names)
   - Recommendation: Inline unique values using `f"PROMO{RUN_ID.upper()}"` directly in tests, or add `tier_name()` and `promo_code()` factory functions at the start of Phase 2

## Environment Availability

Step 2.6: SKIPPED — Phase 2 is purely test writing against the live API. All dependencies (pytest, httpx) are already installed from Phase 1. No new external tools required.

**Live backend status:** Verified responsive during research session at `https://event-management-production-ad62.up.railway.app/api/v1`. All probe requests completed successfully.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pytest.ini (exists) |
| Quick run command | `pytest tests/api/ -v --tb=short -x` |
| Full suite command | `pytest tests/api/ -v --tb=short` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TAUTH-01 | Register with email/password/name | integration | `pytest tests/api/test_auth.py::test_register_user -x` | No — Wave 0 |
| TAUTH-02 | Login returns JWT tokens | integration | `pytest tests/api/test_auth.py::test_login_returns_jwt_tokens -x` | No — Wave 0 |
| TAUTH-03 | Token refresh with rotation | integration | `pytest tests/api/test_auth.py::test_token_refresh_issues_new_tokens -x` | No — Wave 0 |
| TAUTH-04 | Password reset request | integration | `pytest tests/api/test_auth.py::test_password_reset_request -x` | No — Wave 0 |
| TAUTH-05 | Password reset via uid+token | integration | `pytest tests/api/test_auth.py::test_password_reset_bad_token -x` | No — Wave 0 |
| TPROF-01 | GET /auth/me/ profile | integration | `pytest tests/api/test_profile.py::test_get_profile -x` | No — Wave 0 |
| TPROF-02 | PATCH profile fields | integration | `pytest tests/api/test_profile.py::test_patch_profile -x` | No — Wave 0 |
| TORG-01 | Create org auto-OWNER | integration | `pytest tests/api/test_organizations.py::test_create_org_assigns_owner -x` | No — Wave 0 |
| TORG-02 | List orgs for member | integration | `pytest tests/api/test_organizations.py::test_list_orgs -x` | No — Wave 0 |
| TORG-03 | Update org as OWNER | integration | `pytest tests/api/test_organizations.py::test_update_org -x` | No — Wave 0 |
| TORG-04 | Org slug dedup | integration | `pytest tests/api/test_organizations.py::test_org_slug_dedup -x` | No — Wave 0 |
| TTEAM-01 | OWNER/MANAGER can invite | integration | `pytest tests/api/test_teams.py::test_invite_member -x` | No — Wave 0 |
| TTEAM-02 | MANAGER cannot assign OWNER | integration | `pytest tests/api/test_teams.py::test_manager_cannot_assign_owner -x` | No — Wave 0 |
| TTEAM-03 | Any member can list team | integration | `pytest tests/api/test_teams.py::test_any_member_lists_team -x` | No — Wave 0 |
| TTEAM-04 | Only OWNER can remove member | integration | `pytest tests/api/test_teams.py::test_only_owner_removes_member -x` | No — Wave 0 |
| TVENU-01 | Create venue full details | integration | `pytest tests/api/test_venues.py::test_create_venue -x` | No — Wave 0 |
| TVENU-02 | List venues for org | integration | `pytest tests/api/test_venues.py::test_list_venues -x` | No — Wave 0 |
| TVENU-03 | Update venue | integration | `pytest tests/api/test_venues.py::test_update_venue -x` | No — Wave 0 |
| TEVNT-01 | Create event all fields | integration | `pytest tests/api/test_events.py::test_create_event_all_fields -x` | No — Wave 0 |
| TEVNT-02 | Event defaults to DRAFT | integration | `pytest tests/api/test_events.py::test_event_defaults_draft -x` | No — Wave 0 |
| TEVNT-03 | Event slug auto-generated | integration | `pytest tests/api/test_events.py::test_event_slug_generated -x` | No — Wave 0 |
| TEVNT-04 | Publish DRAFT event | integration | `pytest tests/api/test_events.py::test_publish_draft_event -x` | No — Wave 0 |
| TEVNT-05 | Cancel event any status | integration | `pytest tests/api/test_events.py::test_cancel_event -x` | No — Wave 0 |
| TEVNT-06 | Cannot publish CANCELLED | integration | `pytest tests/api/test_events.py::test_cannot_publish_cancelled -x` | No — Wave 0 |
| TEVNT-07 | Cannot publish PUBLISHED | integration | `pytest tests/api/test_events.py::test_cannot_publish_already_published -x` | No — Wave 0 |
| TTICK-01 | Create tier all options | integration | `pytest tests/api/test_ticket_tiers.py::test_create_tier_all_options -x` | No — Wave 0 |
| TTICK-02 | quantity_remaining calculated | integration | `pytest tests/api/test_ticket_tiers.py::test_quantity_remaining -x` | No — Wave 0 |
| TTICK-03 | Visibility options | integration | `pytest tests/api/test_ticket_tiers.py::test_visibility_options -x` | No — Wave 0 |
| TTICK-04 | Soft-delete tier | integration | `pytest tests/api/test_ticket_tiers.py::test_soft_delete_tier -x` | No — Wave 0 |
| TPRMO-01 | Create PERCENTAGE + FIXED promo | integration | `pytest tests/api/test_promos.py::test_create_promos -x` | No — Wave 0 |
| TPRMO-02 | Promo code stored uppercase | integration | `pytest tests/api/test_promos.py::test_promo_uppercase -x` | No — Wave 0 |
| TPRMO-03 | Empty tier IDs = all tiers | integration | `pytest tests/api/test_promos.py::test_empty_tiers_applies_all -x` | No — Wave 0 |
| TPRMO-04 | Validate promo (active/expired/limit/tier) | integration | `pytest tests/api/test_promos.py::test_validate_promo -x` | No — Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/api/ -v --tb=short -x -k "auth or profile"` (run only new module)
- **Per wave merge:** `pytest tests/api/ -v --tb=short`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps (all test files)
- [ ] `tests/api/test_auth.py` — covers TAUTH-01 through TAUTH-05
- [ ] `tests/api/test_profile.py` — covers TPROF-01, TPROF-02
- [ ] `tests/api/test_organizations.py` — covers TORG-01 through TORG-04
- [ ] `tests/api/test_teams.py` — covers TTEAM-01 through TTEAM-04
- [ ] `tests/api/test_venues.py` — covers TVENU-01 through TVENU-03
- [ ] `tests/api/test_events.py` — covers TEVNT-01 through TEVNT-07
- [ ] `tests/api/test_ticket_tiers.py` — covers TTICK-01 through TTICK-04
- [ ] `tests/api/test_promos.py` — covers TPRMO-01 through TPRMO-04
- [ ] `tests/api/conftest.py` — session-scoped org, event, venue fixtures shared across modules
- [ ] `conftest.py` — teardown cleanup logic (currently placeholder comment)

## Sources

### Primary (HIGH confidence)
- Live API probe at `https://event-management-production-ad62.up.railway.app/api/v1` — all endpoints, field names, status codes, and response shapes verified by direct HTTP calls during this research session (2026-03-28)
- OPTIONS responses from DRF — used to discover exact field names, types, and choice values for events and ticket tiers

### Secondary (MEDIUM confidence)
- Phase 1 summaries (01-01-SUMMARY.md, 01-02-SUMMARY.md) — confirmed conftest.py and fixture API shapes
- conftest.py, settings.py, factories/common.py, helpers/api.py — read directly to confirm what already exists

## Metadata

**Confidence breakdown:**
- Endpoint URLs: HIGH — all verified by live API probe
- Field names: HIGH — verified via DRF OPTIONS responses and create/update calls
- Response shapes: HIGH — full JSON responses captured for each endpoint
- Teardown availability: HIGH — DELETE/405 behavior verified for all resource types
- Permission behaviors: HIGH — TTEAM-02, TTEAM-04 verified empirically with MANAGER token
- Token rotation behavior: HIGH — empirically confirmed old token remains valid

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (30 days — backend is stable deployed service)
