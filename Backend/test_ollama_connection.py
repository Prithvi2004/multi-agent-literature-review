import os
from ollama import Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv('OLLAMA_API_KEY')
if not api_key:
    print("❌ ERROR: OLLAMA_API_KEY not found in .env file")
    print("Please add OLLAMA_API_KEY to your .env file")
    exit(1)

client = Client(
    host="https://ollama.com",
    headers={'Authorization': f'Bearer {api_key}'}
)

messages = [
  {
    'role': 'user',
    'content': 'Why is the sky blue?',
  },
]

for part in client.chat('gpt-oss:120b', messages=messages, stream=True):
  print(part['message']['content'], end='', flush=True)