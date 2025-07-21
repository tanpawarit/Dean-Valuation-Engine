from langgraph.graph import END, StateGraph

from src.graph_nodes.graph_state import PlanExecuteState
from src.graph_nodes.nodes.conditional_logic import should_continue
from src.graph_nodes.nodes.executor_logic import executor_node
from src.graph_nodes.nodes.planner_logic import planner_node
from src.graph_nodes.nodes.state_handlers import handle_error_node, handle_success_node
from src.utils.checkpoint_manager import CheckpointManager
from src.utils.checkpoint_registry import get_checkpoint_manager, set_checkpoint_manager
from src.utils.logger import get_logger
from src.utils.recovery_handler import RecoveryHandler

logger = get_logger(__name__)


def build_graph(enable_checkpointing: bool = False, checkpoint_manager: CheckpointManager | None = None):
    """
    Build the LangGraph workflow with optional checkpointing support.

    Args:
        enable_checkpointing: Whether to enable state checkpointing
        checkpoint_manager: Optional CheckpointManager instance

    Returns:
        Compiled LangGraph application
    """
    workflow: StateGraph[PlanExecuteState] = StateGraph(PlanExecuteState)

    # Configure checkpoint manager if requested
    if enable_checkpointing:
        if checkpoint_manager:
            set_checkpoint_manager(checkpoint_manager)
        elif not get_checkpoint_manager():
            # Create default checkpoint manager
            default_manager = CheckpointManager()
            set_checkpoint_manager(default_manager)
            logger.info("Created default checkpoint manager")

    _ = workflow.add_node("planner_node", planner_node)
    _ = workflow.add_node("executor_node", executor_node)
    _ = workflow.add_node("error_node", handle_error_node)
    _ = workflow.add_node("success_node", handle_success_node)

    # Define the entry point - start with planner
    _ = workflow.set_entry_point("planner_node")

    # Define transitions
    _ = workflow.add_edge("planner_node", "executor_node")  # Always try to execute after planning

    _ = workflow.add_conditional_edges(
        "executor_node",
        should_continue,
        {
            "executor_node": "executor_node",  # Loop back to execute next step
            "end_graph_success": "success_node",  # Go directly to success node
            "end_graph_error": "error_node",  # Go to error node if critical error
        },
    )
    _ = workflow.add_edge("error_node", END)
    _ = workflow.add_edge("success_node", END)

    # Compile the graph
    app = workflow.compile()

    if enable_checkpointing:
        logger.info("Graph built with checkpointing enabled")

    return app


def build_graph_with_recovery(run_id: str | None = None) -> tuple[object, object]:
    """
    Build graph with recovery capabilities.

    Args:
        run_id: Optional run ID for recovery

    Returns:
        Tuple of (app, initial_state) where initial_state is recovered state or None
    """
    # Create or get checkpoint manager
    manager = CheckpointManager(run_id=run_id) if run_id else CheckpointManager()
    recovery = RecoveryHandler(manager)

    # Build graph with checkpointing
    app = build_graph(enable_checkpointing=True, checkpoint_manager=manager)

    # Try to recover state
    initial_state = None
    if recovery.can_recover():
        logger.info("Recovery possible - checking options")
        recovery_info = recovery.get_recovery_info()

        if recovery_info:
            logger.info(f"Recovery info: {recovery_info}")

            # Auto-recover if possible
            initial_state = recovery.auto_recover()
            if initial_state:
                logger.info("Successfully recovered initial state")
            else:
                logger.warning("Auto-recovery failed")
    else:
        logger.info("No recovery state available - starting fresh")

    return app, initial_state
