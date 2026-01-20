# tasks.py
"""Task definitions with topic anchoring and validation guards."""

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
    """Create RAG-first workflow tasks with topic anchoring.
    
    Every task includes:
    - Explicit reference to the original research idea
    - FAIL_FAST condition if no evidence found
    - Required citation format with [P#] handles
    """

    domain_str = ", ".join(domains)
    
    # Topic anchor - included in every task to prevent drift
    topic_anchor = f"""
**TOPIC ANCHOR (Stay on this topic):**
Research Idea: "{user_idea}"
Domains: {domain_str}

**FAIL_FAST RULES:**
- If RAG Search returns INSUFFICIENT_EVIDENCE, report that clearly
- NEVER fabricate papers, citations, or claims
- Every paper cited MUST have a valid [P#] handle from RAG Search
- Stay focused on the research idea above - NO topic drift
"""

    retrieval_task = Task(
        description=(
            f"Use RAG Search tool to find relevant papers for:\n"
            f"Research Idea: '{user_idea}'\n"
            f"Domains: {domain_str}\n\n"
            f"{topic_anchor}\n\n"
            f"**INSTRUCTIONS:**\n"
            f"1. Call RAG Search with the research idea\n"
            f"2. List ALL papers returned with their [P#] handles\n"
            f"3. Include: title, authors, year, source for each paper\n"
            f"4. If INSUFFICIENT_EVIDENCE returned, state: 'No relevant papers found'\n"
            f"5. Maximum 10 papers"
        ),
        agent=retrieval_agent,
        expected_output=(
            "List of papers in format:\n"
            "[P#] Title | Authors | Year | Source\n"
            "Abstract snippet: [first 2 sentences]\n"
            "Relevance: [brief justification]\n\n"
            "OR if no papers: 'INSUFFICIENT_EVIDENCE: [reason]'"
        ),
    )

    summarization_task = Task(
        description=(
            f"Summarize each paper from the retrieval results.\n\n"
            f"{topic_anchor}\n\n"
            f"**INSTRUCTIONS:**\n"
            f"1. Use RAG Search to get details for each paper [P#]\n"
            f"2. Extract: contribution, methodology, results, limitations\n"
            f"3. Include [P#] citation handles for every paper\n"
            f"4. Focus on aspects relevant to: '{user_idea}'\n"
            f"5. If paper not found in RAG, state 'Details not available'"
        ),
        agent=summarization_agent,
        expected_output=(
            "Structured summary per paper:\n"
            "[P#] Title:\n"
            "- Problem: [what problem solved]\n"
            "- Method: [approach/algorithm]\n"
            "- Results: [key findings with metrics]\n"
            "- Limitations: [acknowledged weaknesses]\n"
            "- Relevance to research idea: [connection]"
        ),
        context=[retrieval_task]
    )

    comparison_task = Task(
        description=(
            f"Compare methodologies across papers from summaries.\n\n"
            f"{topic_anchor}\n\n"
            f"**INSTRUCTIONS:**\n"
            f"1. Compare techniques, datasets, evaluation metrics\n"
            f"2. Identify common approaches vs variations\n"
            f"3. Note any conflicts or contradictions\n"
            f"4. Use [P#] citations for all comparisons\n"
            f"5. Create comparison table if 3+ papers available"
        ),
        agent=method_comparison_agent,
        expected_output=(
            "Comparative analysis with:\n"
            "- Common approaches: [list with [P#] citations]\n"
            "- Key differences: [variations noted]\n"
            "- Datasets used: [by paper]\n"
            "- Metrics: [evaluation methods]\n"
            "- Trends: [emerging patterns]"
        ),
        context=[summarization_task]
    )

    gap_task = Task(
        description=(
            f"Identify research gaps based on method comparison.\n\n"
            f"{topic_anchor}\n\n"
            f"**INSTRUCTIONS:**\n"
            f"1. Identify 3-5 gaps NOT addressed by existing papers\n"
            f"2. For each gap: explain importance and supporting evidence\n"
            f"3. Cite papers [P#] that reveal each gap\n"
            f"4. Rate gap importance: High/Medium/Low with justification\n"
            f"5. Connect gaps to research idea: '{user_idea}'"
        ),
        agent=gap_analysis_agent,
        expected_output=(
            "Gap #1: [description]\n"
            "  Importance: [High/Medium/Low]\n"
            "  Evidence: [P#] citations supporting this gap\n"
            "  Opportunity: [how it relates to research idea]\n\n"
            "[Repeat for 3-5 gaps]"
        ),
        context=[comparison_task]
    )

    novelty_task = Task(
        description=(
            f"Evaluate novelty of the research idea vs existing literature.\n\n"
            f"{topic_anchor}\n\n"
            f"**INSTRUCTIONS:**\n"
            f"1. Use RAG Search to find closest existing work\n"
            f"2. Use Citation Verifier to validate claims\n"
            f"3. Score novelty 0-100 based on evidence\n"
            f"4. Identify what's novel vs what's incremental\n"
            f"5. Cite specific papers [P#] for all comparisons\n"
            f"6. If uncertain, state uncertainty level"
        ),
        agent=novelty_agent,
        expected_output=(
            "Novelty Score: X/100\n"
            "Reasoning: [evidence-based justification with [P#] citations]\n"
            "Closest work: [P#] [title] - [similarity %]\n"
            "Novel aspects: [what's new]\n"
            "Incremental aspects: [what builds on prior work]\n"
            "Recommendation: [Highly Novel / Moderately Novel / Incremental]"
        ),
        context=[gap_task, summarization_task]
    )

    synthesis_task = Task(
        description=(
            f"SYNTHESIZE ALL PREVIOUS OUTPUTS INTO ONE COMPREHENSIVE REPORT.\n\n"
            f"**TOPIC ANCHOR:**\n"
            f"Research Idea: '{user_idea}'\n"
            f"Domains: {domain_str}\n\n"
            f"**YOU HAVE RECEIVED:**\n"
            f"1. Retrieved papers with [P#] handles\n"
            f"2. Paper summaries\n"
            f"3. Method comparison\n"
            f"4. Research gaps\n"
            f"5. Novelty assessment\n\n"
            f"**CRITICAL INSTRUCTIONS:**\n"
            f"- DO NOT ask for user input\n"
            f"- DO NOT start new research\n"
            f"- ONLY synthesize what previous agents provided\n"
            f"- Use REAL [P#] citations from the evidence\n"
            f"- Stay focused on: '{user_idea}'\n"
            f"- If any section lacks evidence, state: 'Limited evidence available'"
        ),
        agent=controller_agent,
        expected_output=(
            "**COMPREHENSIVE LITERATURE REVIEW REPORT**\n\n"
            "**Research Context**: [user's idea]\n"
            "**Domains**: [domains]\n"
            "**Papers Analyzed**: [count]\n\n"
            "**Executive Summary**: [150-200 words]\n\n"
            "**1. Retrieved Papers**: [list with [P#] citations]\n\n"
            "**2. Literature Analysis**: [summaries]\n\n"
            "**3. Methodology Comparison**: [analysis]\n\n"
            "**4. Research Gaps**: [gaps with evidence]\n\n"
            "**5. Novelty Assessment**: [score and reasoning]\n\n"
            "**6. Recommendations**: [actionable next steps]"
        ),
        context=[retrieval_task, summarization_task, comparison_task, gap_task, novelty_task]
    )

    return [
        retrieval_task,
        summarization_task,
        comparison_task,
        gap_task,
        novelty_task,
        synthesis_task,
    ]