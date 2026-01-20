# evidence_store.py
"""
Central Evidence Store - Singleton repository for all paper evidence.

This module provides a thread-safe, centralized store for all retrieved papers
and their chunks. All agents MUST use this store for grounded evidence.

Schema:
EvidenceStore = {
  "paper_id": {
    "title": str,
    "authors": list[str],
    "year": int,
    "venue": str,
    "doi_or_arxiv": str,
    "chunks": [{"chunk_id": str, "text": str, "embedding_id": str}]
  }
}
"""

import json
import os
import hashlib
import threading
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

EVIDENCE_STORE_PATH = "evidence_store.json"


class EvidenceStore:
    """Thread-safe singleton for centralized paper evidence management.
    
    All agents share this store to ensure:
    - No hallucinated papers
    - Consistent [P#] handle references
    - Grounded evidence for all claims
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._store: Dict[str, Dict[str, Any]] = {}
        self._handle_map: Dict[str, str] = {}  # paper_id -> P# handle
        self._next_handle = 1
        self._metadata = {
            "created_at": datetime.now().isoformat(),
            "last_updated": None,
            "total_papers": 0,
            "total_chunks": 0
        }
        self._load()
        self._initialized = True
        logger.info(f"EvidenceStore initialized with {len(self._store)} papers")
    
    def _generate_paper_id(self, title: str, authors: str = "") -> str:
        """Generate unique paper ID from title and authors."""
        normalized = f"{title.lower().strip()}:{authors.lower().strip()}"
        return hashlib.md5(normalized.encode()).hexdigest()[:12]
    
    def _load(self) -> None:
        """Load evidence store from disk."""
        if os.path.exists(EVIDENCE_STORE_PATH):
            try:
                with open(EVIDENCE_STORE_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._store = data.get("papers", {})
                    self._handle_map = data.get("handle_map", {})
                    self._next_handle = data.get("next_handle", 1)
                    self._metadata = data.get("metadata", self._metadata)
                logger.info(f"Loaded {len(self._store)} papers from evidence store")
            except Exception as e:
                logger.error(f"Error loading evidence store: {e}")
                self._store = {}
    
    def _save(self) -> None:
        """Persist evidence store to disk."""
        self._metadata["last_updated"] = datetime.now().isoformat()
        self._metadata["total_papers"] = len(self._store)
        self._metadata["total_chunks"] = sum(
            len(p.get("chunks", [])) for p in self._store.values()
        )
        
        try:
            with open(EVIDENCE_STORE_PATH, 'w', encoding='utf-8') as f:
                json.dump({
                    "papers": self._store,
                    "handle_map": self._handle_map,
                    "next_handle": self._next_handle,
                    "metadata": self._metadata
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving evidence store: {e}")
    
    def add_paper(
        self,
        title: str,
        authors: List[str] | str,
        year: int | str,
        venue: str = "Unknown",
        doi_or_arxiv: str = "",
        abstract: str = "",
        url: str = "",
        source: str = "Unknown"
    ) -> str:
        """Add a paper to the evidence store.
        
        Returns:
            The P# handle for this paper (e.g., "P1", "P2")
        """
        # Normalize authors
        if isinstance(authors, str):
            authors_list = [a.strip() for a in authors.split(",") if a.strip()]
        else:
            authors_list = list(authors)
        
        # Normalize year
        if isinstance(year, str):
            try:
                year = int(year) if year else 0
            except ValueError:
                year = 0
        
        paper_id = self._generate_paper_id(title, str(authors))
        
        # Check if already exists
        if paper_id in self._store:
            return self._handle_map.get(paper_id, f"P{self._next_handle}")
        
        # Assign P# handle
        handle = f"P{self._next_handle}"
        self._next_handle += 1
        self._handle_map[paper_id] = handle
        
        # Create chunks from abstract
        chunks = []
        if abstract:
            # Split abstract into chunks of ~300 chars
            chunk_size = 300
            for i in range(0, len(abstract), chunk_size):
                chunk_text = abstract[i:i + chunk_size]
                chunk_id = f"{paper_id}_chunk_{i // chunk_size}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "embedding_id": f"emb_{chunk_id}"
                })
        
        # Store paper
        self._store[paper_id] = {
            "paper_id": paper_id,
            "handle": handle,
            "title": title,
            "authors": authors_list,
            "year": year,
            "venue": venue,
            "doi_or_arxiv": doi_or_arxiv,
            "url": url,
            "source": source,
            "abstract": abstract,
            "chunks": chunks,
            "added_at": datetime.now().isoformat()
        }
        
        self._save()
        logger.info(f"Added paper [{handle}]: {title[:50]}...")
        return handle
    
    def add_papers_batch(self, papers: List[Dict[str, Any]]) -> List[str]:
        """Add multiple papers efficiently.
        
        Args:
            papers: List of paper dicts with keys: title, authors, year, abstract, source, url
            
        Returns:
            List of P# handles
        """
        handles = []
        for p in papers:
            handle = self.add_paper(
                title=p.get("title", "Untitled"),
                authors=p.get("authors", "Unknown"),
                year=p.get("year", 0),
                venue=p.get("venue", p.get("source", "Unknown")),
                doi_or_arxiv=p.get("doi_or_arxiv", p.get("url", "")),
                abstract=p.get("abstract", ""),
                url=p.get("url", ""),
                source=p.get("source", "Unknown")
            )
            handles.append(handle)
        return handles
    
    def get_paper_by_handle(self, handle: str) -> Optional[Dict[str, Any]]:
        """Get paper by its P# handle (e.g., 'P1', 'P2')."""
        for paper_id, h in self._handle_map.items():
            if h == handle:
                return self._store.get(paper_id)
        return None
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get paper by its internal ID."""
        return self._store.get(paper_id)
    
    def get_all_papers(self) -> List[Dict[str, Any]]:
        """Get all papers in the store."""
        return list(self._store.values())
    
    def get_paper_count(self) -> int:
        """Get total number of papers in store."""
        return len(self._store)
    
    def validate_citation(self, handle: str) -> tuple[bool, Optional[Dict[str, Any]]]:
        """Validate that a citation handle exists and return paper info.
        
        Args:
            handle: P# handle to validate (e.g., 'P1', 'P2', '[P1]')
            
        Returns:
            Tuple of (is_valid, paper_dict_or_none)
        """
        # Normalize handle
        clean_handle = handle.strip().replace("[", "").replace("]", "").upper()
        if not clean_handle.startswith("P"):
            clean_handle = f"P{clean_handle}"
        
        paper = self.get_paper_by_handle(clean_handle)
        return (paper is not None, paper)
    
    def format_citation(self, handle: str, style: str = "full") -> str:
        """Format a citation for output.
        
        Args:
            handle: P# handle
            style: 'full', 'short', or 'inline'
            
        Returns:
            Formatted citation string
        """
        is_valid, paper = self.validate_citation(handle)
        if not is_valid or paper is None:
            return f"[{handle}] - INVALID CITATION"
        
        authors = paper.get("authors", [])
        if isinstance(authors, list):
            if len(authors) > 2:
                author_str = f"{authors[0]} et al."
            else:
                author_str = ", ".join(authors)
        else:
            author_str = str(authors)
        
        year = paper.get("year", "n.d.")
        title = paper.get("title", "Untitled")
        source = paper.get("source", "")
        
        if style == "full":
            return f"[{paper['handle']}] {author_str} ({year}). {title}. {source}"
        elif style == "short":
            return f"[{paper['handle']}] {author_str} ({year})"
        else:  # inline
            return f"[{paper['handle']}]"
    
    def get_evidence_for_query(self, query: str, handles: List[str] = None) -> str:
        """Get formatted evidence relevant to a query.
        
        Args:
            query: The query/claim to find evidence for
            handles: Optional list of P# handles to limit search
            
        Returns:
            Formatted string of evidence passages
        """
        papers = self.get_all_papers() if handles is None else [
            self.get_paper_by_handle(h) for h in handles if self.get_paper_by_handle(h)
        ]
        
        if not papers:
            return "INSUFFICIENT_EVIDENCE: No papers in evidence store."
        
        evidence_lines = []
        query_lower = query.lower()
        
        for paper in papers:
            if paper is None:
                continue
            
            # Check if abstract contains relevant terms
            abstract = paper.get("abstract", "").lower()
            title = paper.get("title", "").lower()
            
            # Simple relevance check
            query_terms = [t for t in query_lower.split() if len(t) > 3]
            relevance_score = sum(1 for term in query_terms if term in abstract or term in title)
            
            if relevance_score > 0:
                evidence_lines.append(
                    f"[{paper['handle']}] {paper.get('title', 'Untitled')}\n"
                    f"  Authors: {', '.join(paper.get('authors', ['Unknown']))}\n"
                    f"  Year: {paper.get('year', 'n.d.')}\n"
                    f"  Evidence: {paper.get('abstract', 'No abstract')[:300]}..."
                )
        
        if not evidence_lines:
            return f"INSUFFICIENT_EVIDENCE: No passages found matching '{query[:50]}...'"
        
        return "\n\n".join(evidence_lines)
    
    def clear(self) -> None:
        """Clear all papers from the store."""
        self._store = {}
        self._handle_map = {}
        self._next_handle = 1
        self._save()
        logger.info("Evidence store cleared")
    
    def get_corpus_summary(self) -> str:
        """Get a summary of the current corpus for agents."""
        if not self._store:
            return "CORPUS_EMPTY: No papers in evidence store."
        
        papers = self.get_all_papers()
        summary_lines = [
            f"**Evidence Store Summary**",
            f"Total Papers: {len(papers)}",
            f"",
            f"**Available Papers:**"
        ]
        
        for paper in papers:
            summary_lines.append(
                f"- [{paper['handle']}] {paper.get('title', 'Untitled')[:60]}... "
                f"({paper.get('year', 'n.d.')}, {paper.get('source', 'Unknown')})"
            )
        
        return "\n".join(summary_lines)


# Global singleton instance
evidence_store = EvidenceStore()
