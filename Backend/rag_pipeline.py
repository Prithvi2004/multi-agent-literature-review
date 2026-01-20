# rag_pipeline.py
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import json
import logging
import time
import numpy as np
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Imports for Hybrid Search & Reranking
try:
    from sentence_transformers import SentenceTransformer, CrossEncoder
except ImportError:
    SentenceTransformer = None
    CrossEncoder = None
    
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Import centralized store
from evidence_store import evidence_store

logger = logging.getLogger(__name__)

class SBERTEmbeddings:
    """Optimized embedding adapter using sentence-transformers with caching."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if SentenceTransformer is None:
            raise ImportError("sentence_transformers is not installed. Please install it.")
        self.model = SentenceTransformer(model_name)
        self._cache = {}

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        # Batch encoding for efficiency
        emb = self.model.encode(texts, show_progress_bar=False, batch_size=32)
        return emb.tolist()

    def embed_query(self, text: str) -> List[float]:
        cache_key = hash(text)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        emb = self.model.encode([text], show_progress_bar=False)[0]
        result = emb.tolist()
        
        if len(self._cache) < 1000:
            self._cache[cache_key] = result
        
        return result

    def __call__(self, texts):
        if texts is None:
            return []
        if isinstance(texts, (list, tuple)):
            return self.embed_documents(list(texts))
        return self.embed_query(str(texts))

METADATA_STORE_PATH = "papers_metadata.json"

class HybridRetriever:
    """Simple Sparse Retriever using TF-IDF (approximate BM25)."""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        self.docs = []
        self.tfidf_matrix = None
        self.is_fitted = False
        
    def fit(self, docs: List[Document]):
        """Fit TF-IDF on the document corpus."""
        if not docs:
            return
        self.docs = docs
        texts = [d.page_content for d in docs]
        self.tfidf_matrix = self.vectorizer.fit_transform(texts)
        self.is_fitted = True
        
    def search(self, query: str, k: int = 10) -> List[Document]:
        """Return top-k docs based on TF-IDF score."""
        if not self.is_fitted or not self.docs:
            return []
        
        query_vec = self.vectorizer.transform([query])
        # Compute cosine similarity (equivalent to refined TF-IDF matching)
        scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # Get top-k indices
        top_indices = scores.argsort()[-k:][::-1]
        
        results = []
        for idx in top_indices:
            score = scores[idx]
            if score > 0.05: # Minimal threshold
                doc = self.docs[idx]
                # Inject score metadata
                doc.metadata['sparse_score'] = float(score)
                results.append(doc)
        return results

class RAGPipeline:
    """Advanced RAG pipeline with Hybrid Search (Dense + Sparse) and Reranking."""

    def __init__(self):
        logger.info("Initializing Advanced RAG Pipeline")
        self.embeddings = SBERTEmbeddings()
        self.db = None
        
        # Sparse Retriever
        self.sparse_retriever = HybridRetriever()
        
        # Reranker (Cross-Encoder)
        self.reranker = None
        if CrossEncoder:
            try:
                # Use a lightweight cross-encoder
                self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', max_length=512)
            except Exception as e:
                logger.warning(f"Could not load CrossEncoder: {e}")
        
        self.query_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.all_chunks: List[Document] = [] # Keep explicit track of chunks for sparse search
        
        self._init_db()
        self._load_metadata()
        logger.info(f"RAG Pipeline initialized - {len(self.metadata)} papers, {len(self.all_chunks)} chunks")

    # --------------------
    # Persistence helpers
    # --------------------
    def _init_db(self) -> None:
        if os.path.exists("faiss_index"):
            logger.info("Loading existing FAISS index")
            self.db = FAISS.load_local("faiss_index", self.embeddings, allow_dangerous_deserialization=True)
            
            # Reconstruct all_chunks relies on docstore, but FAISS docstore lookup is tricky.
            # Ideally, we should persist chunks separately or iterate.
            # For simplicity in this session-based pipeline, we might need to rely on reloading.
            # But since FAISS.load_local loads docs into memory, we can access them if we iterate docstore.
            # Hack: We will rely on new additions for sparse index or reload if possible.
            try:
                self.all_chunks = list(self.db.docstore._dict.values())
                # Re-fit sparse retriever
                if self.all_chunks:
                    logger.info("Fitting sparse retriever on loaded docs...")
                    self.sparse_retriever.fit(self.all_chunks)
            except Exception as e:
                logger.warning(f"Could not restore docs for sparse index: {e}")
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
            pass

    # --------------------
    # Indexing
    # --------------------
    def add_papers(self, papers: List[Dict[str, Any]]) -> List[str]:
        """Bulk-add papers with Hybrid indexing."""
        if not papers:
            return []
        
        logger.info(f"Batch processing {len(papers)} papers for Hybrid Index")
        new_docs = []
        handles = []
        
        for p in papers:
            title = p.get("title") or "Untitled"
            abstract = p.get("abstract") or ""
            if not abstract or not abstract.strip():
                continue
            
            # 1. Add to Evidence Store
            handle = evidence_store.add_paper(
                title=title,
                authors=p.get("authors", "Unknown"),
                year=p.get("year", 0),
                venue=p.get("source", "Unknown"),
                doi_or_arxiv=p.get("url", ""),
                abstract=abstract,
                url=p.get("url", ""),
                source=p.get("source", "Unknown")
            )
            handles.append(handle)
            
            meta = {
                "title": title,
                "source": p.get("source", "Unknown"),
                "authors": p.get("authors"),
                "year": p.get("year"),
                "url": p.get("url"),
                "handle": handle,
            }
            
            # 2. Advanced Chunking (Semantic approx)
            # Use smaller chunks for better dense retrieval, contextual overlap
            splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=100)
            chunks = splitter.split_text(abstract) 
            # Also index title/intro explicitly
            chunks.insert(0, f"Title: {title}\nAbstract: {abstract[:200]}")
            
            for chunk in chunks:
                new_docs.append(Document(page_content=chunk, metadata=meta))
            
            self.metadata[title] = meta
        
        if new_docs:
            # Update Dense Index
            self.db.add_documents(new_docs)
            
            # Update Sparse Index (Re-fit on all docs + new docs)
            self.all_chunks.extend(new_docs)
            logger.info("Refitting sparse retriever...")
            self.sparse_retriever.fit(self.all_chunks)
            
            self._save_metadata()
        
        return handles

    # --------------------
    # Retrieval
    # --------------------
    def search(self, query: str, k: int = 5) -> str:
        """Expose structured results as string."""
        results = self.hybrid_search(query, k=k)
        
        if not results:
            return "INSUFFICIENT_EVIDENCE: No supporting passages found."
        
        lines = []
        for idx, r in enumerate(results, start=1):
            handle = r.get("handle") or f"P{idx}"
            title = r.get("title", "Untitled")
            source = r.get("source", "N/A")
            authors = r.get("authors") or "Unknown"
            year = r.get("year") or "n.d."
            score = r.get("score", 0.0)
            
            header = f"[{handle}] {title} — {authors} ({year}) [Relevance: {score:.2f}]"
            body = r.get("content", "")
            lines.append(f"{header}\n{body}")
            
        return "\n\n".join(lines)

    def hybrid_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Perform Hybrid Search (BM25 + Dense) with Cross-Encoder Reranking."""
        start_time = time.time()
        
        # 1. Dense Search (FAISS)
        dense_docs = self.db.similarity_search_with_score(query, k=k*2)
        # FAISS returns L2 distance (lower is better) or dot product depending on index.
        # Assuming L2 default: convert to similarity? Or just normalize.
        # For simplicity, treat them as candidate set 1.
        candidate_map = {}
        for doc, score in dense_docs:
            # In FAISS L2, score is distance.
            uid = f"{doc.metadata.get('handle')}_{hash(doc.page_content)}"
            candidate_map[uid] = doc
            doc.metadata['dense_score'] = float(score)

        # 2. Sparse Search (TF-IDF)
        sparse_docs = self.sparse_retriever.search(query, k=k*2)
        for doc in sparse_docs:
            uid = f"{doc.metadata.get('handle')}_{hash(doc.page_content)}"
            if uid not in candidate_map:
                candidate_map[uid] = doc
        
        candidates = list(candidate_map.values())
        logger.info(f"Hybrid Search candidates: {len(candidates)} (Query: {query[:50]})")
        
        # 3. Reranking
        if self.reranker and candidates:
            pairs = [[query, doc.page_content] for doc in candidates]
            scores = self.reranker.predict(pairs)
            
            # Attach scores
            for doc, score in zip(candidates, scores):
                doc.metadata['rerank_score'] = float(score)
            
            # Sort by reranker score (descending)
            candidates.sort(key=lambda x: x.metadata['rerank_score'], reverse=True)
        else:
            # Fallback: Prefer sparse (keyword match) if dense fails, or simple merge
            # Here we just take them roughly as is.
            pass
            
        final_results = []
        for doc in candidates[:k]:
            meta = doc.metadata
            final_results.append({
                "content": doc.page_content,
                "title": meta.get("title"),
                "handle": meta.get("handle"),
                "authors": meta.get("authors"),
                "year": meta.get("year"),
                "source": meta.get("source"),
                "score": meta.get('rerank_score', 0.0)
            })
            
        return final_results

    def save(self) -> None:
        self.db.save_local("faiss_index")
        self._save_metadata()
