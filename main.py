import os
import re
from typing import List, Dict, Optional, Literal, Any # Removed TypedDict as PlanExecuteState is imported
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
import json
from datetime import datetime
from src.tools.search_tools import search_tool
from src.utils import Config
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from langchain.agents import AgentExecutor, create_openai_functions_agent

 
from src.graph_nodes.graph_state import PlanExecuteState
from src.agents.registry import AGENT_REGISTRY  
from src.graph_nodes.executor_logic import executor_node
from src.graph_nodes.planner_logic import planner_node
from src.graph_nodes.conditional_logic import should_continue
from src.graph_nodes.state_handlers import handle_error_node, handle_success_node

all_configs = Config().get_config()

os.environ["OPENAI_API_KEY"] = all_configs['openai']['token']
os.environ["SERPER_API_KEY"] = all_configs['serper']['token']
   
# --- Construct the Graph ---
workflow: StateGraph = StateGraph(PlanExecuteState)

workflow.add_node("planner_node", planner_node)
workflow.add_node("executor_node", executor_node)
workflow.add_node("error_node", handle_error_node)
workflow.add_node("success_node", handle_success_node)

# Define the entry point
workflow.set_entry_point("planner_node")

# Define transitions
workflow.add_edge("planner_node", "executor_node") # Always try to execute after planning

workflow.add_conditional_edges(
    "executor_node",
    should_continue,
    {
        "executor_node": "executor_node", # Loop back to execute next step
        "end_graph_success": "success_node",   # Go to end if plan is complete
        "end_graph_error": "error_node"      # Go to error node if critical error
    }
)
workflow.add_edge("error_node", END)
workflow.add_edge("success_node", END)


# Compile the graph
app = workflow.compile()

# from IPython.display import Image, display

# display(Image(app.get_graph(xray=True).draw_mermaid_png()))

if __name__ == "__main__": 

    # initial_query = "Provide a comprehensive financial strength and business model analysis for Apple Inc. (AAPL)."
    initial_query = "What is the current D/E ratio for Microsoft?" # Test simpler query

    # initial_query = "hi there" # Test simpler query
    inputs: dict[str, str] = {"original_query": initial_query}
    
    print(f"\n--- Running Graph for Query: '{initial_query}' ---")
    final_state = None
    for s in app.stream(inputs, {"recursion_limit": 15}): # Added recursion_limit
        print(f"\n--- Current State Snapshot ---")
        # Filter out potentially very long outputs for snapshot printing
        for key, value in s.items():
            print(f"Graph Node: {key}")
            # print(f"State Values: {value}") # This can be very verbose
            if value:
                if 'executed_steps' in value and value['executed_steps']:
                    # Create a summary of executed steps instead of printing all details
                    summary_executed = []
                    for step in value['executed_steps']:
                        summary_executed.append({
                            'step_id': step.get('step_id'),
                            'assigned_agent': step.get('assigned_agent'),
                            'status': step.get('status'),
                            'output_snippet': str(step.get('output'))[:100] + "..." if step.get('output') else "N/A"
                        })
                    print(f"  Executed Steps Summary: {summary_executed}")
                if 'plan' in value and value['plan']:
                     print(f"  Plan: {value['plan']}")
                if 'current_step_index' in value:
                    print(f"  Current Step Index: {value['current_step_index']}")
                if 'final_result' in value:
                     print(f"  Final Result: {str(value['final_result'])[:500]}...")


        if END in s: # Check if it's the end state from a specific node
            final_state = s[END]
            break
        # If streaming directly the state changes without explicit END key from nodes
        # the last `s` before loop ends might be what you need, or `app.invoke`
        # For simplicity, let's try to get the last relevant state if END isn't directly keyed.
        # This part of LangGraph streaming can be tricky depending on exact graph structure.
        # Using app.invoke might be simpler if you don't need intermediate streaming.

    # If using app.invoke to get the final state directly:
    # final_state_invoke = app.invoke(inputs, {"recursion_limit": 15})
    # print("\n--- Final State from Invoke ---")
    # print(final_state_invoke)


    if not final_state: # Fallback if END key wasn't found, take the last `s` (which could be just one node's output)
        # This logic might need adjustment based on how your graph is truly structured to end
        # The 'success_node' and 'error_node' should ideally be the ones setting final_result
        print("END key not found in stream, inspecting last streamed state value if available from success/error nodes.")
        # The `s` in the loop is a dict where keys are node names and values are their outputs (which is a state dict)
        # We need to find the output of our designated end nodes.
        if 'success_node' in s:
            final_state = s['success_node']
        elif 'error_node' in s:
            final_state = s['error_node']
        else:
            print("Could not determine final state from stream.")


    print("\n--- FINAL RESULT ---")
    if final_state and isinstance(final_state, dict):
        if "final_result" in final_state:
            print(final_state["final_result"])
        elif "error_message" in final_state:
             print(f"Graph ended with an error: {final_state['error_message']}")
        else:
            print("Final result key not found in final state. Full final state:")
            print(final_state)

    elif final_state:
        print(final_state) # If it's not a dict as expected.
    else:
        print("No final state could be retrieved from the graph execution.")