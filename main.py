from pathlib import Path

from src.graph_nodes.graph_builder import build_graph
from src.utils import load_app_config, setup_logging
from src.utils.logger import get_logger

load_app_config()  # Load config and set ENV VARS FIRST
setup_logging()

logger = get_logger(__name__)

# ========= CONSTRUCT THE GRAPH =========
app = build_graph()

# ========= RUN THE GRAPH =========
# initial_query = "Analyze expected growth of UBER"
# initial_query = "analyze moat comparison of Uber and Lyft"
initial_query = "analyze profitability of Uber"


# Run the graph
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
