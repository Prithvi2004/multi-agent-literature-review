# 🚀 Quick Deployment Guide - Render Fix

## What Was Wrong?

Your Flask app wasn't binding to Render's dynamic `$PORT` environment variable, so Render couldn't detect it as running.

## What I Fixed

### 1. ✅ Updated `api_server.py`
- Now reads `PORT` from environment variable
- Detects production vs development mode
- Disables debug mode in production

### 2. ✅ Created `render.yaml`
- Blueprint configuration for easy deployment
- Proper health check setup
- Environment variable definitions

## 🎯 Deploy Now - 3 Steps

### Step 1: Update Render Settings

In your Render dashboard, verify these settings:

```
Root Directory: Backend
Build Command: pip install -r requirements.txt
Start Command: gunicorn api_server:app --bind 0.0.0.0:$PORT --timeout 600 --workers 2 --worker-class sync --log-level info
Health Check Path: /api/health
```

### Step 2: Set Environment Variables

Go to Render Dashboard → Your Service → Environment

Add these variables:
```bash
OLLAMA_API_KEY=<your_actual_key>
OLLAMA_BASE_URL=https://ollama.com
PYTHON_VERSION=3.13.1
RENDER=true
```

> ⚠️ **CRITICAL**: Replace `<your_actual_key>` with your real Ollama API key!

### Step 3: Deploy

```bash
# Commit the fixes
git add Backend/api_server.py Backend/render.yaml
git commit -m "fix: Render deployment port binding"
git push origin main
```

Render will auto-deploy. Watch the logs for:
```
✓ Starting Flask API Server for Multi-Agent Literature Review
✓ Environment: PRODUCTION
✓ API will be available at: http://0.0.0.0:<dynamic-port>
```

## ✅ Verify Deployment

Once deployed, test:
```bash
curl https://your-app.onrender.com/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "service": "Multi-Agent Literature Review API"
}
```

## 🔧 Still Having Issues?

### "No open ports detected"
- Check environment variables are set in Render dashboard
- Verify logs show: `API will be available at: http://0.0.0.0:<PORT>`
- Ensure `$PORT` is a dynamic number (not 5000)

### Build Failures
- Check `runtime.txt` has `python-3.13.1`
- Review build logs for package installation errors
- Some packages may need system dependencies

### Health Check Fails
- Wait 2-3 minutes for first deployment
- Check `/api/health` returns 200 OK
- Increase health check timeout in Render settings

## 📋 Files Changed

| File | Status |
|------|--------|
| `Backend/api_server.py` | ✅ Updated |
| `Backend/render.yaml` | ✅ Created |

## 🎉 What's Next?

After successful deployment:
1. Test the `/api/analyze` endpoint
2. Connect your frontend to the deployed backend URL
3. Update CORS origins if needed for your frontend domain

---

**Need more details?** See the full `implementation_plan.md` for comprehensive troubleshooting.
