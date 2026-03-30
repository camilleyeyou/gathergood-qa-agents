# Phase 7: Digital Literacy Persona Agents - Research

**Researched:** 2026-03-30
**Domain:** Persona-driven AI agent UX evaluation + FastAPI deployment + static HTML report generation
**Confidence:** HIGH (primary sources: existing codebase, verified package versions, official docs)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01:** Personas defined as Python dataclasses/dicts with fields: `name`, `literacy_level` (1-5 scale), `system_prompt` (behavioral description), `constraints` (list of behavioral rules like "never uses keyboard shortcuts")

**D-02:** 5 personas required:
1. Tech-savvy (literacy 5) — 25yo developer, scans for patterns, tries shortcuts, expects instant feedback
2. Casual user (literacy 3) — 45yo office worker, reads labels carefully, hesitates at jargon, expects confirmation dialogs
3. Low digital literacy (literacy 1) — 70yo retiree, confused by icons without text, misses small buttons, doesn't scroll instinctively
4. Non-native English speaker (literacy 3) — struggles with idioms/jargon, relies on visual cues over text
5. Impatient/distracted (literacy 4) — skips instructions, clicks fast, abandons if stuck >10 seconds

**D-03:** Persona behavior is deterministic — same persona produces consistent friction patterns across runs for reproducibility

**D-04:** Per-persona-per-flow output is structured JSON: `friction_score` (1-10), `task_completed` (bool), `confusion_points` (list of {step, screenshot_path, description, severity}), `suggestions` (list of strings), `steps_taken` (int), `tokens_used` (int)

**D-05:** Friction score calculated as weighted combination of:
- Steps taken vs optimal path length (step ratio)
- Wrong clicks / backtracking count
- Explicit confusion observations from the agent
- Task completion (failure = automatic score 10)

**D-06:** Aggregate output is HTML matrix: personas (rows) x flows (columns), cells show friction score with heatmap coloring (green 1-3, yellow 4-6, red 7-10)

**D-07:** 3 core flows per persona:
1. Registration & login
2. Event browsing & discovery
3. Ticket checkout (free tier)

**D-08:** These cover the critical new-user journey — the delta between tech-savvy and low-literacy personas reveals UX gaps

**D-09:** Railway: Python agent runner triggered via FastAPI endpoint (POST to start persona sweep, returns job ID) + manual CLI via `pytest tests/persona_agents/`

**D-10:** Vercel: Static HTML report generated from JSON result artifacts — no live backend on Vercel side

**D-11:** Results stored as JSON files in reports/ directory, HTML report generated from those JSONs

**D-12:** Environment config follows existing pattern: pydantic-settings with .env for ANTHROPIC_API_KEY, BASE_URL, API_URL, RAILWAY_URL

### Claude's Discretion

- Agent prompt engineering details (exact wording of persona system prompts)
- FastAPI endpoint structure and authentication
- JSON schema exact field names
- HTML report styling and layout
- Optimal path calculation methodology

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| P7-SC1 | Each persona agent completes core flows and produces structured usability report with friction score, confusion points, and improvement suggestions | run_agent_scenario() extension with structured JSON output parsing from Claude's response |
| P7-SC2 | At least 5 distinct digital literacy personas configurable via prompt templates | Python dataclasses/dicts pattern (D-01, D-02); deterministic system prompts |
| P7-SC3 | Aggregate report compares persona results side-by-side as heatmap matrix | Jinja2 3.1.6 (already installed) for HTML generation; JSON → HTML pipeline |
| P7-SC4 | System deployable on Railway (agent runner) and Vercel (report dashboard) with environment config | FastAPI 0.122.0 + uvicorn 0.38.0 already installed; Railway nixpacks auto-detection; Vercel static file hosting |
| P7-SC5 | Full persona sweep produces actionable UX insights, not just pass/fail | Structured confusion_points with screenshot_path and severity; suggestions list in output schema |
</phase_requirements>

---

## Summary

This phase extends the Phase 6 Computer Use agent framework with persona-aware system prompts and structured usability output. The core loop (`run_agent_scenario()`) is reused without modification — the key additions are: (1) persona definitions as Python dataclasses, (2) a modified agent call that instructs Claude to role-play as a specific persona AND produce structured JSON output at completion, (3) a friction score calculator that post-processes the raw agent result, and (4) an HTML report generator that renders the 5x3 persona/flow matrix.

The deployment architecture separates concerns cleanly: Railway runs the Python agent workload (long-running, CPU-bound), Vercel serves the pre-generated static HTML report. FastAPI provides the Railway-side trigger endpoint; Jinja2 generates the static HTML from the JSON artifacts. Both packages are already installed in the project environment.

The most critical design challenge is getting Claude to simultaneously act as a persona AND report observations in a machine-parseable format. The approach that works reliably: the system prompt encodes the persona behavior; the goal message instructs Claude to output a JSON block delimited by ```json ... ``` at completion alongside its PASS/FAIL/INCONCLUSIVE verdict. The runner parses this block after the loop terminates.

**Primary recommendation:** Build `tests/persona_agents/` as a thin wrapper around the existing agent framework — add persona dataclasses, a `run_persona_scenario()` function that calls `run_agent_scenario()` and post-processes the result, and a `generate_report.py` script. FastAPI endpoint in `api/persona_runner.py` handles the Railway trigger. Jinja2 template in `templates/persona_report.html.j2` generates the matrix.

---

## Project Constraints (from CLAUDE.md)

| Directive | Requirement |
|-----------|-------------|
| Target URLs | Tests run against live deployed endpoints — frontend: `https://event-management-two-red.vercel.app/`, backend: `https://event-management-production-ad62.up.railway.app/api/v1` |
| Test isolation | Use unique data per run (uuid4 suffixes via faker). No shared mutable state. |
| No destructive actions | Must not delete production data other users depend on |
| Stack language | Python 3.11+, pytest, httpx, Playwright Python bindings |
| No os.environ for config | Use pydantic-settings BaseSettings |
| No time.sleep() | Playwright auto-wait; agent loop paces itself via API round-trips |
| GSD workflow enforcement | All file changes through a GSD command |

---

## Standard Stack

### Core (already installed — no new installs needed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| anthropic | 0.86.0 | Computer Use API — same as Phase 6 | Already in requirements.txt; persona agents use same `run_agent_scenario()` loop |
| playwright (Python) | 1.58.0 | Browser backend for persona agents | Already installed; PlaywrightComputerBackend reused as-is |
| fastapi | 0.122.0 | HTTP trigger endpoint on Railway | Already installed in project venv; confirmed via `pip show fastapi` 2026-03-30 |
| uvicorn | 0.38.0 | ASGI server for FastAPI on Railway | Already installed; confirmed via `pip show uvicorn` 2026-03-30 |
| jinja2 | 3.1.6 | HTML report template rendering | Already installed as transitive dependency; confirmed via `pip show jinja2` 2026-03-30 |
| pydantic-settings | 2.13.1 | Environment config (D-12 pattern) | Already in requirements.txt |
| httpx | 0.28.1 | API setup before persona browser flows | Already in requirements.txt |
| faker | 33.x | Unique test data per persona run | Already in requirements.txt |
| pytest | 9.0.2 | CLI runner: `pytest tests/persona_agents/` | Already in requirements.txt |

### New additions to requirements.txt

No new packages are required. All dependencies are already present.

**Version verification (confirmed 2026-03-30 via pip show):**
- fastapi 0.122.0 — installed
- uvicorn 0.38.0 — installed
- jinja2 3.1.6 — installed
- anthropic 0.86.0 — installed

### Alternatives Considered

| Recommended | Alternative | Tradeoff |
|-------------|-------------|----------|
| Jinja2 for HTML | Python f-string HTML | Jinja2 is already installed; templates are maintainable; f-strings become unreadable for a 200-line HTML matrix |
| FastAPI | Flask | FastAPI is already installed; automatic OpenAPI docs; async-ready; no reason to introduce Flask |
| pytest as CLI runner | standalone Python script | pytest keeps the persona sweep in the existing test infrastructure; markers, reports, and fixtures all work |

---

## Architecture Patterns

### Recommended Project Structure

```
tests/
├── persona_agents/              # New: Digital literacy persona agents
│   ├── __init__.py
│   ├── personas.py              # Persona dataclass definitions (D-01, D-02)
│   ├── persona_runner.py        # run_persona_scenario() wrapping run_agent_scenario()
│   ├── friction_scorer.py       # Friction score calculation (D-05)
│   ├── conftest.py              # Persona-specific fixtures
│   └── test_persona_sweep.py   # pytest entry point for full 5x3 sweep
api/
├── __init__.py
└── persona_runner.py            # FastAPI app for Railway trigger endpoint (D-09)
templates/
└── persona_report.html.j2       # Jinja2 template for heatmap matrix (D-06)
scripts/
└── generate_persona_report.py   # CLI: reads reports/persona/*.json → renders HTML
reports/
└── persona/                     # Per-run JSON artifacts (D-11)
    ├── run_<timestamp>/
    │   ├── tech_savvy_registration.json
    │   ├── tech_savvy_browsing.json
    │   ├── low_literacy_checkout.json
    │   └── ...
    └── persona_matrix.html      # Generated aggregate report
```

### Pattern 1: Persona Dataclass Definition

**What:** Each persona is a Python dataclass with `name`, `literacy_level`, `system_prompt`, and `constraints`. The system_prompt is the behavioral description passed to Claude as the `system` parameter.

**When to use:** Import from `personas.py` in all persona agent code. Never hard-code persona text in test files.

```python
# tests/persona_agents/personas.py
from dataclasses import dataclass, field

@dataclass
class Persona:
    name: str
    literacy_level: int  # 1-5 scale (D-01)
    system_prompt: str   # Behavioral description for Claude
    constraints: list[str] = field(default_factory=list)  # Behavioral rules

# D-02: The 5 required personas
TECH_SAVVY = Persona(
    name="tech_savvy",
    literacy_level=5,
    system_prompt=(
        "You are a 25-year-old software developer testing a website. "
        "You scan pages quickly for patterns, look for keyboard shortcuts, "
        "expect instant feedback, and become impatient with unnecessary confirmation dialogs. "
        "You click confidently and navigate efficiently."
    ),
    constraints=[
        "Use keyboard shortcuts when available (Tab, Enter, Ctrl+Click)",
        "Scan, don't read every word",
        "Click the most obvious primary action immediately",
    ],
)

LOW_LITERACY = Persona(
    name="low_literacy",
    literacy_level=1,
    system_prompt=(
        "You are a 70-year-old retiree who rarely uses websites. "
        "You are confused by icons that don't have text labels. "
        "You miss small buttons and don't scroll instinctively. "
        "You read every word carefully and hesitate before clicking anything. "
        "If you don't understand something, you report confusion rather than guessing."
    ),
    constraints=[
        "Never use keyboard shortcuts",
        "Only click elements with visible text labels",
        "Do not scroll unless you see a visual indicator",
        "Report confusion if any label is ambiguous or icon-only",
    ],
)

ALL_PERSONAS = [TECH_SAVVY, CASUAL, LOW_LITERACY, NON_NATIVE, IMPATIENT]
```

### Pattern 2: Persona Scenario Runner

**What:** `run_persona_scenario()` wraps `run_agent_scenario()` with persona-aware system prompt injection and structured JSON output parsing.

**When to use:** Call instead of `run_agent_scenario()` for all persona agent flows. The persona's system_prompt replaces the generic AGENT_SYSTEM_PROMPT.

```python
# tests/persona_agents/persona_runner.py
import json
import re
from dataclasses import dataclass, field
from typing import Any

from tests.ai_agents.agent_runner import run_agent_scenario
from tests.ai_agents.computer_use_backend import PlaywrightComputerBackend
from tests.persona_agents.personas import Persona
import anthropic

PERSONA_OUTPUT_INSTRUCTIONS = """
At the end of your session, you MUST output a JSON block in this exact format:

```json
{
  "task_completed": true or false,
  "steps_taken": <integer>,
  "confusion_points": [
    {"step": <int>, "description": "<what confused you>", "severity": "low|medium|high"}
  ],
  "suggestions": ["<UX improvement suggestion>", ...]
}
```

Before the JSON, output your verdict on its own line: PASS (task completed), FAIL (could not complete), or INCONCLUSIVE.
"""


def run_persona_scenario(
    backend: PlaywrightComputerBackend,
    client: anthropic.Anthropic,
    persona: Persona,
    flow_goal: str,
    optimal_steps: int,
    max_iterations: int = 25,
) -> dict[str, Any]:
    """Run a single flow for one persona, returning structured usability data.

    Calls run_agent_scenario() with the persona's system_prompt and parses
    the structured JSON output from Claude's final response.
    """
    system_prompt = (
        persona.system_prompt
        + "\n\nBehavioral constraints:\n"
        + "\n".join(f"- {c}" for c in persona.constraints)
        + "\n\n"
        + PERSONA_OUTPUT_INSTRUCTIONS
    )

    raw_result = run_agent_scenario(
        backend=backend,
        client=client,
        goal=flow_goal,
        system_prompt=system_prompt,
        max_iterations=max_iterations,
    )

    # Parse structured JSON from Claude's final text
    structured = _parse_structured_output(raw_result["reasoning"])

    # Calculate friction score (D-05)
    friction_score = calculate_friction_score(
        steps_taken=structured.get("steps_taken", raw_result["steps"]),
        optimal_steps=optimal_steps,
        confusion_points=structured.get("confusion_points", []),
        task_completed=structured.get("task_completed", raw_result["verdict"] == "PASS"),
    )

    return {
        "persona": persona.name,
        "literacy_level": persona.literacy_level,
        "verdict": raw_result["verdict"],
        "task_completed": structured.get("task_completed", raw_result["verdict"] == "PASS"),
        "friction_score": friction_score,
        "steps_taken": structured.get("steps_taken", raw_result["steps"]),
        "optimal_steps": optimal_steps,
        "confusion_points": structured.get("confusion_points", []),
        "suggestions": structured.get("suggestions", []),
        "tokens_used": raw_result["input_tokens"],
        "reasoning": raw_result["reasoning"],
    }


def _parse_structured_output(text: str) -> dict:
    """Extract JSON block from Claude's final response text."""
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return {}
```

### Pattern 3: Friction Score Calculation (D-05)

**What:** Weighted combination of objective metrics (step ratio) and Claude's subjective observations (confusion_points, task failure).

**When to use:** Called by `run_persona_scenario()` after every agent run.

```python
# tests/persona_agents/friction_scorer.py

def calculate_friction_score(
    steps_taken: int,
    optimal_steps: int,
    confusion_points: list[dict],
    task_completed: bool,
) -> int:
    """Calculate friction score 1-10 (D-05).

    Weights:
    - Task failure: automatic score 10
    - Step ratio: 0-4 points (steps_taken / optimal_steps, capped at 4x)
    - Confusion severity: 0-4 points (sum of severity weights)
    - Wrong clicks/backtracking embedded in confusion_points count

    Returns int in [1, 10].
    """
    if not task_completed:
        return 10

    # Step ratio component (0.0 to 1.0, then scaled to 0-4)
    ratio = min(steps_taken / max(optimal_steps, 1), 4.0)
    step_score = (ratio - 1.0) / 3.0 * 4.0  # 1x = 0 pts, 4x = 4 pts
    step_score = max(0.0, step_score)

    # Confusion component (0-4 points)
    severity_weights = {"low": 0.5, "medium": 1.0, "high": 2.0}
    confusion_score = sum(
        severity_weights.get(cp.get("severity", "low"), 0.5)
        for cp in confusion_points
    )
    confusion_score = min(confusion_score, 4.0)

    raw = 1.0 + step_score + confusion_score
    return min(10, max(1, round(raw)))
```

### Pattern 4: JSON Artifact Storage (D-11)

**What:** Save each persona/flow result as a JSON file in `reports/persona/<run_timestamp>/`. The aggregate report script reads these to generate the HTML matrix.

**When to use:** After every `run_persona_scenario()` call in the test and in the FastAPI endpoint.

```python
import json
import os
from datetime import datetime, timezone

def save_persona_result(result: dict, run_id: str) -> str:
    """Save persona result JSON to reports/persona/<run_id>/.

    Returns the path to the saved file.
    """
    run_dir = os.path.join("reports", "persona", run_id)
    os.makedirs(run_dir, exist_ok=True)
    filename = f"{result['persona']}_{result['flow']}.json"
    path = os.path.join(run_dir, filename)
    with open(path, "w") as f:
        json.dump(result, f, indent=2)
    return path
```

### Pattern 5: HTML Report Generation with Jinja2 (D-06)

**What:** Read all JSON artifacts for a run, build a 5x3 matrix, render via Jinja2 template with heatmap CSS classes.

**When to use:** Run after all persona scenarios complete, either via CLI (`python scripts/generate_persona_report.py`) or triggered by the FastAPI endpoint.

```python
# scripts/generate_persona_report.py
import json
import os
from jinja2 import Environment, FileSystemLoader

def generate_report(run_id: str) -> str:
    """Read persona JSON artifacts and render the HTML matrix report."""
    run_dir = os.path.join("reports", "persona", run_id)
    results = {}
    for fname in os.listdir(run_dir):
        if fname.endswith(".json"):
            with open(os.path.join(run_dir, fname)) as f:
                r = json.load(f)
                results[(r["persona"], r["flow"])] = r

    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("persona_report.html.j2")

    html = template.render(
        run_id=run_id,
        personas=["tech_savvy", "casual", "low_literacy", "non_native", "impatient"],
        flows=["registration", "browsing", "checkout"],
        results=results,
    )
    output_path = os.path.join("reports", "persona", run_id, "persona_matrix.html")
    with open(output_path, "w") as f:
        f.write(html)
    return output_path
```

### Pattern 6: FastAPI Trigger Endpoint (D-09)

**What:** POST `/sweep` on the Railway-hosted FastAPI app launches a background persona sweep and returns a job ID. GET `/sweep/{job_id}` returns status and result path.

**When to use:** For remote triggering from Railway without SSH access.

```python
# api/persona_runner.py
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import uuid

app = FastAPI(title="Persona Agent Runner")

sweeps: dict[str, dict] = {}  # In-memory job store (sufficient for v1)


class SweepRequest(BaseModel):
    personas: list[str] | None = None  # None = all 5
    flows: list[str] | None = None     # None = all 3


@app.post("/sweep")
async def start_sweep(request: SweepRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    sweeps[job_id] = {"status": "running", "result_path": None}
    background_tasks.add_task(_run_sweep, job_id, request.personas, request.flows)
    return {"job_id": job_id, "status": "running"}


@app.get("/sweep/{job_id}")
async def get_sweep_status(job_id: str):
    if job_id not in sweeps:
        return {"error": "Job not found"}, 404
    return sweeps[job_id]


@app.get("/health")
async def health():
    return {"status": "ok"}
```

### Pattern 7: Optimal Step Counts per Flow

**What:** Hardcoded optimal step counts based on the known GatherGood UI flows. Used by the friction scorer.

**When to use:** Pass as `optimal_steps` argument to `run_persona_scenario()`.

```python
OPTIMAL_STEPS = {
    "registration": 6,   # Fill email, password, confirm, first name, last name, submit
    "browsing": 3,        # Navigate to events, apply filter or search, view event detail
    "checkout": 5,        # Select ticket, enter billing info, confirm, view confirmation
}
```

These are estimates. The tech-savvy persona establishes the empirical baseline on first run, which can be used to calibrate.

### Anti-Patterns to Avoid

- **Modifying run_agent_scenario():** The existing agent loop is production-tested. Wrap it via `run_persona_scenario()`, do not edit the original.
- **Storing screenshots in JSON:** confusion_points should store `screenshot_path` (relative path to a saved PNG), not base64 data. Base64 screenshots in JSON files create multi-MB artifacts.
- **Single test function running all 15 combinations:** Each persona/flow combination should be a separate pytest test so failures are isolated and partial runs are possible.
- **In-memory job store for Railway production:** The dict-based job store in Pattern 6 is only safe for single-process Railway deployments. Do not use if multiple workers are started.
- **Blocking FastAPI endpoint:** Use `BackgroundTasks` — persona sweeps take 5-30 minutes and will time out HTTP connections if run synchronously.
- **Hardcoding persona prompts in test files:** All persona definitions live in `personas.py`. Tests import from there.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Browser automation | Custom browser driver | `PlaywrightComputerBackend` (Phase 6, unchanged) | Already handles all 10 action types; viewport sizing; error recovery |
| Computer Use agent loop | Custom API call loop | `run_agent_scenario()` from `agent_runner.py` | Has rate-limit retry, cost cap, token tracking, verdict parsing |
| HTML templating | f-string HTML generation | Jinja2 3.1.6 (already installed) | Template separation; easier to maintain 200-line report matrix |
| HTTP API server | Raw socket server | FastAPI 0.122.0 (already installed) | Background task support, OpenAPI docs, pydantic validation |
| Structured output parsing | Custom JSON extraction | Regex + json.loads (Pattern 2 above) | Simple; Claude reliably produces ```json blocks when instructed |
| Friction scoring | ML-based quality model | Weighted formula (Pattern 3 above) | Interpretable; tunable without retraining; sufficient for UX diff signal |

**Key insight:** 90% of Phase 7 is configuration and orchestration of already-built components. The new code is: persona definitions (~50 lines), the persona runner wrapper (~60 lines), the friction scorer (~30 lines), the Jinja2 template (~100 lines), and the FastAPI endpoint (~50 lines). None of these require new packages.

---

## Common Pitfalls

### Pitfall 1: Claude Ignores Persona Behavioral Constraints

**What goes wrong:** Claude acknowledges the persona system prompt but then navigates the site efficiently like itself, not like the persona. The tech-savvy and low-literacy agents produce nearly identical paths.

**Why it happens:** Claude's default behavior is helpful and efficient. Persona constraints that conflict with helpfulness (e.g., "be confused by icons") require explicit, repeated reinforcement in the system prompt.

**How to avoid:** The system prompt must use first-person present tense ("I am a 70-year-old...") and constraints must be framed as self-descriptions, not instructions ("I never use keyboard shortcuts" not "Do not use keyboard shortcuts"). Add: "Stay in character throughout. If I would be confused, I should stop and note the confusion rather than proceeding."

**Warning signs:** All personas complete tasks in the same step count; confusion_points list is always empty.

### Pitfall 2: JSON Output Block Not Reliably Produced

**What goes wrong:** Claude ends its response with the verdict text but omits the ```json block, causing `_parse_structured_output()` to return an empty dict and the friction scorer to use fallback values.

**Why it happens:** Claude can run out of output tokens (max_tokens=4096) before producing the JSON block if the reasoning text is very long.

**How to avoid:** (1) Instruct Claude in the goal message (not just system prompt): "IMPORTANT: Your final message MUST include the ```json block before stopping." (2) Increase `max_tokens` to 8192 for persona scenarios. (3) Implement fallback: if JSON not found, construct a minimal result dict from the raw verdict and step count.

**Warning signs:** `_parse_structured_output()` returns `{}` more than 20% of the time; confusion_points always empty.

### Pitfall 3: Screenshot Paths in confusion_points Break After Run

**What goes wrong:** `confusion_points[i]["screenshot_path"]` references a file that doesn't exist or uses an absolute path that is wrong on Vercel.

**Why it happens:** Screenshots saved during agent execution use absolute paths or paths relative to the working directory at execution time, not relative to the report location.

**How to avoid:** Save confusion screenshots to `reports/persona/<run_id>/screenshots/` and store only the relative path from the run directory. The Jinja2 template constructs URLs relative to the HTML file location.

**Warning signs:** Broken image icons in the HTML report; `file not found` errors when opening report on a different machine.

### Pitfall 4: FastAPI Background Task Runs Agent in the Wrong Process State

**What goes wrong:** The Playwright browser launched in a FastAPI background task cannot connect to the display or crashes with "Executable doesn't exist."

**Why it happens:** Railway workers may not have Chromium on PATH if `playwright install chromium` was not run during the build step.

**How to avoid:** Add `RUN playwright install chromium` to the Railway `Dockerfile` or build command. Alternatively, run the persona sweep as a subprocess (`subprocess.Popen(["pytest", "tests/persona_agents/"])`) from the FastAPI background task, which ensures the pytest/playwright environment is activated.

**Warning signs:** FastAPI endpoint returns 200 but job stays in "running" status indefinitely; Railway logs show "Executable doesn't exist at .../chromium".

### Pitfall 5: 15-Scenario Sweep Costs Exceed Budget

**What goes wrong:** 5 personas x 3 flows = 15 scenarios. At medium complexity (~20,000 tokens each), total input tokens = 300,000 = $0.90. With complex flows (checkout), each scenario can hit 40,000+ tokens, pushing the sweep to $1.80+.

**Why it happens:** Each persona explores the UI more hesitantly than the Phase 6 agents (especially low_literacy and non_native), requiring more iterations and more screenshots per scenario.

**How to avoid:** Set `max_iterations=25` for complex personas (low_literacy, non_native) but `max_iterations=15` for tech_savvy and impatient (who complete faster). Add a per-sweep cost cap: abort remaining scenarios if total tokens > 500,000.

**Warning signs:** Single persona/flow run exceeds 30,000 input tokens; sweep cost > $2.00.

### Pitfall 6: Determinism (D-03) is Difficult to Guarantee

**What goes wrong:** The same persona produces different friction scores on repeat runs because Claude's sampling is non-deterministic.

**Why it happens:** Claude's temperature defaults to 1.0 for the beta.messages endpoint. There is no `temperature=0` option for Computer Use beta.

**How to avoid:** D-03 says "same persona produces consistent friction patterns" — interpret this as qualitative consistency (tech-savvy always scores lower than low-literacy), not bit-for-bit identical scores. Document in CONTEXT.md that determinism means "the relative ordering of friction scores is stable", not "exact scores are identical." Use the aggregate trend over multiple runs rather than a single run as the source of truth.

**Warning signs:** Tech-savvy persona scores 8/10 on one run and 2/10 on the next; this indicates a problem with the prompt or flow, not just natural variance.

---

## Code Examples

### Persona System Prompt Engineering (for low_literacy)

```python
# Effective persona prompt — first-person, behavioral, self-descriptions
LOW_LITERACY_PROMPT = """\
I am a 70-year-old retiree who rarely uses websites. Here is how I behave:

- I read every word on the page before I click anything
- I am confused when I see an icon without a text label next to it
- I do not scroll down unless I see a scroll bar or an arrow indicating there is more
- I never use keyboard shortcuts — I always use the mouse
- I do not know what 'login' means as a verb — I look for 'Sign In' or 'Enter'
- If I am unsure about a button, I describe my confusion rather than clicking it
- I am patient and careful, not impulsive

When I complete the task or give up, I output my verdict (PASS/FAIL/INCONCLUSIVE)
and the required JSON block describing my experience.
"""
```

### Complete Persona Test Function

```python
# tests/persona_agents/test_persona_sweep.py
import pytest
from tests.persona_agents.personas import LOW_LITERACY, OPTIMAL_STEPS
from tests.persona_agents.persona_runner import run_persona_scenario
from tests.persona_agents.artifact_writer import save_persona_result

@pytest.mark.persona_agent
def test_low_literacy_registration(agent_backend, claude_client, base_url, run_id):
    """Low-literacy persona attempts registration flow."""
    agent_backend.page.goto(f"{base_url}/register", timeout=60000)
    agent_backend.page.wait_for_load_state("networkidle")

    result = run_persona_scenario(
        backend=agent_backend,
        client=claude_client,
        persona=LOW_LITERACY,
        flow_goal=(
            "You are on a website. Try to create a new account so you can use the site. "
            "Act exactly as described in your character description. "
            "When done or if you give up, output your verdict and the JSON block."
        ),
        optimal_steps=OPTIMAL_STEPS["registration"],
        max_iterations=25,
    )
    result["flow"] = "registration"
    save_persona_result(result, run_id)

    # Persona tests do not assert PASS — they record the friction score
    # A "successful" low-literacy run might still have friction_score=7
    assert result["friction_score"] is not None, "Friction score must be calculated"
```

### Heatmap Coloring Logic (CSS classes)

```python
# Template helper
def friction_class(score: int) -> str:
    """Return CSS class for heatmap coloring (D-06)."""
    if score <= 3:
        return "friction-low"    # green
    elif score <= 6:
        return "friction-mid"    # yellow
    else:
        return "friction-high"   # red
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Generic QA agent with pass/fail | Persona-aware agent with friction scoring | Phase 7 (this phase) | Produces UX delta across literacy levels, not just binary correctness |
| Verdict-only agent output | Structured JSON with confusion_points | Phase 7 | Actionable specificity for UX team |
| pytest-html report | Custom Jinja2 matrix report | Phase 7 | 5x3 heatmap is the executive summary format |

---

## Open Questions

1. **Temperature control for Computer Use beta**
   - What we know: `client.beta.messages.create()` accepts `temperature` parameter. However, Computer Use quality may degrade at temperature=0 if Claude needs to reason about which action to take.
   - What's unclear: Whether setting temperature=0 for persona scenarios produces more deterministic behavior or breaks the agent loop.
   - Recommendation: Start with default temperature. If variance is unacceptable, test temperature=0.3 as a compromise. Document empirically.

2. **Vercel deployment of static HTML report**
   - What we know: Vercel serves static files from a directory. The persona_matrix.html file is generated locally and committed/uploaded.
   - What's unclear: How the HTML file gets from the Railway agent run to the Vercel deployment — does it require a git commit+push trigger, a Vercel deploy hook, or manual upload?
   - Recommendation: For v1, generate the report locally and commit it to the repo under `reports/persona/latest/`. Vercel picks it up on next deploy. Document that automated Railway→Vercel publishing is a v2 enhancement.

3. **Confusion point screenshot capture timing**
   - What we know: The agent loop captures screenshots after every action. We don't have direct access to "when Claude is confused" — we infer it from the JSON confusion_points list.
   - What's unclear: Whether we can capture the screenshot at the exact step number mentioned in confusion_points[i]["step"] by looking up the messages list.
   - Recommendation: Save all agent screenshots to disk during the run (one per action) with step numbers as filenames. The confusion_points reference is then `screenshots/step_{n}.png`. This adds disk I/O but enables forensic review.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.9+ | anthropic SDK | Yes | 3.13.11 | — |
| anthropic SDK | Computer Use API | Yes | 0.86.0 | — |
| playwright 1.58.0 | Browser backend | Yes | 1.58.0 | — |
| fastapi | Railway trigger endpoint | Yes | 0.122.0 | — |
| uvicorn | ASGI server for FastAPI | Yes | 0.38.0 | — |
| jinja2 | HTML report generation | Yes | 3.1.6 | — |
| ANTHROPIC_API_KEY | Agent API calls | Configured in .env | — | Tests skip without it |
| Chromium binary | Playwright browser | Yes (installed in venv) | 1.58.0 bundle | `playwright install chromium` |
| Railway CLI / account | Deployment | Unknown | — | Local CLI run only |
| Vercel project | Static report hosting | Unknown | — | Local file open |

**Missing dependencies with no fallback:**
- Railway account and project: required for D-09 deployment. If unavailable, persona sweep still runs locally via `pytest tests/persona_agents/`.
- Vercel project connected to repo: required for D-10. If unavailable, report is a local HTML file.

**Missing dependencies with fallback:**
- Railway/Vercel unavailable: full persona sweep runs locally; report opens from `reports/persona/<run_id>/persona_matrix.html`.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pytest.ini` (existing, needs `persona_agent` marker added) |
| Quick run command | `pytest tests/persona_agents/ -k "tech_savvy" --tb=short` |
| Full suite command | `pytest tests/persona_agents/ --html=reports/persona_report.html` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| P7-SC1 | Persona produces structured JSON with friction_score and confusion_points | Persona agent | `pytest tests/persona_agents/ -k "registration" -v` | No — Wave 0 |
| P7-SC2 | 5 personas configurable via Python dataclasses | Unit | `pytest tests/persona_agents/ -k "personas" -v` | No — Wave 0 |
| P7-SC3 | HTML matrix report renders from JSON artifacts | Script test | `python scripts/generate_persona_report.py` | No — Wave 0 |
| P7-SC4 | FastAPI endpoint accepts POST /sweep and returns job_id | Integration | `pytest tests/test_api_runner.py` | No — Wave 0 |
| P7-SC5 | Confusion points list non-empty for low-literacy persona | Persona agent | `pytest tests/persona_agents/ -k "low_literacy" -v` | No — Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/persona_agents/ -k "tech_savvy and registration" --tb=short` (single fastest scenario)
- **Per wave merge:** `pytest tests/persona_agents/ --tb=short` (all 15 scenarios)
- **Phase gate:** Full 15-scenario sweep green + HTML report renders before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/persona_agents/__init__.py` — package marker
- [ ] `tests/persona_agents/personas.py` — 5 persona dataclass definitions
- [ ] `tests/persona_agents/persona_runner.py` — `run_persona_scenario()` function
- [ ] `tests/persona_agents/friction_scorer.py` — `calculate_friction_score()` function
- [ ] `tests/persona_agents/conftest.py` — `run_id` fixture and persona-specific fixtures
- [ ] `tests/persona_agents/test_persona_sweep.py` — 15 test functions (5 personas x 3 flows)
- [ ] `api/__init__.py` — package marker
- [ ] `api/persona_runner.py` — FastAPI app with `/sweep` and `/health` endpoints
- [ ] `templates/persona_report.html.j2` — Jinja2 heatmap matrix template
- [ ] `scripts/generate_persona_report.py` — CLI report generator
- [ ] `pytest.ini` — add `persona_agent` marker registration
- [ ] `requirements.txt` — add `fastapi`, `uvicorn` if not already present (they are; no action)

---

## Sources

### Primary (HIGH confidence)

- Existing codebase: `tests/ai_agents/agent_runner.py`, `computer_use_backend.py`, `conftest.py` — Phase 6 implementation verified 2026-03-30
- `pip show fastapi uvicorn jinja2 anthropic` — package versions confirmed installed 2026-03-30
- `settings.py` — pydantic-settings config pattern confirmed
- Phase 6 RESEARCH.md — Computer Use API patterns, cost model, pitfalls (verified and battle-tested)

### Secondary (MEDIUM confidence)

- FastAPI Background Tasks docs (https://fastapi.tiangolo.com/tutorial/background-tasks/) — `BackgroundTasks` pattern for long-running agent jobs
- Jinja2 Environment + FileSystemLoader pattern — standard documented usage, no verification needed for this well-known API

### Tertiary (LOW confidence — not used for technical decisions)

- Railway nixpacks Python detection behavior — assumed to work for standard Python projects; verify with `railway.json` or `Procfile` if needed

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages confirmed installed; no new dependencies
- Architecture: HIGH — extends verified Phase 6 patterns; new code is orchestration only
- Persona prompts: MEDIUM — effectiveness of persona prompts requires empirical validation; cannot guarantee determinism
- Deployment: MEDIUM — FastAPI/uvicorn deployment to Railway is standard; exact Railway build commands unverified for this project

**Research date:** 2026-03-30
**Valid until:** 2026-04-30 (30 days; stable stack)
