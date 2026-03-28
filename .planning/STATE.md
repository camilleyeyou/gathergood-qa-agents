# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-28)

**Core value:** Community organizers can create an event, publish it, and have people register (free or paid) with working tickets and QR check-in
**Current focus:** Phase 1 — Foundation

## Current Position

Phase: 1 of 6 (Foundation)
Plan: 0 of TBD in current phase
Status: Ready to plan
Last activity: 2026-03-28 — Roadmap created, traceability table populated

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: —
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: —
- Trend: —

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Init]: Django 5.2 LTS + DRF + Next.js 16 App Router + PostgreSQL 16 stack confirmed
- [Init]: JWT stored in memory (not localStorage) + HttpOnly cookies for refresh tokens — security baseline
- [Init]: HMAC-signed QR codes use dedicated QR_SIGNING_KEY env var, not SECRET_KEY
- [Init]: select_for_update() inside transaction.atomic() required for checkout — ticket overselling prevention
- [Phase 3 note]: Stripe 15.0.0 is a March 2026 major release — verify changelog before Phase 3 implementation

### Pending Todos

None yet.

### Blockers/Concerns

- [Phase 3]: Stripe Python SDK 15.0.0 is a same-month major release — API surface changes must be verified against changelog before checkout implementation begins
- [Phase 5]: Email SMTP provider not yet selected — Postmark, SendGrid, or AWS SES decision needed before Phase 5
- [Phase 1]: Tailwind v4 + Shadcn/UI component compatibility should be verified before committing to component library

## Session Continuity

Last session: 2026-03-28
Stopped at: Roadmap created, STATE.md initialized — ready to begin Phase 1 planning
Resume file: None
