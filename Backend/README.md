# Multi-Agent LLM for Literature Review & Novelty Detection

Automated system that uses multiple specialized LLM agents to:
- Retrieve relevant academic papers
- Summarize and compare methodologies
- Identify research gaps
- Evaluate novelty of user-provided ideas

## Architecture

[User Interface] → [Controller / Orchestrator Agent]
                         ↓
       ┌───────────────┴───────────────┐
       ↓                               ↓
[Paper Retrieval Agent]         [Summarization Agent]
       ↓                               ↓
[RAG Module] ←→ [Vector DB (FAISS)]    ↓
       ↓                               ↓
[Method Comparison Agent] ←─────────────┘
       ↓
[Research Gap Analysis Agent]
       ↓
[Novelty Detection Agent]
       ↓
[Citation Verification Module]
       ↓
[Final Literature Review & Novelty Report]