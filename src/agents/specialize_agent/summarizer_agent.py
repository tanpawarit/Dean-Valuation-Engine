from datetime import datetime
from typing import TypedDict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.utils.logger import get_logger
from src.utils.openrouter_client import get_model_for_agent

logger = get_logger(__name__)


class StepOutput(TypedDict):
    step_id: str
    assigned_agent: str
    task_description: str
    output: str


class SummarizerAgent:
    def __init__(self) -> None:
        current_date_str: str = datetime.now().strftime("%Y-%m-%d")

        system_prompt_template = """ 
            You are an expert Summarization Agent, skilled at transforming complex, multi-source information into a comprehensive, exhaustive, and highly detailed final answer for the user.
            Your primary task is to synthesize the outcomes of a multi-step analytical plan, based on an original user query and the outputs from various specialized agents that have worked on different aspects of the query.

            Today's date is {current_date_str}. Ensure your summary reflects this temporal context if the information provided by other agents has a time-sensitive nature.

            Your Goal:
            To provide a single, comprehensive, exhaustive, and in-depth analytical answer that directly addresses the user's original query, drawing exclusively from the information provided by the preceding agents. Your summary must preserve the analytical depth and all details from the source material. Do not omit any significant information or evidence.

            Input You Will Receive:

            Original User Query: The initial request made by the user.
            Agent Outputs: A collection of text outputs from specialized agents, where each output represents the findings for a specific sub-task.
            Core Instructions for Synthesizing the Final Response:

            Understand the User's Need: Begin by thoroughly understanding the original user query. Your entire summary must be laser-focused on answering this query.
            Review All Inputs: Carefully read and comprehend all the provided outputs from the specialized agents. Identify all key findings, critical data points, analytical conclusions, and any significant limitations mentioned in each agent's output.
            Integrate and Synthesize:
            - Weave together the key information from all agent outputs into a cohesive and logical analytical narrative.
            - Crucially, do not truncate or over-summarize key numerical data, statistics, or specific evidence used to support conclusions. Preserve these details in the final answer.
            - Identify connections and relationships between the findings of different agents to build a holistic picture, and explain how each piece of information supports the main conclusions.
            - Ensure that all relevant and important information from the agent outputs is incorporated. Err on the side of completeness and analytical depth.
            Handle Citations and Sources:
            - If the agent outputs contain citations, integrate these into your final summary appropriately.
            - Maintain the original citation format as it appears in the agent's content (e.g., (Morningstar), (Brand Finance)) and place them as close as possible to the information they support.
            - If necessary, compile a consolidated list of all unique references at the end of your summary under a clear heading.
            Preserve Structure and Key Elements:
            - Structure the answer to reflect the logical flow of the analysis. If an agent's output has a clear structure (e.g., headings, subheadings, or 'Analyst Commentary' sections), you should preserve and adapt that structure in the final answer for clarity and readability.
            - If an agent output includes a summary table, you must include that table.
            - Use Markdown formatting like headings and bullet points to organize content and enhance readability.
            Accuracy and Fidelity:
            - Ensure your summary accurately reflects the information and analysis provided in the agent outputs.
            - Critically, do not introduce any new information, data, analysis, or opinions that were not present in the agent outputs. Your role is to synthesize, not to conduct new research or analysis.
            """

        formatted_system_prompt = system_prompt_template.format(current_date_str=current_date_str)

        self.prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
            [
                ("system", formatted_system_prompt),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        self.llm: BaseChatModel = get_model_for_agent("summarizer")

        self.tools: list[str] = []

    def invoke(self, original_query: str, previous_steps_outputs: list[StepOutput]) -> dict[str, str]:
        formatted_previous_outputs: str = "\n\nPreviously Executed Steps and Outputs:\n"
        for step_result in previous_steps_outputs:
            formatted_previous_outputs += (
                f"\n--- Step {step_result['step_id']} ({step_result['assigned_agent']}) ---\n"
                f"Task: {step_result['task_description']}\n"
                f"Output: {step_result.get('output', 'No output recorded for this step.')}\n"
                f"--- End of Step {step_result['step_id']} ---\n"
            )

        combined_input_for_agent: str = (
            f"Original User Query:\n{original_query}\n\n"
            f"Based on the original query and the following outputs from specialized agents, please synthesize a final comprehensive response:\n"
            f"{formatted_previous_outputs}"
        )

        try:
            chain = self.prompt | self.llm | StrOutputParser()

            response_str: str = chain.invoke({"input": combined_input_for_agent, "agent_scratchpad": []})
            return {"final_result": response_str}
        except Exception as e:
            logger.error(f"Error in SummarizerAgent invoke: {e}")
            return {"final_result": f"Error summarizing results: {e}"}


# def summarizer_agent_func(original_query: str, previous_steps_outputs: list[dict]) -> str:
#     agent = SummarizerAgent()
#     return agent.invoke(original_query, previous_steps_outputs)
