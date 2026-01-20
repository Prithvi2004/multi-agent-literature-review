"""
Quick diagnostic script to test Ollama connection and streaming
"""

import requests
import json
import sys

def test_ollama_connection():
    """Test basic Ollama connection and streaming"""
    
    base_url = "http://localhost:11434"
    model = "qwen3:4b"  # Change to your model
    
    print("="*80)
    print("OLLAMA CONNECTION DIAGNOSTIC")
    print("="*80)
    
    # Test 1: Check if server is running
    print(f"\n1. Testing connection to {base_url}...")
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=5)
        if resp.status_code == 200:
            print(f"   ✓ Server is running")
            data = resp.json()
            models = data.get('models', [])
            if models:
                print(f"   ✓ Available models:")
                for m in models[:10]:
                    print(f"      - {m.get('name', 'unknown')}")
            else:
                print(f"   ⚠ No models found. Pull a model with: ollama pull {model}")
        else:
            print(f"   ❌ Server responded with status {resp.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"   ❌ Cannot connect: {e}")
        print(f"\n   Please start Ollama:")
        print(f"      1. Run: ollama serve")
        print(f"      2. Or start the Ollama desktop app")
        sys.exit(1)
    
    # Test 2: Try a simple generation
    print(f"\n2. Testing streaming generation with model: {model}...")
    payload = {
        "model": model,
        "prompt": "Say 'Hello, I am working correctly!' in one sentence.",
        "stream": True,
        "options": {
            "num_predict": 50
        }
    }
    
    try:
        resp = requests.post(
            f"{base_url}/api/generate",
            json=payload,
            stream=True,
            timeout=60
        )
        resp.raise_for_status()
        
        print("   ✓ Request sent, receiving stream...")
        
        result = ""
        chunk_count = 0
        
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            try:
                chunk = json.loads(line)
                chunk_count += 1
                
                if 'error' in chunk:
                    print(f"   ❌ Error in response: {chunk['error']}")
                    sys.exit(1)
                
                response_part = chunk.get('response', '')
                if response_part:
                    result += response_part
                    print(f"      Chunk {chunk_count}: {response_part}", end='', flush=True)
                
                if chunk.get('done'):
                    print(f"\n   ✓ Stream completed")
                    print(f"\n   Full response: {result}")
                    print(f"   Total chunks: {chunk_count}")
                    
                    # Show metadata
                    if chunk.get('prompt_eval_count'):
                        print(f"   Prompt tokens: {chunk.get('prompt_eval_count')}")
                    if chunk.get('eval_count'):
                        print(f"   Response tokens: {chunk.get('eval_count')}")
                    break
                    
            except json.JSONDecodeError as je:
                print(f"   ⚠ Failed to parse chunk: {line[:100]}")
                continue
        
        if not result or len(result.strip()) == 0:
            print(f"\n   ❌ PROBLEM: Empty response received!")
            print(f"   This means the model returned no text.")
            print(f"\n   Possible causes:")
            print(f"      1. Model '{model}' not found - pull it with: ollama pull {model}")
            print(f"      2. Model is loading - wait a moment and try again")
            print(f"      3. Try a different model - list with: ollama list")
            sys.exit(1)
        else:
            print(f"\n   ✓ SUCCESS! Response length: {len(result)} chars")
            
    except requests.exceptions.Timeout:
        print(f"   ❌ Request timed out")
        print(f"   The model might be too large or the server is overloaded")
        sys.exit(1)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("✓ ALL TESTS PASSED")
    print("="*80)
    print(f"\nYour Ollama setup is working correctly!")
    print(f"You can now run your main application.\n")

if __name__ == "__main__":
    test_ollama_connection()
