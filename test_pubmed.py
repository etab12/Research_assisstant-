
from tools.pubmed import search_pubmed


TRAUMA_SEARCH_QUERIES = [
    '"trauma registry" AND ("machine learning" OR "deep learning" OR "large language model" OR LLM)',
    '("Injury Severity Score" OR ISS) AND trauma AND ("machine learning" OR "deep learning" OR "large language model" OR LLM)',
    '("trauma patients" OR "injured patients") AND "mortality prediction" AND ("machine learning" OR "deep learning" OR "large language model" OR LLM)',
    '("trauma patients" OR "trauma registry") AND ("tabular data" OR "clinical variables" OR "structured clinical data") AND ("machine learning" OR "deep learning" OR "large language model" OR LLM)',
    '(trauma OR "injured patients") AND ICD-10 AND ("machine learning" OR "deep learning" OR "large language model" OR LLM)',
    '("trauma patients" OR "injured patients") AND "length of stay" AND ("machine learning" OR "deep learning" OR "large language model" OR LLM)',
    '("trauma patients" OR "injured patients") AND ("ICU admission" OR "intensive care") AND ("machine learning" OR "deep learning" OR "large language model" OR LLM)',
]


def main():
    all_papers = {}

    for query in TRAUMA_SEARCH_QUERIES:
        print(f"\nSearching: {query}")

        papers = search_pubmed.invoke({
            "query": query,
            "start_year": 2020,
            "end_year": 2026,
            "max_results": 5,
        })

        for paper in papers:
            key = paper.get("pmid") or paper.get("doi") or paper.get("title")
            if key and key not in all_papers:
                all_papers[key] = paper

    print(f"\nRetrieved {len(all_papers)} unique papers\n")

    for number, paper in enumerate(all_papers.values(), start=1):
        print(f"{number}. {paper['title']}")
        print(f"   Year: {paper['publication_date']}")
        print(f"   PMID: {paper['pmid']}")
        print(f"   DOI: {paper['doi'] or 'Not available'}")
        print(f"   URL: {paper['pubmed_url']}")
        print("-" * 60)


if __name__ == "__main__":
    main()
