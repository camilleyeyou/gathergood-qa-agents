---
phase: 1
slug: foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-28
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x + httpx 0.28.x + playwright 1.58.x |
| **Config file** | `pytest.ini` (created in this phase) |
| **Quick run command** | `pytest tests/ -x --tb=short` |
| **Full suite command** | `pytest tests/ -v --tb=long` |
| **Estimated runtime** | ~15 seconds (foundation smoke tests only) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x --tb=short`
- **After every plan wave:** Run `pytest tests/ -v --tb=long`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | INFR-01 | smoke | `pytest tests/test_smoke.py -v` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | INFR-02 | unit | `python -c "from config.settings import Settings"` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 2 | INFR-03 | integration | `pytest tests/test_auth_fixture.py -v` | ❌ W0 | ⬜ pending |
| 01-04-01 | 04 | 2 | INFR-04 | unit | `pytest tests/test_factories.py -v` | ❌ W0 | ⬜ pending |
| 01-05-01 | 05 | 3 | INFR-05 | integration | `pytest tests/test_teardown.py -v` | ❌ W0 | ⬜ pending |
| 01-06-01 | 06 | 3 | INFR-06 | unit | `pytest tests/test_markers.py -v` | ❌ W0 | ⬜ pending |
| 01-07-01 | 07 | 3 | INFR-07 | smoke | `pytest --co -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `requirements.txt` — install pytest, httpx, playwright, pydantic-settings, pytest-html, faker
- [ ] `pytest.ini` — configure test discovery, markers, and plugins
- [ ] `tests/conftest.py` — shared fixtures skeleton

*This phase IS the foundation — Wave 0 and Phase 1 overlap significantly.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| JWT token refresh before expiry | INFR-03 | Requires waiting for near-expiry timing | Run suite, check logs for refresh message before 401 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
