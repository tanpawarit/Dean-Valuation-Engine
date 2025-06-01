import os
from datetime import datetime
from src.utils import Config # Assuming this is correctly defined elsewhere
from langchain.chat_models import init_chat_model # Assuming this is correctly defined elsewhere
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_functions_agent
from src.tools.search_tools import search_tool

all_configs = Config().get_config()

os.environ["OPENAI_API_KEY"] = all_configs['openai']['token']
if all_configs['serper']['token']:
    os.environ["SERPER_API_KEY"] = all_configs['serper']['token']

class BusinessAnalystAgent:
    def __init__(self) -> None:
        self.template_str = (
            '''   
            You are **Business Analyst** expert in business-model and market-sizing analysis.   
            If you are not sure about any detail in the data sources, **use your tools** to fetch or read the latest data and do NOT guess or make up facts.  
            You **MUST plan extensively** before each section of your analysis, and reflect on outcomes of any tool call before moving on.  

            Date: {current_date}
        
            # Core Business Model  
            - **Products/Services:** Briefly describe what the company sells or provides (apps, platforms, financial services, logistics, etc.).  
            - **Business Model Type:** Classify as Marketplace, B2B SaaS, D2C, Subscription-based, On-demand, etc.  
            - **Analyst Commentary:** Explain why this model makes the company competitive or where risks lie. 

            # Revenue Breakdown  
            - List each major product/service line with its **% of total revenue**.  
            - **Analyst Commentary:** Discuss what this mix means for growth prospects and margin stability.

            # Revenue Consistency  
            - Is revenue **cyclical** or **recurring**?  
            - Are there any **seasonal** or **economic-cycle** dependencies?  
            - **Analyst Commentary:** Evaluate how these patterns impact valuation and forecasting.

            # Business Category  
            - Classify as **Growth** (high-expansion, e.g. EV, AI, Healthtech) or **Defensive** (stable, e.g. Utilities, Consumer Staples).  
            - **Analyst Commentary:** Justify the classification and its implications for portfolio allocation.
        
            # Market Sizing Analysis
            - **TAM (Total Addressable Market):** Describe the total market demand your company could serve if there were no constraints on reach or resources.
            - **SAM (Serviceable Available Market):** Define the portion of the TAM that your company can realistically serve today given its current capabilities and geographic reach.
            - **SOM (Serviceable Obtainable Market):** State the share of the SAM that your company is currently capturing.

            if High SOM:
            - **Expansion Opportunities:** Identify adjacent customer segments or new geographies (e.g., international markets, verticals) you could pursue to grow share.
            - **Analyst Commentary:** Explain why these expansion moves make strategic sense and what resources or partnerships would be required.

            if Low SOM:
            - **Growth Potential:** Assess your competitive advantages (e.g., technology, pricing, brand) and latent market demand to project potential share gains.
            - **Analyst Commentary:** Discuss which levers (marketing, product features, distribution) will drive that growth.
        
            ## Content Guidelines:
            ### Required Information:
            - Annual Reports (10-K, 56-1)
            - Analyst Reports (Equity Research)
            - Latest Investor Presentation
            - Quarterly revenue compared to economic cycles
            - Market size data from reference sources such as McKinsey, Statista, and Gartner
            - Market share figures from industry reports
            - Reports from competitors within the same industry
        
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

            **Use only the most up-to-date sources as of {current_date}:** **Output only the 4 sections—no intros, no conclusions**
            '''
        )

        self.system_prompt = self.template_str.format(
            current_date=datetime.now().strftime("%Y-%m-%d")
        )

        self.model = init_chat_model(
            "openai:gpt-4.1", 
            temperature=0.1
        )
 
        self.agent_prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        self.tools = [search_tool] 
        
        self.agent = create_openai_functions_agent(llm=self.model, tools=self.tools, prompt=self.agent_prompt_template)

        self.business_analyst_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True, 
            handle_parsing_errors="An error occurred while parsing the agent's response. Please try rephrasing or check the output format.",
            name="business_analyst_executor",
            max_iterations=30, 
        )

    def invoke(self, task_detail: str) -> str:
        try:
            response_dict = self.business_analyst_executor.invoke({
                "input": task_detail
            })
            return response_dict.get('output', f"Business Analyst Agent did not produce a final output for: {task_detail}")
        except Exception as e:
            print(f"Error in Business Analyst Agent: {e}")
            return f"Error executing Business Analyst Agent: {e}"

# def business_analyst_agent(task_detail: str) -> str:
#     agent: BusinessAnalystAgent = BusinessAnalystAgent()
#     return agent.invoke(task_detail)