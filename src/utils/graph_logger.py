import json
import datetime
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Define the log file path at the project root
LOG_FILE_PATH = Path("graph_execution_details.log")

def generate_run_id() -> str:
    """Generates a unique run ID."""
    return uuid.uuid4().hex

def _write_log(log_entry: Dict[str, Any]) -> None:
    """Helper function to write a log entry to the file."""
    try:
        # Create logs directory if it doesn't exist (optional, for now logs at root)
        # LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, indent=2, ensure_ascii=False, default=str) + "\n")
    except Exception as e:
        # Fallback to print if logging fails
        logger.error(f"Error writing to log file {LOG_FILE_PATH}: {e}")
        logger.error(f"Log entry was: {log_entry}")

def log_graph_start(run_id: str, initial_state: Dict[str, Any]) -> None:
    """Logs the start of a graph execution."""
    log_entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "run_id": run_id,
        "event_type": "graph_start",
        "initial_state": initial_state,
    }
    _write_log(log_entry)

def log_node_execution(
    run_id: str,
    node_name: str,
    state_before: Dict[str, Any],
    state_after: Dict[str, Any],
    output: Optional[Any] = None,
    error: Optional[Any] = None,
) -> None:
    """
    Logs the state of a node before and after execution, along with its output or error.
    """
    log_entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "run_id": run_id,
        "node_name": node_name,
        "event_type": "node_execution",
        "state_before": state_before,
        "state_after": state_after,
        "output": output,
        "error": str(error) if error else None,
    }
    _write_log(log_entry)

def log_graph_end(
    run_id: str,
    final_state: Dict[str, Any],
    result: Optional[Any] = None,
    error: Optional[Any] = None,
) -> None:
    """Logs the end of a graph execution."""
    log_entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "run_id": run_id,
        "event_type": "graph_end",
        "final_state": final_state,
        "result": result,
        "error": str(error) if error else None,
    }
    _write_log(log_entry)
