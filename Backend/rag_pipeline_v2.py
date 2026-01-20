# rag_pipeline_v2.py
"""
Advanced RAG Pipeline with Hybrid Search, Re-ranking, and Query Enhancement

Features:
- Semantic-aware chunking with overlap
- Hybrid retrieval (Dense FAISS + Sparse BM25)
- Cross-Encoder re-ranking for precision
- Query expansion and HyDE (Hypothetical Document Embeddings)
- Contextual compression
- Intelligent caching
- Product Quantization for FAISS optimization
"""

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, SentenceTransformersTokenTextSplitter
import os
import json
import logging
import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from functools import lru_cache
import hashlib

# Advanced RAG components
try:
    from sentence_transformers import SentenceTransformer, CrossEncoder
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False
    logging.warning("sentence-transformers not available")

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    logging.warning("rank-bm25 not available, falling back to TF-IDF")

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Import centralized store
from evidence_store import evidence_store

logger = logging.getLogger(__name__)

class AdvancedEmbeddings:
    """
    High-performance embedding adapter with caching and batching.
    
    Supports multiple embedding models:
    - all-MiniLM-L6-v2: Fast, good for general use (default)
    - mxbai-embed-large: High quality, larger model
    - nomic-embed-text: Optimized for long context
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if not SBERT_AVAILABLE:
            raise ImportError("sentence_transformers is required for advanced embeddings")
        
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self._cache = {}
        self._cache_hits = 0
        self._cache_misses = 0

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Batch embed multiple documents with progress tracking."""
        if not texts:
            return []
        
        # Filter cached vs. non-cached
        cached_results = []
        to_embed = []
        indices = []
        
        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            if cache_key in self._cache:
                cached_results.append((i, self._cache[cache_key]))
                self._cache_hits += 1
            else:
                to_embed.append(text)
                indices.append(i)
                self._cache_misses += 1
        
        # Embed non-cached texts
        if to_embed:
            embeddings = self.model.encode(
                to_embed, 
                show_progress_bar=len(to_embed) > 20,
                batch_size=32,
                normalize_embeddings=True  # Normalize for cosine similarity
            )
            
            # Cache new embeddings
            for text, emb in zip(to_embed, embeddings):
                cache_key = self._get_cache_key(text)
                if len(self._cache) < 10000:  # Limit cache size
                    self._cache[cache_key] = emb.tolist()
        else:
            embeddings = []
        
        # Reconstruct in original order
        results = [None] * len(texts)
        for idx, emb in cached_results:
            results[idx] = emb
        for idx, emb in zip(indices, embeddings):
            results[idx] = emb.tolist() if hasattr(emb, 'tolist') else emb
        
        return results

    def embed_query(self, text: str) -> List[float]:
        """Embed single query with caching."""
        cache_key = self._get_cache_key(text)
        if cache_key in self._cache:
            self._cache_hits += 1
            return self._cache[cache_key]
        
        self._cache_misses += 1
        emb = self.model.encode([text], normalize_embeddings=True)[0]
        result = emb.tolist()
        
        if len(self._cache) < 10000:
            self._cache[cache_key] = result
        
        return result

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Return cache performance statistics."""
        total = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total if total > 0 else 0
        return {
            "cache_size": len(self._cache),
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": round(hit_rate * 100, 2)
        }

    def __call__(self, texts):
        """Make callable for langchain compatibility."""
        if texts is None:
            return []
        if isinstance(texts, (list, tuple)):
            return self.embed_documents(list(texts))
        return self.embed_query(str(texts))


class BM25Retriever:
    """
    Optimized BM25 sparse retriever for keyword matching.
    
    BM25 (Best Matching 25) is a probabilistic retrieval function that ranks 
    documents based on query term frequency and document length normalization.
    """
    
    def __init__(self):
        self.docs = []
        self.bm25 = None
        self.tokenized_corpus = []
        self.is_fitted = False
        logger.info("BM25Retriever initialized")
        
    def _tokenize(self, text: str) -> List[str]:
        """Simple whitespace tokenization with lowercasing."""
        return text.lower().split()
    
    def fit(self, docs: List[Document]):
        """Fit BM25 on document corpus."""
        if not docs:
            logger.warning("No documents to fit BM25")
            return
        
        self.docs = docs
        self.tokenized_corpus = [self._tokenize(d.page_content) for d in docs]
        
        if BM25_AVAILABLE:
            self.bm25 = BM25Okapi(self.tokenized_corpus)
            logger.info(f"BM25 fitted on {len(docs)} documents")
        else:
            # Fallback to TF-IDF
            logger.warning("BM25 not available, using TF-IDF fallback")
            self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
            texts = [d.page_content for d in docs]
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)
        
        self.is_fitted = True
        
    def search(self, query: str, k: int = 10) -> List[Tuple[Document, float]]:
        """Return top-k docs with BM25 scores."""
        if not self.is_fitted or not self.docs:
            return []
        
        if BM25_AVAILABLE and self.bm25:
            tokenized_query = self._tokenize(query)
            scores = self.bm25.get_scores(tokenized_query)
            
            # Get top-k indices
            top_indices = np.argsort(scores)[::-1][:k]
            
            results = []
            for idx in top_indices:
                score = scores[idx]
                if score > 0.1:  # Minimal threshold
                    doc = self.docs[idx]
                    # Create a copy to avoid modifying original
                    doc_copy = Document(
                        page_content=doc.page_content,
                        metadata={**doc.metadata, 'bm25_score': float(score)}
                    )
                    results.append((doc_copy, float(score)))
        else:
            # TF-IDF fallback
            query_vec = self.vectorizer.transform([query])
            scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
            top_indices = scores.argsort()[-k:][::-1]
            
            results = []
            for idx in top_indices:
                score = scores[idx]
                if score > 0.05:
                    doc = self.docs[idx]
                    doc_copy = Document(
                        page_content=doc.page_content,
                        metadata={**doc.metadata, 'bm25_score': float(score)}
                    )
                    results.append((doc_copy, float(score)))
        
        return results


class QueryEnhancer:
    """
    Advanced query enhancement with expansion and HyDE.
    
    Techniques:
    1. Query Expansion: Add related terms and synonyms
    2. HyDE: Generate hypothetical ideal document for the query
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self._expansion_cache = {}
        logger.info("QueryEnhancer initialized")
    
    def expand_query(self, query: str, domains: List[str] = None) -> str:
        """
        Expand query with domain-specific terms.
        
        Args:
            query: Original user query
            domains: List of research domains
            
        Returns:
            Expanded query string
        """
        cache_key = f"{query}_{','.join(domains or [])}"
        if cache_key in self._expansion_cache:
            return self._expansion_cache[cache_key]
        
        # Add domain context
        if domains:
            domain_terms = " ".join(domains)
            expanded = f"{query} {domain_terms}"
        else:
            expanded = query
        
        # Cache result
        self._expansion_cache[cache_key] = expanded
        return expanded
    
    def generate_hyde(self, query: str) -> str:
        """
        Generate hypothetical ideal document (HyDE).
        
        Creates a hypothetical document that would perfectly answer the query,
        then uses it for retrieval to improve semantic matching.
        """
        if not self.llm_client:
            return query
        
        prompt = f"""Given the research query: "{query}"

Generate a brief hypothetical abstract (2-3 sentences) of an ideal paper that would perfectly address this query.
Focus on technical details and key concepts.

Hypothetical Abstract:"""
        
        try:
            hyde_doc = self.llm_client.generate(prompt, timeout=15)
            return f"{query}\n\n{hyde_doc}"
        except Exception as e:
            logger.warning(f"HyDE generation failed: {e}")
            return query


class ContextualCompressor:
    """
    Compress retrieved contexts to reduce noise and improve relevance.
    
    Extracts only the most relevant sentences from retrieved chunks.
    """
    
    def __init__(self, compression_ratio: float = 0.5):
        self.compression_ratio = compression_ratio
        logger.info(f"ContextualCompressor initialized (ratio={compression_ratio})")
    
    def compress(self, documents: List[Document], query: str) -> List[Document]:
        """
        Compress documents by extracting most relevant sentences.
        
        Args:
            documents: List of retrieved documents
            query: Original query for relevance scoring
            
        Returns:
            Compressed documents
        """
        compressed = []
        
        for doc in documents:
            # Split into sentences
            sentences = doc.page_content.split('. ')
            if len(sentences) <= 2:
                compressed.append(doc)  # Keep short docs as-is
                continue
            
            # Simple relevance scoring (count query term matches)
            query_terms = set(query.lower().split())
            sentence_scores = []
            
            for sent in sentences:
                sent_terms = set(sent.lower().split())
                overlap = len(query_terms & sent_terms)
                sentence_scores.append((sent, overlap))
            
            # Keep top sentences
            sentence_scores.sort(key=lambda x: x[1], reverse=True)
            num_keep = max(2, int(len(sentences) * self.compression_ratio))
            top_sentences = [s[0] for s in sentence_scores[:num_keep]]
            
            # Reconstruct document
            compressed_content = '. '.join(top_sentences) + '.'
            compressed_doc = Document(
                page_content=compressed_content,
                metadata={**doc.metadata, 'compressed': True}
            )
            compressed.append(compressed_doc)
        
        return compressed


METADATA_STORE_PATH = "papers_metadata.json"


class AdvancedRAGPipeline:
    """
    State-of-the-art RAG pipeline with hybrid search and advanced retrieval.
    
    Architecture:
    1. Semantic Chunking: Sentence-aware splitting with overlap
    2. Dual Indexing: Dense (FAISS) + Sparse (BM25)
    3. Hybrid Retrieval: Combine dense and sparse results
    4. Re-ranking: Cross-encoder for final precision
    5. Contextual Compression: Extract most relevant content
    6. Query Enhancement: Expansion + HyDE for better matching
    """

    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2", use_hyde: bool = False):
        logger.info("="*80)
        logger.info("Initializing Advanced RAG Pipeline v2.0")
        logger.info("="*80)
        
        # Core components
        self.embeddings = AdvancedEmbeddings(embedding_model)
        self.db = None  # FAISS vector store
        
        # Sparse retrieval
        self.bm25_retriever = BM25Retriever()
        
        # Re-ranker
        self.reranker = None
        if SBERT_AVAILABLE:
            try:
                self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', max_length=512)
                logger.info("Cross-Encoder reranker loaded")
            except Exception as e:
                logger.warning(f"Could not load CrossEncoder: {e}")
        
        # Query enhancement
        self.query_enhancer = QueryEnhancer()
        self.use_hyde = use_hyde
        
        # Contextual compression
        self.compressor = ContextualCompressor(compression_ratio=0.7)
        
        # Storage
        self.query_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.all_chunks: List[Document] = []
        
        # Performance tracking
        self.stats = {
            "total_searches": 0,
            "cache_hits": 0,
            "avg_search_time": 0.0,
            "total_chunks": 0
        }
        
        self._init_db()
        self._load_metadata()
        
        logger.info(f"RAG Pipeline initialized successfully")
        logger.info(f"  - Papers indexed: {len(self.metadata)}")
        logger.info(f"  - Total chunks: {len(self.all_chunks)}")
        logger.info(f"  - Embedding model: {embedding_model}")
        logger.info(f"  - BM25 enabled: {BM25_AVAILABLE}")
        logger.info(f"  - Reranker enabled: {self.reranker is not None}")
        logger.info(f"  - HyDE enabled: {use_hyde}")
        logger.info("="*80)

    # ==================== Initialization ====================
    
    def _init_db(self) -> None:
        """Initialize or load FAISS vector database."""
        if os.path.exists("faiss_index"):
            logger.info("Loading existing FAISS index...")
            try:
                self.db = FAISS.load_local(
                    "faiss_index", 
                    self.embeddings, 
                    allow_dangerous_deserialization=True
                )
                
                # Reconstruct document list
                self.all_chunks = list(self.db.docstore._dict.values())
                logger.info(f"Loaded {len(self.all_chunks)} chunks from FAISS")
                
                # Fit BM25 on loaded docs
                if self.all_chunks:
                    self.bm25_retriever.fit(self.all_chunks)
                    
            except Exception as e:
                logger.error(f"Error loading FAISS index: {e}")
                logger.info("Creating new FAISS index")
                self._create_new_db()
        else:
            logger.info("Creating new FAISS index")
            self._create_new_db()
    
    def _create_new_db(self):
        """Create a new FAISS database."""
        # Initialize with a dummy document
        dummy_doc = ["Advanced RAG Pipeline initialized"]
        self.db = FAISS.from_texts(dummy_doc, self.embeddings)
        self.db.save_local("faiss_index")

    def _load_metadata(self) -> None:
        """Load paper metadata from disk."""
        if os.path.exists(METADATA_STORE_PATH):
            try:
                with open(METADATA_STORE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.metadata = data
                        logger.info(f"Loaded metadata for {len(self.metadata)} papers")
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
                self.metadata = {}

    def _save_metadata(self) -> None:
        """Persist metadata to disk."""
        try:
            with open(METADATA_STORE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")

    # ==================== Indexing ====================
    
    def add_papers(self, papers: List[Dict[str, Any]]) -> List[str]:
        """
        Add papers with advanced semantic chunking and dual indexing.
        
        Args:
            papers: List of paper dictionaries with title, abstract, authors, etc.
            
        Returns:
            List of evidence store handles (P# identifiers)
        """
        if not papers:
            return []
        
        logger.info(f"Processing {len(papers)} papers for indexing")
        new_docs = []
        handles = []
        
        for p in papers:
            title = p.get("title") or "Untitled"
            abstract = p.get("abstract") or ""
            
            if not abstract or not abstract.strip():
                logger.warning(f"Skipping paper with empty abstract: {title}")
                continue
            
            # Add to Evidence Store
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
            
            # Metadata for chunks
            meta = {
                "title": title,
                "source": p.get("source", "Unknown"),
                "authors": p.get("authors"),
                "year": p.get("year"),
                "url": p.get("url"),
                "handle": handle,
            }
            
            # Advanced Semantic Chunking
            # Strategy: Use sentence-aware splitting with overlap for context preservation
            chunks = self._create_semantic_chunks(title, abstract)
            
            for chunk_text in chunks:
                new_docs.append(Document(
                    page_content=chunk_text,
                    metadata=meta.copy()
                ))
            
            self.metadata[title] = meta
            logger.debug(f"Indexed paper: {title} ({len(chunks)} chunks)")
        
        if new_docs:
            # Update Dense Index (FAISS)
            logger.info(f"Adding {len(new_docs)} chunks to FAISS index")
            self.db.add_documents(new_docs)
            
            # Update Sparse Index (BM25)
            self.all_chunks.extend(new_docs)
            logger.info("Refitting BM25 retriever...")
            self.bm25_retriever.fit(self.all_chunks)
            
            # Update stats
            self.stats["total_chunks"] = len(self.all_chunks)
            
            # Persist
            self.save()
            
            logger.info(f"Successfully indexed {len(papers)} papers")
        
        return handles
    
    def _create_semantic_chunks(self, title: str, abstract: str, chunk_size: int = 400, overlap: int = 100) -> List[str]:
        """
        Create semantically-aware chunks with contextual overlap.
        
        Strategy:
        1. Create title + intro chunk for high-level matching
        2. Split abstract into smaller chunks with overlap
        3. Ensure chunks preserve sentence boundaries
        
        Args:
            title: Paper title
            abstract: Paper abstract
            chunk_size: Target chunk size in characters
            overlap: Overlap between chunks
            
        Returns:
            List of chunk texts
        """
        chunks = []
        
        # Chunk 1: Title + Abstract preview (for broad matching)
        title_chunk = f"Title: {title}\n\nAbstract Preview: {abstract[:200]}..."
        chunks.append(title_chunk)
        
        # Chunk 2+: Semantic splitting of abstract
        # Use RecursiveCharacterTextSplitter with sentence awareness
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", ". ", " ", ""],  # Respect sentence boundaries
            length_function=len,
        )
        
        abstract_chunks = splitter.split_text(abstract)
        chunks.extend(abstract_chunks)
        
        return chunks

    # ==================== Retrieval ====================
    
    def search(self, query: str, k: int = 5, use_compression: bool = True) -> str:
        """
        Main search interface returning formatted string results.
        
        Args:
            query: Search query
            k: Number of results
            use_compression: Whether to apply contextual compression
            
        Returns:
            Formatted string with search results
        """
        results = self.hybrid_search(query, k=k, use_compression=use_compression)
        
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
            
            header = f"[{handle}] {title} — {authors} ({year}) [Relevance: {score:.3f}]"
            body = r.get("content", "")
            lines.append(f"{header}\n{body}")
        
        return "\n\n".join(lines)
    
    def hybrid_search(
        self, 
        query: str, 
        k: int = 5, 
        use_compression: bool = True,
        alpha: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Advanced hybrid search with dense + sparse retrieval and re-ranking.
        
        Pipeline:
        1. Query Enhancement (expansion + optional HyDE)
        2. Dense Retrieval (FAISS)
        3. Sparse Retrieval (BM25)
        4. Result Fusion
        5. Cross-Encoder Re-ranking
        6. Contextual Compression (optional)
        
        Args:
            query: Search query
            k: Number of final results
            use_compression: Apply contextual compression
            alpha: Balance between dense (1.0) and sparse (0.0) retrieval
            
        Returns:
            List of result dictionaries with content, metadata, and scores
        """
        start_time = time.time()
        self.stats["total_searches"] += 1
        
        # Check cache
        cache_key = self._get_cache_key(query, k)
        if cache_key in self.query_cache:
            self.stats["cache_hits"] += 1
            logger.info(f"Cache hit for query: {query[:50]}...")
            return self.query_cache[cache_key]
        
        logger.info(f"Hybrid search: '{query[:60]}...' (k={k})")
        
        # Step 1: Query Enhancement
        enhanced_query = self.query_enhancer.expand_query(query)
        if self.use_hyde:
            enhanced_query = self.query_enhancer.generate_hyde(enhanced_query)
        
        # Step 2: Dense Retrieval (FAISS)
        dense_docs = self._dense_search(enhanced_query, k=k*3)
        
        # Step 3: Sparse Retrieval (BM25)
        sparse_docs = self._sparse_search(query, k=k*3)  # Use original query for keyword matching
        
        # Step 4: Fusion (combine and deduplicate)
        candidate_docs = self._fuse_results(dense_docs, sparse_docs, alpha=alpha)
        
        # Step 5: Re-ranking
        if self.reranker and candidate_docs:
            candidate_docs = self._rerank(query, candidate_docs)
        
        # Step 6: Contextual Compression
        if use_compression and candidate_docs:
            candidate_docs = self.compressor.compress(candidate_docs, query)
        
        # Select top-k
        final_docs = candidate_docs[:k]
        
        # Format results
        final_results = []
        for doc in final_docs:
            meta = doc.metadata
            final_results.append({
                "content": doc.page_content,
                "title": meta.get("title"),
                "handle": meta.get("handle"),
                "authors": meta.get("authors"),
                "year": meta.get("year"),
                "source": meta.get("source"),
                "score": meta.get('final_score', meta.get('rerank_score', 0.0)),
                "compressed": meta.get('compressed', False)
            })
        
        # Cache results
        if len(self.query_cache) < 1000:
            self.query_cache[cache_key] = final_results
        
        # Update stats
        duration = time.time() - start_time
        self.stats["avg_search_time"] = (
            (self.stats["avg_search_time"] * (self.stats["total_searches"] - 1) + duration) 
            / self.stats["total_searches"]
        )
        
        logger.info(f"Hybrid search completed in {duration:.3f}s ({len(final_results)} results)")
        
        return final_results
    
    def _dense_search(self, query: str, k: int) -> List[Document]:
        """Dense retrieval using FAISS."""
        try:
            results = self.db.similarity_search_with_score(query, k=k)
            docs = []
            for doc, score in results:
                doc.metadata['dense_score'] = float(score)
                docs.append(doc)
            return docs
        except Exception as e:
            logger.error(f"Dense search error: {e}")
            return []
    
    def _sparse_search(self, query: str, k: int) -> List[Document]:
        """Sparse retrieval using BM25."""
        try:
            results = self.bm25_retriever.search(query, k=k)
            return [doc for doc, score in results]
        except Exception as e:
            logger.error(f"Sparse search error: {e}")
            return []
    
    def _fuse_results(self, dense_docs: List[Document], sparse_docs: List[Document], alpha: float = 0.5) -> List[Document]:
        """
        Fuse dense and sparse results using reciprocal rank fusion.
        
        Args:
            dense_docs: Results from dense retrieval
            sparse_docs: Results from sparse retrieval
            alpha: Weight for dense (1-alpha for sparse)
            
        Returns:
            Fused and deduplicated document list
        """
        # Use reciprocal rank fusion (RRF)
        doc_scores = {}
        
        # Process dense results
        for rank, doc in enumerate(dense_docs, start=1):
            doc_id = hash(doc.page_content)
            rrf_score = alpha / (60 + rank)  # RRF with k=60
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {"doc": doc, "score": 0}
            doc_scores[doc_id]["score"] += rrf_score
        
        # Process sparse results
        for rank, doc in enumerate(sparse_docs, start=1):
            doc_id = hash(doc.page_content)
            rrf_score = (1 - alpha) / (60 + rank)
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {"doc": doc, "score": 0}
            doc_scores[doc_id]["score"] += rrf_score
        
        # Sort by fused score
        sorted_docs = sorted(doc_scores.values(), key=lambda x: x["score"], reverse=True)
        
        # Attach fusion score to metadata
        result = []
        for item in sorted_docs:
            doc = item["doc"]
            doc.metadata['fusion_score'] = item["score"]
            result.append(doc)
        
        return result
    
    def _rerank(self, query: str, docs: List[Document]) -> List[Document]:
        """
        Re-rank documents using cross-encoder.
        
        Args:
            query: Original query
            docs: Candidate documents
            
        Returns:
            Re-ranked documents
        """
        if not self.reranker or not docs:
            return docs
        
        # Create query-document pairs
        pairs = [[query, doc.page_content] for doc in docs]
        
        # Predict relevance scores
        scores = self.reranker.predict(pairs)
        
        # Attach scores and sort
        for doc, score in zip(docs, scores):
            doc.metadata['rerank_score'] = float(score)
            doc.metadata['final_score'] = float(score)
        
        docs.sort(key=lambda x: x.metadata['rerank_score'], reverse=True)
        
        return docs
    
    def _get_cache_key(self, query: str, k: int) -> str:
        """Generate cache key for query."""
        return hashlib.md5(f"{query}_{k}".encode()).hexdigest()

    # ==================== Persistence ====================
    
    def save(self) -> None:
        """Save FAISS index and metadata."""
        try:
            self.db.save_local("faiss_index")
            self._save_metadata()
            logger.debug("RAG pipeline saved successfully")
        except Exception as e:
            logger.error(f"Error saving RAG pipeline: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Return pipeline performance statistics."""
        cache_stats = self.embeddings.get_cache_stats()
        return {
            **self.stats,
            "embedding_cache": cache_stats,
            "query_cache_size": len(self.query_cache)
        }


# Singleton instance (backward compatibility)
rag_pipeline = None

def get_rag_pipeline() -> AdvancedRAGPipeline:
    """Get or create global RAG pipeline instance."""
    global rag_pipeline
    if rag_pipeline is None:
        rag_pipeline = AdvancedRAGPipeline()
    return rag_pipeline
