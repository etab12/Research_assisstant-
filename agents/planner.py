
import json
import re

from agents.llm import llm


def planner_agent(state):
    question = state["question"].strip()

    prompt = f"""
You are the planning agent of a general-purpose academic
research assistant.

The user may ask about ANY research topic.

Research question:
{question}

Create a focused literature search plan.

REQUIREMENTS:

1. Understand the research question before generating queries.
2. Identify the relevant:
   - Research topic and domain
   - Population or subject, if applicable
   - Main outcomes or research objectives
   - Methods or study designs, if relevant
3. Generate 3 to 5 DISTINCT search queries.
4. Each query must explore a useful aspect of the question.
   Avoid generating several nearly identical queries.
5. Include relevant synonyms and alternative terminology.
6. Use appropriate academic search terms.
7. Do not assume that every paper uses AI or machine learning.
   Include these terms only when relevant to the question.
8. Do not introduce unrelated topics or populations.
9. Define inclusion and exclusion criteria specifically for
   the user's research question.
10. Do not invent constraints that the user did not request.
11. Use publication years 2019 through 2026 by default.
12. Return only valid JSON using this structure:

{{
  "research_question": "The original research question",
  "research_domain": "The identified research domain",
  "objectives": [
    "First research objective",
    "Second research objective"
  ],
  "queries": [
    "First focused search query",
    "Second focused search query",
    "Third focused search query"
  ],
  "inclusion_criteria": [
    "Question-specific inclusion criterion"
  ],
  "exclusion_criteria": [
    "Question-specific exclusion criterion"
  ],
  "year_from": 2019,
  "year_to": 2026
}}

All criteria must be derived from the research question.
Return JSON only. Do not include Markdown or explanations.
"""

    response = llm.invoke(prompt).content

    if isinstance(response, list):
        response = "".join(
            item.get("text", "") if isinstance(item, dict)
            else str(item)
            for item in response
        )

    try:
        match = re.search(
            r"\{.*\}",
            response,
            flags=re.DOTALL,
        )

        if not match:
            raise ValueError("No JSON object found")

        plan = json.loads(match.group(0))

        # Validate search queries.
        queries = plan.get("queries")

        if not isinstance(queries, list):
            raise ValueError("Queries must be a list")

        queries = list(dict.fromkeys(
            str(query).strip()
            for query in queries
            if isinstance(query, str) and query.strip()
        ))

        if not 3 <= len(queries) <= 5:
            raise ValueError("Expected 3 to 5 valid queries")

        # Validate criteria and objectives.
        for field in (
            "objectives",
            "inclusion_criteria",
            "exclusion_criteria",
        ):
            value = plan.get(field)

            if not isinstance(value, list) or not value:
                raise ValueError(f"Invalid {field}")

            plan[field] = [
                str(item).strip()
                for item in value
                if isinstance(item, str) and item.strip()
            ]

            if not plan[field]:
                raise ValueError(f"Empty {field}")

        plan["research_question"] = question

        if not isinstance(plan.get("research_domain"), str):
            raise ValueError("Missing research domain")

        plan["research_domain"] = plan["research_domain"].strip()

        if not plan["research_domain"]:
            raise ValueError("Empty research domain")

        plan["queries"] = queries

        plan["year_from"] = int(plan.get("year_from", 2019))
        plan["year_to"] = int(plan.get("year_to", 2026))

        if not (
            1900 <= plan["year_from"]
            <= plan["year_to"] <= 2026
        ):
            raise ValueError("Invalid publication-year range")

    except (ValueError, TypeError, json.JSONDecodeError):
        # Generic fallback; never assume a specific research domain.
        plan = {
            "research_question": question,
            "research_domain": "Not determined",
            "objectives": [question],
            "queries": [question],
            "inclusion_criteria": [
                "Directly addresses the user's research question."
            ],
            "exclusion_criteria": [
                "Does not address the user's research question."
            ],
            "year_from": 2019,
            "year_to": 2026,
        }

        print("[PLANNER] Warning: Invalid plan; using fallback.")

    print("\n[PLANNER] Search plan:")
    print(json.dumps(plan, indent=2, ensure_ascii=False))

    return {"plan": plan}
