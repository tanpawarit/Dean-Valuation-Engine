from src.utils import load_app_config
from src.utils import setup_logging
from typing import Any, Dict
from langgraph.graph import Graph
load_app_config() # Load config and set ENV VARS FIRST
setup_logging()

from src.graph_nodes.graph_builder import build_graph
from langgraph.graph import END
 
# --- Construct the Graph ---
app = build_graph()

#TODO debug ว่า graph state ทำงานถูกต้องหรือไม่
#TODO ทำไฟล main ใหม่ เเละทำ guardrail node

# from IPython.display import Image, display
# display(Image(app.get_graph(xray=True).draw_mermaid_png()))


def run_graph_stream_debug(app_instance: Any, initial_inputs: Dict[str, str]) -> Dict[str, Any]:
    print(f"\n--- Running Graph in DEBUG STREAM MODE for Query: '{initial_inputs['original_query']}' ---")
    final_state: Dict[str, Any] = {} 
    for s_item in app_instance.stream(initial_inputs, {"recursion_limit": 15}):
        print(f"\n--- Current State Snapshot ---")
        for key, value in s_item.items():
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
                if 'final_output' in value and value['final_output']:
                     print(f"  Snapshot 'final_output': {str(value['final_output'])[:200]}...")
                if 'final_answer' in value and value['final_answer']:
                     print(f"  Snapshot 'final_answer': {str(value['final_answer'])[:200]}...")
            elif value:
                 print(f"  Value (snapshot, non-dict): {str(value)[:200]}...")
            else:
                print(f"  Value (snapshot): {value}") 
        final_state = s_item 
    return final_state

def run_graph_production(app_instance: Any, initial_inputs: Dict[str, str]) -> Dict[str, Any]:
    print(f"\n--- Running Graph in PRODUCTION MODE for Query: '{initial_inputs['original_query']}' ---")
    final_state = app_instance.invoke(initial_inputs, {"recursion_limit": 15})
    
    print(f"\n--- Production Mode Final State (Concise) ---")
    if not final_state:
        print("Graph invocation in production mode did not produce a final state.")
        return final_state # Return early if no final_state

    found_answer_node_name: str | None = None
    found_answer_content: Any = None
    found_output_node_name: str | None = None
    found_output_content: Any = None

    # First pass: prioritize finding final_answer from any node
    for node_name, node_content in final_state.items():
        if isinstance(node_content, dict):
            if node_content.get("final_answer"): # Checks for key existence and truthy value
                found_answer_node_name = node_name
                found_answer_content = node_content["final_answer"]
                break  # Found the best possible answer (final_answer), no need to look further in other nodes for this key

    # Second pass (only if no final_answer was found): look for final_output from any node
    if not found_answer_content:
        for node_name, node_content in final_state.items():
            if isinstance(node_content, dict):
                if node_content.get("final_output"): # Checks for key existence and truthy value
                    found_output_node_name = node_name
                    found_output_content = node_content["final_output"]
                    break # Found a final_output, take the first one encountered

    primary_output_printed = False
    if found_answer_content: # This implies found_answer_node_name is also set
        print(f"Node '{found_answer_node_name}' -> Final Answer: {found_answer_content}")
        primary_output_printed = True
    elif found_output_content: # This implies found_output_node_name is also set
        print(f"Node '{found_output_node_name}' -> Final Output (snippet): {str(found_output_content)[:200]}...")
        primary_output_printed = True
        
    if not primary_output_printed:
        # Fallback: provide more detailed diagnostic info if no primary output was found
        print("Primary output (final_answer or final_output) not explicitly found in any node.")
        
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
    # Set to True to use verbose streaming output for debugging, False for production (invoke) mode.
    USE_DEBUG_STREAM_MODE = True 
    initial_query = "Analyze the TAM SAM SOM of JPMorgan Chase" # Default query

    inputs: Dict[str, str] = {"original_query": initial_query}
    s: Dict[str, Any] = {} # Initialize s, will hold the final state from either mode

    if USE_DEBUG_STREAM_MODE:
        print("--- RUNNING IN DEBUG STREAM MODE ---")
        s = run_graph_stream_debug(app, inputs)
    else:
        print("--- RUNNING IN PRODUCTION MODE ---")
        s = run_graph_production(app, inputs) 

    print(f"\n--- Final State Details (from last streamed state 's') ---")
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
        print("Graph stream did not produce a final state 's'.")

    final_graph_output_payload = None
    if s:
        for node_name, node_output_state in s.items():
            if isinstance(node_output_state, dict):
                if "final_result" in node_output_state: 
                    final_graph_output_payload = node_output_state["final_result"]
                    print(f"Identified 'final_result' from node '{node_name}'.")
                    break
                elif "error_message" in node_output_state: 
                    final_graph_output_payload = f"Graph ended with an error from node '{node_name}': {node_output_state['error_message']}"
                    print(f"Identified 'error_message' from node '{node_name}'.")
                    break
            elif node_name == END and node_output_state is not None: 
                 final_graph_output_payload = node_output_state
                 print(f"Identified output from END node.")
                 break

        if final_graph_output_payload is None:
            print("Could not determine a specific 'final_result' or 'error_message' from the last graph state's nodes. Using the full last state 's' as fallback.")
            final_graph_output_payload = s 
            
    print("\n--- GRAPH'S FINAL OUTPUT PAYLOAD ---")
    # --- Save the 'final_result' content to a Markdown file ---
    content_to_save_to_file = None
    if isinstance(final_graph_output_payload, dict):
        content_to_save_to_file = final_graph_output_payload.get("final_result")

    if isinstance(content_to_save_to_file, str) and content_to_save_to_file:
        report_filename = "analysis_report.md" # Fixed filename
        try:
            with open(report_filename, "w", encoding="utf-8") as f:
                f.write(content_to_save_to_file)
            print(f"\n--- Report successfully saved to {report_filename} ---")
        except IOError as e:
            print(f"\n--- Error saving report to {report_filename}: {e} ---")
    else:
        if final_graph_output_payload is not None and not (isinstance(final_graph_output_payload, dict) and final_graph_output_payload.get("final_result")):
            print("\n--- 'final_result' not found or not a string in the output; report not saved. ---")
    # --- End of save report ---
 