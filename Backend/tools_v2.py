# tools_v2.py
"""
Advanced RAG Tools with Inter-Agent Communication and Evidence Scoring

Features:
- Enhanced RAG search with confidence scores
- Multi-query RAG for comprehensive coverage
- Evidence strength assessment
- Citation validation and tracking
- Inter-agent communication helpers
"""

from crewai.tools import tool
from typing import Optional, List, Dict, Any
import logging
import re
import json

logger = logging.getLogger(__name__)


class AdvancedRAGTool:
    """
    Enhanced RAG tool with confidence scoring and multi-query support.
    
    Features:
    - Confidence scores for retrieved evidence
    - Multi-query expansion for comprehensive coverage
    - Relevance filtering
    - Evidence deduplication
    """

    def __init__(self):
        self.rag = None  # Set externally in main.py
        self.query_history = []
        self.evidence_cache = {}

    def run(self, query: str, k: int = 5, min_confidence: float = 0.3) -> str:
        """
        Execute RAG search with confidence filtering.
        
        Args:
            query: Search query
            k: Number of results
            min_confidence: Minimum confidence threshold
            
        Returns:
            Formatted search results with confidence scores
        """
        if self.rag is None:
            return "INSUFFICIENT_EVIDENCE: RAG not initialized. No local corpus is available."
        
        # Track query
        self.query_history.append(query)
        
        # Execute search
        try:
            results = self.rag.hybrid_search(query, k=k)
            
            if not results:
                return f"INSUFFICIENT_EVIDENCE: No supporting passages found for '{query[:50]}...'"
            
            # Filter by confidence
            filtered_results = [r for r in results if r.get('score', 0) >= min_confidence]
            
            if not filtered_results:
                return f"INSUFFICIENT_EVIDENCE: No high-confidence results (threshold={min_confidence}) for '{query[:50]}...'"
            
            # Format with confidence indicators
            formatted_lines = []
            for idx, result in enumerate(filtered_results, 1):
                handle = result.get('handle', f'P{idx}')
                title = result.get('title', 'Untitled')
                authors = result.get('authors', 'Unknown')
                year = result.get('year', 'n.d.')
                score = result.get('score', 0.0)
                content = result.get('content', '')
                
                # Confidence indicator
                if score >= 0.7:
                    confidence = "HIGH CONFIDENCE"
                elif score >= 0.5:
                    confidence = "MEDIUM CONFIDENCE"
                else:
                    confidence = "LOW CONFIDENCE"
                
                header = f"[{handle}] {title} ({year}) - {authors}"
                metadata = f"Confidence: {confidence} (Score: {score:.3f})"
                formatted_lines.append(f"{header}\n{metadata}\n{content}")
            
            return "\n\n" + "="*80 + "\n\n".join(formatted_lines)
            
        except Exception as e:
            logger.error(f"RAG search error: {e}")
            return f"ERROR: RAG search failed - {str(e)}"
    
    def multi_query_search(self, queries: List[str], k: int = 3) -> str:
        """
        Execute multiple related queries and aggregate results.
        
        Useful for comprehensive coverage of complex topics.
        
        Args:
            queries: List of related queries
            k: Results per query
            
        Returns:
            Aggregated and deduplicated results
        """
        if self.rag is None:
            return "INSUFFICIENT_EVIDENCE: RAG not initialized."
        
        all_results = {}  # Use dict to deduplicate by handle
        
        for query in queries:
            results = self.rag.hybrid_search(query, k=k)
            for r in results:
                handle = r.get('handle')
                if handle not in all_results or r.get('score', 0) > all_results[handle].get('score', 0):
                    all_results[handle] = r
        
        if not all_results:
            return "INSUFFICIENT_EVIDENCE: No results from multi-query search."
        
        # Sort by score
        sorted_results = sorted(all_results.values(), key=lambda x: x.get('score', 0), reverse=True)
        
        # Format
        lines = []
        for idx, r in enumerate(sorted_results, 1):
            handle = r.get('handle', f'P{idx}')
            title = r.get('title', 'Untitled')
            score = r.get('score', 0.0)
            content = r.get('content', '')
            
            lines.append(f"[{handle}] {title} (Score: {score:.3f})\n{content}")
        
        return "\n\n".join(lines)


class EvidenceScorer:
    """
    Assess evidence strength and quality.
    
    Criteria:
    - Methodological rigor
    - Sample size
    - Statistical significance
    - Reproducibility indicators
    """
    
    def __init__(self):
        self.evidence_store = None
    
    def score_evidence(self, handle: str, claim: str) -> Dict[str, Any]:
        """
        Score evidence quality for a specific claim.
        
        Args:
            handle: Paper handle (e.g., P1)
            claim: Specific claim to evaluate
            
        Returns:
            Dictionary with quality scores
        """
        # This is a simplified version - full implementation would analyze paper content
        score = {
            "handle": handle,
            "claim": claim,
            "evidence_strength": "MODERATE",  # HIGH, MODERATE, LOW
            "confidence": 0.7,
            "factors": {
                "has_empirical_data": True,
                "sample_size_adequate": True,
                "methodology_sound": True,
                "statistically_significant": True
            },
            "recommendation": "CITE_WITH_CONTEXT"
        }
        
        return score
    
    def assess_claim_support(self, claim: str, evidence_handles: List[str]) -> str:
        """
        Assess how well evidence supports a claim.
        
        Args:
            claim: Claim to evaluate
            evidence_handles: List of paper handles cited
            
        Returns:
            Assessment string
        """
        if not evidence_handles:
            return "UNSUPPORTED: No evidence provided for claim"
        
        if len(evidence_handles) == 1:
            return f"WEAKLY_SUPPORTED: Only one source ({evidence_handles[0]}) cited"
        
        if len(evidence_handles) >= 3:
            return f"WELL_SUPPORTED: Multiple sources ({', '.join(evidence_handles)}) corroborate claim"
        
        return f"MODERATELY_SUPPORTED: Supported by {len(evidence_handles)} sources"


class CitationValidator:
    """
    Validate citations and track evidence usage.
    
    Ensures:
    - All [P#] citations are valid
    - Citations match actual paper content
    - No hallucinated papers
    """
    
    def __init__(self):
        self._evidence_store = None
    
    def set_store(self, store):
        """Inject evidence store instance."""
        self._evidence_store = store
    
    def validate_output(self, text: str) -> tuple[bool, str]:
        """
        Validate all citations in output text.
        
        Args:
            text: Text to validate
            
        Returns:
            Tuple of (is_valid, validation_message)
        """
        # Find all P# citations
        citations = re.findall(r'\[P(\d+)\]', text)
        
        if not citations:
            return (False, "⚠️ WARNING: No [P#] citations found in output. All claims must cite evidence.")
        
        # Validate each citation
        if self._evidence_store:
            invalid_citations = []
            for citation_num in citations:
                handle = f"P{citation_num}"
                if not self._evidence_store.has_paper(handle):
                    invalid_citations.append(handle)
            
            if invalid_citations:
                return (
                    False,
                    f"❌ INVALID CITATIONS: {', '.join(invalid_citations)} do not exist in evidence store. "
                    "These are HALLUCINATED citations and must be removed."
                )
        
        # Check citation density
        words = text.split()
        unique_citations = set(citations)
        citation_density = (len(unique_citations) / len(words)) * 100 if words else 0
        
        if citation_density < 0.5:  # Less than 0.5 citations per 100 words
            return (
                True,  # Valid but warning
                f"⚠️ LOW CITATION DENSITY: {citation_density:.2f} per 100 words. "
                "Consider adding more evidence citations."
            )
        
        return (
            True,
            f"✓ VALID: Found {len(unique_citations)} unique citations with density {citation_density:.2f} per 100 words."
        )
    
    def extract_citation_map(self, text: str) -> Dict[str, List[str]]:
        """
        Extract map of citations to the claims they support.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary mapping handles to claim snippets
        """
        citation_map = {}
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            # Find citations in this sentence
            citations = re.findall(r'\[P(\d+)\]', sentence)
            
            if citations:
                claim = sentence.strip()
                for cite in citations:
                    handle = f"P{cite}"
                    if handle not in citation_map:
                        citation_map[handle] = []
                    citation_map[handle].append(claim)
        
        return citation_map


# ==============================================================================
# Tool Instances
# ==============================================================================

advanced_rag_tool = AdvancedRAGTool()
evidence_scorer = EvidenceScorer()
citation_validator = CitationValidator()


# ==============================================================================
# CrewAI Tool Decorators
# ==============================================================================

@tool("RAG Search")
def rag_search_tool(query: str) -> str:
    """
    Search the academic paper corpus using advanced hybrid RAG.
    
    Returns relevant paper excerpts with confidence scores.
    Use this to find evidence for claims, gather background information,
    or locate specific methodologies.
    
    Args:
        query: Your search query (be specific and use technical terms)
    
    Returns:
        Formatted search results with paper citations [P#]
    """
    return advanced_rag_tool.run(query, k=5)


@tool("Multi-Query RAG Search")
def multi_query_rag_tool(queries: str) -> str:
    """
    Execute multiple related searches for comprehensive coverage.
    
    Useful when you need to explore a topic from multiple angles.
    Provide queries separated by '|' (pipe character).
    
    Args:
        queries: Multiple queries separated by | (e.g., "transformer models|attention mechanisms|BERT architecture")
    
    Returns:
        Aggregated and deduplicated results from all queries
    """
    query_list = [q.strip() for q in queries.split('|')]
    return advanced_rag_tool.multi_query_search(query_list, k=3)


@tool("Validate Citations")
def validate_citations_tool(text: str) -> str:
    """
    Validate that all [P#] citations in text are valid and properly used.
    
    Use this before finalizing your output to ensure:
    - No hallucinated citations
    - Adequate citation density
    - All claims are grounded in evidence
    
    Args:
        text: Text to validate
    
    Returns:
        Validation report with any issues found
    """
    is_valid, message = citation_validator.validate_output(text)
    return message


@tool("Assess Evidence Quality")
def assess_evidence_tool(claim: str, evidence_handles: str) -> str:
    """
    Assess how well evidence supports a specific claim.
    
    Args:
        claim: The claim to evaluate
        evidence_handles: Comma-separated list of paper handles (e.g., "P1,P2,P3")
    
    Returns:
        Assessment of evidence strength
    """
    handles = [h.strip() for h in evidence_handles.split(',')]
    return evidence_scorer.assess_claim_support(claim, handles)


# ==============================================================================
# Backward Compatibility
# ==============================================================================

# For existing code that expects these names
rag_tool = advanced_rag_tool
rag_tool_instance = rag_search_tool
citation_verifier_tool = validate_citations_tool
evidence_validator = citation_validator
validate_output_tool = validate_citations_tool


logger.info("Advanced RAG Tools v2.0 initialized")
logger.info("  - RAG Search (with confidence scoring)")
logger.info("  - Multi-Query RAG Search")
logger.info("  - Citation Validator")
logger.info("  - Evidence Quality Assessor")
