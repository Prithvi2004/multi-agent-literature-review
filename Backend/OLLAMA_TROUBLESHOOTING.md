# Ollama Integration Troubleshooting Guide

## Common Error: "Invalid response from LLM call - None or empty"

This error occurs when Ollama returns an empty response. Here's how to fix it:

### Step 1: Verify Ollama is Running

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve
```

### Step 2: Test Your Connection

Run the diagnostic script:

```bash
python test_ollama_connection.py
```

### Step 3: Check Your Model

```bash
# List installed models
ollama list

# If your model (gpt-oss:120b-cloud) is not listed, pull it
ollama pull gpt-oss:120b-cloud

# Or use a smaller model for testing
ollama pull llama2:7b
```

### Step 4: Update agents.py if Using Different Model

In `agents.py`, line ~237, change the model name:

```python
# Change from:
llm = OllamaLLM()  # defaults to "gpt-oss:120b-cloud"

# To your model:
llm = OllamaLLM(model="llama2:7b")
```

## Streaming Features Added

The system now includes:

1. **Real-time Streaming**: Responses stream as they're generated
2. **Detailed Logging**: All API calls logged to `outputs/latest_research_session/ollama_logs/ollama_api.log`
3. **Metadata Tracking**: Token counts, durations, and performance metrics
4. **Error Recovery**: Automatic retry on empty responses
5. **Connection Testing**: Validates Ollama connection at startup

## Log File Location

```
outputs/latest_research_session/
├── ollama_logs/
│   └── ollama_api.log  ← All Ollama API calls and responses
├── metrics/
│   └── metrics.json
├── terminal_output/
│   └── terminal_output.txt
└── final_report/
    └── final_research_report.md
```

## Quick Test Command

```bash
# Test Ollama directly
curl http://localhost:11434/api/generate -d '{
  "model": "gpt-oss:120b-cloud",
  "prompt": "Say hello",
  "stream": false
}'
```

## Performance Tips

1. **Use smaller models for testing**: llama2:7b, mistral:7b
2. **Increase timeout** if using large models (in agents.py line ~71)
3. **Reduce context window** (num_ctx in agents.py line ~103) if running out of memory
4. **Monitor logs** in real-time:
   ```bash
   tail -f outputs/latest_research_session/ollama_logs/ollama_api.log
   ```

## Common Issues

### Issue: Model loading is slow

**Solution**: First request always takes longer as model loads into memory

### Issue: Connection refused

**Solution**: Start Ollama with `ollama serve` in a separate terminal

### Issue: Model not found

**Solution**: Pull the model first with `ollama pull <model-name>`

### Issue: Empty responses

**Solution**:

- Check if model is fully loaded
- Try a smaller prompt
- Increase num_predict in agents.py
- Check ollama_api.log for details

## Environment Variables

You can set these in your environment or `.env` file:

```bash
# Ollama settings
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gpt-oss:120b-cloud
OLLAMA_TEMPERATURE=0.2

# CrewAI settings
CREWAI_TRACING_ENABLED=true
```

## Need Help?

1. Check `ollama_api.log` for detailed error messages
2. Run `python test_ollama_connection.py` for diagnostics
3. Verify your model with `ollama list`
4. Check Ollama logs: usually in `~/.ollama/logs/`
