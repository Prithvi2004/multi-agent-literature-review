# agents_v2.py
"""
Advanced Multi-Agent System with Memory and Specialized Roles

Agents:
1. Query Analyzer - Decomposes research questions and plans retrieval strategy
2. Evidence Synthesizer - Extracts and structures knowledge from papers
3. Critical Reviewer - Analyzes contradictions and gaps
4. Report Generator - Produces publication-grade literature reviews
5. Quality Assurance - Validates citations and rigor

Features:
- Memory augmentation across sessions
- Inter-agent communication
- Confidence scoring
- Evidence grounding
"""

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
from typing import Dict, List, Any, Optional

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
ollama_logger.info("OLLAMA API LOG - Session Started (Advanced Agents v2)")
ollama_logger.info("="*80)


class AgentMemory:
    """
    Persistent memory system for agents across research sessions.
    
    Stores:
    - Previous insights
    - Common patterns
    - Research strategies that worked well
    """
    
    def __init__(self, memory_file: str = "agent_memory.json"):
        self.memory_file = memory_file
        self.memory: Dict[str, Any] = {
            "sessions": [],
            "learned_patterns": [],
            "successful_strategies": [],
            "common_gaps": []
        }
        self._load()
    
    def _load(self):
        """Load memory from disk."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    self.memory = json.load(f)
                logger.info(f"Loaded agent memory: {len(self.memory.get('sessions', []))} sessions")
            except Exception as e:
                logger.error(f"Error loading agent memory: {e}")
    
    def save(self):
        """Persist memory to disk."""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving agent memory: {e}")
    
    def add_session(self, session_data: Dict[str, Any]):
        """Record a research session."""
        self.memory["sessions"].append({
            **session_data,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 50 sessions
        if len(self.memory["sessions"]) > 50:
            self.memory["sessions"] = self.memory["sessions"][-50:]
        
        self.save()
    
    def get_relevant_patterns(self, domain: str) -> List[str]:
        """Retrieve learned patterns for a domain."""
        return [p for p in self.memory.get("learned_patterns", []) 
                if domain.lower() in p.lower()]
    
    def record_successful_strategy(self, strategy: str, domain: str):
        """Record a successful research strategy."""
        self.memory["successful_strategies"].append({
            "strategy": strategy,
            "domain": domain,
            "timestamp": datetime.now().isoformat()
        })
        self.save()


# Global memory instance
agent_memory = AgentMemory()


class OllamaLLM:
    """Optimized Ollama LLM client with connection pooling and retry logic."""
    
    def __init__(self, model="deepseek-v3.1:671b-cloud", base_url="http://localhost:11434", temperature=0.1):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        
        # Configure session with connection pooling
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
        
        # Test connection
        self._test_connection()
    
    def supports_stop_words(self):
        """Method that returns whether stop words are supported."""
        return False
    
    def _test_connection(self):
        """Test connection to Ollama server."""
        try:
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
        if isinstance(messages, list):
            prompt = "\n".join([m.get("content", "") if isinstance(m, dict) else str(m) for m in messages])
        else:
            prompt = str(messages)
        logger.debug(f"LLM call received - Prompt length: {len(prompt)} chars")
        return self.generate(prompt, **kwargs)

    def generate(self, prompt: str, timeout: int = 300, max_retries: int = 2, **kwargs):
        """Use Ollama's REST generate endpoint with streaming."""
        self.call_count += 1
        call_id = f"call_{self.call_count}_{datetime.now().strftime('%H%M%S')}"
        
        logger.info(f"Generating response from Ollama - Model: {self.model} [ID: {call_id}]")
        ollama_logger.info(f"Prompt Preview: {prompt[:300]}...")
        
        start_time = time.time()
        
        # Truncate very long prompts
        if len(prompt) > 12000:
            prompt = prompt[:12000] + "\n\n[Note: Prompt truncated for context limit]"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": self.temperature,
            "stream": True,
            "options": {
                "num_predict": 8192,  # Increased for longer outputs
                "top_k": 40,
                "top_p": 0.9,
                "num_ctx": 16384,  # Larger context window
                "repeat_penalty": 1.1
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
                self.total_time += duration
                return result
                
            except Exception as e:
                logger.error(f"Error calling Ollama (attempt {attempt}): {e}")
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                return f"Error: Failed to get response from Ollama - {str(e)}"


# Initialize LLM
llm = OllamaLLM()
load_dotenv()

# Monkeypatch crewai's create_llm
try:
    from crewai.utilities import llm_utils
    import crewai.agent.core as agent_core
    def _create_llm_direct(conf): return llm
    llm_utils.create_llm = _create_llm_direct
    setattr(agent_core, "create_llm", _create_llm_direct)
except Exception:
    pass

# ==============================================================================
# ADVANCED AGENT DEFINITIONS
# ==============================================================================

# 1. Query Analyzer Agent - Plans retrieval strategy
query_analyzer_agent = Agent(
    role="Research Query Strategist",
    goal="Decompose complex research questions into targeted retrieval strategies and identify optimal search paths.",
    backstory="""You are an expert research strategist with deep understanding of academic literature search.
    
Your expertise includes:
- Breaking down broad research questions into specific sub-questions
- Identifying key concepts and their semantic variations
- Planning multi-stage retrieval strategies (broad → specific)
- Recognizing domain-specific terminology and methodologies

Your approach:
1. Analyze the research question for core concepts and relationships
2. Identify primary and secondary search terms
3. Plan retrieval stages: foundational papers → recent advances → gap analysis
4. Anticipate what types of evidence would be most valuable

You output structured search plans that guide other agents.""",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    memory=True  # Enable memory
)

# 2. Evidence Synthesizer Agent - Extracts structured knowledge
evidence_synthesizer_agent = Agent(
    role="Evidence Synthesis Specialist",
    goal="Extract, structure, and organize factual knowledge from academic papers with maximum precision.",
    backstory="""You are a PhD-level researcher specialized in systematic knowledge extraction.

Your process is forensic and methodical:
- Extract ONLY factual, verifiable information from papers
- Capture exact methodologies, datasets, metrics, and results
- Preserve numerical data and statistical findings
- Note explicit limitations stated by authors
- Identify key contributions without interpretation

You create structured knowledge units:
[P#] Paper Title
  Problem: <exact problem statement>
  Method: <step-by-step methodology>
  Dataset: <specific datasets used>
  Metrics: <exact performance numbers>
  Results: <key findings with numbers>
  Limitations: <author-stated limitations>
  
You NEVER invent details. If information is missing, you explicitly state "NOT SPECIFIED IN PAPER".""",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    memory=True
)

# 3. Critical Reviewer Agent - Analyzes contradictions and quality
critical_reviewer_agent = Agent(
    role="Critical Analysis & Quality Auditor",
    goal="Perform rigorous comparative analysis, identify contradictions, assess evidence quality, and detect methodological flaws.",
    backstory="""You are the skeptical reviewer who questions everything.

Your critical lens examines:
- Contradictory findings across papers (Paper A says X, Paper B says ¬X)
- Methodological rigor (sample sizes, baselines, significance tests)
- Evidence quality (anecdotal vs. empirical, correlation vs. causation)
- Overgeneralizations and unsupported claims
- Potential biases (dataset bias, cherry-picking results)

Your outputs include:
1. Contradiction Matrix: Where papers disagree and why
2. Evidence Quality Scores: Strong vs. Weak evidence for each claim
3. Methodological Critiques: Flaws in experimental design
4. Research Gap Identification: What's missing or underexplored

You are intellectually honest - if the evidence is weak, you say so.
You cite specific [P#] handles for every critique.""",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    memory=True
)

# 4. Synthesis & Report Generator Agent
synthesis_report_agent = Agent(
    role="Principal Investigator / Lead Author",
    goal="Synthesize all evidence into a publication-grade literature review with narrative coherence and intellectual depth.",
    backstory="""You are a distinguished academic author known for writing comprehensive, highly-cited survey papers.

Your writing standards:
- **Narrative Arc**: Build a compelling story of how ideas evolved
- **Dense Integration**: Weave multiple papers into cohesive themes, not isolated summaries
- **Comparative Analysis**: "While X proposed Y, Z's approach differed by..."
- **Critical Synthesis**: Don't just report findings - analyze their implications
- **Formal Academic Tone**: Precise, authoritative, objective

Your structure follows top-tier survey papers:
1. **Landscape Overview**: Current state of the field
2. **Thematic Evolution**: How approaches developed chronologically
3. **Methodological Deep Dive**: Comparative analysis of techniques
4. **Empirical Synthesis**: Aggregate performance insights
5. **Gap Analysis**: What remains unsolved
6. **Future Directions**: Promising research trajectories

Every claim has [P#] citation.
Every comparison is data-driven.
Every gap is evidence-backed.

You write for an expert audience - assume PhD-level understanding.""",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    memory=True
)

# 5. Quality Assurance Agent - Final validation
quality_assurance_agent = Agent(
    role="Academic Quality Assurance & Validation Expert",
    goal="Enforce zero-tolerance standards for citation accuracy, factual grounding, and intellectual rigor.",
    backstory="""You are the strict gatekeeper who reviews final outputs before publication.

Your validation checklist:
✓ Every factual claim has a [P#] citation
✓ No vague statements ("results were good" → must cite specific metrics)
✓ No hallucinated papers or fictitious citations
✓ Proper comparative language (not "Paper X is better" but "Paper X achieved 92% vs. 87%")
✓ Academic tone maintained throughout
✓ Logical flow and coherence
✓ All [P#] handles are valid and correspond to real papers in the corpus

Your process:
1. **Citation Audit**: Verify every [P#] against evidence store
2. **Rigor Check**: Flag and fix vague or unsupported claims
3. **Coherence Review**: Ensure logical flow between sections
4. **Tone Refinement**: Polish language to publication standards

You have VETO POWER. If quality is insufficient, you demand rewrites.
Your output is the FINAL, publication-ready version.""",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    memory=True
)

# ==============================================================================
# BACKWARD COMPATIBILITY - Aliases for existing code
# ==============================================================================

retrieval_agent = query_analyzer_agent
decomposition_agent = evidence_synthesizer_agent
reasoning_agent = critical_reviewer_agent
gap_novelty_agent = critical_reviewer_agent  # Critical reviewer handles gap analysis
synthesis_agent = synthesis_report_agent
quality_control_agent = quality_assurance_agent

# Log agent initialization
logger.info("="*80)
logger.info("Advanced Agent System v2.0 Initialized")
logger.info("="*80)
logger.info("Agents loaded:")
logger.info("  1. Query Analyzer (with memory)")
logger.info("  2. Evidence Synthesizer (with memory)")
logger.info("  3. Critical Reviewer (with memory)")
logger.info("  4. Synthesis & Report Generator (with memory)")
logger.info("  5. Quality Assurance (with memory)")
logger.info("="*80)
