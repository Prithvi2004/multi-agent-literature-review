# Backend Deployment Guide - Render.com

## Current Setup

- **Frontend**: Deployed to Vercel at https://malrs.vercel.app/
- **Backend**: Flask API with CrewAI agents and Ollama Cloud integration
- **LLM**: deepseek-v3.1:671b-cloud (Ollama Cloud API)
- **Deployment Platform**: Render.com (recommended)

## Configuration Updates Made

✅ **Backend/.env** - Added Ollama Cloud configuration
✅ **Backend/api_server.py** - Updated CORS to allow https://malrs.vercel.app/
✅ **Backend/llm_client.py** - Now reads from environment variables
✅ **Backend/requirements.txt** - Added gunicorn for production
✅ **Backend/Procfile** - Created for Render deployment
✅ **MALRS-Frontend/.env** - Set API URL to Render backend

## Deployment Steps

### 1. Get Your Ollama Cloud API Key

1. Go to https://ollama.cloud
2. Sign up or log in
3. Go to Settings → API Keys
4. Create a new API key and copy it
5. Save it somewhere safe - you'll need it for environment variables

### 2. Push Backend Code to GitHub

```bash
cd d:\15B\multi-agent-literature-review\Backend

# Initialize git (if not already done)
git init
git add .
git commit -m "Prepare backend for Render deployment with Ollama Cloud"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
git push -u origin main
```

### 3. Deploy to Render

1. Go to https://render.com and sign up/login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select the repository where you pushed the Backend code

5. **Configure the Service**:
   - **Name**: `malrs-backend`
   - **Root Directory**: Leave blank (or enter `Backend` if using monorepo)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn api_server:app --timeout 600 --workers 2 --worker-class sync`
   - **Instance Type**: `Free` or `Starter` (for testing) or `Standard` (for production)

6. **Add Environment Variables**:
   Click "Add Environment Variable" and add:

   ```
   OLLAMA_MODEL=deepseek-v3.1:671b-cloud
   OLLAMA_BASE_URL=https://api.ollama.cloud
   OLLAMA_API_KEY=<paste-your-ollama-cloud-api-key-here>
   TEMPERATURE=0.1
   FLASK_ENV=production
   ```

7. Click **"Create Web Service"**
8. Wait for deployment to complete (check logs for any errors)
9. You'll get a URL like: `https://malrs-backend.onrender.com`

### 4. Verify Deployment

1. **Check Backend Health**:

   ```bash
   curl https://malrs-backend.onrender.com/api/health
   ```

2. **Check Logs in Render Dashboard**:
   - Go to your service in Render
   - Click "Logs" tab
   - Look for initialization messages and any errors

3. **Test from Frontend**:
   - The MALRS-Frontend .env is already configured
   - The frontend will now send requests to your Render backend
   - Test by running an analysis from the frontend

## Important Notes

### About Ollama Cloud API Key

- Store your API key securely in Render environment variables
- Never commit it to GitHub
- You can regenerate keys in Ollama Cloud settings if compromised

### Timeout Configuration

- The `deepseek-v3.1:671b-cloud` model can take time for responses
- Gunicorn timeout is set to 600 seconds (10 minutes)
- Render automatically handles connection pooling

### Free Tier Limitations on Render

- Service spins down after 15 minutes of inactivity
- First request after spin-down takes 30-60 seconds to initialize
- For production use, consider upgrading to paid tier

### CORS Configuration

- Configured to allow requests from https://malrs.vercel.app/
- Also allows localhost for local development
- If you change your Vercel URL, update CORS in api_server.py and redeploy

## Troubleshooting

### Backend Returns 502 Bad Gateway

1. Check Render logs for errors
2. Verify Ollama API key is correct
3. Check if Ollama Cloud API is accessible
4. Wait for service to initialize (takes a minute on first startup)

### API Returns 401 Unauthorized from Ollama

1. Verify OLLAMA_API_KEY environment variable is set
2. Check if key is correct and hasn't expired in Ollama Cloud
3. Regenerate key in Ollama Cloud settings if needed

### Timeout Errors

1. Extend timeout further if needed
2. Check if Ollama Cloud is responding slowly
3. Monitor Render dashboard for resource usage

### CORS Errors from Frontend

1. Verify VITE_API_URL in MALRS-Frontend/.env
2. Check if Vercel frontend URL matches CORS origins in api_server.py
3. Redeploy backend if you updated CORS

## Alternative: Railway Deployment

If you prefer Railway instead of Render:

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub"
3. Select your repository
4. Railway auto-detects Python and requirements.txt
5. Add environment variables same as Render
6. Deploy

Railway has similar features and free tier with more generous limits.

## Architecture Diagram

```
┌─────────────────────────────┐
│  Browser/Client             │
└──────────────┬──────────────┘
               │ HTTPS
               ▼
┌─────────────────────────────┐
│  Vercel Frontend            │
│  https://malrs.vercel.app   │
└──────────────┬──────────────┘
               │ API Requests
               ▼
┌─────────────────────────────┐
│  Render Backend             │
│  https://malrs-backend...   │
│  (Flask + CrewAI)           │
└──────────────┬──────────────┘
               │ HTTPS with API Key
               ▼
┌─────────────────────────────┐
│  Ollama Cloud               │
│  https://api.ollama.cloud   │
│  (deepseek-v3.1 model)      │
└─────────────────────────────┘
```

## Next Steps

1. Get your Ollama Cloud API key
2. Push code to GitHub
3. Deploy to Render following the steps above
4. Test the deployment
5. Monitor logs for any issues

Good luck with your deployment! 🚀
