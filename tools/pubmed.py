
import logging
import os

from dotenv import load_dotenv
from langchain_core.tools import tool
from pymed import PubMed

load_dotenv()

logger = logging.getLogger(__name__)

NCBI_EMAIL = os.getenv("NCBI_EMAIL", "")


def _get_pubmed():
    """Create a PyMed client."""
    if not NCBI_EMAIL:
        raise ValueError(
            "Set NCBI_EMAIL in your .env file."
        )

    return PubMed(
        tool="ResearchAssistant",
        email=NCBI_EMAIL,
    )



def _format_paper(article) -> dict:
    """Convert a PyMed PubMedArticle object into a dictionary."""

    pmid = str(getattr(article, "pubmed_id", "") or "")
    pmid = pmid.splitlines()[0].strip().split()[0] if pmid.strip() else ""

    return {
        "pmid": pmid,
        "title": getattr(article, "title", None) or "",
        "authors": getattr(article, "authors", None) or [],
        "journal": getattr(article, "journal", None) or "",
        "publication_date": str(
            getattr(article, "publication_date", None) or ""
        ),
        "abstract": getattr(article, "abstract", None) or "",
        "doi": getattr(article, "doi", None) or "",
        "keywords": getattr(article, "keywords", None) or [],
        "pubmed_url": (
            f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            if pmid else ""
        ),
        "source": "PubMed",
    }


@tool
def search_pubmed(
    query: str,
    start_year: int,
    end_year: int,
    max_results: int = 20,
) -> list[dict]:
    """Search PubMed for papers matching a topic and publication years.

    Args:
        query: PubMed search query using keywords and Boolean operators.
        start_year: Earliest publication year to include.
        end_year: Latest publication year to include.
        max_results: Maximum number of records to retrieve.

    Returns:
        Article metadata, abstracts, DOI, PMID, and PubMed links.
    """

    if not query.strip():
        raise ValueError("Query cannot be empty.")

    if start_year > end_year:
        raise ValueError("start_year must not exceed end_year.")

    if not 1 <= max_results <= 10000:
        raise ValueError("max_results must be between 1 and 10000.")

    logger.info(
        "Searching PubMed for %s (%s-%s)",
        query,
        start_year,
        end_year,
    )

    # Apply the publication date filter in the PubMed query.
    dated_query = (
        f"({query}) AND "
        f'("{start_year}/01/01"[Date - Publication] : '
        f'"{end_year}/12/31"[Date - Publication])'
    )

    pubmed = _get_pubmed()
    articles = pubmed.query(
        dated_query,
        max_results=max_results,
    )

    papers = []
    seen = set()

    for article in articles:
        paper = _format_paper(article)
        pmid = paper["pmid"]

        if pmid and pmid not in seen:
            seen.add(pmid)
            papers.append(paper)

    logger.info("Retrieved %d unique papers.", len(papers))

    return papers


@tool
def fetch_pubmed_details(pmids: list[str]) -> list[dict]:
    """Fetch article details for known PubMed IDs.

    Args:
        pmids: PubMed identifiers to retrieve.

    Returns:
        Metadata and abstracts for the requested papers.
    """

    if not pmids:
        return []

    if len(pmids) > 100:
        raise ValueError("Fetch no more than 100 PMIDs per call.")

    normalized = list(dict.fromkeys(
        str(pmid).strip() for pmid in pmids
    ))

    if any(not pmid.isdigit() for pmid in normalized):
        raise ValueError("Every PMID must contain digits only.")

    logger.info("Fetching %d PubMed records.", len(normalized))

    pubmed = _get_pubmed()
    query = " OR ".join(
        f"{pmid}[PMID]" for pmid in normalized
    )

    articles = pubmed.query(
        query,
        max_results=len(normalized),
    )

    papers = [_format_paper(article) for article in articles]
    requested = set(normalized)

    return [
        paper for paper in papers
        if paper["pmid"].splitlines()[0].split()[0] in requested
    ]
