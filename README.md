# Analyst Robot: AI-Powered Financial & Business Analysis System

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-Framework-green)](https://github.com/langchain-ai/langchain)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange)](https://openai.com/)

## Overview

Analyst Robot is an advanced AI-powered system that performs comprehensive financial and business analysis using a multi-agent architecture. The system leverages large language models (LLMs) to analyze companies, generate insights, and provide detailed reports on business models, market sizing, and financial strength.

## Key Features

- **Multi-Agent Architecture**: Specialized agents work together to analyze different aspects of a company
- **Orchestrated Workflow**: Dynamic planning and execution using a graph-based workflow system
- **Specialized Analysis Capabilities**:
  - Business Model & Market Sizing Analysis
  - Financial Strength Analysis
  - Comprehensive Data Synthesis
- **Web Search Integration**: Real-time data collection for up-to-date analysis
- **Type-Safe Implementation**: Fully typed Python codebase with strict type checking

## System Architecture

```
analyst_robot/
├── src/
│   ├── agents/                 # Specialized AI agents
│   │   ├── specialize_agent/   # Domain-specific analysis agents
│   │   └── planner_agent.py    # Orchestration and planning
│   ├── graph_nodes/            # LangGraph workflow components
│   │   └── nodes/              # Individual workflow nodes
│   ├── tools/                  # External API integrations
│   │   └── search_tools.py     # Web search capabilities
│   └── utils/                  # Shared utilities
└── [additional project files]
```

## Technical Implementation

### Agent System

The project implements a sophisticated multi-agent system where each agent specializes in a specific domain of analysis:

- **Business Analyst Agent**: Analyzes business models, revenue streams, and market sizing
- **Financial Strength Analyst Agent**: Evaluates financial health through key metrics and ratios
- **Summarizer Agent**: Synthesizes outputs from multiple agents into coherent, actionable insights

Each agent is built using LangChain's agent framework with custom prompts engineered for specific analytical tasks.

### Workflow Orchestration

The system uses a graph-based workflow engine to:

1. Plan the analysis based on the user's query
2. Assign specialized agents to specific analytical tasks
3. Execute the plan in a coordinated sequence
4. Synthesize results into a comprehensive final report

This approach enables complex, multi-step analyses that combine insights from different analytical perspectives.

### Key Technologies

- **LangChain**: For agent construction and prompt engineering
- **OpenAI GPT-4**: Powers the core reasoning capabilities
- **LangGraph**: Orchestrates the multi-agent workflow
- **Type Hints**: Comprehensive typing for improved code quality and maintainability
- **Serper API**: Integration for real-time web search capabilities

## Development Practices

- **Type Safety**: Comprehensive type annotations throughout the codebase
- **Error Handling**: Robust error management for API calls and agent execution
- **Logging**: Detailed logging for debugging and monitoring
- **Modular Design**: Clean separation of concerns between agents, tools, and workflow

## Future Enhancements

- Integration with financial data APIs for direct access to company filings
- Expanded agent capabilities for technical analysis and competitive intelligence
- Interactive visualization of financial metrics and business insights
- Containerization for easy deployment and scaling

## Getting Started

### Prerequisites

- Python 3.10+
- OpenAI API key
- Serper API key for web search capabilities

### Installation

```bash
# Clone the repository
git clone https://github.com/tanpawarit/analyst_robot.git
cd analyst_robot

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies using uv
uv pip install -r requirements.txt

# Set up environment variables
export OPENAI_API_KEY="your_openai_api_key"
export SERPER_API_KEY="your_serper_api_key"
```

### Usage

```python
from src.agents.planner_agent import PlannerAgent
from src.graph_nodes.graph_state import PlanExecuteState

# Initialize the system
planner = PlannerAgent()

# Run an analysis
query = "Analyze the business model and financial strength of Tesla"
result = planner.create_and_execute_plan(query)

# Access the final analysis
print(result["final_result"])
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

*Developed by Pawarison Tanyu - A demonstration of advanced AI system design, LLM orchestration, and financial analysis capabilities.*