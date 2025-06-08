from src.agents.planner_agent import Planner
from src.agents.other_agent.general_analyst_agent import GeneralAnalystAgent
from src.agents.specialize_agent import BusinessAnalystAgent, FinancialStrengthAnalystAgent, SummarizerAgent
from typing import Any

planner_agent: Planner = Planner()
general_analyst_agent: GeneralAnalystAgent = GeneralAnalystAgent()
financial_strength_analyst_agent: FinancialStrengthAnalystAgent = FinancialStrengthAnalystAgent()
business_analyst_agent: BusinessAnalystAgent = BusinessAnalystAgent()
summarizer_agent: SummarizerAgent = SummarizerAgent()

# Agent Registry specialized agents and others agents
AGENT_REGISTRY: dict[str, Any] = {
    "BusinessAnalystAgent": business_analyst_agent,
    "FinancialStrengthAnalystAgent": financial_strength_analyst_agent,
    "SummarizerAgent": summarizer_agent,
    "GeneralAnalystAgent": general_analyst_agent
}
