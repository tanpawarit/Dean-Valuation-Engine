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

# from IPython.display import Image, display
# display(Image(app.get_graph(xray=True).draw_mermaid_png()))


def run_graph_stream_debug(app_instance: Any, initial_inputs: Dict[str, str], run_id: str) -> Dict[str, Any]:
    print(f"\n--- Running Graph in DEBUG STREAM MODE for Query: '{initial_inputs['original_query']}' (Run ID: {run_id}) ---")
    final_state: Dict[str, Any] = {}
    previous_state: Dict[str, Any] = initial_inputs.copy()

    for s_item in app_instance.stream(initial_inputs, {"recursion_limit": 15}):
        current_state = s_item
        print(f"\n--- Current State Snapshot (Run ID: {run_id}) ---")
        for key, value in current_state.items():
            print(f"Graph Node: {key}")
            if value and isinstance(value, dict): 
                if 'executed_steps' in value and value['executed_steps']:
                    summary_executed = []
                    for step in value['executed_steps']:
                        summary_executed.append({
                            'step_id': step.get('step_id'),
                            'assigned_agent': step.get('assigned_agent'),
                            'status': step.get('status'),
                            'output_snippet': str(step.get('output'))[:100] + "..." if step.get('output') else "N/A"
                        })
                    print(f"  Executed Steps Summary (snapshot): {summary_executed}")
                # final_output and final_answer specific snapshot logging removed
            elif value:
                 print(f"  Value (snapshot, non-dict): {str(value)[:200]}...")
            else:
                print(f"  Value (snapshot): {value}")
        
        # Log node executions for this step
        for node_name, node_value in current_state.items():
            if node_name not in previous_state or previous_state.get(node_name) != node_value:
                log_node_execution(
                    run_id=run_id,
                    node_name=node_name,
                    state_before=previous_state,
                    state_after=current_state,
                    output=node_value
                )
        
        previous_state = current_state.copy()
        final_state = s_item 
    return final_state

def run_graph_production(app_instance: Any, initial_inputs: Dict[str, str], run_id: str) -> Dict[str, Any]: # Added run_id
    print(f"\n--- Running Graph in PRODUCTION MODE for Query: '{initial_inputs['original_query']}' (Run ID: {run_id}) ---")
    final_state = app_instance.invoke(initial_inputs, {"recursion_limit": 15})
    
    print(f"\n--- Production Mode Final State (Concise) ---")
    if not final_state:
        print("Graph invocation in production mode did not produce a final state.")
        return final_state # Return early if no final_state

    # Logic for finding and printing 'final_answer' or 'final_output' has been removed.
    # The following block will provide general diagnostic information about the final state.
    print("--- Production Mode Final State Details ---")

    diagnostic_items = {}
    for k, v_node_content in final_state.items():
        if isinstance(v_node_content, dict):
            # Check for common potentially relevant keys or summarize if it's a non-empty dict
            if v_node_content.get("summary"):
                 diagnostic_items[k] = f"summary: {str(v_node_content['summary'])[:150]}..."
            elif v_node_content.get("result"):
                 diagnostic_items[k] = f"result: {str(v_node_content['result'])[:150]}..."
            elif v_node_content: # Any other non-empty dict
                diagnostic_items[k] = f"content (dict): {str(v_node_content)[:150]}..."
        elif isinstance(v_node_content, str) and v_node_content: # Non-empty string
            diagnostic_items[k] = f"content (str): {str(v_node_content)[:150]}..."
        elif v_node_content: # Other non-empty, non-dict, non-str types
            diagnostic_items[k] = f"content ({type(v_node_content).__name__}): {str(v_node_content)[:150]}..."

    if diagnostic_items:
        print("Relevant final state items for diagnostics:")
        for node, item_summary in diagnostic_items.items():
            print(f"  Node '{node}': {item_summary}")
    else:
        # If no specific items found, just list the keys of the final_state
        print(f"No specific relevant items found for diagnostics. Full state keys: {list(final_state.keys())}")
        # Optionally, for very thorough debugging, uncomment to print a snippet of the full state:
        # print(f"Full final_state (first 500 chars): {str(final_state)[:500]}...")
    
    return final_state

if __name__ == "__main__":
    # --- Configuration ---
    USE_DEBUG_STREAM_MODE = True 
    initial_query = "Analyze expected growth of UBER"
    # initial_query = "Analyze the TAM SAM SOM of JPMorgan Chase"
    # initial_query = "Analyze peer group of UBER"
    # initial_query = "Hi"

    inputs: Dict[str, str] = {"original_query": initial_query}
    s: Dict[str, Any] = {} # Initialize s, will hold the final state
    graph_error_obj: Optional[Exception] = None

    # Clear the log file at the start of each run
    if LOG_FILE_PATH.exists():
        try:
            LOG_FILE_PATH.unlink()
            print(f"--- Cleared old log file: {LOG_FILE_PATH} ---")
        except OSError as e:
            print(f"--- Error clearing log file {LOG_FILE_PATH}: {e} ---")

    run_id = generate_run_id()
    log_graph_start(run_id=run_id, initial_state=inputs)

    try:
        if USE_DEBUG_STREAM_MODE:
            print(f"--- RUNNING IN DEBUG STREAM MODE (Run ID: {run_id}) ---")
            s = run_graph_stream_debug(app, inputs, run_id)
        else:
            print(f"--- RUNNING IN PRODUCTION MODE (Run ID: {run_id}) ---")
            s = run_graph_production(app, inputs, run_id)
    except Exception as e:
        print(f"!!! Graph execution failed with error: {e} (Run ID: {run_id}) !!!")
        graph_error_obj = e

    # --- Determine Final Graph Output Payload (for report and logging) ---
    final_graph_output_payload = None
    if graph_error_obj:
        final_graph_output_payload = f"Graph execution failed: {str(graph_error_obj)}"
    elif s:
        for node_name, node_output_state in s.items():
            if isinstance(node_output_state, dict):
                if "final_result" in node_output_state:
                    final_graph_output_payload = node_output_state["final_result"]
                    print(f"Identified 'final_result' from node '{node_name}' (Run ID: {run_id}).")
                    break
                elif "error_message" in node_output_state:
                    final_graph_output_payload = f"Graph ended with an error from node '{node_name}': {node_output_state['error_message']}"
                    print(f"Identified 'error_message' from node '{node_name}' (Run ID: {run_id}).")
                    break
            elif node_name == END and node_output_state is not None:
                 final_graph_output_payload = node_output_state
                 print(f"Identified output from END node (Run ID: {run_id}).")
                 break
        if final_graph_output_payload is None: # Fallback if no specific result/error found in nodes
            print(f"Could not determine a specific 'final_result' or 'error_message' from the graph's final state. Using full state as fallback (Run ID: {run_id}).")
            final_graph_output_payload = s
    else: # s is empty and no graph_error_obj (e.g. if graph was interrupted before s was populated)
        final_graph_output_payload = f"Graph did not produce a final state 's' and no explicit error was caught externally (Run ID: {run_id})."

    log_graph_end(
        run_id=run_id,
        final_state=s if s else {},
        result=final_graph_output_payload,
        error=str(graph_error_obj) if graph_error_obj else None
    )

    # --- Print Final State Details (from 's') ---
    print(f"\n--- Final State Details (from last graph state 's', Run ID: {run_id}) ---")
    if s:
        for key, value in s.items(): 
            print(f"Graph Node (final state): {key}")
            if value and isinstance(value, dict):
                if 'executed_steps' in value and value['executed_steps']:
                    summary_executed = []
                    for step_info in value['executed_steps']:
                        summary_executed.append({
                            'step_id': step_info.get('step_id'),
                            'assigned_agent': step_info.get('assigned_agent'),
                            'status': step_info.get('status'),
                            'output_snippet': str(step_info.get('output'))[:100] + "..." if step_info.get('output') else "N/A"
                        })
                    print(f"  Executed Steps Summary (final): {summary_executed}")
                if 'final_output' in value and value['final_output']:
                     print(f"  Final State 'final_output': {value['final_output']}")
                if 'final_answer' in value and value['final_answer']:
                     print(f"  Final State 'final_answer': {value['final_answer']}")
            elif value:
                 print(f"  Final State Value (non-dict): {value}")
            else:
                print(f"  Final State Value: {value}")
    else:
        print(f"Graph did not produce a final state 's' (Run ID: {run_id}).")

    # --- Print and Save Report --- 
    print(f"\n--- GRAPH'S FINAL OUTPUT PAYLOAD (Run ID: {run_id}) ---")
    # final_graph_output_payload is already determined above

    content_to_save_to_file = None
    if isinstance(final_graph_output_payload, dict):
        # If the payload is a dict, try to get 'final_result' for the report
        # Otherwise, the report will contain the string representation of the dict
        content_to_save_to_file = final_graph_output_payload.get("final_result", str(final_graph_output_payload))
    elif isinstance(final_graph_output_payload, str):
        content_to_save_to_file = final_graph_output_payload
    else: # Other types, convert to string
        content_to_save_to_file = str(final_graph_output_payload)

    if content_to_save_to_file: # Ensure there's something to save
        report_filename = "analysis_report.md"
        print(f"content_to_save_to_file: {content_to_save_to_file}")
        try:
            with open(report_filename, "w", encoding="utf-8") as f:
                f.write(content_to_save_to_file)
            print(f"\n--- Report successfully saved to {report_filename} (Run ID: {run_id}) ---")
        except IOError as e:
            print(f"\n--- Error saving report to {report_filename}: {e} (Run ID: {run_id}) ---")
    else:
        print(f"\n--- No content derived for saving report (Run ID: {run_id}). --- ")
    # --- End of save report ---
 