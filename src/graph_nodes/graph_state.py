from typing import TypedDict


class PlanStep(TypedDict):
    """Type definition for a plan step."""

    step_id: str
    task_description: str
    assigned_agent: str


class ExecutedStep(TypedDict):
    """Type definition for an executed step."""

    step_id: str
    task_description: str
    assigned_agent: str
    output: str


class PlanExecuteState(TypedDict):
    original_query: str
    plan: list[PlanStep]
    executed_steps: list[ExecutedStep]
    current_step_index: int  # To keep track of which step in the plan to execute next
    error_message: str | None  # To store any error messages
    final_result: str | None  # To store the final summarized result
