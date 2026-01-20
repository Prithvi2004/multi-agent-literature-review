# tools.py
"""Enhanced RAG tools with EvidenceStore integration and validation."""

from crewai.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RAGTool:
    """Thin wrapper around the shared RAGPipeline instance.

    The actual RAGPipeline object is injected in main.py so this
    module stays importable without side effects.
    """

    def __init__(self):
        self.rag = None  # Set externally in main.py

    def run(self, query: str) -> str:
        if self.rag is None:
            return "INSUFFICIENT_EVIDENCE: RAG not initialized. No local corpus is available."
        
        result = self.rag.search(query)
        
        # Check if result indicates insufficient evidence
        if not result or "INSUFFICIENT_EVIDENCE" in result:
            logger.warning(f"RAG search returned no results for query: {query[:50]}...")
            return f"INSUFFICIENT_EVIDENCE: No supporting passages found for '{query[:50]}...'"
        
        return result


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
            return "INSUFFICIENT_EVIDENCE: Citation verifier unavailable - RAG corpus not initialized."

        evidence = self._rag_tool.rag.search(claim, k=6)
        
        if "INSUFFICIENT_EVIDENCE" in evidence or not evidence:
            return (
                "⚠️ INSUFFICIENT_EVIDENCE: Unable to find strong supporting evidence.\n"
                "REQUIRED ACTION: Use cautious language, mark this as UNCERTAIN, "
                "and DO NOT invent citations. State clearly what evidence is missing."
            )

        header = (
            "📚 EVIDENCE RETRIEVED - Below are the most relevant passages.\n"
            "INSTRUCTIONS:\n"
            "- Only treat claim as SUPPORTED if passage directly states or numerically supports it\n"
            "- If no direct support found, mark as PARTIALLY_SUPPORTED or UNSUPPORTED\n"
            "- Cite using exact [P#] handles shown below\n"
            "---\n"
        )
        return header + evidence


class EvidenceValidator:
    """Validates that outputs contain proper citations from the Evidence Store."""
    
    def __init__(self):
        self._evidence_store = None
    
    def set_store(self, store):
        """Inject the evidence store instance."""
        self._evidence_store = store
    
    def validate_output(self, text: str) -> tuple[bool, str]:
        """Check if output contains valid citations.
        
        Returns:
            Tuple of (is_valid, validation_message)
        """
        import re
        
        # Find all P# citations in text
        citations = re.findall(r'\[P(\d+)\]', text)
        
        if not citations:
            return (False, "WARNING: No [P#] citations found in output. All claims must cite evidence.")
        
        # Validate each citation if evidence store is available
        if self._evidence_store:
            invalid_citations = []
            for num in citations:
                handle = f"P{num}"
                is_valid, _ = self._evidence_store.validate_citation(handle)
                if not is_valid:
                    invalid_citations.append(handle)
            
            if invalid_citations:
                return (False, f"INVALID_CITATIONS: These handles don't exist: {invalid_citations}")
        
        return (True, f"OK: Found {len(set(citations))} valid citations")
    
    def check_topic_drift(self, query: str, output: str, threshold: float = 0.2) -> tuple[bool, str]:
        """Check if output relates to the original query.
        
        Returns:
            Tuple of (is_on_topic, message)
        """
        # Extract key terms from query
        query_terms = set(word.lower() for word in query.split() if len(word) > 4)
        
        if not query_terms:
            return (True, "OK: No key terms to validate")
        
        # Check how many query terms appear in output
        output_lower = output.lower()
        matches = sum(1 for term in query_terms if term in output_lower)
        score = matches / len(query_terms)
        
        if score < threshold:
            return (False, f"TOPIC_DRIFT_WARNING: Only {score:.0%} of query terms found in output")
        
        return (True, f"OK: {score:.0%} topic relevance")

class ContextTool:
    """Tool for agents to read and write to the shared Research Context."""
    
    def __init__(self):
        self.context = None # Injected by main.py
        
    def set_context(self, context):
        self.context = context
        
    def log_insight(self, content: str, agent_name: str) -> str:
        if self.context:
            self.context.add_insight(content, source_agent=agent_name)
            return "✅ Insight logged to Research Context."
        return "❌ Context not initialized."
        
    def read_summary(self) -> str:
        if self.context:
            return self.context.get_context_summary()
        return "No context available."

# Initialize Context Tool
context_tool_wrapper = ContextTool()

@tool("Read Research Context")
def read_context_tool() -> str:
    """Read the current summary of insights, gaps, and findings from the shared session memory.
    Use this to see what other agents have found so far to avoid duplication."""
    return context_tool_wrapper.read_summary()

@tool("Log Insight")
def log_insight_tool(insight: str, agent_name: str) -> str:
    """Log a key finding or insight into the shared memory. 
    Args:
        insight: The finding to record
        agent_name: Your role name
    """
    return context_tool_wrapper.log_insight(insight, agent_name)


# External tools (fallback, e.g., for metadata lookups beyond local corpus)
search_tool = DuckDuckGoSearchRun()

# Tool instances wired to the shared RAG wrapper
rag_tool = RAGTool()
citation_verifier = CitationVerifier(rag_tool)
evidence_validator = EvidenceValidator()


@tool("RAG Search")
def rag_tool_instance(query: str) -> str:
    """Search the locally indexed academic literature using semantic similarity.
    
    IMPORTANT: Always use this tool FIRST before making any claims about papers.
    Only cite papers that appear in the results using their [P#] handles.
    If results show INSUFFICIENT_EVIDENCE, do NOT invent papers - report the gap.
    
    Args:
        query: The search query string
    
    Returns:
        Relevant passages from the indexed literature with [P#] citation handles.
        If no relevant papers found, returns INSUFFICIENT_EVIDENCE message.
    """
    return rag_tool.run(query)


@tool("Citation Verifier")
def citation_verifier_tool(claim: str) -> str:
    """Retrieve evidence passages related to a specific factual claim from the local corpus.
    
    Use this to verify whether a claim is:
    - SUPPORTED: Direct evidence found with citations
    - PARTIALLY_SUPPORTED: Related evidence but not direct
    - UNSUPPORTED: No evidence found - mark as uncertain
    
    Args:
        claim: The factual claim to verify
    
    Returns:
        Evidence passages with support assessment and [P#] handles for citation.
    """
    return citation_verifier.run(claim)


@tool("Validate Output")
def validate_output_tool(text: str) -> str:
    """Validate that an output contains proper citations and stays on topic.
    
    Use this to check your final output before submitting.
    
    Args:
        text: The output text to validate
    
    Returns:
        Validation results indicating any issues found.
    """
    is_valid, message = evidence_validator.validate_output(text)
    return f"{'✅' if is_valid else '❌'} {message}"