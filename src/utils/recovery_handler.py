from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from src.graph_nodes.graph_state import PlanExecuteState
from src.utils.checkpoint_manager import CheckpointManager
from src.utils.state_serializer import StateSerializer
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RecoveryHandler:
    """Handles state recovery, rollback, and resume operations."""
    
    def __init__(self, checkpoint_manager: CheckpointManager):
        """
        Initialize recovery handler.
        
        Args:
            checkpoint_manager: CheckpointManager instance to use
        """
        self.checkpoint_manager = checkpoint_manager
        
    def can_recover(self) -> bool:
        """Check if recovery is possible (checkpoint exists)."""
        return self.checkpoint_manager.has_checkpoint("current")
    
    def get_recovery_info(self) -> Optional[Dict[str, Any]]:
        """Get information about available recovery options."""
        try:
            if not self.can_recover():
                return None
                
            state = self.checkpoint_manager.load_checkpoint("current")
            if not state:
                return None
                
            summary = StateSerializer.get_state_summary(state)
            checkpoints = self.checkpoint_manager.list_checkpoints()
            
            recovery_info = {
                "can_recover": True,
                "current_state": summary,
                "available_checkpoints": len(checkpoints),
                "recovery_options": {
                    "resume": self._can_resume(state),
                    "rollback": len(checkpoints) > 1,
                    "restart": True
                }
            }
            
            return recovery_info
            
        except Exception as e:
            logger.error(f"Failed to get recovery info: {e}")
            return None
    
    def _can_resume(self, state: PlanExecuteState) -> bool:
        """Check if state can be resumed (not completed, no fatal error)."""
        if state.get("error_message"):
            return False
        
        current_step = state.get("current_step_index", 0)
        total_steps = len(state.get("plan", []))
        
        return current_step < total_steps and not state.get("final_result")
    
    def recover_state(self, checkpoint_name: str = "current") -> Optional[PlanExecuteState]:
        """
        Recover state from checkpoint.
        
        Args:
            checkpoint_name: Name of checkpoint to recover from
            
        Returns:
            Recovered PlanExecuteState or None if failed
        """
        try:
            logger.info(f"Attempting to recover state from checkpoint: {checkpoint_name}")
            
            state = self.checkpoint_manager.load_checkpoint(checkpoint_name)
            if not state:
                logger.error(f"Failed to load checkpoint: {checkpoint_name}")
                return None
            
            if not StateSerializer.validate_state(state):
                logger.error(f"Invalid state in checkpoint: {checkpoint_name}")
                return None
            
            logger.info(f"Successfully recovered state from checkpoint: {checkpoint_name}")
            self._log_recovery_details(state)
            
            return state
            
        except Exception as e:
            logger.error(f"Recovery failed: {e}")
            return None
    
    def _log_recovery_details(self, state: PlanExecuteState):
        """Log details about recovered state."""
        summary = StateSerializer.get_state_summary(state)
        logger.info(f"Recovery details: {summary}")
        
        # Log progress details
        current_step = state.get("current_step_index", 0)
        total_steps = len(state.get("plan", []))
        
        if total_steps > 0:
            progress_pct = (current_step / total_steps) * 100
            logger.info(f"Execution progress: {current_step}/{total_steps} steps ({progress_pct:.1f}%)")
            
            # Log remaining steps
            if current_step < total_steps:
                remaining_steps = state["plan"][current_step:]
                logger.info(f"Remaining steps: {len(remaining_steps)}")
                for i, step in enumerate(remaining_steps[:3]):  # Log first 3 remaining steps
                    logger.info(f"  Step {current_step + i + 1}: {step.get('task_description', '')[:100]}")
    
    def rollback_to_step(self, target_step: int) -> Optional[PlanExecuteState]:
        """
        Rollback state to a specific step.
        
        Args:
            target_step: Step number to rollback to (1-indexed)
            
        Returns:
            Modified state or None if failed
        """
        try:
            state = self.checkpoint_manager.load_checkpoint("current")
            if not state:
                logger.error("No current state to rollback from")
                return None
            
            current_step = state.get("current_step_index", 0)
            
            if target_step < 0 or target_step > current_step:
                logger.error(f"Invalid rollback target: {target_step} (current: {current_step})")
                return None
            
            # Create rollback state
            rollback_state = state.copy()
            rollback_state["current_step_index"] = target_step
            rollback_state["executed_steps"] = state["executed_steps"][:target_step]
            rollback_state["error_message"] = None  # Clear error on rollback
            
            # Don't clear final_result if we're rolling back to a completed state
            if target_step < len(state.get("plan", [])):
                rollback_state["final_result"] = None
            
            # Save rollback state
            if self.checkpoint_manager.save_checkpoint(rollback_state, "rollback"):
                logger.info(f"Rolled back to step {target_step}")
                return rollback_state
            else:
                logger.error("Failed to save rollback state")
                return None
                
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return None
    
    def find_last_successful_checkpoint(self) -> Optional[Tuple[str, PlanExecuteState]]:
        """
        Find the most recent checkpoint without errors.
        
        Returns:
            Tuple of (checkpoint_name, state) or None if not found
        """
        try:
            checkpoints = self.checkpoint_manager.list_checkpoints()
            
            # Sort by modification time (most recent first)
            checkpoints.sort(key=lambda x: x["modified"], reverse=True)
            
            for checkpoint in checkpoints:
                checkpoint_name = checkpoint["name"]
                state = self.checkpoint_manager.load_checkpoint(checkpoint_name)
                
                if state and not state.get("error_message"):
                    return checkpoint_name, state
            
            logger.warning("No successful checkpoint found")
            return None
            
        except Exception as e:
            logger.error(f"Failed to find successful checkpoint: {e}")
            return None
    
    def auto_recover(self) -> Optional[PlanExecuteState]:
        """
        Automatically recover from the best available state.
        
        Returns:
            Recovered state or None if no recovery possible
        """
        try:
            logger.info("Starting auto-recovery process")
            
            # First, try current checkpoint if it's not errored
            current_state = self.checkpoint_manager.load_checkpoint("current")
            if current_state and not current_state.get("error_message"):
                logger.info("Current checkpoint is valid, using it for recovery")
                return current_state
            
            # If current is errored, find last successful checkpoint
            result = self.find_last_successful_checkpoint()
            if result:
                checkpoint_name, state = result
                logger.info(f"Auto-recovery using checkpoint: {checkpoint_name}")
                
                # Save as current for future operations
                self.checkpoint_manager.save_checkpoint(state, "current")
                return state
            
            logger.warning("Auto-recovery failed: no valid checkpoints found")
            return None
            
        except Exception as e:
            logger.error(f"Auto-recovery failed: {e}")
            return None
    
    def create_recovery_report(self) -> Dict[str, Any]:
        """Create a detailed recovery report."""
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "recovery_possible": self.can_recover(),
                "checkpoints": self.checkpoint_manager.list_checkpoints(),
                "current_state": None,
                "recommendations": []
            }
            
            # Add current state info if available
            if self.can_recover():
                state = self.checkpoint_manager.load_checkpoint("current")
                if state:
                    report["current_state"] = StateSerializer.get_state_summary(state)
                    
                    # Add recommendations based on state
                    if state.get("error_message"):
                        report["recommendations"].append("Current state has errors - consider rollback or auto-recovery")
                    elif self._can_resume(state):
                        report["recommendations"].append("State can be resumed from current position")
                    elif state.get("final_result"):
                        report["recommendations"].append("Analysis appears complete")
                    else:
                        report["recommendations"].append("State may need manual inspection")
            else:
                report["recommendations"].append("No recovery checkpoints available - fresh start required")
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to create recovery report: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def validate_recovery_integrity(self, state: PlanExecuteState) -> Tuple[bool, List[str]]:
        """
        Validate integrity of recovered state.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        try:
            # Basic state validation
            if not StateSerializer.validate_state(state):
                issues.append("State failed basic validation")
            
            # Check step consistency
            current_step = state.get("current_step_index", 0)
            executed_steps = state.get("executed_steps", [])
            
            if current_step != len(executed_steps):
                issues.append(f"Step index mismatch: current={current_step}, executed={len(executed_steps)}")
            
            # Check plan consistency
            plan = state.get("plan", [])
            if current_step > len(plan):
                issues.append(f"Current step ({current_step}) exceeds plan length ({len(plan)})")
            
            # Check for required fields in plan steps
            for i, step in enumerate(plan):
                if not isinstance(step, dict):
                    issues.append(f"Plan step {i+1} is not a dictionary")
                    continue
                
                required_fields = ["step_id", "task_description", "assigned_agent"]
                for field in required_fields:
                    if field not in step:
                        issues.append(f"Plan step {i+1} missing field: {field}")
            
            # Check executed steps integrity
            for i, executed_step in enumerate(executed_steps):
                if not isinstance(executed_step, dict):
                    issues.append(f"Executed step {i+1} is not a dictionary")
                    continue
                
                if "status" not in executed_step:
                    issues.append(f"Executed step {i+1} missing status")
            
            is_valid = len(issues) == 0
            return is_valid, issues
            
        except Exception as e:
            issues.append(f"Validation error: {str(e)}")
            return False, issues