# Analyst Robot

An intelligent agent system for automated data analysis and processing.

## Project Structure

```
.
├── src/                    # Source code directory
│   ├── agents/            # AI agent implementations
│   │   ├── project_manager.py    # Project management and coordination
│   │   ├── qa_team/             # Quality assurance team agents
│   │   ├── business_analyst_team/ # Business analysis specialists
│   │   └── fundamental_analyst_team/ # Fundamental analysis experts
│   ├── utils/             # Helper functions and utilities
│   │   ├── config.py      # Configuration management
│   │   ├── logger.py      # Logging system
│   │   ├── pretty_print.py # Formatted output utilities
│   │   └── __init__.py
│   ├── orchestrators/     # Workflow orchestration logic
│   │   └── hierarchical_orchestrator.py # Hierarchical task management
│   ├── tools/             # Custom tools and utilities
│   │   ├── web_loader_tools.py # Web data loading utilities
│   │   ├── search_tools.py    # Search functionality
│   │   └── __init__.py
│   ├── data/              # Data processing and management
│   │   └── __init__.py
│   └── guardrails/        # Safety and validation checks
│       └── __init__.py
├── docs/                  # Documentation
│   ├── agent_business_analyst.mkd    # Business analyst documentation
│   ├── agent_fundamental_analyst.mkd # Fundamental analyst documentation
│   ├── agent_moat_analyst.mkd        # Moat analysis documentation
│   └── fundamental_framework.txt     # Analysis framework guide
├── main.py               # Main application entry point
├── config.yaml          # Configuration settings
├── pyproject.toml       # Project dependencies and metadata
├── agentic_test.ipynb   # Agent testing notebook
├── agentic_test2.ipynb  # Additional agent testing
├── test.ipynb           # General testing notebook
├── hierarchical_agent_flow.png # System architecture diagram
└── README.md            # This file
```

## Description

Analyst Robot is a sophisticated AI-powered system designed for automated data analysis and processing. The project leverages modern AI technologies and follows a modular architecture to provide flexible and extensible data analysis capabilities.

### Key Components

- **Agents**: AI-powered components that handle specific analysis tasks
  - Project Manager: Coordinates and manages the overall analysis workflow
  - QA Team: Ensures quality and accuracy of analysis
  - Business Analyst Team: Specializes in business metrics and market analysis
  - Fundamental Analyst Team: Focuses on fundamental company analysis

- **Orchestrators**: Coordinate and manage the flow of analysis workflows
  - Hierarchical Orchestrator: Manages complex multi-level analysis tasks and team coordination

- **Tools**: Custom utilities for data processing and analysis
  - Web Loader Tools: Handles web data extraction and processing
  - Search Tools: Provides advanced search capabilities for data gathering

- **Utils**: Core utility functions
  - Config: Manages system configuration
  - Logger: Handles system logging
  - Pretty Print: Formats output for better readability

### Technology Stack

- Python 3.12+
- LangChain for AI agent framework
- OpenAI integration for advanced AI capabilities
- Pandas for data manipulation
- BeautifulSoup4 for web scraping
- LangGraph for workflow management

### Dependencies

The project uses modern Python packages including:
- langchain >= 0.3.25
- langchain-community >= 0.3.24
- langchain-openai >= 0.3.17
- langgraph >= 0.4.5
- numpy >= 2.2.5
- openai >= 1.78.1
- pandas >= 2.2.3

## Getting Started

1. Ensure you have Python 3.12 or higher installed
2. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/analyst_robot.git
   cd analyst_robot
   ```
3. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -e .
   ```
5. Configure your environment variables and settings in `config.yaml`
6. Run the main application:
   ```bash
   python main.py
   ```

## Development

For development, additional dependencies are available in the dev group:
- ipykernel >= 6.29.5 (for Jupyter notebook support)
- pytest >= 7.4.0 (for testing)
- black >= 23.7.0 (for code formatting)
- isort >= 5.12.0 (for import sorting)
- flake8 >= 6.1.0 (for linting)

### Development Setup

1. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

2. Run tests:
   ```bash
   pytest
   ```

3. Format code:
   ```bash
   black .
   isort .
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure they pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.
 
