# Phase 7: Digital Literacy Persona Agents - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-30
**Phase:** 07-digital-literacy-persona-agents
**Areas discussed:** Persona Design, Output & Scoring, Deployment Architecture, Flow Coverage & Comparison
**Mode:** --auto (all decisions auto-selected as recommended defaults)

---

## Persona Design

| Option | Description | Selected |
|--------|-------------|----------|
| Prompt templates in Python config | Personas as Python dataclasses with system_prompt and constraints | ✓ |
| YAML/JSON config files | External config files loaded at runtime | |
| Database-driven personas | Stored in DB for dynamic management | |

**User's choice:** Prompt templates in Python config (auto-selected)
**Notes:** 5 personas covering tech-savvy, casual, low-literacy, non-native English, and impatient archetypes

| Option | Description | Selected |
|--------|-------------|----------|
| Deterministic with persona seed | Same persona behaves consistently across runs | ✓ |
| Randomized within bounds | Persona behavior varies within defined ranges | |

**User's choice:** Deterministic with persona seed (auto-selected)
**Notes:** Reproducibility is essential for tracking UX improvements over time

---

## Output & Scoring

| Option | Description | Selected |
|--------|-------------|----------|
| Structured JSON per-run + aggregate HTML | JSON artifacts per run, HTML dashboard for comparison | ✓ |
| Markdown reports only | Simpler but harder to aggregate | |
| Database with live dashboard | More infrastructure, overkill for v1 | |

**User's choice:** Structured JSON per-run + aggregate HTML (auto-selected)

| Option | Description | Selected |
|--------|-------------|----------|
| Step count ratio + explicit confusion markers | Weighted combination of objective and subjective measures | ✓ |
| Binary pass/fail only | Too simple, misses gradations | |
| Time-based scoring | Not directly measurable with agent iterations | |

**User's choice:** Step count ratio + explicit confusion markers (auto-selected)

---

## Deployment Architecture

| Option | Description | Selected |
|--------|-------------|----------|
| Railway runs agents, Vercel serves static report | Clean separation, minimal Vercel infrastructure | ✓ |
| Everything on Railway | Simpler but Vercel already used for frontend | |
| Serverless functions on Vercel | Not suited for long-running agent tasks | |

**User's choice:** Railway runs agents, Vercel serves static report (auto-selected)

| Option | Description | Selected |
|--------|-------------|----------|
| API endpoint + manual CLI | FastAPI on Railway + pytest locally | ✓ |
| CLI only | No remote trigger capability | |
| GitHub Actions trigger | Adds CI dependency | |

**User's choice:** API endpoint + manual CLI (auto-selected)

---

## Flow Coverage & Comparison

| Option | Description | Selected |
|--------|-------------|----------|
| 3 core flows covering main user journey | Registration, browsing, checkout | ✓ |
| All 5 Phase 6 scenario flows | More coverage but higher cost | |
| Single flow (checkout only) | Too narrow | |

**User's choice:** 3 core flows covering main user journey (auto-selected)

| Option | Description | Selected |
|--------|-------------|----------|
| Score matrix with heatmap coloring | Personas x flows grid with color-coded friction scores | ✓ |
| Bar charts per persona | Harder to compare across dimensions | |
| Text-only comparison table | Less visual impact | |

**User's choice:** Score matrix with heatmap coloring (auto-selected)

---

## Claude's Discretion

- Agent prompt engineering details (exact persona system prompts)
- FastAPI endpoint structure
- JSON schema field names
- HTML report styling
- Optimal path calculation methodology

## Deferred Ideas

None — discussion stayed within phase scope
