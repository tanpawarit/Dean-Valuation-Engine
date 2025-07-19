import os
import time
from typing import Any, Optional

import requests
from langchain_core.tools import tool

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Global variable to track last API call time for rate limiting
_last_api_call_time = 0.0


def extract_search_results(search_response: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract and format search results from Brave Search API response.

    Args:
        search_response (dict[str, Any]): Raw response from Brave Search API

    Returns:
        list[dict[str, Any]]: List of formatted search results
    """
    results: list[dict[str, Any]] = []

    # Extract web results from Brave Search
    if "web" in search_response and "results" in search_response["web"]:
        for result in search_response["web"]["results"]:
            results.append(
                {
                    "title": result.get("title", ""),
                    "link": result.get("url", ""),
                    "snippet": result.get("description", ""),
                }
            )

    return results


@tool("search_with_brave", parse_docstring=True)
def search_tool(query: str, api_key: Optional[str] = None) -> list[dict[str, Any]]:
    """
    Perform a web search using the Brave Search API.

    This tool enables an agent to retrieve real-time search results from the web. It can be used
    to look up recent news, facts, or general information. The function will return a list of
    search results including title, link, and snippet for each entry.

    Args:
        query (str): The search query string to send to the Brave Search API.
        api_key (Optional[str]): Your Brave Search API key. If not provided, the function will
                                 attempt to retrieve it from the BRAVE_API_KEY environment variable.

    Returns:
        list[dict[str, Any]]: A list of dictionaries, each containing:
            - 'title' (str): The title of the search result.
            - 'link' (str): The URL of the search result.
            - 'snippet' (str): A brief description or preview text of the result.

    Raises:
        ValueError: If the API key is missing and not set in environment variables.
        requests.RequestException: If the API request fails (e.g., network issues or bad response).

    Example:
        >>> results = search_with_brave("latest AI news")
        >>> print(results[0]["title"])
        "OpenAI releases new GPT model"
    """
    # Determine the effective API key
    env_api_key = os.getenv("BRAVE_API_KEY")
    effective_api_key = ""

    if api_key and api_key != "api_key":  # Parameter provided and it's not the literal string 'api_key'
        effective_api_key = api_key
        logger.debug(
            f"Using API key from parameter: {'*' * (len(effective_api_key) - 4) + effective_api_key[-4:] if effective_api_key else 'EMPTY'}"
        )
    elif env_api_key:
        effective_api_key = env_api_key
        logger.debug(
            f"Using API key from BRAVE_API_KEY environment variable: {'*' * (len(effective_api_key) - 4) + effective_api_key[-4:] if effective_api_key else 'EMPTY'}"
        )
    else:
        logger.debug("No API key found from parameter or environment variable.")

    if not effective_api_key:
        raise ValueError("Brave API key not provided and BRAVE_API_KEY environment variable not set")

    # Brave Search API endpoint
    url = "https://api.search.brave.com/res/v1/web/search"

    # Headers for the request
    headers: dict[str, str] = {"X-Subscription-Token": effective_api_key, "Accept": "application/json"}

    # Query parameters
    params: dict[str, str] = {
        "q": query,
        "count": "10",  # Number of results to return
        "offset": "0",  # Pagination offset
    }

    # Rate limiting - ensure at least 1 second between requests
    global _last_api_call_time
    current_time = time.time()
    time_since_last_call = current_time - _last_api_call_time

    if time_since_last_call < 1.0:
        sleep_time = 1.0 - time_since_last_call
        logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
        time.sleep(sleep_time)

    try:
        # Make the API request
        response = requests.get(url, headers=headers, params=params)
        _last_api_call_time = time.time()  # Update last call time after successful request
        response.raise_for_status()  # Raise exception for bad status codes

        return extract_search_results(response.json())

    except requests.RequestException as e:
        # Update last call time even on error to prevent rapid retries
        _last_api_call_time = time.time()
        raise requests.RequestException(f"Failed to perform search with Brave API: {str(e)}")
