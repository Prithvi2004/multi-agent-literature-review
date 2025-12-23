# rag_pipeline.py
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import json
import logging
import time
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class SBERTEmbeddings:
    """Optimized embedding adapter using sentence-transformers with caching.

    Implements the methods expected by the FAISS wrapper used in this
    project: `embed_documents` and `embed_query`.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self._cache = {}  # Simple in-memory cache

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        # Batch encoding for efficiency
        emb = self.model.encode(texts, show_progress_bar=False, batch_size=32)
        return emb.tolist()

    def embed_query(self, text: str) -> List[float]:
        # Check cache first
        cache_key = hash(text)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        emb = self.model.encode([text], show_progress_bar=False)[0]
        result = emb.tolist()
        
        # Cache the result (limit cache size)
        if len(self._cache) < 1000:
            self._cache[cache_key] = result
        
        return result

    def __call__(self, texts):
        """Make the embeddings object callable.

        - If passed a list of strings, return a list of vectors.
        - If passed a single string, return a single vector.
        This keeps compatibility with older/newer vectorstore expectations.
        """
        if texts is None:
            return []
        if isinstance(texts, (list, tuple)):
            return self.embed_documents(list(texts))
        return self.embed_query(str(texts))

METADATA_STORE_PATH = "papers_metadata.json"


class RAGPipeline:
    """Simple RAG wrapper around a persisted FAISS index.

    Responsibilities:
    - Maintain a vector index of paper chunks with rich metadata
    - Persist index and a lightweight metadata catalog across runs
    - Provide both string and structured retrieval for tools/agents
    - Offer basic in-memory query caching for efficiency
    """

    def __init__(self):
        # Use a local SBERT model for embeddings to avoid external embed model
        # requirements (e.g., Ollama nomic-embed-text). This keeps the pipeline
        # runnable offline once the sentence-transformers model is cached.
        logger.info("Initializing RAG Pipeline")
        self.embeddings = SBERTEmbeddings()
        self.db = None
        self.query_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self._init_db()
        self._load_metadata()
        logger.info(f"RAG Pipeline initialized - {len(self.metadata)} papers in metadata store")

    # --------------------
    # Persistence helpers
    # --------------------
    def _init_db(self) -> None:
        if os.path.exists("faiss_index"):
            logger.info("Loading existing FAISS index")
            self.db = FAISS.load_local("faiss_index", self.embeddings, allow_dangerous_deserialization=True)
        else:
            logger.info("Creating new FAISS index")
            self.db = FAISS.from_texts(["Initial document"], self.embeddings)
            self.db.save_local("faiss_index")

    def _load_metadata(self) -> None:
        if os.path.exists(METADATA_STORE_PATH):
            try:
                with open(METADATA_STORE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.metadata = data
            except Exception:
                self.metadata = {}

    def _save_metadata(self) -> None:
        try:
            with open(METADATA_STORE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception:
            # Metadata persistence failures should not break the pipeline
            pass

    # --------------------
    # Indexing
    # --------------------
    def add_paper(self, title: str, content: str, source: str = "Unknown", **extra_metadata: Any) -> None:
        """Add a single paper (usually abstract + title) to the index.

        Metadata is stored both at the document-chunk level and in a
        lightweight catalog keyed by title for downstream citation lookup.
        """
        if not content or not content.strip():
            logger.warning(f"Skipping paper with empty content: {title}")
            return

        logger.debug(f"Adding paper to index: '{title}' (source: {source})")
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_text(content)
        logger.debug(f"  Split into {len(chunks)} chunks")

        base_meta: Dict[str, Any] = {"title": title, "source": source}
        base_meta.update(extra_metadata)

        docs = [
            Document(page_content=chunk, metadata=base_meta)
            for chunk in chunks
        ]
        self.db.add_documents(docs)

        # Update high-level metadata catalog (used for citations/summaries)
        self.metadata[title] = base_meta
        self._save_metadata()

    def add_papers(self, papers: List[Dict[str, Any]]) -> None:
        """Bulk-add papers with batch processing for efficiency."""
        if not papers:
            return
        
        logger.info(f"Batch processing {len(papers)} papers")
        all_docs = []
        
        for p in papers:
            title = p.get("title") or "Untitled"
            abstract = p.get("abstract") or ""
            source = p.get("source", "Unknown")
            
            if not abstract or not abstract.strip():
                logger.debug(f"Skipping paper with empty abstract: {title}")
                continue
            
            # Prepare metadata
            meta = {
                "title": title,
                "source": source,
                "authors": p.get("authors"),
                "year": p.get("year"),
                "url": p.get("url"),
            }
            
            # Split into chunks
            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            chunks = splitter.split_text(abstract or title)
            
            # Create documents
            for chunk in chunks:
                all_docs.append(Document(page_content=chunk, metadata=meta))
            
            # Update metadata catalog
            self.metadata[title] = meta
        
        # Batch add all documents at once for efficiency
        if all_docs:
            logger.info(f"Adding {len(all_docs)} document chunks to index")
            self.db.add_documents(all_docs)
            self._save_metadata()
        else:
            logger.warning("No valid documents to add")

    # --------------------
    # Retrieval
    # --------------------
    def similarity_search(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        """Return structured search results for use by tools/agents.

        Each result contains page_content and metadata including title,
        source, authors, year, and url when available.
        """
        start_time = time.time()
        cache_key = f"{query}::k={k}"
        cache_hit = cache_key in self.query_cache
        
        if cache_hit:
            logger.debug(f"Returning cached results for query: '{query[:50]}...'")
            duration = time.time() - start_time
            # Log to metrics if available
            try:
                from main import metrics
                metrics.log_rag_operation("similarity_search", query, len(self.query_cache[cache_key]), duration, cache_hit=True)
            except:
                pass
            return self.query_cache[cache_key]

        logger.info(f"Performing similarity search - Query: '{query[:100]}...', k={k}")
        docs = self.db.similarity_search(query, k=k)
        logger.info(f"Found {len(docs)} results")
        results: List[Dict[str, Any]] = []
        for doc in docs:
            meta = doc.metadata or {}
            results.append(
                {
                    "content": doc.page_content,
                    "title": meta.get("title", "Untitled"),
                    "source": meta.get("source", "N/A"),
                    "authors": meta.get("authors"),
                    "year": meta.get("year"),
                    "url": meta.get("url"),
                }
            )

        self.query_cache[cache_key] = results
        duration = time.time() - start_time
        
        # Log to metrics if available
        try:
            from main import metrics
            metrics.log_rag_operation("similarity_search", query, len(results), duration, cache_hit=False)
        except:
            pass
        
        return results

    def search(self, query: str, k: int = 4) -> str:
        """Human/LLM-friendly string view of retrieved evidence.

        This is what the RAG tool currently exposes to agents. It keeps
        explicit citation handles [P1], [P2], ... to encourage traceable
        referencing in downstream reasoning.
        """
        results = self.similarity_search(query, k=k)
        lines = []
        for idx, r in enumerate(results, start=1):
            handle = f"P{idx}"
            title = r.get("title", "Untitled")
            source = r.get("source", "N/A")
            authors = r.get("authors") or "Unknown authors"
            year = r.get("year") or "n.d."
            url = r.get("url") or ""

            header = f"[{handle}] {title} — {authors} ({year}, {source})"
            if url:
                header += f"\nURL: {url}"

            body = r.get("content", "")
            lines.append(f"{header}\n---\n{body}")

        if not lines:
            return "No supporting passages found in the current corpus."

        return "\n\n".join(lines)

    def save(self) -> None:
        self.db.save_local("faiss_index")
        self._save_metadata()
