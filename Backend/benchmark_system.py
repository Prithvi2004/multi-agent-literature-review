import time
import logging
import numpy as np
from rag_pipeline import RAGPipeline
from llm_client import llm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_benchmark():
    print("="*80)
    print("🚀 SYSTEM BENCHMARKING SUITE")
    print("="*80)
    
    # 1. Initialize
    print("\n[1/3] Initializing RAG Pipeline...")
    start_init = time.time()
    rag = RAGPipeline()
    init_time = time.time() - start_init
    print(f"✓ Pipeline initialized in {init_time:.2f}s")
    
    # 2. Test Queries
    queries = [
        "What are the limitations of Transformer models?",
        "How does semantic search differ from keyword search?",
        "Recent advances in multi-agent reinforcement learning",
        "Explain the concept of HyDE (Hypothetical Document Embeddings)",
        "Optimization techniques for RAG systems"
    ]
    
    # 3. Run Benchmark
    print(f"\n[2/3] Running Search Benchmark ({len(queries)} queries)...")
    latencies_standard = []
    latencies_hyde = []
    
    # HyDE Generator
    def hyde_gen(q):
        return llm.generate(f"Hypothetical abstract: {q}")

    for q in queries:
        print(f"  > Query: {q}")
        
        # Standard Hybrid
        s_start = time.time()
        rag.hybrid_search(q, k=5, use_hyde=False)
        s_dur = time.time() - s_start
        latencies_standard.append(s_dur)
        print(f"    - Standard Hybrid: {s_dur:.4f}s")
        
        # HyDE
        h_start = time.time()
        rag.hybrid_search(q, k=5, use_hyde=True, generator_func=hyde_gen)
        h_dur = time.time() - h_start
        latencies_hyde.append(h_dur)
        print(f"    - HyDE Enhanced:   {h_dur:.4f}s")
    
    # 4. Report
    print(f"\n[3/3] Results")
    print("-" * 40)
    print(f"Standard Hybrid Search:")
    print(f"  Avg Latency: {np.mean(latencies_standard):.4f}s")
    print(f"  P95 Latency: {np.percentile(latencies_standard, 95):.4f}s")
    print("-" * 40)
    print(f"HyDE Enhanced Search:")
    print(f"  Avg Latency: {np.mean(latencies_hyde):.4f}s")
    print(f"  P95 Latency: {np.percentile(latencies_hyde, 95):.4f}s")
    print("-" * 40)
    print("Benchmark Complete.")

if __name__ == "__main__":
    run_benchmark()
