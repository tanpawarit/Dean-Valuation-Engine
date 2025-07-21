from datetime import datetime
from typing import Any

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
from langchain_core.runnables import Runnable

from src.tools.search_tools import search_tool
from src.utils.openrouter_client import get_model_for_agent


class GeneralAnalystAgent:
    def __init__(self) -> None:
        self.general_llm: BaseChatModel = get_model_for_agent("general_analyst")
        self.general_tools: list[BaseTool] = [search_tool]
        current_date_str: str = datetime.now().strftime("%Y-%m-%d")

        system_prompt: str = f"""
            You are highly skilled Investment Analyst expert in general financial analysis. 
            If you are not sure about any detail in the data sources, **use your tools** to fetch or read the latest data and do NOT guess or make up facts. 
            You **MUST plan extensively** before each section of your analysis, and reflect on outcomes of any tool call before moving on. 
            Key Guidelines:
                1.  **Task Execution**: For direct questions, provide precise, thorough, and well-supported answers. For instructions or broader tasks, execute them diligently, focusing on delivering robust analytical outcomes. Clearly articulate your findings, reasoning, and any conclusions drawn.
                2.  **Tool Usage**: Leverage your available tools, especially search, effectively and judiciously to gather relevant and up-to-date information pertinent to the analysis. 

            ## Content Guidelines: 
            ### Depth and Breadth:
            - Aim for comprehensive coverage of each subsection 
            - Include definitions of key terms and concepts
            - Discuss current understanding and applications  
            - Address relationships between different concepts  
            - Add citations and link

            ### Structure:
            - Use hierarchical formatting with clear headings  
            - Use paragraphs to organize information logically  
            - Include transitional phrases between subsections  
            - no intro and conclusion

            ### Content Quality:
            - Prioritize accuracy and clarity  
            - Provide specific examples to illustrate concepts  
            - Include relevant data points, statistics, or findings when applicable  
            - Maintain an objective, scholarly tone  
            - Avoid oversimplification of topics  

            **Use only the most up-to-date sources as of {current_date_str}:** **Output no intros, no conclusions**
            """
        self.general_react_prompt_template: ChatPromptTemplate = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        self.general_step_agent: Runnable[Any, Any] = create_openai_tools_agent(
            llm=self.general_llm, tools=self.general_tools, prompt=self.general_react_prompt_template
        )
        self.general_step_agent_executor: AgentExecutor = AgentExecutor(
            agent=self.general_step_agent,
            tools=self.general_tools,
            verbose=True,
            handle_parsing_errors="An error occurred while processing the general task step. Please check the input or tool usage.",
            name="general_step_executor",
            max_iterations=5,
        )

    def invoke(self, step_to_execute: str) -> dict[str, str]:
        try:
            agent_response: dict[str, Any] = self.general_step_agent_executor.invoke({"input": step_to_execute})
            output_content = agent_response.get(
                "output", f"General React Agent did not produce a final output for: {step_to_execute}"
            )
            if not isinstance(output_content, str):
                output_content = str(output_content)
            return {"final_result": output_content}
        except Exception as e:
            return {"error_message": f"Error in GeneralAnalystAgent for task '{step_to_execute}': {e}"}


def general_analyst_agent(step_to_execute: str) -> dict[str, str]:
    agent: GeneralAnalystAgent = GeneralAnalystAgent()
    return agent.invoke(step_to_execute)
