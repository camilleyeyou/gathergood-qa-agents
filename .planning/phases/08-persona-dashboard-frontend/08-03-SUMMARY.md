---
phase: 08-persona-dashboard-frontend
plan: 03
subsystem: ui
tags: [nextjs, recharts, react, tailwind, dashboard, sparkline, run-selector, base-ui]

# Dependency graph
requires:
  - phase: 08-persona-dashboard-frontend
    provides: HeatmapMatrix with detail panel, DeltaBadge, types, utils from plans 01-02
provides:
  - RunSelector component with shadcn Select dropdown and aggregate delta badges per run
  - Sparkline component with recharts LineChart for friction trend visualization
  - HeatmapMatrix updated to use RunSelector and show Sparkline in slide-over detail panel
affects:
  - Future phases consuming persona dashboard (Vercel deployment)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Aggregate delta: average friction delta across all persona-flow pairs for a run-level badge"
    - "Sparkline inside detail panel only shown when 2+ runs exist (graceful degradation)"
    - "base-ui Select onValueChange receives string | null — null guard required before numeric conversion"

key-files:
  created:
    - dashboard/src/components/RunSelector.tsx
    - dashboard/src/components/Sparkline.tsx
  modified:
    - dashboard/src/components/HeatmapMatrix.tsx

key-decisions:
  - "RunSelector computes aggregate delta by averaging raw friction delta across all paired persona-flow results (not re-using computeDelta helper)"
  - "Sparkline shown in detail panel (not in each heatmap cell) to keep cell size manageable"
  - "base-ui Select onValueChange type is (value: string | null, ...) — must guard for null before calling onRunChange"

patterns-established:
  - "Aggregate delta pattern: sum raw deltas, average, then derive direction from sign of average"
  - "Sparkline guard: filter out score=0 entries (missing results) before rendering"

requirements-completed:
  - P8-SC3
  - P8-SC4
  - P8-SC5

# Metrics
duration: 3min
completed: 2026-03-31
---

# Phase 8 Plan 03: Run Selector, Sparklines, and Visual Verification Summary

**RunSelector dropdown with aggregate delta badges and Sparkline trend charts integrated into HeatmapMatrix detail panel, completing the persona dashboard with historical run tracking**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-31T14:25:28Z
- **Completed:** 2026-03-31T14:28:38Z
- **Tasks:** 2 (Task 1 executed; Task 2 auto-approved in --auto mode)
- **Files modified:** 3

## Accomplishments

- Created Sparkline.tsx using recharts ResponsiveContainer + LineChart with Tooltip, handles <2 data points gracefully
- Created RunSelector.tsx using shadcn (base-ui) Select with per-run aggregate delta badges showing average friction change
- Updated HeatmapMatrix.tsx to use RunSelector component and embed Sparkline in the slide-over detail panel when 2+ runs are available
- Build passes (Next.js 15.5 Turbopack, TypeScript strict mode)

## Task Commits

Each task was committed atomically:

1. **Task 1: Build RunSelector and Sparkline components, integrate into HeatmapMatrix** - `733f20c` (feat)
2. **Task 2: Visual verification** - Auto-approved (checkpoint:human-verify in --auto mode)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `dashboard/src/components/Sparkline.tsx` - recharts inline trend chart for friction score history per persona-flow pair; renders dash if < 2 data points
- `dashboard/src/components/RunSelector.tsx` - shadcn Select dropdown with run IDs, aggregate delta badges, ISO timestamp formatting, run count summary
- `dashboard/src/components/HeatmapMatrix.tsx` - replaced inline select with RunSelector import; added Sparkline in detail panel with buildSparklineData helper

## Decisions Made

- RunSelector computes aggregate delta by averaging raw friction delta across all paired persona-flow results rather than re-using computeDelta helper (direct arithmetic is cleaner at the aggregation level)
- Sparkline placed in the detail panel only (not in each heatmap cell) to keep cell dimensions manageable
- base-ui Select's onValueChange has type `(value: string | null, eventDetails: ...) => void` — added null guard before passing to onRunChange

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed TypeScript type error on base-ui Select onValueChange**
- **Found during:** Task 1 (build verification)
- **Issue:** Plan expected standard React `onChange` pattern; base-ui's onValueChange passes `string | null`, not `string`. Build failed with type error.
- **Fix:** Changed callback signature to `(value: string | null) => void` with null guard
- **Files modified:** dashboard/src/components/RunSelector.tsx
- **Verification:** `npm run build` exits 0
- **Committed in:** `733f20c` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (type error)
**Impact on plan:** Minor — base-ui API requires null handling; no scope change.

## Issues Encountered

- base-ui Select onValueChange type differs from standard HTML select onChange — required null guard on value before numeric conversion. Caught at build time.

## User Setup Required

None — no external service configuration required for this plan. Dashboard is a static Next.js build.

## Next Phase Readiness

- Phase 8 plan 3 of 3 complete — all three plans in Phase 8 are now done
- Dashboard fully functional: heatmap, detail panel, run selector, sparklines, responsive layout
- Ready for Vercel deployment (see plan frontmatter user_setup for Vercel project linking steps)
- No blockers

---
*Phase: 08-persona-dashboard-frontend*
*Completed: 2026-03-31*
