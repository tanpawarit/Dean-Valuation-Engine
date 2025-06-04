from src.utils import load_app_config
from src.utils import setup_logging
from nemoguardrails import LLMRails, RailsConfig
load_app_config() # Load config and set ENV VARS FIRST
setup_logging()

from src.graph_nodes.graph_builder import build_graph
# from src.utils import load_app_config # Removed duplicate import
from langgraph.graph import END
 
# --- Construct the Graph ---
app = build_graph()

# --- Initialize NeMo Guardrails ---
guardrails_config = RailsConfig.from_path("src/guardrails/")
rails = LLMRails(config=guardrails_config)

# from IPython.display import Image, display
# display(Image(app.get_graph(xray=True).draw_mermaid_png()))

if __name__ == "__main__": 
    initial_query = "What is the current D/E ratio for Microsoft?" # Test simpler query
    inputs: dict[str, str] = {"original_query": initial_query}
    
    print(f"\n--- Running Graph for Query: '{initial_query}' ---")
    
    s = {} # To store the last state from the stream
    for s_item in app.stream(inputs, {"recursion_limit": 15}):
        print(f"\n--- Current State Snapshot ---")
        for key, value in s_item.items():
            print(f"Graph Node: {key}")
            if value and isinstance(value, dict): # Ensure value is a dict before accessing keys
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
        s = s_item 

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

    print(f"\n--- Attempting to Summarize Final Graph Output with NeMo Guardrails ---")
    text_to_summarize = None
    if s:
        for node_name, node_state in s.items():
            if isinstance(node_state, dict):
                if "final_output" in node_state and isinstance(node_state["final_output"], str) and node_state["final_output"]:
                    text_to_summarize = node_state["final_output"]
                    print(f"Using 'final_output' from node '{node_name}' for summarization.")
                    break
                elif "final_answer" in node_state and isinstance(node_state["final_answer"], str) and node_state["final_answer"]:
                    text_to_summarize = node_state["final_answer"]
                    print(f"Using 'final_answer' from node '{node_name}' for summarization.")
                    break
        
        if not text_to_summarize: 
            for node_name, node_state in s.items():
                if isinstance(node_state, dict):
                    for _key_in_node, val_in_node in node_state.items():
                        if isinstance(val_in_node, str) and len(val_in_node) > 50: 
                            text_to_summarize = val_in_node
                            print(f"Using content from node '{node_name}', key '{_key_in_node}' as fallback for summarization.")
                            break
                if text_to_summarize:
                    break
        
        if not text_to_summarize: 
            print("Could not find a specific text field in the last state. Summarizing string representation of the entire last state 's'.")
            text_to_summarize = str(s)
    else:
        print("No final state 's' from graph stream to use for summarization.")

    if text_to_summarize:
        print_snippet = text_to_summarize[:1000] + ("..." if len(text_to_summarize) > 1000 else "")
        print(f"\nContent to be summarized (snippet):\n---\n{print_snippet}\n---")
        try:
            guardrail_result = rails.generate(prompt=text_to_summarize) 
            print("\n--- Guardrails Summary Result ---")
            if isinstance(guardrail_result, str): 
                print(guardrail_result)
            else: 
                print("Guardrails did not return the expected string format.")
                print(f"Raw guardrails output: {guardrail_result}")
        except Exception as e:
            print(f"Error during NeMo Guardrails summarization: {e}")
    else:
        print("No text found or generated to summarize.")

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
    if final_graph_output_payload is not None:
        print(final_graph_output_payload)
    else:
        print("No final output payload could be determined from the graph execution.")