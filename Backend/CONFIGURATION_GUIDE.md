# Configuration Guide for Advanced RAG System v2.0

## 🔧 Configuration Options

This guide explains all customizable parameters for optimizing your literature review system.

---

## 📋 Environment Variables (.env)

Create a `.env` file in the Backend directory:

```env
# =============================================================================
# LLM CONFIGURATION
# =============================================================================

# Ollama Model Selection
OLLAMA_MODEL=qwen2.5:14b
# Options: qwen2.5:14b, qwen2.5:7b, llama2:13b, mistral:7b, etc.
# Larger models = better quality, slower inference

# Ollama Server URL
OLLAMA_BASE_URL=http://localhost:11434
# Change if Ollama runs on different host/port

# Temperature (0.0 - 1.0)
TEMPERATURE=0.1
# Lower = more deterministic, Higher = more creative
# Recommended: 0.1 for academic rigor

# Context Window Size
OLLAMA_CONTEXT_SIZE=16384
# Larger = more context, more memory usage
# Options: 4096, 8192, 16384, 32768

# =============================================================================
# RAG PIPELINE CONFIGURATION
# =============================================================================

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2
# Options:
#   - all-MiniLM-L6-v2: Fast, good quality (384 dims)
#   - all-MiniLM-L12-v2: Slower, better quality (384 dims)
#   - mxbai-embed-large: High quality (1024 dims)
#   - nomic-embed-text: Optimized for long context (768 dims)

# Chunking Strategy
CHUNK_SIZE=400
# Characters per chunk (300-600 recommended)

CHUNK_OVERLAP=100
# Overlap between chunks (50-150 recommended)

# Retrieval Settings
TOP_K_RESULTS=5
# Number of results to return (3-10 recommended)

MIN_CONFIDENCE_THRESHOLD=0.3
# Minimum relevance score (0.0-1.0)

# Hybrid Search Balance
HYBRID_SEARCH_ALPHA=0.5
# Dense vs Sparse balance (0.0-1.0)
# 0.0 = 100% sparse (keyword), 1.0 = 100% dense (semantic)

# =============================================================================
# ADVANCED FEATURES
# =============================================================================

# Enable HyDE (Hypothetical Document Embeddings)
USE_HYDE=false
# true = Better semantic matching, slower
# false = Faster, standard retrieval

# Enable Re-ranking
ENABLE_RERANKING=true
# true = Higher precision, slower
# false = Faster, lower precision

# Enable Contextual Compression
USE_COMPRESSION=true
# true = Extract only relevant sentences
# false = Use full chunks

COMPRESSION_RATIO=0.7
# Portion of text to keep (0.5-0.9 recommended)

# =============================================================================
# PERFORMANCE TUNING
# =============================================================================

# Cache Settings
MAX_EMBEDDING_CACHE_SIZE=10000
# Number of embeddings to cache

MAX_QUERY_CACHE_SIZE=1000
# Number of query results to cache

# Batch Processing
EMBEDDING_BATCH_SIZE=32
# Embeddings per batch (16-64 recommended)

# Parallel Retrieval
MAX_PARALLEL_SOURCES=3
# Number of paper sources to query in parallel

# =============================================================================
# AGENT CONFIGURATION
# =============================================================================

# Agent Memory
ENABLE_AGENT_MEMORY=true
# Persistent memory across sessions

MEMORY_FILE=agent_memory.json
# File to store agent memory

MAX_MEMORY_SESSIONS=50
# Number of past sessions to remember

# Agent Verbosity
AGENT_VERBOSE=true
# Print agent reasoning steps

# =============================================================================
# EVALUATION SETTINGS
# =============================================================================

# Enable Evaluation Framework
ENABLE_EVALUATION=true
# Run quality metrics after generation

# RAGAS Metrics
ENABLE_RAGAS=false
# Requires OpenAI API (optional)

# Custom Metrics
MIN_CITATION_DENSITY=1.5
# Citations per 100 words (target)

MIN_ACADEMIC_RIGOR=0.7
# Overall rigor score threshold (0-1)

# =============================================================================
# OUTPUT SETTINGS
# =============================================================================

# Output Directory
OUTPUT_DIR=outputs/latest_research_session

# Save Intermediate Results
SAVE_AGENT_OUTPUTS=true
# Save each agent's output separately

# Logging Level
LOG_LEVEL=INFO
# Options: DEBUG, INFO, WARNING, ERROR

# Enable Colored Logs
ENABLE_COLOR_LOGS=true
# Beautiful terminal output

# =============================================================================
# PAPER RETRIEVAL
# =============================================================================

# arXiv Settings
ARXIV_MAX_RESULTS=5
ARXIV_DELAY_SECONDS=3.0

# Semantic Scholar Settings
SEMANTIC_SCHOLAR_MAX_RESULTS=4

# PubMed Settings
PUBMED_MAX_RESULTS=4

# API Rate Limiting
API_DELAY=1.5
# Seconds between API calls

MAX_RETRIES=3
# Retry attempts for failed requests

# =============================================================================
# FAISS INDEX OPTIMIZATION
# =============================================================================

# Index Type
FAISS_INDEX_TYPE=Flat
# Options: Flat (accurate), IVF (fast), PQ (compressed)

# IVF Parameters (if using IVF)
FAISS_NLIST=100
# Number of clusters

FAISS_NPROBE=10
# Clusters to search

# Product Quantization (if using PQ)
FAISS_M=8
# Number of subquantizers

FAISS_NBITS=8
# Bits per subquantizer
```

---

## 🎯 Configuration Profiles

### Profile 1: Maximum Quality

```env
OLLAMA_MODEL=qwen2.5:14b
TEMPERATURE=0.1
EMBEDDING_MODEL=mxbai-embed-large
USE_HYDE=true
ENABLE_RERANKING=true
TOP_K_RESULTS=10
CHUNK_SIZE=400
CHUNK_OVERLAP=150
HYBRID_SEARCH_ALPHA=0.5
```

**Best for:** PhD-level research, publication-grade reviews  
**Tradeoff:** Slower (1.5-2x), higher memory usage

---

### Profile 2: Balanced Performance

```env
OLLAMA_MODEL=qwen2.5:7b
TEMPERATURE=0.1
EMBEDDING_MODEL=all-MiniLM-L6-v2
USE_HYDE=false
ENABLE_RERANKING=true
TOP_K_RESULTS=5
CHUNK_SIZE=400
CHUNK_OVERLAP=100
HYBRID_SEARCH_ALPHA=0.5
```

**Best for:** Most use cases, good balance  
**Tradeoff:** Recommended default

---

### Profile 3: Maximum Speed

```env
OLLAMA_MODEL=qwen2.5:7b
TEMPERATURE=0.1
EMBEDDING_MODEL=all-MiniLM-L6-v2
USE_HYDE=false
ENABLE_RERANKING=false
TOP_K_RESULTS=3
CHUNK_SIZE=300
CHUNK_OVERLAP=50
HYBRID_SEARCH_ALPHA=1.0
```

**Best for:** Quick explorations, testing  
**Tradeoff:** Lower quality, faster results

---

## 🔬 Experiment Guide

### Test Different Embedding Models

```python
from rag_pipeline_v2 import AdvancedRAGPipeline

# Test 1: Fast model
rag_fast = AdvancedRAGPipeline(embedding_model="all-MiniLM-L6-v2")

# Test 2: High-quality model
rag_quality = AdvancedRAGPipeline(embedding_model="mxbai-embed-large")

# Compare results
query = "transformer attention mechanisms"
results_fast = rag_fast.hybrid_search(query, k=5)
results_quality = rag_quality.hybrid_search(query, k=5)
```

### Test HyDE Impact

```python
# Without HyDE
rag_no_hyde = AdvancedRAGPipeline(use_hyde=False)

# With HyDE
rag_with_hyde = AdvancedRAGPipeline(use_hyde=True)

# Compare relevance scores
```

### Test Hybrid Search Balance

```python
rag = AdvancedRAGPipeline()

# More semantic (dense)
results_semantic = rag.hybrid_search(query, alpha=0.9)

# Balanced
results_balanced = rag.hybrid_search(query, alpha=0.5)

# More keyword (sparse)
results_keyword = rag.hybrid_search(query, alpha=0.1)
```

---

## 📊 Performance Tuning

### For Speed

1. **Reduce chunk size**: `CHUNK_SIZE=300`
2. **Disable HyDE**: `USE_HYDE=false`
3. **Disable re-ranking**: `ENABLE_RERANKING=false`
4. **Smaller model**: `EMBEDDING_MODEL=all-MiniLM-L6-v2`
5. **Fewer results**: `TOP_K_RESULTS=3`

### For Quality

1. **Increase chunk overlap**: `CHUNK_OVERLAP=150`
2. **Enable HyDE**: `USE_HYDE=true`
3. **Enable re-ranking**: `ENABLE_RERANKING=true`
4. **Larger model**: `EMBEDDING_MODEL=mxbai-embed-large`
5. **More results**: `TOP_K_RESULTS=10`

### For Memory Efficiency

1. **Smaller embedding model**: `EMBEDDING_MODEL=all-MiniLM-L6-v2`
2. **Reduce cache size**: `MAX_EMBEDDING_CACHE_SIZE=5000`
3. **Smaller chunks**: `CHUNK_SIZE=300`
4. **Disable compression**: `USE_COMPRESSION=false`

---

## 🧪 A/B Testing Template

```python
import time
from rag_pipeline_v2 import AdvancedRAGPipeline

# Configuration A
config_a = {
    "embedding_model": "all-MiniLM-L6-v2",
    "use_hyde": False
}

# Configuration B
config_b = {
    "embedding_model": "mxbai-embed-large",
    "use_hyde": True
}

# Test queries
test_queries = [
    "efficient transformer architectures",
    "attention mechanisms in NLP",
    "low-resource machine translation"
]

# Run tests
for name, config in [("Config A", config_a), ("Config B", config_b)]:
    print(f"\nTesting {name}")
    rag = AdvancedRAGPipeline(**config)

    total_time = 0
    for query in test_queries:
        start = time.time()
        results = rag.hybrid_search(query, k=5)
        duration = time.time() - start
        total_time += duration

        print(f"  {query[:40]}... : {duration:.3f}s, {len(results)} results")

    avg_time = total_time / len(test_queries)
    print(f"  Average: {avg_time:.3f}s")

    # Get stats
    stats = rag.get_stats()
    print(f"  Cache hit rate: {stats['embedding_cache']['hit_rate']:.1f}%")
```

---

## 📝 Best Practices

### 1. Start with Defaults

Use the balanced profile for most cases:

```env
EMBEDDING_MODEL=all-MiniLM-L6-v2
USE_HYDE=false
ENABLE_RERANKING=true
TOP_K_RESULTS=5
```

### 2. Monitor Performance

Check stats after each run:

```python
stats = rag.get_stats()
print(f"Searches: {stats['total_searches']}")
print(f"Cache hits: {stats['cache_hits']}")
print(f"Avg time: {stats['avg_search_time']}s")
```

### 3. Adjust Based on Results

- **Low relevance scores?** → Increase TOP_K, enable HyDE
- **Too slow?** → Disable HyDE, reduce TOP_K
- **Missing keywords?** → Lower HYBRID_SEARCH_ALPHA (more sparse)
- **Missing semantics?** → Increase HYBRID_SEARCH_ALPHA (more dense)

### 4. Profile Your Workload

- **Broad topics** → Use HyDE, higher alpha (semantic)
- **Specific terms** → Disable HyDE, lower alpha (keyword)
- **Mixed queries** → Balanced (alpha=0.5)

---

## 🎓 Advanced Configuration

### Custom Embedding Model

```python
# In rag_pipeline_v2.py, modify AdvancedEmbeddings.__init__():

if model_name == "my-custom-model":
    self.model = SentenceTransformer("path/to/model")
```

### Custom Re-ranker

```python
# In rag_pipeline_v2.py, modify AdvancedRAGPipeline.__init__():

self.reranker = CrossEncoder('cross-encoder/ms-marco-TinyBERT-L-2-v2')
# Faster but less accurate
```

### Custom Chunking Strategy

```python
# In rag_pipeline_v2.py, modify _create_semantic_chunks():

splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,  # Smaller chunks
    chunk_overlap=75,
    separators=["\n\n", "\n", ". ", " "],
)
```

---

## 📞 Troubleshooting Configuration Issues

### "Out of memory during indexing"

```env
CHUNK_SIZE=300
EMBEDDING_BATCH_SIZE=16
MAX_EMBEDDING_CACHE_SIZE=5000
```

### "Search too slow"

```env
USE_HYDE=false
ENABLE_RERANKING=false
TOP_K_RESULTS=3
```

### "Low-quality results"

```env
TOP_K_RESULTS=10
ENABLE_RERANKING=true
CHUNK_OVERLAP=150
```

### "Ollama timeouts"

```env
OLLAMA_CONTEXT_SIZE=8192
TEMPERATURE=0.1
# Use smaller model
OLLAMA_MODEL=qwen2.5:7b
```

---

**Customize these settings to optimize for your specific research needs!** 🎯
