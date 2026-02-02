# Render Deployment Fix - Dependency Resolution Issues

## Problem

The deployment was failing due to:

1. **Long dependency resolution**: pip spending excessive time trying different versions of `instructor`
2. **Build failure**: Attempting to compile `jiter-0.5.0` from source (requires Rust)
3. **Read-only file system**: Render's build environment couldn't write Cargo cache

## Root Cause

- `crewai` requires `instructor>=1.3.3`
- Older `instructor` versions pulled in incompatible `jiter` versions
- `jiter<0.9.0` needed Rust compilation (no pre-built wheels for Python 3.13)
- Render's environment has read-only `/usr/local/cargo` directory

## Solutions Implemented

### 1. Added Dependency Pins (requirements.txt)

```txt
jiter>=0.9.0  # Forces use of pre-built wheels
instructor<1.12.0,>=1.11.0  # Specific compatible range
openai>=1.40.0,<2.0.0  # Prevents jiter conflicts
pre-commit>=4.3.0  # Required by instructor
```

### 2. Created runtime.txt

```txt
python-3.11.11
```

Using Python 3.11 instead of 3.13 provides:

- Better wheel availability for all packages
- More stable dependency resolution
- Faster build times

## Deployment Steps

1. **Commit the changes**:

   ```bash
   git add Backend/requirements.txt Backend/runtime.txt
   git commit -m "Fix: Pin dependencies for Render deployment"
   git push
   ```

2. **Trigger Render redeploy**:
   - Go to your Render dashboard
   - Click "Manual Deploy" → "Deploy latest commit"
   - Or push will auto-deploy if auto-deploy is enabled

3. **Expected build time**: ~5-8 minutes (much faster than before)

## Verification

After successful deployment, test:

```bash
curl https://your-app.onrender.com/health
```

## Alternative Solutions (if issues persist)

### Option 1: Use a build script

Create `build.sh` in Backend/:

```bash
#!/usr/bin/env bash
pip install --upgrade pip
pip install wheel
pip install -r requirements.txt --prefer-binary
```

Then update Render build command to: `./build.sh`

### Option 2: Pre-compile dependencies

Create a `requirements-lock.txt`:

```bash
pip-compile requirements.txt
```

Use this locked file in Render.

### Option 3: Docker deployment

If pip issues persist, switch to Docker:

- More control over build environment
- Can use conda for FAISS
- Consistent across environments

## Environment Variables Needed

Ensure these are set in Render:

```
OLLAMA_BASE_URL=<your-ollama-endpoint>
GEMINI_API_KEY=<your-gemini-key>
PYTHON_VERSION=3.11.11
```

## Common Render Deployment Issues

1. **Build timeout**: Reduce dependencies or upgrade Render plan
2. **Memory issues**: Increase instance RAM in Render settings
3. **Port binding**: Ensure using `$PORT` environment variable
4. **CORS errors**: Verify Flask-CORS configuration includes frontend URL

## Monitoring

After deployment, check logs:

```bash
render logs -f
```

Look for:

- ✅ "Successfully installed" messages
- ✅ "Starting gunicorn"
- ❌ "ModuleNotFoundError"
- ❌ "ImportError"
