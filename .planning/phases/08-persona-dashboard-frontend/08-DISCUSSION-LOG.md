# Phase 8: Persona Dashboard Frontend - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-30
**Phase:** 08-persona-dashboard-frontend
**Areas discussed:** Framework & Rendering, Dashboard Layout, Interactivity & Drill-downs, Historical Runs, Data Pipeline
**Mode:** --auto (all decisions auto-selected as recommended defaults)

---

## Framework & Rendering

| Option | Description | Selected |
|--------|-------------|----------|
| Static import at build time | JSON committed to repo, Next.js reads at build | ✓ |
| API route fetching | Next.js API routes serve JSON | |
| Client-side fetch from S3/CDN | Store JSON externally | |

**User's choice:** Static import at build time (auto-selected)

| Option | Description | Selected |
|--------|-------------|----------|
| App Router with Server Components | Modern Next.js, server components read files directly | ✓ |
| Pages Router with getStaticProps | Legacy but well-documented | |

**User's choice:** App Router with Server Components (auto-selected)

---

## Dashboard Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Single page with tabbed sections | Heatmap default, tabs for comparison/settings | ✓ |
| Multi-page with sidebar nav | Separate pages for matrix, details, history | |
| Single scroll page | Everything visible on one long page | |

**User's choice:** Single page with tabbed sections (auto-selected)

---

## Interactivity & Drill-downs

| Option | Description | Selected |
|--------|-------------|----------|
| Slide-over panel | Right panel opens on cell click, stays open across cells | ✓ |
| Modal dialog | Centered overlay with confusion details | |
| Inline expansion | Row expands below the cell | |

**User's choice:** Slide-over panel (auto-selected)

---

## Historical Runs

| Option | Description | Selected |
|--------|-------------|----------|
| Scan directory at build time | Each reports/persona/ subdirectory is a run | ✓ |
| Database-backed run list | Overkill for static site | |
| Single latest run only | No history tracking | |

**User's choice:** Scan directory at build time (auto-selected)

---

## Data Pipeline

| Option | Description | Selected |
|--------|-------------|----------|
| Git commit trigger | Railway commits JSON, push triggers Vercel rebuild | ✓ |
| Webhook from Railway | Railway notifies Vercel to rebuild | |
| Manual upload | User copies JSON files | |

**User's choice:** Git commit trigger (auto-selected)

---

## Claude's Discretion

- Component library choice
- Tailwind color values for heatmap
- Slide-over animation
- Chart library for sparklines
- Next.js app folder structure

## Deferred Ideas

None
