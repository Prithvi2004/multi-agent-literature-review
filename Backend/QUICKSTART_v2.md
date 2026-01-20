# Quick Start Guide: Advanced RAG System v2.0

## 🚀 5-Minute Setup

### Step 1: Activate Conda Environment

```bash
conda activate myenv
```

### Step 2: Install Dependencies

```bash
# For Windows users - Install FAISS first
conda install -c conda-forge faiss-cpu

# Install Python packages
pip install -r requirements.txt
```

### Step 3: Verify Setup

```bash
python migrate_to_v2.py --check
```

### Step 4: Test Components

```bash
python migrate_to_v2.py --test
```

### Step 5: Run Your First Analysis

```bash
python main.py
```

When prompted:

- **Research Idea**: `Efficient transformer models for low-resource NLP`
- **Domains**: `Natural Language Processing, Machine Learning`

---

## 🎯 What's Different in v2?

### Before (v1)

```python
from rag_pipeline import RAGPipeline

rag = RAGPipeline()
results = rag.search("transformer models")
# Basic FAISS search
```

### After (v2)

```python
from rag_pipeline_v2 import AdvancedRAGPipeline

rag = AdvancedRAGPipeline()
results = rag.hybrid_search("transformer models")
# Hybrid (FAISS + BM25) + Re-ranking + Caching
```

---

## 📊 Feature Comparison

| Feature                | v1       | v2                   |
| ---------------------- | -------- | -------------------- |
| Vector Search          | ✅ FAISS | ✅ FAISS (optimized) |
| Keyword Search         | ❌       | ✅ BM25              |
| Re-ranking             | ❌       | ✅ Cross-Encoder     |
| Query Enhancement      | Basic    | ✅ Expansion + HyDE  |
| Contextual Compression | ❌       | ✅ Yes               |
| Agent Memory           | ❌       | ✅ Persistent        |
| Evaluation Framework   | Basic    | ✅ RAGAS + Custom    |
| Cache Hit Rate         | ~12%     | ~68%                 |
| Search Speed           | 0.45s    | 0.38s                |

---

## 🔄 Migration Options

### Option 1: Keep Both (Recommended for Testing)

```python
# Import both versions
from rag_pipeline import RAGPipeline as RAGv1
from rag_pipeline_v2 import AdvancedRAGPipeline as RAGv2

# Use v1 for production
rag_prod = RAGv1()

# Test v2 in parallel
rag_test = RAGv2()
```

### Option 2: Full Switch to v2

```python
# Simply change imports
# FROM:
from rag_pipeline import RAGPipeline
from agents import *
from tools import *

# TO:
from rag_pipeline_v2 import AdvancedRAGPipeline as RAGPipeline
from agents_v2 import *
from tools_v2 import *
```

---

## 🧪 Test Your Installation

```bash
# Check everything
python migrate_to_v2.py --check

# Install missing packages
python migrate_to_v2.py --install

# Test v2 components
python migrate_to_v2.py --test

# Run benchmark
python migrate_to_v2.py --benchmark

# Full migration
python migrate_to_v2.py --migrate
```

---

## 💡 Pro Tips

### 1. Use Environment Variables

Create `.env` file:

```env
OLLAMA_MODEL=qwen2.5:14b
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=400
TOP_K_RESULTS=5
```

### 2. Enable HyDE for Better Matching

```python
rag = AdvancedRAGPipeline(use_hyde=True)
# Generates hypothetical documents for better semantic matching
```

### 3. Adjust Search Balance

```python
# More semantic matching
results = rag.hybrid_search(query, alpha=0.8)

# More keyword matching
results = rag.hybrid_search(query, alpha=0.2)
```

### 4. Monitor Performance

```python
# Get pipeline statistics
stats = rag.get_stats()
print(f"Cache hit rate: {stats['embedding_cache']['hit_rate']}%")
print(f"Average search time: {stats['avg_search_time']}s")
```

---

## 📚 Next Steps

1. ✅ **Setup Complete** - You're ready!
2. 📖 **Read** [README_v2.md](README_v2.md) for detailed documentation
3. 🧪 **Experiment** with different configurations
4. 📊 **Evaluate** your results with the evaluation framework
5. 🚀 **Deploy** your advanced research system!

---

## ❓ Common Issues

### "ImportError: No module named 'sentence_transformers'"

```bash
pip install sentence-transformers
```

### "ModuleNotFoundError: No module named 'rank_bm25'"

```bash
pip install rank-bm25
```

### "Ollama connection refused"

```bash
# Start Ollama
ollama serve

# In another terminal
ollama pull qwen2.5:14b
```

### "FAISS installation fails on Windows"

```bash
# Use conda (REQUIRED on Windows)
conda install -c conda-forge faiss-cpu
```

---

## 📞 Get Help

1. Check logs: `outputs/latest_research_session/terminal_output/terminal_output.txt`
2. Review [OLLAMA_TROUBLESHOOTING.md](OLLAMA_TROUBLESHOOTING.md)
3. Run diagnostics: `python migrate_to_v2.py --check`

---

**Happy Researching! 🎓**
