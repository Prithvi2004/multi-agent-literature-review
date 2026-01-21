# Flask API Integration - Quick Start Guide

## Overview

The Multi-Agent Literature Review System now has a Flask REST API that connects the Streamlit frontend with the CrewAI backend.

## Architecture

```
┌─────────────────────┐         HTTP POST          ┌──────────────────────┐
│  Streamlit Frontend │  ────────────────────────▶ │   Flask API Server   │
│   (Frontend/app.py) │                             │ (Backend/api_server.py│
└─────────────────────┘                             └──────────────────────┘
                                                              │
                                                              ▼
                                                    ┌──────────────────────┐
                                                    │  CrewAI Multi-Agent  │
                                                    │   Backend (main.py)  │
                                                    └──────────────────────┘
```

## Setup Instructions

### 1. Install Backend Dependencies

```powershell
cd d:\15B\multi-agent-literature-review\Backend
pip install -r requirements.txt
```

**Key new dependencies:**
- `Flask>=3.0.0` - Web framework for API server
- `Flask-CORS>=4.0.0` - Cross-origin resource sharing support

### 2. Install Frontend Dependencies

```powershell
cd d:\15B\multi-agent-literature-review\Frontend
pip install -r requirements.txt
```

**Key new dependency:**
- `requests>=2.31.0` - HTTP client for API calls

## Running the System

### Step 1: Start the Flask API Server

Open a terminal and run:

```powershell
cd d:\15B\multi-agent-literature-review\Backend
python api_server.py
```

You should see:
```
================================================================================
Starting Flask API Server for Multi-Agent Literature Review
================================================================================
API will be available at: http://localhost:5000
Health check: http://localhost:5000/api/health
Analyze endpoint: http://localhost:5000/api/analyze
================================================================================
 * Running on http://0.0.0.0:5000
```

### Step 2: Start the Streamlit Frontend

Open a **new terminal** and run:

```powershell
cd d:\15B\multi-agent-literature-review\Frontend
streamlit run app.py
```

The browser should automatically open at `http://localhost:8501`

### Step 3: Use the Application

1. **Upload or Add Paper Data** (Tab 1: Input & Configure)
   - Add paper sections (Title, Abstract, etc.)
   - Or upload papers in the Paper Library tab

2. **Optional: Add Research Idea and Domains**
   - Enter your research hypothesis
   - Select relevant research domains

3. **Launch Analysis**
   - Click "Launch Comprehensive Analysis"
   - Watch the progress as the backend processes your request
   - Wait for completion (may take several minutes)

4. **View Results** (Tab 2: Results & Analysis)
   - Automatically switches to results tab when complete
   - View the comprehensive analysis report
   - Download reports in multiple formats

## API Endpoints

### Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-21T23:58:00",
  "service": "Multi-Agent Literature Review API"
}
```

### Analyze Research
```http
POST /api/analyze
Content-Type: application/json
```

**Request Body:**
```json
{
  "research_idea": "Your research question or hypothesis",
  "selected_domains": ["Domain 1", "Domain 2"],
  "paper_data": {
    "paper_sections": [
      {"field": "Title", "content": "Paper title"},
      {"field": "Abstract", "content": "Paper abstract"}
    ],
    "uploaded_papers": []
  }
}
```

**Success Response (200 OK):**
```json
{
  "status": "success",
  "message": "Analysis completed successfully",
  "data": {
    "final_report": "Comprehensive analysis report...",
    "agent_outputs": {
      "retrieval": "...",
      "decomposition": "...",
      "reasoning": "...",
      "gap_novelty": "...",
      "synthesis": "..."
    },
    "papers": [
      {
        "handle": "P1",
        "title": "Paper title",
        "authors": "Author names",
        "year": "2024",
        "abstract": "Abstract text"
      }
    ],
    "metrics": {
      "total_duration_seconds": 145.23,
      "total_papers_retrieved": 15,
      "total_agents": 6
    }
  }
}
```

**Error Response (400/500):**
```json
{
  "status": "error",
  "message": "Error description",
  "data": null
}
```

## Testing the API

### Manual Test with cURL

```powershell
curl -X POST http://localhost:5000/api/analyze `
  -H "Content-Type: application/json" `
  -d '{\"research_idea\": \"Test idea\", \"selected_domains\": [\"AI\"]}'
```

### Automated Test Script

```powershell
cd d:\15B\multi-agent-literature-review\Backend
python test_api.py
```

This will run comprehensive tests including:
- Health check verification
- Input validation tests
- Full analysis workflow

## Troubleshooting

### Error: "Cannot connect to the backend API"

**Solution:** Make sure the Flask server is running on port 5000
```powershell
cd Backend
python api_server.py
```

### Error: Port 5000 already in use

**Solution:** Kill the process using port 5000 or change the port in `api_server.py`:
```python
app.run(host='0.0.0.0', port=5001)  # Use different port
```

Then update `Frontend/app.py`:
```python
API_BASE_URL = "http://localhost:5001"  # Match the new port
```

### Error: Timeout during analysis

**Solution:** Increase the timeout in `Frontend/app.py`:
```python
response = requests.post(
    f"{API_BASE_URL}/api/analyze",
    json=payload,
    timeout=900  # Increase to 15 minutes
)
```

### Backend analysis takes too long

**Possible causes:**
1. Many papers being retrieved and analyzed
2. Ollama/LLM response time is slow
3. Network latency for API calls to arXiv/PubMed

**Solutions:**
- Reduce `max_results` in `retrieve_and_index_papers()`
- Use faster LLM models
- Add caching to reduce API calls

## Configuration

### API Base URL (Frontend)

Edit `Frontend/app.py`:
```python
API_BASE_URL = "http://localhost:5000"  # Change to your server address
```

### Server Settings (Backend)

Edit `Backend/api_server.py`:
```python
app.run(
    host='0.0.0.0',      # Listen on all interfaces
    port=5000,            # Port number
    debug=False,          # Set True for development
    threaded=True         # Enable concurrent requests
)
```

## Next Steps

- The system is ready for end-to-end testing
- Try with real research data
- Monitor backend logs for any issues
- Export and review the generated reports

## Support

For issues or questions, check:
1. Backend logs in terminal running `api_server.py`
2. Frontend errors displayed in Streamlit UI
3. Browser console for client-side errors (F12)
