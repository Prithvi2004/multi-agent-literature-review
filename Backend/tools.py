# tools.py
from crewai.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from typing import Optional


# Placeholder for dynamic RAG tool
class RAGTool:
    """Thin wrapper around the shared RAGPipeline instance.

    The actual RAGPipeline object is injected in main.py so this
    module stays importable without side effects.
    """

    def __init__(self):
        self.rag = None  # Set externally in main.py

    def run(self, query: str) -> str:
        if self.rag is None:
            return "RAG not initialized. No local corpus is available."
        return self.rag.search(query)


class CitationVerifier:
    """Evidence-first citation helper built on top of RAG.

    This tool does not "magically" verify claims. Instead, it:
    - Retrieves the top-k most similar passages to the claim
    - Returns them in a structured, human-readable way
    - Explicitly flags when no supporting evidence is found

    Agents are expected to base their judgments only on this evidence
    and must surface uncertainty when evidence is weak or absent.
    """

    def __init__(self, rag_tool: Optional[RAGTool] = None):
        self._rag_tool = rag_tool

    def run(self, claim: str) -> str:
        if self._rag_tool is None or self._rag_tool.rag is None:
            return "Citation verifier unavailable: RAG corpus not initialized."

        evidence = self._rag_tool.rag.search(claim, k=6)
        if "No supporting passages found" in evidence:
            return (
                "⚠️ Unable to find strong supporting evidence for this claim in the current corpus.\n"
                "Use cautious language, mark this as uncertain, and avoid inventing citations."
            )

        header = (
            "Below are the most relevant passages from the indexed literature. "
            "Only treat the claim as strongly supported if at least one passage "
            "directly states or numerically supports it. If not, mark it as "
            "partially supported or unsupported and explain the gap.\n"
        )
        return header + "\n" + evidence


# External tools (fallback, e.g., for metadata lookups beyond local corpus)
search_tool = DuckDuckGoSearchRun()


# Tool instances wired to the shared RAG wrapper
rag_tool = RAGTool()
citation_verifier = CitationVerifier(rag_tool)

@tool("RAG Search")
def rag_tool_instance(query: str) -> str:
    """Search the locally indexed academic literature using semantic similarity.
    Always use this before answering, and cite passages using their [P#] handles.
    
    Args:
        query: The search query string
    
    Returns:
        Relevant passages from the indexed literature with citation handles
    """
    return rag_tool.run(query)

@tool("Citation Verifier")
def citation_verifier_tool(claim: str) -> str:
    """Retrieve evidence passages related to a specific factual claim from the local corpus.
    Use it to check whether a claim is strongly supported, partially supported, or unsupported.
    
    Args:
        claim: The factual claim to verify
    
    Returns:
        Evidence passages with support assessment
    """
    return citation_verifier.run(claim)