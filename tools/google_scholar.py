
import os
import logging

import serpapi
from dotenv import load_dotenv
from langchain_core.tools import tool


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

logger = logging.getLogger(__name__)

API_KEY = os.getenv("SERPAPI_KEY")


# ============================================================
# GOOGLE SCHOLAR SEARCH TOOL
# ============================================================

@tool
def search_google_scholar(
    query: str,
    start_year: int = 2020,
    end_year: int = 2026,
    max_results: int = 10,
) -> list[dict]:
    """
    Search Google Scholar for academic papers on any topic.

    Returns titles, authors, publication details, snippets,
    links, and citation counts when available.
    """

    if not API_KEY:
        raise ValueError(
            "SERPAPI_KEY is missing from the .env file."
        )

    if start_year > end_year:
        raise ValueError("start_year must be <= end_year")

    if max_results < 1:
        raise ValueError("max_results must be at least 1")

    client = serpapi.Client(api_key=API_KEY, timeout=30)

    results = client.search(
        engine="google_scholar",
        q=query,
        as_ylo=start_year,
        as_yhi=end_year,
        num=min(max_results, 20),
        hl="en",
    )

    if results.get("error"):
        raise RuntimeError(results["error"])

    papers = []

    for item in results.get("organic_results", [])[:max_results]:
        publication_info = item.get("publication_info", {})
        cited_by = item.get("inline_links", {}).get("cited_by", {})

        papers.append({
            "title": item.get("title", "No title"),
            "authors": publication_info.get("authors", []),
            "publication_info": publication_info.get("summary", ""),
            "abstract": item.get("snippet", ""),
            "publication_date": None,
            "journal": None,
            "doi": None,
            "scholar_url": item.get("link"),
            "citation_count": cited_by.get("total"),
            "source": "Google Scholar",
            "search_query": query,
        })

    logger.info(
        "Retrieved %d papers for query: %s",
        len(papers),
        query,
    )

    return papers
