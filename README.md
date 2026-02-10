# Multi-Agent Literature Review System (MALRS) - System Documentation

## 1. Project Overview

### Purpose
The Multi-Agent Literature Review System (MALRS) is an advanced research automation platform designed to produce PhD-level academic literature reviews. It mimics the cognitive workflow of human researchers by employing a team of specialized AI agents to discover, read, analyze, and synthesize scientific papers.

### Problem It Solves
Traditional literature review is time-consuming, prone to bias, and overwhelming due to the sheer volume of new publications. MALRS automates this process, reducing weeks of manual work into minutes while ensuring comprehensive coverage and reducing hallucinations through strict grounded evidence.

### Target Users
- Academic Researchers (PhD students, Professors)
- R&D Scientists
- Technical Analysts
- Medical Researchers

### Key Features
- **Multi-Source Retrieval**: Fetches papers from arXiv, PubMed, Semantic Scholar, and OpenAlex.
- **AI Agent Team**: Six specialized agents mimic a research lab (Retrieval, Decomposition, Reasoning, etc.).
- **Advanced RAG Pipeline**: Uses Hybrid Search (Dense + Sparse), Semantic Chunking, and HyDE (Hypothetical Document Embeddings) for high-recall data retrieval.
- **Hallucination Control**: Strict citation verification ensures every claim is backed by a real paper handle [P#].
- **Interactive Reports**: Generates detailed markdown reports and real-time streaming analysis logs.

---

## 2. High-Level System Architecture

### Architecture Style
The system follows a **Client-Server Architecture** with a **Service-Oriented** backend. The backend logic is **Agentic**, orchestrated by CrewAI.

### Components
1.  **Presentation Layer (Frontend)**: A modern, reactive Single Page Application (SPA) that handles user input, visualization, and real-time status updates.
2.  **API Layer (Backend Interface)**: A Flask-based REST API that exposes the core analysis logic and supports Server-Sent Events (SSE) for log streaming.
3.  **Agent Orchestration Layer**: A CrewAI execution engine that coordinates the specialized agents.
4.  **Data & RAG Layer**: A hybrid storage system containing a Vector Database (FAISS), a Metadata Store (JSON), and an Evidence Store.

### Architecture Diagram

```text
      +--------+       HTTP/SSE       +------------+
      |  User  | <------------------> | Frontend   |
      +--------+                      +------------+
                                            |
                                            | API Calls
                                            v
                                   +-------------------+
                                   | Flask API Server  |
                                   +-------------------+
                                            |
                                            v
                                +-------------------------+
                                |    Main Orchestrator    |
                                +-------------------------+
                                            |
         +----------------------------------+----------------------------------+
         |                                  |                                  |
         v                                  v                                  v
+------------------+              +--------------------+            +---------------------+
|  Paper Scrapers  |              |    RAG Pipeline    |            |  CrewAI Agent Team  |
| (arXiv, PubMed)  |              |    (FAISS + HyDE)  |            |                     |
+------------------+              +--------------------+            |  1. Retrieval       |
         |                                  ^                       |  2. Decomposition   |
         | Raw Papers                       | Context Queries       |  3. Reasoning       |
         +----------------------------------+                       |  4. Gap & Novelty   |
                                            | <-------------------- |  5. Synthesis       |
                                            |                       |  6. Quality Control |
                                            |                       +---------------------+
                                                                               |
                                                                               | Final Report
                                                                               v
                                                                        +-------------+
                                                                        |  MD Report  |
                                                                        +-------------+
```

---

## 3. Technology Stack

### Frontend
-   **Framework**: React 18 with Vite (Fast, modern build tool)
-   **Language**: TypeScript
-   **Styling**: Tailwind CSS + Shadcn/UI (for premium, accessible components)
-   **State Management**: React Query (TanStack Query) for server state & caching
-   **Visualization**: Recharts (for metrics), Framer Motion (for animations)
-   **Communication**: Axios/Fetch for API, EventSource for SSE

### Backend
-   **Language**: Python 3.10+
-   **API Framework**: Flask (Lightweight, robust WSGI server)
-   **Agent Framework**: CrewAI (Orchestrates autonomous agents)
-   **LLM Interface**: LangChain (for RAG and tool abstractions)
-   **Vector Logic**: FAISS (Vector Store), Sentence-Transformers (Embeddings)
-   **Data Processing**: NumPy, Scikit-learn (for TF-IDF/Cosine Similarity), BeautifulSoup (Parsing)
-   **External APIs**: arXiv API, Semantic Scholar Graph API, PubMed (BioPython/Requests), OpenAlex

---

## 4. Detailed Workflow Explanation

1.  **Initialization**: The user provides a research topic (e.g., "Transformers in Healthcare") and selects domains.
2.  **Paper Discovery**: The system parallel-fetches papers from multiple external repositories (arXiv, PubMed, etc.).
3.  **Ingestion & Indexing**:
    *   **Semantic Chunking**: Abstracts are split into meaningful chunks based on semantic similarity rather than just character counts.
    *   **Hybrid Indexing**: Chunks are embedded (Dense Vector) and tokenized (Sparse TF-IDF) to allow for both conceptual and keyword-based retrieval.
4.  **Agent Execution Loop**:
    *   The **Retrieval Agent** broadens the search using HyDE (generating hypothetical abstracts to partial-match).
    *   The **Decomposition Agent** extracts claims, methods, and results from the papers.
    *   The **Reasoning Agent** looks for contradictions and consensus across papers.
    *   The **Synthesis Agent** drafts the final review.
    *   The **Quality Control Agent** verifies every citation against the actual evidence store.
5.  **Output Generation**: The system compiles a detailed Markdown report, a raw analysis log, and JSON metrics.

---

## 5. Input-to-Output Lifecycle (Core Requirement)

### 1. Input Source
*   **User UI**: User types a "Research Idea" and selects "Domains" in the React frontend.
*   **Uploads**: Optionally, the user uploads PDF/Text files which are parsed and indexed immediately.

### 2. Validation & Preprocessing
*   **Frontend**: Zod schema validation ensures the research idea is not empty.
*   **Backend API**: `api_server.py` validates the JSON payload.
*   **Query Expansion**: The `QueryRewriter` module expands the simple user query into complex boolean queries optimized for academic search engines.

### 3. Data Retrieval & Indexing
*   **Parallel Scraping**: `ThreadPoolExecutor` triggers simultaneous calls to arXiv, PubMed, and Semantic Scholar.
*   **Deduplication**: Papers with identical titles/DOIs are merged.
*   **RAG Ingestion**:
    *   Papers are converted to `Document` objects.
    *   `SBERTEmbeddings` generates vector embeddings.
    *   FAISS index and `papers_metadata.json` are updated.

### 4. Business Logic (The Crew)
The `main.py` orchestrator kicks off the sequential CrewAI process:
*   **Step A (Retrieval)**: Queries the RAG system for foundational papers.
*   **Step B (Decomposition)**: Breaks down key papers into "Atomic Facts".
*   **Step C (Reasoning)**: Builds a "Synthesis Matrix" comparing papers.
*   **Step D (Drafting)**: Writes the sections of the review.

### 5. Response Generation
*   **Streaming**: Throughout the process, the backend pushes logs via SSE (`/api/logs/stream`) to the frontend terminal.
*   **Formatting**: The `output_formatter.py` compiles agent outputs into a structured Markdown file (`final_research_report.md`).

### 6. Output Delivery
*   The API returns a JSON response containing the full report content and metadata.
*   The Frontend renders the Markdown report and unlocks the "Download" buttons.

---

## 6. Internal Code Structure

### Backend (`/Backend`)
*   **`api_server.py`**: The entry point. Handles HTTP requests and manages the background threads for log broadcasting.
*   **`main.py`**: The core logic. Initializes the RAG pipeline, tools, and the CrewAI team. Contains the `retrieve_and_index_papers` function.
*   **`rag_pipeline.py`**: Implementation of `RAGPipeline`, `HybridRetriever`, and `SemanticChunker`. Manages FAISS interactions.
*   **`agents.py`**: Defines the 6 specific agents, their goals, backstories, and allowed tools.
*   **`tools.py`**: Wrappers for the RAG search, context reading, and logging tools used by agents.
*   **`evidence_store.py`**: A thread-safe singleton that manages the raw text of papers to ensure "grounding."

### Frontend (`/MALRS-Frontend`)
*   **`src/App.tsx`**: Main application router and layout shell.
*   **`src/components/InputSection.tsx`**: Form for user input config.
*   **`src/components/ResultsSection.tsx`**: Handles the display of the final report and the real-time terminal.
*   **`src/lib/api.ts`**: Axios instance and API helper functions.
*   **`src/hooks/use-research-stream.ts`**: Custom hook handling the EventSource connection for streaming logs.

---

## 7. Data Flow & State Management

### Data Storage
*   **Ephemeral**: In-memory Python objects for active agent tasks.
*   **Persistent (Session)**:
    *   `outputs/research_session_YMD_HMS/`: Stores all artifacts for a specific run.
    *   `faiss_index/`: Stores vector embeddings on disk.
    *   `papers_metadata.json`: Stores metadata (Title, Author, Year, DOI) mapped to internal handles.

### State Management
*   **Backend**: Stateless API design, but relies on the file system (`outputs/`) to maintain session context between the "Start" request and "Get Report" requests.
*   **Frontend**: Uses `React Query` to manage async server state (loading flags, data availability). `Context API` (implied) or local state manages UI themes and active tabs.

### Error Handling
*   **API Level**: Try/Catch blocks in `api_server.py` return 500 errors with stack traces.
*   **Agent Level**: CrewAI handles some retries. `MetricsTracker` logs failures without crashing the entire pipeline if possible.
*   **Graceful Degradation**: If one paper source (e.g., PubMed) fails, the system continues with results from others.

---

## 8. Security & Performance Considerations

### Security
*   **Analysis Sandbox**: The system runs locally; no data is sent to third-party cloud vector stores (FAISS is local).
*   **Input Sanitization**: Basic JSON validation prevents injection of malformed data structures.
*   **CORS**: Configured to allow communication only between the specific frontend and backend ports.

### Performance
*   **Parallelism**: Uses `ThreadPoolExecutor` for fetching papers (IO-bound).
*   **Indexing**: `SBERTEmbeddings` are batched to maximize GPU/CPU throughput.
*   **Reranking**: Uses a lightweight Cross-Encoder (`ms-marco-MiniLM-L-6-v2`) to balance accuracy and speed (reranking only top 20 candidates).
*   **Caching**: `lru_cache` and simple dictionary caches prevent redundant embedding of the same query.

---

## 9. End-to-End Execution Flow (Narrative Style)

**The Story of a Request:**

1.  **The User Acts**: A researcher opens the web app, types "Impact of sleep on memory consolidation," selects "Neuroscience," and clicks "Launch Analysis."
2.  **The System Awakens**: The Frontend sends a POST request to the Backend. The Backend immediately responds, "I'm on it," and spins up a background thread.
3.  **The Hunt**: The Backend's `ThreadPool` simultaneous contacts arXiv, PubMed, and Semantic Scholar. It asks for papers related to the topic, automatically expanding the query to include terms like "REM sleep" and "Hippocampus."
4.  **The Library**: Within seconds, 15-50 papers are downloaded. The system reads them, chops them into semantic blocks, and files them into the digital library (FAISS Index).
5.  **The Crew Assembles**:
    *   **Retrieval Agent**: "I need to find the seminal paper from 2005." It searches the index.
    *   **Decomposition Agent**: "I see the 2005 paper. Extracting sample size: n=40. Method: EEG."
    *   **Reasoning Agent**: "Wait, a 2019 paper contradicts this. It says n=40 is too small. Noting the conflict."
    *   **Synthesis Agent**: "I'll write the section on 'Methodological Controversies' using that conflict."
6.  **The Gatekeeper**: The Quality Control agent scans the draft. "You cited [P5] for that claim, but [P5] is about diet, not sleep. Correcting citation."
7.  **Delivery**: The final report is saved as Markdown. The Frontend sees the "Complete" signal, fetches the report, and renders it beautifully for the user to read.

---

## 10. Summary for Presentation & Interviews

### Execution Summary
The **Multi-Agent Literature Review System** is an autonomous AI research assistant. It solves the problem of information overload in academia by using a team of six specialized AI agents to independently search, read, analyze, and synthesize scientific literature. Unlike standard AI chatbots that hallucinate, this system uses a strict **RAG (Retrieval-Augmented Generation)** pipeline where every sentence is grounded in a retrieved academic paper.

### Key Talking Points
*   **Agentic Architecture**: It's not just one prompt; it's a workflow of specialized roles (Researcher, Analyst, Writer).
*   **Hybrid Search**: Combines keyword search (like Google) with semantic search (like ChatGPT) for best-in-class retrieval.
*   **Hallucination Proof**: The "Quality Control" agent performs a dedicated citation verification pass.
*   **Scalable**: The system creates a local knowledge base that grows with every new paper added.

### "How It Works" in One Sentence
"We built a digital research lab where AI agents act as research assistants—fetching papers, reading them, and writing a synthesized review—so you can focus on the breakthrough ideas instead of the busy work."
