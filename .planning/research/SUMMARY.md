# Project Research Summary

**Project:** GatherGood E2E Testing Agent
**Domain:** Automated QA — REST API + Browser UI against Django REST Framework + Next.js
**Researched:** 2026-03-28
**Confidence:** HIGH

## Executive Summary

The GatherGood E2E testing agent is a Python-based automated QA tool targeting a live Railway-deployed Django REST Framework backend and a Vercel-deployed Next.js frontend. Research across all four domains converges on a single clear recommendation: use Python + pytest as the test runner, httpx for API-layer tests, and pytest-playwright for browser UI tests. This unified Python stack is the correct choice because the backend is Python/Django, the spec (TEST_SPEC.md) already defines 79 explicit requirement IDs that tests must map to, and Playwright's Python bindings are now mature enough to match the TypeScript Playwright experience. Cypress and Selenium are definitively ruled out — Cypress for its JavaScript-only constraint and tab/iframe limitations, Selenium for its legacy architecture and maintenance burden.

The single most important design decision is to build the foundation correctly before writing a single test case. The agent is targeting a live production database with no rollback mechanism. Every test run writes real data. This means the naming strategy (unique run-prefixed identifiers), teardown harness, and authentication fixture (with JWT refresh handling) must be the first deliverables, not afterthoughts. A session-scoped auth fixture that logs in once and refreshes the 30-minute access token before expiry underpins every other phase.

The key risks are live database pollution, JWT expiry cascading to mass failures, brittle CSS selectors breaking on Next.js deploys, and Stripe live-mode inadvertently processing real payments. All of these are preventable with known patterns — unique data factories, token refresh wrappers, semantic Playwright locators, and Stripe mode detection — and the pitfalls research has mapped each risk to the specific phase where it must be addressed. The overall architecture is well-understood; there are no novel integration challenges here.

## Key Findings

### Recommended Stack

The recommended stack is Python 3.11+, pytest 9.0.2, httpx 0.28.1, playwright 1.58.0 (Python bindings), and pytest-playwright 0.7.2. Supporting libraries are pydantic-settings 2.13.1 for type-safe environment variable validation, faker 33.x for unique test data generation, and pytest-html 4.x for local HTML reports. All versions are verified against PyPI as of 2026-03-28 — this is not speculative stack selection.

The split between httpx (API tests) and pytest-playwright (UI tests) within a single pytest session is the defining architectural pattern. API tests run without a browser, are 10-100x faster, and cover the majority of the 79 requirements. Browser tests cover only the 10 FEND requirements and checkout UI flows where JavaScript interaction is required. Both test types share the same session-scoped auth fixture, so no duplicate login overhead occurs.

**Core technologies:**
- Python 3.11+: Agent runtime — keeps stack unified with Django backend; pytest is Python-native
- pytest 9.0.2: Test runner — parameterization, fixture scoping, plugin ecosystem; no alternative matches it
- httpx 0.28.1: API HTTP client — sync/async API, request/response inspection; preferred over requests for async-readiness
- playwright 1.58.0 (Python): Browser automation — auto-waiting eliminates sleep() calls; Trace Viewer for debugging
- pytest-playwright 0.7.2: Playwright-pytest integration — provides page/browser/context fixtures automatically
- pydantic-settings 2.13.1: Config validation — fails fast at startup if required env vars are missing
- faker 33.x: Unique test data — prevents collision against live database across runs

### Expected Features

The feature set is fully defined by TEST_SPEC.md's 79 requirements. The research clarifies which features are non-negotiable for v1, which should be added after initial validation, and which to explicitly defer.

**Must have (table stakes):**
- JWT authentication handling with token refresh — 100% of tests depend on this
- Unique test data per run (uuid/timestamp-prefixed) — mandatory with no test DB reset
- Teardown / cleanup of created resources — live DB has no rollback
- API test coverage of all 79 requirements — the core deliverable
- Permission boundary matrix (OWNER / MANAGER / VOLUNTEER) — common auth regression vector
- Browser UI tests (FEND-01 to FEND-10) — navigation, checkout UI, responsive design
- Pass/fail report mapped to TEST_SPEC.md requirement IDs — stakeholder-facing output
- Free checkout flow validation — safe to run regardless of Stripe mode
- Edge case coverage: expired promos, capacity overflow, cancelled-event checkout attempts

**Should have (differentiators):**
- Screenshot and trace on failure — zero-config in Playwright, high value for debugging
- Stripe mode detection — auto-skip paid checkout tests if live-mode detected
- HMAC QR code format validation — retrieve from API, then verify format and use in check-in tests
- Status transition guard tests — verify illegal state changes return 400/403
- JSON results artifact — machine-readable output for future CI integration
- Idempotent re-run behavior — verified by running twice with no added failures

**Defer (v2+):**
- CI/CD pipeline integration — explicitly out of scope for v1; add once suite is stable
- Parallel test execution — requires isolated test database strategy; not viable on live deployment
- Visual regression (screenshot diff) — explicitly out of scope; high false-positive rate
- Load/performance testing — out of scope; would disrupt real users on live deployment

### Architecture Approach

The architecture follows a layered pattern: CLI entry point (pytest invocation) → test orchestration (conftest.py + pytest config) → fixture layer (session-scoped auth, API client, browser context) → test suite layer (tests/api/ and tests/ui/) → support layer (page objects, API helpers, data factories) → reporter layer (pytest-html, JUnit XML, console). The hard separation between tests/api/ and tests/ui/ is a deliberate design choice that allows API-only runs without loading Playwright, and vice versa.

**Major components:**
1. conftest.py (root) — session-scoped auth fixture; shared JWT token and httpx client for all tests
2. tests/api/ — 16 test modules, one per TEST_SPEC domain (AUTH, ORG, EVNT, TICK, PRMO, CHKT, ORDR, CHKN, STAT, SRCH, GUST, EMAL, PUBL, ANLT, PROF, VENU)
3. tests/ui/ — 4 Playwright test modules (navigation, checkout UI, responsive, public UI)
4. pages/ — Page Object Models (LoginPage, EventPage, CheckoutPage, DashboardPage); selectors live here, not in test files
5. factories/ — Unique-per-run data generators (unique_email(), org_payload(), event_payload()); uuid4-suffixed
6. helpers/ — Pure assertion helpers (assert_ok(), HMAC QR builder/validator, token extraction)
7. Reporter — pytest-html (HTML report), --junitxml (XML), console -v output with requirement ID markers

The requirement ID marker pattern (`@pytest.mark.req("AUTH-01")`) is a critical architectural decision: it links every test function to its TEST_SPEC.md requirement, making the report directly auditable against the specification.

### Critical Pitfalls

1. **Live database pollution** — Every test run creates real records with no rollback. Use `test-{run-id}-` namespace prefixes on all created data; build a session teardown that deletes resources in reverse dependency order. Define this strategy before writing any test cases. Recovery is medium-cost: a one-time cleanup script against live API endpoints.

2. **JWT token expiry causing silent cascade failures** — 30-minute access tokens will expire during a full 79-requirement suite run. Implement a token manager that proactively refreshes 5 minutes before expiry using the 7-day refresh token. Treat 401 responses as harness-level concerns (refresh + retry), not test failures. Failing to handle this causes every test after the 30-minute mark to fail with a misleading "401 Unauthorized" message.

3. **Test order dependency creating cascade failures** — When early tests fail (e.g., auth), downstream tests fail not because they are broken but because their prerequisites don't exist. Design domain test groups to be independently runnable: each group creates its own prerequisites via fixtures rather than relying on globals from prior groups. Distinguish integration-sequence tests (intentionally chained) from domain unit tests (independently runnable).

4. **Brittle UI selectors breaking on Next.js hydration/Tailwind deploys** — CSS class selectors break on every frontend deploy. Use Playwright semantic locators in priority order: getByRole() > getByLabel() > getByText() > getByTestId() > CSS as last resort. Request data-testid attributes from the frontend team for interactive elements that lack semantic roles.

5. **Stripe live-mode damage** — The deployed backend's Stripe mode is unknown. If paid checkout tests run against live-mode Stripe keys with test card numbers, they produce malformed orders in the production database. Implement mode detection before any paid checkout test: attempt a test card and check whether it is rejected with card_error (live mode) or succeeds (test mode). Skip paid tests cleanly if live-mode detected; never fail them.

6. **HMAC QR code generation from wrong assumptions** — Do not synthesize QR codes with computed HMAC values. The HMAC secret is held by the backend and not exposed. Retrieve real QR codes from the GET /orders/{id}/tickets/ endpoint after completing a checkout. Use the API-returned QR string as check-in test input; test the invalid-QR case by mutating a valid string.

7. **Permission test state escalation** — Shared test users across permission scenarios contaminate boundary tests. Create fresh users for each role (OWNER, MANAGER, VOLUNTEER) at the start of permission tests. Assert the current role as a precondition. Verify rejection (403) before acceptance (200).

## Implications for Roadmap

Based on combined research, the build order is dictated by hard technical dependencies. Auth and data isolation are not phase 1 because they are easy — they are phase 1 because nothing else is possible or safe without them.

### Phase 1: Foundation and Infrastructure

**Rationale:** Every other phase depends on auth, config, and data isolation. Building tests before the foundation means rewriting them when these are added. The pitfalls research explicitly maps database pollution and JWT expiry to "Phase 1 — must be addressed before writing any test case."
**Delivers:** Project scaffold (conftest.py, pytest.ini, requirements.txt), environment variable config (.env + pydantic-settings), session-scoped auth fixture with token refresh, data factories with unique-per-run prefixes, teardown harness, Railway health-check on suite startup, CLI entry point.
**Addresses:** Unique test data per run, teardown/cleanup, JWT auth with refresh, environment variable config.
**Avoids:** Live DB pollution (Pitfall 1), JWT expiry cascade (Pitfall 2).

### Phase 2: API Test Suite — Core Domain Coverage

**Rationale:** API tests cover the majority of the 79 requirements and have no browser dependency. They run faster and are more reliable than browser tests. The domain dependency chain (org → event → ticket tier → checkout → order → check-in) dictates the internal ordering within this phase. Permission boundary tests require team management tests to run first.
**Delivers:** Full API test coverage of AUTH-01–05, PROF-01–02, ORG-01–04, TEAM-01–04, VENU-01–03, EVNT-01–09, TICK-01–04, PRMO-01–04, ORDR-01–07, CHKN-01–06, MCHK-01–02, STAT-01–03, SRCH-01, GUST-01–02, EMAL-01–04, PUBL-01–05, ANLT-01–03. Requirement ID markers on all tests. Permission boundary matrix (3 roles x N actions).
**Uses:** httpx.Client, session-scoped auth fixture, data factories, API helpers.
**Implements:** tests/api/ module structure, conftest.py fixture hierarchy, helpers/ and factories/ support layer, requirement ID marker plugin.
**Avoids:** Test order dependency cascade (Pitfall 3), permission state escalation (Pitfall 7).

### Phase 3: Browser UI Test Suite

**Rationale:** UI tests require the API test suite to exist first, because browser auth state is derived from the API auth fixture. The Page Object Model and selector conventions must be established before any UI test is written, not retrofitted afterward.
**Delivers:** Playwright browser context with pre-loaded auth state (storageState), Page Object Models (LoginPage, EventPage, CheckoutPage, DashboardPage), FEND-01–10 browser tests (navigation, checkout UI, responsive design, public browse), screenshot and trace on failure.
**Uses:** pytest-playwright, Playwright browser contexts, storageState for auth sharing.
**Implements:** tests/ui/ module structure, pages/ POM layer, browser_auth fixture.
**Avoids:** Brittle UI selectors (Pitfall 5) — selector conventions established from day one.

### Phase 4: Checkout, Payments, and Orders

**Rationale:** Checkout tests depend on published events with active ticket tiers (Phase 2 prerequisite). Stripe mode detection must run before any paid checkout test is attempted. This phase is isolated because it touches live payment infrastructure and requires careful gating.
**Delivers:** Free checkout flow (CHKT-01–08 for free tier), Stripe mode detection logic, paid checkout tests gated on mode detection (CHKT-09–12), order verification (ORDR-01–07), HMAC QR format validation (QR retrieved from orders API), check-in flow tests (CHKN-01–06, MCHK-01–02), teardown of payment-related objects.
**Uses:** httpx for checkout API, Playwright for checkout UI steps, Stripe test card 4242 4242 4242 4242.
**Avoids:** Stripe live-mode damage (Pitfall 4), HMAC generation from wrong assumptions (Pitfall 6).

### Phase 5: Edge Cases, Validation, and Report Polish

**Rationale:** Edge cases require the full happy path to be stable first. Report completeness (all 79 requirement IDs listed with PASS/FAIL/SKIP) can only be verified once all tests exist.
**Delivers:** Edge case tests (expired promos, capacity overflow, cancelled-event checkout), status transition guard tests (illegal state changes return 400/403), idempotency verification (two sequential full runs produce identical results), report completeness check (all 79 IDs covered), JSON results artifact.
**Addresses:** Status transition guards, edge case coverage, idempotent re-run behavior, JSON results artifact.

### Phase Ordering Rationale

- Foundation before tests is non-negotiable: the live DB constraint makes naming strategy and teardown a prerequisite, not an enhancement.
- API before browser: browser auth state derives from the API auth fixture; also, API tests cover more requirements at lower cost.
- Core API domains before checkout: checkout requires a published event with a ticket tier; the domain dependency chain in TEST_SPEC.md enforces this order.
- Checkout isolated in its own phase: the Stripe risk profile is distinct from other API tests and warrants separate treatment.
- Edge cases last: they require stable happy-path tests as a baseline; they also need the full fixture infrastructure to be in place.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 4 (Checkout/Payments):** Stripe mode detection logic requires verification against the actual GatherGood deployment's Stripe configuration. The API response shape for a test-card rejection needs to be observed empirically to write reliable detection logic.
- **Phase 4 (HMAC QR):** The exact QR string format from the live API needs empirical verification before writing the format assertion. TEST_SPEC.md documents the format; confirming the live API matches before writing tests prevents a false-positive validation failure.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** pytest fixture scoping and pydantic-settings config are thoroughly documented; no research needed during planning.
- **Phase 2 (API Test Suite):** httpx + pytest patterns for REST API testing are mature and well-documented. The domain structure is defined by TEST_SPEC.md.
- **Phase 3 (Browser UI):** Playwright POM pattern and storageState auth are official documented patterns with no ambiguity.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All package versions verified against PyPI; official Playwright Python docs confirm patterns; DjangoCon 2025 community validation |
| Features | HIGH | TEST_SPEC.md fully defines the feature set; research confirms which are table stakes vs. differentiators vs. anti-features |
| Architecture | HIGH | Standard pytest fixture hierarchy and POM pattern are well-documented; layered structure is unambiguous for this domain |
| Pitfalls | HIGH | 7 critical pitfalls identified across 15+ current sources; all have documented prevention strategies and recovery costs |

**Overall confidence:** HIGH

### Gaps to Address

- **Stripe mode (live vs. test) of deployed GatherGood backend:** Unknown at research time. The detection logic is defined; the empirical confirmation (what does a test-card rejection look like against this specific backend?) must happen during Phase 4 implementation.
- **QR code response shape from live API:** TEST_SPEC.md documents the format `{order_id}:{tier_id}:{ticket_id}:{hmac_sha256_first16}`. Confirm this matches the actual API response before writing HMAC validation in Phase 4.
- **Token expiry timing:** Access token TTL documented as 30 minutes; verify against the live backend's actual JWT configuration at Phase 1 implementation to calibrate the refresh threshold.
- **data-testid attribute availability in GatherGood frontend:** Some UI elements may lack semantic roles and may not have data-testid attributes. If the frontend team cannot add them, CSS selectors become unavoidable for specific elements — document which ones at Phase 3.

## Sources

### Primary (HIGH confidence)
- [playwright PyPI](https://pypi.org/project/playwright/) — version 1.58.0 confirmed
- [pytest-playwright PyPI](https://pypi.org/project/pytest-playwright/) — version 0.7.2 confirmed
- [pytest PyPI](https://pypi.org/project/pytest/) — version 9.0.2 confirmed
- [httpx PyPI](https://pypi.org/project/httpx/) — version 0.28.1 confirmed
- [pydantic-settings PyPI](https://pypi.org/project/pydantic-settings/) — version 2.13.1 confirmed
- [Playwright Python docs — Page Object Models](https://playwright.dev/python/docs/pom) — POM pattern
- [Playwright Python docs — API Testing](https://playwright.dev/python/docs/api-testing) — API test patterns
- [Playwright Best Practices](https://playwright.dev/docs/best-practices) — selector strategy, auto-waiting
- [Playwright Authentication docs](https://playwright.dev/docs/auth) — storageState pattern
- [pytest fixture documentation](https://docs.pytest.org/en/stable/how-to/fixtures.html) — session scope, fixture hierarchy
- [Stripe Automated Testing docs](https://docs.stripe.com/automated-testing) — test card numbers, mode behavior
- [Playwright Locators docs](https://playwright.dev/docs/locators) — selector priority order

### Secondary (MEDIUM confidence)
- [DjangoCon Europe 2025 — E2E testing Django with pytest+Playwright](https://pretalx.evolutio.pt/djangocon-europe-2025/talk/ETFCCS/) — community validation
- [Bunnyshell: Best Practices for E2E Testing 2026](https://www.bunnyshell.com/blog/best-practices-for-end-to-end-testing-in-2025/) — isolation and cleanup patterns
- [Semaphore: How to Avoid Flaky Tests in Playwright](https://semaphore.io/blog/flaky-tests-playwright) — anti-flakiness patterns
- [BrowserStack: Playwright Selector Best Practices](https://www.browserstack.com/guide/playwright-selectors-best-practices) — selector hierarchy
- [CloudQA: Why Traditional E2E API Testing is Failing in 2026](https://cloudqa.io/why-traditional-e2e-api-testing-is-failing-in-2026/) — pitfall context
- [Frugal Testing: Playwright vs Cypress 2025](https://www.frugaltesting.com/blog/playwright-vs-cypress-the-ultimate-2025-e2e-testing-showdown) — ecosystem comparison
- [Manalivesoftware: How to Clean Test Data from E2E Tests](https://manalivesoftware.com/articles/how-to-clean-test-data-from-end-to-end-tests/) — teardown patterns
- [Autonoma: Django Playwright Testing Guide](https://www.getautonoma.com/blog/django-playwright-testing-guide) — Django-specific integration
- [Better Stack: Avoiding Flaky Playwright Tests](https://betterstack.com/community/guides/testing/avoid-flaky-playwright-tests/) — timing and hydration
- [Thunders: Modern E2E Test Architecture Patterns](https://www.thunders.ai/articles/modern-e2e-test-architecture-patterns-and-anti-patterns-for-a-maintainable-test-suite) — architecture patterns
- [Moldstud: Common Stripe Integration Mistakes](https://moldstud.com/articles/p-common-mistakes-developers-make-when-using-stripe-payment-processing-avoid-these-pitfalls/) — Stripe pitfalls

---
*Research completed: 2026-03-28*
*Ready for roadmap: yes*
