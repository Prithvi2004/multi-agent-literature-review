# Render Deployment Troubleshooting Guide

## Issue: Rust Compilation Error (jiter package)

### Problem

When deploying to Render, you may encounter this error:

```
error: failed to create directory `/usr/local/cargo/registry/cache/index.crates.io-1949cf8c6b5b557f`
Caused by: Read-only file system (os error 30)
```

This occurs when pip tries to build `jiter` from source, which requires Rust toolchain compilation.

### Solution Applied

✅ **Updated requirements.txt** to pin dependencies and avoid Rust compilation:

- Added `jiter>=0.9.0` to ensure pre-built wheels are used
- Pinned `openai>=1.40.0,<2.0.0` to prevent version conflicts
- Added `ollama>=0.4.0` for official Ollama Python SDK

✅ **Updated llm_client.py** to use official Ollama Python client instead of raw HTTP requests

✅ **Simplified dependencies** to avoid complex backtracking during installation

### Environment Variables for Render

Set these in your Render dashboard:

```
OLLAMA_MODEL=gpt-oss:120b
OLLAMA_BASE_URL=https://ollama.com
OLLAMA_API_KEY=<your-actual-api-key>
TEMPERATURE=0.1
FLASK_ENV=production
```

### Deployment Command for Render

**Build Command**:

```bash
pip install -r requirements.txt
```

**Start Command**:

```bash
gunicorn api_server:app --timeout 600 --workers 2 --worker-class sync
```

## Common Issues and Fixes

### 1. Import Errors After Deployment

**Problem**: Missing module imports
**Solution**: Ensure all dependencies are in requirements.txt

### 2. Timeout During Model Responses

**Problem**: Gunicorn times out before model finishes
**Solution**: Increase timeout in start command (already set to 600s)

### 3. CORS Errors from Frontend

**Problem**: Frontend can't connect to backend
**Solution**: Verify CORS configuration in api_server.py includes your Vercel URL

### 4. Ollama API Key Issues

**Problem**: 401 Unauthorized from Ollama
**Solution**:

- Verify API key is correct in Render environment variables
- Check if key hasn't expired in Ollama Cloud dashboard
- Regenerate key if needed

### 5. Memory Issues on Free Tier

**Problem**: Out of memory errors
**Solution**:

- Use Starter tier or higher
- Reduce `--workers` to 1 if needed
- Monitor memory usage in Render dashboard

## Verification Steps

After deployment:

1. **Check Logs**:
   - Go to Render Dashboard → Your Service → Logs
   - Look for "✓ Ollama client initialized with API key authentication"
   - Check for any import errors or crashes

2. **Test Health Endpoint**:

   ```bash
   curl https://multi-agent-literature-review.onrender.com/api/health
   ```

   Expected response: `{"status": "healthy", ...}`

3. **Test from Frontend**:
   - Open https://malrs.vercel.app/
   - Try submitting a research query
   - Check browser console for errors

## Build Time Optimization

To speed up future deployments:

1. **Use Build Cache**: Render caches Python packages between builds
2. **Pin All Versions**: Reduces dependency resolution time
3. **Remove Unused Packages**: Clean up requirements.txt regularly

## Alternative: Use Docker (Advanced)

If issues persist, consider using a Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8080

# Run gunicorn
CMD ["gunicorn", "api_server:app", "--timeout", "600", "--workers", "2", "--bind", "0.0.0.0:8080"]
```

## Contact Support

If issues persist:

- Check Render status page: https://status.render.com/
- Review Render docs: https://render.com/docs/troubleshooting-deploys
- Check Ollama Cloud status: https://ollama.com/status
