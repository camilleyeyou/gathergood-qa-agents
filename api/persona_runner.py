"""FastAPI app for triggering digital literacy persona sweeps remotely.

Endpoints:
    POST /sweep       — Start a background persona sweep; returns job_id.
    GET  /sweep/{id}  — Poll job status and result path when done.
    GET  /health      — Liveness check; confirms ANTHROPIC_API_KEY is configured.

The sweep runs pytest (tests/persona_agents/) in a subprocess to avoid
Playwright browser lifecycle conflicts inside the FastAPI event loop.
"""
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

from settings import Settings

app = FastAPI(
    title="Persona Agent Runner",
    description="Triggers digital literacy persona sweeps against the GatherGood platform",
)

_settings = Settings()

# ---------------------------------------------------------------------------
# In-memory job store (resets on process restart; sufficient for trigger use).
# ---------------------------------------------------------------------------
sweeps: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------


class SweepRequest(BaseModel):
    """Optional filters for the persona sweep.

    Attributes:
        personas: List of persona names to include (e.g. ['TECH_SAVVY', 'CASUAL']).
            None means all 5 personas.
        flows: List of flow names to include (e.g. ['registration', 'browsing']).
            None means all 3 flows.
    """

    personas: list[str] | None = None
    flows: list[str] | None = None


# ---------------------------------------------------------------------------
# Background task
# ---------------------------------------------------------------------------


def _run_sweep(job_id: str, personas: list[str] | None, flows: list[str] | None) -> None:
    """Run pytest against tests/persona_agents/ in a subprocess.

    Uses subprocess rather than direct import to avoid Playwright browser
    lifecycle issues inside the FastAPI event loop (RESEARCH Pitfall 4).

    Args:
        job_id: Key in the ``sweeps`` store to update with progress/results.
        personas: Optional list of persona name substrings for pytest -k filtering.
        flows: Optional list of flow name substrings for pytest -k filtering.
    """
    try:
        cmd = [sys.executable, "-m", "pytest", "tests/persona_agents/", "-v", "--tb=short"]

        if personas:
            k_expr = " or ".join(personas)
            if flows:
                flow_expr = " or ".join(flows)
                k_expr = f"({k_expr}) and ({flow_expr})"
            cmd.extend(["-k", k_expr])
        elif flows:
            cmd.extend(["-k", " or ".join(flows)])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800,  # 30-minute timeout
        )

        sweeps[job_id]["status"] = "completed" if result.returncode == 0 else "failed"
        sweeps[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
        sweeps[job_id]["error"] = result.stderr if result.returncode != 0 else None

        # Find the latest run directory in reports/persona/
        report_dir = "reports/persona"
        if os.path.exists(report_dir):
            runs = sorted([d for d in os.listdir(report_dir) if d.startswith("run_")])
            if runs:
                sweeps[job_id]["result_path"] = os.path.join(
                    report_dir, runs[-1], "persona_matrix.html"
                )

    except subprocess.TimeoutExpired:
        sweeps[job_id]["status"] = "failed"
        sweeps[job_id]["error"] = "Sweep timed out after 30 minutes"
        sweeps[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
    except Exception as e:
        sweeps[job_id]["status"] = "failed"
        sweeps[job_id]["error"] = str(e)
        sweeps[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post("/sweep")
def start_sweep(request: SweepRequest, background_tasks: BackgroundTasks) -> dict:
    """Start a background persona sweep.

    Returns:
        JSON with ``job_id`` and initial ``status`` of "running".
    """
    job_id = str(uuid.uuid4())
    sweeps[job_id] = {
        "status": "running",
        "result_path": None,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "error": None,
    }
    background_tasks.add_task(_run_sweep, job_id, request.personas, request.flows)
    return {"job_id": job_id, "status": "running"}


@app.get("/sweep/{job_id}")
def get_sweep_status(job_id: str) -> dict:
    """Poll the status of a sweep job.

    Args:
        job_id: UUID returned by POST /sweep.

    Returns:
        Job record with status, result_path, started_at, completed_at, error.

    Raises:
        HTTPException 404: If job_id is not found in the in-memory store.
    """
    if job_id not in sweeps:
        raise HTTPException(status_code=404, detail="Job not found")
    return sweeps[job_id]


@app.get("/health")
def health() -> dict:
    """Liveness check.

    Returns:
        JSON with ``status`` of "ok" and ``anthropic_key_configured`` boolean.
    """
    return {
        "status": "ok",
        "anthropic_key_configured": bool(_settings.ANTHROPIC_API_KEY),
    }
