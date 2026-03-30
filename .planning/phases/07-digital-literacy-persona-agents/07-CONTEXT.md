# Phase 7: Digital Literacy Persona Agents - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

AI agents that simulate users of varying digital literacy levels across GatherGood's core user flows. Each persona navigates the site like a real person of that skill level, reporting friction scores, confusion points, and UX improvement suggestions. The system produces an aggregate comparison report and is deployable on Railway (agent runner) and Vercel (report dashboard).

This phase builds ON TOP of Phase 6's Computer Use agent framework — it reuses the agent loop, Playwright backend, and reporting integration, adding persona prompt engineering, structured usability output, and deployment infrastructure.

</domain>

<decisions>
## Implementation Decisions

### Persona Design
- **D-01:** Personas defined as Python dataclasses/dicts with fields: `name`, `literacy_level` (1-5 scale), `system_prompt` (behavioral description), `constraints` (list of behavioral rules like "never uses keyboard shortcuts")
- **D-02:** 5 personas required:
  1. **Tech-savvy** (literacy 5) — 25yo developer, scans for patterns, tries shortcuts, expects instant feedback
  2. **Casual user** (literacy 3) — 45yo office worker, reads labels carefully, hesitates at jargon, expects confirmation dialogs
  3. **Low digital literacy** (literacy 1) — 70yo retiree, confused by icons without text, misses small buttons, doesn't scroll instinctively
  4. **Non-native English speaker** (literacy 3) — struggles with idioms/jargon, relies on visual cues over text
  5. **Impatient/distracted** (literacy 4) — skips instructions, clicks fast, abandons if stuck >10 seconds
- **D-03:** Persona behavior is deterministic — same persona produces consistent friction patterns across runs for reproducibility

### Output & Scoring
- **D-04:** Per-persona-per-flow output is structured JSON: `friction_score` (1-10), `task_completed` (bool), `confusion_points` (list of {step, screenshot_path, description, severity}), `suggestions` (list of strings), `steps_taken` (int), `tokens_used` (int)
- **D-05:** Friction score calculated as weighted combination of:
  - Steps taken vs optimal path length (step ratio)
  - Wrong clicks / backtracking count
  - Explicit confusion observations from the agent
  - Task completion (failure = automatic score 10)
- **D-06:** Aggregate output is HTML matrix: personas (rows) x flows (columns), cells show friction score with heatmap coloring (green 1-3, yellow 4-6, red 7-10)

### Flow Coverage
- **D-07:** 3 core flows per persona:
  1. Registration & login
  2. Event browsing & discovery
  3. Ticket checkout (free tier)
- **D-08:** These cover the critical new-user journey — the delta between tech-savvy and low-literacy personas reveals UX gaps

### Deployment Architecture
- **D-09:** Railway: Python agent runner triggered via FastAPI endpoint (POST to start persona sweep, returns job ID) + manual CLI via `pytest tests/persona_agents/`
- **D-10:** Vercel: Static HTML report generated from JSON result artifacts — no live backend on Vercel side
- **D-11:** Results stored as JSON files in reports/ directory, HTML report generated from those JSONs
- **D-12:** Environment config follows existing pattern: pydantic-settings with .env for ANTHROPIC_API_KEY, BASE_URL, API_URL, RAILWAY_URL

### Claude's Discretion
- Agent prompt engineering details (exact wording of persona system prompts)
- FastAPI endpoint structure and authentication
- JSON schema exact field names
- HTML report styling and layout
- Optimal path calculation methodology

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Agent Framework
- `tests/ai_agents/agent_runner.py` — Core agent loop (screenshot → Claude → action → repeat), reuse pattern for persona agents
- `tests/ai_agents/computer_use_backend.py` — PlaywrightComputerBackend adapter, reuse as-is
- `tests/ai_agents/conftest.py` — Agent fixtures (claude_client, agent_backend, system prompt, reporting hooks)

### Test Infrastructure
- `settings.py` — pydantic-settings config pattern (BASE_URL, API_URL, ANTHROPIC_API_KEY)
- `conftest.py` (root) — Health checks, auth_client, teardown, requirement markers

### Specifications
- `.planning/TEST_SPEC.md` — Source of truth for all feature requirements being tested
- `.planning/ROADMAP.md` — Phase 6 details for agent framework decisions to carry forward

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `agent_runner.py:run_agent_scenario()` — Core loop can be extended with persona-aware system prompts and structured output parsing
- `PlaywrightComputerBackend` — Browser adapter works as-is for persona agents
- `conftest.py` agent fixtures — `claude_client`, `agent_backend`, `agent_config` can be reused or extended
- Phase 6 test scenarios — Setup helpers (`_create_published_event()`, `_create_event_with_free_tier()`) can be reused for persona flow setup

### Established Patterns
- System prompt engineering for agent behavior (AGENT_SYSTEM_PROMPT in conftest.py)
- httpx API setup before agent browser verification
- Verdict parsing from Claude's text response
- pytest-html report integration with custom hook
- Token tracking and cost cap (1M input tokens per scenario)

### Integration Points
- `pytest tests/persona_agents/` — New test directory alongside `tests/ai_agents/`
- `reports/` — JSON artifacts and HTML persona report
- `.env` — Same environment variables, possibly adding RAILWAY_URL for deployment trigger
- `requirements.txt` — FastAPI/uvicorn for Railway deployment endpoint

</code_context>

<specifics>
## Specific Ideas

- The key insight is the **delta** between personas — if a tech-savvy user completes checkout in 4 steps but a low-literacy user takes 15 (or fails), that reveals exactly where UX improvements are needed
- Confusion point screenshots should capture the exact moment the agent hesitates or tries a wrong action — these are the actionable UX artifacts
- The heatmap matrix is the executive summary — a team lead should be able to glance at it and know which flows need redesigning for accessibility
- Deployment on Railway means the persona sweep can run on a schedule (e.g., after each deploy) without human intervention

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-digital-literacy-persona-agents*
*Context gathered: 2026-03-30*
