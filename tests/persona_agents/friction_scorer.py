"""Friction score calculator for persona UX evaluation.

Computes a 1-10 friction score based on:
  - Steps taken versus optimal path length (step ratio)
  - Confusion severity observations from the agent
  - Task completion (failure = automatic score 10)

Per D-05 specification.
"""


def calculate_friction_score(
    steps_taken: int,
    optimal_steps: int,
    confusion_points: list[dict],
    task_completed: bool,
) -> int:
    """Calculate a UX friction score for a completed (or abandoned) persona flow.

    Args:
        steps_taken: Number of browser interactions the agent made.
        optimal_steps: Minimum steps for a frictionless completion of this flow.
        confusion_points: List of confusion observation dicts, each with a
            'severity' key of 'low', 'medium', or 'high'.
        task_completed: Whether the persona successfully finished the task.

    Returns:
        Integer friction score in range [1, 10].
        Returns 10 immediately when task_completed is False.
        Returns 1 for a perfectly optimal, confusion-free completion.
    """
    # Task failure is the worst possible outcome.
    if not task_completed:
        return 10

    # --- Step ratio component (0.0 – 4.0 points) ---
    # ratio=1.0 means exactly optimal (0 pts), ratio>=4.0 means 4x slower (4 pts).
    ratio = min(steps_taken / max(optimal_steps, 1), 4.0)
    step_score = max(0.0, (ratio - 1.0) / 3.0 * 4.0)

    # --- Confusion component (0.0 – 4.0 points, capped) ---
    severity_weights: dict[str, float] = {"low": 0.5, "medium": 1.0, "high": 2.0}
    raw_confusion = sum(
        severity_weights.get(cp.get("severity", "low"), 0.5)
        for cp in confusion_points
    )
    confusion_score = min(raw_confusion, 4.0)

    # --- Final score ---
    # Minimum baseline of 1.0, add step and confusion penalties.
    raw = 1.0 + step_score + confusion_score
    return min(10, max(1, round(raw)))
