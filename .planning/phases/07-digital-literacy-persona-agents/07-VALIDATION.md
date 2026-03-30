---
phase: 7
slug: digital-literacy-persona-agents
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | `pytest.ini` / `conftest.py` |
| **Quick run command** | `pytest tests/persona_agents/ -x --tb=short` |
| **Full suite command** | `pytest tests/persona_agents/ --html=reports/persona_report.html` |
| **Estimated runtime** | ~300 seconds (5 personas x 3 flows, API-bound) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/persona_agents/ -x --tb=short`
- **After every plan wave:** Run `pytest tests/persona_agents/ --html=reports/persona_report.html`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds (excluding API calls)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | D-01, D-02 | unit | `python -c "from tests.persona_agents.personas import PERSONAS; assert len(PERSONAS) == 5"` | ❌ W0 | ⬜ pending |
| 07-01-02 | 01 | 1 | D-03 | unit | `pytest tests/persona_agents/test_persona_runner.py -x` | ❌ W0 | ⬜ pending |
| 07-02-01 | 02 | 2 | SC-1 | integration | `pytest tests/persona_agents/scenarios/ -x --tb=short` | ❌ W0 | ⬜ pending |
| 07-03-01 | 03 | 3 | D-04, D-05 | unit | `pytest tests/persona_agents/test_scoring.py -x` | ❌ W0 | ⬜ pending |
| 07-04-01 | 04 | 4 | D-06, SC-3 | integration | `python -m tests.persona_agents.report_generator --check` | ❌ W0 | ⬜ pending |
| 07-05-01 | 05 | 5 | D-09, SC-4 | integration | `pytest tests/persona_agents/test_api.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/persona_agents/__init__.py` — package init
- [ ] `tests/persona_agents/conftest.py` — shared fixtures extending ai_agents conftest

*Existing infrastructure covers framework install — pytest and playwright already installed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Persona prompts produce qualitatively different behaviors | D-02 | AI behavior is non-deterministic; cannot assert exact confusion patterns | Run 2 personas on same flow, visually compare screenshots and reports |
| Railway deployment serves API endpoint | SC-4 | Requires live Railway deployment | Deploy to Railway, POST to /run endpoint, verify 200 response |
| Vercel serves static HTML report | SC-4 | Requires live Vercel deployment | Deploy report HTML, verify accessible at URL |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
