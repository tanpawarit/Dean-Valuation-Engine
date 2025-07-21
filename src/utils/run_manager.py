"""
Run management utilities for viewing and organizing checkpoint runs by datetime.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

from src.utils.checkpoint_manager import CheckpointManager
from src.utils.state_serializer import StateSerializer
from src.utils.logger import get_logger

logger = get_logger(__name__)


def list_runs_by_datetime(base_dir: Optional[Path] = None, show_details: bool = True) -> List[Dict[str, Any]]:
    """
    List all runs sorted by creation datetime with enhanced information.
    
    Args:
        base_dir: Base directory for runs (defaults to .dean_state)
        show_details: Include detailed information about each run
    
    Returns:
        List of run information dictionaries sorted by creation time (newest first)
    """
    base_dir = base_dir or Path(".dean_state")
    runs = []
    
    try:
        if not base_dir.exists():
            logger.info("No .dean_state directory found")
            return runs
        
        for run_dir in base_dir.glob("run_*"):
            if not run_dir.is_dir():
                continue
                
            run_info = {
                "run_id": run_dir.name.replace("run_", ""),
                "directory": run_dir.name,
                "path": str(run_dir),
                "created_at": None,
                "created_at_formatted": "Unknown",
                "status": "unknown"
            }
            
            # Read metadata
            metadata_path = run_dir / "metadata.json"
            if metadata_path.exists():
                try:
                    with open(metadata_path) as f:
                        metadata = json.load(f)
                        created_at_str = metadata.get("created_at")
                        
                        if created_at_str:
                            run_info["created_at"] = created_at_str
                            # Parse and format datetime
                            try:
                                dt = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                                run_info["created_at_formatted"] = dt.strftime("%Y-%m-%d %H:%M:%S")
                            except ValueError:
                                run_info["created_at_formatted"] = created_at_str
                                
                except Exception as e:
                    logger.warning(f"Failed to read metadata for {run_dir}: {e}")
            
            # Add detailed information if requested
            if show_details:
                try:
                    manager = CheckpointManager(base_dir=base_dir, run_id=run_info["run_id"])
                    
                    if manager.has_checkpoint("current"):
                        state = manager.load_checkpoint("current")
                        if state:
                            summary = StateSerializer.get_state_summary(state)
                            run_info.update({
                                "query": summary["query"],
                                "total_steps": summary["total_steps"],
                                "completed_steps": summary["completed_steps"],
                                "has_error": summary["has_error"],
                                "has_final_result": summary["has_final_result"],
                                "status": "completed" if summary["has_final_result"] else ("error" if summary["has_error"] else "in_progress")
                            })
                        else:
                            run_info["status"] = "corrupted"
                    else:
                        run_info["status"] = "no_checkpoint"
                        
                except Exception as e:
                    logger.warning(f"Failed to get details for {run_dir}: {e}")
                    run_info["status"] = "error"
            
            runs.append(run_info)
        
        # Sort by creation time (newest first)
        return sorted(runs, key=lambda x: x["created_at"] or "", reverse=True)
        
    except Exception as e:
        logger.error(f"Failed to list runs: {e}")
        return []


def print_runs_table(base_dir: Optional[Path] = None):
    """Print a formatted table of all runs sorted by datetime."""
    runs = list_runs_by_datetime(base_dir, show_details=True)
    
    if not runs:
        print("No analysis runs found in .dean_state directory")
        return
    
    print(f"\n📊 Analysis Runs (Total: {len(runs)})")
    print("=" * 120)
    print(f"{'Directory':<15} {'Created':<17} {'Status':<12} {'Steps':<8} {'Query':<50}")
    print("-" * 120)
    
    for run in runs:
        directory = run["directory"]
        created = run["created_at_formatted"]
        status = run.get("status", "unknown")
        
        # Format status with colors/symbols
        status_display = {
            "completed": "✅ Complete",
            "in_progress": "🔄 Running", 
            "error": "❌ Error",
            "no_checkpoint": "📝 No Data",
            "corrupted": "🔧 Corrupted",
            "unknown": "❓ Unknown"
        }.get(status, status)
        
        steps = ""
        if run.get("total_steps") is not None and run.get("completed_steps") is not None:
            steps = f"{run['completed_steps']}/{run['total_steps']}"
        
        query = run.get("query", "No query found")[:47]
        if len(run.get("query", "")) > 47:
            query += "..."
            
        print(f"{directory:<15} {created:<17} {status_display:<20} {steps:<8} {query}")
    
    print("=" * 120)
    print(f"💾 Checkpoint directory: {base_dir or Path('.dean_state')}")


def get_run_details(run_id: str, base_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Get detailed information about a specific run."""
    try:
        manager = CheckpointManager(base_dir=base_dir, run_id=run_id)
        
        if not manager.has_checkpoint("current"):
            return None
        
        state = manager.load_checkpoint("current")
        if not state:
            return None
        
        # Get run metadata
        metadata_path = manager.run_dir / "metadata.json"
        metadata = {}
        if metadata_path.exists():
            with open(metadata_path) as f:
                metadata = json.load(f)
        
        # Get state summary
        summary = StateSerializer.get_state_summary(state)
        
        # Get checkpoint list
        checkpoints = manager.list_checkpoints()
        
        details = {
            "run_id": run_id,
            "metadata": metadata,
            "state_summary": summary,
            "checkpoints": checkpoints,
            "run_directory": str(manager.run_dir),
            "completed_steps": len(state.get("executed_steps", [])),
            "current_step": state.get("current_step_index", 0),
            "plan": state.get("plan", []),
            "final_result_length": len(str(state.get("final_result", ""))) if state.get("final_result") else 0
        }
        
        return details
        
    except Exception as e:
        logger.error(f"Failed to get run details for {run_id}: {e}")
        return None


def cleanup_old_runs_by_date(base_dir: Optional[Path] = None, keep_last_n: int = 5) -> bool:
    """Clean up old runs, keeping only the most recent N runs by creation date."""
    try:
        runs = list_runs_by_datetime(base_dir, show_details=False)
        
        # Keep only the most recent runs
        runs_to_delete = runs[keep_last_n:]
        
        deleted_count = 0
        for run in runs_to_delete:
            run_path = Path(run["path"])
            if run_path.exists():
                import shutil
                shutil.rmtree(run_path)
                logger.info(f"Deleted old run: {run['directory']}")
                deleted_count += 1
        
        if deleted_count > 0:
            print(f"🧹 Cleaned up {deleted_count} old run(s), kept {keep_last_n} most recent")
        else:
            print(f"✅ No cleanup needed, only {len(runs)} run(s) found")
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to cleanup old runs: {e}")
        return False