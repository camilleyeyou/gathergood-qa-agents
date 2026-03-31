"""Core agent loop — drives Claude Computer Use scenarios to completion."""
import time
from typing import Any

import anthropic

from tests.ai_agents.computer_use_backend import PlaywrightComputerBackend

# Tool definition for Claude Computer Use (November 2025 version)
COMPUTER_USE_TOOL = {
    "type": "computer_20251124",
    "name": "computer",
    "display_width_px": 1280,
    "display_height_px": 800,
}

COMPUTER_USE_BETA = "computer-use-2025-11-24"
MODEL = "claude-sonnet-4-6"
MAX_ITERATIONS = 20
MAX_INPUT_TOKENS = 1_000_000  # Hard cost cap per scenario (AIQA-10)


def run_agent_scenario(
    backend: PlaywrightComputerBackend,
    client: anthropic.Anthropic,
    goal: str,
    system_prompt: str | None = None,
    max_iterations: int = MAX_ITERATIONS,
    max_input_tokens: int = MAX_INPUT_TOKENS,
) -> dict[str, Any]:
    """Run a single AI QA scenario to completion.

    Takes an initial screenshot, sends the goal to Claude, and loops:
    screenshot -> Claude decides action -> execute action -> screenshot -> repeat.

    Stops when Claude stops issuing tool calls, the iteration cap is hit,
    or the input token cost cap is exceeded.

    Args:
        backend: PlaywrightComputerBackend wrapping the browser page.
        client: Anthropic API client.
        goal: Natural language description of what to verify.
        system_prompt: Optional system prompt for Claude.
        max_iterations: Maximum number of loop iterations.
        max_input_tokens: Hard input token budget — aborts if exceeded.

    Returns:
        Dict with keys: verdict, reasoning, steps, input_tokens, output_tokens.
    """
    # Start with an initial screenshot so Claude sees current state
    initial_screenshot = backend.screenshot()

    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": initial_screenshot,
                    },
                },
                {"type": "text", "text": goal},
            ],
        }
    ]

    iterations = 0
    final_text = ""
    total_input_tokens = 0
    total_output_tokens = 0

    while iterations < max_iterations:
        iterations += 1

        # Cost cap check (AIQA-10): abort before making another API call
        if total_input_tokens >= max_input_tokens:
            final_text = (
                f"INCONCLUSIVE\n\nCost cap reached: {total_input_tokens} input tokens "
                f"exceeded limit of {max_input_tokens}."
            )
            break

        kwargs: dict[str, Any] = {
            "model": MODEL,
            "max_tokens": 4096,
            "tools": [COMPUTER_USE_TOOL],
            "messages": messages,
            "betas": [COMPUTER_USE_BETA],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        # Retry with exponential backoff on rate limit errors
        for attempt in range(4):
            try:
                response = client.beta.messages.create(**kwargs)
                break
            except anthropic.RateLimitError:
                if attempt == 3:
                    return {
                        "verdict": "INCONCLUSIVE",
                        "reasoning": "Rate limited after 4 retries. Try again later.",
                        "steps": iterations,
                        "input_tokens": total_input_tokens,
                        "output_tokens": total_output_tokens,
                    }
                wait = 2 ** attempt * 15  # 15s, 30s, 60s, 120s
                time.sleep(wait)

        # Track token usage
        total_input_tokens += response.usage.input_tokens
        total_output_tokens += response.usage.output_tokens

        # Append assistant response to conversation history
        messages.append({"role": "assistant", "content": response.content})

        # Process response blocks: collect text, execute tool calls
        tool_results: list[dict[str, Any]] = []
        for block in response.content:
            if block.type == "text":
                final_text = block.text
            elif block.type == "tool_use" and block.name == "computer":
                action = block.input["action"]
                screenshot_b64 = backend.execute_action(action, block.input)

                result_content: list[dict[str, Any]] = []
                if screenshot_b64:
                    result_content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": screenshot_b64,
                        },
                    })

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_content,
                })

        # No tool calls means Claude is done
        if not tool_results:
            break

        messages.append({"role": "user", "content": tool_results})

    # Parse verdict from final text
    verdict = "INCONCLUSIVE"
    upper_text = final_text.upper()
    if "PASS" in upper_text:
        verdict = "PASS"
    elif "FAIL" in upper_text:
        verdict = "FAIL"

    return {
        "verdict": verdict,
        "reasoning": final_text,
        "steps": iterations,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
    }
