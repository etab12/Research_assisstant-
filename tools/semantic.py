
import time
import requests

API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

HEADERS = {
    "User-Agent": "TraumaResearchAssistant/1.0"
}

FIELDS = (
    "title,authors,year,abstract,venue,"
    "citationCount,externalIds,openAccessPdf,url"
)


def search_semantic_scholar(query, limit=10, year=None):
    params = {
        "query": query,
        "limit": min(max(limit, 1), 100),
        "fields": FIELDS,
    }

    if year:
        params["year"] = year

    for attempt in range(6):
        try:
            response = requests.get(
                API_URL,
                params=params,
                headers=HEADERS,
                timeout=30,
            )

            print("HTTP status:", response.status_code)

            if response.status_code == 429:
                if attempt == 5:
                    print("Rate limit persists. Try again later.")
                    return []

                retry_after = response.headers.get("Retry-After")

                try:
                    wait = float(retry_after) if retry_after else 10 * (2 ** attempt)
                except ValueError:
                    wait = 10 * (2 ** attempt)

                wait = min(wait, 120)

                print(
                    f"Rate limited. Waiting {wait:g} seconds "
                    f"(attempt {attempt + 1}/6)."
                )
                time.sleep(wait)
                continue

            response.raise_for_status()
            data = response.json()

            results = []

            for paper in data.get("data", []):
                ids = paper.get("externalIds") or {}
                pdf = paper.get("openAccessPdf") or {}

                results.append({
                    "source": "Semantic Scholar",
                    "title": paper.get("title"),
                    "authors": [
                        a.get("name")
                        for a in paper.get("authors", [])
                    ],
                    "year": paper.get("year"),
                    "journal": paper.get("venue"),
                    "abstract": paper.get("abstract"),
                    "doi": ids.get("DOI"),
                    "citations": paper.get("citationCount"),
                    "url": paper.get("url"),
                    "open_access_pdf": pdf.get("url"),
                })

            return results

        except requests.RequestException as error:
            print("Request failed:", error)
            return []

    return []


def display_results(papers):
    print(f"\nTotal papers retrieved: {len(papers)}")

    for i, paper in enumerate(papers, start=1):
        print("\n" + "=" * 65)
        print(f"{i}. {paper['title']}")
        print(f"Year: {paper['year']}")
        print(f"Journal: {paper['journal']}")
        print(f"DOI: {paper['doi']}")
        print(f"Citations: {paper['citations']}")
        print(f"Abstract: {paper['abstract'] or 'Not available'}")
        print(f"URL: {paper['url']}")


if __name__ == "__main__":
    query = "trauma machine learning mortality prediction"

    papers = search_semantic_scholar(query, limit=10)
    display_results(papers)
