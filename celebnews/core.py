import os
from serpapi import GoogleSearch

def fetch_and_summarize(name: str, count: int = 5) -> str:
    """Fetches `count` latest news stories for `name` and returns a text summary."""
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        raise RuntimeError("Set SERPAPI_API_KEY in your environment.")
    params = {
        "engine": "news",
        "q": name,
        "api_key": api_key,
        "num": count
    }
    search = GoogleSearch(params)
    results = search.get_dict().get("news_results", [])
    if not results:
        return f"No recent news found for “{name}.”"
    lines = [f"Top {min(count, len(results))} items on {name}:\n"]
    for i, item in enumerate(results[:count], start=1):
        headline = item.get("title")
        snippet  = item.get("snippet")
        date     = item.get("date")
        lines.append(f"{i}. “{headline}” ({date})\n   {snippet}\n")
    return "\n".join(lines)
