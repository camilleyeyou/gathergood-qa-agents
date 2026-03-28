# Pitfalls Research

**Domain:** E2E Testing Agent — Django REST + Next.js live deployment
**Researched:** 2026-03-28
**Confidence:** HIGH (critical pitfalls verified across multiple current sources)

---

## Critical Pitfalls

### Pitfall 1: Live Database Pollution From Tests That Don't Clean Up

**What goes wrong:**
Every test run creates real records in the production database — users, events, organisations, orders, tickets. Because there is no isolation layer, accumulated test records compound across runs. Future test assertions fail because they find multiple records when they expect one, or they pick up stale records from previous runs.

**Why it happens:**
Developers build the happy path first (create, assert pass) and defer cleanup. On a live target this is especially dangerous because there is no rollback mechanism — the API does not expose mass-delete endpoints for most resources, and direct DB access is unavailable.

**How to avoid:**
- Use a deterministic namespace prefix on all test-created data: `test-{run-id}-` for email addresses, org names, event titles, etc. This lets you identify and delete test records across runs.
- Build a teardown phase that calls the API to delete all resources created during the run, in reverse dependency order (tickets before orders, orders before events, events before venues, etc.).
- Where deletion is not available via the API (e.g. orders once confirmed), document which resources are irrecoverable and flag them explicitly in the run report.
- Maintain a "test manifest" of all created resource IDs during the run so cleanup is explicit and auditable.

**Warning signs:**
- Subsequent test runs producing `409 Conflict` or `duplicate` errors on resource creation
- Assertions like "should have exactly 1 event" returning 2+ events
- Growing list of `test-*` named entities visible in the live UI

**Phase to address:** Phase 1 (Foundation) — define the naming strategy and teardown harness before writing a single test case.

---

### Pitfall 2: JWT Token Expiry Mid-Suite Causes Silent Cascading Failures

**What goes wrong:**
The GatherGood backend issues 30-minute access tokens. A full suite run covering 79 requirements across 10 domains can easily exceed 30 minutes. When the access token expires, API calls start returning 401. If the test harness does not handle this, every subsequent test fails — and the failure message is "401 Unauthorized" not "token expired", making the root cause non-obvious.

**Why it happens:**
JWT expiry is handled at the application level, not by the HTTP client. Developers write tests that authenticate once at the top, assume the token is always valid, and never implement refresh logic.

**How to avoid:**
- Implement a token manager that wraps every API call: checks token age against a threshold (e.g. 25 minutes), calls the refresh endpoint before the token expires, and updates the stored token transparently.
- Use the 7-day refresh token to obtain new access tokens rather than re-authenticating from credentials.
- Log a clear warning whenever a token refresh occurs during the run so it is visible in the report.
- Treat `401` responses specifically: distinguish "credentials wrong" (test failure) from "token expired, now refreshed, should retry" (harness concern).

**Warning signs:**
- Tests that pass individually but fail when run as a full suite
- All failures after a certain test index reporting 401 status
- Full suite run time approaching 25–30 minutes without refresh logic

**Phase to address:** Phase 1 (Foundation) — the authentication harness must include refresh logic before building any other tests.

---

### Pitfall 3: Test Order Dependency Creates Cascade Failures

**What goes wrong:**
An integration sequence (like the 10-phase sequence in TEST_SPEC.md) naturally produces ordered data: create user → create org → create event → buy ticket → check in. Tests in later phases depend on IDs and state created by earlier tests. When any early test fails, all downstream tests fail too — not because they have bugs, but because their prerequisites don't exist. A single auth failure causes 60 tests to fail.

**Why it happens:**
Sequential business flows map naturally to sequential test design. Developers pass created resource IDs down the chain rather than creating independent data per test. This looks correct when the suite passes but becomes undebuggable when something early breaks.

**How to avoid:**
- Structure tests so each domain test group is independently runnable: it creates its own prerequisites rather than relying on globals from a previous test group.
- Use a shared fixture setup (pytest fixtures or Playwright setup functions) that creates base resources once per domain group, not once globally for the whole suite.
- Distinguish "integration sequence" tests (intentionally chained, used to verify the full 10-phase flow) from "unit" domain tests (independently runnable). Maintain both, with clear separation.
- When a prerequisite step fails, emit a clear `PRECONDITION FAILED` status rather than propagating the failure as a test failure in the downstream test.

**Warning signs:**
- More than 5 consecutive failures all tracing back to the same missing resource ID
- Test failure messages saying "NoneType has no attribute X" or "null ID" rather than assertion errors
- Tests that only fail when run after other tests, never in isolation

**Phase to address:** Phase 2 (API Test Suite) — establish the fixture architecture and isolation strategy before writing domain tests.

---

### Pitfall 4: Stripe Paid Checkout Tests Block or Damage Production Data

**What goes wrong:**
The GatherGood backend is running against Stripe in either test mode or live mode. If the test suite submits a checkout with a real PaymentIntent against live Stripe keys, it charges a real card. If it uses Stripe test card numbers against live keys, the transaction fails at the Stripe level in an unexpected way. Either way, incomplete order records may be left in the database in a partially-confirmed state.

**Why it happens:**
The deployed backend's Stripe mode (test vs. live) is not visible to the test agent. Developers assume the deployed site is in test mode without verifying. The Stripe test card `4242 4242 4242 4242` only works against test-mode keys — it will be rejected by live-mode keys.

**How to avoid:**
- Before writing any paid checkout tests, inspect the API response for a checkout attempt with a known Stripe test card. If the card is rejected with a Stripe `card_error` rather than succeeding, the backend is in live mode — mark paid checkout tests as `SKIPPED: live-mode-detected`.
- Do not attempt to force-pass paid checkout tests in live mode. Flag them clearly in the report as requiring test-mode keys.
- Free checkout tests (zero-amount) can always run safely regardless of Stripe mode.
- Document the detection logic explicitly in the test report so the team knows which tests were skipped and why.

**Warning signs:**
- Checkout endpoint returning Stripe error codes rather than a created PaymentIntent
- `stripe.error.CardError: No such card` or similar responses during test card usage
- Partially-created order records visible in the database after a failed checkout test

**Phase to address:** Phase 4 (Checkout Testing) — include a Stripe mode detection step at the start of the checkout test group.

---

### Pitfall 5: Brittle UI Selectors Break When Next.js Rerenders or Hydrates

**What goes wrong:**
Playwright tests that select elements by CSS class names (e.g. `.checkout-button`, `div.container > button:nth-child(2)`) break when Next.js hydrates the page, when Tailwind class names are purged/renamed during a deploy, or when a developer moves a wrapper element. A single style refactor breaks dozens of tests that have nothing to do with the changed component.

**Why it happens:**
CSS classes are the most visually obvious handles on elements. They are also the least stable. Next.js + Tailwind CSS generates utility class names that can change between builds. Hydration also introduces a window where elements exist in the DOM but are not yet interactive, causing timing-sensitive selector failures.

**How to avoid:**
- Prefer Playwright's semantic locators in this priority order: `getByRole()` > `getByLabel()` > `getByText()` > `getByTestId()` > CSS as last resort.
- For elements that lack semantic roles, request that the GatherGood frontend adds `data-testid` attributes to key interactive elements (checkout button, QR scan input, etc.) — these attributes have no reason to change.
- Use `waitForLoadState('networkidle')` or explicit `waitForResponse()` calls after navigation rather than `page.waitForTimeout()` to handle hydration.
- Never use `nth-child` or positional CSS selectors — use text content or role selectors instead.

**Warning signs:**
- Tests failing with "element not found" after a frontend deploy where no functionality changed
- Tests passing on first run but failing on retry (hydration timing)
- More than 20% of test failures attributable to selector errors rather than assertion failures

**Phase to address:** Phase 3 (UI Test Suite) — establish selector conventions before writing any browser automation tests.

---

### Pitfall 6: HMAC QR Code Tests Fail Due to Incorrect Secret or Format Assumptions

**What goes wrong:**
The QR check-in flow requires generating a valid HMAC-SHA256 token: `{order_id}:{tier_id}:{ticket_id}:{hmac_sha256_first_16_hex_chars}`. Tests that generate QR payloads using the wrong HMAC secret, the wrong field ordering, or the full hash instead of the first 16 hex characters will produce tokens that the backend rejects with `invalid QR` — even though the test logic appears correct.

**Why it happens:**
The QR format specification in TEST_SPEC.md is precise but easy to misread. The HMAC secret is a backend-held value not exposed in the API, so the test agent cannot derive valid QR codes from scratch. Developers assume they can generate test QR codes independently.

**How to avoid:**
- Do not generate QR codes from scratch in the test agent. Instead, complete the checkout flow to obtain a real order/ticket, then retrieve the generated QR code from the `GET /orders/{id}/tickets/` endpoint response. Use the QR value returned by the API as the input to check-in tests.
- Test HMAC validation failure cases (CHKN-05: invalid QR) by deliberately mutating a valid QR string (change one character), not by generating an invalid HMAC from scratch.
- Verify the QR format from the API response matches the documented format before using it in check-in tests.

**Warning signs:**
- All check-in tests returning `invalid QR` even for cases that should succeed
- HMAC values in test logs that are longer than 16 hex characters
- Check-in tests failing with 400 rather than the expected 200/409/422 status codes

**Phase to address:** Phase 4 (Orders/Tickets) and Phase 5 (Check-In) — retrieve real QR codes from ticket endpoints, do not synthesize them.

---

### Pitfall 7: Permission Boundary Tests Create Unintended State Escalation

**What goes wrong:**
Permission tests verify that MANAGER cannot do OWNER actions, VOLUNTEER cannot do MANAGER actions, etc. A badly ordered permission test that first creates a MANAGER user, then accidentally grants them OWNER privileges (e.g. via a test for the invite endpoint), and then runs permission boundary assertions — finds the boundary is not enforced because the test itself escalated permissions.

**Why it happens:**
Permission tests are written focusing on what the API should reject, not on ensuring the test user's current permission level is exactly what was intended. Tests share user accounts across permission scenarios, so earlier tests that modify roles contaminate later tests.

**How to avoid:**
- Create a fresh test user for each permission level at the start of permission boundary tests. Do not reuse users across permission scenarios.
- Assert the current permission level of the test user as a precondition step before running boundary tests.
- Verify rejection (403) before verifying acceptance (200) — this ensures the boundary is enforced before testing the happy path.
- Keep OWNER, MANAGER, and VOLUNTEER test accounts in separate pytest fixtures/Playwright contexts with no shared state.

**Warning signs:**
- Permission boundary tests intermittently passing — a flaky permission test is almost always a shared-state problem
- A test asserting 403 receiving 200 — check whether role was inadvertently elevated by a previous test
- Invite/role tests and permission boundary tests sharing the same user account

**Phase to address:** Phase 2 (API Test Suite, Team Management domain) — fixture design must isolate permission contexts.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Global auth token, no refresh | Simpler harness code | All tests after 30 min fail silently | Never — GatherGood tokens expire at 30 min |
| `time.sleep(2)` between steps | Avoids waiting for API responses | Slow suite, still flaky on slow connections | Never — use `waitForResponse` or retry logic |
| Hardcoded resource IDs (event ID, org ID) | Quick to write first tests | Suite breaks when those records are deleted | Never against a live database |
| Skip teardown for "simpler" test runs | Faster iteration during development | Permanent test data pollution in production DB | Development only, never in final agent |
| Catch-all `except Exception` in API wrappers | Prevents test crashes | Masks real errors as generic failures | Never — exceptions should surface with context |
| CSS class selectors for Playwright | Quick to write | Breaks on any frontend deploy | Only if `data-testid` is genuinely unavailable |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Stripe | Assuming deployed backend is in test mode | Detect mode by attempting a test card and checking the error type before running paid flow tests |
| Stripe | Leaving partial PaymentIntent records from failed tests | Run free-checkout tests first; skip paid tests if live-mode detected; always cancel created PaymentIntents in teardown |
| JWT refresh | Calling refresh with the access token instead of the refresh token | Store both tokens from login response; use refresh token specifically for the `POST /auth/token/refresh/` call |
| Railway (backend) | Cold start latency causing first API call timeouts | Add a health-check ping at suite startup with a 30-second timeout before beginning test execution |
| Vercel (frontend) | Edge cache returning stale pages during UI tests | Include `Cache-Control: no-cache` headers in test requests, or navigate to pages with a query param to bust cache |
| HMAC QR | Generating QR payloads with the wrong secret | Retrieve QR codes from the orders API, never generate independently |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Sequential API calls with no parallelism | Suite run time exceeds 45 minutes | Parallelise independent domain groups (auth, venues, public pages) where they do not share state | At 79+ test cases with network latency |
| Re-authenticating before every test | Adds 1-2 seconds per test, cumulative total is significant | Authenticate once per domain group using session fixtures, refresh as needed | Immediately at scale |
| Playwright launching a new browser for each test | Resource exhaustion and slow startup | Reuse browser context per domain group; only reset cookies/storage between groups | At 50+ Playwright tests |
| Waiting for full page load on every navigation | `networkidle` waits for all requests, which can stall on analytics/chat widgets | Use `load` state instead of `networkidle` unless the next action specifically requires all async calls to complete | On pages with third-party async scripts |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing test credentials (email/password) in plaintext in the test script | Credentials committed to source control or visible in logs | Use environment variables (`TEST_USER_EMAIL`, `TEST_USER_PASSWORD`) and a `.env` file excluded from version control |
| Logging full JWT access tokens in test output | Token can be replayed to impersonate test user | Log only the first 8 characters of tokens for debugging; mask the rest |
| Creating admin/owner test users that are never deleted | Persistent privileged accounts on production | Include all test user accounts in teardown; document accounts that cannot be deleted and disable them manually |
| Testing role escalation without expecting 403 | If the API has a bug, the test passes and the vulnerability is not caught | Always assert that escalation attempts return 403 before testing legitimate permission grants |

---

## "Looks Done But Isn't" Checklist

- [ ] **Test isolation:** Each test group creates its own data — verify by running groups in random order and confirming results are identical.
- [ ] **Teardown coverage:** After a full suite run, search the live database for `test-` prefixed records — there should be none remaining.
- [ ] **Token refresh:** Run the suite for longer than 30 minutes — verify no 401 failures appear after the 30-minute mark.
- [ ] **Stripe mode detection:** Confirm the checkout test group correctly identifies and skips paid tests in live mode without failing.
- [ ] **QR code retrieval:** Confirm check-in tests use QR codes retrieved from the orders API, not hardcoded or generated values.
- [ ] **Report completeness:** Verify the report lists every TEST_SPEC.md requirement ID (79 total) with a PASS/FAIL/SKIP status — not just the ones that ran.
- [ ] **Permission boundary tests:** Verify all three role levels (OWNER, MANAGER, VOLUNTEER) have independent fixture users that are created fresh per run.
- [ ] **Error messages:** Verify that assertion failures show the actual vs. expected value, the endpoint called, the HTTP status received, and the response body — not just "assertion failed".

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Live DB polluted with test data | MEDIUM | Identify all records with `test-` prefix via API (list endpoints with pagination); write a one-time cleanup script that deletes in dependency order; run and verify |
| Token expiry cascaded 40+ failures | LOW | Add refresh logic to the API wrapper; re-run the suite; the failures disappear |
| Selector breakage after frontend deploy | MEDIUM | Audit all failing selectors; replace with `getByRole`/`getByText`; request `data-testid` attributes for elements that have no semantic alternative |
| QR check-in tests all returning invalid | LOW | Switch to retrieving QR from the tickets endpoint rather than generating; re-run check-in group |
| Stripe live-mode charged a real card | HIGH | Immediately refund via Stripe dashboard; switch paid checkout tests to skip in live-mode; implement mode detection before re-running |
| Permission tests intermittently flaky | MEDIUM | Create independent fixture users per permission level; purge shared state; re-run with `--repeat-each 5` to confirm stability |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Live DB pollution | Phase 1: Foundation (naming strategy + teardown harness) | After full run, query API for `test-` records — zero remaining |
| JWT token expiry | Phase 1: Foundation (token manager with refresh) | Run suite for 35 minutes — no 401 failures |
| Test order dependency | Phase 2: API Test Suite (fixture isolation) | Run domain groups in reverse order — results identical |
| Stripe live-mode damage | Phase 4: Checkout Testing (mode detection) | Suite emits `SKIP: live-mode-detected` for paid tests, not FAIL |
| Brittle UI selectors | Phase 3: UI Test Suite (selector conventions) | Zero test failures attributable to selector errors after a frontend CSS-only deploy |
| HMAC QR generation | Phase 4 (Orders) + Phase 5 (Check-In) (retrieve from API) | Check-in tests pass against real QR codes from API response |
| Permission state contamination | Phase 2: API Test Suite (fixture design) | Permission tests pass when run in isolation AND as part of full suite |
| Stripe partial records | Phase 4: Checkout Testing (teardown for payment objects) | No orphaned orders in `pending` state after suite teardown |

---

## Sources

- [Why Traditional E2E API Testing is Failing in 2026 - CloudQA](https://cloudqa.io/why-traditional-e2e-api-testing-is-failing-in-2026/)
- [End-to-End Testing Challenges | Why E2E Tests Fail in 2026 - ACCELQ](https://www.accelq.com/blog/end-to-end-testing-challenges/)
- [Best Practices for End-to-End Testing - Bunnyshell](https://www.bunnyshell.com/blog/best-practices-for-end-to-end-testing-in-2025/)
- [How to Avoid Flaky Tests in Playwright - Semaphore](https://semaphore.io/blog/flaky-tests-playwright)
- [Authentication | Playwright official docs](https://playwright.dev/docs/auth)
- [Avoiding Flaky Tests in Playwright | Better Stack](https://betterstack.com/community/guides/testing/avoid-flaky-playwright-tests/)
- [How to Clean Test Data From End-to-End Tests - Manalive Software](https://manalivesoftware.com/articles/how-to-clean-test-data-from-end-to-end-tests/)
- [4 Ways to Handle Test Data for Your End-to-End Tests](https://dev-tester.com/4-ways-to-handle-test-data-for-your-end-to-end-tests/)
- [Common Mistakes Developers Make When Using Stripe - Moldstud](https://moldstud.com/articles/p-common-mistakes-developers-make-when-using-stripe-payment-processing-avoid-these-pitfalls/)
- [Stripe Automated Testing | official Stripe docs](https://docs.stripe.com/automated-testing)
- [15 Playwright Selector Best Practices - BrowserStack](https://www.browserstack.com/guide/playwright-selectors-best-practices)
- [Playwright Locators | official Playwright docs](https://playwright.dev/docs/locators)
- [Why Your Playwright Tests Are Still Flaky - Medium / CodeToDeploy](https://medium.com/codetodeploy/why-your-playwright-tests-are-still-flaky-and-its-not-because-of-timing-9c005d0e83a3)
- [E2E Tests: Avoiding the Top 3 Pitfalls - GAP](https://www.growthaccelerationpartners.com/blog/avoid-e2e-tests-pitfalls)
- [Testing JWT Tokens with Playwright - Medium](https://medium.com/@mahtabnejad/testing-jwt-tokens-with-playwright-2002a8b64341)

---
*Pitfalls research for: E2E Testing Agent — GatherGood (Django REST + Next.js)*
*Researched: 2026-03-28*
