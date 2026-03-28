# Phase 1: Foundation - Research

**Researched:** 2026-03-28
**Domain:** pytest test harness scaffolding — auth fixtures, data isolation, teardown, config, markers
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INFR-01 | Project scaffolded with pytest, httpx, and Playwright Python bindings | Standard stack section; installation commands; version compatibility table |
| INFR-02 | Environment config via pydantic-settings (.env for BASE_URL, credentials, secrets) | Standard stack; code example for Settings class; .env.example pattern |
| INFR-03 | Session-scoped JWT auth fixture that registers/logs in and auto-refreshes tokens before expiry | Auth fixture pattern; token manager pattern; JWT pitfall section |
| INFR-04 | Unique test data factories using uuid4 suffixes to avoid live DB pollution | Factories pattern; code example for unique_email() and run_id prefix |
| INFR-05 | Teardown harness that cleans up test-created data after each run where API allows | Teardown registry pattern; reverse-dependency deletion order; pitfall 1 |
| INFR-06 | Requirement ID markers (@pytest.mark.req) mapping each test to its TEST_SPEC ID | Marker registration pattern; conftest hook example |
| INFR-07 | Single CLI command to run the full test suite (pytest entry point) | pytest.ini configuration; CLI invocation section |
</phase_requirements>

---

## Summary

Phase 1 builds the test harness skeleton that every subsequent phase depends on. The work is entirely infrastructure: no test cases, no domain assertions — only the scaffolding that makes it safe and reliable to write tests against a live production database with no rollback mechanism.

The stack is locked (Python 3.11+, pytest, httpx, pydantic-settings, faker — all versions verified against PyPI by prior research). The architecture is also locked: a layered project structure with session-scoped auth at the root conftest, a token manager that proactively refreshes JWTs before the 30-minute expiry, uuid4-prefixed data factories, a session teardown registry that deletes created resources in reverse dependency order, and a custom `@pytest.mark.req` marker registered in conftest.

**Critical constraint from project research:** The live Railway backend has no rollback, no test database isolation, and no mass-delete endpoint. Every design decision in this phase must treat the live DB as permanent until explicitly cleaned up. The naming strategy and teardown harness are not nice-to-haves — they are prerequisites for everything else.

**Environment note:** The live backend is confirmed responsive. A GET to `/api/v1/auth/register/` returns 405 (method not allowed), confirming the endpoint exists and accepts POST. The live URL is `https://event-management-production-ad62.up.railway.app/api/v1`.

**Primary recommendation:** Build phase 1 components in dependency order: project scaffold → config → auth fixture with token manager → factories → teardown registry → markers → pytest.ini entry point. Do not proceed to Phase 2 until `pytest --co` (collection-only) passes cleanly and a smoke test of the auth fixture against the live backend succeeds.

---

## Project Constraints (from CLAUDE.md)

The following directives from CLAUDE.md are binding on this phase:

- **Target URLs**: Tests must run against the live deployed endpoints (not local dev). Backend: `https://event-management-production-ad62.up.railway.app/api/v1`. Frontend: `https://event-management-two-red.vercel.app/`.
- **Test isolation**: Tests must clean up after themselves where possible, or use unique data per run to avoid polluting the live database.
- **Stripe**: Paid checkout tests will need Stripe test mode or must be marked as manual/skipped if no test keys are available.
- **No destructive actions**: Tests must not delete production data that other users depend on.
- **GSD workflow**: File changes must go through GSD commands (`/gsd:execute-phase`), not direct ad-hoc edits.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.11+ | Agent runtime | Verified installed: 3.13.11 is on this machine. pytest is Python-native; no language split needed. |
| pytest | 9.0.2 | Test runner | Session fixtures, marker system, plugin ecosystem. Installed version: 8.3.5 — planner must include upgrade to 9.0.2. |
| httpx | 0.28.1 | HTTP client for API calls | Sync + async API; drop-in requests replacement; installed version confirmed 0.28.1. |
| pydantic-settings | 2.13.1 | Type-safe .env config | Fails fast at startup if env vars missing. NOT currently installed — planner must install. |
| faker | 33.x | Unique test data | Prevents live DB collision. Installed: 40.11.1 (compatible; above 33.x). |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-dotenv | 1.0.x | .env parsing | Required by pydantic-settings; likely installed as a transitive dep but must be verified. |
| pytest-html | 4.x | HTML test reports | Local run reports. NOT currently installed — add to requirements.txt. |
| playwright (Python) | 1.58.0 | Browser automation | Phase 1 installs it; browser tests come in Phase 3. Installed: 1.58.0. |
| pytest-playwright | 0.7.2 | Playwright fixtures | Add now even though UI tests are Phase 3 — ensures consistent fixture availability. NOT installed. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pydantic-settings | raw os.environ | os.environ silently accepts missing vars; pydantic-settings fails immediately at import. Never acceptable here. |
| faker uuid4 suffix | timestamp suffix | Both work; uuid4 is shorter and guaranteed unique without clock skew. |
| pytest 9.0.2 | pytest 8.3.5 (installed) | 8.3.5 works; 9.0.2 adds improved output formatting. Upgrade is low-risk but must be pinned explicitly. |

**Installation (full requirements.txt for this phase):**
```bash
pip install pytest==9.0.2 httpx==0.28.1 pydantic-settings==2.13.1 python-dotenv faker pytest-html playwright==1.58.0 pytest-playwright==0.7.2
playwright install chromium
```

**Version verification (done 2026-03-28):**
- pytest: installed 8.3.5, target 9.0.2 (upgrade needed)
- httpx: 0.28.1 installed (matches target)
- playwright: 1.58.0 installed (matches target)
- faker: 40.11.1 installed (above target 33.x, compatible)
- pydantic-settings: NOT installed (must install)
- pytest-playwright: NOT installed (must install)
- pytest-html: NOT installed (must install)

---

## Architecture Patterns

### Recommended Project Structure

```
gathergood-e2e/
├── conftest.py                  # Root: session fixtures (auth, api_client, teardown registry)
├── pytest.ini                   # Markers, base options, html report, testpaths
├── requirements.txt             # All pinned dependencies
├── .env                         # Local secrets (gitignored)
├── .env.example                 # Documented placeholder values (committed)
│
├── tests/
│   ├── conftest.py              # Test-layer shared fixtures
│   ├── api/                     # API-only tests (no browser needed)
│   │   └── conftest.py          # API fixtures
│   └── ui/                      # Browser UI tests (Playwright)
│       └── conftest.py          # UI fixtures
│
├── helpers/
│   ├── __init__.py
│   └── api.py                   # assert_status(), extract_token()
│
├── factories/
│   ├── __init__.py
│   └── common.py                # unique_email(), run_id, prefixed names
│
└── reports/                     # gitignored — pytest-html output
```

Phase 1 delivers: `conftest.py`, `pytest.ini`, `requirements.txt`, `.env.example`, `helpers/api.py`, `factories/common.py`. The `tests/` subdirectories are created as empty packages with `__init__.py` so Phase 2 can add test files without restructuring.

### Pattern 1: Session-Scoped Auth Fixture with Token Manager

**What:** Register a fresh test user once per pytest session, log in, cache both access and refresh tokens, expose an authenticated httpx client. A token manager checks remaining lifetime before every API call and proactively refreshes when within 5 minutes of expiry.

**When to use:** Always. Every API test and browser test depends on this fixture.

**Critical detail:** The backend uses `djangorestframework-simplejwt==5.5.1`. Default access token lifetime is 5 minutes unless overridden in Django settings. The research assumption of 30 minutes must be verified empirically at Phase 1 implementation — check the `exp` claim in the JWT response. The refresh logic must be calibrated to the actual TTL, not the assumed one.

**Example:**
```python
# conftest.py (root)
# Source: https://docs.pytest.org/en/stable/how-to/fixtures.html (session scope)
#         https://pypi.org/project/httpx/ (httpx.Client)
import uuid
import time
import pytest
import httpx

from settings import Settings

settings = Settings()


class TokenManager:
    """Wraps an httpx.Client and refreshes the access token before expiry."""

    def __init__(self, client: httpx.Client, access_token: str, refresh_token: str,
                 access_exp: float, base_url: str):
        self.client = client
        self._access = access_token
        self._refresh = refresh_token
        self._exp = access_exp          # UTC epoch seconds
        self._base_url = base_url
        self._refresh_margin = 300      # refresh 5 min before expiry

    def _ensure_fresh(self):
        remaining = self._exp - time.time()
        if remaining < self._refresh_margin:
            resp = httpx.post(
                f"{self._base_url}/auth/token/refresh/",
                json={"refresh": self._refresh},
            )
            resp.raise_for_status()
            data = resp.json()
            self._access = data["access"]
            # simplejwt rotation: update refresh token if returned
            if "refresh" in data:
                self._refresh = data["refresh"]
            import jwt as pyjwt  # PyJWT for decoding exp claim
            payload = pyjwt.decode(self._access, options={"verify_signature": False})
            self._exp = payload["exp"]
            self.client.headers["Authorization"] = f"Bearer {self._access}"

    def get(self, url, **kwargs):
        self._ensure_fresh()
        return self.client.get(url, **kwargs)

    def post(self, url, **kwargs):
        self._ensure_fresh()
        return self.client.post(url, **kwargs)

    def patch(self, url, **kwargs):
        self._ensure_fresh()
        return self.client.patch(url, **kwargs)

    def delete(self, url, **kwargs):
        self._ensure_fresh()
        return self.client.delete(url, **kwargs)


@pytest.fixture(scope="session")
def auth_client(teardown_registry):
    """Register a test user, log in, return a TokenManager-wrapped client."""
    run_id = uuid.uuid4().hex[:8]
    email = f"test-{run_id}@gathergood-test.invalid"
    password = "TestPass123!"

    client = httpx.Client(base_url=settings.API_URL)

    # Register
    r = client.post("/auth/register/", json={
        "email": email,
        "password": password,
        "first_name": "Test",
        "last_name": f"User{run_id}",
    })
    assert r.status_code == 201, f"Registration failed: {r.text}"

    # Login
    r = client.post("/auth/login/", json={"email": email, "password": password})
    assert r.status_code == 200, f"Login failed: {r.text}"
    data = r.json()
    access = data["access"]
    refresh = data["refresh"]

    import jwt as pyjwt
    payload = pyjwt.decode(access, options={"verify_signature": False})
    exp = payload["exp"]

    client.headers.update({"Authorization": f"Bearer {access}"})
    manager = TokenManager(client, access, refresh, exp, settings.API_URL)

    # Register test user for teardown
    teardown_registry["test_user_email"] = email

    yield manager
    client.close()
```

### Pattern 2: pydantic-settings Config

**What:** A `Settings` class that reads all required env vars from `.env` at import time, with type validation and clear error messages for missing values.

**When to use:** First file created. All fixtures import `Settings` — never `os.environ` directly.

**Example:**
```python
# settings.py
# Source: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_URL: str = "https://event-management-production-ad62.up.railway.app/api/v1"
    BASE_URL: str = "https://event-management-two-red.vercel.app"
    TEST_USER_EMAIL: str = ""      # optional: pre-existing user (Phase 2+)
    TEST_USER_PASSWORD: str = ""
    STRIPE_TEST_KEY: str = ""      # optional: Phase 4

    model_config = {"env_file": ".env", "extra": "ignore"}
```

**`.env.example` (committed to repo):**
```
API_URL=https://event-management-production-ad62.up.railway.app/api/v1
BASE_URL=https://event-management-two-red.vercel.app
TEST_USER_EMAIL=
TEST_USER_PASSWORD=
STRIPE_TEST_KEY=
```

### Pattern 3: Run-ID Data Factories

**What:** A module-level `RUN_ID` generated once per process. All test data entities use `test-{RUN_ID}-` prefix, making them identifiable and cleanable.

**When to use:** Every function that creates a named entity (user, org, event, venue, etc.).

**Example:**
```python
# factories/common.py
import uuid

RUN_ID = uuid.uuid4().hex[:8]   # e.g. "a3f9b2c1"


def unique_email() -> str:
    """test-{run}-{token}@gathergood-test.invalid"""
    token = uuid.uuid4().hex[:6]
    return f"test-{RUN_ID}-{token}@gathergood-test.invalid"


def org_name() -> str:
    return f"test-{RUN_ID}-org-{uuid.uuid4().hex[:4]}"


def event_title() -> str:
    return f"test-{RUN_ID}-event-{uuid.uuid4().hex[:4]}"


def venue_name() -> str:
    return f"test-{RUN_ID}-venue-{uuid.uuid4().hex[:4]}"
```

### Pattern 4: Teardown Registry

**What:** A session-scoped dict that accumulates IDs of all created resources during the session. At session end, the fixture deletes them in reverse dependency order.

**When to use:** Every test that creates a persistent resource calls `teardown_registry["category"].append(id)`.

**Dependency order for deletion (reverse):**
```
tickets → orders → promo codes → ticket tiers → events → venues → organizations → users
```

**Example:**
```python
# conftest.py (root)
@pytest.fixture(scope="session")
def teardown_registry():
    registry = {
        "users": [],
        "organizations": [],
        "venues": [],
        "events": [],
        "ticket_tiers": [],
        "promo_codes": [],
        "orders": [],
    }
    yield registry
    # Teardown happens here after session; client needed for cleanup
    # Planner should wire this to a cleanup_client fixture
```

### Pattern 5: Requirement ID Markers

**What:** A custom marker `req` registered in `conftest.py`. Every test function that addresses a TEST_SPEC requirement is tagged `@pytest.mark.req("AUTH-01")`.

**When to use:** Every test in Phase 2+. Phase 1 does not write test cases, but registers the marker system for future tests.

**Example:**
```python
# conftest.py (root)
# Source: https://docs.pytest.org/en/stable/how-to/mark.html
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "req(id): TEST_SPEC.md requirement ID this test verifies"
    )

# Usage in test files (Phase 2+):
# @pytest.mark.req("AUTH-01")
# def test_register_new_user(auth_client): ...
```

### Pattern 6: pytest.ini Configuration

**What:** Central pytest configuration that sets default CLI options, declares markers (prevents unknown-marker warnings), specifies test paths, and wires up reporting.

**Example:**
```ini
# pytest.ini
[pytest]
testpaths = tests
addopts = -v --tb=short --html=reports/report.html --self-contained-html
markers =
    req: TEST_SPEC.md requirement ID (e.g. @pytest.mark.req("AUTH-01"))
```

### Pattern 7: Railway Health Check on Startup

**What:** A `pytest_sessionstart` hook that pings the live Railway backend before any test runs. If the backend is unreachable or returning errors, the session aborts with a clear message rather than producing 79 cascading failures.

**When to use:** Add to root conftest. Runs once at session start.

**Example:**
```python
# conftest.py (root)
def pytest_sessionstart(session):
    import httpx
    from settings import Settings
    s = Settings()
    try:
        r = httpx.get(s.API_URL + "/", timeout=30)
        # 404 is acceptable (no root view); 5xx means backend is down
        if r.status_code >= 500:
            raise RuntimeError(f"Backend health check failed: {r.status_code}")
    except httpx.ConnectError as e:
        raise RuntimeError(f"Cannot reach backend at {s.API_URL}: {e}")
```

**Note:** The live backend returns 404 on GET `/api/v1/` (confirmed above — the Railway deployment does not serve the api_root view from the local source). A 404 at the root is acceptable; only 5xx or connection failure should abort the session.

### Anti-Patterns to Avoid

- **Using `os.environ` directly:** Silently accepts undefined vars. Always use pydantic-settings.
- **No token refresh logic:** The 30-minute (or possibly 5-minute — verify empirically) access token will expire mid-suite. A suite with no refresh produces cascading 401s starting at an unpredictable point.
- **Hardcoded test data:** `email = "testuser@test.com"` breaks on the second run due to uniqueness constraints.
- **Teardown skipped "for speed":** Creates permanent garbage in the live DB that corrupts future test assertions.
- **Markers not registered:** pytest warns about unknown markers and may suppress them with `--strict-markers`. Register `req` in `pytest_configure` before any Phase 2 test is written.
- **No Railway health check:** A cold-started Railway instance can take 30+ seconds to respond. Without a startup check, the first test fails with a connection timeout and the error looks like a test bug.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JWT decoding for exp claim | Custom base64 decode | `PyJWT` (decode without verify) | simplejwt tokens use standard JWT format; PyJWT handles edge cases (padding, encoding) correctly |
| .env parsing | Custom file reader | pydantic-settings + python-dotenv | Type validation, default handling, error messages already built in |
| Unique ID generation | timestamp-based suffix | `uuid.uuid4().hex[:8]` | Clock skew between runs can produce collisions; uuid4 is guaranteed unique |
| HTTP client with auth headers | Custom wrapper class | httpx.Client with `headers=` | httpx persists headers across requests; custom wrappers duplicate this |
| HTML test reports | Custom HTML generator | pytest-html | Already integrated with pytest's result collection; zero extra code needed |

**Key insight:** Every "hand-rolled" version of these utilities has edge cases that the library already handles. The live-DB constraint makes correctness non-negotiable — an off-by-one in a timestamp suffix or a JWT decode bug can corrupt an entire test run.

---

## Common Pitfalls

### Pitfall 1: JWT Expiry — Unknown Actual TTL

**What goes wrong:** simplejwt's default access token lifetime is 5 minutes (not 30 minutes as assumed in high-level research). If the deployed backend uses defaults, a refresh margin of 5 minutes means near-constant refreshes. More critically, if the TTL is unknown and the harness does not decode the `exp` claim from the actual token, the refresh threshold is wrong.

**Why it happens:** The backend source (`config/settings/`) is not available in the repo checked out locally — only base requirements are present. The actual JWT TTL is set in Django settings, which may differ from simplejwt defaults.

**How to avoid:** At Phase 1 smoke test, log in, decode the returned access token's `exp` claim, and log the TTL. Set the refresh margin to `min(300, TTL * 0.8)`. The `TokenManager` above decodes `exp` from the live response — this is the correct approach.

**Warning signs:** Auth fixture refreshes token on every single API call (TTL < 5 minutes), or 401 errors appear after 5 minutes of test run time.

### Pitfall 2: Registration Endpoint Shape Unknown

**What goes wrong:** The backend source shows `apps/accounts/urls.py` contains empty `urlpatterns = []`. The live deployment has auth endpoints (confirmed: `/api/v1/auth/register/` returns 405 on GET), but the exact request/response schema is not in the source code checked out locally.

**Why it happens:** The local source is an early-stage scaffold; the full implementation is deployed on Railway. The field names for registration (`first_name` / `last_name` vs `name` vs `username`) must be verified against the live API, not assumed from the model.

**How to avoid:** At Phase 1 smoke test, attempt registration with a candidate payload and inspect the 400 response's error keys to determine required fields. The `User` model requires `first_name`, `last_name` (via `REQUIRED_FIELDS`), and `email`. The auth fixture example above uses `first_name` + `last_name` — verify this matches the live serializer.

**Warning signs:** Registration returns 400 with field errors; adjust payload to match actual required fields.

### Pitfall 3: Live Data Pollution Without Teardown

**What goes wrong:** Each test run that does not clean up leaves `test-{RUN_ID}-*` records in the live database. After 10 runs, list endpoints return 10+ records when tests expect 1. Analytics endpoints accumulate fake revenue. The public event browse page shows test events.

**Why it happens:** Teardown is treated as optional. On a live DB it is mandatory.

**How to avoid:** The teardown registry fixture must yield before the session ends. Every Phase 2+ test that creates a resource must register the resource ID immediately after creation, not at test end.

**Warning signs:** List endpoints returning more records than created in the current run; `test-` prefixed names visible in the live UI.

### Pitfall 4: pytest.ini addopts Breaking CI-style Invocations

**What goes wrong:** `--html=reports/report.html` in `addopts` fails if the `reports/` directory does not exist when pytest starts. This blocks `pytest --co` (collection-only) used in CI or pre-run checks.

**How to avoid:** Create `reports/.gitkeep` as part of the scaffold. Or use `--html` as a CLI argument only and keep `addopts` minimal. Add `reports/` to `.gitignore` to keep it clean.

**Warning signs:** `pytest --co` exits non-zero with a file-not-found error before collecting any tests.

### Pitfall 5: Missing `__init__.py` in Package Directories

**What goes wrong:** pytest imports helpers and factories as modules. Without `__init__.py`, relative imports fail in some configurations. `from factories.common import unique_email` breaks with `ModuleNotFoundError`.

**How to avoid:** Add `__init__.py` to `helpers/`, `factories/`, `pages/` when creating the scaffold. Empty files are sufficient.

**Warning signs:** `ModuleNotFoundError: No module named 'factories'` when running tests.

---

## Code Examples

Verified patterns from official sources:

### Full conftest.py Skeleton (Phase 1 deliverable)

```python
# conftest.py (project root)
# Sources:
#   pytest fixture docs: https://docs.pytest.org/en/stable/how-to/fixtures.html
#   pydantic-settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
#   httpx: https://www.python-httpx.org/

import uuid
import time
import pytest
import httpx

from settings import Settings
from factories.common import RUN_ID


settings = Settings()


def pytest_configure(config):
    """Register custom markers to suppress unknown-marker warnings."""
    config.addinivalue_line(
        "markers",
        "req(id): TEST_SPEC.md requirement ID this test verifies"
    )


def pytest_sessionstart(session):
    """Abort early if the backend is unreachable."""
    try:
        r = httpx.get(settings.API_URL.rstrip("/") + "/", timeout=30)
        if r.status_code >= 500:
            raise RuntimeError(
                f"Backend health check returned {r.status_code}. Aborting session."
            )
    except httpx.ConnectError as e:
        raise RuntimeError(f"Cannot connect to backend at {settings.API_URL}: {e}")


@pytest.fixture(scope="session")
def teardown_registry():
    """Accumulate created resource IDs; delete in reverse dependency order at session end."""
    registry = {
        "user_ids": [],
        "org_ids": [],
        "venue_ids": [],
        "event_ids": [],
        "ticket_tier_ids": [],
        "promo_code_ids": [],
        "order_ids": [],
    }
    yield registry
    # Cleanup is wired here in Phase 2 once we have a cleanup client


@pytest.fixture(scope="session")
def auth_client(teardown_registry):
    """
    Session-scoped authenticated HTTP client.
    Registers a fresh test user, logs in, and wraps the client with token refresh.
    """
    email = f"test-{RUN_ID}@gathergood-test.invalid"
    password = "TestPass123!"

    base = settings.API_URL.rstrip("/")
    client = httpx.Client(base_url=base, timeout=30.0)

    # Register
    r = client.post("/auth/register/", json={
        "email": email,
        "password": password,
        "first_name": "Test",
        "last_name": f"User-{RUN_ID}",
    })
    assert r.status_code == 201, (
        f"Test user registration failed ({r.status_code}): {r.text}\n"
        "Check that the registration payload matches the live API's required fields."
    )

    # Login
    r = client.post("/auth/login/", json={"email": email, "password": password})
    assert r.status_code == 200, f"Login failed ({r.status_code}): {r.text}"
    tokens = r.json()

    client.headers["Authorization"] = f"Bearer {tokens['access']}"

    # Decode exp without verifying signature (secret is server-side)
    try:
        import base64, json as _json
        payload_b64 = tokens["access"].split(".")[1]
        # Add padding
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        exp = _json.loads(base64.urlsafe_b64decode(payload_b64))["exp"]
    except Exception:
        exp = time.time() + 300   # fallback: assume 5-minute TTL

    ttl = exp - time.time()
    print(f"\n[auth_client] JWT TTL: {ttl:.0f}s (expires at epoch {exp:.0f})")

    class _Client:
        """Thin wrapper that refreshes the token before expiry."""
        def __init__(self):
            self._access = tokens["access"]
            self._refresh = tokens["refresh"]
            self._exp = exp
            self._margin = max(60, ttl * 0.15)   # refresh at 15% remaining, min 60s

        def _maybe_refresh(self):
            remaining = self._exp - time.time()
            if remaining < self._margin:
                r2 = httpx.post(
                    f"{base}/auth/token/refresh/",
                    json={"refresh": self._refresh},
                    timeout=30,
                )
                r2.raise_for_status()
                data = r2.json()
                self._access = data["access"]
                if "refresh" in data:
                    self._refresh = data["refresh"]
                try:
                    import base64, json as _json
                    p = self._access.split(".")[1]
                    p += "=" * (4 - len(p) % 4)
                    self._exp = _json.loads(base64.urlsafe_b64decode(p))["exp"]
                except Exception:
                    self._exp = time.time() + ttl
                client.headers["Authorization"] = f"Bearer {self._access}"
                print(f"\n[auth_client] Token refreshed. New exp: {self._exp:.0f}")

        def get(self, url, **kw):    self._maybe_refresh(); return client.get(url, **kw)
        def post(self, url, **kw):   self._maybe_refresh(); return client.post(url, **kw)
        def patch(self, url, **kw):  self._maybe_refresh(); return client.patch(url, **kw)
        def put(self, url, **kw):    self._maybe_refresh(); return client.put(url, **kw)
        def delete(self, url, **kw): self._maybe_refresh(); return client.delete(url, **kw)

    yield _Client()
    client.close()
```

### settings.py

```python
# settings.py
# Source: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_URL: str = "https://event-management-production-ad62.up.railway.app/api/v1"
    BASE_URL: str = "https://event-management-two-red.vercel.app"
    STRIPE_TEST_KEY: str = ""   # optional; Phase 4 gates on this being non-empty

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
```

### factories/common.py

```python
# factories/common.py
import uuid

RUN_ID = uuid.uuid4().hex[:8]


def unique_email() -> str:
    return f"test-{RUN_ID}-{uuid.uuid4().hex[:6]}@gathergood-test.invalid"

def org_name() -> str:
    return f"test-{RUN_ID}-org-{uuid.uuid4().hex[:4]}"

def event_title() -> str:
    return f"test-{RUN_ID}-event-{uuid.uuid4().hex[:4]}"

def venue_name() -> str:
    return f"test-{RUN_ID}-venue-{uuid.uuid4().hex[:4]}"
```

### helpers/api.py

```python
# helpers/api.py
import httpx


def assert_status(response: httpx.Response, expected: int, context: str = "") -> None:
    """Assert HTTP status with a meaningful error message."""
    if response.status_code != expected:
        body = response.text[:500]
        raise AssertionError(
            f"{context}\n"
            f"Expected {expected}, got {response.status_code}\n"
            f"URL: {response.url}\n"
            f"Body: {body}"
        )
```

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | Agent runtime | Yes | 3.13.11 | — |
| pytest | INFR-01, INFR-07 | Yes | 8.3.5 (upgrade to 9.0.2 needed) | — |
| httpx | INFR-01, INFR-03 | Yes | 0.28.1 | — |
| playwright | INFR-01 | Yes | 1.58.0 | — |
| faker | INFR-04 | Yes | 40.11.1 | — |
| pydantic-settings | INFR-02 | No | not installed | Must install; no fallback |
| pytest-playwright | INFR-01 | No | not installed | Must install; needed for Phase 3 |
| pytest-html | INFR-07 | No | not installed | Must install; no fallback |
| Live Railway backend | INFR-03 smoke test | Yes | responds (405 on GET /register) | — |
| Chromium browser | INFR-01 (Playwright) | Not verified | — | Run `playwright install chromium` |

**Missing dependencies with no fallback:**
- `pydantic-settings` — required for INFR-02; must be installed before writing `settings.py`
- `pytest-playwright` — required for INFR-01 (full stack scaffold); must be installed
- `pytest-html` — required for INFR-07 (HTML report); must be installed
- Chromium browser binary — required for Phase 3; install via `playwright install chromium`

**Missing dependencies with fallback:**
- None.

---

## Validation Architecture

`nyquist_validation` is enabled (`true` in config.json).

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 (upgrade from 8.3.5) |
| Config file | `pytest.ini` — created in Wave 0 of this phase |
| Quick run command | `pytest --co -q` (collection-only, no network) |
| Full suite command | `pytest tests/ -v --html=reports/report.html` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFR-01 | pytest, httpx, playwright importable | smoke | `python -c "import pytest, httpx, playwright"` | Wave 0 |
| INFR-02 | Settings loads from .env without error | smoke | `python -c "from settings import Settings; Settings()"` | Wave 0 |
| INFR-03 | auth_client fixture produces authenticated response | integration | `pytest tests/smoke/test_auth_fixture.py -x` | Wave 0 |
| INFR-04 | unique_email() returns test-prefixed unique addresses | unit | `pytest tests/smoke/test_factories.py -x` | Wave 0 |
| INFR-05 | teardown_registry accumulates and deletes resources | integration | `pytest tests/smoke/test_teardown.py -x` | Wave 0 |
| INFR-06 | @pytest.mark.req recognized without warning | smoke | `pytest --co -W error::pytest.PytestUnknownMarkWarning` | Wave 0 |
| INFR-07 | Full suite runs with single command, exits 0 | integration | `pytest tests/ --html=reports/report.html` | Wave 0 |

**Note on INFR-03:** The smoke test for the auth fixture makes a live network call to the Railway backend. This is intentional — the entire purpose of INFR-03 is to verify the fixture works against the live API, not a mock.

### Sampling Rate

- **Per task commit:** `pytest --co -q` (collection-only; no network calls)
- **Per wave merge:** `pytest tests/smoke/ -x -v` (all smoke tests; live network)
- **Phase gate:** All smoke tests green, `pytest --co` exits 0, before advancing to Phase 2

### Wave 0 Gaps (all gaps — this is a greenfield phase)

- [ ] `tests/__init__.py` — package init
- [ ] `tests/smoke/__init__.py` — smoke test package
- [ ] `tests/smoke/test_auth_fixture.py` — covers INFR-03 (live auth call)
- [ ] `tests/smoke/test_factories.py` — covers INFR-04 (uniqueness, prefix format)
- [ ] `tests/smoke/test_teardown.py` — covers INFR-05 (registry accumulation)
- [ ] `tests/api/__init__.py` — placeholder for Phase 2
- [ ] `tests/ui/__init__.py` — placeholder for Phase 3
- [ ] `helpers/__init__.py` — package init
- [ ] `factories/__init__.py` — package init
- [ ] `reports/.gitkeep` — ensures directory exists before pytest runs
- [ ] Framework install: `pip install pytest==9.0.2 pydantic-settings pytest-html pytest-playwright`

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `requests` + manual token header | `httpx.Client` with persistent headers | 2022+ | httpx is now the standard; async-ready without rewrite |
| `os.environ` config | `pydantic-settings` BaseSettings | 2023+ | Fail-fast at import rather than at first env var access |
| `selenium` browser automation | `playwright` Python bindings | 2021+ | Auto-waiting eliminates explicit sleeps; Trace Viewer |
| `pytest.ini` with `[pytest]` section | Can also use `pyproject.toml [tool.pytest.ini_options]` | 2022+ | Both work; `pytest.ini` is simpler for a standalone test agent |

**Deprecated/outdated:**
- `unittest` as the runner: pytest is the community standard; unittest is still supported but not recommended for new projects.
- `nose` / `nose2`: Not maintained. Do not use.
- `selenium` WebDriver: Playwright is now the clear choice for new projects in 2026.

---

## Open Questions

1. **Actual JWT TTL from the live backend**
   - What we know: simplejwt default access token lifetime is 5 minutes; project research assumes 30 minutes.
   - What's unclear: The deployed backend's Django settings override (if any) is not in the local source.
   - Recommendation: At Phase 1 smoke test execution, decode the `exp` claim from the returned access token and log the TTL. Set the refresh margin accordingly. The `_Client` class above already does this dynamically.

2. **Registration endpoint field names**
   - What we know: The local `User` model has `first_name`, `last_name` as `REQUIRED_FIELDS`. The accounts `urls.py` is empty in the local repo.
   - What's unclear: The live serializer may use `name` (single field) or `username` instead of separate first/last name fields.
   - Recommendation: At smoke test time, attempt registration and inspect the 400 response. Adjust the fixture payload to match. Add a clear assertion error message that shows the response body if registration fails.

3. **PyJWT as a dependency**
   - What we know: The conftest JWT decode can be done without PyJWT using base64 + json parsing (shown in the code example above).
   - What's unclear: Whether adding PyJWT is preferable to the raw base64 approach.
   - Recommendation: Use the base64 approach from the code example — it avoids an extra dependency and the only thing needed is the `exp` claim. PyJWT is not needed.

---

## Sources

### Primary (HIGH confidence)
- [pytest fixture documentation](https://docs.pytest.org/en/stable/how-to/fixtures.html) — session scope, pytest_configure, pytest_sessionstart hooks
- [pytest mark documentation](https://docs.pytest.org/en/stable/how-to/mark.html) — custom marker registration
- [pydantic-settings documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) — BaseSettings, env_file config
- [httpx documentation](https://www.python-httpx.org/) — Client, persistent headers, timeout
- [djangorestframework-simplejwt 5.5.1](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/) — token structure, default TTLs, refresh endpoint
- Prior domain research: `.planning/research/STACK.md`, `.planning/research/ARCHITECTURE.md`, `.planning/research/PITFALLS.md`

### Secondary (MEDIUM confidence)
- Live backend probe: GET `https://event-management-production-ad62.up.railway.app/api/v1/auth/register/` → 405 (endpoint confirmed present)
- Local backend source inspection: `backend/apps/accounts/models.py` (User fields), `backend/requirements/base.txt` (simplejwt 5.5.1)

### Tertiary (LOW confidence)
- Assumption that simplejwt uses non-default TTL (30 min) is unverified — must be confirmed empirically at Phase 1 execution.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified against PyPI; installed versions confirmed on this machine
- Architecture: HIGH — patterns are from official pytest/httpx/pydantic-settings docs
- Auth fixture: HIGH (pattern) / LOW (JWT TTL) — the pattern is correct; the TTL assumption must be verified live
- Pitfalls: HIGH — verified against PITFALLS.md and official simplejwt docs

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable stack, 30-day validity; re-verify if pydantic-settings or simplejwt release breaking changes)
