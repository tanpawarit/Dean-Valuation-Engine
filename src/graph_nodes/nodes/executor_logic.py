
from typing import List, Optional, Literal, Any
from src.agents.registry import AGENT_REGISTRY
from src.graph_nodes.graph_state import PlanExecuteState
from src.utils.logger import get_logger

logger = get_logger(__name__)

def executor_node(state: PlanExecuteState) -> dict[str, Any]:  
    logger.info(f"--- EXECUTOR ---")
    plan: List[dict] = state["plan"]
    current_step_idx: int = state["current_step_index"]
    executed_steps_history: List[dict] = state["executed_steps"]

    if current_step_idx >= len(plan):
        logger.info("Execution complete, no more steps in the plan.") 
        return {"error_message": "Execution attempted beyond plan length."}

    current_step_details: dict = plan[current_step_idx]
    task_description: str = current_step_details["task_description"]
    agent_name: str = current_step_details["assigned_agent"]
    logger.info(f"Executing Step {current_step_details['step_id']}: '{task_description}' with {agent_name}")

    agent_to_execute: Any | None = AGENT_REGISTRY.get(agent_name)
    
    # Initialize variables to store results for the current step
    step_output_content: Optional[dict[str, Any] | str] = None # Content of the output from the agent
    step_status: Literal["pending", "success", "error"] = "pending" # Will be 'success' or 'error'
    error_message_for_state: Optional[str] = None # Error message to be put into state.error_message if this step fails
    
    # Initialize new_final_result with the current value from the state.
    # This variable will hold the potential new final_result if SummarizerAgent runs.
    new_final_result: Optional[str] = state.get("final_result")

    if not agent_to_execute:
        logger.error(f"Error: Agent '{agent_name}' not found.")
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
                    logger.info(f"Output from {agent_name} (Summary): {summary_text[:200]}...")
                    step_output_content = raw_agent_output # Store the full dict as output for history
                    step_status = "success"
                    new_final_result = summary_text # Update potential new_final_result
                else:
                    summarizer_error_detail: str = f"SummarizerAgent output missing 'final_result' key. Output: {raw_agent_output}"
                    logger.error(f"Error: {summarizer_error_detail}")
                    step_output_content = {"error": summarizer_error_detail, "details": raw_agent_output}
                    step_status = "error"
                    error_message_for_state = "SummarizerAgent output error: Missing 'final_result' key."

            else:
                # Other agents take only the task description
                raw_agent_output = agent_to_execute.invoke(task_description)
                output_for_log: str = str(raw_agent_output)[:200]
                logger.info(f"Output from {agent_name}: {output_for_log}...")
                step_output_content = raw_agent_output # Store the direct output for history
                step_status = "success"
                
                # If this is the GeneralAnalystAgent and it's the only step in the plan,
                # set its output as the final result.
                if agent_name == "GeneralAnalystAgent" and len(plan) == 1:
                    if isinstance(raw_agent_output, str):
                        new_final_result = raw_agent_output
                        logger.info(f"GeneralAnalystAgent is the only step. Setting final_result: {str(new_final_result)[:200] if new_final_result is not None else 'None'}...")
                    elif isinstance(raw_agent_output, dict) and "response" in raw_agent_output: # Assuming GeneralAnalyst might return a dict
                        new_final_result = raw_agent_output["response"]
                        logger.info(f"GeneralAnalystAgent is the only step (from dict). Setting final_result: {str(new_final_result)[:200] if new_final_result is not None else 'None'}...")
                    # Add more conditions here if GeneralAnalystAgent can return other types

        except Exception as e:
            execution_error_detail: str = f"Error executing step with {agent_name}: {e}"
            logger.error(execution_error_detail)
            step_output_content = execution_error_detail # Error message for history
            step_status = "error"
            error_message_for_state = execution_error_detail # Error message for state

    # Construct the result for the current step to be added to history
    current_step_result_for_history = {
        **current_step_details, # Includes step_id, task_description, assigned_agent
        "output": step_output_content,
        "status": step_status
    }
    updated_executed_steps = executed_steps_history + [current_step_result_for_history]
    
    # Prepare the dictionary with only the changed parts of the state for returning 
    return_payload: dict[str, Any] = {
        "executed_steps": updated_executed_steps,
        "current_step_index": current_step_idx + 1,
        "error_message": error_message_for_state, # This will be the error message from this step or None
    }

    # (i.e., new_final_result is different from the final_result in the incoming state).
    # LangGraph will preserve the old value of 'final_result' if it's not in the payload.
    if new_final_result != state.get("final_result"):
        return_payload["final_result"] = new_final_result
        
    return return_payload