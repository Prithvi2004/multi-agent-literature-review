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
    
    def __init__(self, model="qwen3-vl:235b-cloud", base_url="http://localhost:11434", temperature=0.2):
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
                data = test_resp.json()
                models = data.get('models', [])
                if models:
                    model_names = [m.get('name', 'unknown') for m in models[:5]]
                    ollama_logger.info(f"  Available models: {', '.join(model_names)}")
                return True
            else:
                logger.warning(f"⚠ Ollama server responded with status {test_resp.status_code}")
                ollama_logger.warning(f"⚠ Connection test returned status {test_resp.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot connect to Ollama at {self.base_url}: {e}")
            ollama_logger.error(f"❌ Connection test FAILED: {e}")
            ollama_logger.error(f"   Make sure Ollama is running: ollama serve")
            print(f"\n⚠️  WARNING: Cannot connect to Ollama at {self.base_url}")
            print(f"   Error: {e}")
            print(f"   Please ensure Ollama is running: ollama serve\n")
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

    def generate(self, prompt: str, timeout: int = 180, max_retries: int = 2, **kwargs):
        """Use Ollama's REST generate endpoint with streaming enabled."""
        self.call_count += 1
        call_id = f"call_{self.call_count}_{datetime.now().strftime('%H%M%S')}"
        
        logger.info(f"Generating response from Ollama - Model: {self.model} [ID: {call_id}]")
        ollama_logger.info(f"\n{'='*80}")
        ollama_logger.info(f"OLLAMA API CALL #{self.call_count} - ID: {call_id}")
        ollama_logger.info(f"{'='*80}")
        
        start_time = time.time()
        prompt_length = len(prompt)
        
        ollama_logger.info(f"Model: {self.model}")
        ollama_logger.info(f"Temperature: {self.temperature}")
        ollama_logger.info(f"Prompt Length: {prompt_length} chars")
        ollama_logger.info(f"Prompt Preview: {prompt[:200]}...")
        
        # Truncate very long prompts to prevent timeouts
        if prompt_length > 4000:
            logger.warning(f"Prompt too long ({prompt_length} chars), truncating to 4000")
            ollama_logger.warning(f"Prompt too long ({prompt_length} chars), truncating to 4000")
            prompt = prompt[:4000] + "\n\n[Note: Prompt truncated for efficiency]"
            prompt_length = len(prompt)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": self.temperature,
            "stream": True,  # Enable streaming
            "options": {
                "num_predict": 1000,  # Reduced from 2000 for faster responses
                "top_k": 40,
                "top_p": 0.9,
                "num_ctx": 4096  # Context window
            }
        }
        
        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Sending request to {self.base_url}/api/generate (attempt {attempt + 1}/{max_retries + 1})")
                ollama_logger.info(f"Sending streaming request (attempt {attempt + 1}/{max_retries + 1})")
                
                resp = self.session.post(
                    f"{self.base_url}/api/generate", 
                    json=payload, 
                    stream=True,  # Enable streaming response
                    timeout=timeout,
                    headers={"Content-Type": "application/json"}
                )
                resp.raise_for_status()
                
                # Parse streaming response
                result = ""
                final_metadata = None
                chunk_count = 0
                
                ollama_logger.info("Streaming response started...")
                try:
                    for line in resp.iter_lines(decode_unicode=True):
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            chunk_count += 1
                            
                            # Check for error in chunk
                            if 'error' in chunk:
                                error_msg = f"Ollama returned error: {chunk['error']}"
                                logger.error(error_msg)
                                ollama_logger.error(error_msg)
                                raise ValueError(error_msg)
                            
                            response_part = chunk.get('response', '')
                            if response_part:
                                result += response_part
                            
                            if chunk.get('done'):
                                final_metadata = chunk
                                break
                        except json.JSONDecodeError as je:
                            ollama_logger.warning(f"Failed to parse chunk: {line[:100]}")
                            continue
                    
                    ollama_logger.info(f"Received {chunk_count} chunks")
                except Exception as stream_err:
                    logger.error(f"Error during streaming: {stream_err}")
                    ollama_logger.error(f"Error during streaming: {stream_err}")
                    raise
                
                duration = time.time() - start_time
                response_length = len(result)
                
                logger.info(f"Response received - Length: {response_length} chars in {duration:.2f}s")
                ollama_logger.info(f"Response completed - Length: {response_length} chars in {duration:.2f}s")
                ollama_logger.info(f"Response Preview: {result[:200]}...")
                
                # Log metadata if available
                if final_metadata:
                    ollama_logger.info(f"\nMetadata:")
                    ollama_logger.info(f"  Model: {final_metadata.get('model')}")
                    ollama_logger.info(f"  Done Reason: {final_metadata.get('done_reason')}")
                    ollama_logger.info(f"  Prompt Eval Count: {final_metadata.get('prompt_eval_count')}")
                    ollama_logger.info(f"  Eval Count: {final_metadata.get('eval_count')}")
                    
                    # Convert nanoseconds to seconds for durations
                    def ns_to_s(ns):
                        return f"{(ns/1e9):.3f}s" if isinstance(ns, (int, float)) else "N/A"
                    
                    ollama_logger.info(f"  Total Duration: {ns_to_s(final_metadata.get('total_duration'))}")
                    ollama_logger.info(f"  Load Duration: {ns_to_s(final_metadata.get('load_duration'))}")
                    ollama_logger.info(f"  Prompt Eval Duration: {ns_to_s(final_metadata.get('prompt_eval_duration'))}")
                    ollama_logger.info(f"  Eval Duration: {ns_to_s(final_metadata.get('eval_duration'))}")
                    
                    # Update stats
                    prompt_tokens = final_metadata.get('prompt_eval_count', 0)
                    response_tokens = final_metadata.get('eval_count', 0)
                    self.total_tokens += (prompt_tokens + response_tokens)
                    ollama_logger.info(f"  Total Tokens (this call): {prompt_tokens + response_tokens}")
                    ollama_logger.info(f"  Cumulative Tokens (session): {self.total_tokens}")
                
                self.total_time += duration
                ollama_logger.info(f"  Cumulative Time (session): {self.total_time:.2f}s")
                ollama_logger.info(f"{'='*80}")
                
                # Validate response is not empty
                if not result or len(result.strip()) == 0:
                    error_msg = "[OLLAMA_ERROR] Empty response received from model"
                    logger.error(error_msg)
                    ollama_logger.error(error_msg)
                    
                    # Try one more time if we have retries left
                    if attempt < max_retries:
                        logger.warning("Empty response, retrying...")
                        ollama_logger.warning("Empty response, retrying...")
                        time.sleep(2)
                        continue
                    else:
                        # Return a fallback response instead of empty string
                        fallback = "I apologize, but I was unable to generate a proper response. Please try rephrasing your query or check if the Ollama service is running correctly."
                        logger.warning(f"Returning fallback response after empty result")
                        ollama_logger.warning(f"Returning fallback response")
                        return fallback
                
                # Log to metrics if available
                try:
                    from main import metrics
                    metrics.log_llm_call(self.model, prompt_length, response_length, duration, True)
                except:
                    pass
                
                return result
            except requests.exceptions.Timeout as e:
                duration = time.time() - start_time
                if attempt < max_retries:
                    logger.warning(f"Timeout after {duration:.2f}s, retrying... ({attempt + 1}/{max_retries})")
                    ollama_logger.warning(f"Timeout after {duration:.2f}s, retrying... ({attempt + 1}/{max_retries})")
                    time.sleep(2)
                    continue
                else:
                    error_msg = f"[OLLAMA_TIMEOUT] Max retries exceeded after {duration:.2f}s"
                    logger.error(error_msg)
                    ollama_logger.error(error_msg)
                    ollama_logger.error(f"{'='*80}")
                    try:
                        from main import metrics
                        metrics.log_llm_call(self.model, prompt_length, 0, duration, False)
                        metrics.log_error("TIMEOUT_ERROR", error_msg, "OllamaLLM.generate")
                    except:
                        pass
                    return f"Error: LLM timeout after {duration:.2f}s. Please try with a smaller query or simpler task."
            except Exception as e:
                error_msg = f"[OLLAMA_ERROR] {e}"
                duration = time.time() - start_time
                logger.error(error_msg)
                ollama_logger.error(error_msg)
                ollama_logger.error(f"{'='*80}")
                
                # Log error to metrics if available
                try:
                    from main import metrics
                    metrics.log_llm_call(self.model, prompt_length, 0, duration, False)
                    metrics.log_error("LLM_ERROR", str(e), "OllamaLLM.generate")
                except:
                    pass
                
                # Retry if we have attempts left
                if attempt < max_retries:
                    logger.warning(f"Error occurred, retrying... ({attempt + 1}/{max_retries})")
                    ollama_logger.warning(f"Error occurred, retrying... ({attempt + 1}/{max_retries})")
                    time.sleep(2)
                    continue
                else:
                    # Return meaningful error message
                    return f"Error: Failed to get response from Ollama - {str(e)}. Please check if Ollama is running at {self.base_url}"

# Direct Ollama LLM instantiation (no LiteLLM fallback)
llm = OllamaLLM()
# 1bb77bd79e6143daac348ab4d5fd402b.9Yu0iDLZ3QxDvVDlNPMZrclz

# Load environment variables
load_dotenv()

# # Initialize LLM
# llm = LLM(
#     model="gemini/gemini-2.5-flash",
#     verbose=True,
#     temperature=0.5,
#     api_key=os.getenv("GEMINI_API_KEY") or "AIzaSyBD3x7NuOgEUzD_0COroFvyT_p2yNrJyUc" # Use environment variable for security
# )


# Monkeypatch crewai's create_llm to always return our Ollama client
try:
    from crewai.utilities import llm_utils
    import crewai.agent.core as agent_core

    def _create_llm_direct(conf):
        """Always return our direct Ollama client."""
        return llm

    llm_utils.create_llm = _create_llm_direct
    setattr(agent_core, "create_llm", _create_llm_direct)
except Exception:
    pass

# ----------------------------
# 1. Report Synthesis Agent (Controller)
# ----------------------------
controller_agent = Agent(
    role="Literature Review Synthesizer",
    goal="Synthesize all agent outputs into a comprehensive, research-grade literature review with deep insights and proper academic structure.",
    backstory="""
You are a senior research synthesizer with expertise in creating publication-quality literature reviews.
ALL research work is already complete by other agents. Your job is to combine their outputs into one coherent, research-grade report.

YOU WILL RECEIVE:
1. Retrieved papers list from Paper Retrieval Agent
2. Paper summaries from Research Summarizer
3. Method comparison from Methodology Analyst
4. Research gaps from Research Gap Detective
5. Novelty assessment from Novelty Evaluator

YOUR OUTPUT FORMAT (RESEARCH-GRADE):
---
**COMPREHENSIVE LITERATURE REVIEW REPORT**

**Research Context**: [user's idea]
**Research Domains**: [domains]
**Total Papers Analyzed**: [count]

**EXECUTIVE SUMMARY** (150-200 words)
[Synthesize key findings, major trends, critical gaps, and novelty assessment in a coherent narrative]

**1. RETRIEVED PAPERS CORPUS**
[List ALL papers with proper citations: [P#] Author et al. (Year). Title. Source]
- Group by research theme/methodology if applicable
- Highlight seminal works vs recent advances

**2. DETAILED LITERATURE ANALYSIS**
[For each major paper/theme, provide:]
- **Research Problem Addressed**: [specific problem]
- **Methodology**: [detailed approach with algorithms/frameworks]
- **Key Findings**: [quantitative results with metrics when available]
- **Limitations**: [acknowledged weaknesses]
- **Citation**: [P#]

**3. COMPARATIVE METHODOLOGY ANALYSIS**
[Create structured comparison:]
- **Common Approaches**: [frameworks, algorithms, datasets used across papers]
- **Methodological Variations**: [how different papers approach similar problems]
- **Performance Benchmarks**: [if available, compare reported metrics]
- **Dataset Analysis**: [common datasets, sizes, domains]
- **Evaluation Metrics**: [how success is measured across studies]

**4. IDENTIFIED RESEARCH GAPS** (Evidence-Based)
[For each gap:]
- **Gap #X**: [specific gap description]
  - **Importance**: [High/Medium/Low with justification]
  - **Supporting Evidence**: [cite papers [P#] that reveal this gap]
  - **Potential Impact**: [why addressing this matters]
  - **Feasibility**: [challenges in addressing this gap]

**5. NOVELTY ASSESSMENT** (Comprehensive)
- **Novelty Score**: X/100
- **Detailed Reasoning**:
  - [Why this score? Compare against existing work point-by-point]
  - [What specifically is novel vs. incremental?]
- **Closest Existing Work**: [cite specific papers [P#] and explain overlap]
- **Differentiation Points**: [what makes this research unique]
- **Recommendation**: [Highly Novel / Moderately Novel / Incremental / Not Novel]
- **Strategic Advice**: [how to position this research for maximum impact]

**6. SYNTHESIS & RECOMMENDATIONS**
[Provide integrated insights:]
- **Major Trends in Field**: [emerging patterns across papers]
- **Theoretical Contributions**: [conceptual advances]
- **Practical Applications**: [real-world implications]
- **Future Research Directions**: [specific, actionable suggestions]
- **Recommended Reading Order**: [for someone new to this topic]

**7. CRITICAL LIMITATIONS & UNCERTAINTIES**
- **Evidence Quality**: [assess reliability of findings]
- **Coverage Gaps**: [what domains/papers may be missing]
- **Contradictory Findings**: [if any papers disagree]
- **Temporal Limitations**: [how recent is this analysis]
---

IMPORTANT QUALITY STANDARDS:
- Use REAL citations from provided papers (not placeholders like [Author A])
- Provide SPECIFIC evidence (metrics, datasets, algorithms) not generic statements
- Compare papers QUANTITATIVELY when data available
- Identify PRECISE gaps with supporting evidence
- Write in ACADEMIC tone suitable for research publication
- DO NOT ask for user input or start new work - ONLY synthesize provided outputs
- Ensure ALL sections have substantive content (no "TBD" or placeholders)
""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)
# ----------------------------
# 2. Paper Retrieval Agent
# ----------------------------
retrieval_agent = Agent(
    role="Paper Retrieval Specialist",
    goal="Find the most relevant academic papers from arXiv, Semantic Scholar, and PubMed based on user’s research idea and fields.",
    backstory="""
You are an expert in academic paper retrieval. You use semantic search and keyword expansion to find papers that match the user’s research idea.

**INPUT**: User’s research idea + selected fields

**OUTPUT FORMAT** (from RAG Search results):
- [P#] [PAPER TITLE] | [AUTHORS] | [YEAR] | [SOURCE]
- Abstract: [First 2 sentences from RAG result]
- Relevance: [Brief justification based on query match]

**RULES**:
- Use RAG Search tool FIRST before any analysis
- Prioritize recent papers (last 5 years)
- Return max 10 papers with valid [P#] handles
- If no papers match, state clearly: INSUFFICIENT_EVIDENCE
""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# ----------------------------
# 3. Summarization Agent
# ----------------------------
summarization_agent = Agent(
    role="Research Summarizer",
    goal="Extract key insights from papers using RAG tool.",
    backstory="""You are a research analyst specializing in deep paper analysis.
For each paper, extract detailed information suitable for comparative research.

**OUTPUT PER PAPER**:
---
**[P#] Title**: [Exact paper title]
**Authors and Year**: [Author et al., YEAR]
**Source**: [Journal/Conference/arXiv]

**Research Problem**: [What specific problem? 2-3 sentences]

**Methodology**:
- **Approach**: [Algorithm/Framework/Method name]
- **Architecture**: [Technical details if provided]
- **Datasets Used**: [Name, size, domain]
- **Baselines**: [What they compared against]

**Key Results**:
- [Specific metrics with values]
- [Main findings with quantitative support]

**Contributions**:
1. [Novel aspect]
2. [Novel aspect]

**Limitations**:
- [Technical limitations]
- [Scope limitations]

**Relevance to Research Idea**: [Why this paper matters]
---

**ANALYSIS REQUIREMENTS**:
- Use RAG tool to extract EXACT information
- Include QUANTITATIVE results when available
- Note SPECIFIC algorithms/frameworks
- Identify clear LIMITATIONS
- Extract REAL author names and years (no placeholders)
""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# ----------------------------
# 4. Method Comparison Agent
# ----------------------------
method_comparison_agent = Agent(
    role="Methodology Analyst",
    goal=(
        "Compare the methods used in retrieved papers to identify similarities, "
        "differences, conflicts, and trends, strictly grounded in retrieved evidence."
    ),
    backstory="""You are a methodology expert specializing in comparative research analysis.
Your goal is to identify patterns, variations, and gaps in how researchers approach problems.

**OUTPUT FORMAT**:
---
**COMPARATIVE METHODOLOGY ANALYSIS**

**1. COMMON APPROACHES**:
- **Deep Learning**: [List papers [P#] with specific architectures]
- **Traditional ML**: [Papers using classical methods]
- **Hybrid Approaches**: [Papers combining methods]
- **Novel Frameworks**: [Papers introducing new paradigms]

**2. DATASET ANALYSIS**:
- List datasets used by each paper [P#]
- Note common datasets across papers
- Identify dataset gaps

**3. EVALUATION METRICS**:
- List metrics used by each paper [P#]
- Identify standard vs custom metrics
- Note if different metrics used for same task

**4. PERFORMANCE COMPARISON**:
- Compare reported results when papers tackle similar problems
- Create comparison table
- Identify best-performing approaches

**5. METHODOLOGICAL VARIATIONS**:
- Different preprocessing approaches
- Feature engineering differences
- Architecture variations
- Training strategy differences

**6. IDENTIFIED PATTERNS**:
- **Trends**: [What is becoming more common]
- **Consensus Areas**: [What papers agree on]
- **Controversial Choices**: [Where papers diverge]

**7. METHODOLOGICAL GAPS**:
- Unexplored techniques that might be valuable
- Missing ablation studies
- Lacking cross-dataset validation
- Insufficient comparison with baselines
---

**ANALYSIS STANDARDS**:
- Compare SPECIFIC methods (not generic descriptions)
- Include QUANTITATIVE comparisons when possible
- Identify PRECISE differences
- Highlight innovations vs incremental changes
- Use technical terminology accurately
""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# ----------------------------
# 5. Research Gap Analysis Agent
# ----------------------------
gap_analysis_agent = Agent(
    role="Research Gap Detective",
    goal=(
        "Identify underexplored areas, contradictions, or limitations in existing "
        "literature, clearly stating how strongly each gap is supported by evidence."
    ),
    backstory="""
You look for what’s missing or poorly addressed in current research. Ask:
- Are there unanswered questions?
- Are there conflicting results?
- Are there methods that haven’t been applied to this domain?
- Are there datasets or evaluation metrics that are lacking?

**INPUT**: Summaries + Method Comparison from previous agents

**OUTPUT FORMAT**:
---
**Identified Research Gaps**:
1. [Gap 1]: [Description + why it matters] (Supported by: [P#,...], Uncertainty: Low/Med/High)
2. [Gap 2]: [Description + why it matters] (Supported by: [P#,...], Uncertainty: Low/Med/High)
3. [Gap 3]: [Description + why it matters] (Supported by: [P#,...], Uncertainty: Low/Med/High)

**Opportunity for Novelty**: [How user’s idea could fill these gaps]
---
""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# ----------------------------
# 6. Novelty Detection Agent
# ----------------------------
novelty_agent = Agent(
    role="Novelty Evaluator",
    goal=(
        "Assess the novelty of the user’s research idea relative to prior work, "
        "providing a transparent, evidence-grounded score and explanation."
    ),
    backstory="""
You compare the user’s proposed idea against the synthesized literature. Evaluate novelty based on:
- Methodological innovation
- Dataset uniqueness
- Problem formulation
- Objective or metric improvement

**INPUT**: User’s research idea + Summaries + Gap Analysis

**OUTPUT FORMAT**:
---
**Novelty Assessment**:
- Novelty Score: [0-100] (Based on divergence from SOTA)
- Reasoning: [Why it’s novel or not — cite specific papers with [P#] handles]
- Closest Prior Work: [Titles + authors + year + similarity %, with [P#] references]
- Recommendation: [“Highly Novel”, “Moderately Novel”, “Not Novel”]

**Evidence Table**:
- Supported aspects: [List aspects of the idea clearly supported by [P#] evidence]
- Weakly supported aspects: [List where evidence is indirect or thin]
- Unsupported / speculative aspects: [List and clearly mark as speculative]

**Uncertainty & Conflicts**:
- Overall uncertainty: [Low / Medium / High + 1–2 sentences]
- Conflicting prior work: [If any, with [P#] references and short discussion]
---
""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)