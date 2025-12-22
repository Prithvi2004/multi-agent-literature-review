# main.py
import os
import arxiv
import requests
from bs4 import BeautifulSoup
from crewai import Crew, Process
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
    client = arxiv.Client()
    search = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance)
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
    return papers

def fetch_semantic_scholar_papers(query: str, max_results=5):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {"query": query, "limit": max_results, "fields": "title,authors,year,abstract,url"}
    try:
        res = requests.get(url, params=params, timeout=10)
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
        return papers
    except:
        return []

def fetch_pubmed_papers(query: str, max_results=5):
    esearch = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"}
    try:
        res = requests.get(esearch, params=params, timeout=10)
        ids = res.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []
        efetch = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        fetch_res = requests.get(efetch, params={"db": "pubmed", "id": ",".join(ids), "retmode": "xml"})
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
        return papers
    except:
        return []

def retrieve_and_index_papers(user_idea: str, domains: list):
    query = f"{user_idea} {' '.join(domains)}"
    print("🔍 Retrieving papers from arXiv, Semantic Scholar, PubMed...")
    
    papers = []
    papers.extend(fetch_arxiv_papers(query, 4))
    papers.extend(fetch_semantic_scholar_papers(query, 3))
    papers.extend(fetch_pubmed_papers(query, 3))
    
    # Deduplicate by title
    seen = set()
    unique_papers = []
    for p in papers:
        if p["title"] not in seen:
            seen.add(p["title"])
            unique_papers.append(p)
    
    # Index into RAG
    for p in unique_papers[:10]:
        content = p.get("abstract", "") or p.get("title", "")
        rag_pipeline.add_paper(p["title"], content, p["source"])
    
    rag_pipeline.save()
    return unique_papers[:10]

def run_analysis(user_idea: str, selected_domains: list):
    # 1. Retrieve and index papers
    papers = retrieve_and_index_papers(user_idea, selected_domains)
    if not papers:
        return "❌ No relevant papers found."

    # 2. Inject RAG into tools
    from tools import rag_tool
    rag_tool.rag = rag_pipeline

    # 3. Assign tools to agents
    novelty_agent.tools = [rag_tool_instance, citation_verifier_tool]
    gap_analysis_agent.tools = [rag_tool_instance]

    # 4. Create tasks
    tasks = create_tasks(user_idea, selected_domains)

    # 5. Run crew
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
        verbose=2
    )

    result = crew.kickoff()
    return str(result)

# CLI Entry
if __name__ == "__main__":
    idea = input("Enter your research idea: ")
    domains = input("Enter domains (comma-separated): ").split(",")
    domains = [d.strip() for d in domains if d.strip()]
    
    if not idea or not domains:
        print("❌ Idea and at least one domain are required.")
    else:
        report = run_analysis(idea, domains)
        print("\n" + "="*80)
        print("FINAL NOVELTY REPORT")
        print("="*80)
        print(report)