import requests
import logging
import time
import json
import os
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Setup dedicated Ollama log file
ollama_log_folder = os.path.join('outputs', 'latest_research_session', 'ollama_logs')
os.makedirs(ollama_log_folder, exist_ok=True)
ollama_log_file = os.path.join(ollama_log_folder, 'ollama_api.log')

# Create Ollama-specific logger
ollama_logger = logging.getLogger('ollama_api')
ollama_logger.setLevel(logging.INFO)
# Clear existing handlers to avoid duplicates on reload
if ollama_logger.hasHandlers():
    ollama_logger.handlers.clear()
    
ollama_handler = logging.FileHandler(ollama_log_file, mode='a', encoding='utf-8')
ollama_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
ollama_logger.addHandler(ollama_handler)

class OllamaLLM:
    """Optimized Ollama LLM client with connection pooling and retry logic."""
    
    def __init__(self, model=None, base_url=None, temperature=None): 
        # Get configuration from environment variables with fallbacks
        self.model = model or os.getenv("OLLAMA_MODEL", "deepseek-v3.1:671b-cloud")
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "https://api.ollama.cloud")).rstrip("/")
        self.temperature = float(temperature or os.getenv("TEMPERATURE", "0.1"))
        
        # Get API key if using Ollama Cloud
        self.api_key = os.getenv("OLLAMA_API_KEY")
        
        # Configure session with connection pooling and retries
        self.session = requests.Session()
        
        # Add authorization header if API key exists
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        logger.info(f"OllamaLLM initialized - Model: {model}, Base URL: {base_url}")
        self.call_count = 0
        
        # Test connection
        self._test_connection()
    
    def supports_stop_words(self):
        return False
    
    def _test_connection(self):
        try:
            test_resp = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            if test_resp.status_code == 200:
                logger.info(f"✓ Ollama server connection successful")
                return True
            logger.warning(f"⚠ Ollama server responded with {test_resp.status_code}")
            return False
        except Exception as e:
            logger.error(f"❌ Cannot connect to Ollama: {e}")
            # Don't fail initialization - connection might work when actually generating
            return False

    def call(self, messages, **kwargs):
        """CrewAI expects a call method that accepts messages and returns response text."""
        if isinstance(messages, list):
            prompt = "\n".join([m.get("content", "") if isinstance(m, dict) else str(m) for m in messages])
        else:
            prompt = str(messages)
        return self.generate(prompt, **kwargs)

    def generate(self, prompt: str, timeout: int = 300, max_retries: int = 2, **kwargs):
        self.call_count += 1
        
        # Truncate very long prompts
        if len(prompt) > 12000:
            prompt = prompt[:12000] + "\n\n[Prompt truncated...]"
        
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
                    try:
                        chunk = json.loads(line)
                        if 'response' in chunk: result += chunk['response']
                    except:
                        pass
                
                ollama_logger.info(f"Response generated in attempt {attempt+1}")
                return result
                
            except Exception as e:
                logger.error(f"Ollama attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                return f"Error: Failed to get response from Ollama - {str(e)}"

# Singleton instance
llm = OllamaLLM()

# Monkeypatch crewai (Keep this magic here)
try:
    from crewai.utilities import llm_utils
    import crewai.agent.core as agent_core
    def _create_llm_direct(conf): return llm
    llm_utils.create_llm = _create_llm_direct
    setattr(agent_core, "create_llm", _create_llm_direct)
except Exception:
    pass
