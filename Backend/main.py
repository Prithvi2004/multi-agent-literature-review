# main.py
import os
import json
import arxiv
import requests
import logging
import sys
import time
import re
from datetime import datetime
from bs4 import BeautifulSoup
from crewai import Crew, Process
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import hashlib
from typing import Dict, Any, List

# Enable CrewAI tracing
os.environ['CREWAI_TRACING_ENABLED'] = 'true'

class TeeOutput:
    """Capture output to both file and original stream, with ANSI code stripping for file."""
    def __init__(self, file_path, original_stream):
        self.file = open(file_path, 'w', encoding='utf-8')
        self.original = original_stream
        self.buffer = []
        import re
        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    
    def write(self, data):
        self.original.write(data)
        self.original.flush()
        clean_data = self.ansi_escape.sub('', data)
        self.file.write(clean_data)
        self.file.flush()
    
    def flush(self):
        self.original.flush()
        self.file.flush()
    
    def close(self):
        self.file.close()

# Metrics tracking
class MetricsTracker:
    def __init__(self):
        self.start_time = time.time()
        self.metrics = {
            "session_id": datetime.now().strftime('%Y%m%d_%H%M%S'),
            "start_time": datetime.now().isoformat(),
            "inputs": {},
            "outputs": {},
            "api_calls": [],
            "agent_performance": [],
            "rag_operations": [],
            "llm_calls": [],
            "errors": [],
            "timing": {}
        }
    
    def log_input(self, key: str, value: Any):
        self.metrics["inputs"][key] = value
    
    def log_output(self, key: str, value: Any):
        self.metrics["outputs"][key] = value
    
    def log_api_call(self, source: str, query: str, results_count: int, duration: float, success: bool, error: str = None):
        self.metrics["api_calls"].append({
            "source": source,
            "query": query[:100],
            "results_count": results_count,
            "duration_seconds": round(duration, 2),
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
    
    def log_agent_performance(self, agent_name: str, task: str, duration: float, input_length: int, output_length: int, success: bool):
        self.metrics["agent_performance"].append({
            "agent": agent_name,
            "task": task[:200],
            "duration_seconds": round(duration, 2),
            "input_length_chars": input_length,
            "output_length_chars": output_length,
            "estimated_tokens": (input_length + output_length) // 4,  # Rough estimate
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
    
    def log_rag_operation(self, operation: str, query: str, results_count: int, duration: float, cache_hit: bool = False):
        self.metrics["rag_operations"].append({
            "operation": operation,
            "query": query[:100],
            "results_count": results_count,
            "duration_seconds": round(duration, 4),
            "cache_hit": cache_hit,
            "timestamp": datetime.now().isoformat()
        })
    
    def log_llm_call(self, model: str, prompt_length: int, response_length: int, duration: float, success: bool):
        self.metrics["llm_calls"].append({
            "model": model,
            "prompt_length_chars": prompt_length,
            "response_length_chars": response_length,
            "estimated_input_tokens": prompt_length // 4,
            "estimated_output_tokens": response_length // 4,
            "duration_seconds": round(duration, 2),
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
    
    def log_error(self, error_type: str, message: str, context: str = ""):
        self.metrics["errors"].append({
            "type": error_type,
            "message": message,
            "context": context,
            "timestamp": datetime.now().isoformat()
        })
    
    def log_timing(self, phase: str, duration: float):
        self.metrics["timing"][phase] = round(duration, 2)
    
    def finalize(self):
        self.metrics["end_time"] = datetime.now().isoformat()
        self.metrics["total_duration_seconds"] = round(time.time() - self.start_time, 2)
        self.metrics["summary"] = {
            "total_api_calls": len(self.metrics["api_calls"]),
            "successful_api_calls": sum(1 for call in self.metrics["api_calls"] if call["success"]),
            "total_papers_retrieved": sum(call["results_count"] for call in self.metrics["api_calls"]),
            "total_agent_tasks": len(self.metrics["agent_performance"]),
            "total_rag_operations": len(self.metrics["rag_operations"]),
            "total_llm_calls": len(self.metrics["llm_calls"]),
            "total_estimated_tokens": sum(call.get("estimated_input_tokens", 0) + call.get("estimated_output_tokens", 0) for call in self.metrics["llm_calls"]),
            "rag_cache_hit_rate": round(sum(1 for op in self.metrics["rag_operations"] if op.get("cache_hit", False)) / max(len(self.metrics["rag_operations"]), 1) * 100, 2),
            "total_errors": len(self.metrics["errors"])
        }
    
    def save(self, filename: str = None, finalize: bool = True):
        if filename is None:
            filename = f"metrics_{self.metrics['session_id']}.json"
        if finalize:
            self.finalize()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, indent=2, ensure_ascii=False)
        return filename
    
    def save_realtime(self, filename: str = None):
        if filename is None:
            filename = f"metrics_{self.metrics['session_id']}.json"
        temp_metrics = self.metrics.copy()
        temp_metrics["current_duration_seconds"] = round(time.time() - self.start_time, 2)
        temp_metrics["status"] = "in_progress"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(temp_metrics, f, indent=2, ensure_ascii=False)
        return filename

# Global metrics tracker
metrics = MetricsTracker()

# Configure logging and output capture with organized folders
session_folder = os.path.join('outputs', 'latest_research_session')
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_folder = os.path.join('outputs', f'backup_session_{timestamp}')

review_folder = os.path.join(session_folder, 'review')
terminal_folder = os.path.join(session_folder, 'terminal_output')
metrics_folder = os.path.join(session_folder, 'metrics')
final_report_folder = os.path.join(session_folder, 'final_report')

os.makedirs(review_folder, exist_ok=True)
os.makedirs(terminal_folder, exist_ok=True)
os.makedirs(metrics_folder, exist_ok=True)
os.makedirs(final_report_folder, exist_ok=True)

print(f"\n{'='*80}")
print(f"🚀 Multi-Agent Literature Review System - Research Grade (PhD Level)")
print(f"{'='*80}")
print(f"\n📁 SESSION OUTPUTS")
print(f"{'='*80}")
print(f"📁 Main Session: {session_folder}")
print(f"   (This folder will be overwritten each run)")
print(f"   📝 review/literature_review.log")
print(f"   🖥️  terminal_output/terminal_output.txt")
print(f"   📊 metrics/metrics.json")
print(f"   🤖 ollama_logs/ollama_api.log  ← Streaming API Calls")
print(f"   📄 final_report/final_research_report.md")
print(f"   📄 final_report/detailed_agent_analysis.txt")
print(f"{'='*80}\n")

log_filename = os.path.join(review_folder, 'literature_review.log')
output_filename = os.path.join(terminal_folder, 'terminal_output.txt')
metrics_filename = os.path.join(metrics_folder, 'metrics.json')
final_report_filename = os.path.join(final_report_folder, 'final_research_report.md')
detailed_analysis_filename = os.path.join(final_report_folder, 'detailed_agent_analysis.txt')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

original_stdout = sys.stdout
original_stderr = sys.stderr
sys.stdout = TeeOutput(output_filename, original_stdout)
sys.stderr = sys.stdout

logger.info(f"=" * 80)
logger.info(f"Multi-Agent Literature Review System Started (PhD Edition)")
logger.info(f"Session folder: {session_folder}")
logger.info(f"Review log: {log_filename}")
logger.info(f"=" * 80)

# Rate limiting configuration
API_DELAY = 1.5
MAX_RETRIES = 3
RETRY_DELAY = 2

# IMPORT NEW AGENTS
from agents import (
    retrieval_agent, 
    decomposition_agent,
    reasoning_agent, 
    gap_novelty_agent,
    synthesis_agent,
    quality_control_agent
)
from tasks import create_tasks
from tools import rag_tool, rag_tool_instance, citation_verifier_tool, evidence_validator, validate_output_tool
from rag_pipeline import RAGPipeline
from evidence_store import evidence_store
from query_rewriter import query_rewriter

# Initialize global RAG
rag_pipeline = RAGPipeline()
evidence_validator.set_store(evidence_store)

def fetch_arxiv_papers(query: str, max_results=5):
    """Fetch papers from arXiv with retry logic and rate limiting."""
    logger.info(f"Fetching papers from arXiv with query: '{query}' (max_results={max_results})")
    start_time = time.time()
    for attempt in range(MAX_RETRIES):
        try:
            time.sleep(API_DELAY)
            client = arxiv.Client(
                page_size=max_results,
                delay_seconds=3.0,
                num_retries=2
            )
            search = arxiv.Search(
                query=query, 
                max_results=max_results, 
                sort_by=arxiv.SortCriterion.Relevance
            )
            papers = []
            for r in client.results(search):
                papers.append({
                    "title": r.title,
                    "authors": ", ".join([str(a) for a in r.authors]),
                    "year": r.published.year,
                    "abstract": r.summary,
                    "source": "arXiv",
                    "url": r.entry_id
                })
            duration = time.time() - start_time
            logger.info(f"Retrieved {len(papers)} papers from arXiv in {duration:.2f}s")
            metrics.log_api_call("arXiv", query, len(papers), duration, True)
            return papers
        except arxiv.HTTPError as e:
            if "429" in str(e):
                wait_time = RETRY_DELAY * (attempt + 1)
                logger.warning(f"arXiv rate limit hit. Waiting {wait_time}s")
                time.sleep(wait_time)
            else:
                logger.error(f"arXiv HTTP error: {e}")
                break
        except Exception as e:
            logger.error(f"Error fetching from arXiv: {e}")
            break
    metrics.log_api_call("arXiv", query, 0, time.time() - start_time, False, "Max retries exceeded")
    return []

def fetch_semantic_scholar_papers(query: str, max_results=5):
    """Fetch papers from Semantic Scholar with retry logic."""
    start_time = time.time()
    logger.info(f"Fetching papers from Semantic Scholar with query: '{query}' (max_results={max_results})")
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {"query": query, "limit": max_results, "fields": "title,authors,year,abstract,url"}
    
    for attempt in range(MAX_RETRIES):
        try:
            time.sleep(API_DELAY)
            res = requests.get(url, params=params, timeout=15)
            res.raise_for_status()
            data = res.json()
            papers = []
            for p in data.get("data", []):
                authors = ", ".join([a.get("name", "") for a in p.get("authors", [])])
                papers.append({
                    "title": p.get("title", ""),
                    "authors": authors,
                    "year": p.get("year", ""),
                    "abstract": p.get("abstract", ""),
                    "source": "Semantic Scholar",
                    "url": p.get("url", "")
                })
            duration = time.time() - start_time
            logger.info(f"Retrieved {len(papers)} papers from Semantic Scholar in {duration:.2f}s")
            metrics.log_api_call("Semantic Scholar", query, len(papers), duration, True)
            return papers
        except Exception as e:
            logger.error(f"Error fetching from Semantic Scholar: {e}")
            break
    metrics.log_api_call("Semantic Scholar", query, 0, time.time() - start_time, False, "Max retries exceeded")
    return []

def fetch_pubmed_papers(query: str, max_results=5):
    """Fetch papers from PubMed with retry logic."""
    start_time = time.time()
    logger.info(f"Fetching papers from PubMed with query: '{query}' (max_results={max_results})")
    esearch = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"}
    
    for attempt in range(MAX_RETRIES):
        try:
            time.sleep(API_DELAY)
            res = requests.get(esearch, params=params, timeout=15)
            res.raise_for_status()
            ids = res.json().get("esearchresult", {}).get("idlist", [])
            if not ids:
                return []
            
            time.sleep(API_DELAY)
            efetch = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            fetch_res = requests.get(efetch, params={"db": "pubmed", "id": ",".join(ids), "retmode": "xml"}, timeout=15)
            fetch_res.raise_for_status()
            soup = BeautifulSoup(fetch_res.content, "xml")
            papers = []
            for article in soup.find_all("PubmedArticle"):
                title = article.find("ArticleTitle").text if article.find("ArticleTitle") else ""
                authors = ", ".join([
                    f"{a.find('LastName').text} {a.find('ForeName').text}"
                    for a in article.find_all("Author")
                    if a.find("LastName") and a.find("ForeName")
                ])
                year = article.find("PubDate").find("Year").text if article.find("PubDate") and article.find("PubDate").find("Year") else ""
                abstract = article.find("AbstractText").text if article.find("AbstractText") else ""
                pmid = article.find("PMID").text if article.find("PMID") else ""
                url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}" if pmid else ""
                papers.append({
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "abstract": abstract,
                    "source": "PubMed",
                    "url": url
                })
            duration = time.time() - start_time
            logger.info(f"Retrieved {len(papers)} papers from PubMed in {duration:.2f}s")
            metrics.log_api_call("PubMed", query, len(papers), duration, True)
            return papers
        except Exception as e:
            logger.error(f"Error fetching from PubMed: {e}")
            break
    return []

def retrieve_and_index_papers(user_idea: str, domains: list):
    """Retrieve papers from multiple sources in parallel for efficiency."""
    start_time = time.time()
    base_query = f"{user_idea} {' '.join(domains)}"
    expanded_query = query_rewriter.rewrite(user_idea, domains)
    
    logger.info(f"Starting paper retrieval for idea: '{user_idea}'")
    logger.info(f"Expanded query: '{expanded_query}'")
    
    papers = []
    
    # Parallel fetching with max workers for speed
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(fetch_arxiv_papers, expanded_query, 5): "arXiv",
            executor.submit(fetch_semantic_scholar_papers, expanded_query, 4): "Semantic Scholar",
            executor.submit(fetch_pubmed_papers, expanded_query, 4): "PubMed"
        }
        
        for future in as_completed(futures):
            source = futures[future]
            try:
                result = future.result(timeout=30)
                papers.extend(result)
                logger.info(f"Successfully fetched {len(result)} papers from {source}")
            except Exception as e:
                logger.error(f"Exception fetching from {source}: {e}")
    
    # Deduplicate
    seen = set()
    unique_papers = []
    for p in papers:
        if p["title"] not in seen:
            seen.add(p["title"])
            unique_papers.append(p)
    
    if not unique_papers:
        return []
    
    # Increase Limit for Deep Research
    top_papers = unique_papers[:15]
    logger.info(f"Indexing top {len(top_papers)} papers into RAG pipeline")
    
    # Use Hybrid Indexing
    rag_pipeline.add_papers(top_papers)
    rag_pipeline.save()
    
    retrieval_duration = time.time() - start_time
    metrics.log_timing("paper_retrieval_and_indexing", retrieval_duration)
    return top_papers

def index_uploaded_paper(paper_data: dict):
    logger.info("Processing uploaded paper data")
    title = None
    abstract = None
    for sec in paper_data.get("paper_sections", []):
        if sec.get("field", "").lower() == "title":
            title = sec.get("content")
        if sec.get("field", "").lower() == "abstract":
            abstract = sec.get("content")

    if not title and paper_data.get("uploaded_papers"):
        first = paper_data.get("uploaded_papers")[0]
        title = title or first.get("title")
        abstract = abstract or first.get("abstract")

    if title:
        paper = {
            "title": title,
            "authors": paper_data.get("authors", "Unknown"),
            "year": paper_data.get("year", ""),
            "abstract": abstract or "",
            "source": paper_data.get("source", "UserUploaded"),
            "url": paper_data.get("url", "")
        }
        rag_pipeline.add_papers([paper])
        rag_pipeline.save()
        return paper
    return None

def run_analysis(user_idea: str, selected_domains: list):
    logger.info(f"="*80)
    logger.info(f"STARTING ANALYSIS")
    logger.info(f"Research Idea: {user_idea}")
    logger.info(f"="*80)
    
    metrics.log_input("research_idea", user_idea)
    metrics.log_input("selected_domains", selected_domains)
    analysis_start = time.time()
    
    # 1. Retrieve and index papers
    papers = retrieve_and_index_papers(user_idea, selected_domains)
    if not papers:
        return "❌ No relevant papers found."

    # 2. Inject RAG into tools
    logger.info("Injecting RAG pipeline into tools")
    from tools import rag_tool
    rag_tool.rag = rag_pipeline

    # 3. Assign tools to agents
    logger.info("Assigning RAG tools to agents")
    retrieval_agent.tools = [rag_tool_instance]
    decomposition_agent.tools = [rag_tool_instance]
    reasoning_agent.tools = [rag_tool_instance]
    gap_novelty_agent.tools = [rag_tool_instance, citation_verifier_tool]
    synthesis_agent.tools = [rag_tool_instance]
    quality_control_agent.tools = [rag_tool_instance, validate_output_tool, citation_verifier_tool]

    # 4. Create tasks
    logger.info("Creating tasks for crew")
    tasks = create_tasks(user_idea, selected_domains)

    # 5. Run crew
    logger.info("Initializing crew with 6 agents")
    crew = Crew(
        agents=[
            retrieval_agent,
            decomposition_agent,
            reasoning_agent,
            gap_novelty_agent,
            synthesis_agent,
            quality_control_agent
        ],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
        tracing=True
    )

    logger.info("Starting crew execution...")
    crew_start = time.time()
    result = crew.kickoff()
    crew_duration = time.time() - crew_start
    
    logger.info(f"Crew execution completed in {crew_duration:.2f}s")
    
    # Post-processing validation
    result_str = str(result)
    
    # Check for valid citations
    citation_valid, citation_msg = evidence_validator.validate_output(result_str)
    
    # Log outputs
    analysis_duration = time.time() - analysis_start
    metrics.log_timing("total_analysis", analysis_duration)
    metrics.log_output("success", True)
    
    return result_str

# CLI Entry supporting JSON inputs for paper data and optional fields
if __name__ == "__main__":
    logger.info("Starting CLI interface")
    # Built-in defaults (used when user opts in)
    default_paper_json = {
        "paper_sections": [
            {"field": "Title", "content": "Improving Text Classification Using Transformer Models"},
            {"field": "Abstract", "content": "This paper explores the use of transformer-based architectures to enhance text classification accuracy across multiple NLP tasks."}
        ],
        "uploaded_papers": []
    }

    default_optional_json = {
        "research_idea": "Investigate how lightweight transformer models can achieve competitive performance with reduced computational cost.",
        "selected_domains": ["Natural Language Processing", "Artificial Intelligence"]
    }

    # Offer a simple choice: defaults (1) or enter new data (2)
    print("Input mode:\n  1) Use built-in default values for PAPER DATA and OPTIONAL FIELDS\n  2) Enter/paste new data (JSON or manual)")
    mode = input("Press 1 or 2 (default 1): ").strip()

    paper_json = None
    optional_json = None

    if mode in ['', '1']:
        # Use both defaults
        paper_json = default_paper_json
        optional_json = default_optional_json
        logger.info("Input mode: defaults selected for both PAPER DATA and OPTIONAL FIELDS")
        print("Using built-in default PAPER DATA and OPTIONAL FIELDS.")
    else:
        # PAPER DATA input (user-provided)
        print("Paste PAPER DATA JSON (or press Enter to skip):")
        try:
            line = input().strip()
            if line:
                buffer = [line]
                while True:
                    try:
                        more = input()
                    except EOFError:
                        break
                    if not more.strip():
                        break
                    buffer.append(more)
                paper_json = json.loads("\n".join(buffer))
                logger.info("Paper data JSON parsed successfully")
            else:
                paper_json = None
        except Exception as e:
            logger.error(f"Invalid PAPER DATA JSON: {e}")
            print("Invalid PAPER DATA JSON, skipping uploaded papers.")
            paper_json = None

        # OPTIONAL FIELDS input
        print("Paste OPTIONAL FIELDS DATA JSON (or press Enter to type manually):")
        try:
            line = input().strip()
            if line:
                buffer = [line]
                while True:
                    try:
                        more = input()
                    except EOFError:
                        break
                    if not more.strip():
                        break
                    buffer.append(more)
                optional_json = json.loads("\n".join(buffer))
                logger.info("Optional fields JSON parsed successfully")
            else:
                optional_json = None
        except Exception as e:
            logger.error(f"Invalid optional fields JSON: {e}")
            optional_json = None

    # If optional fields JSON provided, use it; otherwise prompt
    if optional_json and optional_json.get("research_idea") and optional_json.get("selected_domains"):
        idea = optional_json.get("research_idea")
        domains = optional_json.get("selected_domains")
        logger.info(f"Using research idea from JSON: '{idea}'")
        logger.info(f"Using domains from JSON: {domains}")
    else:
        idea = input("Enter your research idea: ")
        domains = input("Enter domains (comma-separated): ").split(",")
        domains = [d.strip() for d in domains if d.strip()]
        logger.info(f"Manual input - Research idea: '{idea}'")
        logger.info(f"Manual input - Domains: {domains}")

    # Index uploaded paper if provided
    if paper_json:
        added = index_uploaded_paper(paper_json)
        if added:
            print(f"Indexed uploaded paper: {added.get('title')}")

    # Log and display inputs
    print(f"\n{'='*80}")
    print("📥 INPUT CONFIGURATION")
    print(f"{'='*80}")
    print(f"Research Idea: {idea}")
    print(f"Domains: {', '.join(domains)}")
    print(f"Uploaded Paper: {'Yes' if paper_json else 'No'}")
    print(f"{'='*80}\n")
    
    logger.info("="*80)
    logger.info("INPUT CONFIGURATION")
    logger.info("="*80)
    logger.info(f"Research Idea: {idea}")
    logger.info(f"Domains: {domains}")
    logger.info(f"Uploaded Paper: {paper_json is not None}")
    logger.info("="*80)
    
    # Store inputs in metrics
    metrics.log_input('research_idea', idea)
    metrics.log_input('domains', domains)
    metrics.log_input('uploaded_paper', paper_json is not None)
    metrics.save_realtime(metrics_filename)
    
    if not idea or not domains:
        logger.error("Missing required inputs: idea or domains")
        metrics.log_output("success", False)
        metrics.log_error("INPUT_ERROR", "Missing required inputs", "main")
        metrics.save(metrics_filename)
        print("❌ Idea and at least one domain are required.")
        print(f"\n📁 Partial outputs saved to: {session_folder}")
        tee.close()
    else:
        session_start = time.time()
        report = run_analysis(idea, domains)
        session_elapsed = time.time() - session_start
        
        print("\n" + "="*80)
        print("📊 FINAL NOVELTY REPORT")
        print("="*80)
        print(report)
        print("="*80)
        
        # Save final report to dedicated file
        with open(final_report_filename, 'w', encoding='utf-8') as f:
            f.write("# LITERATURE REVIEW REPORT\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            f.write(report)
            f.write("\n\n---\n\n")
            f.write(f"**Session Duration**: {session_elapsed:.2f} seconds\n")
        
        # Copy detailed terminal output to final_report folder
        import shutil
        try:
            shutil.copy2(output_filename, detailed_analysis_filename)
            logger.info(f"Detailed agent analysis copied to: {detailed_analysis_filename}")
        except Exception as e:
            logger.error(f"Error copying detailed analysis: {e}")
        
        logger.info("="*80)
        logger.info("FINAL NOVELTY REPORT")
        logger.info("="*80)
        logger.info(report)
        logger.info("="*80)
        logger.info(f"Final report saved to: {final_report_filename}")
        
        # Finalize metrics
        metrics.log_timing('total_session', session_elapsed)
        metrics.log_output('report_length', len(str(report)))
        metrics.log_output('success', True)
        
        # Save metrics to JSON (finalized)
        metrics_file = metrics.save(metrics_filename, finalize=True)
        
        logger.info("Process completed successfully")
        logger.info(f"Session folder: {session_folder}")
        logger.info(f"All outputs saved")
        
        print("\n" + "="*80)
        print("✅ Research Session Complete")
        print("="*80)
        print(f"📁 Research outputs saved to: {session_folder}")
        print(f"   (Folder will be overwritten on next run)")
        print(f"   📝 review/literature_review.log")
        print(f"   🖥️  terminal_output/terminal_output.txt")
        print(f"   📊 metrics/metrics.json")
        print(f"   🤖 ollama_logs/ollama_api.log  ← Streaming API Calls")
        print(f"   📄 final_report/final_research_report.md  ← Synthesized Report")
        print(f"   📄 final_report/detailed_agent_analysis.txt  ← Detailed Agent Outputs")
        print(f"⏱️  Total time: {session_elapsed:.2f}s")
        print("="*80 + "\n")
    
    # Cleanup - close output file handles
    try:
        if hasattr(sys.stdout, 'close'):
            sys.stdout.close()
        sys.stdout = original_stdout
        sys.stderr = original_stderr
    except Exception as e:
        logger.error(f"Error closing output files: {e}")