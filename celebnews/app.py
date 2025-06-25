import os
from serpapi.google_search import GoogleSearch
from dotenv import load_dotenv
from openai import OpenAI
from bs4 import BeautifulSoup
import requests

def crawl_text(url):
    """
    Crawls a webpage and extracts text content in the order it appears.
    """
    try:
        # Send GET request to the URL
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Create BeautifulSoup object
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script, style, and hidden elements
        for element in soup(['script', 'style', 'meta', '[display:none]']):
            element.decompose()
            
        # Find all paragraphs and headers in order
        content_text = ''
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = element.get_text(strip=True)
            if text:  # Only add non-empty elements
                content_text += '\n' + text
        
        return True, content_text
        
    except requests.exceptions.HTTPError as http_err:
        error_msg = f"HTTP error occurred: {http_err}"
        return False, error_msg
        
    except requests.exceptions.ConnectionError:
        error_msg = "Failed to connect to the server"
        return False, error_msg
        
    except requests.exceptions.Timeout:
        error_msg = "Request timed out"
        return False, error_msg
        
    except requests.exceptions.RequestException as e:
        error_msg = f"An error occurred while fetching the page: {str(e)}"
        return False, error_msg
        
    except Exception as e:
        error_msg = f"An error occurred while parsing the page: {str(e)}"
        return False, error_msg

def _llm_summarize(query: str, full_text: str) -> str:
    openai_api_key = os.getenv('OPENAI_API_KEY')
    client = OpenAI(api_key=openai_api_key)
    completion = client.chat.completions.create(
        model= 'gpt-4o-mini',
        messages=[
            {"role": "system", "content": "You are  assistant summarizing information on a personality from given scraped text for top news about celebrity as context. Summarize to 3 paragraph articles."},
            {"role": "user", "content":  f"""Answer the following question based on this context primarily:

                    {full_text}

                    Question: Summarize the latest news about {query} 
                    """
                }
        ]
    )
    return completion.choices[0].message.content

def fetch_and_summarize(
    name: str,
    date_value: int | None = None,
    date_unit: str | None = None
) -> str:
    """
    Fetch latest news on `name`, limited to `count` items.
    Optionally filter to the last `date_value` `date_unit`(s)
    (where unit is 'day', 'week', or 'month').
    """
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return "Missing SERPAPI_API_KEY environment variable."
    
    # Build base params
    params: dict[str, str | int] = {
        "engine": "google",
        "q": name,
        "tbm": "nws",
        "api_key": os.getenv("SERPAPI_KEY")
    }

    # Only add as_qdr if both date_value and date_unit are provided
    if date_value is not None or date_unit is not None:
        if date_value is None or date_unit is None:
            return "To filter by date, provide both date_value and date_unit."
        unit_map = {"day": "d", "week": "w", "month": "m"}
        short = unit_map.get(date_unit.lower())
        if not short:
            return f"Unsupported date_unit '{date_unit}'. Choose day, week, or month."
        params["as_qdr"] = f"{short}{date_value}"
    
    # Fetch from SerpAPI
    try:
        search = GoogleSearch(params)
        data = search.get_dict()
    except Exception as e:
        print(f"Failed to fetch news or an unexpected error occurred: {e}")

    # Handle API-level errors or no results
    if "error" in data:
        msg = data.get("error")
        detail = data.get("error_details") or ""
        return f"SerpAPI returned an error: {msg}. {detail}"
    print(data)
    results = data["news_results"]
    if not results:
        return f"No recent news found for '{name}'."

    # Prepare items for LLM
    items = [
        {
            "title": itm.get("title", "No title"),
            "snippet": itm.get("snippet", "No snippet available."),
            "date": itm.get("date", "Unknown date"),
            "link": itm.get("link")
        }
        for itm in results
    ]
    
    crawls_links = [link['link'] for link in items]
    
    i = 1
    full_text = ''
    for link in crawls_links:
        success,text = crawl_text(link)
        if success and text != '':
            i += 1
            full_text += f'Text {count}\n' + text + '\n'
        if i == count:
            break

    # Summarize with LLM (fallback to bullets on error)
    try:
        return _llm_summarize(name, full_text)
    except Exception as e:
        bullets = "\n".join(
            f"{i+1}. {it['title']} ({it['date']})\n   {it['snippet']}"
            for i, it in enumerate(items)
        )
        return (
            f"Summary generation failed: {e}\n\n"
            f"Here are the raw top {len(items)} items:\n\n{bullets}"
        )
