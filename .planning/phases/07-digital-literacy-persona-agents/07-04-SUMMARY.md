---
phase: 07-digital-literacy-persona-agents
plan: "04"
subsystem: api
tags: [fastapi, railway, deployment, persona-agents]
dependency_graph:
  requires: ["07-01", "07-02"]
  provides: ["FastAPI persona sweep endpoint", "Railway Procfile", "env documentation"]
  affects: ["tests/persona_agents/", "scripts/generate_persona_report.py"]
tech_stack:
  added: ["fastapi", "uvicorn"]
  patterns: ["BackgroundTasks subprocess pattern", "in-memory job store"]
key_files:
  created:
    - api/__init__.py
    - api/persona_runner.py
    - Procfile
  modified:
    - .env.example
decisions:
  - "Subprocess pytest invocation avoids Playwright browser lifecycle conflicts in FastAPI event loop (per RESEARCH Pitfall 4)"
  - "In-memory job store is sufficient for trigger use — resets on process restart, stateless polling acceptable"
  - "RAILWAY_URL added to .env.example for remote sweep triggering after Railway deployment"
metrics:
  duration: "~2 minutes"
  completed: "2026-03-30"
  tasks_completed: 2
  files_created: 3
  files_modified: 1
---

# Phase 7 Plan 4: FastAPI Deployment Endpoint Summary

FastAPI persona runner with /sweep, /sweep/{job_id}, and /health endpoints deployed via Procfile to Railway; runs pytest persona tests as subprocesses for browser lifecycle isolation.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Create FastAPI persona runner app | 9a71ab5 | api/__init__.py, api/persona_runner.py |
| 2 | Create deployment configuration files | f5367e7 | Procfile, .env.example |

## What Was Built

### api/persona_runner.py

FastAPI application with three endpoints:

- `POST /sweep` — accepts `SweepRequest` with optional `personas` and `flows` filter lists, generates a UUID job_id, stores job state in the in-memory `sweeps` dict, and enqueues `_run_sweep` as a BackgroundTask. Returns `{"job_id": ..., "status": "running"}`.
- `GET /sweep/{job_id}` — polls job state; returns status (running/completed/failed), result_path (path to persona_matrix.html when done), started_at, completed_at, error. Returns 404 if job_id unknown.
- `GET /health` — liveness probe; returns `{"status": "ok", "anthropic_key_configured": <bool>}`.

The `_run_sweep` background function builds a `pytest tests/persona_agents/ -v --tb=short` command, optionally extending with `-k` expressions for persona/flow filtering. It uses `subprocess.run` with a 1800-second timeout. On completion it scans `reports/persona/` for the latest `run_*` subdirectory and records the `persona_matrix.html` path.

### Procfile

```
web: uvicorn api.persona_runner:app --host 0.0.0.0 --port ${PORT:-8000}
```

Railway auto-injects the `PORT` variable; the `:-8000` fallback allows local testing.

### .env.example

Updated with all required and optional variables, with comments explaining each:
- `BASE_URL` — GatherGood frontend
- `API_URL` — GatherGood backend
- `STRIPE_TEST_KEY` — optional, skips paid checkout tests if absent
- `ANTHROPIC_API_KEY` — required for AI agent and persona agent tests
- `RAILWAY_URL` — new, set after Railway deployment for remote sweep triggering

Previous placeholder value `sk-ant-YOUR_KEY_HERE` replaced with empty value to avoid confusion.

## Verification

```
python -c "from fastapi.testclient import TestClient; from api.persona_runner import app; c = TestClient(app); assert c.get('/health').status_code == 200"
cat Procfile  # shows uvicorn command
grep RAILWAY_URL .env.example  # shows new variable
```

All checks passed.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — the FastAPI endpoints are fully functional. The `result_path` field will be `None` until a sweep completes and generates a report, which is the correct initial state.

## User Setup Required

The following steps require manual action (Railway/Vercel accounts):

1. **Railway:** Create project, connect to this repo, set environment variables (`ANTHROPIC_API_KEY`, `BASE_URL`, `API_URL`). Railway will auto-detect the Procfile and deploy.
2. **Vercel:** Confirm the `reports/` directory is served as static files for HTML report access.

These are documented in the plan's `user_setup` section and not blockers for local development.

## Self-Check: PASSED

- api/__init__.py: exists
- api/persona_runner.py: exists, contains `app = FastAPI(`, `/sweep`, `/sweep/{job_id}`, `/health`
- Procfile: exists, contains uvicorn command
- .env.example: updated with all 5 required variables
- Commits 9a71ab5 and f5367e7: both verified in git log
