# agents.py
from crewai import Agent, LLM
import requests
import logging
import time
import json
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
import os


logger = logging.getLogger(__name__)

# Setup dedicated Ollama log file
ollama_log_folder = os.path.join('outputs', 'latest_research_session', 'ollama_logs')
os.makedirs(ollama_log_folder, exist_ok=True)
ollama_log_file = os.path.join(ollama_log_folder, 'ollama_api.log')

# Create Ollama-specific logger
ollama_logger = logging.getLogger('ollama_api')
ollama_logger.setLevel(logging.INFO)
ollama_handler = logging.FileHandler(ollama_log_file, mode='w', encoding='utf-8')
ollama_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
ollama_logger.addHandler(ollama_handler)
ollama_logger.info("="*80)
ollama_logger.info("OLLAMA API LOG - Session Started")
ollama_logger.info("="*80)

class OllamaLLM:
    """Optimized Ollama LLM client with connection pooling and retry logic."""
    
    def __init__(self, model="qwen3-vl:235b-cloud", base_url="http://localhost:11434", temperature=0.1): # Lower temp for rigor
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        
        # Configure session with connection pooling and retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        logger.info(f"OllamaLLM initialized - Model: {model}, Base URL: {base_url}, Temp: {temperature}")
        ollama_logger.info(f"OllamaLLM initialized - Model: {model}, Base URL: {base_url}, Temp: {temperature}")
        self.call_count = 0
        self.total_tokens = 0
        self.total_time = 0
        
        # Test connection to Ollama
        self._test_connection()
    
    def supports_stop_words(self):
        """Method that returns whether stop words are supported."""
        return False
    
    def _test_connection(self):
        """Test connection to Ollama server."""
        try:
            # Try to list models or check if server is accessible
            test_resp = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            if test_resp.status_code == 200:
                logger.info(f"✓ Ollama server connection successful at {self.base_url}")
                ollama_logger.info(f"✓ Ollama server connection test: SUCCESS")
                return True
            else:
                logger.warning(f"⚠ Ollama server responded with status {test_resp.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot connect to Ollama at {self.base_url}: {e}")
            return False

    def call(self, messages, **kwargs):
        """CrewAI expects a call method that accepts messages and returns response text."""
        # Convert messages to a single prompt string
        if isinstance(messages, list):
            prompt = "\n".join([m.get("content", "") if isinstance(m, dict) else str(m) for m in messages])
        else:
            prompt = str(messages)
        logger.debug(f"LLM call received - Prompt length: {len(prompt)} chars")
        return self.generate(prompt, **kwargs)

    def generate(self, prompt: str, timeout: int = 240, max_retries: int = 2, **kwargs):
        """Use Ollama's REST generate endpoint with streaming enabled."""
        self.call_count += 1
        call_id = f"call_{self.call_count}_{datetime.now().strftime('%H%M%S')}"
        
        logger.info(f"Generating response from Ollama - Model: {self.model} [ID: {call_id}]")
        ollama_logger.info(f"Prompt Preview: {prompt[:300]}...")
        
        start_time = time.time()
        
        # Truncate very long prompts
        if len(prompt) > 8000:
            prompt = prompt[:8000] + "\n\n[Note: Prompt truncated for context limit]"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": self.temperature,
            "stream": True,
            "options": {
                "num_predict": 4096,
                "top_k": 40,
                "top_p": 0.9,
                "num_ctx": 8192
            }
        }
        
        for attempt in range(max_retries + 1):
            try:
                resp = self.session.post(
                    f"{self.base_url}/api/generate", 
                    json=payload, 
                    stream=True, 
                    timeout=timeout
                )
                resp.raise_for_status()
                
                result = ""
                for line in resp.iter_lines(decode_unicode=True):
                    if not line: continue
                    chunk = json.loads(line)
                    if 'response' in chunk: result += chunk['response']
                
                duration = time.time() - start_time
                ollama_logger.info(f"Response ({len(result)} chars) in {duration:.2f}s")
                return result
                
            except Exception as e:
                logger.error(f"Error calling Ollama (attempt {attempt}): {e}")
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                return f"Error: Failed to get response from Ollama - {str(e)}"

# Direct Ollama LLM instantiation
llm = OllamaLLM()
load_dotenv()

# Monkeypatch crewai's create_llm to always return our Ollama client
try:
    from crewai.utilities import llm_utils
    import crewai.agent.core as agent_core
    def _create_llm_direct(conf): return llm
    llm_utils.create_llm = _create_llm_direct
    setattr(agent_core, "create_llm", _create_llm_direct)
except Exception:
    pass

# ==============================================================================
#  AGENTS DEFINITION
# ==============================================================================

# 1. Retrieval Architect Agent
retrieval_agent = Agent(
    role="Retrieval Architect",
    goal="Design and execute advanced RAG retrieval pipelines to build a high-quality paper corpus.",
    backstory="""You are a senior information retrieval specialist. 
Your job is to strategically find the most impactful and relevant literature for the user's research topic.
You do not just keyword search; you perform semantic discovery, filter for seminal works versus recent advances, 
and ensure the retrieved corpus is diverse enough to support a PhD-level review.""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# 2. Literature Decomposition Agent
decomposition_agent = Agent(
    role="Literature Decomposition Specialist",
    goal="Break down complex academic papers into atomic knowledge units (problems, methods, findings, limitations).",
    backstory="""You are an expert at dissecting academic texts. 
You strip away fluff and extract hard facts. 
For every paper, you isolate:
- The exact core problem addressed
- The specific hypothesis
- The methodology (including algorithms and datasets)
- The raw results/metrics
- Explicit claims and assumptions
- Authors' stated limitations
You ensure no detail is hallucinated; if it's not in the text, you report it as missing.""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# 3. Cross-Paper Reasoning Agent
reasoning_agent = Agent(
    role="Cross-Paper Reasoning Analyst",
    goal="Synthesize comparative insights across multiple papers, identifying conflicts, agreements, and evolution.",
    backstory="""You are a comparative theorist. You never look at one paper in isolation.
You look at the CORPUS as a graph of ideas.
Your tasks:
- Compare Method A vs Method B across papers.
- Identify contradictory findings (e.g., Paper X says A is better, Paper Y says B is better).
- Trace the evolution of a concept over time.
- Detect when different authors use different terms for the same concept.
Your output must be structurally dense comparative analysis.""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# 4. Research Gap & Novelty Agent
gap_novelty_agent = Agent(
    role="Research Gap & Novelty Auditor",
    goal="Identify clear, evidence-backed research gaps and assess the novelty of the proposed idea.",
    backstory="""You are the critic who identifies what is MISSING.
Based on the comparative analysis, where are the holes?
- Underexplored problems?
- Biased datasets?
- Assumptions that have never been tested?
- Contradictions that remain unresolved?
You also evaluate the user's proposed contribution: is it truly novel or just incremental? 
You demand evidence for every claim of a "gap".""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# 5. Synthesis & Writing Agent
synthesis_agent = Agent(
    role="Principal Investigator / Lead Author",
    goal="Write a publication-grade literature review that synthesizes all insights into a coherent narrative.",
    backstory="""You are the lead author of a top-tier survey paper (e.g., ACM Computing Surveys, Nature Reviews).
You take the atomic facts, comparative matrices, and gap analysis, and weave them into a COMPLELLING NARRATIVE.
- No listicles.
- No "Paper A did X, Paper B did Y".
- Instead: "While Paper A approached X using Y, Paper B challenged this by..."
- You ensure formal academic tone, precise terminology, and perfect flow.
- You integrate citations naturally [P#].""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# 6. Quality Control & Precision Agent
quality_control_agent = Agent(
    role="Academic Reviewer / Editor",
    goal="Enforce strict academic rigor, zero hallucination, and high intellectual density.",
    backstory="""You are the 'Reviewer #2' - the strict gatekeeper.
You review the final draft.
Your rules:
1. Every claim must have a citation [P#].
2. No vague statements (e.g., "results were good"). Demand numbers.
3. No surface-level analysis.
4. If a section is weak, you flag it or rewrite it to be denser.
5. You ensure the tone is professional, objective, and authoritative.
You reject anything that looks like a generic AI summary.""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)
