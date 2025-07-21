from functools import lru_cache


# Lazy loading agent registry
class AgentRegistry:
    """Lazy loading registry for agent instances."""

    @staticmethod
    @lru_cache(maxsize=1)
    def get_planner():
        from src.agents.planner_agent import Planner

        return Planner()

    @staticmethod
    @lru_cache(maxsize=1)
    def get_general_analyst():
        from src.agents.other_agent.general_analyst_agent import GeneralAnalystAgent

        return GeneralAnalystAgent()

    @staticmethod
    @lru_cache(maxsize=1)
    def get_business_analyst():
        from src.agents.specialize_agent.business_analyst_agent import BusinessAnalystAgent

        return BusinessAnalystAgent()

    @staticmethod
    @lru_cache(maxsize=1)
    def get_financial_strength_analyst():
        from src.agents.specialize_agent.financial_strength_analyst_agent import FinancialStrengthAnalystAgent

        return FinancialStrengthAnalystAgent()

    @staticmethod
    @lru_cache(maxsize=1)
    def get_growth_analyst():
        from src.agents.specialize_agent.growth_analyst_agent import GrowthAnalystAgent

        return GrowthAnalystAgent()

    @staticmethod
    @lru_cache(maxsize=1)
    def get_summarizer():
        from src.agents.specialize_agent.summarizer_agent import SummarizerAgent

        return SummarizerAgent()

    @staticmethod
    @lru_cache(maxsize=1)
    def get_moat_analyst():
        from src.agents.specialize_agent.moat_analyst_agent import MoatAnalystAgent

        return MoatAnalystAgent()

    @staticmethod
    @lru_cache(maxsize=1)
    def get_profitability_analyst():
        from src.agents.specialize_agent.profitability_analyst_agent import ProfitabilityAnalystAgent

        return ProfitabilityAnalystAgent()


# Agent Registry with lazy loading
AGENT_REGISTRY = {
    "BusinessAnalystAgent": lambda: AgentRegistry.get_business_analyst(),
    "FinancialStrengthAnalystAgent": lambda: AgentRegistry.get_financial_strength_analyst(),
    "GrowthAnalystAgent": lambda: AgentRegistry.get_growth_analyst(),
    "SummarizerAgent": lambda: AgentRegistry.get_summarizer(),
    "GeneralAnalystAgent": lambda: AgentRegistry.get_general_analyst(),
    "MoatAnalystAgent": lambda: AgentRegistry.get_moat_analyst(),
    "ProfitabilityAnalystAgent": lambda: AgentRegistry.get_profitability_analyst(),
}


# Planner agent (used separately)
def planner_agent():
    return AgentRegistry.get_planner()
