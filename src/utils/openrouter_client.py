"""
OpenRouter client wrapper for LangChain compatibility.
Provides a drop-in replacement for ChatOpenAI with multi-model support.
"""

import os
from typing import Any, Dict, Optional

from langchain_openai import ChatOpenAI

from src.utils.logger import get_logger

logger = get_logger(__name__)


def OpenRouterChat(
    model: str = "openai/gpt-4o",
    temperature: float = 0.1,
    max_tokens: Optional[int] = None,
    openrouter_api_key: Optional[str] = None,
    **kwargs: Any,
) -> ChatOpenAI:
    """
    OpenRouter-compatible chat model factory.

    Returns a ChatOpenAI instance configured to use OpenRouter API.

    Args:
        model: Model identifier in format "provider/model-name"
        temperature: Sampling temperature
        max_tokens: Maximum tokens in response
        openrouter_api_key: OpenRouter API key (optional, uses env var if not provided)
        **kwargs: Additional arguments passed to ChatOpenAI

    Returns:
        ChatOpenAI instance configured for OpenRouter
    """
    api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "OpenRouter API key not found. Set OPENROUTER_API_KEY environment variable "
            "or provide openrouter_api_key parameter."
        )

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        default_headers={"HTTP-Referer": "http://localhost:3000", "X-Title": "Dean Valuation Engine"},
        **kwargs,
    )


def get_model_for_agent(agent_type: str, config: Dict[str, Any] = None) -> ChatOpenAI:
    """
    Get the appropriate OpenRouter model for a specific agent type.

    Args:
        agent_type: Type of agent (e.g., 'planner', 'summarizer', etc.)
        config: Configuration dictionary (uses global config if not provided)

    Returns:
        OpenRouterChat instance configured for the agent
    """
    if config is None:
        from src.utils.config_manager import get_config

        config = get_config()

    openrouter_config = config.get("openrouter", {})
    models = openrouter_config.get("models", {})

    # Get model name for agent type
    model_name = models.get(agent_type, "openai/gpt-4o")

    # Get base configuration
    base_url = openrouter_config.get("base_url", "https://openrouter.ai/api/v1")
    api_key = openrouter_config.get("api_key") or os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise ValueError("OpenRouter API key not found in configuration or environment")

    logger.info(f"Using OpenRouter model '{model_name}' for agent '{agent_type}'")

    return OpenRouterChat(
        model=model_name, openrouter_api_key=api_key, temperature=0.1 if agent_type != "planner" else 0.0
    )
