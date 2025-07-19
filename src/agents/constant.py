SPECIAIZE_AGENT_DESCRIPTIONS: dict[str, str] = {
    "GeneralAnalystAgent": (
        "* Expertise: Provides comprehensive and insightful general financial analysis. Can answer broad questions, "
        "perform initial research, summarize findings, and interpret data.\n"
        "* Tools: Search.\n"
        "* Use when: General financial questions, initial data gathering, or tasks not fitting other specialists."
    ),
    "FinancialStrengthAnalystAgent": (
        "* Expertise: Deep dives into financial strength analysis. Focuses on Debt-to-Equity (D/E), "
        "Current/Quick Ratios, Free Cash Flow (FCF), and FCF Margin.\n"
        "* Tools: Search.\n"
        "* Use when: Detailed analysis of a company's financial leverage, liquidity, and cash flow generation capabilities is required.\n"
        "* Keywords: financial strength, debt-to-equity, D/E ratio, debt ratio, liquidity, cash flow, free cash flow, FCF, "
        "current ratio, quick ratio, leverage, solvency, balance sheet strength, financial health, financial metrics"
    ),
    "BusinessAnalystAgent": (
        "* Expertise: Analyzes business models, revenue breakdowns, revenue consistency, "
        "business categories (Growth vs. Defensive), and market sizing (TAM, SAM, SOM).\n"
        "* Tools: Search.\n"
        "* Use when: Understanding a company's core operations, revenue streams, market position, and growth potential is required.\n"
        "* Keywords: business model, revenue breakdown, revenue streams, market sizing, TAM, SAM, SOM, market analysis, "
        "core operations, business strategy, market position, competitive positioning, market opportunity, total addressable market"
    ),
    "GrowthAnalystAgent": (
        "* Expertise: Analyzes growth metrics, including Revenue CAGR, EPS Growth, and FCF Growth. "
        "Focuses on evaluating the quality of earnings and the company's reinvestment strategies.\n"
        "* Tools: Search.\n"
        "* Use when: Detailed analysis of a company's growth potential is required.\n"
        "* Keywords: growth analysis, growth potential, CAGR, revenue growth, EPS growth, earnings growth, "
        "FCF growth, growth metrics, expansion rate, growth drivers, growth strategy, growth forecast"
    ),
    "SummarizerAgent": (
        "* Expertise: Combines and synthesizes results from specialized agents to create a coherent and comprehensive final answer "
        "for the user, based on the original user query and the collected agent outputs.\n"
        "* Tools: None (relies on text inputs from other agents).\n"
        "* Use when: This should typically be the **final step** in any plan that requires synthesizing information from "
        "multiple preceding analytical steps to provide a complete answer to the user."
    ),
    "MoatAnalystAgent": (
        "* Expertise: Analyzes a company's economic moat, including definitions, current understanding, applications, "
        "and relationships between relevant concepts.\n"
        "* Tools: Search.\n"
        "* Use when: Understanding a company's competitive advantage, barriers to entry, and sustainable competitive position is required.\n"
        "* Keywords: moat, economic moat, competitive advantage, competitive edge, barriers to entry, sustainable advantage, "
        "competitive position, competitive moat, competitive analysis, competitive landscape, defensive moat, competitive strength"
    ),
}
