from src.graph_nodes.graph_state import PlanExecuteState
from typing import Optional

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
