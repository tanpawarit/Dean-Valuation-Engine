from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime 
from src.utils import logger
from src.agents.specialize_agent.constant import SPECIAIZE_AGENT_DESCRIPTIONS
 
 
class Planner:
    def __init__(self) -> None: 
        prompt_template_content = f"""You are a master financial analysis planner. Your goal is to break down a complex user request into a series of actionable, ordered steps.
            Each step must be assignable to one of the available specialized agents.
            Today's date is {{current_date}}. Ensure all analysis plans are relevant to this date.

            You have the following specialized agents at your disposal:
            1.  **GeneralAnalystAgent**:
                {SPECIAIZE_AGENT_DESCRIPTIONS["GeneralAnalystAgent"]}

            2.  **FinancialStrengthAnalystAgent**:
                {SPECIAIZE_AGENT_DESCRIPTIONS["FinancialStrengthAnalystAgent"]}

            3.  **BusinessAnalystAgent**:
                {SPECIAIZE_AGENT_DESCRIPTIONS["BusinessAnalystAgent"]}

            4.  **SummarizerAgent**:
                {SPECIAIZE_AGENT_DESCRIPTIONS["SummarizerAgent"]}

            **Instructions for Planning:**
            1.  **Understand the Request:** Carefully analyze the user's overall goal. Determine if the request is related to financial analysis or a general conversational query.
            2.  **Specialized Analysis Requests:**
                a.  **Break Down:** Decompose the specialized analysis request into logical sub-tasks.
                b.  **Assign Agents:** For each sub-task, identify the most appropriate agent from the list above.
                c.  **Order Tasks:** Ensure the tasks are in a logical sequence.
                d.  **Be Specific:** Clearly define what each task should achieve.
                e.  **Final Summary with SummarizerAgent:** If the plan involves ANY of the following specialized agents (FinancialStrengthAnalystAgent, BusinessAnalystAgent), then the VERY FINAL step in the plan MUST be assigned to the **SummarizerAgent**. The SummarizerAgent will use the original query and all outputs from previous steps to generate a comprehensive final answer. This applies even if there's only one specialized step before the summary.
            3.  **Non-Analytical/General Conversational Queries:**
                a.  If the user query is a general greeting, a simple question not requiring financial analysis (e.g., "hi how are you", "what's your name?"), or seems unrelated to your financial analysis capabilities (i.e., does NOT require FinancialStrengthAnalystAgent or BusinessAnalystAgent), create a single step plan.
                b.  This single step should be assigned to the **GeneralAnalystAgent** ONLY. Do NOT include a SummarizerAgent for these types of queries.
                c.  The task_description for this step should be the original user query, possibly with an instruction for the GeneralAnalystAgent to provide a polite, general response or acknowledge the query. For example: "User query: '{{user_input}}'. Provide a general acknowledgement or response."
            4.  **Output Format:** Respond ONLY with a valid JSON list of objects as described below. Do not include any other text before or after the JSON.
                Each object in the JSON list must have the following keys:
                * "step_id": (integer) A sequential identifier for the step, starting from 1.
                * "task_description": (string) A clear and concise description of what the agent needs to do for this step.
                * "assigned_agent": (string) The name of the agent to perform this task. Must be one of ["GeneralAnalystAgent", "FinancialStrengthAnalystAgent", "BusinessAnalystAgent", "SummarizerAgent"].

            User query: {{user_input}}

            Based on the user query, provide your plan as a JSON list of objects:
        """ 
        
        final_prompt_for_langchain: str = prompt_template_content.replace("{{current_date}}", "{current_date}").replace("{{user_input}}", "{user_input}")
        

        self.prompt = ChatPromptTemplate.from_template(final_prompt_for_langchain) 

        llm = ChatOpenAI(model="gpt-4o", temperature=0) 
        self.chain = self.prompt | llm | JsonOutputParser()

    def generate_plan(self, user_input: str) -> list:
        current_date = datetime.now().strftime("%Y-%m-%d")
        try:
            plan = self.chain.invoke({
                "user_input": user_input,
                "current_date": current_date
            })
            
            if isinstance(plan, list):
                if not plan: 
                    # TODO handle empty plan with fallback or none
                    pass # ถ้า plan ว่าง และ prompt ควรจะจัดการได้แล้ว ก็ปล่อยให้เป็น list ว่างได้
 
                required_keys: list[str] = ["step_id", "task_description", "assigned_agent"]
                for step_idx, step in enumerate(plan): # เพิ่ม step_idx สำหรับ error message
                    if not isinstance(step, dict):
                        logger.info(f"Planner output step {step_idx + 1} is not a dictionary: {step}")
                        raise ValueError(f"Invalid plan structure: step {step_idx + 1} is not a dictionary.")
                    if not all(key in step for key in required_keys):
                        logger.info(f"Planner output step {step_idx + 1} is missing required keys: {step}")
                        raise ValueError(f"Invalid plan structure: step {step_idx + 1} missing keys.")
                return plan  
            else:
                logger.info(f"Planner output was not a list of dicts as expected: {plan}") 
                return [{"step_id": 1, "task_description": f"Planner error: Output was not a list. Original query: {user_input}", "assigned_agent": "GeneralAnalystAgent"}]

        except Exception as e:
            logger.info(f"Error generating plan: {e}")
            return [{"step_id": 1, "task_description": f"Error in planning process. Original query: {user_input}", "assigned_agent": "GeneralAnalystAgent"}]