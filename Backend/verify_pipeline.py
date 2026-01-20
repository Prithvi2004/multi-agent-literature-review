
import os
import time
from main import run_analysis
from rag_pipeline import RAGPipeline

def test_pipeline():
    print("="*80)
    print("🧪 STARTING VERIFICATION TEST OF ADVANCED RAG PIPELINE")
    print("="*80)

    # 1. Initialize RAG Pipeline to ensure dependencies are loaded
    print("\n[1/3] Initializing RAG Pipeline...")
    try:
        rag = RAGPipeline()
        print("✅ RAG Pipeline initialized successfully.")
    except Exception as e:
        print(f"❌ RAG Pipeline initialization FAILED: {e}")
        return

    # 2. Define Test Query
    test_idea = "Agentic workflows in Large Language Models for automated code generation"
    test_domains = ["Computer Science", "Artificial Intelligence", "Software Engineering"]
    
    print(f"\n[2/3] Simulating Research Run: '{test_idea}'")
    print(f"      Domains: {test_domains}")

    # 3. Run Analysis (This mimics the full agent flow)
    print("\n[3/3] Running Agentic Workflow (Draft Mode)...")
    try:
        # We'll rely on the existing main.py logic but we want to monitor output
        # run_analysis returns the final result string
        result = run_analysis(test_idea, test_domains)
        
        print("\n" + "="*80)
        print("✅ PIPELINE EXECUTION COMPLETED")
        print("="*80)
        
        # Basic validation of output
        if "INSUFFICIENT_EVIDENCE" in result and len(result) < 500:
             print("⚠️ WARNING: Result seems sparse (Insufficient Evidence). Check retrieval.")
        elif len(result) > 1000:
             print(f"✅ Result length looks good: {len(result)} chars")
             print("Sample Output Start:\n" + result[:500])
        else:
             print(f"⚠️ Result length is {len(result)} chars. Verify quality.")

    except Exception as e:
        print(f"❌ Pipeline Execution FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pipeline()
