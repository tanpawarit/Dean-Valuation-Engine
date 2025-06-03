import os
import re
from typing import TypedDict, List, Dict, Optional, Literal, Any
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
from src.agents.others_agent.general_analyst_agent import GeneralAnalystAgent

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

AGENT_REGISTRY: dict[str, Any] = {
    "BusinessAnalystAgent": business_analyst_agent,
    "FinancialStrengthAnalystAgent": financial_strength_analyst_agent, 
    "SummarizerAgent": summarizer_agent,
    "GeneralAnalystAgent": general_analyst_agent,
} 
 
def planner_node(state: PlanExecuteState) -> PlanExecuteState:
    print("--- PLANNER ---")
    query: str = state["original_query"]
    plan = planner_agent.generate_plan(query)
    print(f"Generated Plan: {plan}")
    return {
        "plan": plan,
        "current_step_index": 0,
        "executed_steps": [],
        "error_message": None,
        "final_result": None
    }

def executor_node(state: PlanExecuteState) -> dict:  
    print(f"--- EXECUTOR ---")
    plan: List[dict] = state["plan"]
    current_step_idx: int = state["current_step_index"]
    executed_steps_history: List[dict] = state["executed_steps"]

    if current_step_idx >= len(plan):
        print("Execution complete, no more steps in the plan.") 
        return {"error_message": "Execution attempted beyond plan length."}

    current_step_details: dict = plan[current_step_idx]
    task_description: str = current_step_details["task_description"]
    agent_name: str = current_step_details["assigned_agent"]
    print(f"Executing Step {current_step_details['step_id']}: '{task_description}' with {agent_name}")

    agent_to_execute: Any | None = AGENT_REGISTRY.get(agent_name)
    
    # Initialize variables to store results for the current step
    step_output_content: Optional[dict[str, Any] | str] = None # Content of the output from the agent
    step_status: Literal["pending", "success", "error"] = "pending" # Will be 'success' or 'error'
    error_message_for_state: Optional[str] = None # Error message to be put into state.error_message if this step fails
    
    # Initialize new_final_result with the current value from the state.
    # This variable will hold the potential new final_result if SummarizerAgent runs.
    new_final_result: Optional[str] = state.get("final_result")

    if not agent_to_execute:
        print(f"Error: Agent '{agent_name}' not found.")
        step_output_content = f"Error: Agent '{agent_name}' not found for task: {task_description}"
        step_status = "error"
        error_message_for_state = step_output_content
    else:
        try:
            if agent_name == "SummarizerAgent":
                # SummarizerAgent needs the original query and all previous executed steps
                raw_agent_output = agent_to_execute.invoke(
                    original_query=state["original_query"],
                    previous_steps_outputs=executed_steps_history
                )
                # 'raw_agent_output' from SummarizerAgent is expected to be a dict like {"final_result": "summary"}
                summary_text = raw_agent_output.get("final_result")
                if summary_text is not None:
                    print(f"Output from {agent_name} (Summary): {summary_text[:200]}...")
                    step_output_content = raw_agent_output # Store the full dict as output for history
                    step_status = "success"
                    new_final_result = summary_text # Update potential new_final_result
                else:
                    error_detail: str = f"SummarizerAgent output missing 'final_result' key. Output: {raw_agent_output}"
                    print(f"Error: {error_detail}")
                    step_output_content = {"error": error_detail, "details": raw_agent_output}
                    step_status = "error"
                    error_message_for_state = "SummarizerAgent output error: Missing 'final_result' key."

            else:
                # Other agents take only the task description
                raw_agent_output = agent_to_execute.invoke(task_description)
                output_for_log: str = str(raw_agent_output)[:200]
                print(f"Output from {agent_name}: {output_for_log}...")
                step_output_content = raw_agent_output # Store the direct output for history
                step_status = "success"
                
                # If this is the GeneralAnalystAgent and it's the only step in the plan,
                # set its output as the final result.
                if agent_name == "GeneralAnalystAgent" and len(plan) == 1:
                    if isinstance(raw_agent_output, str):
                        new_final_result = raw_agent_output
                        print(f"GeneralAnalystAgent is the only step. Setting final_result: {str(new_final_result)[:200] if new_final_result is not None else 'None'}...")
                    elif isinstance(raw_agent_output, dict) and "response" in raw_agent_output: # Assuming GeneralAnalyst might return a dict
                        new_final_result = raw_agent_output["response"]
                        print(f"GeneralAnalystAgent is the only step (from dict). Setting final_result: {str(new_final_result)[:200] if new_final_result is not None else 'None'}...")
                    # Add more conditions here if GeneralAnalystAgent can return other types

        except Exception as e:
            error_detail: str = f"Error executing step with {agent_name}: {e}"
            print(error_detail)
            step_output_content = error_detail # Error message for history
            step_status = "error"
            error_message_for_state = error_detail # Error message for state

    # Construct the result for the current step to be added to history
    current_step_result_for_history = {
        **current_step_details, # Includes step_id, task_description, assigned_agent
        "output": step_output_content,
        "status": step_status
    }
    updated_executed_steps = executed_steps_history + [current_step_result_for_history]
    
    # Prepare the dictionary with only the changed parts of the state for returning
    # Note: `Dict` is already imported from `typing`.
    return_payload: Dict[str, any] = {
        "executed_steps": updated_executed_steps,
        "current_step_index": current_step_idx + 1,
        "error_message": error_message_for_state, # This will be the error message from this step or None
    }

    # (i.e., new_final_result is different from the final_result in the incoming state).
    # LangGraph will preserve the old value of 'final_result' if it's not in the payload.
    if new_final_result != state.get("final_result"):
        return_payload["final_result"] = new_final_result
        
    return return_payload
    


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


def handle_error_node(state: PlanExecuteState) -> dict:
    '''
    Handles the state update for the error_node.
    Sets a final_result indicating an error and preserves the error_message.
    '''
    error_message = state.get('error_message', 'Any error')
    print(f'--- ERROR NODE: Graph ended with error: {error_message} ---')
    return {
        'final_result': f'Graph ended with error: {error_message}',
        'error_message': error_message
    }

def handle_success_node(state: PlanExecuteState) -> dict:
    '''
    Handles the state update for the success_node.
    Sets the final_result based on what's in the state, or a default success message.
    '''
    final_result: Optional[str] = state.get('final_result')
    if final_result:
        print(f'--- SUCCESS NODE: Plan finished. Final Result: {str(final_result)[:200]}... ---')
        return {'final_result': final_result}
    else:
        success_message = 'Plan finished successfully, but no specific final result was set in the state.'
        print(f'--- SUCCESS NODE: {success_message} ---')
        return {'final_result': success_message}

# --- 5. Construct the Graph ---
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
    # initial_query = "What is the current D/E ratio for Microsoft?" # Test simpler query

    initial_query = "hi there" # Test simpler query
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