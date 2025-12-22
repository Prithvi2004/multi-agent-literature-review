# tasks.py
from crewai import Task
from agents import (
    retrieval_agent, summarization_agent, method_comparison_agent,
    gap_analysis_agent, novelty_agent
)

def create_tasks(user_idea: str, domains: list):
    query = f"{user_idea} {' '.join(domains)}"

    retrieval_task = Task(
        description=f"Retrieve up to 10 relevant papers for: '{user_idea}' in fields: {', '.join(domains)} from arXiv, Semantic Scholar, and PubMed.",
        agent=retrieval_agent,
        expected_output="List of papers with title, authors, year, abstract, source, and relevance score."
    )

    summarization_task = Task(
        description="Summarize each retrieved paper. Extract: contribution, method, result, limitation.",
        agent=summarization_agent,
        expected_output="One structured summary per paper."
    )

    comparison_task = Task(
        description="Compare methodologies across all papers. Identify common techniques, datasets, and innovations.",
        agent=method_comparison_agent,
        expected_output="Comparative analysis highlighting trends and methodological gaps."
    )

    gap_task = Task(
        description=f"Identify 3-5 research gaps in the literature related to: '{user_idea}'.",
        agent=gap_analysis_agent,
        expected_output="Numbered list of gaps with explanations tied to specific papers."
    )

    novelty_task = Task(
        description=f"Evaluate novelty of: '{user_idea}' against retrieved literature. Assign score (0-100). Cite closest work.",
        agent=novelty_agent,
        expected_output=(
            "**Novelty Score**: X/100\n"
            "**Reasoning**: ...\n"
            "**Closest Prior Work**: ...\n"
            "**Verdict**: Highly/Moderately/Not Novel"
        )
    )

    return [
        retrieval_task,
        summarization_task,
        comparison_task,
        gap_task,
        novelty_task
    ]