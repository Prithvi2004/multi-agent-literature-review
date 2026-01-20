from google import genai

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client()

print("=" * 80)
print("🧪 GEMINI API TEST")
print("=" * 80)

# Test basic content generation
print("\n📝 Testing content generation...")
response = client.models.generate_content(
    model="gemini-2.0-flash-exp", contents="Explain how AI works in a few words"
)
print(f"Response: {response.text}\n")

# List available models
print("=" * 80)
print("📋 AVAILABLE GEMINI MODELS")
print("=" * 80)
try:
    models = client.models.list()
    for model in models:
        print(f"\n✓ {model.name}")
        if hasattr(model, 'display_name'):
            print(f"  Display Name: {model.display_name}")
        if hasattr(model, 'description'):
            print(f"  Description: {model.description}")
        if hasattr(model, 'supported_generation_methods'):
            print(f"  Supported Methods: {', '.join(model.supported_generation_methods)}")
except Exception as e:
    print(f"Error listing models: {e}")

# Display rate limits information
print("\n" + "=" * 80)
print("⚡ GEMINI API RATE LIMITS (Free Tier)")
print("=" * 80)
print("""
Gemini 2.0 Flash (Experimental):
  • 10 RPM (Requests Per Minute)
  • 1,500 RPD (Requests Per Day)
  • 4 Million TPM (Tokens Per Minute)

Gemini 1.5 Flash:
  • 15 RPM
  • 1,500 RPD
  • 1 Million TPM

Gemini 1.5 Pro:
  • 2 RPM
  • 50 RPD
  • 32,000 TPM

Gemini 2.0 Flash Thinking (Experimental):
  • 2 RPM
  • 50 RPD
  • 32,000 TPM

Note: Rate limits may vary based on your API plan (Free vs Paid).
For paid plans, limits are significantly higher.
""")

print("=" * 80)
print("✅ TEST COMPLETED")
print("=" * 80)