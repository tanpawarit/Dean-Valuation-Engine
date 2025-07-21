from pathlib import Path

from src.graph_nodes.graph_builder import build_graph, build_graph_with_recovery
from src.utils import load_app_config, setup_logging
from src.utils.config_manager import get_checkpoint_config
from src.utils.logger import get_logger

load_app_config()  # Load config and set ENV VARS FIRST
setup_logging()

logger = get_logger(__name__)

# ========= CONFIGURATION =========
checkpoint_config = get_checkpoint_config()
enable_checkpoints = checkpoint_config.get('enabled', False)

logger.info(f"Checkpointing {'enabled' if enable_checkpoints else 'disabled'}")

# ========= CONSTRUCT THE GRAPH =========
if enable_checkpoints:
    # Build graph with recovery capabilities
    app, recovered_state = build_graph_with_recovery()
    
    if recovered_state:
        logger.info("Using recovered state from previous run")
        initial_state = recovered_state
    else:
        logger.info("Starting fresh analysis")
        initial_state = None
else:
    # Build standard graph without checkpointing
    app = build_graph()
    initial_state = None

# ========= RUN THE GRAPH =========
# initial_query = "Analyze expected growth of UBER"
# initial_query = "analyze moat comparison of Uber and Lyft"
initial_query = "analyze profitability of Uber"

# Run the graph
if initial_state:
    # Resume from recovered state
    result = app.invoke(initial_state)
else:
    # Start fresh
    result = app.invoke({"original_query": initial_query})

# ========= SAVE RESULT TO analysis_report.md =========
content_to_save_to_file: str | None = None
if isinstance(result, dict):
    # Prefer the 'final_result' key; fallback to full dict string
    content_to_save_to_file = result.get("final_result", str(result))
elif isinstance(result, str):
    content_to_save_to_file = result
else:
    content_to_save_to_file = str(result)

if content_to_save_to_file:  # Ensure there's content to write
    report_path: Path = Path(__file__).with_name("analysis_report.md")
    with report_path.open("w", encoding="utf-8") as report_file:
        report_file.write(content_to_save_to_file)
