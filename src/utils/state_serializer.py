import json
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

from src.graph_nodes.graph_state import PlanExecuteState
from src.utils.logger import get_logger

logger = get_logger(__name__)


class StateSerializer:
    """JSON serializer/deserializer for PlanExecuteState with proper type handling."""
    
    @staticmethod
    def serialize_state(state: PlanExecuteState) -> Dict[str, Any]:
        """Convert PlanExecuteState to JSON-serializable dictionary."""
        try:
            serialized = {
                "original_query": state.get("original_query", ""),
                "plan": state.get("plan", []),
                "executed_steps": state.get("executed_steps", []),
                "current_step_index": state.get("current_step_index", 0),
                "error_message": state.get("error_message"),
                "final_result": state.get("final_result"),
                "timestamp": datetime.now().isoformat(),
                "_metadata": {
                    "version": "1.0",
                    "serializer": "StateSerializer"
                }
            }
            return serialized
        except Exception as e:
            logger.error(f"Failed to serialize state: {e}")
            raise

    @staticmethod
    def deserialize_state(data: Dict[str, Any]) -> PlanExecuteState:
        """Convert JSON dictionary back to PlanExecuteState."""
        try:
            state: PlanExecuteState = {
                "original_query": data.get("original_query", ""),
                "plan": data.get("plan", []),
                "executed_steps": data.get("executed_steps", []),
                "current_step_index": data.get("current_step_index", 0),
                "error_message": data.get("error_message"),
                "final_result": data.get("final_result")
            }
            return state
        except Exception as e:
            logger.error(f"Failed to deserialize state: {e}")
            raise

    @staticmethod
    def save_to_file(state: PlanExecuteState, file_path: Path) -> bool:
        """Save state to JSON file."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            serialized = StateSerializer.serialize_state(state)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(serialized, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"State saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save state to {file_path}: {e}")
            return False

    @staticmethod
    def load_from_file(file_path: Path) -> Optional[PlanExecuteState]:
        """Load state from JSON file."""
        try:
            if not file_path.exists():
                logger.warning(f"State file not found: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            state = StateSerializer.deserialize_state(data)
            logger.debug(f"State loaded from {file_path}")
            return state
        except Exception as e:
            logger.error(f"Failed to load state from {file_path}: {e}")
            return None

    @staticmethod
    def validate_state(state: PlanExecuteState) -> bool:
        """Validate that state has required fields."""
        required_fields = ["original_query", "plan", "executed_steps", "current_step_index"]
        
        for field in required_fields:
            if field not in state:
                logger.error(f"Missing required field in state: {field}")
                return False
        
        if not isinstance(state["plan"], list):
            logger.error("State 'plan' field must be a list")
            return False
        
        if not isinstance(state["executed_steps"], list):
            logger.error("State 'executed_steps' field must be a list")
            return False
        
        if not isinstance(state["current_step_index"], int):
            logger.error("State 'current_step_index' field must be an integer")
            return False
        
        return True

    @staticmethod
    def get_state_summary(state: PlanExecuteState) -> Dict[str, Any]:
        """Get summary information about the state for debugging."""
        return {
            "query": state.get("original_query", "")[:100] + "..." if len(state.get("original_query", "")) > 100 else state.get("original_query", ""),
            "total_steps": len(state.get("plan", [])),
            "completed_steps": state.get("current_step_index", 0),
            "has_error": state.get("error_message") is not None,
            "has_final_result": state.get("final_result") is not None,
            "executed_steps_count": len(state.get("executed_steps", []))
        }