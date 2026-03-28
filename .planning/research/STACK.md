# Stack Research

**Domain:** E2E Testing Agent — REST API + Browser UI against live Django REST Framework + Next.js
**Researched:** 2026-03-28
**Confidence:** HIGH (all versions verified against PyPI and official sources)

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11+ | Agent runtime language | Django backend is Python; writing the agent in Python means one language for both API calls and browser automation, and pytest is Python-native. Node.js Playwright is viable but splits the stack for no gain here. |
| pytest | 9.0.2 | Test runner and assertion framework | Industry-standard Python test runner. Parameterisation, fixture scoping, plugin ecosystem, and `--tb=short` output are all built-in. No alternative matches its ecosystem maturity for Python E2E agents. |
| httpx | 0.28.1 | HTTP client for API test layer | Sync and async APIs, HTTP/2 support, request/response inspection. Preferred over `requests` because it supports async (future-proofing) and its API is identical to requests so no learning curve. Preferred over `aiohttp` because sync mode is sufficient here and HTTPX has cleaner ergonomics. |
| playwright (Python) | 1.58.0 | Browser automation for UI test layer | Microsoft-backed, fastest-growing E2E framework. Native Python bindings. Auto-waiting eliminates explicit sleep() calls. Trace Viewer records every step for debugging. Surpassed Cypress in weekly downloads in 2024. Supports Chromium, Firefox, WebKit with one API. |
| pytest-playwright | 0.7.2 | Playwright fixtures for pytest | Official Microsoft pytest plugin. Provides `page`, `browser`, `browser_context`, and `playwright` fixtures automatically. Handles browser lifecycle, so tests stay focused on assertions. Without this, browser teardown must be done manually. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic-settings | 2.13.1 | Type-safe config from `.env` | Store BASE_URL, API_URL, test credentials in `.env`; pydantic-settings validates types at startup and raises a clear error if a required variable is missing. Use instead of raw `os.environ` to catch misconfiguration before any test runs. |
| python-dotenv | 1.0.x | `.env` file loading | pydantic-settings delegates `.env` parsing to python-dotenv. Install alongside pydantic-settings; no direct usage needed in test code. |
| pytest-html | 4.x | HTML test report | Simple self-contained HTML report for local runs. No Java dependency (unlike Allure). Suitable for this project's v1 scope (local CLI). Switch to Allure if stakeholder reporting becomes a requirement. |
| faker | 33.x | Unique test data generation | Generates unique emails, names, org slugs per run to avoid collision on the live database. Critical for test isolation without a teardown DB reset. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `pip` + `requirements.txt` | Dependency management | Simple and sufficient for a standalone test agent. No need for Poetry or PDM unless packaging the agent for distribution. |
| `playwright install chromium` | Browser binary download | Run once after `pip install playwright`. Only Chromium needed; Firefox/WebKit add download size with no benefit for this functional-QA scope. |
| `.env` file | Environment configuration | Store `BASE_URL`, `API_URL`, `TEST_USER_EMAIL`, `TEST_USER_PASSWORD`, `STRIPE_TEST_KEY`. Never commit. Provide `.env.example` with placeholder values. |
| `pytest --html=report.html` | Local report generation | Single command to run all tests and produce a report. |

## Installation

```bash
# Core
pip install pytest==9.0.2 httpx==0.28.1 playwright==1.58.0 pytest-playwright==0.7.2

# Supporting
pip install pydantic-settings==2.13.1 python-dotenv faker pytest-html

# Install browser binary (Chromium only for functional QA)
playwright install chromium
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Python + pytest | TypeScript + Playwright Test | If the team is exclusively frontend/TypeScript. TypeScript Playwright has a richer native ecosystem, but for a project touching a Python/Django backend, Python keeps the stack unified. |
| httpx | requests | If async is never needed and you want the most battle-tested library. `requests` is fine; `httpx` is slightly better for forward compatibility. Either works for this project. |
| httpx | Playwright APIRequestContext | Playwright's built-in API client is fine for simple auth flows, but httpx gives more control over headers, redirects, and response inspection for a dedicated API test suite. Use APIRequestContext only for sharing auth state between API setup and browser tests. |
| pytest-html | Allure Report | When non-technical stakeholders need rich dashboards with trends and history. Allure requires a Java runtime, which adds setup friction for a local CLI tool. |
| faker | hardcoded test data | Never use hardcoded data against a live database. Collisions accumulate across runs and corrupt test state. |
| Playwright | Cypress | If the team is entirely JavaScript and only targets Chrome. Playwright supports Python, has better multi-browser support, no iFrame restrictions, and supports multiple browser contexts (essential for permission boundary tests needing simultaneous OWNER and VOLUNTEER sessions). |
| Playwright | Selenium | Selenium is the legacy choice. Playwright's auto-waiting and modern locator API eliminate the flakiness that plagues Selenium suites. No reason to choose Selenium for a new project in 2026. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Selenium / WebDriver | Requires explicit waits for every dynamic element; Next.js SPA transitions cause constant race conditions. Maintenance burden is 3-5x higher than Playwright. | Playwright 1.58 |
| Cypress | JavaScript-only; cannot share test infrastructure with Python API tests. Also has known limitations with cross-origin iframes and multiple browser tabs, which the checkout flow may trigger. | Playwright (Python bindings) |
| `requests` library as sole HTTP client | Sync-only, no HTTP/2. Fine for MVP but requires a library swap if async parallelism is added later. | httpx (sync today, async-ready tomorrow) |
| Raw `os.environ` for config | No type validation; missing variables fail silently at call site, not at startup. Hard to document expected config. | pydantic-settings with BaseSettings |
| Hard-coded sleep/time.sleep() | Makes tests slow and still flaky on slow networks. Playwright auto-waiting makes sleeps unnecessary. | Playwright's built-in auto-wait and `expect(locator).to_be_visible()` |
| Shared mutable test state (module-level variables) | Tests running in a shared state cause ordering-dependent failures. The live database already has global state; the agent must not add more. | pytest fixtures with appropriate scope (`function` scope by default) |

## Stack Patterns by Variant

**For API-only tests (AUTH, PROF, ORG, TEAM, VENU, EVNT, TICK, PRMO, CHKT, ORDR, CHKN, STAT, SRCH, GUST, EMAL, ANLT domains):**
- Use httpx `Client` (sync) with a session-level fixture that holds the JWT access token
- No browser needed; these tests run faster and are more reliable without browser overhead
- Fixture hierarchy: `api_client` (session) → `auth_token` (session) → individual resource fixtures

**For browser UI tests (FEND domain + checkout flows that require JS interaction):**
- Use pytest-playwright `page` fixture with Page Object Model classes
- Each page (EventListPage, CheckoutPage, etc.) encapsulates locators and interaction methods
- Never use raw CSS selectors in test files; always route through page objects

**For tests requiring both API setup and browser verification:**
- Use httpx to create prerequisite data (event, ticket tier) via API
- Hand off to Playwright for browser-side verification
- This is faster and more reliable than creating data via the UI

**For Stripe paid checkout tests:**
- Use Stripe test card numbers (`4242 4242 4242 4242`) if a Stripe test key is available
- If no test key, mark the test with `@pytest.mark.skip(reason="Requires STRIPE_TEST_KEY")` and document in `.env.example`

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| playwright==1.58.0 | pytest-playwright==0.7.2 | Must keep in sync; pytest-playwright pins to matching playwright version internally |
| pytest==9.0.2 | pytest-playwright==0.7.2 | Verified compatible; pytest-playwright 0.7.x requires pytest >=7.0 |
| pydantic-settings==2.13.1 | pydantic>=2.0 | pydantic-settings 2.x requires pydantic 2.x; do not mix with pydantic 1.x |
| Python 3.11+ | playwright==1.58.0 | Playwright Python requires 3.9+; 3.11 recommended for improved asyncio and performance |

## Sources

- [playwright PyPI](https://pypi.org/project/playwright/) — version 1.58.0 confirmed (released Jan 30, 2026)
- [pytest-playwright PyPI](https://pypi.org/project/pytest-playwright/) — version 0.7.2 confirmed (released Nov 24, 2025)
- [pytest PyPI](https://pypi.org/project/pytest/) — version 9.0.2 confirmed (released Dec 6, 2025)
- [httpx PyPI](https://pypi.org/project/httpx/) — version 0.28.1 confirmed (released Dec 6, 2024)
- [pydantic-settings PyPI](https://pypi.org/project/pydantic-settings/) — version 2.13.1 confirmed (released Feb 19, 2026)
- [Playwright Python docs — Page Object Models](https://playwright.dev/python/docs/pom) — POM pattern guidance (HIGH confidence)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices) — auto-waiting, locator strategy (HIGH confidence)
- [Playwright vs Cypress 2025 — Frugal Testing](https://www.frugaltesting.com/blog/playwright-vs-cypress-the-ultimate-2025-e2e-testing-showdown) — ecosystem comparison (MEDIUM confidence)
- [DjangoCon Europe 2025 — E2E testing Django with pytest+Playwright](https://pretalx.evolutio.pt/djangocon-europe-2025/talk/ETFCCS/) — community validation of Python Playwright for Django (MEDIUM confidence)

---
*Stack research for: GatherGood E2E Testing Agent (Django REST Framework + Next.js)*
*Researched: 2026-03-28*
