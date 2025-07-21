from src.graph_nodes.graph_state import PlanExecuteState
from src.agents.registry import planner_agent
from src.utils.logger import get_logger

logger = get_logger(__name__)

def planner_node(state: PlanExecuteState) -> PlanExecuteState:
    logger.info("--- PLANNER ---")
    query: str = state["original_query"]
    plan = planner_agent().generate_plan(query)
    logger.info(f"Generated Plan: {plan}")
    
    # Create new state with plan
    new_state = {
        "original_query": query,
        "plan": plan,
        "current_step_index": 0,
        "executed_steps": [],
        "error_message": None,
        "final_result": None
    }
    
    # Save checkpoint if checkpoint manager is available
    try:
        from src.graph_nodes.graph_builder import get_checkpoint_manager
        checkpoint_manager = get_checkpoint_manager()
        if checkpoint_manager:
            success = checkpoint_manager.save_checkpoint(new_state, "planner")
            if success:
                logger.debug("Planner state checkpointed")
            else:
                logger.warning("Failed to save planner checkpoint")
    except ImportError:
        pass  # Checkpointing not available
    except Exception as e:
        logger.warning(f"Checkpoint error in planner: {e}")
    
    return new_state