from typing import Literal
from src.graph_nodes.graph_state import PlanExecuteState
from src.utils.logger import get_logger

logger = get_logger(__name__)

def should_continue(state: PlanExecuteState) -> Literal["executor_node", "end_graph_success", "end_graph_error"]:
    """
    Determine whether to continue execution, end successfully, or end with error.
    
    Args:
        state: The current state of the graph execution
        
    Returns:
        String indicating the next step:
        - "executor_node": Continue to next execution step
        - "end_graph_success": Successfully complete the workflow
        - "end_graph_error": End with error state
    """
    
    plan = state.get("plan", [])
    current_step_index = state.get("current_step_index", 0)
    
    # Check if we have more steps to execute
    if current_step_index < len(plan):
        logger.info(f"Continue execution: {len(plan) - current_step_index} steps remaining")
        return "executor_node"
    
    # Check if we have any errors
    if state.get("error_message"):
        logger.error(f"Workflow ending with error: {state['error_message']}")
        return "end_graph_error"
    
    # Check if we have a final result (successful completion)
    if state.get("final_result"):
        logger.info("Workflow completed successfully with final result")
        return "end_graph_success"
    
    # Default case - if no more steps and no final result, consider it success
    logger.info("No more steps to execute, workflow completed")
    return "end_graph_success"