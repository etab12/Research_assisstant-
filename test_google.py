
from tools.google_scholar import search_google_scholar


def main():
    query = (
        '("trauma patients" OR "trauma registry" OR "injured patients") '
        '("machine learning" OR "deep learning" OR '
        '"large language model" OR LLM) '
        '(mortality OR "injury severity" OR "ICU admission")'
    )

    papers = search_google_scholar.invoke({
        "query": query,
        "start_year": 2020,
        "end_year": 2026,
        "max_results": 10,
    })

    print(f"\nRetrieved {len(papers)} papers\n")

    for number, paper in enumerate(papers, start=1):
        print(f"{number}. {paper['title']}")
        print(f"   Authors: {paper['authors']}")
        print(f"   Publication: {paper['publication_info']}")
        print(f"   Citations: {paper['citation_count']}")
        print(f"   URL: {paper['scholar_url']}")
        print(f"   Snippet: {paper['abstract']}")
        print("-" * 70)


if __name__ == "__main__":
    main()
