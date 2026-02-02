# 🚂 Railway Deployment Guide - Backend

Complete guide to deploying the Multi-Agent Literature Review System backend on Railway.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Railway Setup](#railway-setup)
4. [Deployment Steps](#deployment-steps)
5. [Environment Configuration](#environment-configuration)
6. [Post-Deployment](#post-deployment)
7. [Monitoring & Logs](#monitoring--logs)
8. [Troubleshooting](#troubleshooting)
9. [Cost Optimization](#cost-optimization)

---

## ✅ Prerequisites

Before deploying to Railway, ensure you have:

1. **Railway Account**
   - Sign up at https://railway.app
   - Connect your GitHub account
   - Add payment method (Railway offers $5 free credit monthly)

2. **Ollama Cloud API Key**
   - Go to https://ollama.cloud (or your Ollama provider)
   - Sign up/login and navigate to API Keys
   - Generate a new API key
   - Save it securely (you'll need it for environment variables)

3. **GitHub Repository**
   - Backend code pushed to a GitHub repository
   - Repository should be public or Railway needs access to private repo

4. **Local Testing Complete**
   - Backend API tested locally
   - All dependencies in [requirements.txt](requirements.txt)
   - `.env` file configured locally (but NOT committed to Git)

---

## 🔍 Pre-Deployment Checklist

### 1. Verify Project Structure

Your Backend folder should contain:

```
Backend/
├── api_server.py          # Main Flask application
├── main.py                # Core agent logic
├── requirements.txt       # Python dependencies
├── Procfile              # Railway start command
├── runtime.txt           # Python version (optional)
├── .env.example          # Example environment variables
├── .gitignore            # Git ignore file
├── agents_v2.py          # Agent definitions
├── rag_pipeline_v2.py    # RAG pipeline
├── llm_client.py         # LLM configuration
└── faiss_index/          # FAISS vector index
    └── index.faiss
```

### 2. Update `.gitignore`

Ensure sensitive files are NOT committed:

```gitignore
# Environment variables
.env
.env.local

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Outputs
outputs/
*.log

# Virtual environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
```

### 3. Check `Procfile`

Your [Procfile](Procfile) should contain:

```
web: gunicorn api_server:app --bind 0.0.0.0:$PORT --timeout 600 --workers 2 --worker-class sync
```

**Note:** Railway automatically sets the `$PORT` environment variable.

### 4. Verify `requirements.txt`

Ensure all dependencies are listed with proper versions:

```txt
# Core dependencies
ollama>=0.4.0
crewai>=0.11.0
crewai-tools
langchain>=0.1.0
langchain-ollama
langchain-community
sentence-transformers>=2.2.0

# API Framework
Flask>=3.0.0
Flask-CORS>=4.0.0
gunicorn>=21.0.0

# Other dependencies
numpy>=1.24.0
faiss-cpu
requests
python-dotenv
```

### 5. Optional: Create `runtime.txt`

Specify Python version (Railway auto-detects, but explicit is better):

```
python-3.11.7
```

---

## 🚀 Railway Setup

### Step 1: Create a New Project

1. Go to https://railway.app/dashboard
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository containing the Backend code

### Step 2: Configure Service

Railway will automatically detect your project. Configure as follows:

#### Root Directory

- If Backend is in root: Leave blank
- If Backend is in subfolder: Set to `Backend`

#### Start Command

Railway should auto-detect the Procfile, but you can manually set:

```bash
gunicorn api_server:app --bind 0.0.0.0:$PORT --timeout 600 --workers 2 --worker-class sync
```

#### Build Command (Optional)

Railway auto-runs `pip install -r requirements.txt`, but you can customize:

```bash
pip install --upgrade pip && pip install -r requirements.txt
```

---

## 🔧 Environment Configuration

### Add Environment Variables

In Railway dashboard:

1. Click on your service
2. Go to **"Variables"** tab
3. Add the following variables:

#### Required Variables

| Variable           | Value                | Description                               |
| ------------------ | -------------------- | ----------------------------------------- |
| `OLLAMA_MODEL`     | `gpt-oss:120b`       | Model to use (adjust based on your needs) |
| `OLLAMA_BASE_URL`  | `https://ollama.com` | Ollama API endpoint                       |
| `OLLAMA_API_KEY`   | `your-api-key-here`  | Your Ollama Cloud API key                 |
| `TEMPERATURE`      | `0.1`                | LLM temperature (0.0-1.0)                 |
| `FLASK_ENV`        | `production`         | Flask environment                         |
| `PYTHONUNBUFFERED` | `1`                  | Disable Python output buffering           |

#### Optional Variables

| Variable      | Value               | Description                |
| ------------- | ------------------- | -------------------------- |
| `PORT`        | Auto-set by Railway | Don't manually set this    |
| `MAX_WORKERS` | `2`                 | Number of gunicorn workers |
| `TIMEOUT`     | `600`               | Request timeout in seconds |
| `LOG_LEVEL`   | `INFO`              | Logging level              |

#### Security Variables (if using custom domains)

| Variable          | Value                    | Description          |
| ----------------- | ------------------------ | -------------------- |
| `ALLOWED_ORIGINS` | `https://yourdomain.com` | CORS allowed origins |

### Example Environment Configuration

```env
# LLM Configuration
OLLAMA_MODEL=gpt-oss:120b
OLLAMA_BASE_URL=https://ollama.com
OLLAMA_API_KEY=sk-your-actual-api-key-here
TEMPERATURE=0.1

# Flask Configuration
FLASK_ENV=production
PYTHONUNBUFFERED=1

# Optional: Gemini fallback
GEMINI_API_KEY=your-gemini-key-here
```

---

## 🚢 Deployment Steps

### Method 1: Deploy via Railway Dashboard (Recommended)

1. **Connect GitHub Repository**

   ```
   Railway Dashboard → New Project → Deploy from GitHub repo
   ```

2. **Select Repository**
   - Choose your backend repository
   - Select the branch (usually `main` or `master`)

3. **Configure Root Directory**
   - If monorepo: Set root directory to `Backend`
   - If backend is at root: Leave blank

4. **Add Environment Variables**
   - Click "Variables" tab
   - Add all required variables from above section
   - Click "Add" for each variable

5. **Deploy**
   - Railway will automatically:
     - Build your project
     - Install dependencies
     - Start the server
   - Monitor deployment in "Deployments" tab

6. **Get Your Domain**
   - Once deployed, Railway provides a public URL
   - Format: `https://your-service-name.railway.app`
   - Or generate custom domain in "Settings" → "Networking"

### Method 2: Deploy via Railway CLI

1. **Install Railway CLI**

   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway**

   ```bash
   railway login
   ```

3. **Initialize Project**

   ```bash
   cd d:\15B\multi-agent-literature-review\Backend
   railway init
   ```

4. **Link to Existing Project (Optional)**

   ```bash
   railway link
   ```

5. **Add Environment Variables**

   ```bash
   railway variables set OLLAMA_API_KEY=your-key-here
   railway variables set OLLAMA_MODEL=gpt-oss:120b
   railway variables set OLLAMA_BASE_URL=https://ollama.com
   railway variables set TEMPERATURE=0.1
   railway variables set FLASK_ENV=production
   railway variables set PYTHONUNBUFFERED=1
   ```

6. **Deploy**

   ```bash
   railway up
   ```

7. **Open Deployment**
   ```bash
   railway open
   ```

---

## ✔️ Post-Deployment

### 1. Verify Deployment

#### Check Health Endpoint

```bash
curl https://your-service-name.railway.app/api/health
```

Expected response:

```json
{
  "status": "healthy",
  "timestamp": "2026-02-02T12:34:56",
  "environment": "production"
}
```

#### Check Ollama Connection

```bash
curl https://your-service-name.railway.app/api/test-ollama
```

Expected response:

```json
{
  "status": "success",
  "model": "gpt-oss:120b",
  "connection": "ok"
}
```

### 2. Update Frontend Configuration

Update your frontend's `.env` file:

```env
# MALRS-Frontend/.env
VITE_API_BASE_URL=https://your-service-name.railway.app
```

### 3. Test End-to-End

1. Open your frontend application
2. Submit a research query
3. Monitor logs in Railway dashboard
4. Verify results are returned correctly

### 4. Set Up Custom Domain (Optional)

1. Go to Railway Dashboard → Your Service → Settings → Networking
2. Click "Generate Domain" for Railway subdomain
3. Or add custom domain:
   - Click "Add Domain"
   - Enter your domain (e.g., `api.yourdomain.com`)
   - Update DNS records as instructed
   - Wait for SSL certificate provisioning

---

## 📊 Monitoring & Logs

### View Real-Time Logs

#### Railway Dashboard

1. Go to your service
2. Click "Deployments" tab
3. Click on active deployment
4. View logs in real-time

#### Railway CLI

```bash
railway logs
```

For continuous streaming:

```bash
railway logs --follow
```

### Key Metrics to Monitor

1. **Deployment Status**
   - Build time
   - Deployment success/failure
   - Active deployment health

2. **Application Logs**
   - API requests
   - Agent execution
   - Error messages
   - Performance metrics

3. **Resource Usage**
   - CPU usage
   - Memory consumption
   - Network traffic
   - Request count

### Set Up Alerts (Optional)

Railway provides webhooks for deployment events:

1. Go to Settings → Webhooks
2. Add webhook URL for notifications
3. Configure events (deploy, restart, error)

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Build Fails - Dependency Installation

**Problem:** `faiss-cpu` fails to install

**Solution:** Add to [requirements.txt](requirements.txt):

```txt
# For Railway deployment
faiss-cpu; platform_system != "Windows"
```

Railway runs on Linux, so this should work.

#### 2. Application Crashes on Start

**Problem:** Gunicorn fails to start

**Check:**

```bash
# View logs
railway logs

# Common issues:
# - Missing environment variables
# - Import errors
# - Port binding issues
```

**Solutions:**

- Verify all environment variables are set
- Check [api_server.py](api_server.py) imports
- Ensure Procfile uses `$PORT` variable

#### 3. Ollama API Connection Fails

**Problem:** Cannot connect to Ollama Cloud

**Check:**

```bash
# Test locally first
python test_ollama_connection.py
```

**Solutions:**

- Verify `OLLAMA_API_KEY` is correct
- Check `OLLAMA_BASE_URL` is set
- Ensure model name matches available models
- Check API quota/rate limits

#### 4. CORS Errors

**Problem:** Frontend can't connect to backend

**Solution:** Update [api_server.py](api_server.py) CORS configuration:

```python
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5173",
            "https://your-frontend-domain.com",
            "https://your-service-name.railway.app"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})
```

#### 5. Timeout Errors

**Problem:** Requests timeout after 60 seconds

**Solutions:**

1. **Increase Gunicorn timeout** in Procfile:

   ```
   web: gunicorn api_server:app --bind 0.0.0.0:$PORT --timeout 900 --workers 2
   ```

2. **Optimize agent execution:**
   - Reduce number of papers retrieved
   - Use faster models
   - Implement caching

#### 6. Memory Issues

**Problem:** Application runs out of memory

**Solutions:**

1. **Reduce workers** in Procfile:

   ```
   web: gunicorn api_server:app --bind 0.0.0.0:$PORT --timeout 600 --workers 1
   ```

2. **Upgrade Railway plan:**
   - Free tier: 512MB RAM
   - Hobby: 8GB RAM
   - Pro: 32GB RAM

3. **Optimize code:**
   - Clear FAISS cache periodically
   - Use smaller embedding models
   - Implement pagination

### Debug Mode

Enable debug logging temporarily:

```bash
# Add to Railway environment variables
LOG_LEVEL=DEBUG
FLASK_DEBUG=0  # Keep False in production for security
```

### Health Check Endpoint

Railway automatically checks `/` or `/health`. Ensure you have:

```python
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("FLASK_ENV", "development")
    })
```

---

## 💰 Cost Optimization

### Railway Pricing

- **Hobby Plan:** $5/month + usage
  - Includes: $5 credit
  - Good for: Low traffic applications
- **Pro Plan:** $20/month + usage
  - Includes: $20 credit
  - Good for: Production applications

### Usage Metrics

- **CPU:** Billed by vCPU-hour
- **Memory:** Billed by GB-hour
- **Network:** Outbound traffic

### Optimization Tips

#### 1. Resource Management

```python
# In api_server.py, implement request queuing
from queue import Queue
request_queue = Queue(maxsize=5)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    if request_queue.full():
        return jsonify({"error": "Server busy"}), 503
    # Process request
```

#### 2. Reduce Worker Count

For low traffic, use 1 worker:

```
web: gunicorn api_server:app --bind 0.0.0.0:$PORT --timeout 600 --workers 1
```

#### 3. Implement Caching

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_query(query_text):
    # Cache frequent queries
    return process_query(query_text)
```

#### 4. Sleep During Inactivity

Railway charges for uptime. For development:

- Use Railway's "sleep" feature
- Wake on HTTP request

#### 5. Monitor Usage

```bash
# Check current usage
railway status

# View metrics
railway metrics
```

---

## 🎯 Production Best Practices

### 1. Security

- **Never commit `.env` files**
- Use Railway's environment variables
- Rotate API keys regularly
- Implement rate limiting

### 2. Reliability

- **Health checks:** Implement robust health endpoints
- **Error handling:** Catch and log all exceptions
- **Retries:** Implement retry logic for external APIs
- **Graceful degradation:** Handle partial failures

### 3. Performance

- **Connection pooling:** Reuse HTTP connections
- **Caching:** Cache frequent queries
- **Async operations:** Use async where possible
- **Database optimization:** Optimize FAISS index queries

### 4. Monitoring

- **Structured logging:** Use JSON logs for easy parsing
- **Metrics:** Track request count, latency, errors
- **Alerts:** Set up notifications for errors
- **Uptime monitoring:** Use external service (e.g., UptimeRobot)

### 5. Deployment

- **CI/CD:** Automate deployments via GitHub Actions
- **Staging environment:** Test before production
- **Rollback plan:** Keep previous deployments accessible
- **Version tagging:** Tag releases in Git

---

## 📚 Additional Resources

### Railway Documentation

- **Official Docs:** https://docs.railway.app
- **Python Guide:** https://docs.railway.app/guides/python
- **Flask Example:** https://docs.railway.app/guides/flask

### Project Documentation

- [API Server Code](api_server.py)
- [Main Agent Logic](main.py)
- [Configuration Guide](CONFIGURATION_GUIDE.md)
- [Render Deployment](DEPLOYMENT_GUIDE.md) (alternative platform)

### Support

- **Railway Discord:** https://discord.gg/railway
- **Railway Status:** https://railway.statuspage.io
- **Project Issues:** GitHub Issues in your repository

---

## ✨ Quick Reference Commands

### Railway CLI Commands

```bash
# Login
railway login

# Initialize project
railway init

# Link to project
railway link

# Deploy
railway up

# View logs
railway logs --follow

# Open dashboard
railway open

# Check status
railway status

# Run command in Railway environment
railway run python test_ollama_connection.py

# Add environment variable
railway variables set KEY=VALUE

# Remove service
railway down
```

### Testing Locally Before Deploy

```bash
# Activate virtual environment
cd d:\15B\multi-agent-literature-review\Backend
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set environment variables (create .env file)
cp .env.example .env
# Edit .env with your values

# Run with gunicorn (production mode)
gunicorn api_server:app --bind 0.0.0.0:5000 --timeout 600 --workers 2

# Test health endpoint
curl http://localhost:5000/api/health

# Test Ollama connection
curl http://localhost:5000/api/test-ollama
```

---

## 🎉 Summary

Your backend is now deployed on Railway! Here's what you accomplished:

✅ Configured Railway project with GitHub integration
✅ Set up environment variables securely
✅ Deployed Flask API with gunicorn
✅ Connected to Ollama Cloud LLM
✅ Set up monitoring and logging
✅ Tested health endpoints

**Your Backend URL:** `https://your-service-name.railway.app`

**Next Steps:**

1. Update frontend to use new backend URL
2. Test end-to-end functionality
3. Monitor logs for issues
4. Optimize based on usage patterns

Need help? Check the Troubleshooting section or Railway documentation!
