# Phase 8: Persona Dashboard Frontend - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Next.js dashboard deployed on Vercel that visualizes persona agent sweep results. Reads JSON artifacts produced by Phase 7's persona agents, renders an interactive heatmap matrix, provides drill-down into confusion points, and tracks historical runs for UX improvement trending. No backend — purely static site generation from committed JSON data.

</domain>

<decisions>
## Implementation Decisions

### Framework & Rendering
- **D-01:** Next.js with App Router and React Server Components — server components read JSON files directly at build time, no client-side fetch needed
- **D-02:** Static Site Generation (SSG) via `getStaticProps` or server components — Vercel rebuilds on push, automatically picking up new run data
- **D-03:** No API routes needed — all data comes from JSON files in `reports/persona/` at build time

### Dashboard Layout
- **D-04:** Single-page layout with tabbed sections: heatmap matrix (default), run comparison, settings
- **D-05:** Run selector dropdown at top of page, sorted by date (most recent first), with delta badges showing score changes between consecutive runs
- **D-06:** Heatmap matrix is the hero view — personas as rows, flows as columns, cells color-coded green (1-3) / yellow (4-6) / red (7-10) matching Phase 7's `friction-low`/`friction-mid`/`friction-high` classes

### Interactivity & Drill-downs
- **D-07:** Clicking a heatmap cell opens a right-side slide-over panel showing:
  - Friction score with breakdown (step ratio, confusion penalty)
  - Confusion points list with severity badges (low/medium/high)
  - Screenshots for each confusion point (if available)
  - Improvement suggestions list
- **D-08:** Panel stays open while navigating between cells — click another cell to swap content without closing
- **D-09:** Task completion status shown as checkmark/X badge on each cell

### Historical Runs
- **D-10:** Runs discovered by scanning `reports/persona/` subdirectories at build time — each subdirectory name is the run ID
- **D-11:** Run comparison shows delta badges (friction score up/down arrows with magnitude) between selected run and previous run
- **D-12:** Trend visualization: simple sparkline or mini chart showing friction score history per persona-flow pair

### Data Pipeline
- **D-13:** Git commit trigger — Railway agent writes JSON, commits to repo, push triggers Vercel rebuild
- **D-14:** No extra infrastructure (no database, no API, no S3) — JSON files in git are the data store

### Styling
- **D-15:** Tailwind CSS for styling (standard Next.js companion)
- **D-16:** Mobile-responsive: works at 375px, 768px, 1280px+ (success criterion P8-SC5)

### Claude's Discretion
- Component library choice (shadcn/ui, headless UI, or custom)
- Exact Tailwind color values for heatmap cells
- Animation/transition details for slide-over panel
- Chart library for sparklines (if any)
- Exact file/folder structure within the Next.js app

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 7 Data Format
- `tests/persona_agents/personas.py` — Persona dataclass definitions (name, literacy_level, constraints) — dashboard must display these
- `tests/persona_agents/friction_scorer.py` — Scoring formula breakdown (step_ratio, confusion_penalty) — dashboard drill-down shows this
- `tests/persona_agents/artifact_writer.py` — JSON schema for per-persona-per-flow results — dashboard reads these files
- `scripts/generate_persona_report.py` — `ALL_PERSONAS` and `ALL_FLOWS` constants for canonical ordering — dashboard must match this order

### Existing Report Template
- `templates/persona_report.html.j2` — Existing heatmap design with friction-low/mid/high CSS classes — dashboard should match this visual language

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/generate_persona_report.py` — JSON parsing logic, `generate_report()` and `generate_report_from_results()` functions show the data transformation pipeline
- `templates/persona_report.html.j2` — Color scheme (green #d4edda, yellow #fff3cd, red #f8d7da), layout patterns, expandable confusion sections
- `ALL_PERSONAS = ["tech_savvy", "casual", "low_literacy", "non_native", "impatient"]` — canonical ordering
- `ALL_FLOWS = ["registration", "browsing", "checkout"]` — canonical ordering

### Established Patterns
- JSON artifacts stored at `reports/persona/<run_id>/<persona>_<flow>.json`
- Each JSON contains: `persona`, `flow`, `literacy_level`, `task_completed`, `friction_score`, `steps_taken`, `optimal_steps`, `confusion_points` (list of {step, description, severity}), `suggestions` (list), `tokens_used`

### Integration Points
- `reports/persona/` — data source directory, Next.js reads at build time
- Vercel deployment — existing project may already have Vercel config for the GatherGood frontend (different app)
- The dashboard is a NEW Next.js app, not part of the GatherGood frontend

</code_context>

<specifics>
## Specific Ideas

- The heatmap matrix should feel like a "mission control" view — at a glance you know which personas struggle where
- Delta badges between runs are the key UX insight tool — if you fix something and friction drops, you see it immediately
- Screenshots in the drill-down are critical — seeing the exact moment a 70-year-old persona got confused is more powerful than any score
- The slide-over panel pattern keeps context (you can see the matrix while reading details)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-persona-dashboard-frontend*
*Context gathered: 2026-03-30*
