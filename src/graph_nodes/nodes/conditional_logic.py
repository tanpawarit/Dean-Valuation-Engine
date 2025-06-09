from src.graph_nodes.graph_state import PlanExecuteState
from src.utils.logger import get_logger

logger = get_logger(__name__)

def should_continue(state: PlanExecuteState) -> str:
    error_msg = state.get("error_message")
    if error_msg and isinstance(error_msg, str) and "Could not generate a valid plan" in error_msg:
        logger.error("Critical error: Could not generate a valid plan. Ending.")
        return "end_graph_error" # Special end node for critical planner failure
    if error_msg: # If an executor step failed
        logger.warning(f"Error encountered: {error_msg}. Considering replan or end.")
        # Simple strategy: end on error. Could add a "replan" branch here.
        return "end_graph_error" # Or a new node for error handling/replanning
    
    current_step_idx = state["current_step_index"]
    if current_step_idx >= len(state["plan"]):
        logger.info("Plan complete.")
        return "end_graph_success"
    return "executor_node"

def check_input_guardrail_result(state: PlanExecuteState) -> str:
    """Determines the next step after input guardrails have been applied."""
    if state.get("error_message"):
        logger.warning(f"Input guardrail failed: {state['error_message']}. Routing to error_node.")
        return "error_node"  # Route to error_node if guardrail validation set an error
    logger.info("Input guardrail passed. Routing to planner_node.")
    return "planner_node"  # Proceed to planner if no error