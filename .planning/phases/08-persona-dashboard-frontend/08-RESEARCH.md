# Phase 8: Persona Dashboard Frontend - Research

**Researched:** 2026-03-30
**Domain:** Next.js static site, data visualization, Vercel deployment
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Next.js with App Router and React Server Components — server components read JSON files directly at build time, no client-side fetch needed
- **D-02:** Static Site Generation (SSG) via server components — Vercel rebuilds on push, automatically picking up new run data
- **D-03:** No API routes needed — all data comes from JSON files in `reports/persona/` at build time
- **D-04:** Single-page layout with tabbed sections: heatmap matrix (default), run comparison, settings
- **D-05:** Run selector dropdown at top of page, sorted by date (most recent first), with delta badges showing score changes between consecutive runs
- **D-06:** Heatmap matrix is the hero view — personas as rows, flows as columns, cells color-coded green (1-3) / yellow (4-6) / red (7-10) matching Phase 7's `friction-low`/`friction-mid`/`friction-high` classes
- **D-07:** Clicking a heatmap cell opens a right-side slide-over panel showing: friction score breakdown (step ratio, confusion penalty), confusion points with severity badges, screenshots for each confusion point, improvement suggestions
- **D-08:** Panel stays open while navigating between cells — click another cell to swap content without closing
- **D-09:** Task completion status shown as checkmark/X badge on each cell
- **D-10:** Runs discovered by scanning `reports/persona/` subdirectories at build time — each subdirectory name is the run ID
- **D-11:** Run comparison shows delta badges (friction score up/down arrows with magnitude) between selected run and previous run
- **D-12:** Trend visualization: simple sparkline or mini chart showing friction score history per persona-flow pair
- **D-13:** Git commit trigger — Railway agent writes JSON, commits to repo, push triggers Vercel rebuild
- **D-14:** No extra infrastructure (no database, no API, no S3) — JSON files in git are the data store
- **D-15:** Tailwind CSS for styling (standard Next.js companion)
- **D-16:** Mobile-responsive: works at 375px, 768px, 1280px+ (success criterion P8-SC5)

### Claude's Discretion
- Component library choice (shadcn/ui, headless UI, or custom)
- Exact Tailwind color values for heatmap cells
- Animation/transition details for slide-over panel
- Chart library for sparklines (if any)
- Exact file/folder structure within the Next.js app

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| P8-SC1 | Heatmap matrix visible with correct color coding (green/yellow/red) | JSON data schema confirmed; friction thresholds ≤3/≤6/>6 from template; Tailwind bg-* classes map directly |
| P8-SC2 | Clicking a cell opens slide-over panel with friction breakdown, confusion points, screenshots | shadcn/ui Sheet component provides accessible slide-over; JSON schema includes all required fields |
| P8-SC3 | Run selector shows delta badges between consecutive runs | Build-time directory scan produces sorted run list; delta calculation is pure arithmetic on friction_score fields |
| P8-SC4 | Historical sparkline shows friction trend per persona-flow pair | Recharts LineChart (compact) or pure SVG path sufficient; data is available across all run directories |
| P8-SC5 | Mobile-responsive at 375px, 768px, 1280px+ | Tailwind responsive prefixes (sm:/md:/lg:) + overflow-x-auto on heatmap table handles small viewports |
</phase_requirements>

---

## Summary

Phase 8 builds a standalone Next.js application (App Router, React Server Components) that reads Phase 7's JSON artifacts from `reports/persona/` at build time and renders an interactive heatmap dashboard. The dashboard is deployed on Vercel and automatically rebuilds whenever new persona run data is committed to the repository.

The core data contract is already established: each JSON file at `reports/persona/<run_id>/<persona>_<flow>.json` contains a flat result dict with fields `persona`, `flow`, `literacy_level`, `task_completed`, `friction_score`, `steps_taken`, `optimal_steps`, `confusion_points` (list of `{step, description, severity, screenshot_path?}`), `suggestions`, and `tokens_used`. The dashboard consumes exactly this schema — no transformation layer is needed.

The application has no backend, no API routes, and no database. All interactivity (cell selection, panel state, run switching) is purely client-side React state after the static build. The build pipeline reads the file system with Node.js `fs` in Server Components, so all data loading happens at `next build` time and zero runtime infrastructure is needed.

**Primary recommendation:** Use Next.js 15 with App Router + Tailwind CSS v4 + shadcn/ui's Sheet component for the slide-over panel. Use Recharts LineChart (compact, no axes) for sparklines. Scaffold with `create-next-app` inside a `dashboard/` subdirectory of the monorepo so the existing Python test project is not disturbed.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| next | 15.x (latest: 15.3.x) | Framework + SSG + App Router | Locked decision D-01/D-02; Vercel-native, optimal static build support |
| react | 19.2.4 | UI runtime | Required by Next.js 15 peer dep; latest stable |
| react-dom | 19.2.4 | DOM renderer | Paired with react |
| typescript | 5.x (use ~5.7 for Next.js 15 compat) | Type safety | Default in `create-next-app`; catches JSON schema mismatches at build time |
| tailwindcss | 4.2.2 | Utility CSS | Locked decision D-15; v4 is the current release with zero-config |
| @tailwindcss/postcss | 4.x | PostCSS plugin for Tailwind v4 | Required for v4 integration in Next.js |

> **Note on Next.js version:** `npm view next version` returns 16.2.1 as of 2026-03-30. However, this is under active development. Use `next@15` explicitly (e.g., `15.3.x`) for a stable, production-ready release. Next.js 15 is the current LTS-equivalent for this project. Verify with `npm view next@15 version` before scaffolding.

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @radix-ui/react-dialog | 1.1.15 | Accessible dialog/sheet primitive | Underpins shadcn/ui Sheet; installed automatically by shadcn CLI |
| clsx | 2.1.1 | Conditional className utility | Combine Tailwind classes cleanly |
| tailwind-merge | 3.5.0 | Merge conflicting Tailwind classes | Required by shadcn/ui components |
| class-variance-authority | 0.7.1 | Type-safe component variants | Required by shadcn/ui components |
| recharts | 3.8.1 | Sparkline trend charts | Declarative React components; LineChart with no axes = compact sparkline |
| lucide-react | 1.7.0 | Icon set | Arrow-up/arrow-down for delta badges; checkmark/X for task completion |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| shadcn/ui Sheet | Custom slide-over | Custom saves a dep but loses focus trap, ARIA, keyboard close (Escape) for free |
| shadcn/ui Sheet | Headless UI Dialog | Both are Radix-based; shadcn copies source so easier to customise Tailwind styles |
| recharts LineChart | react-sparklines | react-sparklines is unmaintained (last release 2018); recharts is actively maintained |
| recharts LineChart | Plain SVG `<polyline>` | Zero dep; viable for 5 data points; recharts preferred for tooltip on hover |
| tailwindcss v4 | tailwindcss v3 | v3 still works; v4 zero-config is simpler for a greenfield app; v4 confirmed working with Next.js 15 |

**Installation (inside `dashboard/` subdirectory):**
```bash
npx create-next-app@15 dashboard --typescript --tailwind --app --src-dir --no-eslint --import-alias "@/*"
cd dashboard
npx shadcn@latest init
npx shadcn@latest add sheet badge button select tabs
npm install recharts lucide-react
```

**Version verification (run before writing Standard Stack table):**
```bash
npm view next@15 version
npm view tailwindcss version
npm view recharts version
npm view lucide-react version
```

---

## Architecture Patterns

### Recommended Project Structure
```
dashboard/                    # New Next.js app — sibling to existing Python project
├── src/
│   ├── app/
│   │   ├── layout.tsx        # Root layout: fonts, global styles
│   │   ├── page.tsx          # Single page — server component reads persona runs
│   │   └── globals.css       # Tailwind @import
│   ├── components/
│   │   ├── HeatmapMatrix.tsx # Client component — heatmap with cell click handlers
│   │   ├── DetailPanel.tsx   # Client component — Sheet slide-over panel
│   │   ├── RunSelector.tsx   # Client component — dropdown + delta badges
│   │   ├── Sparkline.tsx     # Client component — recharts inline trend chart
│   │   ├── DeltaBadge.tsx    # Presentational — arrow + magnitude display
│   │   └── ui/               # shadcn generated components (sheet, badge, etc.)
│   ├── lib/
│   │   ├── data.ts           # Server-side: readPersonaRuns(), loadRunData()
│   │   ├── types.ts          # PersonaResult, RunSummary TypeScript types
│   │   └── utils.ts          # cn() helper, frictionClass(), deltaLabel()
│   └── hooks/
│       └── useSelectedCell.ts # Client hook for selected (persona, flow) state
├── next.config.ts            # output: 'export' NOT set — Vercel handles full SSR/SSG
├── components.json           # shadcn config
├── package.json
└── tsconfig.json
```

### Pattern 1: Server Component Data Loading at Build Time

**What:** `page.tsx` is a React Server Component that calls `fs.readdir` + `fs.readFileSync` to load all persona runs at build time. The loaded data is passed as props to client components.

**When to use:** All data loading — server components never run in the browser, so `fs` is safe. This is the locked decision (D-01/D-03).

**Example:**
```typescript
// src/lib/data.ts — runs on server only (build time on Vercel)
import fs from 'node:fs'
import path from 'node:path'
import type { PersonaResult, RunData } from './types'

const PERSONA_DIR = path.join(process.cwd(), '..', 'reports', 'persona')

export function readPersonaRuns(): string[] {
  if (!fs.existsSync(PERSONA_DIR)) return []
  return fs.readdirSync(PERSONA_DIR)
    .filter(name => fs.statSync(path.join(PERSONA_DIR, name)).isDirectory())
    .sort()
    .reverse()  // most recent first (ISO timestamp run IDs sort lexicographically)
}

export function loadRunData(runId: string): PersonaResult[] {
  const runDir = path.join(PERSONA_DIR, runId)
  return fs.readdirSync(runDir)
    .filter(f => f.endsWith('.json'))
    .map(f => JSON.parse(fs.readFileSync(path.join(runDir, f), 'utf-8')) as PersonaResult)
}
```

```typescript
// src/app/page.tsx — Server Component
import { readPersonaRuns, loadRunData } from '@/lib/data'
import { HeatmapMatrix } from '@/components/HeatmapMatrix'

export default function Page() {
  const runs = readPersonaRuns()                          // [] when no data yet
  const allRunsData = runs.map(id => ({
    runId: id,
    results: loadRunData(id),
  }))

  return <HeatmapMatrix runs={allRunsData} />
}
```

**Critical path note:** `process.cwd()` in Vercel points to the project root (the `dashboard/` directory). The path `../reports/persona` navigates up one level to the monorepo root where `reports/persona/` lives. This MUST be verified in Vercel project settings — the root directory for the Vercel project must be set to `dashboard/`, and the monorepo root must contain `reports/persona/`.

### Pattern 2: Client State for Interactivity

**What:** All interactivity (selected cell, open panel, active run) lives in client component state — no URL params, no server state. The server component passes pre-loaded data arrays as props.

**When to use:** Selected cell tracking, panel open/close (D-07/D-08).

**Example:**
```typescript
// src/components/HeatmapMatrix.tsx
'use client'

import { useState } from 'react'
import { Sheet, SheetContent } from '@/components/ui/sheet'
import { DetailPanel } from './DetailPanel'
import type { PersonaResult, RunData } from '@/lib/types'

const ALL_PERSONAS = ['tech_savvy', 'casual', 'low_literacy', 'non_native', 'impatient']
const ALL_FLOWS = ['registration', 'browsing', 'checkout']

function frictionClass(score: number): string {
  if (score <= 3) return 'bg-[#d4edda] text-[#155724]'  // matches existing template
  if (score <= 6) return 'bg-[#fff3cd] text-[#856404]'
  return 'bg-[#f8d7da] text-[#721c24]'
}

export function HeatmapMatrix({ runs }: { runs: RunData[] }) {
  const [selectedCell, setSelectedCell] = useState<{ persona: string; flow: string } | null>(null)
  const [activeRunId, setActiveRunId] = useState(runs[0]?.runId ?? null)

  const activeResults = runs.find(r => r.runId === activeRunId)?.results ?? []
  const resultMap = Object.fromEntries(
    activeResults.map(r => [`${r.persona}__${r.flow}`, r])
  )

  return (
    <>
      <RunSelector runs={runs} active={activeRunId} onChange={setActiveRunId} />
      <div className="overflow-x-auto">   {/* mobile scroll — P8-SC5 */}
        <table>
          {/* ...matrix rows per ALL_PERSONAS/ALL_FLOWS... */}
          {/* cell onClick: setSelectedCell({ persona, flow }) */}
        </table>
      </div>
      <Sheet open={selectedCell !== null} onOpenChange={(open) => !open && setSelectedCell(null)}>
        <SheetContent side="right" className="w-[480px] sm:max-w-[480px] overflow-y-auto">
          {selectedCell && <DetailPanel result={resultMap[`${selectedCell.persona}__${selectedCell.flow}`]} />}
        </SheetContent>
      </Sheet>
    </>
  )
}
```

### Pattern 3: Delta Badge Calculation

**What:** Compare friction scores between the selected run and the immediately previous run.

**When to use:** Run selector and cell display (D-05, D-11).

**Example:**
```typescript
// src/lib/utils.ts
export function computeDelta(current: number, previous: number | undefined): { delta: number; direction: 'up' | 'down' | 'same' } {
  if (previous === undefined) return { delta: 0, direction: 'same' }
  const delta = current - previous
  return { delta: Math.abs(delta), direction: delta > 0 ? 'up' : delta < 0 ? 'down' : 'same' }
}
```

### Pattern 4: Recharts Sparkline (no axes)

**What:** Inline friction trend chart per persona-flow pair across all historical runs. Recharts LineChart with axes hidden and no container margin.

**When to use:** D-12 trend visualization inside the detail panel or heatmap cell tooltip.

**Example:**
```typescript
// src/components/Sparkline.tsx
'use client'
import { LineChart, Line, ResponsiveContainer, Tooltip } from 'recharts'

export function Sparkline({ data }: { data: { run: string; score: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={40}>
      <LineChart data={data} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
        <Line type="monotone" dataKey="score" dot={false} strokeWidth={2} stroke="#6366f1" />
        <Tooltip
          content={({ active, payload }) =>
            active && payload?.length
              ? <div className="text-xs bg-white border px-2 py-1 rounded shadow">{payload[0].value}</div>
              : null
          }
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
```

### Pattern 5: Vercel Deployment for Monorepo

**What:** Vercel project configured with root directory set to `dashboard/` so it builds only the Next.js app, not the Python project root.

**When to use:** Initial Vercel project setup (not a code pattern, but a critical config decision).

**Configuration in Vercel dashboard:**
- Root Directory: `dashboard`
- Framework Preset: Next.js (auto-detected)
- Build Command: `next build` (default)
- Output Directory: `.next` (default — NOT `out` since `output: 'export'` is not used)
- Install Command: `npm install`

**Why NOT `output: 'export'`:** The locked decisions use Vercel's native Next.js integration which handles SSG automatically. Static export (`output: 'export'`) disables Next.js Image Optimization and is intended for non-Vercel static hosting. On Vercel, simply deploying an App Router app produces SSG for pages with no dynamic data — which is exactly our case. No `output: 'export'` needed.

### Anti-Patterns to Avoid
- **Client-side `fetch()` of JSON files:** Locked decision D-01 specifies server components read files at build time. Never `fetch('/reports/persona/...')` from the browser — those paths are not served.
- **Storing selected cell state in URL params:** Adds complexity for no benefit. useState is sufficient for this internal dashboard.
- **`getStaticProps` (Pages Router pattern):** The locked decision is App Router. `getStaticProps` does not exist in App Router — use async Server Components instead.
- **`output: 'export'` in next.config:** Disables image optimization and Vercel's native SSG pipeline. Unnecessary on Vercel.
- **Importing `recharts` in Server Components:** Recharts uses browser APIs. Always mark components that use recharts with `'use client'`.
- **`time.sleep()` equivalents in data loading:** No artificial delays. The `fs.readdir` calls are synchronous at build time.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Slide-over panel with focus trap | Custom overlay + portal | shadcn/ui Sheet (via Radix Dialog) | Focus trap, ARIA role="dialog", Escape key close, scroll lock — all complex to get right |
| Icon set | SVG inline strings | lucide-react | Tree-shakeable, consistent stroke width, typed props |
| className merging | String concatenation | clsx + tailwind-merge | Tailwind class conflicts (e.g., two `bg-` classes) silently drop one; `cn()` merges correctly |
| Accessible badge variants | Inline style objects | shadcn/ui Badge with CVA variants | Correct contrast ratios, keyboard accessibility handled by library |
| Responsive table scroll | CSS overflow hacks | `overflow-x-auto` wrapper div | Native browser scroll with momentum on iOS |

**Key insight:** The slide-over panel (D-07) is the most complex UI element. Radix Dialog handles 12+ edge cases (focus management, scroll locking, outside click, portal rendering) that a custom solution will miss.

---

## JSON Data Schema (from Phase 7)

This is the authoritative schema the dashboard must consume. Confirmed from `artifact_writer.py` and `friction_scorer.py`.

```typescript
// src/lib/types.ts
export interface ConfusionPoint {
  step: number | string
  description: string
  severity: 'low' | 'medium' | 'high'
  screenshot_path?: string   // relative path from repo root, may be absent
}

export interface PersonaResult {
  persona: string             // e.g. "tech_savvy" | "casual" | "low_literacy" | "non_native" | "impatient"
  flow: string                // e.g. "registration" | "browsing" | "checkout"
  literacy_level: number      // 1-5
  task_completed: boolean
  friction_score: number      // 1-10
  steps_taken: number
  optimal_steps: number       // from OPTIMAL_STEPS: {registration: 6, browsing: 3, checkout: 5}
  confusion_points: ConfusionPoint[]
  suggestions: string[]
  tokens_used: number
}

export interface RunData {
  runId: string               // subdirectory name — treat as ISO timestamp for sorting
  results: PersonaResult[]    // all .json files from that subdirectory
}
```

**Canonical ordering (must match for visual consistency):**
```typescript
// Copied from scripts/generate_persona_report.py
export const ALL_PERSONAS = ['tech_savvy', 'casual', 'low_literacy', 'non_native', 'impatient']
export const ALL_FLOWS = ['registration', 'browsing', 'checkout']
```

**Friction color mapping (matches templates/persona_report.html.j2):**
```typescript
// Exact hex values from existing template — DO NOT change
export const FRICTION_COLORS = {
  low:  { bg: '#d4edda', text: '#155724' },  // score 1-3
  mid:  { bg: '#fff3cd', text: '#856404' },  // score 4-6
  high: { bg: '#f8d7da', text: '#721c24' },  // score 7-10
}
```

---

## Common Pitfalls

### Pitfall 1: `process.cwd()` Path Resolution on Vercel
**What goes wrong:** `fs.readdir(path.join(process.cwd(), '../reports/persona'))` works locally but fails on Vercel because Vercel sets `cwd` to the `dashboard/` subdirectory, and `..` navigates to the Vercel build root — not the monorepo root.
**Why it happens:** Vercel clones the entire monorepo but builds from the `Root Directory` setting. The relative path works only if the monorepo root is in the checkout and the path traversal is correct.
**How to avoid:** Use an absolute path strategy. Either (a) set an env var `PERSONA_DATA_DIR` pointing to the correct directory, or (b) use `path.join(process.cwd(), '..', 'reports', 'persona')` and verify this resolves correctly in a Vercel preview deploy before finalizing. Test with a build-time log: `console.log('Data dir:', PERSONA_DIR)` — visible in Vercel build logs.
**Warning signs:** Build succeeds but `runs` array is empty; dashboard shows "No runs found" after deploying.

### Pitfall 2: Empty `reports/persona/` During First Build
**What goes wrong:** The dashboard is built before any persona agent runs have committed data. `fs.readdir` on an empty or nonexistent directory throws or returns `[]`.
**Why it happens:** Phase 7 agent hasn't run yet, or `reports/persona/` is gitignored.
**How to avoid:** (1) Add `reports/persona/.gitkeep` to ensure the directory exists in git. (2) Handle the empty-array case gracefully — render a "No runs yet" empty state instead of crashing. Check `fs.existsSync(PERSONA_DIR)` before `fs.readdirSync`.
**Warning signs:** Build error `ENOENT: no such file or directory` or blank dashboard with no error message.

### Pitfall 3: Screenshot Paths in JSON Are Repo-Relative, Not URL-Relative
**What goes wrong:** `confusion_point.screenshot_path` is a relative path like `reports/screenshots/xyz.png` (relative to repo root). Serving this as a Next.js image src fails because Next.js serves assets from `dashboard/public/`.
**Why it happens:** Phase 7 saves screenshots to `reports/screenshots/` which is outside the `dashboard/` app directory. Next.js only serves `dashboard/public/` as static assets.
**How to avoid:** Two options: (a) During build, copy `reports/screenshots/` into `dashboard/public/screenshots/` via a prebuild script (`"prebuild": "cp -r ../reports/screenshots ./public/screenshots"`). (b) If screenshots aren't git-committed (likely), show a placeholder or omit the image — check with `fs.existsSync` before rendering `<img>`.
**Warning signs:** `<img>` tags render but return 404; or build fails trying to optimize images that don't exist.

### Pitfall 4: Recharts Imported in Server Components
**What goes wrong:** `import { LineChart } from 'recharts'` in a Server Component causes a build error because recharts uses `window` and browser-only APIs.
**Why it happens:** Recharts is a browser library; Server Components run in Node.js at build time.
**How to avoid:** Always add `'use client'` at the top of any component file that imports recharts. The `Sparkline.tsx` wrapper must be a client component.
**Warning signs:** Build error: `ReferenceError: window is not defined` during `next build`.

### Pitfall 5: Tailwind v4 Configuration Differences from v3
**What goes wrong:** Using `tailwind.config.js` syntax (v3) with a v4 install, or using `@layer components` patterns that changed in v4.
**Why it happens:** Tailwind v4 uses CSS-first configuration via `@theme` directives in `globals.css` instead of `tailwind.config.js`.
**How to avoid:** In v4, define custom colors directly in `globals.css` using `@theme { --color-friction-low: #d4edda; }` rather than in a JS config file. Use `bg-friction-low` as a Tailwind class. Verify with the [Tailwind v4 migration guide](https://tailwindcss.com/docs/v4-beta).
**Warning signs:** Custom color classes like `bg-[#d4edda]` work (arbitrary values) but named theme tokens don't; or `tailwind.config.js` is silently ignored.

### Pitfall 6: `shadcn@latest` React 19 Peer Dependency Warnings
**What goes wrong:** `npx shadcn@latest add sheet` throws peer dependency warnings with React 19.
**Why it happens:** Some shadcn components have peer deps pinned to React 18.
**How to avoid:** Use `--legacy-peer-deps` flag: `npx shadcn@latest add sheet --legacy-peer-deps`. This is a known, documented issue (see shadcn/ui React 19 docs page).
**Warning signs:** `npm error ERESOLVE` during component installation.

### Pitfall 7: Run ID Sort Order
**What goes wrong:** `fs.readdirSync` returns directory entries in filesystem order (not date order), so the "most recent first" requirement (D-05) is not met.
**Why it happens:** Filesystem directory entry order is implementation-defined.
**How to avoid:** Always sort explicitly. Since Phase 7 uses timestamp-based run IDs (ISO format or similar), lexicographic sort + reverse gives correct chronological order. Use `.sort().reverse()`. If run IDs are not ISO timestamps, sort by directory mtime instead: `fs.statSync(path).mtimeMs`.
**Warning signs:** Run selector shows runs in wrong order; delta badges compare wrong consecutive pairs.

---

## Runtime State Inventory

Step 2.5 SKIPPED — this is a greenfield frontend phase, not a rename/refactor/migration. No runtime state inventory required.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Next.js build + npm | Yes | v24.13.0 | — |
| npm | Package management | Yes | 11.6.2 | — |
| npx | Scaffolding (create-next-app, shadcn) | Yes | bundled with npm | — |
| Vercel CLI | Deploy + local preview | Yes | 48.2.9 | Manual Vercel dashboard deploy |
| Git | Trigger Vercel rebuild on push | Yes (repo is git) | — | — |
| `reports/persona/` directory | Data source for dashboard | Yes (empty) | — | Render "No runs yet" empty state |

**Missing dependencies with no fallback:** None — all required tools are available.

**Missing dependencies with fallback:**
- `reports/persona/` is currently empty — dashboard must handle this gracefully with an empty state UI.

---

## Validation Architecture

nyquist_validation is enabled (config.json has `"nyquist_validation": true`).

### Test Framework

| Property | Value |
|----------|-------|
| Framework | None established for the dashboard — Wave 0 must add testing |
| Config file | none — see Wave 0 |
| Quick run command | `cd dashboard && npm run build` (build is the primary validation) |
| Full suite command | `cd dashboard && npm run build && npm run lint` |

**Note:** This phase builds a new standalone Next.js app. There is no existing test infrastructure for it. The primary validation mechanism is `next build` succeeding (which exercises all Server Component data loading, TypeScript type checking, and confirms no import errors). UI behavior validation is manual or via Playwright if desired.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| P8-SC1 | Heatmap renders with correct color classes | Build (type check) | `cd dashboard && npm run build` | Wave 0 |
| P8-SC2 | Cell click opens Sheet panel | Manual (browser) | — | Manual-only: requires browser interaction |
| P8-SC3 | Run selector shows delta badges | Build (type check) | `cd dashboard && npm run build` | Wave 0 |
| P8-SC4 | Sparkline renders trend | Build (type check) | `cd dashboard && npm run build` | Wave 0 |
| P8-SC5 | Mobile responsive at 375px | Manual (browser resize or Playwright) | — | Manual-only |

### Sampling Rate
- **Per task commit:** `cd dashboard && npm run build`
- **Per wave merge:** `cd dashboard && npm run build && npm run lint`
- **Phase gate:** Build passes + manual browser check of all 5 success criteria before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `dashboard/` directory — Next.js app scaffold (create-next-app)
- [ ] `dashboard/src/lib/types.ts` — PersonaResult / RunData / ConfusionPoint types
- [ ] `dashboard/src/lib/data.ts` — readPersonaRuns(), loadRunData() with empty-dir safety
- [ ] `reports/persona/.gitkeep` — ensure directory is tracked in git
- [ ] `dashboard/next.config.ts` — no `output: 'export'`; clean defaults

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `getStaticProps` (Pages Router) | Async Server Components (App Router) | Next.js 13 (stable Next.js 14+) | No `getStaticProps`; just `async function Page()` with `await fs.readFile` |
| `tailwind.config.js` | CSS-first `@theme` in globals.css | Tailwind v4 (2025) | No JS config file needed; custom tokens defined in CSS |
| `next export` CLI command | `output: 'export'` in next.config | Next.js 14 | `next export` command removed; use config option if truly needed (not needed on Vercel) |
| shadcn install `npx shadcn-ui@latest` | `npx shadcn@latest` | 2024 (package renamed) | Package name changed; old command fails |

**Deprecated/outdated:**
- `getStaticProps`: Pages Router only — does not exist in App Router.
- `next export` CLI: Removed in Next.js 14+. Use `output: 'export'` config if needed.
- `npx shadcn-ui@latest`: Package renamed to `shadcn`. Use `npx shadcn@latest`.

---

## Open Questions

1. **Screenshot path strategy**
   - What we know: `confusion_point.screenshot_path` is a repo-relative path (e.g., `reports/screenshots/xyz.png`); Phase 7 may or may not commit these to git
   - What's unclear: Are screenshots committed to git, or written locally only? If not committed, they won't be available in the Vercel build.
   - Recommendation: Treat screenshots as optional in the dashboard. Check `screenshot_path` exists before rendering. Add a Wave 1 note to investigate whether Phase 7 commits screenshots.

2. **Vercel project setup — monorepo root vs. dashboard root**
   - What we know: The Vercel project root directory must be set to `dashboard/` for correct builds
   - What's unclear: Is there an existing Vercel project linked to this repo? CONTEXT.md says "existing project may already have Vercel config for the GatherGood frontend (different app)" — the dashboard is a NEW app.
   - Recommendation: Create a new Vercel project linked to this repo with root directory `dashboard/`. Do not reuse the GatherGood frontend Vercel project.

3. **Run ID format for sort order**
   - What we know: Phase 7 uses `run_id` strings; the artifact writer creates `reports/persona/<run_id>/`
   - What's unclear: What exact format does Phase 7 produce for run IDs? (Checked STATE.md — run IDs are described as "timestamp strings" but exact format not confirmed)
   - Recommendation: Implement sort-by-mtime as fallback. `fs.statSync(runDir).mtimeMs` gives the actual creation time regardless of ID format. Use lexicographic sort as primary, mtime as fallback.

---

## Code Examples

Verified patterns from authoritative sources:

### Reading JSON files in a Server Component (fs, Node.js)
```typescript
// Source: Vercel Knowledge Base — "How to Load Data from a File in Next.js"
// https://vercel.com/kb/guide/loading-static-file-nextjs-api-route
import { promises as fs } from 'node:fs'
import path from 'node:path'

// In an async Server Component or server-side function:
const data = await fs.readFile(path.join(process.cwd(), 'data.json'), 'utf-8')
const parsed = JSON.parse(data)
```

### shadcn/ui Sheet component usage
```typescript
// Source: https://ui.shadcn.com/docs/components/radix/sheet
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet"

<Sheet open={open} onOpenChange={setOpen}>
  <SheetContent side="right">
    <SheetHeader>
      <SheetTitle>Panel Title</SheetTitle>
    </SheetHeader>
    {/* content */}
  </SheetContent>
</Sheet>
```

### Tailwind v4 zero-config globals.css
```css
/* Source: https://tailwindcss.com/docs/guides/nextjs */
@import "tailwindcss";

@theme {
  --color-friction-low: #d4edda;
  --color-friction-mid: #fff3cd;
  --color-friction-high: #f8d7da;
}
```

### create-next-app with App Router
```bash
# Source: https://nextjs.org/docs/app/getting-started
npx create-next-app@15 dashboard \
  --typescript \
  --tailwind \
  --app \
  --src-dir \
  --no-eslint \
  --import-alias "@/*"
```

---

## Sources

### Primary (HIGH confidence)
- [Next.js App Router Docs](https://nextjs.org/docs/app) — Server Components, file system access patterns, static builds
- [Next.js Static Exports Guide](https://nextjs.org/docs/app/guides/static-exports) — output: export vs. Vercel native deployment
- [Vercel Knowledge Base: Loading Static Files](https://vercel.com/kb/guide/loading-static-file-nextjs-api-route) — fs.readFile pattern in Next.js
- [shadcn/ui Installation (Next.js)](https://ui.shadcn.com/docs/installation/next) — npx shadcn@latest init
- [shadcn/ui Sheet Component](https://ui.shadcn.com/docs/components/radix/sheet) — slide-over panel API
- [shadcn/ui React 19 Compatibility](https://ui.shadcn.com/docs/react-19) — --legacy-peer-deps requirement
- [Tailwind CSS v4 Next.js Guide](https://tailwindcss.com/docs/guides/nextjs) — PostCSS setup, zero-config
- npm registry (verified 2026-03-30): next@15, tailwindcss@4.2.2, recharts@3.8.1, lucide-react@1.7.0, react@19.2.4
- Phase 7 source code (this repo): `artifact_writer.py`, `friction_scorer.py`, `personas.py`, `generate_persona_report.py`, `templates/persona_report.html.j2` — authoritative JSON schema and color values

### Secondary (MEDIUM confidence)
- [DEV Community: Next.js 15 + shadcn + Tailwind v4 Setup](https://dev.to/darshan_bajgain/setting-up-2025-nextjs-15-with-shadcn-tailwind-css-v4-no-config-needed-dark-mode-5kl) — confirmed zero-config Tailwind v4 pattern
- [Recharts SimpleLineChart Example](https://recharts.github.io/en-US/examples/SimpleLineChart/) — sparkline implementation pattern
- [Vercel Next.js Frameworks Docs](https://vercel.com/docs/frameworks/full-stack/nextjs) — Vercel native SSG without output: export

### Tertiary (LOW confidence)
- WebSearch results on Next.js monorepo root directory Vercel setup — pattern consistent across sources but not from official docs

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — npm registry versions verified 2026-03-30; Next.js/Tailwind/shadcn official docs consulted
- Architecture: HIGH — patterns derived from official Next.js App Router docs + Phase 7 source code (authoritative schema)
- Pitfalls: MEDIUM-HIGH — screenshot path and Vercel cwd pitfalls based on known Next.js behavior; confirmed by official docs and GitHub discussions

**Research date:** 2026-03-30
**Valid until:** 2026-05-30 (Next.js and Tailwind move fast; verify versions before building)
