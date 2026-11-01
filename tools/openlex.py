
import requests

# ============================================================
# CONFIGURATION
# ============================================================

API_URL = "https://api.openalex.org/works"


# ============================================================
# SEARCH OPENALEX
# ============================================================

def search_openalex(query, limit=10, year_from=None, year_to=None):
    """Search academic papers using the public OpenAlex API."""

    params = {
        "search": query,
        "per-page": min(max(limit, 1), 200),
        "select": (
            "id,doi,title,authorships,publication_year,"
            "primary_location,cited_by_count,indexed_in,"
            "open_access,biblio,type"
        ),
    }

    if year_from and year_to:
        params["filter"] = (
            f"publication_year:{year_from}-{year_to}"
        )
    elif year_from:
        params["filter"] = f"publication_year:>{year_from - 1}"
    elif year_to:
        params["filter"] = f"publication_year:<{year_to + 1}"

    try:
        response = requests.get(
            API_URL,
            params=params,
            timeout=30,
        )

        print("HTTP status:", response.status_code)

        if not response.ok:
            print("API response:", response.text[:1000])
            response.raise_for_status()

        data = response.json()
        results = []

        for paper in data.get("results", []):
            authors = [
                item.get("author", {}).get("display_name")
                for item in paper.get("authorships", [])
                if item.get("author", {}).get("display_name")
            ]

            location = paper.get("primary_location") or {}
            source = location.get("source") or {}
            open_access = paper.get("open_access") or {}

            # OpenAlex stores abstracts as an inverted index.
            inverted_index = paper.get("abstract") or {}
            abstract = reconstruct_abstract(inverted_index)

            results.append({
                "source": "OpenAlex",
                "title": paper.get("title"),
                "authors": authors,
                "year": paper.get("publication_year"),
                "journal": source.get("display_name"),
                "doi": paper.get("doi"),
                "citations": paper.get("cited_by_count"),
                "url": paper.get("id"),
                "landing_page": location.get("landing_page_url"),
                "open_access": open_access.get("is_oa"),
                "pdf_url": open_access.get("oa_url"),
                "type": paper.get("type"),
            })

        return results

    except requests.RequestException as error:
        print("OpenAlex request failed:", error)
        return []


# ============================================================
# RECONSTRUCT ABSTRACT
# ============================================================

def reconstruct_abstract(inverted_index):
    """Convert OpenAlex's abstract index into readable text."""

    if not inverted_index:
        return None

    words = {}

    for word, positions in inverted_index.items():
        for position in positions:
            words[position] = word

    return " ".join(
        words[position] for position in sorted(words)
    )


# ============================================================
# DISPLAY RESULTS
# ============================================================

def display_results(papers):
    print(f"\nTotal papers retrieved: {len(papers)}")

    for number, paper in enumerate(papers, start=1):
        print("\n" + "=" * 75)
        print(f"{number}. {paper['title']}")
        print(f"Year: {paper['year']}")
        print(f"Authors: {', '.join(paper['authors'][:5])}")
        print(f"Journal: {paper['journal']}")
        print(f"DOI: {paper['doi']}")
        print(f"Citations: {paper['citations']}")
        print(f"Open access: {paper['open_access']}")
        print(f"PDF: {paper['pdf_url']}")
        print(f"URL: {paper['landing_page'] or paper['url']}")

# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    query = "trauma machine learning mortality prediction"

    papers = search_openalex(
        query=query,
        limit=10,
        year_from=2025,
        year_to=2026,
    )

    display_results(papers)
