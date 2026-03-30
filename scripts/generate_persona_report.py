"""CLI script to generate persona heatmap matrix report from JSON artifacts.

Usage:
    python scripts/generate_persona_report.py <run_id> [--report-dir reports/persona]

The script reads all .json files from reports/persona/<run_id>/ and renders
templates/persona_report.html.j2 into persona_matrix.html in the same directory.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

from jinja2 import Environment, FileSystemLoader

# Canonical persona and flow ordering (matches D-02 and D-07 in CONTEXT.md)
ALL_PERSONAS = [
    "tech_savvy",
    "casual",
    "low_literacy",
    "non_native",
    "impatient",
]

ALL_FLOWS = [
    "registration",
    "browsing",
    "checkout",
]


def _build_templates_dir() -> str:
    """Return the absolute path to the templates/ directory relative to this script."""
    # scripts/ is one level below project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "templates")


def generate_report(run_id: str, report_dir: str = "reports/persona") -> str:
    """Read JSON artifacts from report_dir/run_id/ and render the HTML heatmap matrix.

    Args:
        run_id: Identifier for the test run (maps to a subdirectory in report_dir).
        report_dir: Base directory containing run subdirectories. Defaults to
            "reports/persona" (relative to cwd, or pass an absolute path for tests).

    Returns:
        Absolute path to the generated persona_matrix.html file.
    """
    run_dir = os.path.join(report_dir, run_id)
    if not os.path.isdir(run_dir):
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    # Collect all .json files from the run directory
    results: dict[tuple[str, str], dict] = {}
    for filename in os.listdir(run_dir):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(run_dir, filename)
        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"Warning: could not read {filepath}: {exc}", file=sys.stderr)
            continue

        persona = data.get("persona")
        flow = data.get("flow")
        if persona and flow:
            results[(persona, flow)] = data

    # Determine ordered persona and flow lists from canonical ordering,
    # but fall back to sorted unique values for unknown entries.
    seen_personas = {k[0] for k in results}
    seen_flows = {k[1] for k in results}

    personas = [p for p in ALL_PERSONAS if p in seen_personas]
    personas += sorted(seen_personas - set(personas))

    flows = [f for f in ALL_FLOWS if f in seen_flows]
    flows += sorted(seen_flows - set(flows))

    # Render Jinja2 template
    templates_dir = _build_templates_dir()
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("persona_report.html.j2")
    html = template.render(
        run_id=run_id,
        personas=personas,
        flows=flows,
        results=results,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )

    # Write output
    output_path = os.path.join(run_dir, "persona_matrix.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return os.path.abspath(output_path)


def generate_report_from_results(
    results_list: list[dict],
    run_id: str,
    output_dir: str,
) -> str:
    """Render the HTML heatmap matrix from an in-memory list of result dicts.

    This is the convenience entry point for the FastAPI endpoint and pytest tests
    that already have results in memory and do not want to write intermediate JSON
    files first.

    Args:
        results_list: Flat list of result dicts. Each dict must have "persona" and
            "flow" string keys plus the standard output fields (friction_score,
            task_completed, confusion_points, suggestions, literacy_level, etc.).
        run_id: Identifier for the test run, embedded in the rendered report title.
        output_dir: Directory where persona_matrix.html will be written. Created if
            it does not exist.

    Returns:
        Absolute path to the generated persona_matrix.html file.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Convert flat list to (persona, flow) keyed dict
    results: dict[tuple[str, str], dict] = {}
    for item in results_list:
        persona = item.get("persona")
        flow = item.get("flow")
        if persona and flow:
            results[(persona, flow)] = item

    # Determine ordered persona and flow lists
    seen_personas = {k[0] for k in results}
    seen_flows = {k[1] for k in results}

    personas = [p for p in ALL_PERSONAS if p in seen_personas]
    personas += sorted(seen_personas - set(personas))

    flows = [f for f in ALL_FLOWS if f in seen_flows]
    flows += sorted(seen_flows - set(flows))

    # Render Jinja2 template
    templates_dir = _build_templates_dir()
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("persona_report.html.j2")
    html = template.render(
        run_id=run_id,
        personas=personas,
        flows=flows,
        results=results,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )

    # Write output
    output_path = os.path.join(output_dir, "persona_matrix.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return os.path.abspath(output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate persona usability heatmap matrix from JSON artifacts."
    )
    parser.add_argument(
        "run_id",
        help="Run ID — subdirectory name inside report_dir containing the JSON artifacts.",
    )
    parser.add_argument(
        "--report-dir",
        default="reports/persona",
        help="Base directory for persona run artifacts (default: reports/persona).",
    )
    args = parser.parse_args()

    try:
        output_path = generate_report(args.run_id, report_dir=args.report_dir)
        print(output_path)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
