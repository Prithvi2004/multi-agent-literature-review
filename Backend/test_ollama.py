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
