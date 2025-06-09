from langgraph.graph import StateGraph, END
from src.graph_nodes.graph_state import PlanExecuteState 
from src.graph_nodes.nodes.executor_logic import executor_node
from src.graph_nodes.nodes.planner_logic import planner_node
from src.graph_nodes.nodes.conditional_logic import should_continue, check_input_guardrail_result
from src.graph_nodes.nodes.state_handlers import handle_error_node, handle_success_node 
from src.graph_nodes.nodes.guard_logic import apply_input_guardrails
from src.utils.logger import get_logger

logger = get_logger(__name__)
  

def build_graph():
    workflow: StateGraph = StateGraph(PlanExecuteState)

    workflow.add_node("input_guardrail", apply_input_guardrails)
    workflow.add_node("planner_node", planner_node)
    workflow.add_node("executor_node", executor_node)
    workflow.add_node("error_node", handle_error_node)
    workflow.add_node("success_node", handle_success_node)

    # Define the entry point - apply guardrails to input first
    workflow.set_entry_point("input_guardrail")
    
    # Define conditional routing after input_guardrail
    workflow.add_conditional_edges(
        "input_guardrail",
        check_input_guardrail_result,
        {
            "error_node": "error_node",
            "planner_node": "planner_node"
        }
    )

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