import os
from datetime import datetime
from langchain_openai import ChatOpenAI # หรือ init_chat_model ของคุณ
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

from src.utils import Config
all_configs = Config().get_config()
os.environ["OPENAI_API_KEY"] = all_configs['openai']['token'] 

class SummarizerAgent:
    def __init__(self) -> None:
        current_date_str: str = datetime.now().strftime("%Y-%m-%d")

        # 1. Define the system prompt template string
        system_prompt_template = (
            '''
            You are an expert Summarization Agent, skilled at transforming complex, multi-source information into a clear, concise, and actionable final answer for the user.
            Your primary task is to synthesize the outcomes of a multi-step analytical plan, based on an original user query and the outputs from various specialized agents that have worked on different aspects of the query.

            Today's date is {current_date_str}. Ensure your summary reflects this temporal context if the information provided by other agents has a time-sensitive nature.

            **Your Goal:**
            To provide a single, comprehensive, and coherent response that directly addresses the user's original query, drawing exclusively from the information provided by the preceding agents.

            **Input You Will Receive (as part of the human message):**
            1.  **Original User Query:** The initial request made by the user.
            2.  **Agent Outputs:** A collection of text outputs from specialized agents, where each output represents the findings for a specific sub-task in the overall plan.

            **Core Instructions for Synthesizing the Final Response:**
            1.  **Understand the User's Need:** Begin by thoroughly understanding the original user query. Your entire summary must be laser-focused on answering this query.
            2.  **Review All Inputs:** Carefully read and comprehend all the provided outputs from the specialized agents. Identify the key findings, critical data points, important conclusions, and any significant limitations or assumptions mentioned in each agent's output.
            3.  **Integrate and Synthesize:**
                * Weave together the key information from all agent outputs into a unified, logical, and flowing narrative. Do not simply list or concatenate the inputs.
                * Identify connections and relationships between the findings of different agents to build a holistic picture.
                * If different agents provide different facets of an answer to a single part of the query, combine them smoothly.
            4.  **Eliminate Redundancy and Irrelevance:**
                * Remove any repetitive information across agent outputs.
                * Omit any details from agent outputs that are not directly relevant to answering the original user query, unless they are crucial for context.
            5.  **Maintain Clarity, Conciseness, and Tone:**
                * Use clear, precise, and easily understandable language. Avoid jargon where possible, or briefly explain it if necessary.
                * Be comprehensive but also concise. Deliver all necessary information without unnecessary length.
                * Maintain a professional, objective, and helpful tone.
            6.  **Structure for Readability:** Organize the final summary in a way that is easy for the user to read and digest. Consider using:
                * A brief introductory sentence that frames the answer.
                * Logical paragraph breaks to separate distinct points or themes.
                * Bullet points for lists or key takeaways, if appropriate.
                * A concluding sentence if it adds value.
            7.  **Accuracy and Fidelity:**
                * Ensure your summary accurately reflects the information provided in the agent outputs.
                * **Crucially, do not introduce any new information, data, analysis, or opinions that were not present in the agent outputs.** Your role is to synthesize, not to conduct new research or analysis.
            8.  **Address Limitations:** If the agent outputs consistently highlight significant limitations or caveats that are critical for the user to understand the scope or certainty of the findings, briefly and clearly include these in your summary.

            You will receive the combined input as a human message. Your task is to generate the final synthesized response based on that input.
            '''
        )

        # 2. Format the system prompt with the current date
        formatted_system_prompt = system_prompt_template.format(current_date_str=current_date_str)
        # 3. Create ChatPromptTemplate
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", formatted_system_prompt),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # 4. Define LLM
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)

        # 5. Define Tools (empty for this agent)
        self.tools = []

        # The SummarizerAgent does not use tools, so no AgentExecutor is needed.
        # We will directly use the LLM with the prompt in the invoke method.
        pass

    def invoke(self, original_query: str, previous_steps_outputs: list[dict]) -> dict[str, str]:
        # เตรียม input string สำหรับ Agent เหมือนเดิม
        formatted_previous_outputs = "\n\nPreviously Executed Steps and Outputs:\n"
        for step_result in previous_steps_outputs:
            formatted_previous_outputs += (
                f"\n--- Step {step_result['step_id']} ({step_result['assigned_agent']}) ---\n"
                f"Task: {step_result['task_description']}\n"
                f"Output: {step_result.get('output', 'No output recorded for this step.')}\n"
                f"--- End of Step {step_result['step_id']} ---\n"
            )

        # Input ที่จะส่งให้ AgentExecutor จะอยู่ใน key "input"
        # ซึ่งจะถูก map เข้ากับ "{input}" ใน ChatPromptTemplate
        combined_input_for_agent = (
            f"Original User Query:\n{original_query}\n\n"
            f"Based on the original query and the following outputs from specialized agents, please synthesize a final comprehensive response:\n"
            f"{formatted_previous_outputs}"
        )

        try:
            # Create a chain with prompt, LLM, and an output parser
            chain = self.prompt | self.llm | StrOutputParser()

            # Invoke the chain
            # MessagesPlaceholder for "agent_scratchpad" needs to be provided,
            # even if empty for a non-tool-using agent.
            response_str = chain.invoke({
                "input": combined_input_for_agent,
                "agent_scratchpad": [] 
            })
            return {"final_result": response_str}
        except Exception as e:
            print(f"Error in SummarizerAgent invoke: {e}")
            return {"final_result": f"Error summarizing results: {e}"}

# def summarizer_agent_func(original_query: str, previous_steps_outputs: list[dict]) -> str:
#     agent = SummarizerAgent()
#     return agent.invoke(original_query, previous_steps_outputs)