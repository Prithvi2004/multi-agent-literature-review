# tasks.py
from crewai import Task
from agents import (
    retrieval_agent,
    decomposition_agent,
    reasoning_agent,
    gap_novelty_agent,
    synthesis_agent,
    quality_control_agent
)

def create_tasks(user_idea: str, domains: list):
    """Create RAG-first workflow tasks with strict PhD-level requirements."""

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

    # 1. Retrieval Task
    retrieval_task = Task(
        description=(
            f"Execute a comprehensive search strategy to find impactful papers for: '{user_idea}'\n"
            f"in domains: {domain_str}.\n"
            f"1. Use RAG Search to retrieve top papers.\n"
            f"2. Ensure a mix of seminal papers and recent (last 3 years) advances.\n"
            f"3. Filter for high relevance.\n"
            f"{topic_anchor}"
        ),
        agent=retrieval_agent,
        expected_output=(
            "Structured list of top 10-15 papers:\n"
            "- [P#] Title | Authors | Year | Venue\n"
            "- Relevance justification\n"
            "- Abstract snippet"
        ),
    )

    # 2. Decomposition Task
    decomposition_task = Task(
        description=(
            f"Analyze the retrieved papers deeply. For EACH relevant paper found:\n"
            f"1. Extract the Core Problem, Hypothesis, Methodology (Steps/Algorithms), and Key Result (metrics).\n"
            f"2. Extract explicit Limitations stated by authors.\n"
            f"3. Ignore fluff; focus on technical substance.\n"
            f"{topic_anchor}"
        ),
        agent=decomposition_agent,
        expected_output=(
            "JSON-like or structured blocks per paper:\n"
            "[P#] Title\n"
            "   Problem: ...\n"
            "   Method: ...\n"
            "   Results: ...\n"
            "   Limitations: ..."
        ),
        context=[retrieval_task],
        async_execution=True # Enable parallel processing for paper analysis
    )

    # 3. Cross-Paper Reasoning Task
    reasoning_task = Task(
        description=(
            f"Perform comparative analysis across the extracted knowledge.\n"
            f"1. Group papers by approach/school of thought.\n"
            f"2. Compare conflicting evidence: Does Paper A contradict Paper B?\n"
            f"3. Trace methodology evolution: How did methods improve over time?\n"
            f"4. Create a Comparative Matrix of features/performance.\n"
            f"{topic_anchor}"
        ),
        agent=reasoning_agent,
        expected_output=(
            "1. Thematic Taxonomy (grouping of approaches)\n"
            "2. Comparative Matrix (table of methods vs metrics)\n"
            "3. Consensus vs Conflict Analysis (where papers agree/disagree)"
        ),
        context=[decomposition_task]
    )

    # 4. Gap & Novelty Task
    gap_novelty_task = Task(
        description=(
            f"Identify RESEARCH GAPS and assess NOVELTY of '{user_idea}'.\n"
            f"1. Based on the analysis, what is missing? (Unsolved problems, weak baselines, etc.)\n"
            f"2. Compare '{user_idea}' to the closest existing papers.\n"
            f"3. Score Novelty (0-100) with strict justification.\n"
            f"{topic_anchor}"
        ),
        agent=gap_novelty_agent,
        expected_output=(
            "1. Validated Research Gaps (with [P#] citations)\n"
            "2. Novelty Assessment (Score + Reasoning)\n"
            "3. Critical Differentiators"
        ),
        context=[reasoning_task]
    )

    # 5. Synthesis Task
    synthesis_task = Task(
        description=(
            f"Write a PhD-level Literature Review merging all insights.\n"
            f"Structure:\n"
            f"- Information Landscape (Overview)\n"
            f"- Thematic Evolution (History of ideas)\n"
            f"- Methodological Deep Dive (Comparative)\n"
            f"- The Gap Analysis\n"
            f"- Future Directions\n"
            f"TONE: Formal, dense, authoritative. NO placeholders.\n"
            f"{topic_anchor}"
        ),
        agent=synthesis_agent,
        expected_output=(
            "A complete 1500+ word Literature Review Markdown.\n"
            "Including 'References' section with [P#] mapping."
        ),
        context=[retrieval_task, decomposition_task, reasoning_task, gap_novelty_task]
    )

    # 6. Quality Control Task
    quality_control_task = Task(
        description=(
            f"Review the draft Literature Review. CRITIQUE and REFINE it.\n"
            f"1. Check all [P#] citations correspond to real papers in the context.\n"
            f"2. Remove any vague claims ('performance was good') -> replace with metrics if available or delete.\n"
            f"3. Ensure the flow is logical. If not, re-write sections.\n"
            f"4. Final Output must be the POLISHED versions.\n"
            f"{topic_anchor}"
        ),
        agent=quality_control_agent,
        expected_output=(
            "FINAL REVISED LITERATURE REVIEW.\n"
            "Ready for submission."
        ),
        context=[synthesis_task, retrieval_task] # Needs retrieval_task to verify citations
    )

    return [
        retrieval_task,
        decomposition_task,
        reasoning_task,
        gap_novelty_task,
        synthesis_task,
        quality_control_task
    ]
