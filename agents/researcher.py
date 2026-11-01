 
import json
import re

from agents.llm import llm
from tools.pubmed import search_pubmed
from tools.openlex import search_openalex
from tools.semantic import search_semantic_scholar


# ============================================================
# HELPERS
# ============================================================

def normalize_title(title):
    """Normalize titles for duplicate detection."""
    return re.sub(r"[^a-z0-9]+", "", (title or "").lower())


def call_tool(tool, arguments):
    """Support regular Python functions and LangChain tools."""
    if hasattr(tool, "invoke"):
        return tool.invoke(arguments)

    return tool(**arguments)


def extract_papers(results):
    """Extract paper records from common API response formats."""
    if isinstance(results, list):
        return results

    if isinstance(results, dict):
        for key in ("papers", "results", "data"):
            if isinstance(results.get(key), list):
                return results[key]

    return []


def normalize_paper(paper, source):
    """Convert a paper into a consistent format."""
    if not isinstance(paper, dict) or not paper.get("title"):
        return None

    external_ids = paper.get("externalIds") or {}
    doi = paper.get("doi") or external_ids.get("DOI")

    if doi:
        doi = (
            str(doi)
            .lower()
            .replace("https://doi.org/", "")
            .replace("http://doi.org/", "")
            .strip()
        )

    authors = paper.get("authors") or []

    if isinstance(authors, list):
        authors = [
            author.get("name", "")
            if isinstance(author, dict)
            else str(author)
            for author in authors
        ]

    pdf = paper.get("open_access_pdf") or paper.get("openAccessPdf")

    if isinstance(pdf, dict):
        pdf = pdf.get("url")

    return {
        "source": paper.get("source", source),
        "title": str(paper["title"]).strip(),
        "authors": authors,
        "year": paper.get("year"),
        "journal": paper.get("journal") or paper.get("venue"),
        "abstract": paper.get("abstract"),
        "doi": doi,
        "citations": (
            paper.get("citations")
            if paper.get("citations") is not None
            else paper.get("citationCount")
        ),
        "url": paper.get("url"),
        "open_access_pdf": pdf,
    }


# ============================================================
# DATABASE SEARCH
# ============================================================

def call_pubmed(query, year_from, year_to, limit):
    return call_tool(
        search_pubmed,
        {
            "query": query,
            "start_year": year_from,
            "end_year": year_to,
            "max_results": limit,
        },
    )


def call_openalex(query, year_from, year_to, limit):
    return call_tool(
        search_openalex,
        {
            "query": query,
            "limit": limit,
            "year_from": year_from,
            "year_to": year_to,
        },
    )


def call_semantic_scholar(query, year_from, year_to, limit):
    # Semantic Scholar expects "year", not year_from/year_to.
    return call_tool(
        search_semantic_scholar,
        {
            "query": query,
            "limit": limit,
            "year": f"{year_from}-{year_to}",
        },
    )


# ============================================================
# DEDUPLICATION
# ============================================================

def deduplicate_papers(papers):
    """Merge duplicate records while retaining available metadata."""
    unique = []
    doi_index = {}
    title_index = {}

    for paper in papers:
        doi = paper.get("doi")
        title = normalize_title(paper.get("title"))

        existing_index = None

        if doi:
            existing_index = doi_index.get(doi)

        if existing_index is None and title:
            existing_index = title_index.get(title)

        if existing_index is not None:
            existing = unique[existing_index]

            # Keep metadata from whichever source has more information.
            for key, value in paper.items():
                if value not in (None, "", [], {}):
                    if existing.get(key) in (None, "", [], {}):
                        existing[key] = value

            sources = existing.get("sources", [existing.get("source")])
            if paper.get("source") and paper["source"] not in sources:
                sources.append(paper["source"])
            existing["sources"] = sources

            if doi:
                doi_index[doi] = existing_index
            if title:
                title_index[title] = existing_index

            continue

        paper["sources"] = [paper.get("source")] if paper.get("source") else []
        index = len(unique)
        unique.append(paper)

        if doi:
            doi_index[doi] = index
        if title:
            title_index[title] = index

    return unique


# ============================================================
# LLM RELEVANCE SCREENING
# ============================================================

def screen_papers(papers, plan, batch_size=10):
    """
    Screen papers against the current research question.
    Papers without enough information are marked uncertain.
    """
    relevant = []
    uncertain = []

    question = plan.get("research_question", "")
    objectives = plan.get("objectives", [])
    inclusion = plan.get("inclusion_criteria", [])
    exclusion = plan.get("exclusion_criteria", [])

    for start in range(0, len(papers), batch_size):
        batch = papers[start:start + batch_size]

        paper_inputs = []

        for i, paper in enumerate(batch):
            paper_inputs.append({
                "id": i,
                "title": paper.get("title"),
                "abstract": paper.get("abstract") or "",
                "year": paper.get("year"),
                "journal": paper.get("journal"),
            })

        prompt = f"""
You are a careful academic literature-screening assistant.

Research question:
{question}

Research objectives:
{json.dumps(objectives, ensure_ascii=False)}

Inclusion criteria:
{json.dumps(inclusion, ensure_ascii=False)}

Exclusion criteria:
{json.dumps(exclusion, ensure_ascii=False)}

Screen the papers below based on their titles and abstracts.

Rules:
- Assess relevance to the actual research question.
- Do not assume a specific research domain unless stated in the question.
- Do not classify a paper as relevant merely because it mentions
  machine learning, AI, prediction, or a related general term.
- Consider the population, topic, outcome, and study objective.
- Use "uncertain" when the available information is insufficient.
- Do not invent information not present in the paper record.
- Return exactly one decision for every paper ID.
- Return only valid JSON.

Required format:
{{
  "results": [
    {{
      "id": 0,
      "decision": "relevant",
      "reason": "Brief explanation"
    }}
  ]
}}

Allowed decisions: relevant, irrelevant, uncertain.

Papers:
{json.dumps(paper_inputs, ensure_ascii=False)}
"""

        try:
            response = llm.invoke(prompt).content

            if isinstance(response, list):
                response = "".join(
                    item.get("text", "") if isinstance(item, dict)
                    else str(item)
                    for item in response
                )

            match = re.search(r"\{.*\}", response, flags=re.DOTALL)

            if not match:
                raise ValueError("The LLM returned invalid JSON")

            decisions = json.loads(match.group(0)).get("results", [])
            decision_map = {
                item.get("id"): item
                for item in decisions
                if isinstance(item, dict)
            }

            for i, paper in enumerate(batch):
                decision = decision_map.get(i)

                if not decision:
                    paper["screening_decision"] = "uncertain"
                    paper["screening_reason"] = (
                        "No screening decision was returned."
                    )
                    uncertain.append(paper)
                    continue

                label = str(decision.get("decision", "")).lower().strip()

                paper["screening_decision"] = label
                paper["screening_reason"] = decision.get("reason", "")

                if label == "relevant":
                    relevant.append(paper)
                elif label == "irrelevant":
                    continue
                else:
                    paper["screening_decision"] = "uncertain"
                    uncertain.append(paper)

        except Exception as error:
            print(f"[RESEARCHER] Screening error: {error}")

            # Do not silently discard papers if screening fails.
            for paper in batch:
                paper["screening_decision"] = "uncertain"
                paper["screening_reason"] = (
                    "Automatic screening failed; manual review is needed."
                )
                uncertain.append(paper)

    return relevant, uncertain


# ============================================================
# RESEARCHER AGENT
# ============================================================

def researcher_agent(state):
    plan = state["plan"]

    year_from = plan.get("year_from", 2019)
    year_to = plan.get("year_to", 2026)
    queries = plan.get("queries", [])

    if not queries:
        queries = [state["question"]]

    all_papers = []
    results_per_query = 10

    search_sources = [
        ("PubMed", call_pubmed),
        ("OpenAlex", call_openalex),
        ("Semantic Scholar", call_semantic_scholar),
    ]

    for query in queries:
        print(f"\n[RESEARCHER] Searching: {query}")

        for source_name, search_function in search_sources:
            try:
                results = search_function(
                    query=query,
                    year_from=year_from,
                    year_to=year_to,
                    limit=results_per_query,
                )

                papers = extract_papers(results)
                added = 0

                for paper in papers:
                    normalized = normalize_paper(paper, source_name)

                    if normalized:
                        all_papers.append(normalized)
                        added += 1

                print(f"[RESEARCHER] {source_name}: {added} records")

            except Exception as error:
                print(f"[RESEARCHER] {source_name} error: {error}")

    unique_papers = deduplicate_papers(all_papers)

    print(f"\n[RESEARCHER] Retrieved records: {len(all_papers)}")
    print(f"[RESEARCHER] Unique papers: {len(unique_papers)}")

    relevant, uncertain = screen_papers(unique_papers, plan)

    print(f"[RESEARCHER] Relevant papers: {len(relevant)}")
    print(f"[RESEARCHER] Uncertain papers: {len(uncertain)}")

    return {
        "papers": relevant,
        "uncertain_papers": uncertain,
    }
