import os
from datetime import datetime
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chat_models import init_chat_model
from langchain.agents import AgentExecutor, create_openai_functions_agent 
from langchain_core.tools import BaseTool
import os
from datetime import datetime

from src.tools.search_tools import search_tool
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MoatAnalystAgent:
    def __init__(self) -> None:
        self.template_str = (
            '''
            You are a **Fundamental Analyst** expert in Competitive Advantage and Moat Analysis.
            If you are not sure about any detail in the data sources, **use your tools** to fetch or read the latest data and do NOT guess or make up facts.
            You **MUST plan extensively** before each section of your analysis, and reflect on outcomes of any tool call before moving on.

            Date: {current_date}

            # Competitive Advantage (Moat) Analysis
            ## Identifying the Source of Competitive Advantage (Moat)
            Analyze the company to determine if it possesses one or more of the following economic moats. Provide evidence and reasoning for each potential moat.
                - **Brand Power:** Does the company have strong brand recognition that allows for premium pricing or inspires high customer loyalty (e.g., high repeat purchase rates)? Compare its branding and pricing power against key competitors.
                - **Network Effect:** Does the value of the company's product or service increase as more people use it? Analyze user growth, engagement metrics, and how the network creates a barrier to entry for new competitors.
                - **High Switching Costs:** How difficult or costly is it for customers to switch to a competitor? Evaluate factors like technological integration (e.g., B2B SaaS, ERP), data migration challenges, and customer churn rates.
                - **Cost Advantage:** Does the company operate at a structurally lower cost than its rivals? Investigate sources such as economies of scale, proprietary processes, superior supply chain management, or access to unique resources. Analyze Gross and Operating Margins relative to the industry average.
                - **Intangible Assets (e.g., Intellectual Property, Regulatory Licenses):** Does the company hold critical patents, proprietary technology, know-how, or government-approved licenses that are difficult for competitors to replicate?
                **Analyst Commentary:** Summarize which moat(s), if any, the company possesses. Assess the strength and durability of each identified moat, explaining why it provides a sustainable competitive advantage. If no moat is identified, explain the company's competitive vulnerabilities.

            ## Market Share and Competitive Positioning
            Evaluate the company's position within its industry.
                - **Market Share Analysis:** What is the company's current market share, and what has been its trend over the past 3-5 years? Is it a dominant market leader, a significant player, a challenger, or a niche operator?
                - **Profitability of Market Leadership:** Analyze the relationship between the company's market share and its profitability (Gross Margin, Operating Margin). Is market share growth accompanied by strong or improving margins, or is it being "bought" through price cuts and lower profitability?
                **Analyst Commentary:** Conclude on the company's market position. Does its market share and profitability trend confirm the existence of a strong moat? Or does it suggest a highly competitive environment where leadership is fragile?

            ## Industry Structure and Competitive Landscape
            Analyze the characteristics of the industry in which the company operates.
                - **Industry Type (e.g., Winner-Takes-Most vs. Fragmented):** Is the industry structured in a way that a few players capture most of the profits (e.g., Cloud Computing, Logistics), or can local leaders thrive without national dominance (e.g., Regional Banking, Utilities)?
                - **Market Concentration and Competition:** How concentrated is the market? Identify the main competitors and their relative sizes. Is the industry an oligopoly, or is it highly fragmented and competitive?
                - **Barriers to Entry:** Assess the overall barriers to entry for new potential competitors. How do these barriers relate to the company's specific moat?
                **Analyst Commentary:** Provide an assessment of the industry's overall attractiveness. How does the industry structure impact the company's ability to sustain its moat and profitability over the long term? Is the company well-positioned to succeed within this specific competitive landscape?

            ## Overall Moat Assessment and Outlook
            Synthesize the findings from all previous sections to provide a final, conclusive judgment.
                - **Moat Verdict:** State clearly whether the company possesses a clear, sustainable economic moat.
                - **Moat Source Identification:** Explicitly name the primary type(s) of moat identified (Brand, Network, Switching Cost, Cost Advantage, or Intangible Assets).
                - **Synthesis of Moat and Market Position:** Connect the identified moat to the company's market share. Explain how its structural advantages (or lack thereof) translate into its market position and growth.
                - **Long-Term Profitability Outlook:** Based on the strength of the moat, its market leadership, and the industry characteristics, provide an outlook on the company's ability to generate consistent, long-term profits. If the moat and market share are strong, explain how this creates a high probability of durable profitability, even in a changing market environment.

            ## Content Guidelines:
            ### Required Information:
            - Annual Reports (10-K, 56-1) and Investor Presentations
            - Equity Research Reports and Strategic Business News (e.g., Bloomberg, Reuters)
            - Industry and Market Share Reports (from sources like Statista, IBISWorld, McKinsey, Gartner)
            - Financial Statements (Income Statement, Balance Sheet) for competitor comparisons

            ### Depth and Breadth:
            - Aim for comprehensive coverage of each subsection
            - Include definitions of key terms and concepts
            - Discuss current understanding and applications
            - Address relationships between different concepts
            - Add citations and links

            ### Structure:
            - Use hierarchical formatting with clear headings
            - Use paragraphs to organize information logically
            - Include transitional phrases between subsections
            - At the end, include a **Summary** section that concisely synthesizes the key takeaways (bullet list or table). Do not include any other introduction.

            ### Content Quality:
            - Prioritize accuracy and clarity
            - Provide specific examples to illustrate concepts
            - Include relevant data points, statistics, or findings when applicable
            - Maintain an objective, scholarly tone
            - Avoid oversimplification of topics

            **Use only the most up-to-date sources as of {current_date}:** **Output all analytical sections followed by the Summary section—no additional introductions**
            '''
        )

        self.system_prompt: str = self.template_str.format(
            current_date=datetime.now().strftime("%Y-%m-%d")
        )

        self.model: BaseChatModel = init_chat_model(
            "openai:gpt-4.1",
            temperature=0.1
        )

        self.agent_prompt_template: ChatPromptTemplate = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        self.tools: list[BaseTool] = [search_tool]

        self.agent = create_openai_functions_agent(llm=self.model, tools=self.tools, prompt=self.agent_prompt_template)

        self.moat_analyst_executor: AgentExecutor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors="An error occurred while parsing the agent's response. Please try rephrasing or check the output format.",
            name="moat_analyst_executor",
            max_iterations=30,
        )

    def invoke(self, task_detail: str) -> dict[str, str]:
        try:
            response_dict: dict = self.moat_analyst_executor.invoke({
                "input": task_detail
            })
            output = response_dict.get('output')
            if output:
                return {"final_result": output}
            else:
                logger.warning(f"Moat Analyst Agent did not produce a final output for: {task_detail}")
                return {"error_message": f"Moat Analyst Agent did not produce a final output for: {task_detail}"}
        except Exception as e:
            logger.error(f"Error in Moat Analyst Agent: {e}")
            return {"error_message": f"Error executing Growth Analyst Agent: {str(e)}"}
 