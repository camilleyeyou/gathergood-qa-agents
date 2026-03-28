# Architecture Research

**Domain:** E2E Testing Agent — REST API + Browser UI against Django/Next.js
**Researched:** 2026-03-28
**Confidence:** HIGH (primary components), MEDIUM (specific integration patterns)

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLI Entry Point                               │
│                    python -m pytest / run.py                         │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                     Test Orchestration Layer                          │
│                                                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │  conftest.py     │  │  pytest config  │  │  pytest-playwright  │  │
│  │  (root)          │  │  (pytest.ini /  │  │  plugin             │  │
│  │  session fixtures│  │   pyproject.toml│  │                     │  │
│  └────────┬─────────┘  └────────┬────────┘  └──────────┬──────────┘  │
│           │                     │                       │             │
└───────────┼─────────────────────┼───────────────────────┼─────────────┘
            │                     │                       │
┌───────────▼─────────────────────▼───────────────────────▼─────────────┐
│                         Fixture Layer                                   │
│                                                                         │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │  Auth Fixture     │    │  API Client       │    │  Browser Context  │  │
│  │  (session scope)  │    │  Fixture          │    │  Fixture          │  │
│  │                   │    │  (session scope)  │    │  (function scope) │  │
│  │  - register user  │    │  - httpx client   │    │  - Playwright     │  │
│  │  - login → JWT    │    │  - JWT headers    │    │    browser page   │  │
│  │  - refresh tokens │    │  - base URL       │    │  - storageState   │  │
│  └──────────┬────────┘    └────────┬──────────┘    └────────┬──────────┘  │
│             └────────────┬─────────┘                        │             │
└──────────────────────────┼──────────────────────────────────┼─────────────┘
                           │                                  │
┌──────────────────────────▼──────────────────────────────────▼─────────────┐
│                          Test Suite Layer                                   │
│                                                                             │
│  ┌─────────────────────────────┐    ┌──────────────────────────────────┐   │
│  │    API Test Modules          │    │    Browser UI Test Modules        │   │
│  │    tests/api/                │    │    tests/ui/                      │   │
│  │                              │    │                                   │   │
│  │  test_auth.py                │    │  test_navigation.py               │   │
│  │  test_orgs.py                │    │  test_checkout_ui.py              │   │
│  │  test_events.py              │    │  test_event_detail.py             │   │
│  │  test_checkout.py            │    │  test_responsive.py               │   │
│  │  test_checkin.py             │    │                                   │   │
│  │  ...                         │    │  Uses Page Object Models          │   │
│  └──────────────────────────────┘    └───────────────────────────────── ┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                           │                                  │
┌──────────────────────────▼──────────────────────────────────▼─────────────┐
│                        Support Layer                                        │
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │  Page Objects     │  │  API Helpers     │  │  Data Factories           │  │
│  │  pages/           │  │  helpers/api.py  │  │  factories/               │  │
│  │                   │  │                  │  │                           │  │
│  │  - LoginPage      │  │  - assert_ok()   │  │  - unique_email()         │  │
│  │  - EventPage      │  │  - build_qr_     │  │  - org_payload()          │  │
│  │  - CheckoutPage   │  │    payload()     │  │  - event_payload()        │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼────────────────────────────────────────────────┐
│                        Reporter Layer                                       │
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │  pytest-html      │  │  JUnit XML       │  │  Console Summary          │  │
│  │  (full report)    │  │  (--junitxml)    │  │  (terminal pass/fail)     │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| CLI Entry Point | Trigger full test run with correct options | `pytest tests/ -v --html=report.html` invoked via `Makefile` or `run_tests.py` |
| conftest.py (root) | Session-scoped shared state: auth tokens, API client, browser auth storage | pytest `conftest.py` with `scope="session"` fixtures |
| Auth Fixture | Register/login once per session, cache JWT access + refresh tokens, expose auth headers | `httpx.Client` POST to `/api/v1/auth/register` and `/api/v1/auth/login`, yielded dict |
| API Client Fixture | Pre-configured HTTP client with base URL and Bearer token header | `httpx.Client` or sync `requests.Session` with `Authorization: Bearer {token}` |
| Browser Context Fixture | Playwright browser with auth state pre-loaded via storageState so UI tests skip login UI | `playwright.chromium.launch()` + `browser.new_context(storage_state=...)` |
| API Test Modules | One module per TEST_SPEC domain, each test maps to one requirement ID | pytest test functions using the API client fixture |
| Browser UI Test Modules | Tests for FEND-01 to FEND-10 and checkout UI flows | pytest functions using the page fixture + page object models |
| Page Objects | Encapsulate UI selectors and actions per page/feature | Python classes with `__init__(self, page: Page)`, locator properties, action methods |
| API Helpers | Shared assertion helpers, QR payload builder, response validators | Plain Python functions in `helpers/` |
| Data Factories | Unique-per-run test data to avoid live DB pollution | Functions returning dicts with `uuid4` or timestamp-suffixed values |
| Reporter | Pass/fail output with requirement ID tagging | `pytest-html`, `--junitxml`, console `-v` output |

## Recommended Project Structure

```
gathergood-e2e/
├── conftest.py                  # Root: session fixtures (auth, api_client, browser_auth)
├── pytest.ini                   # Base URL, markers, default options, html report path
├── requirements.txt             # pytest, playwright, httpx, pytest-html, pytest-playwright
│
├── tests/
│   ├── conftest.py              # Test-layer fixtures that need test directory scope
│   ├── api/                     # API-only tests (no browser)
│   │   ├── conftest.py          # API-specific fixtures if needed
│   │   ├── test_auth.py         # AUTH-01 to AUTH-05
│   │   ├── test_profile.py      # PROF-01, PROF-02
│   │   ├── test_orgs.py         # ORG-01 to ORG-04
│   │   ├── test_team.py         # TEAM-01 to TEAM-04
│   │   ├── test_venues.py       # VENU-01 to VENU-03
│   │   ├── test_events.py       # EVNT-01 to EVNT-09
│   │   ├── test_tickets.py      # TICK-01 to TICK-04
│   │   ├── test_promos.py       # PRMO-01 to PRMO-04
│   │   ├── test_checkout.py     # CHKT-01 to CHKT-12
│   │   ├── test_orders.py       # ORDR-01 to ORDR-07
│   │   ├── test_checkin.py      # CHKN-01 to CHKN-06, MCHK-01/02
│   │   ├── test_stats.py        # STAT-01 to STAT-03, SRCH-01
│   │   ├── test_guestlist.py    # GUST-01, GUST-02
│   │   ├── test_email.py        # EMAL-01 to EMAL-04
│   │   ├── test_public.py       # PUBL-01 to PUBL-05
│   │   └── test_analytics.py   # ANLT-01 to ANLT-03
│   │
│   └── ui/                      # Browser UI tests (Playwright)
│       ├── conftest.py          # UI-specific fixtures (authenticated_page, etc.)
│       ├── test_navigation.py   # FEND-01 to FEND-05 (nav, routing)
│       ├── test_checkout_ui.py  # FEND-06 to FEND-08 (checkout steps)
│       ├── test_responsive.py   # FEND-09, FEND-10 (mobile/responsive)
│       └── test_public_ui.py    # Public browse/event detail UI
│
├── pages/                       # Page Object Models
│   ├── base_page.py             # Shared locator helpers, navigation
│   ├── login_page.py            # Login form interactions
│   ├── event_page.py            # Event detail page
│   ├── checkout_page.py         # Checkout flow steps
│   └── dashboard_page.py        # Organizer dashboard
│
├── helpers/
│   ├── api.py                   # assert_status(), extract_token(), build_qr()
│   ├── auth.py                  # login(), register(), refresh_token()
│   └── qr.py                    # HMAC QR verification logic
│
├── factories/
│   ├── users.py                 # unique_email(), user_payload()
│   ├── events.py                # event_payload(), ticket_tier_payload()
│   └── orgs.py                  # org_payload() with unique slug
│
└── reports/                     # Output directory (gitignored)
    ├── report.html
    └── junit.xml
```

### Structure Rationale

- **tests/api/ vs tests/ui/:** Hard separation prevents browser-heavy fixtures from loading during API-only runs. Run `pytest tests/api/` to skip Playwright entirely.
- **conftest.py at root:** Session-scoped auth lives here so both API and UI test directories share the same JWT without re-logging in.
- **pages/:** Page Object Models live outside `tests/` so they can be imported by any test module without pytest treating them as test files.
- **factories/:** Centralizes data generation with unique identifiers (uuid4/timestamp suffix) — critical when testing against the live deployed database.
- **helpers/:** Pure functions that encapsulate repeated logic (QR HMAC check, status assertion) without side effects — keeps test bodies readable.

## Architectural Patterns

### Pattern 1: Session-Scoped Auth Fixture

**What:** Register + login once at the start of the test session, cache the JWT access token and headers in a session-scoped fixture. All test functions that need auth receive the fixture; no test re-authenticates independently.

**When to use:** Any test suite running against a live API with authentication. Session scope dramatically reduces test run time (79 requirements would otherwise each trigger a login round-trip).

**Trade-offs:** If the token expires mid-session (30-minute access token), the session fixture must handle refresh automatically or set token TTL awareness. Session scope also means auth state is shared — one test mutating roles or deactivating a user can affect subsequent tests unless carefully sequenced.

**Example:**
```python
# conftest.py (root)
import pytest
import httpx

BASE_URL = "https://event-management-production-ad62.up.railway.app/api/v1"

@pytest.fixture(scope="session")
def auth_session():
    import uuid
    email = f"testuser_{uuid.uuid4().hex[:8]}@gathergood-test.invalid"
    password = "TestPassword123!"
    client = httpx.Client(base_url=BASE_URL)

    client.post("/auth/register/", json={"email": email, "password": password, "name": "Test User"})
    resp = client.post("/auth/login/", json={"email": email, "password": password})
    resp.raise_for_status()
    token = resp.json()["access"]

    client.headers.update({"Authorization": f"Bearer {token}"})
    yield {"client": client, "email": email, "token": token}
    client.close()
```

### Pattern 2: Page Object Model (POM) for UI Tests

**What:** Each significant page or feature area is represented by a Python class that encapsulates selectors and interaction methods. Tests call methods on the page object instead of inline `page.locator(...)` calls.

**When to use:** Any browser UI test. POMs are essential once you have more than ~5 UI tests — without them, selector changes require touching every test file.

**Trade-offs:** Small upfront cost to define the classes; paid back immediately when selectors change in the Next.js frontend.

**Example:**
```python
# pages/login_page.py
class LoginPage:
    def __init__(self, page):
        self.page = page
        self.email_input = page.get_by_label("Email")
        self.password_input = page.get_by_label("Password")
        self.submit_button = page.get_by_role("button", name="Sign in")

    def login(self, email: str, password: str):
        self.email_input.fill(email)
        self.password_input.fill(password)
        self.submit_button.click()
```

### Pattern 3: Requirement ID Markers

**What:** Tag every test function with `@pytest.mark.req("AUTH-01")` (or similar) so the test report maps directly back to TEST_SPEC.md requirement IDs. Custom pytest hooks generate a summary table of passing/failing requirement IDs.

**When to use:** This project specifically, since the TEST_SPEC.md defines 79 named requirements that the report must map to.

**Trade-offs:** Requires a small custom plugin or conftest hook to collect and summarize markers. Worth the investment for clear stakeholder reporting.

**Example:**
```python
# conftest.py — register marker
def pytest_configure(config):
    config.addinivalue_line("markers", "req(id): TEST_SPEC.md requirement ID")

# test_auth.py
@pytest.mark.req("AUTH-01")
def test_register_new_user(auth_session):
    # ...
```

### Pattern 4: Unique-Per-Run Data with Factories

**What:** All test data generated with unique identifiers (UUID or timestamp suffix) so concurrent or repeated runs against the live DB do not collide or pollute each other.

**When to use:** Mandatory when running against a live, shared deployed database (as this project does).

**Trade-offs:** Data accumulates in the live DB over time. Mitigation: use clearly prefixed emails (e.g., `testuser_*@gathergood-test.invalid`) and periodically clean them, or track created resource IDs in the session fixture and delete on teardown.

## Data Flow

### API Test Execution Flow

```
pytest discovers test_auth.py
    │
    ▼
conftest.py auth_session fixture (session scope)
    │  POST /auth/register/  →  live Railway backend
    │  POST /auth/login/     →  JWT access token
    │  httpx.Client configured with Bearer header
    ▼
test_register_new_user(auth_session) runs
    │  api_client.get("/auth/me/") → live backend
    │  assert response.status_code == 200
    │  assert response.json()["email"] == expected
    ▼
pytest records PASS/FAIL
    ▼
pytest-html writes report.html after all tests complete
```

### Browser UI Test Execution Flow

```
pytest discovers test_checkout_ui.py
    │
    ▼
conftest.py browser_auth fixture (session scope)
    │  API login → get JWT
    │  Playwright sets cookies/localStorage storageState
    │  Saves auth state to playwright/.auth/session.json
    ▼
conftest.py authenticated_page fixture (function scope)
    │  New BrowserContext loaded with session.json
    │  Fresh page object with auth pre-loaded
    ▼
test_checkout_free_flow(authenticated_page) runs
    │  page.goto("https://event-management-two-red.vercel.app/events/...")
    │  CheckoutPage(page).select_tier("General Admission")
    │  CheckoutPage(page).complete_free_checkout()
    │  assert page.get_by_text("Confirmation").is_visible()
    ▼
pytest records PASS/FAIL + screenshot on failure
```

### Key Data Flows

1. **JWT propagation:** Auth fixture logs in once via API, token flows into both the httpx client (API tests) and Playwright storageState (UI tests) — single source of truth for credentials.
2. **Resource ID chaining:** API tests that span multiple domains (e.g., create org → create event → create ticket tier → checkout) must pass resource IDs forward. These flow as return values stored in session-scoped fixtures or yielded context dicts.
3. **Test report generation:** All test results accumulate in pytest's internal collection; `pytest-html` and `--junitxml` generate output files at session end, not incrementally.
4. **QR HMAC verification:** The agent recomputes `hmac_sha256(secret_key, order_id:tier_id:ticket_id)[:16]` locally and compares against the API-returned QR code string. The HMAC secret must be available as an environment variable.

## Build Order (Component Dependencies)

Building the agent incrementally requires this dependency order:

```
1. Project scaffold (conftest.py, pytest.ini, requirements.txt)
   └─ No dependencies

2. Auth fixture + API client fixture
   └─ Requires: project scaffold, live backend reachable

3. Data factories + API helpers
   └─ Requires: understanding of API response shapes (read TEST_SPEC.md)

4. API test modules (tests/api/)
   └─ Requires: auth fixture, data factories, API helpers

5. Browser auth fixture (Playwright storageState)
   └─ Requires: auth fixture (reuses JWT)

6. Page Object Models (pages/)
   └─ Requires: Playwright installed, UI deployed and reachable

7. UI test modules (tests/ui/)
   └─ Requires: page objects, browser auth fixture

8. Reporter configuration (markers, pytest-html, junit.xml)
   └─ Requires: tests exist to report on
```

## Anti-Patterns

### Anti-Pattern 1: Per-Test Login

**What people do:** Each test function calls the login endpoint directly to get its own token.

**Why it's wrong:** With 79 test cases each making 2 HTTP round trips for register+login, this adds ~158 unnecessary network calls. Against a live Railway-deployed backend, this is slow and may trigger rate limiting.

**Do this instead:** Single session-scoped auth fixture. All tests share one token. If token expiry within a session is a concern, implement a refresh helper.

### Anti-Pattern 2: Hardcoded Test Data

**What people do:** Use a fixed email like `testuser@test.com` or a fixed event title like `"Test Event"`.

**Why it's wrong:** The second test run finds data already in the live database from the first run, causing uniqueness constraint errors or returning stale/unexpected results.

**Do this instead:** Factories with `uuid4` suffixes. Every run creates fresh data, runs are idempotent.

### Anti-Pattern 3: Inline Selectors Throughout Test Files

**What people do:** `page.locator("#checkout-btn").click()` scattered across every UI test.

**Why it's wrong:** When the Next.js frontend changes the selector (inevitable), every test file needs updating.

**Do this instead:** Page Object Models. The selector lives in one place; tests call `checkout_page.click_complete()`.

### Anti-Pattern 4: Running UI Tests for API Assertions

**What people do:** Use a browser page to assert API responses (e.g., checking the DOM for data that could be verified directly via HTTP).

**Why it's wrong:** Browser tests are 10-100x slower than HTTP calls and flakier. DOM rendering is not the right assertion layer for API contract testing.

**Do this instead:** API tests for backend correctness, UI tests only for frontend behavior (navigation, rendering, user flows). The two layers are complementary, not interchangeable.

### Anti-Pattern 5: No Cleanup of Live Data

**What people do:** Tests create orgs, events, and orders in the live DB and never clean them.

**Why it's wrong:** The live GatherGood database accumulates garbage data across runs. Analytics endpoints may return inflated figures. Public event listings show test events.

**Do this instead:** Session fixture teardown deletes created resources in reverse dependency order. Use email domain `@gathergood-test.invalid` as a marker to identify test data. As a fallback, document a cleanup script.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Railway (Django API) | httpx.Client with base URL, Bearer token header | All API tests target this directly. SSL must be valid. |
| Vercel (Next.js frontend) | Playwright browser, chromium, headless | UI tests target the live Vercel URL. No local server needed. |
| Stripe (payments) | Use Stripe test mode cards (4242 4242 4242 4242) in checkout tests | Requires Stripe test publishable key in env. If unavailable, mark paid checkout tests `@pytest.mark.skip`. |
| QR HMAC | Local recomputation using Django's secret key or a shared HMAC secret | Requires environment variable. Document in `.env.example`. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| conftest.py auth fixture ↔ API tests | Fixture injection via pytest (no imports needed) | Tests declare `def test_foo(auth_session)` and pytest provides it |
| conftest.py auth fixture ↔ UI tests | Fixture produces storageState file consumed by Playwright browser context | storageState bridges API-land auth into browser-land |
| API helpers ↔ test modules | Direct Python import (`from helpers.api import assert_ok`) | Not fixtures — pure functions, always available |
| factories ↔ test modules | Direct Python import | factories return plain dicts, no pytest coupling |
| Page Objects ↔ UI test modules | Instantiated inside tests or via fixtures | `LoginPage(page)` pattern — page comes from pytest-playwright fixture |

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 79 requirements (current) | Single-process pytest run, session-scoped auth, sequential execution is fine |
| 200+ requirements | Add `pytest-xdist` for parallel workers. Auth fixture must be process-safe (use file-based token cache). |
| Multi-environment (staging/prod) | Parameterize base URLs via env vars or pytest config profiles rather than hardcoding |

### Scaling Priorities

1. **First bottleneck:** Test run time. Fix with `pytest-xdist -n auto` for parallelism, but requires auth fixtures to be safe across workers.
2. **Second bottleneck:** Flaky UI tests due to network latency against live Vercel deployment. Fix with Playwright's built-in `expect(...).to_be_visible()` auto-retry, not manual `time.sleep()`.

## Sources

- Playwright Python docs — API Testing: https://playwright.dev/python/docs/api-testing
- Playwright Python docs — Page Object Models: https://playwright.dev/python/docs/pom
- pytest-playwright PyPI: https://pypi.org/project/pytest-playwright/
- pytest fixture documentation: https://docs.pytest.org/en/stable/how-to/fixtures.html
- E2E test data strategies (Playwright tips): https://www.playwright-user-event.org/playwright-tips/test-data-strategies-for-e2e-tests
- Building comprehensive E2E suites (100+ cases): https://dev.to/bugslayer/building-a-comprehensive-e2e-test-suite-with-playwright-lessons-from-100-test-cases-171k
- Playwright E2E best practices 2026: https://elionavarrete.com/blog/e2e-best-practices-playwright.html
- pytest session fixture scoping: https://docs.pytest.org/en/stable/example/special.html

---
*Architecture research for: E2E Testing Agent — GatherGood (Django REST + Next.js)*
*Researched: 2026-03-28*
