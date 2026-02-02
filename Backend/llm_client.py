import logging
import time
import os
from datetime import datetime
from dotenv import load_dotenv
from ollama import Client

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
    """Optimized Ollama LLM client using official Ollama Python SDK."""
    
    def __init__(self, model=None, base_url=None, temperature=None): 
        # Get configuration from environment variables with fallbacks
        self.model = model or os.getenv("OLLAMA_MODEL", "gpt-oss:120b")
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "https://ollama.com")).rstrip("/")
        self.temperature = float(temperature or os.getenv("TEMPERATURE", "0.1"))
        
        # Get API key for Ollama Cloud
        self.api_key = os.getenv("OLLAMA_API_KEY")
        
        # Initialize Ollama client with authentication
        if self.api_key:
            self.client = Client(
                host=self.base_url,
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
            logger.info(f"✓ Ollama client initialized with API key authentication")
        else:
            self.client = Client(host=self.base_url)
            logger.info(f"✓ Ollama client initialized without authentication")
        
        logger.info(f"OllamaLLM initialized - Model: {self.model}, Base URL: {self.base_url}")
        self.call_count = 0
        
        # Test connection
        self._test_connection()
    
    def supports_stop_words(self):
        return False
    
    def _test_connection(self):
        """Test connection to Ollama server."""
        try:
            # Try to list models as a connection test
            self.client.list()
            logger.info(f"✓ Ollama server connection successful")
            return True
        except Exception as e:
            logger.warning(f"⚠ Cannot connect to Ollama: {e}")
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
        """Generate response using Ollama chat API with streaming."""
        self.call_count += 1
        
        # Truncate very long prompts
        if len(prompt) > 12000:
            prompt = prompt[:12000] + "\n\n[Prompt truncated...]"
        
        messages = [{'role': 'user', 'content': prompt}]
        
        for attempt in range(max_retries + 1):
            try:
                result = ""
                # Use streaming chat API
                for part in self.client.chat(
                    model=self.model,
                    messages=messages,
                    stream=True,
                    options={
                        'temperature': self.temperature,
                        'num_predict': 4096,
                        'top_k': 40,
                        'top_p': 0.9,
                        'num_ctx': 8192
                    }
                ):
                    if 'message' in part and 'content' in part['message']:
                        result += part['message']['content']
                
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
