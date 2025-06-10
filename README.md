# Analyst Robot: AI-Powered Financial & Business Analysis System

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-Framework-green)](https://github.com/langchain-ai/langchain)
[![LangGraph](https://img.shields.io/badge/LangGraph-Framework-purple)](https://github.com/langchain-ai/langgraph)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange)](https://openai.com/) 

## Overview: Your AI Co-Pilot for Deep Analysis 🚀

Ever wished for an tireless, expert analyst by your side, capable of dissecting complex business landscapes and financial statements in minutes? **Analyst Robot is here!** This isn't just another AI tool; it's a sophisticated, multi-agent system designed to be your intelligent partner in financial and business analysis. Leveraging the cutting-edge power of Large Language Models (LLMs), Analyst Robot dives deep into company data, market trends, and financial health, emerging with crystal-clear insights and comprehensive reports. Get ready to unlock a new level of understanding!

## Table of Contents

- [Features](#features)
- [Sample Analysis Output](#sample-analysis-output)
- [System Architecture](#system-architecture)
- [Technical Deep Dive](#technical-deep-dive)
- [Logging & Guardrails](#logging--guardrails)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Developer Guide](#developer-guide)
- [Testing](#testing)
- [License](#license)

## Key Features: What Makes Analyst Robot Scream-Worthy! 🌟

- **🤖 Symphony of Specialized Agents**: Imagine a dream team of AI analysts! Each agent is a master of its domain (business models, financial health, market trends), collaborating to provide a holistic view.
- **📈 Dynamic Graph-Powered Orchestration**: No rigid scripts here! Analyst Robot uses a flexible, graph-based system (LangGraph) to plan and execute complex analyses dynamically, adapting to the unique needs of each query.
- **🎯 Pinpoint Analysis Capabilities**:
    - **Business Model & Market Sizing Mastery**: Uncover the DNA of a company's success and its true market potential.
    - **Financial X-Ray Vision**: Deep dive into financial statements to assess strength, stability, and future outlook.
    - **Insight Synthesis Engine**: Transforms raw data and individual findings into coherent, actionable intelligence.
- **🌐 Real-Time Web Intelligence**: Stale data? Not on our watch! Integrated web search (via Serper API) ensures your analysis is fueled by the latest information.
- **🛡️ Rock-Solid & Type-Safe**: Built with Python and meticulous type-hinting, ensuring robustness, maintainability, and fewer surprises.
- **✍️ Detailed Execution Logging**: Transparent and detailed logging of every step in the analysis graph, perfect for understanding, debugging, and auditing. (Thanks, `src/utils/graph_logger.py`!)

## Sample Analysis Output
#TODO add flow graph

## System Architecture: A Symphony of AI Agents 🚀

Analyst Robot isn't just a program; it's a sophisticated ecosystem of intelligent agents working in concert, orchestrated by a dynamic graph-based workflow. Imagine a team of expert analysts, each a master of their domain, collaborating seamlessly to deliver profound insights. That's the power of Analyst Robot.

Here's a glimpse into its inner workings:

```
analyst_robot/
├── src/
│   ├── agents/                 # 🧠 The Brains: Specialized AI Agents
│   │   ├── planner_agent.py    # 🗺️ The Master Orchestrator: Plans and directs analysis
│   │   ├── specialize_agent/   # 🕵️‍♂️ Domain Experts: Deep-dive analysis (Business, Financial, etc.)
│   │   ├── other_agent/        # 🧩 Utility Agents: Supporting analytical tasks
│   │   ├── registry.py         # 📚 Agent Directory: Keeps track of available agents
│   │   └── constant.py         # ⚙️ Agent Configuration Constants
│   │
│   ├── graph_nodes/            # 🔗 The Workflow Engine: LangGraph Components
│   │   ├── graph_builder.py    # 🏗️ The Architect: Constructs the analysis workflow
│   │   ├── graph_state.py      # 💾 Shared Memory: Manages state across the workflow
│   │   └── nodes/              # 🧩 Action Blocks: Individual steps in the analysis graph
│   │
│   ├── tools/                  # 🛠️ The Toolkit: External Integrations & Capabilities
│   │   ├── search_tools.py     # 🌐 Web Intelligence: Real-time data via Serper API
│   │   └── web_loader_tools.py # 📄 Content Fetchers: Grabs and processes web content
│   │
│   ├── utils/                  # 🔧 Utility Belt: Shared Helpers & Configuration
│   │   ├── config_manager.py   # 🔑 Secrets & Settings: Manages API keys and configurations
│   │   ├── graph_logger.py     # 📊 Execution Insights: Detailed logging of graph operations
│   │   └── logger.py           # 📝 General Scribe: System-wide logging
│   │
│   ├── guardrails/             # 🛡️ Ethical Compass: Ensuring Responsible AI
│   │   ├── prompt_injection.py # 🛡️ Detects & Mitigates Prompt Injection Attempts
│   │   ├── sensitive_info.py   # 🤫 Identifies & Redacts Sensitive Information (PII)
│   │   └── guardrail_manager.py# 🚦 Orchestrates Guardrail Checks
│
├── pyproject.toml              # 📦 Project Dependencies & Configuration (uv) 
├── main.py                     # 🚀 Entry Point: Kicks off the analysis
└── README.md                   # 🕮 You are here!
```

**Core Principles:**

1.  **Agent Specialization:** At the heart of Analyst Robot are highly specialized agents. The `PlannerAgent` acts as the conductor, interpreting user requests and devising a strategic plan. It then delegates tasks to `SpecializeAgent`s, such as:
    *   **BusinessModelAnalyst:** Dissects business models, revenue streams, and market positioning.
    *   **FinancialStrengthAnalyst:** Scrutinizes financial health, ratios, and stability. 

2.  **Dynamic Workflow Orchestration (LangGraph):** Forget static scripts! Analyst Robot uses `LangGraph` to build and execute dynamic workflows.
    *   The `GraphBuilder` constructs a stateful graph where each `Node` represents a specific action (e.g., run an agent, search the web, process data).
    *   `GraphState` ensures information flows smoothly between nodes, allowing for complex, multi-step reasoning.
    *   This graph-based approach allows for conditional logic, retries, and parallel execution, making the analysis robust and adaptable.

3.  **Data-Driven Insights (Tools):** Agents are empowered by a suite of `Tools`.
    *   `SearchTools` (leveraging Serper API) provide access to real-time web data, ensuring analyses are current and comprehensive.
    *   `WebLoaderTools` fetch and prepare online content for agent consumption.

4.  **Robust Foundation (Utils & Guardrails):**
    *   `ConfigManager` securely handles sensitive information like API keys.
    *   Comprehensive logging (`GraphLogger`, `Logger`) provides transparency and aids in debugging.
    *   The `Guardrails` system aims to ensure ethical, unbiased, and responsible AI outputs.

This architecture allows Analyst Robot to tackle complex analytical challenges with a level of depth and dynamism previously unattainable. It's not just about processing data; it's about generating genuine understanding.

## Technical Deep Dive: How the Magic Happens 🛠️

Analyst Robot's power stems from a carefully crafted architecture, blending specialized AI agents with a dynamic workflow engine. (Refer to the [System Architecture](#system-architecture) diagram for a visual map!)

### The Agentic Powerhouse

The core of Analyst Robot is its multi-agent system, primarily managed within the `src/agents/` directory:
- **`PlannerAgent` (The Conductor)**: This crucial agent, located in `planner_agent.py`, receives the user's request. It then formulates a strategic plan, deciding which specialized agents are needed and in what order they should run. Think of it as the project manager for the AI team.
- **`SpecializeAgent`s (The Experts)**: Housed in `src/agents/specialize_agent/`, these are the domain gurus. Examples include:
    - *BusinessModelAnalyst*: Focuses on understanding a company's operational strategy, revenue generation, and market positioning.
    - *FinancialStrengthAnalyst*: Dives into financial statements, calculating key ratios and assessing overall fiscal health.
    Each agent leverages LangChain for its core logic, equipped with custom-engineered prompts tailored for its specific analytical tasks. The `agents/registry.py` helps in managing and accessing these specialized agents.

### Dynamic Workflow Orchestration with LangGraph

Static, predefined workflows are too limiting for complex analysis. That's where LangGraph, managed in `src/graph_nodes/`, shines:
- **`GraphBuilder` (`graph_builder.py`)**: This module is responsible for constructing the actual execution graph. Based on the `PlannerAgent`'s strategy, it dynamically assembles a series of `Nodes` (from `src/graph_nodes/nodes/`).
- **`GraphState` (`graph_state.py`)**: This defines the shared "memory" or state that is passed between nodes in the graph. It allows information, partial results, and context to flow seamlessly through the analysis pipeline.
- **Nodes**: Each node in the graph represents a specific task – invoking an agent, calling a tool (like web search), processing data, or making a decision. This modularity allows for incredible flexibility and the ability to create sophisticated, multi-step reasoning chains.

### Empowering Tools & Utilities

- **Real-Time Data Acquisition (`src/tools/`)**:
    - `search_tools.py`: Integrates with the Serper API, providing agents with the ability to perform real-time web searches for the most up-to-date information.
    - `web_loader_tools.py`: Fetches and preprocesses content from URLs, making it ready for agent analysis.
- **Robust Foundation (`src/utils/`)**:
    - `config_manager.py`: Securely manages API keys (OpenAI, Serper) and other configurations.
    - `logger.py` & `graph_logger.py`: Provide comprehensive logging. `graph_logger.py` is particularly vital, offering detailed insights into the execution of each node and the overall state of the LangGraph workflow, which is invaluable for debugging and understanding the system's behavior (this logs to `graph_execution_details.log`).

### Key Technologies Fueling the Robot

- **🧠 OpenAI (GPT models)**: The powerhouse behind the agents' reasoning, understanding, and generation capabilities.
- **🔗 LangChain**: The foundational framework for building agents, managing prompts, and structuring interactions with LLMs.
- **📈 LangGraph**: The engine for orchestrating the complex, stateful, multi-agent workflows.
- **🌐 Serper API**: The gateway to real-time web search, keeping analyses fresh and relevant.
- **🔒 Python 3.10+ with Full Type Hinting**: Ensures code clarity, robustness, and easier maintenance.
- **🛡️ spaCy**: Utilized for NLP tasks, potentially within the `guardrails` system for content analysis or PII detection.

## Logging & Guardrails: Transparency and Responsibility 🛡️📊

Understanding what the Analyst Robot is doing and ensuring it operates responsibly are paramount.

### Comprehensive Logging

- **General System Logs (`src/utils/logger.py`)**: Captures broad operational information, errors, and system events.
- **Detailed Graph Execution Logs (`src/utils/graph_logger.py`)**: This is where the magic of the workflow becomes transparent! This module provides meticulous JSON Lines logs (`graph_execution_details.log`) for each graph run. It records:
    - A unique `run_id` for each analysis.
    - The state *before* and *after* each node in the LangGraph executes.
    - The outputs or errors generated by each node.
    - Graph start and end times.
    This granular logging is indispensable for debugging, performance analysis, and auditing the decision-making process of the AI.

### Ethical Guardrails (`src/guardrails/`): Building Trust & Safety

Analyst Robot is engineered with a strong commitment to responsible AI. The `src/guardrails/` directory houses critical components designed to ensure safe and ethical operation, managed by the `guardrail_manager.py`:

- **🛡️ Prompt Injection Defense (`prompt_injection.py`)**: Actively works to detect and neutralize attempts to manipulate the LLM's behavior through malicious inputs. This helps maintain the integrity and intended focus of the analysis.
- **🤫 Sensitive Information (PII) Detection & Redaction (`sensitive_info.py`)**: Scans inputs and potential outputs for Personally Identifiable Information (PII) and other sensitive data. Detected information can be flagged or redacted to protect user privacy and comply with data protection standards. (Leverages spaCy for some NLP-based detection).

**Ongoing Development & Future Goals:**
While the current guardrails provide a strong foundation, we are continuously working to enhance them. Future aspirations include more sophisticated mechanisms for:
- **Bias Mitigation**: Developing techniques to identify and reduce potential biases in analytical outputs.
- **Content Moderation**: Expanding checks to prevent the generation of inappropriate or harmful content beyond PII and prompt injections.
- **Factual Accuracy Enhancement**: Implementing more robust cross-referencing and validation techniques.

Building trust and ensuring the reliability of AI-generated insights is a top priority.

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