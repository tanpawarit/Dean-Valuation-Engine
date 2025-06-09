from src.graph_nodes.graph_state import PlanExecuteState
from src.guardrails.guardrail_manager import GuardrailManager
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Define a function to apply input guardrails only
def apply_input_guardrails(state: PlanExecuteState) -> PlanExecuteState:
    guardrail_mgr = GuardrailManager()
    logger.info("Applying input guardrails")
    
    # Process only the original_query through guardrails
    if "original_query" in state and state["original_query"]:
        original_query = state["original_query"]
        is_safe, processed_query, error_message = guardrail_mgr.validate_input(original_query)
        print(f"Input guardrails result: {is_safe}, processed_query: {processed_query}, error_message: {error_message}")
        # Create a new state with the processed query
        # Start with empty state with required fields
        result: PlanExecuteState = {
            "original_query": processed_query,
            "plan": state.get("plan", []),
            "executed_steps": state.get("executed_steps", []),
            "current_step_index": state.get("current_step_index", 0),
            "error_message": None,
            "final_result": state.get("final_result", None)
        }
        
        # If input is unsafe, set error message
        if not is_safe and error_message:
            result["error_message"] = error_message
            
        return result
    
    # If no original_query, return state unchanged
    return state
