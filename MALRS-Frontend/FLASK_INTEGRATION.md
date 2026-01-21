# React Frontend - Flask API Integration

## Overview

The MALRS-Frontend (React + Vite + TypeScript) now connects to the same Flask backend that the Streamlit frontend uses.

## Setup Instructions

### 1. Install Dependencies

```powershell
cd d:\15B\multi-agent-literature-review\MALRS-Frontend
npm install
```

### 2. Configure Environment

The `.env` file has been created with the default API URL:

```env
VITE_API_URL=http://localhost:5000
```

If your Flask server runs on a different port, update this file.

### 3. Start the Flask Backend

Open a terminal:

```powershell
cd d:\15B\multi-agent-literature-review\Backend
python api_server.py
```

Wait for the message:
```
API will be available at: http://localhost:5000
```

### 4. Start the React Frontend

Open a **new terminal**:

```powershell
cd d:\15B\multi-agent-literature-review\MALRS-Frontend
npm run dev
```

The app will open at `http://localhost:5173` (or the next available port).

## How It Works

### Architecture

```
┌─────────────────────┐         HTTP POST          ┌──────────────────────┐
│   React Frontend    │  ────────────────────────▶ │   Flask API Server   │
│  (MALRS-Frontend)   │                             │ (Backend/api_server) │
└─────────────────────┘                             └──────────────────────┘
         │                                                     │
         │                                                     ▼
         ▼                                          ┌──────────────────────┐
  Components use                                    │  CrewAI Multi-Agent  │
  useResearchState()                                │   Backend (main.py)  │
  hook to trigger                                   └──────────────────────┘
  analysis
```

### Key Files

| File | Purpose |
|------|---------|
| `src/lib/apiService.ts` | API client for Flask backend |
| `src/hooks/useResearchState.ts` | State management & API calls |
| `src/components/tabs/InputConfigureTab.tsx` | Input UI component |
| `src/components/tabs/ResultsTab.tsx` | Results display |
| `.env` | API URL configuration |

### Data Flow

1. **User Input** (InputConfigureTab)
   - User adds paper sections
   - Optionally adds research idea
   - Selects research domains
   - Clicks "Launch Analysis"

2. **API Request** (useResearchState → apiService)
   ```typescript
   const request = {
     research_idea: "...",
     selected_domains: ["..."],
     paper_data: {
       paper_sections: [{field: "...", content: "..."}]
     }
   };
   
   const response = await apiService.analyze(request);
   ```

3. **Backend Processing** (Flask → CrewAI)
   - Flask receives request
   - Calls `run_analysis_api()`
   - Multi-agent crew analyzes
   - Returns structured JSON

4. **Display Results** (ResultsTab)
   - Shows novelty score, metrics
   - Displays analysis report
   - Shows retrieved papers
   - Provides download options

## API Integration Details

### API Service Methods

**`apiService.healthCheck()`**
- Tests if backend is reachable
- Returns service status

**`apiService.analyze(request, onProgress?)`**
- Sends analysis request
- Optional progress callback for UI updates
- Returns complete analysis results

**`apiService.testConnection()`**
- Quick connectivity test
- Returns boolean

### Progress Updates

The API service simulates progress during the analysis:

```typescript
onProgress("Retrieving relevant literature...", 30);
onProgress("Multi-agent analysis in progress...", 50);
onProgress("Processing results...", 70);
```

This provides real-time feedback while waiting for the backend.

### Error Handling

The integration handles three types of errors:

1. **Connection Error**
   ```
   Cannot connect to the backend API. 
   Please ensure the Flask server is running on http://localhost:5000
   ```

2. **API Error**
   ```
   Analysis failed: [error message from backend]
   ```

3. **Unknown Error**
   ```
   Error: [error details]
   ```

## Testing the Integration

### 1. Test Backend Connection

Before running analysis, you can check if the backend is reachable:

```typescript
// In browser console or component
import { apiService } from '@/lib/apiService';
const isConnected = await apiService.testConnection();
console.log('Backend connected:', isConnected);
```

### 2. Test Full Analysis

1. Start both Flask backend and React frontend
2. Navigate to the app in browser
3. Add a paper section (e.g., Abstract)
4. Click "Launch Comprehensive Analysis"
5. Watch the progress bar
6. View results in the Results tab

### 3. Monitor Backend Logs

While testing, keep an eye on the Flask terminal for logs:
- Request received
- Analysis starting
- Papers retrieved
- Crew execution
- Results returned

## Troubleshooting

### "Cannot connect to the backend API"

**Problem**: React can't reach Flask server

**Solutions**:
1. Ensure Flask is running: `python api_server.py`
2. Check the port in `.env` matches Flask (default: 5000)
3. Verify no firewall is blocking localhost:5000

### "CORS Error"

**Problem**: Cross-origin request blocked

**Solution**: Flask-CORS is already configured in `api_server.py`. If you still see CORS errors, ensure the Flask app is running with CORS enabled.

### Analysis Takes Too Long

**Problem**: Request times out or hangs

**Solutions**:
1. Backend may be processing many papers
2. Check backend terminal for progress
3. Reduce number of selected domains
4. Ensure Ollama/LLM is responding quickly

### Results Not Displaying

**Problem**: Analysis completes but nothing shows

**Solutions**:
1. Check browser console for errors
2. Verify API response structure matches interface
3. Check if `analysisResult` is being set in state

## Environment Variables

### Available Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:5000` | Flask API base URL |

### Changing the API URL

If running Flask on a different port or server:

1. Edit `.env`:
   ```env
   VITE_API_URL=http://localhost:8080
   ```

2. Restart the Vite dev server:
   ```powershell
   # Stop the server (Ctrl+C)
   npm run dev
   ```

## Next Steps

- ✅ React frontend now uses real Flask API (same as Streamlit)
- ✅ Paper sections are sent to backend for analysis
- ✅ Progress tracking during analysis
- ✅ Results display with full report and metrics
- ✅ Error handling and user feedback

Try the integration by running both servers and testing the full workflow!
