---
phase: 8
slug: persona-dashboard-frontend
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Next.js build + manual browser verification |
| **Config file** | `dashboard/next.config.js` |
| **Quick run command** | `cd dashboard && npm run build` |
| **Full suite command** | `cd dashboard && npm run build && npx serve out` |
| **Estimated runtime** | ~30 seconds (build) |

---

## Sampling Rate

- **After every task commit:** Run `cd dashboard && npm run build`
- **After every plan wave:** Run `cd dashboard && npm run build && npx serve out`
- **Before `/gsd:verify-work`:** Full build must succeed
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | P8-SC4 | build | `cd dashboard && npm run build` | ❌ W0 | ⬜ pending |
| 08-02-01 | 02 | 1 | P8-SC1 | build | `cd dashboard && npm run build` | ❌ W0 | ⬜ pending |
| 08-03-01 | 03 | 2 | P8-SC2 | build | `cd dashboard && npm run build` | ❌ W0 | ⬜ pending |
| 08-04-01 | 04 | 2 | P8-SC3, P8-SC5 | build | `cd dashboard && npm run build` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `dashboard/package.json` — Next.js project scaffold
- [ ] `dashboard/next.config.js` — Build configuration
- [ ] `npm install` — Install dependencies

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Heatmap cells render correct colors | P8-SC1 | Visual verification | Open dashboard, compare cell colors to friction scores |
| Slide-over panel opens on cell click | P8-SC2 | Interactive UI | Click a heatmap cell, verify panel opens with confusion details |
| Historical run selector works | P8-SC3 | Interactive UI | Select different runs, verify data changes |
| Mobile responsive at 375px | P8-SC5 | Visual verification | Resize browser to 375px, verify layout |
| Vercel deployment works | P8-SC4 | Deployment verification | Push to Vercel, verify live URL loads |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
