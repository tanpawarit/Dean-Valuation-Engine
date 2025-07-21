"""
Global checkpoint manager registry to avoid circular imports.
Provides a centralized way to access the checkpoint manager instance.
"""

from src.utils.checkpoint_manager import CheckpointManager
from src.utils.logger import get_logger
from src.utils.recovery_handler import RecoveryHandler

logger = get_logger(__name__)

# Global checkpoint manager instance
_checkpoint_manager: CheckpointManager | None = None
_recovery_handler: RecoveryHandler | None = None


def set_checkpoint_manager(checkpoint_manager: CheckpointManager) -> None:
    """Set global checkpoint manager instance."""
    global _checkpoint_manager, _recovery_handler
    _checkpoint_manager = checkpoint_manager
    _recovery_handler = RecoveryHandler(checkpoint_manager)
    logger.info("Checkpoint manager configured globally")


def get_checkpoint_manager() -> CheckpointManager | None:
    """Get current checkpoint manager instance."""
    return _checkpoint_manager


def get_recovery_handler() -> RecoveryHandler | None:
    """Get current recovery handler instance."""
    return _recovery_handler