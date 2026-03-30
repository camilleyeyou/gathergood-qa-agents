---
phase: 07-digital-literacy-persona-agents
plan: 03
subsystem: testing
tags: [pytest, playwright, anthropic, persona-agents, friction-score, conftest, fixtures]

# Dependency graph
requires:
  - phase: 07-01
    provides: personas.py (Persona dataclass, ALL_PERSONAS, OPTIMAL_STEPS), persona_runner.py (run_persona_scenario), artifact_writer.py (save_persona_result), friction_scorer.py
  - phase: 07-02
    provides: generate_persona_report.py (generate_report_from_results), persona_report.html.j2 template
  - phase: 06-ai-qa-agents
    provides: PlaywrightComputerBackend, run_agent_scenario, ai_agents/conftest.py pattern
provides:
  - pytest conftest for persona_agents with session-scoped run_id, claude_client, base_url, api_url fixtures
  - Function-scoped agent_backend and record_persona_result fixtures
  - Auto-skip when ANTHROPIC_API_KEY is missing via pytest_collection_modifyitems
  - Auto HTML report generation via pytest_sessionfinish hook
  - 15 parametrized persona test functions (5 personas x 3 flows) as separate named functions
  - API setup helpers for browsing and checkout flows (creates test data via httpx)
  - persona_agent marker registered in pytest.ini
affects: [07-04-PLAN.md, phase 07 completion]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Session-scoped run_id fixture stored as module-level var for sessionfinish hook access"
    - "record_persona_result callable appends to _collected_results list AND stores on request.node for makereport hook"
    - "pytest_sessionfinish generates HTML report from in-memory results via generate_report_from_results()"
    - "15 separate named test functions (not parametrized) for granular -k filter support"
    - "max_iterations=15 for fast personas (TECH_SAVVY, IMPATIENT), 25 for slower personas (CASUAL, LOW_LITERACY, NON_NATIVE)"

key-files:
  created:
    - tests/persona_agents/conftest.py
    - tests/persona_agents/test_persona_sweep.py
  modified:
    - pytest.ini

key-decisions:
  - "Session run_id stored as module-level _session_run_id so pytest_sessionfinish can access it outside fixture scope"
  - "15 separate named test functions (not parametrized) per PLAN.md spec — enables -k 'low_literacy and registration' filtering"
  - "_setup_registration_flow() needs no API setup — registration page is always available"
  - "_setup_browsing_flow() and _setup_checkout_flow() create isolated test data via httpx to avoid depending on pre-existing database state"

patterns-established:
  - "Persona test: setup() -> page.goto() -> run_persona_scenario() -> result['flow'] = X -> save_persona_result() -> record_persona_result() -> assert friction_score"

requirements-completed: [P7-SC1, P7-SC2, P7-SC5]

# Metrics
duration: 15min
completed: 2026-03-30
---

# Phase 7 Plan 3: Persona Test Infrastructure Summary

**pytest conftest with session/function-scoped fixtures, auto-skip, and report hook wired to 15 named persona/flow test functions that produce JSON artifacts and assert friction scores**

## Performance

- **Duration:** 15 min
- **Started:** 2026-03-30T00:00:00Z
- **Completed:** 2026-03-30T00:15:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Created `tests/persona_agents/conftest.py` with 6 fixtures (claude_client, agent_backend, base_url, api_url, run_id, record_persona_result) and 3 hooks (pytest_configure, pytest_collection_modifyitems, pytest_sessionfinish)
- Created `tests/persona_agents/test_persona_sweep.py` with exactly 15 individually named test functions covering all 5 personas x 3 flows
- Registered `persona_agent` marker in pytest.ini alongside existing markers
- API setup helpers use httpx to create isolated test data per run (registration, browsing, checkout flows)
- `pytest tests/persona_agents/ --collect-only` reports 15 test items

## Task Commits

Each task was committed atomically:

1. **Task 1: Create persona conftest with fixtures, skip logic, and report hook** - `cfaf176` (feat)
2. **Task 2: Create 15 persona test functions (5 personas x 3 flows)** - `b163fc7` (feat)

**Plan metadata:** (to be added after final commit)

## Files Created/Modified

- `tests/persona_agents/conftest.py` - Session fixtures, auto-skip hook, sessionfinish report generation, makereport HTML extras
- `tests/persona_agents/test_persona_sweep.py` - 15 individual test functions for all 5 personas x 3 flows with API setup helpers
- `pytest.ini` - Added persona_agent marker registration

## Decisions Made

- Session run_id stored as module-level `_session_run_id` so `pytest_sessionfinish` can access it outside the fixture scope (fixtures aren't available in session hooks)
- 15 separate named test functions instead of parametrized — allows `pytest -k "low_literacy and registration"` to run a single persona/flow combo
- `_setup_registration_flow()` needs no API setup — just returns the /register URL since registration always works on a fresh user
- `_setup_browsing_flow()` and `_setup_checkout_flow()` create their own isolated org/event/tier via the live API to guarantee test data exists regardless of database state

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. Tests automatically skip if ANTHROPIC_API_KEY is not in .env.

## Next Phase Readiness

- Full 15-test persona sweep is runnable via `pytest tests/persona_agents/`
- Each test produces a JSON artifact in `reports/persona/<run_id>/`
- After all tests complete, HTML matrix report auto-generated at `reports/persona/<run_id>/persona_matrix.html`
- Ready for Phase 7 Plan 4 (final integration, documentation, or any remaining phase work)

---
*Phase: 07-digital-literacy-persona-agents*
*Completed: 2026-03-30*
