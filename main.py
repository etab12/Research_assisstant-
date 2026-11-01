
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from agents.planner import planner_agent
from agents.researcher import researcher_agent
from agents.writer import writer_agent


# ============================================================
# SHARED STATE
# ============================================================

class ResearchState(TypedDict, total=False):
    question: str
    plan: dict
    papers: list
    report: str


# ============================================================
# BUILD GRAPH
# ============================================================

builder = StateGraph(ResearchState)

builder.add_node("planner", planner_agent)
builder.add_node("researcher", researcher_agent)
builder.add_node("writer", writer_agent)

builder.add_edge(START, "planner")
builder.add_edge("planner", "researcher")
builder.add_edge("researcher", "writer")
builder.add_edge("writer", END)

research_graph = builder.compile()


# ============================================================
# RUN RESEARCH
# ============================================================

if __name__ == "__main__":

    question = input(
        "Enter your research question: "
    ).strip()

    if not question:
        raise ValueError("Research question cannot be empty.")

    result = research_graph.invoke({
        "question": question
    })

    print("\n" + "=" * 80)
    print("FINAL LITERATURE SEARCH REPORT")
    print("=" * 80)
    print(result["report"])

    # Save the report.
    from pathlib import Path

    output_dir = Path("results")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "literature_report.md"
    output_file.write_text(
        result["report"],
        encoding="utf-8",
    )

    print(f"\nReport saved to: {output_file.resolve()}")
    print(f"Unique papers retrieved: {len(result.get('papers', []))}")
