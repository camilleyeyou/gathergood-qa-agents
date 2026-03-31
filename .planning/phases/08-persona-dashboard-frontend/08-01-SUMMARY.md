---
phase: 08-persona-dashboard-frontend
plan: 01
subsystem: ui
tags: [next.js, react, typescript, tailwind, shadcn-ui, recharts, lucide-react]

# Dependency graph
requires:
  - phase: 07-digital-literacy-persona-agents
    provides: "reports/persona/<run_id>/<persona>_<flow>.json schema"
provides:
  - "Next.js 15 dashboard app in dashboard/ with App Router and TypeScript"
  - "PersonaResult, RunData, ConfusionPoint TypeScript interfaces matching Phase 7 schema"
  - "readPersonaRuns() and loadRunData() server-side data loading from reports/persona/"
  - "frictionClass() and computeDelta() utility helpers"
  - "shadcn/ui Sheet, Badge, Button, Select, Tabs components installed"
  - "Friction color CSS theme tokens (low/mid/high) matching Phase 7 template"
affects: [08-02, 08-03]

# Tech tracking
tech-stack:
  added:
    - next@15.5.14 (App Router, React Server Components, SSG)
    - react@19.2.4
    - tailwindcss@4.2.2 (Tailwind v4 zero-config)
    - shadcn/ui@4.1.1 (Sheet, Badge, Button, Select, Tabs)
    - recharts (sparkline charts)
    - lucide-react (icon set)
    - clsx + tailwind-merge (via shadcn)
  patterns:
    - "Server Component data loading: page.tsx reads fs at build time, passes props to client components"
    - "Friction threshold: score <=3 is low, <=6 is mid, >6 is high (matches Phase 7 HTML template)"
    - "Run IDs are directory names under reports/persona/ — ISO timestamps sort lexicographically"
    - "process.cwd() in dashboard/ points to dashboard root; '../reports/persona' navigates to monorepo root"

key-files:
  created:
    - dashboard/src/lib/types.ts
    - dashboard/src/lib/data.ts
    - dashboard/src/lib/utils.ts
    - dashboard/src/app/page.tsx
    - dashboard/src/app/globals.css
    - dashboard/src/app/layout.tsx
    - dashboard/src/components/ui/sheet.tsx
    - dashboard/src/components/ui/badge.tsx
    - dashboard/src/components/ui/button.tsx
    - dashboard/src/components/ui/select.tsx
    - dashboard/src/components/ui/tabs.tsx
    - reports/persona/.gitkeep
  modified: []

key-decisions:
  - "dashboard/ has no .git directory — removed create-next-app's embedded .git to keep it in the monorepo"
  - "types.ts and data.ts created in Task 1 (not Task 2) so placeholder page.tsx build passes — no stub needed"
  - "Friction tokens added to @theme inline block in globals.css (Tailwind v4 pattern, not @theme)"

patterns-established:
  - "Pattern 1: Server Component reads fs at build time — all data loading in data.ts with node:fs"
  - "Pattern 2: frictionClass() maps friction score to Tailwind utility classes using CSS custom properties"
  - "Pattern 3: computeDelta() returns {delta, direction} for run-over-run badge display"

requirements-completed: [P8-SC1, P8-SC3]

# Metrics
duration: 8min
completed: 2026-03-31
---

# Phase 8 Plan 01: Next.js Dashboard Scaffold Summary

**Next.js 15 App Router dashboard in dashboard/ with TypeScript types matching Phase 7 JSON schema, server-side fs data loading from reports/persona/, and shadcn/ui component suite installed**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-31T14:01:03Z
- **Completed:** 2026-03-31T14:09:03Z
- **Tasks:** 2
- **Files modified:** 26 new + 1 modified

## Accomplishments

- Next.js 15 app scaffolded in dashboard/ with App Router, TypeScript, and Tailwind v4 — builds successfully
- shadcn/ui Sheet, Badge, Button, Select, Tabs installed; friction color CSS tokens (#d4edda/#fff3cd/#f8d7da) in globals.css
- PersonaResult/RunData/ConfusionPoint interfaces, ALL_PERSONAS/ALL_FLOWS constants, and FRICTION_COLORS map in types.ts
- readPersonaRuns() and loadRunData() read reports/persona/ at build time with fs.existsSync safety checks for empty dir
- frictionClass() and computeDelta() utility helpers in utils.ts alongside shadcn's cn()

## Task Commits

Each task was committed atomically:

1. **Task 1: Scaffold Next.js app with all dependencies** - `928dea5` (feat)
2. **Task 2: Create type definitions, data loading, and utility functions** - `32bce36` (feat)

## Files Created/Modified

- `dashboard/src/lib/types.ts` - PersonaResult, RunData, ConfusionPoint interfaces; ALL_PERSONAS, ALL_FLOWS, FRICTION_COLORS constants
- `dashboard/src/lib/data.ts` - readPersonaRuns() and loadRunData() using node:fs with empty-dir safety
- `dashboard/src/lib/utils.ts` - cn() from shadcn plus frictionClass() and computeDelta()
- `dashboard/src/app/page.tsx` - Server component placeholder loading runs and rendering count
- `dashboard/src/app/globals.css` - Tailwind v4 theme with friction color tokens
- `dashboard/src/app/layout.tsx` - Title "Persona Dashboard", description "GatherGood UX persona sweep results"
- `dashboard/src/components/ui/` - sheet.tsx, badge.tsx, button.tsx, select.tsx, tabs.tsx
- `reports/persona/.gitkeep` - Empty data directory tracked in git

## Decisions Made

- Removed create-next-app's embedded .git inside dashboard/ to keep it properly tracked in the monorepo as a regular directory
- Created types.ts and data.ts ahead of Task 2's explicit instructions so the Task 1 build verification would pass (page.tsx imports from both — if stubs weren't present, build would fail)
- Friction color tokens placed in existing `@theme inline` block (Tailwind v4 CSS-native pattern) rather than a separate `@theme` block

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created types.ts and data.ts during Task 1**
- **Found during:** Task 1 (scaffold)
- **Issue:** page.tsx imports from @/lib/data and @/lib/types, but the plan deferred those to Task 2; build in Task 1's verify step would fail without them
- **Fix:** Created full implementations of types.ts and data.ts in Task 1 (not stubs) — Task 2 then only added frictionClass/computeDelta to utils.ts
- **Files modified:** dashboard/src/lib/types.ts, dashboard/src/lib/data.ts
- **Verification:** npm run build passed at end of Task 1
- **Committed in:** 928dea5 (Task 1 commit)

**2. [Rule 3 - Blocking] Removed embedded .git from dashboard/**
- **Found during:** Task 1 (git add)
- **Issue:** create-next-app@15 initializes its own git repo, causing "embedded git repository" warning and preventing files from being tracked in the monorepo
- **Fix:** Removed dashboard/.git, then re-staged with git add dashboard/
- **Files modified:** (no file change — structural git fix)
- **Verification:** git ls-files --stage dashboard/ shows 100644 mode (normal files, not 160000 gitlink)
- **Committed in:** 928dea5 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes required for correct git tracking and build success. No scope creep.

## Issues Encountered

- create-next-app@15 (installed as 15.5.14) creates an embedded git repo — removed before committing
- Tailwind v4's `@theme inline` pattern is different from v3's `extend` in tailwind.config — friction tokens were added correctly to the existing `@theme inline` block

## Known Stubs

None — page.tsx renders a real count of loaded runs from reports/persona/ (which is empty but handled gracefully with "No persona runs found" message).

## Next Phase Readiness

- Plans 02 and 03 can build HeatmapMatrix, DetailPanel, RunSelector, and Sparkline components against the stable type contracts in types.ts
- data.ts exports (readPersonaRuns, loadRunData) are ready to be called from page.tsx once Plans 02/03 add client components
- Build is clean and passing — no blockers for Plans 02 or 03

---
*Phase: 08-persona-dashboard-frontend*
*Completed: 2026-03-31*
