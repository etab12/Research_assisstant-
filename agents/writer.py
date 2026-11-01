import csv
import json
import re
from pathlib import Path

from agents.llm import llm


OUTPUT_DIR = Path("results")

COLUMNS = [
    "title",
    "year",
    "journal",
    "authors",
    "model_used",
    "data_statistics",
    "results",
    "limitations",
]


def clean_text(value):
    """Convert extracted values to readable text."""
    if value is None:
        return "Not reported in abstract/metadata"

    if isinstance(value, list):
        value = "; ".join(str(item) for item in value)

    value = str(value).strip()

    return value or "Not reported in abstract/metadata"


def extract_paper_information(papers):
    """Extract research information from retrieved paper metadata."""

    paper_context = []

    # Limit the number of papers and abstract length to control tokens.
    for index, paper in enumerate(papers[:30], start=1):
        paper_context.append({
            "id": index,
            "title": paper.get("title"),
            "authors": paper.get("authors", []),
            "year": paper.get("year"),
            "journal": paper.get("journal"),
            "abstract": (paper.get("abstract") or "")[:2500],
            "doi": paper.get("doi"),
            "url": paper.get("url"),
            "source": paper.get("source"),
        })

    prompt = f"""
You are an academic research data extraction assistant.

Extract information from the supplied research paper records.

PAPER RECORDS:
{json.dumps(paper_context, ensure_ascii=False)}

Return ONLY a valid JSON array. Each element must contain:
- id
- title
- year
- journal
- authors
- model_used
- data_statistics
- results
- limitations

Extraction rules:
1. Use only the supplied metadata and abstracts.
2. Preserve the original paper title and author information.
3. Identify the specific ML, DL, LLM, or statistical models
   only when supported by the supplied information.
4. Extract sample size, patient count, dataset, study period,
   and train/test split when explicitly available.
5. Extract reported findings and performance metrics, such as
   AUROC, AUPRC, sensitivity, specificity, accuracy, F1, and
   confidence intervals, when available.
6. Record limitations explicitly stated in the abstract.
   Do not invent limitations or assume that missing information
   means the study has no limitations.
7. Do not confuse the number of papers with the number of patients.
8. For missing information, use:
   "Not reported in abstract/metadata".
9. Use concise, factual text.
10. Return one JSON object per input record, preserving its id.
11. Do not invent data, models, results, or citations.
"""

    response = llm.invoke(prompt)
    content = response.content

    if isinstance(content, list):
        content = "\n".join(
            item.get("text", "") if isinstance(item, dict)
            else str(item)
            for item in content
        )

    content = str(content).strip()

    # Remove Markdown code fences if the model adds them.
    content = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        content,
        flags=re.IGNORECASE,
    ).strip()

    try:
        extracted = json.loads(content)

        if not isinstance(extracted, list):
            raise ValueError("Expected a JSON array.")

    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(
            "The writer model did not return valid JSON. "
            "Try reducing the number of papers or checking "
            "the model response."
        ) from exc

    # Match extraction results to the original paper records.
    extracted_by_id = {
        item.get("id"): item
        for item in extracted
        if isinstance(item, dict)
    }

    rows = []

    for index, paper in enumerate(papers[:30], start=1):
        item = extracted_by_id.get(index, {})

        authors = item.get("authors", paper.get("authors", []))

        row = {
            "title": clean_text(
                paper.get("title") or item.get("title")
            ),
            "year": clean_text(
                paper.get("year") or item.get("year")
            ),
            "journal": clean_text(
                paper.get("journal") or item.get("journal")
            ),
            "authors": clean_text(authors),
            "model_used": clean_text(item.get("model_used")),
            "data_statistics": clean_text(
                item.get("data_statistics")
            ),
            "results": clean_text(item.get("results")),
            "limitations": clean_text(item.get("limitations")),
        }

        rows.append(row)

    return rows


def save_csv(rows):
    """Save extracted paper information as a CSV file."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "paper_extraction.csv"

    with output_file.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    return output_file


def save_markdown(question, rows, papers):
    """Save a Markdown report with the paper extraction table."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "literature_report.md"

    def escape_cell(value):
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = [
        "# Literature Search Report",
        "",
        f"**Research question:** {question}",
        "",
        f"**Papers retrieved:** {len(papers)}",
        f"**Papers extracted into the table:** {len(rows)}",
        "",
        "## Paper-by-paper evidence extraction",
        "",
        "The table is based on retrieved metadata and abstracts. "
        "Missing details are identified explicitly.",
        "",
        "| " + " | ".join(COLUMNS) + " |",
        "| " + " | ".join(["---"] * len(COLUMNS)) + " |",
    ]

    for row in rows:
        lines.append(
            "| " + " | ".join(
                escape_cell(row[column])
                for column in COLUMNS
            ) + " |"
        )

    lines.extend([
        "",
        "## References",
        "",
    ])

    for index, paper in enumerate(papers[:30], start=1):
        title = paper.get("title") or "Untitled paper"
        authors = clean_text(paper.get("authors"))
        year = clean_text(paper.get("year"))
        journal = clean_text(paper.get("journal"))
        doi = paper.get("doi")
        url = paper.get("url")

        reference = (
            f"{index}. {title}. {authors}. "
            f"{journal}. {year}."
        )

        if doi:
            doi = str(doi).strip()
            doi_url = (
                doi if doi.startswith("http")
                else f"https://doi.org/{doi}"
            )
            reference += f" DOI: {doi_url}."

        elif url:
            reference += f" URL: {url}."

        lines.append(reference)

    lines.extend([
        "",
        "## Limitations of this report",
        "",
        "- The report is based on retrieved records and available "
        "abstracts, not necessarily full-text articles.",
        "- Missing information should be verified against the "
        "original publications.",
        "- Search coverage depends on the databases, queries, "
        "and retrieval limits used.",
        "- This report is an initial literature search, not a "
        "systematic review.",
        "",
    ])

    output_file.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    return output_file


def writer_agent(state):
    question = state["question"]
    papers = state.get("papers", [])

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not papers:
        report = (
            "# Literature Search Report\n\n"
            f"**Research question:** {question}\n\n"
            "No papers were retrieved. Check the search tools "
            "and their API responses.\n"
        )

        report_file = OUTPUT_DIR / "literature_report.md"
        report_file.write_text(report, encoding="utf-8")

        return {"report": report}

    print(f"\n[WRITER] Extracting information from {min(len(papers), 30)} papers...")

    rows = extract_paper_information(papers)

    csv_file = save_csv(rows)
    md_file = save_markdown(question, rows, papers)

    print(f"[WRITER] CSV saved: {csv_file.resolve()}")
    print(f"[WRITER] Markdown saved: {md_file.resolve()}")

    report = md_file.read_text(encoding="utf-8")

    return {
        "report": report,
        "papers": papers,
    }