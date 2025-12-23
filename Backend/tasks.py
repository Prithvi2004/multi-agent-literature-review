# tasks.py
from crewai import Task
from agents import (
    controller_agent,
    retrieval_agent,
    summarization_agent,
    method_comparison_agent,
    gap_analysis_agent,
    novelty_agent,
)


def create_tasks(user_idea: str, domains: list):
    """Create RAG-first workflow tasks."""

    domain_str = ", ".join(domains)

    retrieval_task = Task(
        description=(
            f"Use RAGSearch tool to find up to 10 relevant papers for: '{user_idea}' "
            f"in {domain_str}. List title, authors, year, source, relevance score."
        ),
        agent=retrieval_agent,
        expected_output="List of papers with [P#] references and relevance justification.",
    )

    summarization_task = Task(
        description=(
            f"Use RAGSearch to summarize each retrieved paper: contribution, method, "
            f"results, limitations. Include [P#] evidence."
        ),
        agent=summarization_agent,
        expected_output="Structured summary per paper with [P#] citations.",
        context=[retrieval_task]  # Use output from retrieval task
    )

    comparison_task = Task(
        description=(
            f"Compare methods across papers: techniques, datasets, metrics. "
            f"Identify trends, gaps, conflicts. Ground in [P#] evidence."
        ),
        agent=method_comparison_agent,
        expected_output="Comparative analysis with [P#] references.",
        context=[summarization_task]  # Use summaries
    )

    gap_task = Task(
        description=(
            f"Identify 3-5 research gaps for: '{user_idea}'. Explain importance, "
            f"evidence strength, [P#] support."
        ),
        agent=gap_analysis_agent,
        expected_output="Numbered gaps with [P#] refs and uncertainty levels.",
        context=[comparison_task]  # Use comparison
    )

    novelty_task = Task(
        description=(
            f"Evaluate novelty of: '{user_idea}' vs literature. Score 0-100, "
            f"identify closest work, use RAGSearch + CitationVerifier."
        ),
        agent=novelty_agent,
        expected_output="Novelty score, reasoning with [P#], closest prior work.",
        context=[gap_task, summarization_task]  # Use gaps and summaries
    )

    synthesis_task = Task(
        description=(
            f"SYNTHESIZE ALL PREVIOUS OUTPUTS INTO ONE REPORT. "
            f"You have received: 1) Retrieved papers, 2) Summaries, 3) Method comparison, "
            f"4) Research gaps, 5) Novelty assessment. "
            f"Research Idea: '{user_idea}'. Domains: {domain_str}. "
            f"DO NOT ask for user input. DO NOT start new work. "
            f"ONLY combine what previous agents provided into final structured report."
        ),
        agent=controller_agent,
        expected_output=(
            "Complete LITERATURE REVIEW REPORT with all sections: papers, summaries, "
            "comparison, gaps, novelty score, limitations. Use [P#] citations throughout."
        ),
        context=[retrieval_task, summarization_task, comparison_task, gap_task, novelty_task]  # ALL previous outputs
    )

    return [
        retrieval_task,
        summarization_task,
        comparison_task,
        gap_task,
        novelty_task,
        synthesis_task,
    ]