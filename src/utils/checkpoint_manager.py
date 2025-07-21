import fcntl
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.graph_nodes.graph_state import PlanExecuteState
from src.utils.logger import get_logger
from src.utils.state_serializer import StateSerializer

logger = get_logger(__name__)


class CheckpointManager:
    """File-based checkpoint manager for LangGraph state persistence."""

    def __init__(self, base_dir: Optional[Path] = None, run_id: Optional[str] = None):
        """
        Initialize checkpoint manager.

        Args:
            base_dir: Base directory for checkpoints (defaults to .dean_state)
            run_id: Unique run identifier (generates UUID if not provided)
        """
        self.base_dir = base_dir or Path(".dean_state")
        self.run_id = run_id or str(uuid.uuid4())[:8]
        self.run_dir = self.base_dir / f"run_{self.run_id}"

        # Create directory structure
        self._setup_directories()

        # Track checkpoint sequence
        self._checkpoint_counter = 0

    def _setup_directories(self):
        """Create necessary directory structure."""
        try:
            self.run_dir.mkdir(parents=True, exist_ok=True)
            (self.run_dir / "steps").mkdir(exist_ok=True)
            (self.run_dir / "locks").mkdir(exist_ok=True)

            # Create metadata file
            metadata = {"run_id": self.run_id, "created_at": datetime.now().isoformat(), "version": "1.0"}

            with open(self.run_dir / "metadata.json", "w") as f:
                import json

                json.dump(metadata, f, indent=2)

            logger.info(f"Checkpoint directories created at {self.run_dir}")

        except Exception as e:
            logger.error(f"Failed to setup checkpoint directories: {e}")
            raise

    def _get_lock_file(self, operation: str) -> Path:
        """Get lock file path for operation."""
        return self.run_dir / "locks" / f"{operation}.lock"

    def _acquire_lock(self, operation: str) -> Optional[Any]:
        """Acquire file lock for operation."""
        lock_file = self._get_lock_file(operation)
        try:
            lock_fd = open(lock_file, "w")
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            lock_fd.write(f"locked_by_run_{self.run_id}_{datetime.now().isoformat()}")
            lock_fd.flush()
            return lock_fd
        except (OSError, IOError) as e:
            logger.warning(f"Could not acquire lock for {operation}: {e}")
            return None

    def _release_lock(self, lock_fd: Any):
        """Release file lock."""
        try:
            if lock_fd:
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
                lock_fd.close()
        except Exception as e:
            logger.warning(f"Error releasing lock: {e}")

    def save_checkpoint(self, state: PlanExecuteState, checkpoint_name: str = "current") -> bool:
        """
        Save state checkpoint to file.

        Args:
            state: PlanExecuteState to save
            checkpoint_name: Name of checkpoint (defaults to "current")

        Returns:
            bool: Success status
        """
        lock_fd = self._acquire_lock("checkpoint")

        try:
            if not StateSerializer.validate_state(state):
                logger.error("Invalid state provided to save_checkpoint")
                return False

            # Save current state
            current_path = self.run_dir / f"{checkpoint_name}.json"
            success = StateSerializer.save_to_file(state, current_path)

            if success and checkpoint_name == "current":
                # Also save numbered checkpoint for history
                self._checkpoint_counter += 1
                numbered_path = self.run_dir / "steps" / f"checkpoint_{self._checkpoint_counter:03d}.json"
                StateSerializer.save_to_file(state, numbered_path)

                # Save individual step if we have executed_steps
                if state.get("executed_steps"):
                    last_step_idx = len(state["executed_steps"]) - 1
                    if last_step_idx >= 0:
                        step_data = state["executed_steps"][last_step_idx]
                        step_path = self.run_dir / "steps" / f"step_{last_step_idx + 1:03d}.json"

                        with open(step_path, "w") as f:
                            import json

                            json.dump(step_data, f, indent=2)

            logger.info(f"Checkpoint '{checkpoint_name}' saved successfully")
            return success

        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return False
        finally:
            self._release_lock(lock_fd)

    def load_checkpoint(self, checkpoint_name: str = "current") -> Optional[PlanExecuteState]:
        """
        Load state checkpoint from file.

        Args:
            checkpoint_name: Name of checkpoint to load

        Returns:
            PlanExecuteState or None if failed
        """
        try:
            checkpoint_path = self.run_dir / f"{checkpoint_name}.json"
            state = StateSerializer.load_from_file(checkpoint_path)

            if state and StateSerializer.validate_state(state):
                logger.info(f"Checkpoint '{checkpoint_name}' loaded successfully")
                return state
            else:
                logger.error(f"Invalid checkpoint data in {checkpoint_path}")
                return None

        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """List available checkpoints with metadata."""
        checkpoints = []

        try:
            # List main checkpoint files
            for checkpoint_file in self.run_dir.glob("*.json"):
                if checkpoint_file.name == "metadata.json":
                    continue

                stat = checkpoint_file.stat()
                checkpoints.append(
                    {
                        "name": checkpoint_file.stem,
                        "path": str(checkpoint_file),
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    }
                )

            # List numbered checkpoints
            steps_dir = self.run_dir / "steps"
            if steps_dir.exists():
                for step_file in steps_dir.glob("checkpoint_*.json"):
                    stat = step_file.stat()
                    checkpoints.append(
                        {
                            "name": step_file.stem,
                            "path": str(step_file),
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        }
                    )

            return sorted(checkpoints, key=lambda x: x["modified"])

        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
            return []

    def get_state_summary(self) -> Optional[Dict[str, Any]]:
        """Get summary of current state."""
        try:
            state = self.load_checkpoint("current")
            if state:
                return StateSerializer.get_state_summary(state)
            return None
        except Exception as e:
            logger.error(f"Failed to get state summary: {e}")
            return None

    def cleanup_old_checkpoints(self, keep_last_n: int = 10) -> bool:
        """
        Clean up old checkpoint files, keeping only the most recent N.

        Args:
            keep_last_n: Number of recent checkpoints to keep

        Returns:
            bool: Success status
        """
        try:
            steps_dir = self.run_dir / "steps"
            if not steps_dir.exists():
                return True

            # Get all checkpoint files sorted by modification time
            checkpoint_files = sorted(
                steps_dir.glob("checkpoint_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,  # Most recent first
            )

            # Delete old checkpoints beyond keep_last_n
            deleted_count = 0
            for old_checkpoint in checkpoint_files[keep_last_n:]:
                old_checkpoint.unlink()
                deleted_count += 1

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old checkpoint files")

            return True

        except Exception as e:
            logger.error(f"Failed to cleanup old checkpoints: {e}")
            return False

    def has_checkpoint(self, checkpoint_name: str = "current") -> bool:
        """Check if checkpoint exists."""
        checkpoint_path = self.run_dir / f"{checkpoint_name}.json"
        return checkpoint_path.exists()

    def delete_run(self) -> bool:
        """Delete entire run directory and all checkpoints."""
        try:
            if self.run_dir.exists():
                shutil.rmtree(self.run_dir)
                logger.info(f"Deleted run directory: {self.run_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete run directory: {e}")
            return False

    @classmethod
    def list_all_runs(cls, base_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        """List all available runs."""
        base_dir = base_dir or Path(".dean_state")
        runs = []

        try:
            if not base_dir.exists():
                return runs

            for run_dir in base_dir.glob("run_*"):
                if run_dir.is_dir():
                    metadata_path = run_dir / "metadata.json"
                    run_info = {"run_id": run_dir.name.replace("run_", ""), "path": str(run_dir), "created": None}

                    if metadata_path.exists():
                        try:
                            import json

                            with open(metadata_path) as f:
                                metadata = json.load(f)
                                run_info["created"] = metadata.get("created_at")
                        except Exception:
                            pass

                    runs.append(run_info)

            return sorted(runs, key=lambda x: x["created"] or "", reverse=True)

        except Exception as e:
            logger.error(f"Failed to list runs: {e}")
            return []

    @classmethod
    def cleanup_old_runs(cls, base_dir: Optional[Path] = None, keep_last_n: int = 5) -> bool:
        """Clean up old run directories."""
        base_dir = base_dir or Path(".dean_state")

        try:
            runs = cls.list_all_runs(base_dir)

            # Delete old runs beyond keep_last_n
            for old_run in runs[keep_last_n:]:
                run_path = Path(old_run["path"])
                if run_path.exists():
                    shutil.rmtree(run_path)
                    logger.info(f"Cleaned up old run: {old_run['run_id']}")

            return True

        except Exception as e:
            logger.error(f"Failed to cleanup old runs: {e}")
            return False
