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
import re

logger = logging.getLogger(__name__)

class SemanticChunker:
    """Splits text into semantically coherent chunks using sentence embeddings."""
    
    def __init__(self, embeddings_model, percentile_threshold=40):
        self.embeddings_model = embeddings_model
        self.percentile_threshold = percentile_threshold
        
    def split_text(self, text: str) -> List[str]:
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.?!])\s+', text)
        if len(sentences) <= 1:
            return sentences
            
        # Embed all sentences
        embeddings = self.embeddings_model.embed_documents(sentences)
        if not embeddings:
            return [text]
            
        # Calculate cosine similarity between adjacent sentences
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = []
        for i in range(len(embeddings) - 1):
            sim = cosine_similarity([embeddings[i]], [embeddings[i+1]])[0][0]
            similarities.append(sim)
            
        # Determine strictness dynamic threshold
        # Split at the "valleys" of similarity
        if not similarities:
            return [text]
            
        threshold = np.percentile(similarities, self.percentile_threshold)
        
        chunks = []
        current_group = [sentences[0]]
        
        for i, sim in enumerate(similarities):
            if sim < threshold:
                # Break point
                chunks.append(" ".join(current_group))
                current_group = [sentences[i+1]]
            else:
                current_group.append(sentences[i+1])
                
        if current_group:
            chunks.append(" ".join(current_group))
            
        return chunks


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
    """Robust Sparse Retriever using TF-IDF with BM25-like scoring."""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2), min_df=1)
        self.docs = []
        self.tfidf_matrix = None
        self.is_fitted = False
        
    def fit(self, docs: List[Document]):
        """Fit TF-IDF on the document corpus."""
        if not docs:
            return
        self.docs = docs
        texts = [d.page_content for d in docs]
        try:
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)
            self.is_fitted = True
        except ValueError:
            # Handle case with empty vocabulary
            self.is_fitted = False
        
    def search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Return top-k docs with normalized scores."""
        if not self.is_fitted or not self.docs:
            return []
        
        try:
            query_vec = self.vectorizer.transform([query])
            scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
            
            # Get top-k indices
            top_indices = scores.argsort()[-k:][::-1]
            
            results = []
            for idx in top_indices:
                score = float(scores[idx])
                if score > 0.01: # Lower threshold
                    doc = self.docs[idx]
                    results.append({
                        "doc": doc,
                        "score": score
                    })
            return results
        except Exception as e:
            logger.warning(f"Sparse search failed: {e}")
            return []

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
        """Bulk-add papers with Semantic Chunking and Hybrid Indexing."""
        if not papers:
            return []
        
        logger.info(f"Batch processing {len(papers)} papers for Hybrid Index (Semantic Chunking Enabled)")
        new_docs = []
        handles = []
        
        semantic_chunker = SemanticChunker(self.embeddings, percentile_threshold=40)
        
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
            
            # 2. Semantic Chunking
            # First, try semantic chunking
            raw_chunks = semantic_chunker.split_text(abstract)
            
            # If chunks are too large, fall back to recursive split on them
            final_chunks = []
            recursive_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)
            for rc in raw_chunks:
                if len(rc) > 800: # Threshold for too big
                    sub_chunks = recursive_splitter.split_text(rc)
                    final_chunks.extend(sub_chunks)
                else:
                    final_chunks.append(rc)
            
            # Always index title explicitly
            final_chunks.insert(0, f"Title: {title}\nAbstract: {abstract[:300]}...")
            
            for chunk in final_chunks:
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

    def hybrid_search(self, query: str, k: int = 5, use_hyde: bool = False, generator_func=None) -> List[Dict[str, Any]]:
        """Perform Hybrid Search (Reciprocal Rank Fusion) with Cross-Encoder Reranking and optional HyDE."""
        start_time = time.time()
        
        search_queries = [query]
        # HyDE Expansion
        if use_hyde and generator_func:
            try:
                # We expect generator_func to take a string and return a hypothetical abstract
                hypothetical_doc = generator_func(query)
                logger.info(f"HyDE generated hypothetical doc length: {len(hypothetical_doc)}")
                search_queries.append(hypothetical_doc)
            except Exception as e:
                logger.warning(f"HyDE generation failed: {e}")

        # Collect candidates from all queries
        candidate_map = {} # handle_contenthash -> {doc, dense_score, sparse_score}
        
        # 1. Reciprocal Rank Fusion Logic
        # We will sum 1/(rank + 60) for dense and sparse ranks
        
        for q in search_queries:
            # A. Dense Search
            dense_results = self.db.similarity_search_with_score(q, k=k*3)
            # Normalize FAISS L2 distances (lower is better) to similarity (0-1)
            # Rough approx: 1 / (1 + distance)
            for rank, (doc, score) in enumerate(dense_results):
                uid = f"{doc.metadata.get('handle')}_{hash(doc.page_content)}"
                if uid not in candidate_map:
                    candidate_map[uid] = {"doc": doc, "rrf_score": 0.0, "dense_score": 0.0, "sparse_score": 0.0}
                
                # RRF update
                candidate_map[uid]["rrf_score"] += 1.0 / (rank + 60)
                candidate_map[uid]["dense_score"] = float(1.0 / (1.0 + score)) # approx

            # B. Sparse Search
            sparse_results = self.sparse_retriever.search(q, k=k*3)
            for rank, res in enumerate(sparse_results):
                doc = res["doc"]
                score = res["score"]
                uid = f"{doc.metadata.get('handle')}_{hash(doc.page_content)}"
                if uid not in candidate_map:
                     candidate_map[uid] = {"doc": doc, "rrf_score": 0.0, "dense_score": 0.0, "sparse_score": 0.0}
                
                candidate_map[uid]["rrf_score"] += 1.0 / (rank + 60)
                candidate_map[uid]["sparse_score"] = float(score)

        # Convert to list
        candidates = list(candidate_map.values())
        # Filter by minimum RRF (optional)
        
        logger.info(f"Hybrid Search (HyDE={use_hyde}) candidates: {len(candidates)} (Query: {query[:50]})")
        
        # 2. Reranking (Cross-Encoder)
        if self.reranker and candidates:
            # We rerank the top 20 by RRF score to save time
            candidates.sort(key=lambda x: x["rrf_score"], reverse=True)
            top_candidates = candidates[:20]
            
            pairs = [[query, c["doc"].page_content] for c in top_candidates]
            scores = self.reranker.predict(pairs)
            
            for i, score in enumerate(scores):
                top_candidates[i]["rerank_score"] = float(score)
                # Inject useful debug scores into metadata
                top_candidates[i]["doc"].metadata["rrf"] = top_candidates[i]["rrf_score"]
                top_candidates[i]["doc"].metadata["cross_score"] = float(score)
            
            # Sort by Cross-Encoder score
            top_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
            final_selection = top_candidates[:k]
        else:
            # Fallback to RRF sort
            candidates.sort(key=lambda x: x["rrf_score"], reverse=True)
            final_selection = candidates[:k]
            for c in final_selection:
                c["rerank_score"] = c["rrf_score"] # Proxy
            
        final_results = []
        for item in final_selection:
            doc = item["doc"]
            meta = doc.metadata
            final_results.append({
                "content": doc.page_content,
                "title": meta.get("title"),
                "handle": meta.get("handle"),
                "authors": meta.get("authors"),
                "year": meta.get("year"),
                "source": meta.get("source"),
                "score": item.get('rerank_score', 0.0)
            })
            
        return final_results

    def save(self) -> None:
        self.db.save_local("faiss_index")
        self._save_metadata()
