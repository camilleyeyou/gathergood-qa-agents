"""JSON artifact writer for persona UX evaluation results.

Saves per-persona-per-flow result dicts as JSON files under
reports/persona/<run_id>/ so each run has its own isolated directory.
"""
import json
import os


def save_persona_result(result: dict, run_id: str) -> str:
    """Save a persona scenario result as a JSON file.

    Creates the directory ``reports/persona/<run_id>/`` if it does not exist,
    then writes the result dict as formatted JSON.

    Args:
        result: Result dict from run_persona_scenario(). Expected keys include
            'persona' (str) and 'flow' (str) for building the filename.
        run_id: Unique identifier for this run (e.g. a timestamp string).

    Returns:
        Absolute path to the written JSON file.
    """
    output_dir = os.path.join("reports", "persona", run_id)
    os.makedirs(output_dir, exist_ok=True)

    persona_name = result.get("persona", "unknown")
    flow_name = result.get("flow", "unknown")
    filename = f"{persona_name}_{flow_name}.json"
    file_path = os.path.join(output_dir, filename)

    with open(file_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    return os.path.abspath(file_path)
