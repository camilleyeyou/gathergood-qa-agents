# Feature Research

**Domain:** E2E Testing Agent — Automated QA for Django REST + Next.js web application
**Researched:** 2026-03-28
**Confidence:** HIGH (well-established domain with mature tooling; specific features verified against official docs and multiple sources)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features the test suite must have or it fails its core purpose. Missing any of these means the agent is not useful as a QA tool.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| API request execution (HTTP verbs, headers, body) | Every backend test requires making authenticated REST calls | LOW | Playwright's `APIRequestContext` covers this natively; no extra library needed |
| JWT authentication handling | 100% of protected endpoints require Bearer token; auth is step 0 | LOW | Store token in test context after login; pass as header on every subsequent call |
| Token refresh flow | Access tokens expire at 30 min; long test runs will hit expiry | MEDIUM | Intercept 401 responses, re-auth with refresh token, replay original request |
| Sequential test execution with shared state | Phases 1–10 in TEST_SPEC.md build on each other (create org → create event → checkout) | MEDIUM | Playwright's `--workers=1` with `storageState` or shared fixtures; ordering matters |
| Pass / fail result per test case | Consumers need "AUTH-01: PASS" not just an exit code | LOW | Playwright's built-in reporters (list, HTML, JSON) satisfy this |
| Exit code 0 on full pass, non-zero on any failure | Required for scripting and CI integration | LOW | Playwright default behavior |
| Clear failure messages with expected vs actual | Debugging failures without this is impractical | LOW | Playwright assertion errors include this; add custom messages for domain context |
| CLI invocation (`npm test` or `npx playwright test`) | Must be runnable with a single command | LOW | Standard Playwright config |
| Browser automation (UI flow testing) | TEST_SPEC.md includes FEND-01–10 frontend checks | MEDIUM | Playwright browser contexts; required for checkout UI, navigation, responsive tests |
| Page Object or equivalent abstraction | Without it, UI tests break on every DOM change | MEDIUM | Page Object Model (POM) is the standard Playwright pattern; essential for maintainability |
| Unique test data per run | Tests against live DB must not pollute each other or block re-runs | MEDIUM | Prefix emails/slugs with a run ID or timestamp; required because there is no test DB reset |
| Test cleanup / teardown | Orphaned test data accumulates across runs on the live deployment | MEDIUM | Delete created resources via API after each test or suite; mark data with a cleanup tag |
| Stripe test mode handling | Paid checkout tests will fail in live mode without test keys | MEDIUM | Gate paid-checkout tests on `STRIPE_TEST_KEY` env var; skip gracefully if absent |
| Environment variable configuration | Target URLs, credentials, Stripe keys must not be hardcoded | LOW | `.env` file + `dotenv`; document required vars in README |
| Timeout and retry configuration | Live deployed app has real network latency; flakiness from fixed waits is guaranteed | LOW | Playwright global `timeout`, `retries: 2` for network-sensitive assertions |

### Differentiators (Competitive Advantage)

Features beyond bare minimum that make this agent significantly more useful than a basic script.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Structured test report mapped to TEST_SPEC.md IDs | "AUTH-03 FAIL: Expected 200, got 422" links directly to the spec; zero hunting | MEDIUM | Annotate each test with its spec ID in the title; Playwright HTML report renders this clearly |
| HMAC QR code validation | Verifies the exact format `{order_id}:{tier_id}:{ticket_id}:{hmac_sha256_first16}` — not just that a QR exists | HIGH | Pure logic test; compute expected HMAC in Node, compare to API response; no QR scanner hardware needed |
| Permission boundary matrix tests | Proves OWNER > MANAGER > VOLUNTEER enforcement — a common auth regression vector | HIGH | Each role-gated action tested with each role; matrix of 3 roles × N actions |
| Edge case coverage (expired promos, capacity overflow, cancelled-event checkout) | Catches the bugs that cost users money or double-book events | HIGH | Requires setup: create promo, expire it, attempt use; requires capacity-capped tier |
| Status transition guard tests | Verifies illegal transitions are rejected (e.g., COMPLETED → PUBLISHED) | MEDIUM | Attempt each invalid transition; assert 400/403 response |
| Idempotent re-run behavior | Suite can be run twice in a row on the live system without failures from leftover data | MEDIUM | Unique data IDs per run + cleanup teardown; critical for live-DB target |
| JSON results artifact | Machine-readable output enables future CI integration or result diffing between runs | LOW | `playwright test --reporter=json` writes `test-results.json`; add to `.gitignore` |
| Screenshot on failure | Captures browser state at moment of failure for UI tests | LOW | Playwright `screenshot: 'only-on-failure'` in config; zero extra code |
| Trace on failure | Full action trace for debugging hard-to-reproduce UI failures | LOW | Playwright `trace: 'retain-on-failure'`; viewable in Playwright Trace Viewer |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem valuable but conflict with the project's constraints or create more problems than they solve.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Parallel test execution | Faster total runtime | Tests share a live database; parallelism causes race conditions (e.g., two runs creating conflicting unique slugs simultaneously) | Run with `--workers=1`; parallelism is only viable with isolated test databases |
| Visual regression (screenshot diff) | Catches CSS regressions | Explicitly out of scope (PROJECT.md); high false-positive rate from font rendering, animation timing, and deployment variability | Functional assertions on computed styles or element visibility if needed |
| Load / performance testing | Verify the site handles traffic | Explicitly out of scope; hammering the live deployment disrupts real users | Keep a separate k6 / Locust project if needed in the future |
| Full CI/CD pipeline integration | Automate test runs on every push | Out of scope for v1; adds infra complexity (secrets management, runner config, notification routing) | v1 is local CLI; add CI config in a later phase after suite is stable |
| Test generation via AI / natural language | Reduce test writing effort | The spec already exists (TEST_SPEC.md); AI-generated tests introduce uncertainty about what is actually being verified | Write explicit, spec-ID-annotated tests against TEST_SPEC.md directly |
| Mocking / stubbing the target API | Speeds up tests, removes network dependency | This is an E2E agent against the live deployment — mocking defeats the entire purpose | Accept live network calls; add appropriate timeouts and retries |
| Storing sensitive test credentials in version control | Simplifies setup | Credentials (test user passwords, Stripe test keys) in git is a security risk even for test accounts | `.env` file excluded from git; document required variables |
| Automated test data seeding via direct DB access | Reliable setup state | Agent has no direct DB access to the Railway-hosted PostgreSQL; bypasses the API and misses API-layer bugs | All setup through API calls using the test stack; DB state is a consequence of API behavior |

---

## Feature Dependencies

```
[CLI Entrypoint (`npx playwright test`)]
    └──requires──> [Playwright Config (env vars, timeout, reporters)]
                       └──requires──> [Environment Variable Setup (.env)]

[Any Protected API Test]
    └──requires──> [JWT Authentication (register + login)]
                       └──requires──> [Unique Test Data Per Run (avoid email collisions)]

[Organization Tests]
    └──requires──> [JWT Authentication]
                       └──enables──> [Event Tests]
                                         └──enables──> [Ticket Tier Tests]
                                                           └──enables──> [Checkout Tests]
                                                                             └──enables──> [Order / QR Tests]
                                                                                               └──enables──> [Check-In Tests]

[Checkout Tests (Paid)]
    └──requires──> [Stripe Test Mode Config]
    └──requires──> [Event Tests] (event must exist and be PUBLISHED)

[Permission Boundary Tests]
    └──requires──> [Team Management Tests] (invite member with role)
    └──requires──> [JWT Authentication] (authenticate as each role)

[HMAC QR Validation]
    └──requires──> [Order / Ticket Tests] (order must exist with ticket data)

[Browser UI Tests (FEND-01–10)]
    └──requires──> [Playwright Browser Context]
    └──enhanced-by──> [Page Object Model]
    └──enhanced-by──> [Screenshot on Failure]

[Screenshot on Failure] ──enhances──> [Browser UI Tests]
[Trace on Failure] ──enhances──> [Browser UI Tests]
[JSON Results Artifact] ──enhances──> [CLI Entrypoint]

[Token Refresh] ──conflicts-with-ignoring──> [Sequential Long Test Runs]
    (must handle or 30-min runs will silently fail with 401s)
```

### Dependency Notes

- **Any Protected API Test requires JWT Authentication:** Every domain except public pages (PUBL-01–05) and the registration endpoint itself requires a valid Bearer token. Auth is always Phase 1.
- **Checkout Tests require Event Tests:** A checkout requires a PUBLISHED event with at least one ACTIVE ticket tier. Events must be created and published before checkout tests run.
- **Permission Boundary Tests require Team Management:** You cannot test a VOLUNTEER's access without first inviting a user to a team with the VOLUNTEER role.
- **HMAC QR Validation requires Order Tests:** The QR code fields come from the order response. Order must be created by a successful checkout first.
- **Unique Test Data requires a run ID strategy:** All tests that register users, create organizations, or create events must incorporate a run-scoped prefix (e.g., timestamp or UUID) to prevent conflicts on re-runs against the live DB.
- **Token Refresh conflicts with ignoring 401s:** If the suite runs longer than 30 minutes without refreshing tokens, all remaining tests will silently fail with 401. Either implement refresh or split the suite into sessions under 30 minutes.

---

## MVP Definition

### Launch With (v1)

Minimum viable: every requirement in PROJECT.md Active list is covered and produces a pass/fail verdict.

- [ ] JWT auth flow (AUTH-01–05) — foundation; nothing else works without it
- [ ] Organization + team management (ORG-01–04, TEAM-01–04) — required for event creation
- [ ] Full event lifecycle (EVNT-01–09) including status transitions — core domain object
- [ ] Ticket tiers (TICK-01–04) and promo codes (PRMO-01–04) — prereqs for checkout
- [ ] Free checkout flow (CHKT-01–08 relevant to free) — validate the happy path without Stripe dependency
- [ ] Orders and QR code format validation (ORDR-01–07) — verify ticket issuance
- [ ] QR check-in flows (CHKN-01–06, MCHK-01–02) — core operational feature
- [ ] Permission boundary tests across OWNER/MANAGER/VOLUNTEER roles
- [ ] Edge cases: expired promos, capacity limits, cancelled-event checkout attempts
- [ ] Frontend UI tests (FEND-01–10) for navigation, responsive design, checkout flow
- [ ] HTML + JSON report output — pass/fail per test case by spec ID
- [ ] Unique test data per run + cleanup teardown — required for live DB safety

### Add After Validation (v1.x)

- [ ] Paid Stripe checkout tests (CHKT-09–12) — add when Stripe test keys are confirmed available; currently gated by external dependency
- [ ] Guest list CSV export (GUST-01–02) and email settings (EMAL-01–04) — lower risk, add once core suite is stable
- [ ] Event analytics (ANLT-01–03) — read-only; low risk to defer
- [ ] Token auto-refresh — add if suite runtime approaches 30 minutes

### Future Consideration (v2+)

- [ ] CI/CD pipeline integration — explicitly out of scope for v1; add when team wants automated runs on PR
- [ ] Parallel test execution — requires a test database strategy; not viable on live deployment
- [ ] Slack / webhook notifications on failure — useful for automated runs, not for local CLI v1

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| JWT auth + token management | HIGH | LOW | P1 |
| Unique test data per run | HIGH | LOW | P1 |
| API test coverage (all 79 requirements) | HIGH | HIGH | P1 |
| Pass/fail report by spec ID | HIGH | LOW | P1 |
| Test cleanup / teardown | HIGH | MEDIUM | P1 |
| Browser UI tests (FEND-01–10) | HIGH | MEDIUM | P1 |
| Permission boundary matrix | HIGH | HIGH | P1 |
| HMAC QR code validation | MEDIUM | MEDIUM | P2 |
| Edge case coverage | HIGH | HIGH | P2 |
| Status transition guard tests | MEDIUM | MEDIUM | P2 |
| Screenshot / trace on failure | MEDIUM | LOW | P2 |
| JSON results artifact | MEDIUM | LOW | P2 |
| Stripe paid checkout tests | HIGH | MEDIUM | P2 (blocked on keys) |
| Token auto-refresh | MEDIUM | MEDIUM | P2 (if runtime > 30 min) |
| CI/CD integration | MEDIUM | HIGH | P3 |
| Parallel execution | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

This is an internal agent, not a product — but the relevant comparators are the tools it could be built on top of (Playwright vs alternatives) and similar agent architectures.

| Feature | Playwright (recommended) | Cypress | pytest + requests |
|---------|--------------------------|---------|-------------------|
| API testing built-in | Yes (`APIRequestContext`) | Limited (cy.request is basic) | Yes (with `httpx` or `requests`) |
| Browser automation | Yes (Chromium, Firefox, WebKit) | Yes (Chromium, Firefox, exp. WebKit) | No (separate tool needed) |
| Parallel execution | Yes (native, free) | Paid (Cypress Cloud) | Yes (pytest-xdist) |
| HTML report | Yes (built-in) | Yes (built-in) | Via pytest-html plugin |
| JSON report | Yes (built-in) | Via plugin | Via pytest-json |
| Screenshot on failure | Yes (built-in) | Yes (built-in) | No |
| Trace viewer | Yes (built-in) | No | No |
| Python-native DX | No (TypeScript/JS) | No (JS only) | Yes |
| Django-native integration | Via pytest-playwright | No | Via pytest-django |
| Weekly downloads (2026) | ~25M | ~10M | N/A |

**Verdict:** Playwright (TypeScript) for a unified API + browser agent is the dominant choice. If the team strongly prefers Python, `pytest + httpx + pytest-playwright` is a viable hybrid but adds integration overhead. A dedicated Python approach with `pytest + httpx` for API tests and `pytest-playwright` for browser tests is the closest Python equivalent.

---

## Sources

- [Playwright Test Reporters — official docs](https://playwright.dev/docs/test-reporters) — HIGH confidence
- [Playwright API Testing — official docs](https://playwright.dev/python/docs/api-testing) — HIGH confidence
- [Playwright Running Tests — official docs](https://playwright.dev/docs/running-tests) — HIGH confidence
- [QA Wolf: 12 Best AI Testing Tools 2026](https://www.qawolf.com/blog/the-12-best-ai-testing-tools-in-2026) — MEDIUM confidence
- [OpenObserve: How AI Agents Automated Our QA](https://openobserve.ai/blog/autonomous-qa-testing-ai-agents-claude-code/) — MEDIUM confidence (real-world case study)
- [Thunders: Modern E2E Test Architecture Patterns](https://www.thunders.ai/articles/modern-e2e-test-architecture-patterns-and-anti-patterns-for-a-maintainable-test-suite) — MEDIUM confidence
- [Bunnyshell: Best Practices for E2E Testing 2026](https://www.bunnyshell.com/blog/best-practices-for-end-to-end-testing-in-2025/) — MEDIUM confidence
- [TestDino: Playwright vs Cypress 2026](https://testdino.com/blog/playwright-vs-cypress/) — MEDIUM confidence
- [BrowserStack: Playwright Test Report Guide 2026](https://www.browserstack.com/guide/playwright-test-report) — MEDIUM confidence
- [TestDevLab: 5 Test Automation Anti-Patterns](https://www.testdevlab.com/blog/5-test-automation-anti-patterns-and-how-to-avoid-them) — MEDIUM confidence
- [BlazeMeter: Why You Should Avoid Testing With Production Data](https://www.blazemeter.com/blog/production-data) — MEDIUM confidence
- [Autonoma: Django Playwright Testing Guide](https://www.getautonoma.com/blog/django-playwright-testing-guide) — MEDIUM confidence

---

*Feature research for: E2E Testing Agent (GatherGood platform)*
*Researched: 2026-03-28*
