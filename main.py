import os
import re
from typing import TypedDict, List, Dict, Optional
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

from src.agents.specialize_agent import BusinessAnalystAgent, FinancialStrengthAnalystAgent, SummarizerAgent
from src.agents.planner_agent import Planner
from src.agents.general_analyst_agent import GeneralAnalystAgent

all_configs = Config().get_config()

os.environ["OPENAI_API_KEY"] = all_configs['openai']['token']
os.environ["SERPER_API_KEY"] = all_configs['serper']['token']

class PlanExecuteState(TypedDict):
    original_query: str
    plan: List[dict] # List of {"step_id": ..., "task_description": ..., "assigned_agent": ...}
    executed_steps: List[dict] # List of {"step_id": ..., "task_description": ..., "assigned_agent": ..., "output": ...}
    current_step_index: int # To keep track of which step in the plan to execute next
    error_message: Optional[str] # To store any error messages
    final_result: Optional[str] # To store the final summarized result

planner_agent = Planner()
general_analyst_agent = GeneralAnalystAgent()
financial_strength_analyst_agent = FinancialStrengthAnalystAgent()
business_analyst_agent = BusinessAnalystAgent()
summarizer_agent = SummarizerAgent()

AGENT_REGISTRY = {
    "BusinessAnalystAgent": business_analyst_agent,
    "FinancialStrengthAnalystAgent": financial_strength_analyst_agent, 
    "SummarizerAgent": summarizer_agent,
    "GeneralAnalystAgent": general_analyst_agent,
} 
 
def planner_node(state: PlanExecuteState) -> PlanExecuteState:
    print("--- PLANNER ---")
    query = state["original_query"]
    plan = planner_agent.generate_plan(query)
    print(f"Generated Plan: {plan}")
    return {
        "plan": plan,
        "current_step_index": 0,
        "executed_steps": [],
        "error_message": None,
        "final_result": None
    }

def executor_node(state: PlanExecuteState) -> PlanExecuteState:
    print(f"--- EXECUTOR ---")
    plan = state["plan"]
    current_step_idx = state["current_step_index"]
    executed_steps_history = state["executed_steps"]

    if current_step_idx >= len(plan):
        print("Execution complete, no more steps in the plan.")
        return {"error_message": "Execution attempted beyond plan length."} # Should be caught by conditional edge

    current_step_details = plan[current_step_idx]
    task_description = current_step_details["task_description"]
    agent_name = current_step_details["assigned_agent"]
    print(f"Executing Step {current_step_details['step_id']}: '{task_description}' with {agent_name}")

    agent_to_execute = AGENT_REGISTRY.get(agent_name)

    if not agent_to_execute:
        print(f"Error: Agent '{agent_name}' not found.")
        output = f"Error: Agent '{agent_name}' not found for task: {task_description}"
        step_result = {**current_step_details, "output": output, "status": "error"}
    else:
        try:
            if agent_name == "SummarizerAgent":
                # SummarizerAgent needs the original query and all previous executed steps
                output = agent_to_execute.invoke(
                    original_query=state["original_query"],
                    previous_steps_outputs=executed_steps_history # Pass history
                )
            else:
                # Other agents take only the task description
                raw_output = agent_to_execute.invoke(task_description)
                output_for_log = str(raw_output)[:200] # Assuming other agents return string or convertible
                output_for_step = raw_output

            # Handle output for logging and step result
            if agent_name == "SummarizerAgent":
                # 'output' from SummarizerAgent is a dict like {"final_result": "summary"}
                summary_text = output.get("final_result", "Error: Summarizer did not produce final_result key.")
                print(f"Output from {agent_name} (Summary): {summary_text[:200]}...")
                step_result = {**current_step_details, "output": output, "status": "success"}
                # Set the final_result in the state directly here
                state["final_result"] = summary_text 
            else:
                print(f"Output from {agent_name}: {output_for_log}...")
                step_result = {**current_step_details, "output": output_for_step, "status": "success"}

        except Exception as e:
            print(f"Error executing step with {agent_name}: {e}")
            error_output_msg = f"Error during execution by {agent_name}: {str(e)}"
            step_result = {**current_step_details, "output": error_output_msg, "status": "error"}
            # Optionally, set an error message in the state for replanning or specific handling
            # return {"error_message": f"Failed at step {current_step_details['step_id']} with {agent_name}"}

    updated_executed_steps = executed_steps_history + [step_result]
    
    # Prepare the dictionary to be returned for state update
    current_final_result = state.get("final_result") # Preserve existing final_result if any

    update_dict: PlanExecuteState = {
        "original_query": state["original_query"],
        "plan": state["plan"],
        "executed_steps": updated_executed_steps,
        "current_step_index": current_step_idx + 1,
        "error_message": None if step_result["status"] == "success" else step_result["output"],
        "final_result": current_final_result # Start with existing or None
    }

    # If SummarizerAgent just ran and successfully produced a summary, update final_result
    if agent_name == "SummarizerAgent" and step_result["status"] == "success":
        # 'output' from SummarizerAgent is a dict like {"final_result": "summary"}
        # This was already set in state["final_result"] = summary_text earlier in the try block
        # So, we ensure it's correctly propagated from the state which was updated in the try block.
        update_dict["final_result"] = state.get("final_result")
    
    return update_dict
    


# --- 4. Define Edges (Conditional Logic) ---
def should_continue(state: PlanExecuteState) -> str:
    error_msg = state.get("error_message")
    if error_msg and isinstance(error_msg, str) and "Could not generate a valid plan" in error_msg:
        print("Critical error: Could not generate a valid plan. Ending.")
        return "end_graph_error" # Special end node for critical planner failure
    if error_msg: # If an executor step failed
        print(f"Error encountered: {error_msg}. Considering replan or end.")
        # Simple strategy: end on error. Could add a "replan" branch here.
        return "end_graph_error" # Or a new node for error handling/replanning
    
    current_step_idx = state["current_step_index"]
    if current_step_idx >= len(state["plan"]):
        print("Plan complete.")
        return "end_graph_success"
    return "executor_node"


# --- 5. Construct the Graph ---
workflow = StateGraph(PlanExecuteState)

workflow.add_node("planner_node", planner_node)
workflow.add_node("executor_node", executor_node)
workflow.add_node("error_node", lambda state: {"final_result": f"Graph ended with error: {state.get('error_message', 'Unknown error')}", "error_message": state.get("error_message", "Unknown error")}) # A simple error end node
workflow.add_node("success_node", lambda state: {"final_result": state.get("final_result") if state.get("final_result") else "Plan finished successfully, but no specific final result was set in the state."}) # Success node

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
    # Ensure OPENAI_API_KEY and SERPER_API_KEY (if used by tools) are set in environment
    # Example: os.environ["OPENAI_API_KEY"] = "your_key"
    #          os.environ["SERPER_API_KEY"] = "your_key" (if search_tool uses it)
    
    initial_query = "Provide a comprehensive financial strength and business model analysis for Apple Inc. (AAPL)."
    # initial_query = "What is the current D/E ratio for Microsoft?" # Test simpler query

    inputs = {"original_query": initial_query}
    
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