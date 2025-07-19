from src.graph_nodes.graph_state import PlanExecuteState
from src.agents.registry import planner_agent
from src.utils.logger import get_logger

logger = get_logger(__name__)

def planner_node(state: PlanExecuteState) -> PlanExecuteState:
    logger.info("--- PLANNER ---")
    query: str = state["original_query"]
    plan = planner_agent().generate_plan(query)
    logger.info(f"Generated Plan: {plan}")
    return {
        "original_query": query,
        "plan": plan,
        "current_step_index": 0,
        "executed_steps": [],
        "error_message": None,
        "final_result": None
    }