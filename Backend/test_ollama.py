"""test_ollama.py
Lightweight Ollama connectivity + sample prompt tester for this project.

Usage:
  python test_ollama.py                # uses defaults (model=qwen2.5:7b)
  python test_ollama.py --model mymod --prompt "Hello world"

This script will:
 - Verify the Ollama service is reachable
 - List available models (and check for a preferred model)
 - Send a sample prompt to a model and print the LLM response

The sample prompt helps verify end-to-end LLM responses during development.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

import requests


OLLAMA_URL = "http://localhost:11434"


def list_models(timeout: float = 5.0) -> Optional[list]:
    """Return list of models (or None on failure)."""
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=timeout)
        if resp.status_code != 200:
            print(f"Ollama returned status {resp.status_code}")
            return None
        data = resp.json()
        # older/newer Ollama versions may return models under different keys
        models = data.get("models") or data.get("tags") or []
        return models
    except requests.exceptions.RequestException as e:
        print(f"Error contacting Ollama: {e}")
        return None


def send_prompt(model: str, prompt: str, timeout: float = 30.0) -> Optional[str]:
    """Try common Ollama generation endpoints and return the textual response.

    We attempt `/api/generate`, `/api/completions`, then `/api/chat` and
    return the first successful textual result. If the endpoint returns JSON
    we attempt to extract likely text fields.
    """
    endpoints = ["/api/generate", "/api/completions", "/api/chat"]
    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens": 256,
        "temperature": 0.2,
    }

    headers = {"Content-Type": "application/json"}
    for ep in endpoints:
        url = f"{OLLAMA_URL}{ep}"
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=timeout)
        except requests.exceptions.RequestException:
            continue

        if not r.ok:
            continue

        # Try to decode JSON response and extract text
        try:
            j = r.json()
        except Exception:
            # Fallback to raw text
            return r.text.strip()

        # Common response shapes: {'response': '...'} or {'choices':[{'text': '...'}]}
        if isinstance(j, dict):
            if "response" in j and isinstance(j["response"], str):
                return j["response"].strip()
            if "text" in j and isinstance(j["text"], str):
                return j["text"].strip()
            if "choices" in j and isinstance(j["choices"], list) and j["choices"]:
                c0 = j["choices"][0]
                if isinstance(c0, dict) and "text" in c0:
                    return c0["text"].strip()
                # older variants may use 'message' or 'content'
                if isinstance(c0, dict) and "message" in c0:
                    return str(c0["message"]).strip()

        # If we get here, return a JSON pretty string so the caller can inspect
        return json.dumps(j, indent=2, ensure_ascii=False)

    return None


def main() -> int:
    p = argparse.ArgumentParser(description="Ollama connectivity + sample prompt tester")
    p.add_argument("--model", "-m", default="qwen2.5:7b", help="Model name to test (default: qwen2.5:7b)")
    p.add_argument("--prompt", "-p", default=(
        "Explain the significance of transformer models in NLP in one concise paragraph."),
        help="Prompt to send to the model"
    )
    p.add_argument("--list-only", action="store_true", help="Only list models and exit")
    args = p.parse_args()

    print("🔍 Checking Ollama service at", OLLAMA_URL)
    models = list_models()
    if models is None:
        print("❌ Could not reach Ollama. Ensure the service is running on localhost:11434.")
        return 1

    model_names = [m.get("name") if isinstance(m, dict) else str(m) for m in models]
    print(f"✅ Ollama reachable — {len(model_names)} models reported")
    for name in model_names:
        print("  -", name)

    preferred = args.model
    if args.list_only:
        return 0

    if preferred not in model_names:
        print(f"\n⚠️ Preferred model '{preferred}' not found on the Ollama server.")
        print("   Available models: ", ", ".join(model_names))
        print("   You can pull a model locally with: ollama pull <model>")

    print(f"\n💬 Sending sample prompt to model: {preferred}\n")
    print("PROMPT:\n", args.prompt)
    print()
    resp = send_prompt(preferred, args.prompt)
    if resp is None:
        print("❌ No successful response from Ollama for the sample prompt.")
        return 2

    print("--- MODEL RESPONSE START ---")
    print(resp)
    print("--- MODEL RESPONSE END ---")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""
Quick test script to verify Ollama connection
Run this before starting api_server.py to ensure Ollama is ready
"""

import requests
import sys

def check_ollama():
    """Check if Ollama is running and accessible"""
    try:
        print("🔍 Checking Ollama service on http://localhost:11434...")
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            print("✅ Ollama is running!")
            print(f"📦 Available models: {len(models)}")
            print(models)
            
            # Check for qwen2.5:7b specifically
            model_names = [m.get('name', '') for m in models]
            if 'qwen2.5:7b' in model_names:
                print("✅ qwen2.5:7b model found - Ready for Finora AI!")
                return True
            else:
                print("⚠️  qwen2.5:7b not found. Available models:")
                for name in model_names:
                    print(f"   - {name}")
                print("\n💡 To install qwen2.5:7b, run:")
                print("   ollama pull qwen2.5:7b")
                return False
        else:
            print(f"❌ Ollama responded with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama on http://localhost:11434")
        print("\n📋 To fix this:")
        print("   1. Install Ollama from https://ollama.ai/download")
        print("   2. Start Ollama service:")
        print("      Windows: Ollama should start automatically")
        print("      Linux/Mac: Run 'ollama serve' in a terminal")
        print("   3. Pull the model: ollama pull qwen2.5:7b")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ Ollama request timed out")
        print("   Service may be starting up - wait a moment and try again")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("FINORA AI - OLLAMA CONNECTION TEST")
    print("=" * 60)
    print()
    
    success = check_ollama()
    
    print()
    print("=" * 60)
    if success:
        print("✅ ALL CHECKS PASSED - Ready to start api_server.py")
        print()
        print("Next steps:")
        print("  1. python api_server.py")
        print("  2. cd ../FinoraAI-FrontEnd && npm run dev")
        sys.exit(0)
    else:
        print("❌ CHECKS FAILED - Fix issues above before proceeding")
        sys.exit(1)
