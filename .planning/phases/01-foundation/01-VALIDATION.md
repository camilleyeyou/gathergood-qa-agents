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
| **Framework** | pytest 8.x (backend) / vitest (frontend) |
| **Config file** | backend/pytest.ini / frontend/vitest.config.ts (Wave 0 installs) |
| **Quick run command** | `cd backend && python -m pytest --tb=short -q` |
| **Full suite command** | `cd backend && python -m pytest -v && cd ../frontend && npx vitest run` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest --tb=short -q`
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | AUTH-01 | unit | `pytest tests/test_auth.py::test_register` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | AUTH-02 | unit | `pytest tests/test_auth.py::test_login` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | AUTH-03 | unit | `pytest tests/test_auth.py::test_token_refresh` | ❌ W0 | ⬜ pending |
| 01-01-04 | 01 | 1 | AUTH-04 | unit | `pytest tests/test_auth.py::test_forgot_password` | ❌ W0 | ⬜ pending |
| 01-01-05 | 01 | 1 | AUTH-05 | unit | `pytest tests/test_auth.py::test_reset_password` | ❌ W0 | ⬜ pending |
| 01-01-06 | 01 | 1 | PROF-01 | unit | `pytest tests/test_auth.py::test_get_profile` | ❌ W0 | ⬜ pending |
| 01-01-07 | 01 | 1 | PROF-02 | unit | `pytest tests/test_auth.py::test_update_profile` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | ORG-01 | unit | `pytest tests/test_orgs.py::test_create_org` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | ORG-02 | unit | `pytest tests/test_orgs.py::test_list_orgs` | ❌ W0 | ⬜ pending |
| 01-02-03 | 02 | 1 | ORG-03 | unit | `pytest tests/test_orgs.py::test_update_org` | ❌ W0 | ⬜ pending |
| 01-02-04 | 02 | 1 | ORG-04 | unit | `pytest tests/test_orgs.py::test_slug_generation` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 1 | TEAM-01 | unit | `pytest tests/test_team.py::test_invite_member` | ❌ W0 | ⬜ pending |
| 01-03-02 | 03 | 1 | TEAM-02 | unit | `pytest tests/test_team.py::test_manager_cannot_assign_owner` | ❌ W0 | ⬜ pending |
| 01-03-03 | 03 | 1 | TEAM-03 | unit | `pytest tests/test_team.py::test_list_members` | ❌ W0 | ⬜ pending |
| 01-03-04 | 03 | 1 | TEAM-04 | unit | `pytest tests/test_team.py::test_owner_remove_member` | ❌ W0 | ⬜ pending |
| 01-04-01 | 04 | 1 | VENU-01 | unit | `pytest tests/test_venues.py::test_create_venue` | ❌ W0 | ⬜ pending |
| 01-04-02 | 04 | 1 | VENU-02 | unit | `pytest tests/test_venues.py::test_list_venues` | ❌ W0 | ⬜ pending |
| 01-04-03 | 04 | 1 | VENU-03 | unit | `pytest tests/test_venues.py::test_update_venue` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_auth.py` — stubs for AUTH-01 through AUTH-05, PROF-01, PROF-02
- [ ] `backend/tests/test_orgs.py` — stubs for ORG-01 through ORG-04
- [ ] `backend/tests/test_team.py` — stubs for TEAM-01 through TEAM-04
- [ ] `backend/tests/test_venues.py` — stubs for VENU-01 through VENU-03
- [ ] `backend/tests/conftest.py` — shared fixtures (test user, test org, API client)
- [ ] `pytest` — install if not in requirements.txt

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| JWT persists across browser refresh | AUTH-02 | Requires browser session state | Log in, close tab, reopen — verify still authenticated |
| Password reset email received | AUTH-04 | Requires email delivery | Trigger reset, check inbox/console for email content |
| Mobile hamburger menu | FEND-03 (Phase 2) | Not in Phase 1 scope | N/A |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
