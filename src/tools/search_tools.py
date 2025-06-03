import os
import requests
from typing import Dict, List, Optional, Any
from langchain_core.tools import tool

def extract_search_results(search_response: Dict) -> List[Dict]:
    """
    Extract and format search results from Serper API response.
    
    Args:
        search_response (Dict): Raw response from Serper API
        
    Returns:
        List[Dict]: List of formatted search results
    """
    results: list[dict[str, Any]] = []
    
    # Extract organic results
    if 'organic' in search_response:
        for result in search_response['organic']:
            results.append({
                'title': result.get('title', ''),
                'link': result.get('link', ''),
                'snippet': result.get('snippet', '')
            })
    
    return results

@tool("search_with_serper", parse_docstring=True)
def search_tool(query: str, api_key: Optional[str] = None) -> list[dict[str, Any]]:
    """
    Perform a Google-style web search using the Serper API.

    This tool enables an agent to retrieve real-time search results from the web. It can be used 
    to look up recent news, facts, or general information. The function will return a list of 
    search results including title, link, and snippet for each entry.

    Args:
        query (str): The search query string to send to the Serper API.
        api_key (Optional[str]): Your Serper API key. If not provided, the function will 
                                 attempt to retrieve it from the SERPER_API_KEY environment variable.

    Returns:
        list[dict[str, Any]]: A list of dictionaries, each containing:
            - 'title' (str): The title of the search result.
            - 'link' (str): The URL of the search result.
            - 'snippet' (str): A brief description or preview text of the result.

    Raises:
        ValueError: If the API key is missing and not set in environment variables.
        requests.RequestException: If the API request fails (e.g., network issues or bad response).

    Example:
        >>> results = search_with_serper("latest AI news")
        >>> print(results[0]["title"])
        "OpenAI releases new GPT model"
    """
    # Get API key from parameter or environment variable
    api_key = api_key or os.getenv('SERPER_API_KEY')
    if not api_key:
        raise ValueError("Serper API key not provided and SERPER_API_KEY environment variable not set") 
    # Serper API endpoint
    url = "https://google.serper.dev/search"
    
    # Headers for the request
    headers: dict[str, str] = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    # Request payload
    payload: dict[str, str] = {
        'q': query,
        'gl': 'us',  # Geographic location
        'hl': 'en'   # Language
    }
    
    try:
        # Make the API request
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise exception for bad status codes
        
        return extract_search_results(response.json())
        
    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to perform search with Serper API: {str(e)}")

  

