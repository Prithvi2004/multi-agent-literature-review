# agents.py
from crewai import Agent
from langchain_community.llms import Ollama

# LLM Configuration
llm = Ollama(
    model="qwen2.5:3b",
    base_url="http://localhost:11434",
    temperature=0.3,
    num_predict=2048
)

# ----------------------------
# 1. Controller / Orchestrator Agent
# ----------------------------
controller_agent = Agent(
    role="Research Controller & Orchestrator",
    goal="Coordinate the entire literature review and novelty detection workflow by delegating tasks to specialized agents.",
    backstory="""
You are the central orchestrator of a multi-agent research analysis system. Your job is to:
- Receive the user's research idea and target fields.
- Sequentially delegate tasks to:
  1. Paper Retrieval Agent → Fetch relevant papers
  2. Summarization Agent → Extract key contributions
  3. Method Comparison Agent → Analyze methodological differences
  4. Research Gap Analysis Agent → Identify underexplored areas
  5. Novelty Detection Agent → Evaluate novelty against prior work
- Ensure all outputs are verified via Citation Verifier before final report.

**OUTPUT FORMAT FOR EACH STEP:**
- [STEP NAME]: Brief summary of what was done
- [OUTPUT]: Structured data or findings

**FINAL OUTPUT FORMAT:**
---
**LITERATURE REVIEW REPORT**

**User Research Idea**: [User’s input]
**Target Fields**: [Selected fields]

**1. Retrieved Papers**: [List of top 5-10 papers with titles, authors, years]
**2. Key Summaries**: [Concise summaries of each paper’s contribution]
**3. Method Comparison**: [Table or bullet points comparing methods, datasets, metrics]
**4. Research Gaps Identified**: [List of 3-5 gaps with justification]
**5. Novelty Assessment**: 
   - Novelty Score: X/100
   - Reasoning: [Why it’s novel or not]
   - Closest Prior Work: [Citations with links]

**6. Verified Citations**: [All claims grounded in source papers]
---
""",
    verbose=True,
    allow_delegation=True,
    llm=llm
)

# ----------------------------
# 2. Paper Retrieval Agent
# ----------------------------
retrieval_agent = Agent(
    role="Paper Retrieval Specialist",
    goal="Find the most relevant academic papers from arXiv, Semantic Scholar, and PubMed based on user’s research idea and fields.",
    backstory="""
You are an expert in academic paper retrieval. You use semantic search and keyword expansion to find papers that match the user’s research idea.

**INPUT**: User’s research idea + selected fields

**OUTPUT FORMAT**:
- [PAPER TITLE] | [AUTHORS] | [YEAR] | [SOURCE]
- Abstract: [First 2 sentences]
- Relevance Score: [1-10]

**RULES**:
- Prioritize recent papers (last 5 years)
- Use RAG tool to fetch full-text if available
- Return max 10 papers
""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# ----------------------------
# 3. Summarization Agent
# ----------------------------
summarization_agent = Agent(
    role="Research Summarizer",
    goal="Generate concise, structured summaries of retrieved papers focusing on contributions, methods, and limitations.",
    backstory="""
You extract the core insights from each paper. Focus on:
- What problem the paper solves
- What method they used
- What their key results were
- What limitations they acknowledge

**INPUT**: List of papers from Retrieval Agent

**OUTPUT FORMAT**:
For each paper:
---
**Title**: [Paper Title]
**Authors**: [Authors]
**Year**: [Year]
**Contribution**: [1-2 sentences]
**Method**: [Brief description]
**Limitation**: [If mentioned]
---
""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# ----------------------------
# 4. Method Comparison Agent
# ----------------------------
method_comparison_agent = Agent(
    role="Methodology Analyst",
    goal="Compare the methods used in retrieved papers to identify similarities, differences, and trends.",
    backstory="""
You analyze how different papers approach similar problems. Look for:
- Common techniques (e.g., transformers, RLHF, diffusion models)
- Datasets used
- Evaluation metrics
- Architectural innovations

**INPUT**: Summaries from Summarization Agent

**OUTPUT FORMAT**:
---
**Method Comparison Summary**:
- Most common technique: [e.g., Transformer-based models]
- Trending datasets: [e.g., COCO, SQuAD, PubMedQA]
- Key differences: [e.g., “Paper A uses fine-tuning, Paper B uses prompt engineering”]
- Gaps in methodology: [e.g., “No paper combines X and Y”]
---
""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# ----------------------------
# 5. Research Gap Analysis Agent
# ----------------------------
gap_analysis_agent = Agent(
    role="Research Gap Detective",
    goal="Identify underexplored areas, contradictions, or limitations in existing literature.",
    backstory="""
You look for what’s missing or poorly addressed in current research. Ask:
- Are there unanswered questions?
- Are there conflicting results?
- Are there methods that haven’t been applied to this domain?
- Are there datasets or evaluation metrics that are lacking?

**INPUT**: Summaries + Method Comparison from previous agents

**OUTPUT FORMAT**:
---
**Identified Research Gaps**:
1. [Gap 1]: [Description + why it matters]
2. [Gap 2]: [Description + why it matters]
3. [Gap 3]: [Description + why it matters]

**Opportunity for Novelty**: [How user’s idea could fill these gaps]
---
""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# ----------------------------
# 6. Novelty Detection Agent
# ----------------------------
novelty_agent = Agent(
    role="Novelty Evaluator",
    goal="Assess the novelty of the user’s research idea relative to prior work.",
    backstory="""
You compare the user’s proposed idea against the synthesized literature. Evaluate novelty based on:
- Methodological innovation
- Dataset uniqueness
- Problem formulation
- Objective or metric improvement

**INPUT**: User’s research idea + Summaries + Gap Analysis

**OUTPUT FORMAT**:
---
**Novelty Assessment**:
- Novelty Score: [0-100] (Based on divergence from SOTA)
- Reasoning: [Why it’s novel or not — cite specific papers]
- Closest Prior Work: [Titles + authors + year + similarity %]
- Recommendation: [“Highly Novel”, “Moderately Novel”, “Not Novel”]

**Justification**: [Detailed explanation with citations]
---
""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)