---
phase: 07-digital-literacy-persona-agents
plan: 01
subsystem: testing
tags: [persona, ux, friction-score, ai-agent, computer-use, playwright, anthropic]

# Dependency graph
requires:
  - phase: 06-ai-qa-agents
    provides: run_agent_scenario() loop and PlaywrightComputerBackend reused by persona runner

provides:
  - 5 Persona dataclasses (TECH_SAVVY, CASUAL, LOW_LITERACY, NON_NATIVE, IMPATIENT)
  - calculate_friction_score() with step-ratio and confusion-severity components
  - run_persona_scenario() wrapping run_agent_scenario() with persona system prompts
  - _parse_structured_output() extracting JSON blocks from Claude response text
  - save_persona_result() writing per-persona-per-flow JSON artifacts

affects:
  - 07-02-persona-test-suite
  - 07-03-report-generator
  - 07-04-deployment

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Persona dataclass with system_prompt in first-person present tense per RESEARCH Pitfall 1
    - PERSONA_OUTPUT_INSTRUCTIONS appended to system prompt per RESEARCH Pitfall 2
    - Friction score formula: 1.0 + step_score (0-4) + confusion_score (0-4), capped 1-10
    - JSON extraction via regex on ```json ... ``` delimiters with re.DOTALL

key-files:
  created:
    - tests/persona_agents/__init__.py
    - tests/persona_agents/personas.py
    - tests/persona_agents/friction_scorer.py
    - tests/persona_agents/persona_runner.py
    - tests/persona_agents/artifact_writer.py
  modified: []

key-decisions:
  - "Persona system prompts end with _VERDICT_INSTRUCTION constant to guarantee PASS/FAIL and JSON block output"
  - "Friction score formula: baseline 1 + step penalty (0-4 pts) + confusion penalty (0-4 pts), capped to 1-10 range"
  - "steps_taken falls back to raw_result steps count when parsed JSON does not include steps_taken"
  - "artifact_writer uses os.path.abspath() to return absolute path for reliable downstream referencing"

patterns-established:
  - "Pattern 1: Persona first-person system prompt + behavioral constraints + output instructions concatenated in run_persona_scenario()"
  - "Pattern 2: _parse_structured_output() extracts JSON from triple-backtick blocks, returns {} on any failure (never raises)"
  - "Pattern 3: friction scorer is a pure function with no side effects — safe to call in tests, report generator, and FastAPI"

requirements-completed: [P7-SC1, P7-SC2, P7-SC5]

# Metrics
duration: 8min
completed: 2026-03-30
---

# Phase 7 Plan 01: Persona Agent Library Summary

**5 digital-literacy persona dataclasses + friction scorer + persona-aware run_agent_scenario() wrapper + JSON artifact writer, forming the foundation layer all subsequent persona plans import from.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-30T16:38:09Z
- **Completed:** 2026-03-30T16:46:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Defined 5 persona dataclasses (TECH_SAVVY, CASUAL, LOW_LITERACY, NON_NATIVE, IMPATIENT) with name, literacy_level 1-5, first-person system_prompt, and behavioral constraints list
- Implemented calculate_friction_score() with step-ratio penalty (0-4 pts) and confusion-severity penalty (0-4 pts, weighted low=0.5/medium=1.0/high=2.0), capped to 1-10; returns 10 immediately on task failure
- Built run_persona_scenario() composing persona.system_prompt + constraints + PERSONA_OUTPUT_INSTRUCTIONS, calling run_agent_scenario(), parsing JSON output block, and returning unified result dict with friction_score
- Built save_persona_result() writing per-persona-per-flow JSON under reports/persona/<run_id>/

## Task Commits

Each task was committed atomically:

1. **Task 1: Create persona definitions and friction scorer** - `9660e83` (feat)
2. **Task 2: Create persona runner wrapper and artifact writer** - `d5c0a47` (feat)

## Files Created/Modified

- `tests/persona_agents/__init__.py` - Empty package marker
- `tests/persona_agents/personas.py` - Persona dataclass + 5 instances + ALL_PERSONAS + OPTIMAL_STEPS
- `tests/persona_agents/friction_scorer.py` - calculate_friction_score() pure function per D-05
- `tests/persona_agents/persona_runner.py` - run_persona_scenario() + _parse_structured_output() + PERSONA_OUTPUT_INSTRUCTIONS
- `tests/persona_agents/artifact_writer.py` - save_persona_result() writing JSON artifacts

## Decisions Made

- Persona system prompts all end with `_VERDICT_INSTRUCTION` constant to guarantee Claude emits PASS/FAIL verdict and JSON block per RESEARCH Pitfall 2
- Friction formula baseline of 1.0 ensures optimal completion always yields score 1 (not 0), matching the 1-10 spec
- `steps_taken` in the result dict falls back to `raw_result["steps"]` when the parsed JSON block does not include `steps_taken`, ensuring the field is always present even if Claude's JSON is incomplete
- `artifact_writer` uses `os.path.abspath()` on the returned path so callers outside the project root can still locate the file reliably

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All modules importable and verified: `from tests.persona_agents.personas import ALL_PERSONAS` (5 personas), `calculate_friction_score(6,6,[],True)` returns 1, `run_persona_scenario` importable, `save_persona_result` importable
- Ready for 07-02 (persona test suite) and 07-03 (report generator) to import from this library
- No blockers

---
*Phase: 07-digital-literacy-persona-agents*
*Completed: 2026-03-30*

## Self-Check: PASSED

- FOUND: tests/persona_agents/__init__.py
- FOUND: tests/persona_agents/personas.py
- FOUND: tests/persona_agents/friction_scorer.py
- FOUND: tests/persona_agents/persona_runner.py
- FOUND: tests/persona_agents/artifact_writer.py
- FOUND: .planning/phases/07-digital-literacy-persona-agents/07-01-SUMMARY.md
- FOUND commit: 9660e83 (Task 1)
- FOUND commit: d5c0a47 (Task 2)
