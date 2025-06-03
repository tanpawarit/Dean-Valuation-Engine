from src.graph_nodes.graph_state import PlanExecuteState
from src.agents.registry import planner_agent

def planner_node(state: PlanExecuteState) -> PlanExecuteState:
    print("--- PLANNER ---")
    query: str = state["original_query"]
    plan = planner_agent.generate_plan(query)
    print(f"Generated Plan: {plan}")
    return {
        "plan": plan,
        "current_step_index": 0,
        "executed_steps": [],
        "error_message": None,
        "final_result": None
    }