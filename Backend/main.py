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

# Enable CrewAI tracing
os.environ['CREWAI_TRACING_ENABLED'] = 'true'


class TeeOutput:
    """Capture output to both file and original stream, with ANSI code stripping for file."""
    def __init__(self, file_path, original_stream):
        self.file = open(file_path, 'w', encoding='utf-8')
        self.original = original_stream
        self.buffer = []
        # ANSI escape code pattern
        import re
        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    
    def write(self, data):
        self.original.write(data)
        self.original.flush()
        # Strip ANSI codes for file output
        clean_data = self.ansi_escape.sub('', data)
        self.file.write(clean_data)
        self.file.flush()
    
    def flush(self):
        self.original.flush()
        self.file.flush()
    
    def close(self):
        self.file.close()
from typing import Dict, Any, List

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
        
        # Calculate summary statistics
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
        """Save metrics without finalizing for real-time updates."""
        if filename is None:
            filename = f"metrics_{self.metrics['session_id']}.json"
        
        # Create a copy with current status
        temp_metrics = self.metrics.copy()
        temp_metrics["current_duration_seconds"] = round(time.time() - self.start_time, 2)
        temp_metrics["status"] = "in_progress"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(temp_metrics, f, indent=2, ensure_ascii=False)
        
        return filename

# Global metrics tracker
metrics = MetricsTracker()

# Configure logging and output capture with organized folders
# Use single fixed folder (latest_session) that gets overwritten each run
session_folder = os.path.join('outputs', 'latest_research_session')

# Also keep timestamped backup folder
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_folder = os.path.join('outputs', f'backup_session_{timestamp}')

# Create 4 subfolders for comprehensive research output
review_folder = os.path.join(session_folder, 'review')
terminal_folder = os.path.join(session_folder, 'terminal_output')
metrics_folder = os.path.join(session_folder, 'metrics')
final_report_folder = os.path.join(session_folder, 'final_report')

os.makedirs(review_folder, exist_ok=True)
os.makedirs(terminal_folder, exist_ok=True)
os.makedirs(metrics_folder, exist_ok=True)
os.makedirs(final_report_folder, exist_ok=True)

print(f"\n{'='*80}")
print(f"🚀 Multi-Agent Literature Review System - Research Grade")
print(f"{'='*80}")
print(f"📁 Main Session: {session_folder}")
print(f"   (This folder will be overwritten each run)")
print(f"   📝 review/literature_review.log")
print(f"   🖥️  terminal_output/terminal_output.txt")
print(f"   📊 metrics/metrics.json")
print(f"   📄 final_report/final_research_report.md")
print(f"   📄 final_report/detailed_agent_analysis.txt")
print(f"{'='*80}\n")

# Configure file paths within subfolders
log_filename = os.path.join(review_folder, 'literature_review.log')
output_filename = os.path.join(terminal_folder, 'terminal_output.txt')
metrics_filename = os.path.join(metrics_folder, 'metrics.json')
final_report_filename = os.path.join(final_report_folder, 'final_research_report.md')
detailed_analysis_filename = os.path.join(final_report_folder, 'detailed_agent_analysis.txt')

# Setup logging (file only)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Capture all terminal output to file while keeping console output
original_stdout = sys.stdout
original_stderr = sys.stderr
sys.stdout = TeeOutput(output_filename, original_stdout)
sys.stderr = sys.stdout

logger.info(f"=" * 80)
logger.info(f"Multi-Agent Literature Review System Started")
logger.info(f"Session folder: {session_folder}")
logger.info(f"Review log: {log_filename}")
logger.info(f"Terminal output: {output_filename}")
logger.info(f"Metrics file: {metrics_filename}")
logger.info(f"Final report: {final_report_filename}")
logger.info(f"=" * 80)
print(f"📁 Research Session: {session_folder}")
print(f"   📝 review/literature_review.log")
print(f"   🖥️  terminal_output/terminal_output.txt")
print(f"   📊 metrics/metrics.json")
print(f"   📄 final_report/final_research_report.md")
print(f"📄 Output file: {output_filename}")
print(f"📊 Metrics file: {metrics_filename}")
print(f"{'='*80}\n")

# Rate limiting configuration
API_DELAY = 1.5  # seconds between API calls
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
from agents import (
    controller_agent, retrieval_agent, summarization_agent,
    method_comparison_agent, gap_analysis_agent, novelty_agent
)
from tasks import create_tasks
from tools import rag_tool, rag_tool_instance, citation_verifier_tool
from rag_pipeline import RAGPipeline

# Initialize global RAG
rag_pipeline = RAGPipeline()

def fetch_arxiv_papers(query: str, max_results=5):
    """Fetch papers from arXiv with retry logic and rate limiting."""
    logger.info(f"Fetching papers from arXiv with query: '{query}' (max_results={max_results})")
    start_time = time.time()
    
    for attempt in range(MAX_RETRIES):
        try:
            time.sleep(API_DELAY)  # Rate limiting
            client = arxiv.Client(
                page_size=max_results,
                delay_seconds=3.0,  # Built-in delay between requests
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
                logger.warning(f"arXiv rate limit hit (429). Waiting {wait_time}s before retry {attempt + 1}/{MAX_RETRIES}")
                time.sleep(wait_time)
            else:
                logger.error(f"arXiv HTTP error: {e}")
                metrics.log_api_call("arXiv", query, 0, time.time() - start_time, False, str(e))
                break
        except Exception as e:
            logger.error(f"Unexpected error fetching from arXiv: {e}")
            metrics.log_api_call("arXiv", query, 0, time.time() - start_time, False, str(e))
            metrics.log_error("API_ERROR", str(e), "fetch_arxiv_papers")
            break
    
    logger.warning("Failed to fetch from arXiv after all retries, continuing with other sources")
    metrics.log_api_call("arXiv", query, 0, time.time() - start_time, False, "Max retries exceeded")
    return []

def fetch_semantic_scholar_papers(query: str, max_results=5):
    """Fetch papers from Semantic Scholar with retry logic."""
    start_time = time.time()
    logger.info(f"Fetching papers from Semantic Scholar with query: '{query}' (max_results={max_results})")
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {"query": query, "limit": max_results, "fields": "title,authors,year,abstract,url"}
    start_time = time.time()
    
    for attempt in range(MAX_RETRIES):
        try:
            time.sleep(API_DELAY)  # Rate limiting
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
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                wait_time = RETRY_DELAY * (attempt + 1)
                logger.warning(f"Semantic Scholar rate limit hit. Waiting {wait_time}s before retry {attempt + 1}/{MAX_RETRIES}")
                time.sleep(wait_time)
            else:
                logger.error(f"Semantic Scholar HTTP error: {e}")
                metrics.log_api_call("Semantic Scholar", query, 0, time.time() - start_time, False, str(e))
                break
        except Exception as e:
            logger.error(f"Error fetching from Semantic Scholar: {e}")
            metrics.log_api_call("Semantic Scholar", query, 0, time.time() - start_time, False, str(e))
            metrics.log_error("API_ERROR", str(e), "fetch_semantic_scholar_papers")
            break
    
    logger.warning("Failed to fetch from Semantic Scholar, continuing with other sources")
    metrics.log_api_call("Semantic Scholar", query, 0, time.time() - start_time, False, "Max retries exceeded")
    return []

def fetch_pubmed_papers(query: str, max_results=5):
    """Fetch papers from PubMed with retry logic."""
    start_time = time.time()
    logger.info(f"Fetching papers from PubMed with query: '{query}' (max_results={max_results})")
    esearch = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"}
    start_time = time.time()
    
    for attempt in range(MAX_RETRIES):
        try:
            time.sleep(API_DELAY)  # Rate limiting for NCBI
            res = requests.get(esearch, params=params, timeout=15)
            res.raise_for_status()
            ids = res.json().get("esearchresult", {}).get("idlist", [])
            if not ids:
                logger.info("No PubMed IDs found for query")
                metrics.log_api_call("PubMed", query, 0, time.time() - start_time, True)
                return []
            
            time.sleep(API_DELAY)  # Additional delay before fetching details
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
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                wait_time = RETRY_DELAY * (attempt + 1)
                logger.warning(f"PubMed rate limit hit. Waiting {wait_time}s before retry {attempt + 1}/{MAX_RETRIES}")
                time.sleep(wait_time)
            else:
                logger.error(f"PubMed HTTP error: {e}")
                metrics.log_api_call("PubMed", query, 0, time.time() - start_time, False, str(e))
                break
        except Exception as e:
            logger.error(f"Error fetching from PubMed: {e}")
            metrics.log_api_call("PubMed", query, 0, time.time() - start_time, False, str(e))
            metrics.log_error("API_ERROR", str(e), "fetch_pubmed_papers")
            break
    
    logger.warning("Failed to fetch from PubMed, continuing with other sources")
    metrics.log_api_call("PubMed", query, 0, time.time() - start_time, False, "Max retries exceeded")
    return []

def retrieve_and_index_papers(user_idea: str, domains: list):
    """Retrieve papers from multiple sources in parallel for efficiency."""
    start_time = time.time()
    query = f"{user_idea} {' '.join(domains)}"
    logger.info(f"Starting paper retrieval for idea: '{user_idea}'")
    logger.info(f"Domains: {domains}")
    logger.info(f"Combined query: '{query}'")
    print("🔍 Retrieving papers from arXiv, Semantic Scholar, PubMed in parallel...")
    
    retrieval_start = time.time()
    papers = []
    
    # Parallel fetching for improved performance
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(fetch_arxiv_papers, query, 4): "arXiv",
            executor.submit(fetch_semantic_scholar_papers, query, 3): "Semantic Scholar",
            executor.submit(fetch_pubmed_papers, query, 3): "PubMed"
        }
        
        for future in as_completed(futures):
            source = futures[future]
            try:
                result = future.result(timeout=30)
                papers.extend(result)
                logger.info(f"Successfully fetched {len(result)} papers from {source}")
            except Exception as e:
                logger.error(f"Exception fetching from {source}: {e}")
    
    # Deduplicate by title
    logger.info(f"Total papers fetched: {len(papers)}")
    seen = set()
    unique_papers = []
    for p in papers:
        if p["title"] not in seen:
            seen.add(p["title"])
            unique_papers.append(p)
    
    logger.info(f"Unique papers after deduplication: {len(unique_papers)}")
    
    if not unique_papers:
        logger.warning("No papers retrieved from any source!")
        return []
    
    # Index into RAG with full metadata
    top_papers = unique_papers[:10]
    logger.info(f"Indexing top {len(top_papers)} papers into RAG pipeline")
    for idx, paper in enumerate(top_papers, 1):
        logger.info(f"  [{idx}] {paper['title']} ({paper['year']}, {paper['source']})")
    rag_pipeline.add_papers(top_papers)
    rag_pipeline.save()
    logger.info("RAG pipeline saved successfully")
    
    retrieval_duration = time.time() - retrieval_start
    metrics.log_timing("paper_retrieval_and_indexing", retrieval_duration)
    print(f"✅ Retrieved and indexed {len(top_papers)} papers in {retrieval_duration:.2f}s")
    return top_papers


def index_uploaded_paper(paper_data: dict):
    """Index a user-uploaded paper payload of the form:
    {"paper_sections":[{"field":"Title","content":"..."},...], "uploaded_papers": [...]}
    We extract Title and Abstract when present and add to the RAG index.
    """
    logger.info("Processing uploaded paper data")
    title = None
    abstract = None
    for sec in paper_data.get("paper_sections", []):
        if sec.get("field", "").lower() == "title":
            title = sec.get("content")
        if sec.get("field", "").lower() == "abstract":
            abstract = sec.get("content")

    if not title and paper_data.get("uploaded_papers"):
        # If uploaded_papers contains dicts with title/abstract, use first
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
        logger.info(f"Indexing uploaded paper: '{title}'")
        rag_pipeline.add_papers([paper])
        rag_pipeline.save()
        logger.info("Uploaded paper indexed successfully")
        return paper
    logger.warning("No valid title found in uploaded paper data")
    return None

def run_analysis(user_idea: str, selected_domains: list):
    logger.info(f"="*80)
    logger.info(f"STARTING ANALYSIS")
    logger.info(f"Research Idea: {user_idea}")
    logger.info(f"Selected Domains: {selected_domains}")
    logger.info(f"="*80)
    
    # Log inputs to metrics
    metrics.log_input("research_idea", user_idea)
    metrics.log_input("selected_domains", selected_domains)
    
    analysis_start = time.time()
    
    # 1. Retrieve and index papers
    papers = retrieve_and_index_papers(user_idea, selected_domains)
    if not papers:
        logger.error("No relevant papers found")
        metrics.log_output("result", "No relevant papers found")
        metrics.log_output("success", False)
        return "❌ No relevant papers found."

    # 2. Inject RAG into tools (RAGSearch + CitationVerifier)
    logger.info("Injecting RAG pipeline into tools")
    from tools import rag_tool
    rag_tool.rag = rag_pipeline

    # 3. Assign tools to agents so all reasoning is RAG-first
    logger.info("Assigning RAG tools to agents")
    retrieval_agent.tools = [rag_tool_instance]
    summarization_agent.tools = [rag_tool_instance]
    method_comparison_agent.tools = [rag_tool_instance]
    gap_analysis_agent.tools = [rag_tool_instance]
    novelty_agent.tools = [rag_tool_instance, citation_verifier_tool]
    logger.info("Tools assigned to all agents")

    # 4. Create tasks
    logger.info("Creating tasks for crew")
    tasks = create_tasks(user_idea, selected_domains)
    logger.info(f"Created {len(tasks)} tasks")

    # 5. Run crew end-to-end
    logger.info("Initializing crew with 6 agents")
    crew = Crew(
        agents=[
            controller_agent,
            retrieval_agent,
            summarization_agent,
            method_comparison_agent,
            gap_analysis_agent,
            novelty_agent
        ],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
        tracing=True
    )

    logger.info("Starting crew execution (sequential process)...")
    crew_start = time.time()
    result = crew.kickoff()
    crew_duration = time.time() - crew_start
    
    logger.info(f"Crew execution completed in {crew_duration:.2f}s")
    logger.info(f"="*80)
    logger.info(f"FINAL RESULT")
    logger.info(f"="*80)
    logger.info(str(result))
    
    # Log outputs to metrics
    analysis_duration = time.time() - analysis_start
    metrics.log_timing("total_analysis", analysis_duration)
    metrics.log_timing("crew_execution", crew_duration)
    metrics.log_output("final_report", str(result)[:1000])  # First 1000 chars
    metrics.log_output("final_report_length", len(str(result)))
    metrics.save_realtime(metrics_filename)
    metrics.log_output("papers_analyzed", len(papers))
    metrics.log_output("success", True)
    
    print(f"\n✅ Analysis completed in {analysis_duration:.2f}s")
    return str(result)

# CLI Entry supporting JSON inputs for paper data and optional fields
if __name__ == "__main__":
    logger.info("Starting CLI interface")
    print("Paste PAPER DATA JSON (or press Enter to skip):")
    paper_json = []
    try:
        line = input().strip()
        if line:
            # allow multi-line JSON paste until a blank line
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
    except Exception as e:
        logger.error(f"Invalid PAPER DATA JSON: {e}")
        print("Invalid PAPER DATA JSON, skipping uploaded papers.")
        paper_json = None

    print("Paste OPTIONAL FIELDS DATA JSON (or press Enter to type manually):")
    optional_json = None
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