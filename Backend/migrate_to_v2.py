# migrate_to_v2.py
"""
Migration Helper Script: Upgrade to Advanced RAG System v2.0

This script helps you:
1. Verify environment setup
2. Install missing dependencies
3. Test v2 components
4. Migrate FAISS index if needed
5. Run comparative benchmarks

Usage:
    python migrate_to_v2.py --check       # Check environment only
    python migrate_to_v2.py --install     # Install dependencies
    python migrate_to_v2.py --test        # Test v2 components
    python migrate_to_v2.py --migrate     # Full migration
    python migrate_to_v2.py --benchmark   # Run benchmarks
"""

import sys
import os
import subprocess
import argparse
import json
import time
from pathlib import Path

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def check_python_version():
    """Check Python version >= 3.9"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print_success(f"Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python version: {version.major}.{version.minor}.{version.micro} (requires >= 3.9)")
        return False


def check_conda_environment():
    """Check if running in conda environment"""
    if 'CONDA_DEFAULT_ENV' in os.environ:
        env_name = os.environ['CONDA_DEFAULT_ENV']
        print_success(f"Conda environment: {env_name}")
        return True
    else:
        print_warning("Not running in a conda environment (recommended)")
        return False


def check_package(package_name, import_name=None):
    """Check if a Python package is installed"""
    if import_name is None:
        import_name = package_name.replace('-', '_')
    
    try:
        __import__(import_name)
        print_success(f"{package_name} is installed")
        return True
    except ImportError:
        print_error(f"{package_name} is NOT installed")
        return False


def check_dependencies():
    """Check all required dependencies"""
    print_header("Checking Dependencies")
    
    required_packages = [
        ("crewai", "crewai"),
        ("langchain", "langchain"),
        ("sentence-transformers", "sentence_transformers"),
        ("rank-bm25", "rank_bm25"),
        ("faiss-cpu", "faiss"),
        ("numpy", "numpy"),
        ("scikit-learn", "sklearn"),
        ("requests", "requests"),
        ("beautifulsoup4", "bs4"),
        ("arxiv", "arxiv"),
    ]
    
    optional_packages = [
        ("ragas", "ragas"),
        ("aiohttp", "aiohttp"),
    ]
    
    missing_required = []
    missing_optional = []
    
    print("\nRequired packages:")
    for pkg_name, import_name in required_packages:
        if not check_package(pkg_name, import_name):
            missing_required.append(pkg_name)
    
    print("\nOptional packages:")
    for pkg_name, import_name in optional_packages:
        if not check_package(pkg_name, import_name):
            missing_optional.append(pkg_name)
    
    return missing_required, missing_optional


def check_ollama():
    """Check if Ollama is running"""
    print_header("Checking Ollama")
    
    try:
        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        if resp.status_code == 200:
            models = resp.json().get('models', [])
            print_success(f"Ollama is running with {len(models)} models")
            if models:
                print_info("Available models:")
                for model in models[:5]:  # Show first 5
                    print(f"  - {model.get('name', 'unknown')}")
            return True
        else:
            print_error("Ollama server responded with error")
            return False
    except Exception as e:
        print_error(f"Cannot connect to Ollama: {e}")
        print_info("Start Ollama with: ollama serve")
        return False


def check_file_structure():
    """Check if necessary files exist"""
    print_header("Checking File Structure")
    
    required_files = [
        "rag_pipeline_v2.py",
        "agents_v2.py",
        "tools_v2.py",
        "evaluation_framework.py",
        "requirements.txt",
        "evidence_store.py",
        "query_rewriter.py"
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print_success(f"{file} exists")
        else:
            print_error(f"{file} NOT FOUND")
            missing_files.append(file)
    
    return len(missing_files) == 0


def install_dependencies(missing_required, missing_optional):
    """Install missing dependencies"""
    print_header("Installing Dependencies")
    
    if not missing_required and not missing_optional:
        print_success("All dependencies already installed!")
        return True
    
    # Check for FAISS special handling
    if "faiss-cpu" in missing_required:
        print_warning("FAISS detected in missing packages")
        if sys.platform == "win32":
            print_info("Windows detected - FAISS should be installed via conda:")
            print_info("  conda install -c conda-forge faiss-cpu")
            response = input("Do you want to attempt conda install now? (y/n): ")
            if response.lower() == 'y':
                subprocess.run(["conda", "install", "-c", "conda-forge", "faiss-cpu", "-y"])
            missing_required.remove("faiss-cpu")
    
    # Install required packages
    if missing_required:
        print_info(f"Installing required packages: {', '.join(missing_required)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_required)
            print_success("Required packages installed successfully")
        except subprocess.CalledProcessError:
            print_error("Failed to install some required packages")
            return False
    
    # Install optional packages
    if missing_optional:
        response = input(f"\nInstall optional packages ({', '.join(missing_optional)})? (y/n): ")
        if response.lower() == 'y':
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_optional)
                print_success("Optional packages installed successfully")
            except subprocess.CalledProcessError:
                print_warning("Some optional packages failed to install")
    
    return True


def test_v2_components():
    """Test v2 components can be imported"""
    print_header("Testing v2 Components")
    
    tests = [
        ("RAG Pipeline v2", "from rag_pipeline_v2 import AdvancedRAGPipeline"),
        ("Agents v2", "from agents_v2 import query_analyzer_agent"),
        ("Tools v2", "from tools_v2 import AdvancedRAGTool"),
        ("Evaluation Framework", "from evaluation_framework import RAGEvaluator"),
    ]
    
    success_count = 0
    for name, import_stmt in tests:
        try:
            exec(import_stmt)
            print_success(f"{name} imported successfully")
            success_count += 1
        except Exception as e:
            print_error(f"{name} import failed: {e}")
    
    if success_count == len(tests):
        print_success("\n✓ All v2 components working!")
        return True
    else:
        print_error(f"\n✗ {len(tests) - success_count} components failed")
        return False


def run_benchmark():
    """Run performance benchmark comparing v1 and v2"""
    print_header("Running Performance Benchmark")
    
    try:
        # Import both versions
        from rag_pipeline import RAGPipeline as RAGv1
        from rag_pipeline_v2 import AdvancedRAGPipeline as RAGv2
        
        print_info("Initializing RAG pipelines...")
        rag_v1 = RAGv1()
        rag_v2 = RAGv2()
        
        # Test queries
        test_queries = [
            "transformer architecture for NLP",
            "attention mechanism in neural networks",
            "efficient deep learning models"
        ]
        
        print_info("Running benchmark queries...")
        
        # Benchmark v1
        print("\nv1 Performance:")
        v1_times = []
        for query in test_queries:
            start = time.time()
            rag_v1.search(query, k=5)
            duration = time.time() - start
            v1_times.append(duration)
            print(f"  {query[:40]}... : {duration:.3f}s")
        
        # Benchmark v2
        print("\nv2 Performance:")
        v2_times = []
        for query in test_queries:
            start = time.time()
            rag_v2.search(query, k=5)
            duration = time.time() - start
            v2_times.append(duration)
            print(f"  {query[:40]}... : {duration:.3f}s")
        
        # Results
        v1_avg = sum(v1_times) / len(v1_times)
        v2_avg = sum(v2_times) / len(v2_times)
        improvement = ((v1_avg - v2_avg) / v1_avg) * 100
        
        print(f"\n{Colors.BOLD}Results:{Colors.ENDC}")
        print(f"  v1 Average: {v1_avg:.3f}s")
        print(f"  v2 Average: {v2_avg:.3f}s")
        if improvement > 0:
            print_success(f"  v2 is {improvement:.1f}% faster!")
        else:
            print_warning(f"  v2 is {abs(improvement):.1f}% slower (may improve with cache warming)")
        
        # Cache stats
        if hasattr(rag_v2, 'get_stats'):
            stats = rag_v2.get_stats()
            print(f"\nv2 Cache Statistics:")
            print(f"  - Query cache: {stats.get('query_cache_size', 0)} entries")
            print(f"  - Embedding cache: {stats.get('embedding_cache', {}).get('cache_size', 0)} entries")
            print(f"  - Cache hit rate: {stats.get('embedding_cache', {}).get('hit_rate', 0):.1f}%")
        
        return True
        
    except Exception as e:
        print_error(f"Benchmark failed: {e}")
        return False


def generate_migration_report():
    """Generate a migration status report"""
    print_header("Migration Status Report")
    
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "conda_env": os.environ.get('CONDA_DEFAULT_ENV', 'None'),
        "checks": {
            "python_version": check_python_version(),
            "conda_environment": check_conda_environment(),
            "file_structure": check_file_structure(),
            "ollama": check_ollama(),
        }
    }
    
    # Save report
    report_file = "migration_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print_success(f"Report saved to: {report_file}")
    
    # Summary
    passed = sum(report["checks"].values())
    total = len(report["checks"])
    
    print(f"\n{Colors.BOLD}Summary:{Colors.ENDC}")
    print(f"  Checks passed: {passed}/{total}")
    
    if passed == total:
        print_success("\n✓ System ready for v2!")
        print_info("\nNext steps:")
        print("  1. Install dependencies: python migrate_to_v2.py --install")
        print("  2. Test components: python migrate_to_v2.py --test")
        print("  3. Run benchmark: python migrate_to_v2.py --benchmark")
        print("  4. Start using v2: from rag_pipeline_v2 import AdvancedRAGPipeline")
    else:
        print_warning("\n⚠ Some checks failed. Review issues above.")
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Migrate to Advanced RAG System v2.0")
    parser.add_argument("--check", action="store_true", help="Check environment and dependencies")
    parser.add_argument("--install", action="store_true", help="Install missing dependencies")
    parser.add_argument("--test", action="store_true", help="Test v2 components")
    parser.add_argument("--benchmark", action="store_true", help="Run performance benchmark")
    parser.add_argument("--migrate", action="store_true", help="Full migration (all steps)")
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if not any(vars(args).values()):
        parser.print_help()
        print("\n" + "="*80)
        print(f"{Colors.BOLD}Quick Start:{Colors.ENDC}")
        print("  python migrate_to_v2.py --check      # Check system")
        print("  python migrate_to_v2.py --migrate    # Full migration")
        print("="*80 + "\n")
        return
    
    # Execute requested operations
    if args.check or args.migrate:
        report = generate_migration_report()
    
    if args.install or args.migrate:
        missing_req, missing_opt = check_dependencies()
        if missing_req or missing_opt:
            install_dependencies(missing_req, missing_opt)
    
    if args.test or args.migrate:
        test_v2_components()
    
    if args.benchmark:
        run_benchmark()
    
    if args.migrate:
        print_header("Migration Complete!")
        print_success("Your system is ready to use Advanced RAG v2.0")
        print_info("\nSee README_v2.md for usage examples and advanced features")


if __name__ == "__main__":
    main()
