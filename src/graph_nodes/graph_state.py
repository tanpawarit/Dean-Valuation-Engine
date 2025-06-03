from typing import TypedDict, List, Optional

class PlanExecuteState(TypedDict):
    original_query: str
    plan: List[dict] # List of {"step_id": ..., "task_description": ..., "assigned_agent": ...}
    executed_steps: List[dict] # List of {"step_id": ..., "task_description": ..., "assigned_agent": ..., "output": ...}
    current_step_index: int # To keep track of which step in the plan to execute next
    error_message: Optional[str] # To store any error messages
    final_result: Optional[str] # To store the final summarized result
    