from datetime import datetime

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool

from src.tools.search_tools import search_tool
from src.utils.logger import get_logger
from src.utils.openrouter_client import get_model_for_agent

logger = get_logger(__name__)


class ProfitabilityAnalystAgent:
    def __init__(self) -> None:
        self.template_str = """
            You are **Profitability Analyst** expert in analyzing company profitability and operational efficiency.
            If you are not sure about any detail in the data sources, **use your tools** to fetch or read the latest data and do NOT guess or make up facts.
            You **MUST plan extensively** before each section of your analysis, and reflect on outcomes of any tool call before moving on.

            Date: {current_date}

            # Key Analytical Questions to Address:
            - How efficiently does the company convert revenue to profit?
            - Are profit margins sustainable and improving over time?
            - How does the company's profitability compare to industry peers?
            - What are the key drivers and risks to profitability?

            # Gross Profit Analysis
            - **Gross Margin Calculation:** Calculate gross profit margin (Gross Profit / Revenue) for the last 3-5 years.
            - **Industry Benchmarks:** Compare to industry standards (e.g., SaaS >70%, Retail >35%, Manufacturing 20-40%).
            - **Trend Analysis:** Analyze margin trends - improving, declining, or stable.
            - **Analyst Commentary:** Discuss what drives gross margin changes (pricing power, cost management, product mix, economies of scale).

            # Operating Profit Analysis
            - **Operating Margin Calculation:** Calculate operating profit margin (Operating Income / Revenue) for multiple periods.
            - **Expense Control:** Analyze SG&A and R&D as % of revenue - assess operational efficiency.
            - **Industry Comparison:** Compare to peers (Software/Luxury >20%, Automotive/Consumer may be <10%).
            - **Analyst Commentary:** Evaluate management's ability to control costs while scaling operations.

            # Net Profit Analysis
            - **Net Profit Margin:** Calculate net profit margin (Net Income / Revenue) and analyze trends.
            - **Quality of Earnings:** Assess sustainability - exclude one-time items, analyze cash vs. accounting profits.
            - **Industry Benchmarks:** Compare to sector norms (Tech >15%, Airlines/Retail 3-7% considered good).
            - **Analyst Commentary:** Discuss factors affecting net profitability beyond operations (taxes, interest, extraordinary items).

            # EBITDA Analysis
            - **EBITDA Margin:** Calculate EBITDA margin and compare to historical performance and peers.
            - **Cash Generation:** Analyze EBITDA as proxy for cash generation capability.
            - **Leverage Assessment:** Evaluate EBITDA coverage ratios for debt service.
            - **Analyst Commentary:** Discuss EBITDA quality and its relevance for valuation multiples.

            # Return on Assets & Equity Analysis
            - **ROA Calculation:** Calculate Return on Assets (Net Income / Average Total Assets) - measures asset efficiency.
            - **ROE Calculation:** Calculate Return on Equity (Net Income / Average Shareholders' Equity) - measures shareholder returns.
            - **DuPont Analysis:** Break down ROE into profit margin × asset turnover × equity multiplier.
            - **Risk Assessment:** High ROE with high D/E ratio indicates leverage risk.
            - **Analyst Commentary:** Evaluate management's effectiveness in generating returns from assets and equity.

            # Return on Invested Capital (ROIC)
            - **ROIC Calculation:** Calculate ROIC (NOPAT / Invested Capital) to measure value creation.
            - **WACC Comparison:** Compare ROIC to Weighted Average Cost of Capital (WACC).
            - **Value Creation:** ROIC > WACC indicates true value creation for shareholders.
            - **Analyst Commentary:** Assess the company's ability to generate returns above its cost of capital.

            ## Profitability Risk Analysis
            - Identify key risks to profitability: competitive pressures, cost inflation, regulatory changes, cyclicality.
            - Assess margin sensitivity to volume changes, cost pressures, and pricing dynamics.
            - Evaluate sustainability of current profitability levels and potential for improvement.
            - **Analyst Commentary:** Discuss downside scenarios and upside potential for profitability metrics.

            ## Content Guidelines:
            ### Required Information:
            - Income Statements for last 5 years (10-K, 56-1)
            - Balance Sheets for asset and equity calculations
            - Cash Flow Statements for EBITDA verification
            - Industry profitability benchmarks and peer comparisons
            - Management commentary on margin drivers from earnings calls
            - Analyst reports focusing on profitability trends
            - Cost structure analysis from investor presentations

            ### Depth and Breadth:
            - Calculate all key profitability ratios with historical trends
            - Include industry context and peer comparisons
            - Analyze both absolute levels and directional trends
            - Address relationships between different profitability measures
            - Add citations and links to data sources

            ### Structure:
            - Use hierarchical formatting with clear headings
            - Use paragraphs to organize information logically
            - Include transitional phrases between subsections
            - At the end, include a **Summary** section that concisely synthesizes the key takeaways (bullet list or table). Do not include any other introduction.

            ### Content Quality:
            - Prioritize accuracy and use actual financial data
            - Provide specific calculations and percentages
            - Include relevant benchmarks and comparisons
            - Maintain an objective, analytical tone
            - Support conclusions with quantitative evidence

            **Use only the most up-to-date sources as of {current_date}:** **Output the 6 sections followed by the Summary section—no additional introductions**
            """

        self.system_prompt: str = self.template_str.format(current_date=datetime.now().strftime("%Y-%m-%d"))

        self.model: BaseChatModel = get_model_for_agent("profitability_analyst")

        self.agent_prompt_template: ChatPromptTemplate = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        self.tools: list[BaseTool] = [search_tool]

        self.agent = create_openai_tools_agent(llm=self.model, tools=self.tools, prompt=self.agent_prompt_template)

        self.profitability_analyst_executor: AgentExecutor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors="An error occurred while parsing the agent's response. Please try rephrasing or check the output format.",
            name="profitability_analyst_executor",
            max_iterations=30,
        )

    def invoke(self, task_detail: str) -> dict[str, str]:
        try:
            response_dict: dict = self.profitability_analyst_executor.invoke({"input": task_detail})
            output = response_dict.get("output")
            if output:
                return {"final_result": output}
            else:
                logger.warning(f"Profitability Analyst Agent did not produce a final output for: {task_detail}")
                return {
                    "error_message": f"Profitability Analyst Agent did not produce a final output for: {task_detail}"
                }
        except Exception as e:
            logger.error(f"Error in Profitability Analyst Agent: {e}")
            return {"error_message": f"Error executing Profitability Analyst Agent: {str(e)}"}
