from langgraph.graph import StateGraph, END
from src.graph_nodes.graph_state import PlanExecuteState 
from src.graph_nodes.nodes.executor_logic import executor_node
from src.graph_nodes.nodes.planner_logic import planner_node
from src.graph_nodes.nodes.conditional_logic import should_continue
from src.graph_nodes.nodes.state_handlers import handle_error_node, handle_success_node
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

def build_graph():
    workflow: StateGraph = StateGraph(PlanExecuteState)

    workflow.add_node("input_guardrail", apply_input_guardrails)
    workflow.add_node("planner_node", planner_node)
    workflow.add_node("executor_node", executor_node)
    workflow.add_node("error_node", handle_error_node)
    workflow.add_node("success_node", handle_success_node)

    # Define the entry point - apply guardrails to input first
    workflow.set_entry_point("input_guardrail")
    
    # Add edge from input guardrail to planner
    workflow.add_edge("input_guardrail", "planner_node")

    # Define transitions
    workflow.add_edge("planner_node", "executor_node") # Always try to execute after planning

    workflow.add_conditional_edges(
        "executor_node",
        should_continue,
        {
            "executor_node": "executor_node",  # Loop back to execute next step
            "end_graph_success": "success_node", # Go directly to success node
            "end_graph_error": "error_node"   # Go to error node if critical error
        }
    )
    workflow.add_edge("error_node", END)
    workflow.add_edge("success_node", END)

    # Compile the graph
    app = workflow.compile()
    return app