from datetime import datetime
from typing import Any

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.agents.constant import SPECIAIZE_AGENT_DESCRIPTIONS
from src.utils.logger import get_logger
from src.utils.openrouter_client import get_model_for_agent

logger = get_logger(__name__)


class Planner:
    def __init__(self) -> None:
        # Dynamically generate the agent descriptions string
        agent_descriptions_string: str = ""
        for i, (agent_name, description) in enumerate(SPECIAIZE_AGENT_DESCRIPTIONS.items()):
            agent_descriptions_string += f"{i + 1}.  **{agent_name}**:\n                {description}\n\n"

        # Dynamically extract keywords from agent descriptions
        keyword_mappings = {}
        for agent_name, description in SPECIAIZE_AGENT_DESCRIPTIONS.items():
            if agent_name not in ["GeneralAnalystAgent", "SummarizerAgent"]:
                # Extract keywords from the description
                keywords = []
                if "* Keywords:" in description:
                    keywords_section = description.split("* Keywords:")[1].split("\n")[0]
                    keywords = [kw.strip() for kw in keywords_section.split(",") if kw.strip()]
                keyword_mappings[agent_name] = keywords

        # Build dynamic keyword triggers section
        keyword_triggers_section = ""
        for agent_name, keywords in keyword_mappings.items():
            if keywords:
                keyword_list = ", ".join(keywords)
                keyword_triggers_section += f"**{agent_name} triggers:** {keyword_list}\n\n"

        # Dynamically generate the list of agent names for the prompt
        agent_names_list_string: str = ", ".join([f'"{name}"' for name in SPECIAIZE_AGENT_DESCRIPTIONS.keys()])

        # Dynamically generate the list of specialized agent names for the SummarizerAgent instruction
        specialized_agent_names: list[str] = [
            name
            for name in SPECIAIZE_AGENT_DESCRIPTIONS.keys()
            if name not in ["GeneralAnalystAgent", "SummarizerAgent"]
        ]
        specialized_agent_names_string: str = ", ".join(specialized_agent_names)

        prompt_template_content = f"""You are a master financial analysis planner. Your goal is to break down a complex user request into a series of actionable, ordered steps.
            Each step must be assignable to one of the available specialized agents.
            Today's date is {{current_date}}. Ensure all analysis plans are relevant to this date.

            You have the following specialized agents at your disposal:
            {agent_descriptions_string}

            **Instructions for Planning:**
            1.  **Understand the Request:** Carefully analyze the user's overall goal. Determine if the request is related to financial analysis or a general conversational query.
            
            2.  **Dynamic Keyword-Based Agent Assignment:**
                Before classifying as a general query, check for keywords from each specialized agent. Use the following keyword mappings:
                
{keyword_triggers_section}
            
            3.  **Specialized Analysis Requests:**
                a.  **Keyword Match:** Scan the user query for keywords from any specialized agent's domain. If keywords are found, assign to the corresponding agent.
                b.  **Context Analysis:** Even if keywords aren't an exact match, analyze the context to determine if the request falls within a specialized agent's expertise.
                c.  **Broad Matching:** Consider partial keyword matches and synonyms. For example:
                   - "business model", "business analysis", "business strategy" → BusinessAnalystAgent
                   - "moat", "competitive advantage", "competitive position" → MoatAnalystAgent
                   - "growth", "expansion", "development" → GrowthAnalystAgent
                   - "financial", "balance sheet", "cash flow" → FinancialStrengthAnalystAgent
                c.  **Break Down:** Decompose complex requests into logical sub-tasks.
                d.  **Assign Agents:** For each sub-task, identify the most appropriate agent based on keywords and context.
                e.  **Order Tasks:** Ensure tasks are in logical sequence.
                f.  **Final Summary with SummarizerAgent:** If the plan involves ANY of the following specialized agents ({specialized_agent_names_string}), then the VERY FINAL step MUST be assigned to the **SummarizerAgent**.
            
            4.  **General Conversational Queries:**
                a.  Only assign to **GeneralAnalystAgent** if NO keywords from specialized agents are detected AND the query is clearly general in nature.
                b.  Examples of general queries: greetings, simple questions not requiring financial analysis, or queries unrelated to the specialized domains above.
                c.  The task_description should be: "User query: '{{user_input}}'."
            4.  **Analytics Task that is not fit for specialized agents:**
                a.  This single step should be assigned to the **GeneralAnalystAgent** ONLY.
                b.  The task_description for this step should be the original user query, possibly with an instruction for the GeneralAnalystAgent to provide a polite response. For example: "User query: '{{user_input}}'."
            5.  **Output Format:** Respond ONLY with a valid JSON list of objects as described below. Do not include any other text before or after the JSON.
                Each object in the JSON list must have the following keys:
                * "step_id": (integer) A sequential identifier for the step, starting from 1.
                * "task_description": (string) A clear and concise description of what the agent needs to do for this step.
                * "assigned_agent": (string) The name of the agent to perform this task. Must be one of [{agent_names_list_string}].

            User query: {{user_input}}

            Based on the user query, provide your plan as a JSON list of objects:
        """

        final_prompt_for_langchain: str = prompt_template_content.replace("{{current_date}}", "{current_date}").replace(
            "{{user_input}}", "{user_input}"
        )

        self.prompt: ChatPromptTemplate = ChatPromptTemplate.from_template(final_prompt_for_langchain)

        llm = get_model_for_agent("planner")
        self.chain = self.prompt | llm | JsonOutputParser()

    def generate_plan(self, user_input: str) -> list[dict[str, Any]]:
        current_date: str = datetime.now().strftime("%Y-%m-%d")
        try:
            plan: list[dict[str, Any]] = self.chain.invoke({"user_input": user_input, "current_date": current_date})

            if isinstance(plan, list):
                if not plan:
                    # handle empty plan with fallback or none
                    pass  # ถ้า plan ว่าง และ prompt ควรจะจัดการได้แล้ว ก็ปล่อยให้เป็น list ว่างได้

                required_keys: list[str] = ["step_id", "task_description", "assigned_agent"]
                for step_idx, step in enumerate(plan):  # เพิ่ม step_idx สำหรับ error message
                    if not isinstance(step, dict):
                        logger.info(f"Planner output step {step_idx + 1} is not a dictionary: {step}")
                        raise ValueError(f"Invalid plan structure: step {step_idx + 1} is not a dictionary.")
                    if not all(key in step for key in required_keys):
                        logger.info(f"Planner output step {step_idx + 1} is missing required keys: {step}")
                        raise ValueError(f"Invalid plan structure: step {step_idx + 1} missing keys.")
                return plan
            else:
                logger.info(f"Planner output was not a list of dicts as expected: {plan}")
                return [
                    {
                        "step_id": 1,
                        "task_description": f"Planner error: Output was not a list. Original query: {user_input}",
                        "assigned_agent": "GeneralAnalystAgent",
                    }
                ]

        except Exception as e:
            logger.info(f"Error generating plan: {e}")
            return [
                {
                    "step_id": 1,
                    "task_description": f"Error in planning process. Original query: {user_input}",
                    "assigned_agent": "GeneralAnalystAgent",
                }
            ]
