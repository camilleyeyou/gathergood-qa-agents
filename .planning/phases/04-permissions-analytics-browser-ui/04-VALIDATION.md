---
phase: 4
slug: permissions-analytics-browser-ui
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-28
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x + httpx 0.28.x + playwright 1.58.x |
| **Config file** | `pytest.ini` (exists from Phase 1) |
| **Quick run command** | `pytest tests/api/{module_just_written} -x --tb=short` |
| **Full suite command** | `pytest tests/api/ tests/ui/ -v --tb=long` |
| **Estimated runtime** | ~60 seconds (API tests ~30s, browser tests ~30s) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/api/{module_just_written} -x --tb=short`
- **After every plan wave:** Run `pytest tests/api/ tests/ui/ -v --tb=long`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Wave 0 Requirements

- [ ] `tests/ui/` directory with `__init__.py`
- [ ] `tests/ui/conftest.py` with Playwright fixtures

*Phase 1 already installed Playwright. Browser tests need a new directory structure.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Bulk email actual delivery | TEMAL-03 | Requires email inbox access | Trigger send, verify 200/400 returned |
| Touch target sizing | TFEND-08 | Requires visual measurement | Run Playwright, measure element dimensions programmatically |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
