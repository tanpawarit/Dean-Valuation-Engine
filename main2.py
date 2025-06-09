from src.utils import load_app_config
from src.utils import setup_logging
from typing import Any, Dict, Optional
from src.utils.graph_logger import generate_run_id, log_graph_start, log_node_execution, log_graph_end, LOG_FILE_PATH
from langgraph.graph import Graph
load_app_config() # Load config and set ENV VARS FIRST
setup_logging()

from src.graph_nodes.graph_builder import build_graph
from langgraph.graph import END
 
# --- Construct the Graph ---
app = build_graph() 

initial_query = "Analyze expected growth of UBER"
inputs: Dict[str, str] = {"original_query": initial_query}

app.invoke(inputs)