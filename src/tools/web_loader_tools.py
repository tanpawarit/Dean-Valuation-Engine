from langchain_community.document_loaders import WebBaseLoader
from typing import List, Dict
from langchain_core.tools import tool 
from requests.exceptions import RequestException 
from urllib.parse import urlparse

@tool("scrape_webpages", parse_docstring=False)
def scrape_webpages_tool(urls: List[str]) -> Dict[str, str]:
    """
    Scrape web pages for a list of URLs.

    Args:
        urls (List[str]): List of URLs to fetch.

    Returns:
        Dict[str, str]: Mapping from URL to HTML content.
    """
    if not urls:
        raise ValueError("No URLs provided")
        
    # Validate URLs
    valid_urls = []
    for url in urls:
        try:
            result = urlparse(url)
            if all([result.scheme, result.netloc]):
                valid_urls.append(url)
        except (ValueError, AttributeError):
            continue
            
    if not valid_urls:
        raise ValueError("No valid URLs provided")
    
    try:
        loader = WebBaseLoader(valid_urls)
        docs = loader.load()
        
        if not docs:
            return {"error": "No content could be extracted from the provided URLs"}
            
        return {
            "content": "\n\n".join(
                [
                    f'<Document name="{doc.metadata.get("title", "")}">\n{doc.page_content}\n</Document>'
                    for doc in docs
                ]
            )
        }
    except RequestException as e:
        raise RequestException(f"Failed to fetch content: {str(e)}")
    except ValueError as e:
        raise ValueError(f"Invalid data encountered while scraping: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred while scraping: {str(e)}")
 