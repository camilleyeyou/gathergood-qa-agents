"""Persona-aware wrapper around run_agent_scenario().

Combines a persona's system prompt with structured output instructions, runs the
agent loop, parses the JSON result block from Claude's final message, and
returns a unified result dict ready for artifact_writer.save_persona_result().
"""
import json
import re
from typing import Any

import anthropic

from tests.ai_agents.agent_runner import run_agent_scenario
from tests.ai_agents.computer_use_backend import PlaywrightComputerBackend
from tests.persona_agents.friction_scorer import calculate_friction_score
from tests.persona_agents.personas import Persona

# ---------------------------------------------------------------------------
# Output schema instructions appended to every persona system prompt.
# ---------------------------------------------------------------------------
PERSONA_OUTPUT_INSTRUCTIONS = """
At the end of my session — whether I complete the task or give up — I MUST output a
structured JSON block in the following exact format, delimited by triple-backtick json
markers, immediately before my final PASS/FAIL/INCONCLUSIVE verdict line:

```json
{
  "task_completed": <true|false>,
  "steps_taken": <integer number of browser interactions>,
  "confusion_points": [
    {
      "step": <integer step number>,
      "description": "<what confused me>",
      "severity": "<low|medium|high>"
    }
  ],
  "suggestions": [
    "<specific UX improvement I would suggest>"
  ]
}
```

IMPORTANT: My final message MUST include the ```json block before stopping.
I will always output this block even if I complete the task perfectly — in that case
confusion_points will be an empty list.
"""


def run_persona_scenario(
    backend: PlaywrightComputerBackend,
    client: anthropic.Anthropic,
    persona: Persona,
    flow_goal: str,
    optimal_steps: int,
    max_iterations: int = 25,
) -> dict[str, Any]:
    """Run a persona agent scenario and return a structured result dict.

    Builds a combined system prompt from the persona's behavioral description,
    constraints, and structured output instructions, then delegates to
    run_agent_scenario(). Post-processes the final text to extract the JSON
    block and calculate a friction score.

    Args:
        backend: PlaywrightComputerBackend wrapping the test browser page.
        client: Anthropic API client.
        persona: Persona dataclass instance.
        flow_goal: Natural language task description for this flow.
        optimal_steps: Minimum steps for a frictionless completion of this flow.
        max_iterations: Maximum agent loop iterations (default 25).

    Returns:
        Dict with keys:
            persona (str), literacy_level (int), verdict (str),
            task_completed (bool), friction_score (int), steps_taken (int),
            optimal_steps (int), confusion_points (list), suggestions (list),
            tokens_used (int), reasoning (str).
    """
    # Build the combined system prompt.
    constraints_block = "\n".join(f"- {c}" for c in persona.constraints)
    system_prompt = (
        persona.system_prompt
        + "\n\nBehavioral constraints:\n"
        + constraints_block
        + "\n\n"
        + PERSONA_OUTPUT_INSTRUCTIONS
    )

    # Run the core agent loop.
    raw_result = run_agent_scenario(
        backend=backend,
        client=client,
        goal=flow_goal,
        system_prompt=system_prompt,
        max_iterations=max_iterations,
    )

    # Parse the structured JSON block from Claude's final text.
    parsed = _parse_structured_output(raw_result.get("reasoning", ""))

    task_completed: bool = bool(parsed.get("task_completed", False))
    steps_taken: int = int(parsed.get("steps_taken", raw_result.get("steps", 0)))
    confusion_points: list[dict] = parsed.get("confusion_points", [])
    suggestions: list[str] = parsed.get("suggestions", [])

    friction_score = calculate_friction_score(
        steps_taken=steps_taken,
        optimal_steps=optimal_steps,
        confusion_points=confusion_points,
        task_completed=task_completed,
    )

    tokens_used = raw_result.get("input_tokens", 0) + raw_result.get("output_tokens", 0)

    return {
        "persona": persona.name,
        "literacy_level": persona.literacy_level,
        "verdict": raw_result.get("verdict", "INCONCLUSIVE"),
        "task_completed": task_completed,
        "friction_score": friction_score,
        "steps_taken": steps_taken,
        "optimal_steps": optimal_steps,
        "confusion_points": confusion_points,
        "suggestions": suggestions,
        "tokens_used": tokens_used,
        "reasoning": raw_result.get("reasoning", ""),
    }


def _parse_structured_output(text: str) -> dict:
    """Extract the JSON block from Claude's final response text.

    Searches for a triple-backtick json ... triple-backtick block in ``text``
    and returns the parsed dict. Returns an empty dict on any parse failure.

    Args:
        text: The raw reasoning/text output from run_agent_scenario().

    Returns:
        Parsed JSON dict, or {} if no valid block was found.
    """
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(1))
    except (json.JSONDecodeError, ValueError):
        return {}
