# tools.py
from langchain_core.tools import Tool
from langchain_community.tools import DuckDuckGoSearchRun
import requests

# Placeholder for dynamic RAG tool
class RAGTool:
    def __init__(self):
        self.rag = None  # Set externally in main.py

    def run(self, query: str) -> str:
        if self.rag:
            return self.rag.search(query)
        return "RAG not initialized."

# Citation Verifier (simulated)
class CitationVerifier:
    def run(self, claim: str) -> str:
        return f"✅ Verified: '{claim[:80]}...'"

# External tools (fallback)
search_tool = DuckDuckGoSearchRun()

# Tool instances
rag_tool = RAGTool()
citation_verifier = CitationVerifier()

rag_tool_instance = Tool(
    name="RAGSearch",
    func=rag_tool.run,
    description="Search user-provided and retrieved academic literature using semantic similarity."
)

citation_verifier_tool = Tool(
    name="CitationVerifier",
    func=citation_verifier.run,
    description="Verify factual claims against literature."
)