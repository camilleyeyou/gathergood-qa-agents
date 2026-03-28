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
| 01-01-01 | 01 | 1 | AUTH-01 | unit | `pytest apps/accounts/tests/test_auth.py::TestRegister` | W0 | pending |
| 01-01-02 | 01 | 1 | AUTH-02 | unit | `pytest apps/accounts/tests/test_auth.py::TestLogin` | W0 | pending |
| 01-01-03 | 01 | 1 | AUTH-03 | unit | `pytest apps/accounts/tests/test_auth.py::TestTokenRefresh` | W0 | pending |
| 01-01-04 | 01 | 1 | AUTH-04 | unit | `pytest apps/accounts/tests/test_auth.py::TestPasswordReset` | W0 | pending |
| 01-01-05 | 01 | 1 | AUTH-05 | unit | `pytest apps/accounts/tests/test_auth.py::TestPasswordResetConfirm` | W0 | pending |
| 01-01-06 | 01 | 1 | PROF-01 | unit | `pytest apps/accounts/tests/test_profile.py::TestGetProfile` | W0 | pending |
| 01-01-07 | 01 | 1 | PROF-02 | unit | `pytest apps/accounts/tests/test_profile.py::TestUpdateProfile` | W0 | pending |
| 01-02-01 | 02 | 1 | ORG-01 | unit | `pytest apps/organizations/tests/test_organizations.py::TestCreateOrganization` | W0 | pending |
| 01-02-02 | 02 | 1 | ORG-02 | unit | `pytest apps/organizations/tests/test_organizations.py::TestListOrganizations` | W0 | pending |
| 01-02-03 | 02 | 1 | ORG-03 | unit | `pytest apps/organizations/tests/test_organizations.py::TestUpdateOrganization` | W0 | pending |
| 01-02-04 | 02 | 1 | ORG-04 | unit | `pytest apps/organizations/tests/test_organizations.py::TestSlugGeneration` | W0 | pending |
| 01-03-01 | 03 | 1 | TEAM-01 | unit | `pytest apps/organizations/tests/test_team.py::TestInviteMember` | W0 | pending |
| 01-03-02 | 03 | 1 | TEAM-02 | unit | `pytest apps/organizations/tests/test_team.py::TestManagerCannotAssignOwner` | W0 | pending |
| 01-03-03 | 03 | 1 | TEAM-03 | unit | `pytest apps/organizations/tests/test_team.py::TestListMembers` | W0 | pending |
| 01-03-04 | 03 | 1 | TEAM-04 | unit | `pytest apps/organizations/tests/test_team.py::TestRemoveMember` | W0 | pending |
| 01-04-01 | 04 | 1 | VENU-01 | unit | `pytest apps/organizations/tests/test_venues.py::TestCreateVenue` | W0 | pending |
| 01-04-02 | 04 | 1 | VENU-02 | unit | `pytest apps/organizations/tests/test_venues.py::TestListVenues` | W0 | pending |
| 01-04-03 | 04 | 1 | VENU-03 | unit | `pytest apps/organizations/tests/test_venues.py::TestUpdateVenue` | W0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `backend/apps/accounts/tests/test_auth.py` — stubs for AUTH-01 through AUTH-05
- [ ] `backend/apps/accounts/tests/test_profile.py` — stubs for PROF-01, PROF-02
- [ ] `backend/apps/organizations/tests/test_organizations.py` — stubs for ORG-01 through ORG-04
- [ ] `backend/apps/organizations/tests/test_team.py` — stubs for TEAM-01 through TEAM-04
- [ ] `backend/apps/organizations/tests/test_venues.py` — stubs for VENU-01 through VENU-03
- [ ] `backend/conftest.py` — shared fixtures (test user, test org, API client)
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
