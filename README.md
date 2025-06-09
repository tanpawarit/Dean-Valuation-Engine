# Analyst Robot: AI-Powered Financial & Business Analysis System

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-Framework-green)](https://github.com/langchain-ai/langchain)
[![LangGraph](https://img.shields.io/badge/LangGraph-Framework-purple)](https://github.com/langchain-ai/langgraph)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange)](https://openai.com/)
[![NemoGuardrails](https://img.shields.io/badge/NemoGuardrails-Framework-purple)](https://github.com/NVIDIA/NeMo-Guardrails)

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

- **OpenAI**: Powers the core reasoning capabilities
- **LangChain**: For agent construction and prompt engineering
- **LangGraph**: Orchestrates the multi-agent workflow 
- **Spacy**: For NLP tasks (guardrails)
- **Serper API**: Integration for real-time web search capabilities

## Development Practices

- **Type Safety**: Comprehensive type annotations throughout the codebase
- **Error Handling**: Robust error management for API calls and agent execution
- **Logging**: Detailed logging for debugging and monitoring
- **Modular Design**: Clean separation of concerns between agents, tools, and workflow

## Future Enhancements
- Specialized AI for Guidance Analysis and Narrative Generation (ongoing)
- Add guardrails for ethical and responsible AI use (e.g., bias mitigation, data privacy, content moderation) (ongoing)
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

1. Ensure you have Python 3.10+ and [uv](https://github.com/astral-sh/uv) installed:
   ```bash
   pip install uv
   ```

2. Install project dependencies using `uv`:
   ```bash
   uv pip install -r pyproject.toml
   ```

3. (Recommended) Create and activate a virtual environment:
   ```bash
   uv venv .venv
   source .venv/bin/activate
   uv pip install -r pyproject.toml
   ```

4. Download the required spaCy language model:
   ```bash
   python -m spacy download en_core_web_sm
   ```


## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

*Developed by Pawarison Tanyu - A demonstration of advanced AI system design, LLM orchestration, and financial analysis capabilities.*