"""
Main entry point for the Analyst Robot system.
"""

import logging
from pathlib import Path
from src.utils.common import load_config, setup_logging, validate_config
from src.orchestrators.workflow_manager import WorkflowManager

def main():
    """Main entry point for the Analyst Robot system."""
    # Load and validate configuration
    config = load_config("config.yaml")
    if not validate_config(config):
        raise ValueError("Invalid configuration file")
    
    # Set up logging
    setup_logging(config)
    logger = logging.getLogger(__name__)
    logger.info("Starting Analyst Robot")
    
    try:
        # Initialize workflow manager
        workflow_manager = WorkflowManager(config)
        
        # Example task
        task = {
            "task_id": "example_analysis",
            "type": "market_analysis",
            "parameters": {
                "symbol": "AAPL",
                "timeframe": "1d",
                "analysis_type": "technical"
            }
        }
        
        # Execute workflow
        results = workflow_manager.execute_workflow(task)
        logger.info(f"Analysis completed: {results}")
        
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()
