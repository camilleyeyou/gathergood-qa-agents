---
phase: 06-ai-qa-agents
plan: 01
subsystem: testing
tags: [anthropic, computer-use, playwright, claude-sonnet, ai-agent]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: "pytest + Playwright + pydantic-settings infrastructure"
  - phase: 04-permissions-analytics-browser-ui
    provides: "UI test patterns and page fixture conventions"
provides:
  - "PlaywrightComputerBackend class translating Claude tool actions to Playwright calls"
  - "run_agent_scenario agent loop with iteration cap and input token cost cap"
  - "claude_client and agent_backend pytest fixtures"
  - "AGENT_SYSTEM_PROMPT for QA verdict generation"
  - "Skip-when-no-key logic for clean CI without ANTHROPIC_API_KEY"
affects: [06-02, 06-03]

# Tech tracking
tech-stack:
  added: [anthropic==0.86.0]
  patterns: [computer-use-backend, agent-loop-with-cost-cap, skip-on-missing-key]

key-files:
  created:
    - tests/ai_agents/__init__.py
    - tests/ai_agents/computer_use_backend.py
    - tests/ai_agents/agent_runner.py
    - tests/ai_agents/conftest.py
  modified:
    - requirements.txt
    - settings.py
    - .env.example

key-decisions:
  - "anthropic 0.86.0 pinned; computer_20251124 tool type with computer-use-2025-11-24 beta header"
  - "MAX_INPUT_TOKENS = 1_000_000 hard cost cap per scenario (AIQA-10)"
  - "Empty ANTHROPIC_API_KEY default with pytest_collection_modifyitems skip — not a pydantic validation error"

patterns-established:
  - "PlaywrightComputerBackend: Playwright page as Computer Use backend — no Docker/Xvfb needed"
  - "Agent loop pattern: screenshot -> Claude decides -> execute action -> screenshot -> repeat"
  - "Skip-on-missing-key: conftest hook skips ai_agents tests cleanly when API key is absent"

requirements-completed: [AIQA-01, AIQA-02, AIQA-10, AIQA-11, AIQA-12]

# Metrics
duration: 3min
completed: 2026-03-29
---

# Phase 6 Plan 1: AI QA Agent Framework Summary

**Claude Computer Use agent loop with PlaywrightComputerBackend, 1M-token cost cap, and skip-when-no-key pytest fixtures**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-29T06:07:58Z
- **Completed:** 2026-03-29T06:11:00Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- PlaywrightComputerBackend handles all Computer Use action types (click, type, scroll, key, mouse_move, etc.) with error-state screenshot fallback
- run_agent_scenario implements full agent loop with MAX_ITERATIONS=20 cap and MAX_INPUT_TOKENS=1M hard cost cap per AIQA-10
- conftest.py provides claude_client, agent_backend, base_url, api_url, agent_system_prompt fixtures with clean skip when ANTHROPIC_API_KEY is empty

## Task Commits

Each task was committed atomically:

1. **Task 1: Add anthropic SDK, extend Settings, update .env.example** - `64d1d98` (feat)
2. **Task 2: Create PlaywrightComputerBackend and agent_runner modules** - `6940f03` (feat)
3. **Task 3: Create conftest.py with fixtures and skip logic** - `866af21` (feat)

## Files Created/Modified
- `requirements.txt` - Added anthropic==0.86.0 dependency
- `settings.py` - Added ANTHROPIC_API_KEY field with empty default
- `.env.example` - Added ANTHROPIC_API_KEY placeholder
- `tests/ai_agents/__init__.py` - Package marker (empty)
- `tests/ai_agents/computer_use_backend.py` - PlaywrightComputerBackend class with all action types
- `tests/ai_agents/agent_runner.py` - Core agent loop with cost cap and token tracking
- `tests/ai_agents/conftest.py` - Fixtures: claude_client, agent_backend, skip-when-no-key

## Decisions Made
- anthropic 0.86.0 pinned with computer_20251124 tool type and computer-use-2025-11-24 beta header for Claude Sonnet 4.6
- MAX_INPUT_TOKENS = 1,000,000 hard cost cap per scenario prevents runaway API costs (AIQA-10)
- Empty ANTHROPIC_API_KEY default with pytest_collection_modifyitems skip logic ensures clean CI without the key — no crash, just skip messages
- Viewport matched to tool definition (1280x800) to avoid coordinate mismatch

## Deviations from Plan

None - plan executed exactly as written. Tasks 1 and 2 were already committed from a prior execution attempt; Task 3 was the remaining untracked file.

## Issues Encountered
- pip installed to Python 3.13 by default while `python` resolves to 3.11 — used `python -m pip install` to target the correct interpreter

## User Setup Required

None - ANTHROPIC_API_KEY is optional. Agent tests skip cleanly when the key is not configured. Users add their key to `.env` when ready to run AI agent tests.

## Next Phase Readiness
- Framework is ready for Plan 02 (scenario tests) and Plan 03 (reporting integration)
- All exports available: PlaywrightComputerBackend, run_agent_scenario, MAX_ITERATIONS, MAX_INPUT_TOKENS, COMPUTER_USE_TOOL, MODEL
- Fixtures available: claude_client, agent_backend, base_url, api_url, agent_system_prompt

---
*Phase: 06-ai-qa-agents*
*Completed: 2026-03-29*
