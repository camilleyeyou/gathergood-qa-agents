---
phase: 2
slug: core-api-tests
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-28
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x + httpx 0.28.x |
| **Config file** | `pytest.ini` (exists from Phase 1) |
| **Quick run command** | `pytest tests/api/ -x --tb=short` |
| **Full suite command** | `pytest tests/api/ -v --tb=long` |
| **Estimated runtime** | ~30 seconds (network-bound, live API calls) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/api/{module_just_written} -x --tb=short`
- **After every plan wave:** Run `pytest tests/api/ -v --tb=long`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Wave 0 Requirements

- [ ] Phase 1 foundation verified (conftest.py, factories, settings)
- [ ] `tests/api/` directory exists with `__init__.py`

*Phase 1 already created tests/api/__init__.py — Wave 0 is satisfied.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Password reset email delivery | TAUTH-04 | Requires email inbox access | Trigger reset, check if 200 returned (delivery unverifiable) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
