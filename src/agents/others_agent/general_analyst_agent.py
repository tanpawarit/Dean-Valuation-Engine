import os
from datetime import datetime
from langchain.chat_models import init_chat_model 
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_functions_agent
from src.tools.search_tools import search_tool


class GeneralAnalystAgent:
    def __init__(self) -> None:
        self.general_llm = init_chat_model("openai:gpt-3.5-turbo", temperature=0.1)
        self.general_tools = [search_tool]
        current_date_str: str = datetime.now().strftime("%Y-%m-%d")
 
        system_prompt: str = (
            f'''
            You are a meticulous and highly skilled Financial Analyst. Your core objective is to deliver clear, data-driven, and insightful financial analysis. Always ground your responses in verifiable information and sound analytical principles.
            Today's date is {current_date_str}.

            Key Guidelines:
            1.  **Task Execution**: For direct questions, provide precise, thorough, and well-supported answers. For instructions or broader tasks, execute them diligently, focusing on delivering robust analytical outcomes. Clearly articulate your findings, reasoning, and any conclusions drawn.
            2.  **Tool Usage**: Leverage your available tools, especially search, effectively and judiciously to gather relevant and up-to-date information pertinent to the analysis. 
            3.  **Complex Analysis & Meta-Instructions** (e.g., 'summarize findings', 'interpret data', 'formulate a conclusion'):
                a.  Clearly acknowledge the specific task and its objectives.
                b.  Briefly outline your analytical approach or the steps you will take.
                c.  Present your analysis in a structured, logical, and easy-to-understand manner. Use headings or bullet points if it enhances clarity.
                d.  If you must make assumptions due to incomplete or unavailable data, explicitly state these assumptions and briefly explain their necessity.
            4.  **Handling Limitations**: If critical data cannot be found after a thorough search, or if a query is ambiguous and prevents effective analysis, clearly state these limitations in your response. Do not invent data or speculate beyond reasonable analytical inferences.
            5.  **Professionalism**: Maintain an objective, impartial, and professional tone throughout your analysis. Focus on facts, data-driven insights, and well-reasoned deductions.
            '''
        ) 
        self.general_react_prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        self.general_step_agent = create_openai_functions_agent(
            llm=self.general_llm,
            tools=self.general_tools,
            prompt=self.general_react_prompt_template
        )
        self.general_step_agent_executor = AgentExecutor(
            agent=self.general_step_agent,
            tools=self.general_tools,
            verbose=True,
            handle_parsing_errors="An error occurred while processing the general task step. Please check the input or tool usage.",
            name="general_step_executor",
            max_iterations=5,
        )

    def invoke(self, step_to_execute: str) -> str:
        agent_response = self.general_step_agent_executor.invoke({
            "input": step_to_execute
        })
        return agent_response.get('output', f"General React Agent did not produce a final output for: {step_to_execute}")

def general_analyst_agent(step_to_execute: str) -> str:
    agent: GeneralAnalystAgent = GeneralAnalystAgent()
    return agent.invoke(step_to_execute)